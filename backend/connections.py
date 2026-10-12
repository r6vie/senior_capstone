"""Requests between members: ask for mentorship, advice or an introduction, talk, then accept or decline.

A request has a conversation. The requester's first message is the request itself; the person
asked can reply. Once they accept, each side gets the other's email address and can carry on
outside the app.
"""

from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from auth import get_current_user
from connection_models import (
    REQUEST_TYPE_LABELS, ConnectionCreate, ConnectionResponse, ConnectionUpdate, MessageCreate, MessageResponse,
    RequestType, RequestTypeOption,
)
from database import get_database
from models import Profile, SavedProfile
from notifications import notify_connection_accepted, notify_connection_request, notify_new_message

router = APIRouter(
    prefix="/connections", tags=["Connections"], dependencies=[Depends(get_current_user)],
)

PROFILE_PROJECTION = {"_id": 1, **{field: 1 for field in Profile.model_fields}}
MAX_REQUESTS_PER_DAY = 10  # per sender, so nobody can message every member at once
MAX_MESSAGES_PER_THREAD = 100


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


def other_user_id(document: dict, user_id: str) -> str:
    return document["recipient_user_id"] if document["sender_user_id"] == user_id else document["sender_user_id"]


def connection_response(
    document: dict, user_id: str, other_profile: dict | None, contact_email: str | None = None,
) -> ConnectionResponse:
    return ConnectionResponse(
        id=document["_id"], status=document["status"],
        type=document.get("type", "other"),  # requests saved before types existed
        direction="outgoing" if document["sender_user_id"] == user_id else "incoming",
        message=document.get("message"), created_at=document["created_at"],
        responded_at=document.get("responded_at"), profile=public_profile(other_profile),
        # An address is only ever shared after the request has been accepted.
        contact_email=contact_email if document["status"] == "accepted" else None,
    )


async def email_of(database, user_id: str) -> str | None:
    user = await database.users.find_one({"_id": user_id, "is_active": True}, {"email": 1})
    return user["email"] if user else None


async def my_connection(database, connection_id: str, user_id: str) -> dict:
    """Load a request, but only for the two people involved; anyone else gets a 404."""
    document = await database.connections.find_one({
        "_id": connection_id, "$or": [{"sender_user_id": user_id}, {"recipient_user_id": user_id}],
    })
    if document is None:
        raise HTTPException(status_code=404, detail="Request not found.")
    return document


@router.get("/types", response_model=list[RequestTypeOption])
async def request_types() -> list[RequestTypeOption]:
    """The kinds of request a member can send, for a dropdown."""
    return [RequestTypeOption(value=value, label=label) for value, label in REQUEST_TYPE_LABELS.items()]


@router.post("", response_model=ConnectionResponse, status_code=201)
async def send_request(
    data: ConnectionCreate, background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user), database=Depends(get_database),
) -> ConnectionResponse:
    """Send someone a request with a type (such as mentorship) and a message. They get an email.

    Only one request can exist between two people, in either direction. A declined request
    stays on record, which stops repeated requests to someone who said no. Each member can
    send up to 10 requests per day. If the request is accepted, you and they see each
    other's email address.
    """
    mine = await database.profiles.find_one({"owner_user_id": user["_id"]}, PROFILE_PROJECTION)
    if mine is None:
        raise HTTPException(status_code=409, detail="Create your profile before sending requests.")
    target = await database.profiles.find_one(
        {"_id": data.profile_id}, {**PROFILE_PROJECTION, "owner_user_id": 1},
    )
    if target is None:
        raise HTTPException(status_code=404, detail="Profile not found.")
    recipient_id = target.get("owner_user_id")
    if recipient_id is None:
        raise HTTPException(status_code=409, detail="This is a demo profile and cannot receive requests.")
    if recipient_id == user["_id"]:
        raise HTTPException(status_code=400, detail="You cannot send a request to yourself.")

    since = datetime.now(timezone.utc) - timedelta(days=1)
    recent = await database.connections.count_documents(
        {"sender_user_id": user["_id"], "created_at": {"$gte": since}},
    )
    if recent >= MAX_REQUESTS_PER_DAY:
        raise HTTPException(
            status_code=429,
            detail=f"You can send up to {MAX_REQUESTS_PER_DAY} requests per day. Please try again tomorrow.",
        )

    document = {
        "_id": str(uuid4()), "pair_key": pair_key(user["_id"], recipient_id),
        "sender_user_id": user["_id"], "recipient_user_id": recipient_id,
        "status": "pending", "type": data.type, "message": data.message,
        "created_at": datetime.now(timezone.utc), "responded_at": None,
    }
    try:
        await database.connections.insert_one(document)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=409, detail="A request between you and this person already exists.",
        ) from None
    background_tasks.add_task(notify_connection_request, database, document["_id"])
    return connection_response(document, user["_id"], target)


@router.get("", response_model=list[ConnectionResponse])
async def list_connections(
    status: Literal["pending", "accepted", "declined"] | None = None,
    request_type: RequestType | None = Query(default=None, alias="type"),
    user: dict = Depends(get_current_user), database=Depends(get_database),
) -> list[ConnectionResponse]:
    """List requests you sent and received, newest first (up to 100), optionally by status or type.

    Accepted requests include the other person's email in contact_email.
    """
    me = user["_id"]
    query = {"$or": [{"sender_user_id": me}, {"recipient_user_id": me}]}
    if status:
        query["status"] = status
    if request_type == "other":
        query["type"] = {"$in": ["other", None]}  # also matches requests saved before types existed
    elif request_type:
        query["type"] = request_type
    cursor = database.connections.find(query).sort("created_at", -1).limit(100)
    documents = await cursor.to_list(length=100)

    other_ids = {other_user_id(d, me) for d in documents}
    profiles = {}
    if other_ids:
        found = database.profiles.find(
            {"owner_user_id": {"$in": list(other_ids)}}, {**PROFILE_PROJECTION, "owner_user_id": 1},
        )
        profiles = {p["owner_user_id"]: p for p in await found.to_list(length=100)}
    accepted_ids = {other_user_id(d, me) for d in documents if d["status"] == "accepted"}
    emails = {}
    if accepted_ids:
        people = database.users.find({"_id": {"$in": list(accepted_ids)}, "is_active": True}, {"email": 1})
        emails = {person["_id"]: person["email"] for person in await people.to_list(length=100)}
    return [
        connection_response(d, me, profiles.get(other_user_id(d, me)), emails.get(other_user_id(d, me)))
        for d in documents
    ]


@router.get("/{connection_id}", response_model=ConnectionResponse)
async def get_connection(
    connection_id: str, user: dict = Depends(get_current_user), database=Depends(get_database),
) -> ConnectionResponse:
    """One request you sent or received. Anyone else gets a 404."""
    document = await my_connection(database, connection_id, user["_id"])
    other_id = other_user_id(document, user["_id"])
    profile = await database.profiles.find_one({"owner_user_id": other_id}, PROFILE_PROJECTION)
    email = await email_of(database, other_id) if document["status"] == "accepted" else None
    return connection_response(document, user["_id"], profile, email)


@router.patch("/{connection_id}", response_model=ConnectionResponse)
async def respond_to_request(
    connection_id: str, data: ConnectionUpdate, background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user), database=Depends(get_database),
) -> ConnectionResponse:
    """Accept or decline a pending request that was sent to you.

    Accepting shares your email address with the sender, and theirs with you.
    Declining closes the conversation.
    """
    document = await database.connections.find_one_and_update(
        {"_id": connection_id, "recipient_user_id": user["_id"], "status": "pending"},
        {"$set": {"status": data.status, "responded_at": datetime.now(timezone.utc)}},
        return_document=ReturnDocument.AFTER,
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Pending request not found.")
    email = None
    if data.status == "accepted":
        background_tasks.add_task(notify_connection_accepted, database, connection_id)
        email = await email_of(database, document["sender_user_id"])
    sender = await database.profiles.find_one({"owner_user_id": document["sender_user_id"]}, PROFILE_PROJECTION)
    return connection_response(document, user["_id"], sender, email)


# ---- The conversation -----------------------------------------------------------------------

@router.get("/{connection_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    connection_id: str, user: dict = Depends(get_current_user), database=Depends(get_database),
) -> list[MessageResponse]:
    """The conversation, oldest first. The first message is always the original request."""
    me = user["_id"]
    document = await my_connection(database, connection_id, me)
    cursor = database.messages.find({"connection_id": connection_id}).sort("created_at", 1).limit(MAX_MESSAGES_PER_THREAD)
    replies = await cursor.to_list(length=MAX_MESSAGES_PER_THREAD)
    thread = []
    if document.get("message"):
        thread.append(MessageResponse(
            id="request", from_me=document["sender_user_id"] == me, body=document["message"],
            created_at=document["created_at"],
        ))
    thread += [
        MessageResponse(id=m["_id"], from_me=m["sender_user_id"] == me, body=m["body"], created_at=m["created_at"])
        for m in replies
    ]
    return thread


@router.post("/{connection_id}/messages", response_model=MessageResponse, status_code=201)
async def send_message(
    connection_id: str, data: MessageCreate, background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user), database=Depends(get_database),
) -> MessageResponse:
    """Reply in a request's conversation. The other person gets an email (at most one per 10 minutes).

    While a request is pending, the person who sent it can write again only after the other
    person has replied. Once it is accepted, either of you can write freely. A declined
    request is closed.
    """
    me = user["_id"]
    document = await my_connection(database, connection_id, me)
    if document["status"] == "declined":
        raise HTTPException(status_code=409, detail="This request was declined, so the conversation is closed.")
    if await database.messages.count_documents({"connection_id": connection_id}) >= MAX_MESSAGES_PER_THREAD:
        raise HTTPException(status_code=409, detail="This conversation is full. Continue by email instead.")
    if document["status"] == "pending" and document["sender_user_id"] == me:
        last = await database.messages.find_one({"connection_id": connection_id}, sort=[("created_at", -1)])
        last_sender = last["sender_user_id"] if last else document["sender_user_id"]
        if last_sender == me:
            raise HTTPException(status_code=409, detail="Please wait for a reply before sending another message.")

    message = {
        "_id": str(uuid4()), "connection_id": connection_id, "sender_user_id": me,
        "body": data.body, "created_at": datetime.now(timezone.utc),
    }
    await database.messages.insert_one(message)
    background_tasks.add_task(notify_new_message, database, connection_id, message["_id"])
    return MessageResponse(id=message["_id"], from_me=True, body=message["body"], created_at=message["created_at"])
