from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from pymongo.asynchronous.database import AsyncDatabase

from trove.auth.service import full_names_of, get_current_user
from trove.core.database import get_database
from trove.meetings import service
from trove.meetings.models import ConfirmRequest, DetailsUpdate, MeetingView, TimesUpdate
from trove.meetings.service import MeetingRefused
from trove.notifications.service import notify_meeting_reminder

router = APIRouter(prefix="/meetings", tags=["Meetings"])


def refused(error: MeetingRefused) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=error.detail)


async def view(database: AsyncDatabase, checkout: dict, meeting: dict | None, user_id: str) -> MeetingView:
    other = service.other_person(checkout, user_id)
    name = (await full_names_of(database, [other])).get(other) or "a former member"
    return MeetingView(
        checkout_id=checkout["_id"],
        book_title=checkout["book_title"],
        other_name=name,
        **service.view_parts(meeting, checkout, user_id, datetime.now(UTC)),
    )


async def send_reminders(database: AsyncDatabase) -> None:
    """Remind both people about meetings starting within a day; each reminder goes out once.

    There is no scheduled job yet, so this runs whenever anyone opens a meeting page.
    """
    meetings = await service.due_reminders(database, datetime.now(UTC))
    for meeting in meetings:
        names = await full_names_of(database, [meeting["reader_id"], meeting["author_id"]])
        for person, other in (
            (meeting["reader_id"], meeting["author_id"]),
            (meeting["author_id"], meeting["reader_id"]),
        ):
            await notify_meeting_reminder(
                database,
                checkout_id=meeting["_id"],
                user_id=person,
                other_name=names.get(other, "a former member"),
                book_title=meeting["book_title"],
                start=meeting["start"].replace(tzinfo=UTC),
                video_link=meeting.get("video_link"),
                place_note=meeting.get("place_note"),
            )


@router.get("/{checkout_id}", response_model=MeetingView)
async def get_meeting(
    checkout_id: str,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> MeetingView:
    """The times each of you offered, where they overlap, and the confirmed meeting if there is one."""
    try:
        checkout = await service.accepted_checkout(database, checkout_id, user["_id"])
    except MeetingRefused as error:
        raise refused(error) from None
    background_tasks.add_task(send_reminders, database)
    return await view(database, checkout, await service.get_meeting(database, checkout_id), user["_id"])


@router.put("/{checkout_id}/times", response_model=MeetingView)
async def offer_times(
    checkout_id: str,
    data: TimesUpdate,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> MeetingView:
    """Replace the times you offer (up to five, 30 minutes each). Send none to take them back."""
    try:
        checkout = await service.accepted_checkout(database, checkout_id, user["_id"])
        meeting = await service.offer_times(database, checkout, user["_id"], data.times, datetime.now(UTC))
    except MeetingRefused as error:
        raise refused(error) from None
    return await view(database, checkout, meeting, user["_id"])


@router.put("/{checkout_id}/confirm", response_model=MeetingView)
async def confirm(
    checkout_id: str,
    data: ConfirmRequest,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> MeetingView:
    """Settle on one of the offered times. Either of you can."""
    try:
        checkout = await service.accepted_checkout(database, checkout_id, user["_id"])
        meeting = await service.confirm(database, checkout, user["_id"], data.start, datetime.now(UTC))
    except MeetingRefused as error:
        raise refused(error) from None
    return await view(database, checkout, meeting, user["_id"])


@router.put("/{checkout_id}/details", response_model=MeetingView)
async def set_details(
    checkout_id: str,
    data: DetailsUpdate,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> MeetingView:
    """The video link and, if you're both nearby, a place to meet."""
    try:
        checkout = await service.accepted_checkout(database, checkout_id, user["_id"])
        meeting = await service.set_details(
            database, checkout, data.video_link, data.place_note, datetime.now(UTC)
        )
    except MeetingRefused as error:
        raise refused(error) from None
    return await view(database, checkout, meeting, user["_id"])


@router.get("/{checkout_id}/invite.ics", response_class=Response)
async def invite(
    checkout_id: str,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> Response:
    """A calendar file for the confirmed meeting."""
    try:
        checkout = await service.accepted_checkout(database, checkout_id, user["_id"])
    except MeetingRefused as error:
        raise refused(error) from None
    meeting = await service.get_meeting(database, checkout_id)
    if not meeting or not meeting.get("start"):
        raise HTTPException(status_code=404, detail="No time has been confirmed yet.")
    name = (await view(database, checkout, meeting, user["_id"])).other_name
    return Response(
        service.calendar_invite(checkout, meeting, name),
        media_type="text/calendar",
        headers={"Content-Disposition": 'attachment; filename="trove-meeting.ics"'},
    )
