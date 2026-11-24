from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Response
from pymongo.asynchronous.database import AsyncDatabase

from trove.auth.service import full_names_of, get_current_user
from trove.core.database import get_database
from trove.messaging import service
from trove.messaging.models import Message, MessageRequest, ReadRequest, Thread
from trove.messaging.service import MessageRefused

router = APIRouter(prefix="/messages", tags=["Messages"])


CheckoutId = Path(max_length=100)


def refused(error: MessageRefused) -> HTTPException:
    headers = {"Retry-After": str(error.retry_after)} if error.retry_after else None
    return HTTPException(status_code=error.status_code, detail=error.detail, headers=headers)


def message_view(message: dict, user_id: str, names: dict[str, str]) -> Message:
    sender_id = message["sender_id"]
    return Message(
        id=message["_id"],
        kind="message" if sender_id else "note",
        from_me=sender_id == user_id,
        sender_name=names.get(sender_id, "") if sender_id else "",
        text=message["text"],
        sent_at=service.as_utc(message["sent_at"]),
    )


@router.get("/{checkout_id}", response_model=Thread)
async def thread(
    checkout_id: str = CheckoutId,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> Thread:
    """The conversation on an accepted checkout, oldest first, starting with the reader's checkout note."""
    try:
        checkout = await service.readable_checkout(database, checkout_id, user["_id"])
    except MessageRefused as error:
        raise refused(error) from None
    names = await full_names_of(database, [checkout["reader_id"], checkout["author_id"]])
    other = service.other_person(checkout, user["_id"])
    checkout_note = Message(
        id=f"checkout-note-{checkout['_id']}",
        kind="checkout_note",
        from_me=checkout["reader_id"] == user["_id"],
        sender_name=names.get(checkout["reader_id"], ""),
        text=checkout["message"],
        sent_at=service.as_utc(checkout["created_at"]),
    )
    messages = await service.messages_of(database, checkout["_id"])
    return Thread(
        checkout_id=checkout["_id"],
        book_title=checkout["book_title"],
        other_name=names.get(other) or (checkout["author_name"] if other == checkout["author_id"] else ""),
        can_write=service.can_write(checkout),
        messages=[checkout_note, *(message_view(message, user["_id"], names) for message in messages)],
    )


@router.post("/{checkout_id}", response_model=Message, status_code=201)
async def send(
    data: MessageRequest,
    background_tasks: BackgroundTasks,
    checkout_id: str = CheckoutId,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> Message:
    """Write in the conversation. The other person is emailed, at most once every 10 minutes."""
    try:
        checkout = await service.readable_checkout(database, checkout_id, user["_id"])
        message = await service.send(database, checkout, user["_id"], data.text)
    except MessageRefused as error:
        raise refused(error) from None
    background_tasks.add_task(service.email_new_message, database, message)
    names = await full_names_of(database, [user["_id"]])
    return message_view(message, user["_id"], names)


@router.post("/{checkout_id}/read", status_code=204, response_class=Response)
async def mark_read(
    data: ReadRequest,
    checkout_id: str = CheckoutId,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> Response:
    """You've seen this conversation up to `seen_up_to`. Only you ever know this."""
    try:
        checkout = await service.readable_checkout(database, checkout_id, user["_id"])
    except MessageRefused as error:
        raise refused(error) from None
    await service.mark_read(database, checkout["_id"], user["_id"], data.seen_up_to)
    return Response(status_code=204)
