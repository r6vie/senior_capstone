"""Connection requests: ask someone to connect, then accept or decline."""

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from auth import get_current_user
from connection_models import ConnectionCreate, ConnectionResponse, ConnectionUpdate
from database import get_database
from models import Profile, SavedProfile
from notifications import notify_connection_accepted, notify_connection_request

router = APIRouter(
    prefix="/connections", tags=["Connections"], dependencies=[Depends(get_current_user)],
)

PROFILE_PROJECTION = {"_id": 1, **{field: 1 for field in Profile.model_fields}}


def public_profile(document: dict | None) -> SavedProfile | None:
    """Public fields only: owner_user_id never leaves the server."""
    if document is None:
        return None
    return SavedProfile.model_validate({
        **{field: document[field] for field in Profile.model_fields if field in document},
        "id": str(document["_id"]),
    })


def pair_key(first_user_id: str, second_user_id: str) -> str:
    # The same for A->B and B->A, so a unique index allows one request per pair.
    return "|".join(sorted((first_user_id, second_user_id)))


def connection_response(document: dict, user_id: str, other_profile: dict | None) -> ConnectionResponse:
    return ConnectionResponse(
        id=document["_id"], status=document["status"],
        direction="outgoing" if document["sender_user_id"] == user_id else "incoming",
        message=document.get("message"), created_at=document["created_at"],
        responded_at=document.get("responded_at"), profile=public_profile(other_profile),
    )


@router.post("", response_model=ConnectionResponse, status_code=201)
async def send_request(
    data: ConnectionCreate, background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user), database=Depends(get_database),
) -> ConnectionResponse:
    """Ask the owner of a profile to connect. They get an email explaining why it could be a good fit.

    Only one request can exist between two people, in either direction. A declined request
    stays on record, which stops repeated requests to someone who said no.
    """
    mine = await database.profiles.find_one({"owner_user_id": user["_id"]}, PROFILE_PROJECTION)
    if mine is None:
        raise HTTPException(status_code=409, detail="Create your profile before sending connection requests.")
    target = await database.profiles.find_one(
        {"_id": data.profile_id}, {**PROFILE_PROJECTION, "owner_user_id": 1},
    )
    if target is None:
        raise HTTPException(status_code=404, detail="Profile not found.")
    recipient_id = target.get("owner_user_id")
    if recipient_id is None:
        raise HTTPException(status_code=409, detail="This is a demo profile and cannot receive requests.")
    if recipient_id == user["_id"]:
        raise HTTPException(status_code=400, detail="You cannot connect with yourself.")

    document = {
        "_id": str(uuid4()), "pair_key": pair_key(user["_id"], recipient_id),
        "sender_user_id": user["_id"], "recipient_user_id": recipient_id,
        "status": "pending", "message": data.message,
        "created_at": datetime.now(timezone.utc), "responded_at": None,
    }
    try:
        await database.connections.insert_one(document)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=409, detail="A connection request between you and this person already exists.",
        ) from None
    background_tasks.add_task(notify_connection_request, database, document["_id"])
    return connection_response(document, user["_id"], target)


@router.get("", response_model=list[ConnectionResponse])
async def list_connections(
    status: Literal["pending", "accepted", "declined"] | None = None,
    user: dict = Depends(get_current_user), database=Depends(get_database),
) -> list[ConnectionResponse]:
    """List requests you sent and received, newest first (up to 100), optionally by status."""
    me = user["_id"]
    query = {"$or": [{"sender_user_id": me}, {"recipient_user_id": me}]}
    if status:
        query["status"] = status
    cursor = database.connections.find(query).sort("created_at", -1).limit(100)
    documents = await cursor.to_list(length=100)

    other_ids = {
        d["recipient_user_id"] if d["sender_user_id"] == me else d["sender_user_id"] for d in documents
    }
    profiles = {}
    if other_ids:
        found = database.profiles.find(
            {"owner_user_id": {"$in": list(other_ids)}}, {**PROFILE_PROJECTION, "owner_user_id": 1},
        )
        profiles = {p["owner_user_id"]: p for p in await found.to_list(length=100)}
    return [
        connection_response(
            d, me, profiles.get(d["recipient_user_id"] if d["sender_user_id"] == me else d["sender_user_id"]),
        )
        for d in documents
    ]


@router.patch("/{connection_id}", response_model=ConnectionResponse)
async def respond_to_request(
    connection_id: str, data: ConnectionUpdate, background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user), database=Depends(get_database),
) -> ConnectionResponse:
    """Accept or decline a pending request that was sent to you."""
    document = await database.connections.find_one_and_update(
        {"_id": connection_id, "recipient_user_id": user["_id"], "status": "pending"},
        {"$set": {"status": data.status, "responded_at": datetime.now(timezone.utc)}},
        return_document=ReturnDocument.AFTER,
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Pending request not found.")
    if data.status == "accepted":
        background_tasks.add_task(notify_connection_accepted, database, connection_id)
    sender = await database.profiles.find_one({"owner_user_id": document["sender_user_id"]}, PROFILE_PROJECTION)
    return connection_response(document, user["_id"], sender)
