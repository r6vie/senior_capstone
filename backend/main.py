import re
from uuid import uuid4

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError, PyMongoError

from auth import get_current_user, router as auth_router
from database import get_database, lifespan
from models import Profile, ProfileUpdate, SavedProfile

# This is our backend application. FastAPI also creates API documentation for us.
app = FastAPI(title="FoundersCircle API", lifespan=lifespan)
protected = APIRouter(dependencies=[Depends(get_current_user)])

# Retrieve only the public profile fields plus MongoDB's ID.
PROFILE_PROJECTION = {"_id": 1, **{field: 1 for field in Profile.model_fields}}


def saved_profile(document: dict) -> SavedProfile:
    """Expose MongoDB's string _id as a regular JSON field named id."""
    return SavedProfile.model_validate({
        **{field: document[field] for field in Profile.model_fields if field in document},
        "id": str(document["_id"]),
    })


@app.exception_handler(PyMongoError)
async def database_error(request: Request, error: PyMongoError):
    return JSONResponse(
        status_code=503,
        content={"detail": "MongoDB is unavailable. Check your connection and Atlas settings."},
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, error: RequestValidationError):
    # Never echo a submitted password (or the full request body) in validation errors.
    details = [{key: item[key] for key in ("type", "loc", "msg")} for item in error.errors()]
    return JSONResponse(status_code=422, content={"detail": details})


@app.middleware("http")
async def private_responses(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith(("/auth", "/profiles")):
        response.headers["Cache-Control"] = "no-store"
    return response


# When someone visits the home address, run this function and return its message.
@app.get("/")
def home() -> dict[str, str]:
    return {"message": "FoundersCircle backend is running."}


@protected.get("/profiles/sample", response_model=SavedProfile)
async def sample_profile(database=Depends(get_database)) -> SavedProfile:
    """Return a fictional person to demonstrate what profile data looks like."""
    profile = await database.profiles.find_one({"_id": "sample-alex"}, PROFILE_PROJECTION)
    if profile is None:
        raise HTTPException(status_code=404, detail="Run backend/seed.py to add the sample profiles.")
    return saved_profile(profile)


@protected.get("/profiles", response_model=list[SavedProfile])
async def list_profiles(
    expertise: str | None = None, database=Depends(get_database)
) -> list[SavedProfile]:
    """List saved profiles, optionally matching part of an expertise label.

    Matching ignores capitalization and surrounding spaces. An omitted or blank
    filter returns all profiles (up to 100); no matches returns an empty list.
    """
    # FastAPI reads expertise from the URL: /profiles?expertise=mentoring
    search_term = (expertise or "").strip()
    query = {}
    if search_term:
        # Escape punctuation so user input is searched as text, not a regex program.
        query = {"expertise": {"$regex": re.escape(search_term), "$options": "i"}}

    cursor = database.profiles.find(query, PROFILE_PROJECTION).sort("_id", 1).limit(100)
    return [saved_profile(document) for document in await cursor.to_list(length=100)]


@protected.post("/profiles", response_model=SavedProfile, status_code=201)
async def create_profile(
    profile: Profile, user: dict = Depends(get_current_user), database=Depends(get_database),
) -> SavedProfile:
    """Create your own profile. Each account may have one profile at a time."""
    document = {"_id": str(uuid4()), "owner_user_id": user["_id"], **profile.model_dump()}
    try:
        await database.profiles.insert_one(document)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="You already have a profile. Edit it instead.") from None
    return saved_profile(document)


@protected.post("/profiles/validate", response_model=Profile)
def validate_profile(profile: Profile) -> Profile:
    """Check a profile with Pydantic and return it without saving to MongoDB.

    All five fields are required. Text must be nonblank; expertise and interests
    must be lists of nonblank strings (empty lists are allowed). Extra fields are
    rejected. Invalid input returns HTTP 422 with the affected field names.
    """
    return profile


# Keep named routes such as /profiles/me above the variable-ID route.
@protected.get("/profiles/me", response_model=SavedProfile)
async def my_profile(user: dict = Depends(get_current_user), database=Depends(get_database)) -> SavedProfile:
    """Find your own profile's ID and data after logging in."""
    document = await database.profiles.find_one({"owner_user_id": user["_id"]}, PROFILE_PROJECTION)
    if document is None:
        raise HTTPException(status_code=404, detail="You have not created a profile yet.")
    return saved_profile(document)


@protected.get("/profiles/{profile_id}", response_model=SavedProfile)
async def get_profile(profile_id: str, database=Depends(get_database)) -> SavedProfile:
    """Retrieve one saved profile using its id."""
    document = await database.profiles.find_one({"_id": profile_id}, PROFILE_PROJECTION)
    if document is None:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return saved_profile(document)


@protected.patch("/profiles/{profile_id}", response_model=SavedProfile)
async def update_profile(
    profile_id: str, changes: ProfileUpdate, user: dict = Depends(get_current_user),
    database=Depends(get_database),
) -> SavedProfile:
    """Update your own profile's supplied fields. Use [] to clear expertise or interests.

    Empty bodies, null values, blank text, and changes to the ID are rejected.
    The returned profile includes all its fields after the update.
    """
    document = await database.profiles.find_one_and_update(
        {"_id": profile_id, "owner_user_id": user["_id"]},
        {"$set": changes.model_dump(exclude_unset=True)},
        projection=PROFILE_PROJECTION,
        return_document=ReturnDocument.AFTER,
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Profile not found or not owned by you.")
    return saved_profile(document)


@protected.delete("/profiles/{profile_id}", status_code=204, response_class=Response)
async def delete_profile(
    profile_id: str, user: dict = Depends(get_current_user), database=Depends(get_database),
) -> Response:
    """Permanently delete your own profile. Success returns 204 with no response body."""
    result = await database.profiles.delete_one({"_id": profile_id, "owner_user_id": user["_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found or not owned by you.")
    return Response(status_code=204)


@protected.get("/health/database")
async def database_health(database=Depends(get_database)) -> dict[str, str]:
    await database.command("ping")
    return {"status": "connected", "database": database.name}


app.include_router(auth_router)
app.include_router(protected)
