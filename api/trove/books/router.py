from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.asynchronous.database import AsyncDatabase

from trove.auth.service import get_current_user
from trove.books import service as books
from trove.books.models import BookCard, BookEdit, ChapterEdit, MyBookResponse, PublicBookResponse, ShelfPage
from trove.books.service import get_book_of, get_public_book, list_shelf, my_book_view, shelf_cursor
from trove.core.database import get_database
from trove.interview.service import changes_waiting, nothing_open

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
    return my_book_view(book, undoable=await nothing_open(database, user["_id"]))


async def _own_view(database: AsyncDatabase, book: dict | None, user_id: str) -> MyBookResponse:
    return my_book_view(book, undoable=await nothing_open(database, user_id))


async def _editable(database: AsyncDatabase, user_id: str) -> None:
    # The member decides on waiting changes first, so an edit and a proposal never collide.
    if await changes_waiting(database, user_id):
        raise HTTPException(
            status_code=409, detail="You have proposed changes waiting. Decide on those first, then edit."
        )


@router.patch("/me", response_model=MyBookResponse)
async def edit_my_book(
    data: BookEdit,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> MyBookResponse:
    """Change the book's title or back cover, in the member's own words. On a published book it's
    live at once, and POST /interview/book/undo takes it back. 409 while proposed changes wait."""
    await _editable(database, user["_id"])
    try:
        book = await books.edit_book(database, user["_id"], title=data.title, blurb=data.blurb)
    except books.EditRefused as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from None
    return await _own_view(database, book, user["_id"])


@router.patch("/me/chapters/{chapter_id}", response_model=MyBookResponse)
async def edit_my_chapter(
    chapter_id: str,
    data: ChapterEdit,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> MyBookResponse:
    """Change a chapter's title or summary. Its quotes stay. In a draft, the last version can be
    restored (`has_previous`, POST /interview/book/chapters/{id}/restore)."""
    await _editable(database, user["_id"])
    try:
        book = await books.edit_chapter(
            database, user["_id"], chapter_id, title=data.title, summary=data.summary
        )
    except books.EditRefused as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from None
    return await _own_view(database, book, user["_id"])


@router.post("/me/take-down", response_model=MyBookResponse)
async def take_down(
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> MyBookResponse:
    """Take the book off the shelf. No new checkouts; anything already arranged goes ahead."""
    book = await books.take_off_shelf(database, user["_id"])
    if book is None:
        raise HTTPException(status_code=409, detail="Your book isn't on the shelf.")
    return await _own_view(database, book, user["_id"])


@router.post("/me/put-back", response_model=MyBookResponse)
async def put_back(
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> MyBookResponse:
    """Put a book that was taken down back on the shelf, in the same place as before."""
    book = await books.put_back_on_shelf(database, user["_id"])
    if book is None:
        raise HTTPException(status_code=409, detail="Your book isn't off the shelf.")
    return await _own_view(database, book, user["_id"])


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
