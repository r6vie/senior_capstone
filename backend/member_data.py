"""The one place that reads and writes member facts.

Other features (matching, notifications, outreach, profile pages) call these functions
instead of querying the facts collection, so the visibility rules live here only:

- the member sees all of their own facts;
- other members see public facts, plus matches_only facts once the two are connected;
- private facts count toward matching but are never returned for another viewer.
"""

from collections import Counter
from datetime import datetime, timezone
from uuid import uuid4

from member_models import (
    AreaCoverage, BasicsForm, Coverage, FactDraft, FactEdit, FactOut, FactRevision, SharedFact,
    slug,
)

FACT_SECTIONS = {
    "need": "Needs", "offer": "Can offer", "experience": "Experience", "goal": "Goals",
    "background": "Background", "preference": "Preferences", "availability": "Availability",
    "other": "Other",
}
ROLE_LABELS = {
    "student": "Student", "alum": "Alum", "faculty": "Faculty", "staff": "Staff",
    "other": "Community member",
}
SEEKING_TEXT = {
    "get_help": "Looking for help from others in the network",
    "give_help": "Wants to help others in the network",
    "both": "Looking for help and wants to help others in the network",
}
AREA_LABELS = {
    "needs": "What you need help with", "offers": "What you can offer",
    "style": "How you like to connect", "background": "Shared background", "goals": "Goals",
}
STATUS_SCORE = {"missing": 0, "started": 50, "good": 100}
MAX_PROFILE_TAGS = 8


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------- writing facts

def new_fact(user_id: str, draft: FactDraft, source: str, confirmed: bool) -> dict:
    now = utcnow()
    return {
        "_id": str(uuid4()), "user_id": user_id, **draft.model_dump(),
        "confirmed": confirmed, "source": source, "created_at": now, "updated_at": now,
    }


async def add_facts(
    database, user_id: str, drafts: list[FactDraft], source: str, confirmed: bool = False,
) -> list[dict]:
    documents = [new_fact(user_id, draft, source, confirmed) for draft in drafts]
    if documents:
        await database.facts.insert_many(documents)
        await sync_profile_tags(database, user_id)
    return documents


async def revise_fact(database, user_id: str, revision: FactRevision) -> dict | None:
    """Apply the AI's refinement of one of this member's facts."""
    fact = await database.facts.find_one({"_id": revision.fact_id, "user_id": user_id})
    if fact is None:
        return None
    changes = revision.model_dump(exclude={"fact_id"}, exclude_none=True)
    if fact["confirmed"]:
        # The member already approved this fact: the AI may refine wording, never re-share it.
        changes.pop("visibility", None)
    if not changes:
        return fact
    changes["updated_at"] = utcnow()
    changes["confirmed"] = False  # changed wording goes back to the member for a look
    await database.facts.update_one({"_id": fact["_id"]}, {"$set": changes})
    await sync_profile_tags(database, user_id)
    return {**fact, **changes}


async def edit_fact(database, user_id: str, fact_id: str, edit: FactEdit) -> dict | None:
    """Apply a member's own edit; any edit also counts as approving the fact."""
    fact = await database.facts.find_one({"_id": fact_id, "user_id": user_id})
    if fact is None:
        return None
    changes = {**edit.model_dump(exclude_none=True), "confirmed": True, "updated_at": utcnow()}
    if "text" in changes:
        changes["source"] = "member_edit"
    await database.facts.update_one({"_id": fact_id}, {"$set": changes})
    await sync_profile_tags(database, user_id)
    return {**fact, **changes}


async def delete_fact(database, user_id: str, fact_id: str) -> bool:
    result = await database.facts.delete_one({"_id": fact_id, "user_id": user_id})
    if result.deleted_count:
        await sync_profile_tags(database, user_id)
    return bool(result.deleted_count)


# ---------------------------------------------------------------- reading facts

async def member_facts(database, user_id: str) -> list[dict]:
    cursor = database.facts.find({"user_id": user_id}).sort("created_at", 1)
    return await cursor.to_list(length=None)


def fact_out(fact: dict) -> FactOut:
    return FactOut.model_validate({**fact, "id": fact["_id"]})


def shared_fact(fact: dict) -> SharedFact:
    return SharedFact.model_validate({**fact, "id": fact["_id"]})


async def can_see_matches_only(database, owner_id: str, viewer_id: str) -> bool:
    """Whether viewer may see owner's matches_only facts.

    Integration point: once connections (Ellie's branch) and matches are merged, return
    True for an accepted connection or a match shown to either member. Until then, only
    public facts are shared, which is the safe default.
    """
    return False


async def visible_facts(database, owner_id: str, viewer_id: str) -> list[dict]:
    facts = await member_facts(database, owner_id)
    if owner_id == viewer_id:
        return facts
    allowed = {"public"}
    if await can_see_matches_only(database, owner_id, viewer_id):
        allowed.add("matches_only")
    return [fact for fact in facts if fact["visibility"] in allowed]


# ---------------------------------------------------------------- Markdown view

def headline(core: dict) -> str:
    parts = [f"{ROLE_LABELS[core['role']]} at CWRU", core["school"]]
    if core.get("grad_year"):
        parts.append(f"Class of {core['grad_year']}")
    if core.get("majors"):
        parts.append(", ".join(core["majors"]))
    parts.append(core["location"])
    return " · ".join(parts)


def fact_line(fact: dict, mark_visibility: bool) -> str:
    line = f"- {fact['text']}"
    extras = [f"{item['key']}: {item['value']}" for item in fact.get("detail", [])]
    if fact.get("strength"):
        extras.insert(0, f"{'priority' if fact['kind'] == 'need' else 'depth'} {fact['strength']}/3")
    if extras:
        line += f" ({'; '.join(extras)})"
    if fact.get("links"):
        line += " " + " ".join(f"`{key}`" for key in fact["links"])
    if mark_visibility and fact["visibility"] != "public":
        line += f" [{fact['visibility'].replace('_', ' ')}]"
    return line


def render_profile_md(name: str, core: dict | None, facts: list[dict], mark_visibility: bool = True) -> str:
    """Plain-code Markdown built from facts, so it can never disagree with them."""
    lines = [f"# {name}"]
    if core:
        lines += ["", headline(core)]
    for kind, title in FACT_SECTIONS.items():
        section = [fact for fact in facts if fact["kind"] == kind]
        if section:
            lines += ["", f"## {title}", *(fact_line(fact, mark_visibility) for fact in section)]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- for other features

async def profile_for(database, user_id: str) -> dict | None:
    return await database.profiles.find_one({"owner_user_id": user_id})


def context_from(profile: dict, facts: list[dict], mark_visibility: bool) -> dict:
    return {
        "user_id": profile["owner_user_id"], "profile_id": profile["_id"], "name": profile["name"],
        "core": profile.get("core"),
        "facts": [fact_out(fact).model_dump(mode="json") for fact in facts],
        "links": sorted({key for fact in facts for key in fact.get("links", [])}),
        "profile_md": render_profile_md(profile["name"], profile.get("core"), facts, mark_visibility),
    }


async def matching_context(database, user_id: str) -> dict | None:
    """Everything about one member, private facts included. Never send this to a browser."""
    profile = await profile_for(database, user_id)
    if profile is None or not profile.get("core"):
        return None
    return context_from(profile, await member_facts(database, user_id), mark_visibility=True)


async def all_matching_contexts(database) -> list[dict]:
    """Every member who finished the basics form, for a matching run."""
    profiles = await database.profiles.find({"core": {"$exists": True}}).to_list(length=None)
    by_user: dict[str, list[dict]] = {}
    for fact in await database.facts.find({}).sort("created_at", 1).to_list(length=None):
        by_user.setdefault(fact["user_id"], []).append(fact)
    return [
        context_from(profile, by_user.get(profile["owner_user_id"], []), mark_visibility=True)
        for profile in profiles
    ]


async def shareable_context(database, owner_id: str, viewer_id: str) -> dict | None:
    """What may be quoted to viewer about owner: for match reasons, outreach, and emails."""
    profile = await profile_for(database, owner_id)
    if profile is None:
        return None
    facts = await visible_facts(database, owner_id, viewer_id)
    context = context_from(profile, facts, mark_visibility=False)
    context["facts"] = [shared_fact(fact).model_dump() for fact in facts]
    return context


async def link_key_counts(database) -> Counter:
    """How many members share each link key; rare shared keys are stronger signals."""
    members_by_key: dict[str, set[str]] = {}
    async for fact in database.facts.find({}, {"links": 1, "user_id": 1}):
        for key in fact.get("links", []):
            members_by_key.setdefault(key, set()).add(fact["user_id"])
    return Counter({key: len(members) for key, members in members_by_key.items()})


async def search_link_keys(database, query: str, limit: int = 10) -> list[dict]:
    """Existing link keys resembling query, most-shared first, so new keys reuse old spellings."""
    words = [word for word in slug(query).split("-") if word]
    counts = await link_key_counts(database)
    found = [key for key in counts if all(word in key for word in words)]
    found.sort(key=lambda key: (-counts[key], key))
    return [{"key": key, "members": counts[key]} for key in found[:limit]]


# ---------------------------------------------------------------- coverage

def area_status(count: int, good_at: int) -> str:
    return "missing" if count == 0 else "good" if count >= good_at else "started"


def compute_coverage(core: dict | None, facts: list[dict]) -> Coverage:
    """How complete a profile is for matching; shown to the member and sent to the AI."""
    learned = [fact for fact in facts if fact["source"] != "basics_form"]
    by_kind = Counter(fact["kind"] for fact in learned)
    detailed_need = any(fact["kind"] == "need" and len(fact.get("detail", [])) >= 2 for fact in learned)
    statuses = {
        "needs": "good" if detailed_need else area_status(by_kind["need"], 2),
        "offers": "good" if by_kind["offer"] and by_kind["experience"] else area_status(by_kind["offer"], 2),
        "style": area_status(by_kind["preference"] + by_kind["availability"], 2),
        "background": area_status(
            sum(fact["kind"] == "background" or bool(fact.get("links")) for fact in learned), 2,
        ),
        "goals": area_status(by_kind["goal"], 1),
    }
    seeking = (core or {}).get("seeking")
    # Shared background is optional and personal, so it never holds the meter back.
    important = {
        "needs": seeking != "give_help", "offers": seeking != "get_help",
        "style": True, "background": False, "goals": True,
    }
    scored = [STATUS_SCORE[statuses[area]] for area in statuses if important[area]]
    return Coverage(
        percent=round(sum(scored) / len(scored)),
        areas=[
            AreaCoverage(area=area, label=AREA_LABELS[area], status=status, important=important[area])
            for area, status in statuses.items()
        ],
    )


# ---------------------------------------------------------------- basics form and profile

def link(kind: str, value: object) -> list[str]:
    # Free text like "!!!" has no usable slug; skip the key rather than reject the form.
    return [f"{kind}:{slug(str(value))}"] if slug(str(value)) else []


def basics_drafts(form: BasicsForm) -> list[FactDraft]:
    """The basics form, restated as confirmed facts so the fact store is complete on its own."""
    role = ROLE_LABELS[form.role]
    year = f", class of {form.grad_year}" if form.grad_year else ""
    drafts = [
        FactDraft(
            kind="background", topic="CWRU", text=f"{role} at CWRU, {form.school}{year}",
            links=link("school", f"cwru {form.school}") + link("class-year", form.grad_year or ""),
            visibility="public", confidence=1,
        ),
        FactDraft(
            kind="preference", topic="mentoring", text=SEEKING_TEXT[form.seeking],
            visibility="public", confidence=1,
        ),
        FactDraft(
            kind="background", topic="location", text=f"Based in {form.location}",
            links=link("city", form.location), visibility="public", confidence=1,
        ),
    ]
    if form.majors:
        drafts.insert(1, FactDraft(
            kind="background", topic="studies", text=f"Studies {' and '.join(form.majors)}",
            links=[key for major in form.majors for key in link("major", major)],
            visibility="public", confidence=1,
        ))
    return drafts


async def save_basics(database, user: dict, form: BasicsForm) -> dict:
    """Create or update the member's profile from the basics form and refresh its facts."""
    core = form.model_dump()
    affiliation = f"CWRU {ROLE_LABELS[form.role].lower()} · {form.school}"
    profile = await profile_for(database, user["_id"])
    if profile is None:
        profile = {
            "_id": str(uuid4()), "owner_user_id": user["_id"], "name": user["name"],
            "affiliation": affiliation, "location": form.location, "expertise": [], "interests": [],
            "core": core,
        }
        await database.profiles.insert_one(profile)
    else:
        changes = {"affiliation": affiliation, "location": form.location, "core": core}
        await database.profiles.update_one({"_id": profile["_id"]}, {"$set": changes})
        profile = {**profile, **changes}
    await database.facts.delete_many({"user_id": user["_id"], "source": "basics_form"})
    await add_facts(database, user["_id"], basics_drafts(form), "basics_form", confirmed=True)
    return profile


def unique_topics(facts: list[dict], kind: str) -> list[str]:
    topics: dict[str, str] = {}
    for fact in facts:
        if fact["kind"] == kind and fact["visibility"] == "public":
            topics.setdefault(fact["topic"].casefold(), fact["topic"])
    return list(topics.values())[:MAX_PROFILE_TAGS]


async def sync_profile_tags(database, user_id: str):
    """Keep the directory card's expertise and interests in step with public facts.

    A list is only replaced once there is at least one public fact of that kind, so
    tags typed into the older profile editor survive until the interview has better ones.
    """
    facts = await member_facts(database, user_id)
    changes = {}
    if offers := unique_topics(facts, "offer"):
        changes["expertise"] = offers
    if needs := unique_topics(facts, "need"):
        changes["interests"] = needs
    if changes:
        await database.profiles.update_one({"owner_user_id": user_id}, {"$set": changes})
