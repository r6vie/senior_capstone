from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.asynchronous.database import AsyncDatabase

from trove.auth.service import get_current_user
from trove.books.models import BookCard, MyBookResponse, PublicBookResponse, ShelfPage
from trove.books.service import get_book_of, get_public_book, list_shelf, my_book_view, shelf_cursor
from trove.core.database import get_database

router = APIRouter(prefix="/books", tags=["Books"])


def _card(book: dict) -> dict:
    return {**book, "id": book["_id"], "blurb": book.get("blurb")}


@router.get("", response_model=ShelfPage)
async def shelf(
    limit: int = Query(20, ge=1, le=50),
    after: str | None = Query(None, max_length=200, description="The `next` value from the previous page."),
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> ShelfPage:
    """Books on the shelf, newest first."""
    # Ask for one extra book to know whether there is another page.
    try:
        books = await list_shelf(database, limit=limit + 1, after=after)
    except ValueError:
        raise HTTPException(status_code=422, detail="This shelf position is not valid.") from None
    page = books[:limit]
    return ShelfPage(
        books=[BookCard.model_validate(_card(book)) for book in page],
        next=shelf_cursor(page[-1]) if len(books) > limit else None,
    )


@router.get("/me", response_model=MyBookResponse)
async def my_book(
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> MyBookResponse:
    book = await get_book_of(database, user["_id"])
    if book is None:
        raise HTTPException(status_code=404, detail="You don't have a book yet.")
    return my_book_view(book)


@router.get("/{book_id}", response_model=PublicBookResponse)
async def open_book(
    book_id: str,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> PublicBookResponse:
    book = await get_public_book(database, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="This book isn't on the shelf.")
    return PublicBookResponse.model_validate(_card(book))
