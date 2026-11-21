from fastapi import APIRouter, Depends, Request
from pymongo.asynchronous.database import AsyncDatabase

from trove.ai.client import optional_claude
from trove.auth.service import get_current_user
from trove.core.database import get_database
from trove.discovery.models import LibrarianRecommendation
from trove.discovery.service import librarian_recommendation

router = APIRouter(prefix="/discovery", tags=["Discovery"])


@router.get("/recommendation", response_model=LibrarianRecommendation)
async def recommendation(
    request: Request,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> LibrarianRecommendation:
    """The Librarian's one current pick, based only on this member's own book."""
    return await librarian_recommendation(database, user["_id"], optional_claude(request))
