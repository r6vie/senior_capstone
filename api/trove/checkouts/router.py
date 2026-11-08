from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from pymongo.asynchronous.database import AsyncDatabase

from trove.auth.service import full_names_of, get_current_user
from trove.checkouts import service
from trove.checkouts.models import (
    CheckoutRequest,
    LendingCheckout,
    MyCheckouts,
    ReaderBook,
    ReadingCheckout,
)
from trove.checkouts.service import CheckoutRefused
from trove.core.database import get_database
from trove.notifications.service import notify_checkout_requested

router = APIRouter(prefix="/checkouts", tags=["Checkouts"])

READER_STATUS = {
    service.REQUESTED: "waiting",
    service.ACCEPTED: "accepted",
    service.CANCELLED: "cancelled",
    service.DECLINED: "unavailable",
    service.EXPIRED: "unavailable",
}


def refused(error: CheckoutRefused) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=error.detail)


async def reading_views(database: AsyncDatabase, checkouts: list[dict]) -> list[ReadingCheckout]:
    # Authors' current names; the name saved on the checkout covers sample books with no account.
    names = await full_names_of(database, list({checkout["author_id"] for checkout in checkouts}))
    return [
        ReadingCheckout(
            id=checkout["_id"],
            book_id=checkout["book_id"],
            book_title=checkout["book_title"],
            author_name=names.get(checkout["author_id"]) or checkout["author_name"],
            message=checkout["message"],
            status=READER_STATUS[checkout["status"]],
            created_at=checkout["created_at"],
            expires_at=checkout["expires_at"] if checkout["status"] == service.REQUESTED else None,
        )
        for checkout in checkouts
    ]


async def lending_views(database: AsyncDatabase, checkouts: list[dict]) -> list[LendingCheckout]:
    names = await full_names_of(database, list({checkout["reader_id"] for checkout in checkouts}))
    views = []
    for checkout in checkouts:
        book = await service.reader_book_of(database, checkout["reader_id"])
        views.append(
            LendingCheckout(
                id=checkout["_id"],
                book_id=checkout["book_id"],
                book_title=checkout["book_title"],
                reader_name=names.get(checkout["reader_id"], ""),
                reader_book=ReaderBook(id=book["_id"], title=book["title"]) if book else None,
                message=checkout["message"],
                status="accepted" if checkout["status"] == service.ACCEPTED else "waiting",
                created_at=checkout["created_at"],
                expires_at=checkout["expires_at"] if checkout["status"] == service.REQUESTED else None,
            )
        )
    return views


@router.post("", response_model=ReadingCheckout, status_code=201)
async def check_out(
    data: CheckoutRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> ReadingCheckout:
    """Check out a book with a short message to its author."""
    try:
        checkout = await service.check_out(
            database, reader_id=user["_id"], book_id=data.book_id, message=data.message
        )
    except CheckoutRefused as error:
        raise refused(error) from None
    reader_name = (await full_names_of(database, [user["_id"]])).get(user["_id"], user["first_name"])
    background_tasks.add_task(
        notify_checkout_requested,
        database,
        checkout_id=checkout["_id"],
        author_id=checkout["author_id"],
        reader_name=reader_name,
        book_title=checkout["book_title"],
        message=checkout["message"],
    )
    return (await reading_views(database, [checkout]))[0]


@router.get("", response_model=MyCheckouts)
async def my_checkouts(
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> MyCheckouts:
    """Books you've checked out, and open checkouts of your book."""
    return MyCheckouts(
        reading=await reading_views(database, await service.checkouts_of_reader(database, user["_id"])),
        lending=await lending_views(database, await service.open_checkouts_of_author(database, user["_id"])),
    )


@router.post("/{checkout_id}/cancel", response_model=ReadingCheckout)
async def cancel(
    checkout_id: str,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> ReadingCheckout:
    """Withdraw a checkout the author hasn't answered yet."""
    try:
        checkout = await service.cancel(database, checkout_id, user["_id"])
    except CheckoutRefused as error:
        raise refused(error) from None
    return (await reading_views(database, [checkout]))[0]


@router.post("/{checkout_id}/accept", response_model=LendingCheckout)
async def accept(
    checkout_id: str,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> LendingCheckout:
    """Say yes to a checkout of your book."""
    try:
        checkout = await service.accept(database, checkout_id, user["_id"])
    except CheckoutRefused as error:
        raise refused(error) from None
    return (await lending_views(database, [checkout]))[0]


@router.post("/{checkout_id}/decline", status_code=204, response_class=Response)
async def decline(
    checkout_id: str,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> Response:
    """Say no to a checkout of your book. The reader sees "this book isn't available right now"."""
    try:
        await service.decline(database, checkout_id, user["_id"])
    except CheckoutRefused as error:
        raise refused(error) from None
    return Response(status_code=204)
