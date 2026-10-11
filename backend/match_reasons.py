"""The one place matching plugs into the emails.

match_reasons(viewer, other) returns plain-English reasons why `viewer` would want to meet
`other`, for example ["Taylor has experience in Medical devices, which you're interested in"].
Both arguments are public profile dicts (name, affiliation, location, expertise, interests).

This is a placeholder that returns nothing, so emails simply leave out the "why" section and
show the other person's profile summary instead. Whoever builds the matching algorithm
replaces the body of this function; no email code needs to change.

For a periodic "people worth meeting" email, the template already exists:

    from email_templates import Suggestion, match_digest
    from notifications import frontend_url, notify_once

    email = match_digest(profile, [Suggestion(person, reasons), ...], frontend_url())
    await notify_once(database, f"digest:{user_id}:{today}", user_id, email.render)

Skip members with no suggestions (match_digest refuses to build an empty email), and run it
from a scheduled script rather than the web server so each member gets it only once.
"""


def match_reasons(viewer: dict, other: dict) -> list[str]:
    return []
