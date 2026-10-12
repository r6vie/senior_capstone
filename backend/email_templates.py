"""Email wording and layout.

Every email is an `Email`: a subject, a heading, some paragraphs, optional sections of
bullet points, and one button. `render()` produces the plain-text and HTML versions, so a
new kind of email is a short function that builds an `Email`, with no HTML to write.
Anything a member typed (names, notes) is escaped in the HTML.
"""

from dataclasses import dataclass, field
from html import escape


def first_name(full_name: str) -> str:
    return full_name.split()[0]


@dataclass
class Suggestion:
    """One person recommended to a member, with plain-English reasons (the list may be empty).

    The matching code produces these; the digest template only displays them.
    """

    profile: dict
    reasons: list[str] = field(default_factory=list)


@dataclass
class Section:
    title: str
    items: list[str] = field(default_factory=list)
    card: bool = False  # draw a box around it (used for each person in a digest)


@dataclass
class Email:
    subject: str
    heading: str
    paragraphs: list[str]
    button_text: str
    button_url: str
    quote: str | None = None  # a personal note written by another member
    sections: list[Section] = field(default_factory=list)
    show_unsubscribe: bool = True  # False for account emails, which every member needs

    def render(self, unsubscribe_url: str) -> tuple[str, str, str]:
        """Return (subject, plain_text, html)."""
        return self.subject, self._text(unsubscribe_url), self._html(unsubscribe_url)

    def _text(self, unsubscribe_url: str) -> str:
        lines: list[str] = []
        for paragraph in self.paragraphs:
            lines += [paragraph, ""]
        if self.quote:
            lines += [f'"{self.quote}"', ""]
        for section in self.sections:
            lines.append(section.title + (":" if section.items else ""))
            lines += [f"- {item}" for item in section.items]
            lines.append("")
        lines.append(f"{self.button_text}: {self.button_url}")
        if self.show_unsubscribe:
            lines += ["", f"Unsubscribe from these emails: {unsubscribe_url}"]
        return "\n".join(lines)

    def _html(self, unsubscribe_url: str) -> str:
        parts = [f"<h2 style='margin-bottom:.5rem'>{escape(self.heading)}</h2>"]
        parts += [f"<p>{escape(paragraph)}</p>" for paragraph in self.paragraphs]
        if self.quote:
            parts.append("<blockquote style='margin:1rem 0;padding-left:1rem;border-left:3px solid #d9dee5'>"
                         f"{escape(self.quote)}</blockquote>")
        for section in self.sections:
            bullets = ("<ul>" + "".join(f"<li>{escape(item)}</li>" for item in section.items) + "</ul>"
                       if section.items else "")
            if section.card:
                parts.append("<div style='border:1px solid #d9dee5;border-radius:8px;padding:.8rem 1rem;margin:.8rem 0'>"
                             f"<strong>{escape(section.title)}</strong>{bullets}</div>")
            else:
                parts.append(f"<p><strong>{escape(section.title)}</strong></p>{bullets}")
        parts.append(
            f"<p><a href='{escape(self.button_url)}' style='display:inline-block;background:#0b5c6b;color:#fff;"
            "padding:.7rem 1.2rem;border-radius:6px;text-decoration:none;font-weight:600'>"
            f"{escape(self.button_text)}</a></p>"
        )
        if self.show_unsubscribe:
            parts.append("<p style='font-size:.8rem;color:#5d6b7c'>You get these emails because you have a "
                         f"FoundersCircle account. <a href='{escape(unsubscribe_url)}'>Unsubscribe</a></p>")
        return ("<div style='font-family:system-ui,Segoe UI,sans-serif;max-width:32rem;margin:auto;color:#1b2430'>"
                + "".join(parts) + "</div>")


# ---- The emails ----------------------------------------------------------------------------

def about(person: dict) -> Section | None:
    """A factual summary taken straight from the profile; no matching involved."""
    items = []
    if person["expertise"]:
        items.append("Expertise: " + ", ".join(person["expertise"]))
    if person["interests"]:
        items.append("Interests: " + ", ".join(person["interests"]))
    return Section(f"About {first_name(person['name'])}", items) if items else None


def _optional(*sections: Section | None) -> list[Section]:
    return [section for section in sections if section is not None]


def verify_email(name: str, verify_url: str) -> Email:
    return Email(
        subject="Confirm your email for FoundersCircle",
        heading="Confirm your email",
        paragraphs=[f"Hi {first_name(name)},",
                    "Press the button to confirm this email address and finish creating your account. "
                    "The link works for 24 hours.",
                    "If you didn't sign up for FoundersCircle, you can ignore this email."],
        button_text="Confirm email", button_url=verify_url, show_unsubscribe=False,
    )


def welcome(name: str, app_url: str) -> Email:
    return Email(
        subject="Welcome to FoundersCircle",
        heading="Welcome to FoundersCircle",
        paragraphs=[f"Hi {first_name(name)},",
                    "Your account is ready. Create your profile so other members can find you and ask to connect."],
        button_text="Create your profile", button_url=app_url,
    )


# Wording for each request type: (subject, heading, "sent you ...", noun for the accepted email).
# Keep the keys in step with RequestType in connection_models.py (a test checks this).
REQUEST_WORDING = {
    "mentorship": ("{name} would like you as a mentor", "{name} is asking for mentorship",
                   "a mentorship request", "mentorship"),
    "career_advice": ("{name} is asking for your career advice", "{name} wants career advice",
                      "a request for career advice", "career advice"),
    "introduction": ("{name} would like an introduction", "{name} would like an introduction",
                     "an introduction request", "introduction"),
    "collaboration": ("{name} would like to collaborate with you", "{name} wants to collaborate",
                      "a collaboration request", "collaboration"),
    "other": ("{name} wants to connect with you on FoundersCircle", "{name} wants to connect",
              "a connection request", "connection"),
}


def _wording(request_type: str) -> tuple[str, str, str, str]:
    return REQUEST_WORDING.get(request_type, REQUEST_WORDING["other"])


def connection_request(
    recipient: dict, sender: dict, note: str | None, reasons: list[str], app_url: str,
    request_type: str = "other",
) -> Email:
    """`recipient` and `sender` are profiles. `reasons` come from the matching code and may be empty."""
    name = first_name(sender["name"])
    subject, heading, what, _ = _wording(request_type)
    return Email(
        subject=subject.format(name=name),
        heading=heading.format(name=name),
        paragraphs=[f"Hi {first_name(recipient['name'])},",
                    f"{sender['name']} ({sender['affiliation']}, {sender['location']}) sent you {what}.",
                    f"If you accept, you and {name} will be able to see each other's email address."],
        quote=note,
        sections=_optional(Section("Why it could be a good fit", reasons) if reasons else None, about(sender)),
        button_text="View request", button_url=app_url,
    )


def connection_accepted(
    recipient: dict, accepter: dict, reasons: list[str], app_url: str, request_type: str = "other",
    contact_email: str | None = None,
) -> Email:
    """`recipient` sent the request; `accepter` said yes and agreed to share `contact_email`."""
    name = first_name(accepter["name"])
    contact = Section(f"How to reach {name}", [contact_email]) if contact_email else None
    return Email(
        subject=f"{name} accepted your {_wording(request_type)[3]} request",
        heading=f"You're connected with {name}",
        paragraphs=[f"Hi {first_name(recipient['name'])},", f"You're now connected with {accepter['name']}."],
        sections=_optional(contact, Section("Conversation starters", reasons) if reasons else None, about(accepter)),
        button_text="Say hello", button_url=app_url,
    )


def new_message(recipient: dict, sender: dict, body: str, app_url: str) -> Email:
    """Someone wrote in a request's conversation. `recipient` and `sender` are profiles."""
    name = first_name(sender["name"])
    return Email(
        subject=f"{name} sent you a message on FoundersCircle",
        heading=f"New message from {name}",
        paragraphs=[f"Hi {first_name(recipient['name'])},", f"{sender['name']} wrote:"],
        quote=body,
        button_text="Reply", button_url=app_url,
    )


def match_digest(recipient: dict, suggestions: list[Suggestion], app_url: str) -> Email:
    """Ready for the matching code: pass it ranked suggestions. Not sent by anything yet."""
    if not suggestions:
        raise ValueError("Do not send an empty digest; skip members with no suggestions.")
    lead = first_name(suggestions[0].profile["name"])
    extra = f" (plus {len(suggestions) - 1} more)" if len(suggestions) > 1 else ""
    return Email(
        subject=f"{lead} could be a great connection{extra}",
        heading="New people for you",
        paragraphs=[f"Hi {first_name(recipient['name'])}, here are people worth meeting:"],
        sections=[
            Section(f"{s.profile['name']} ({s.profile['affiliation']}, {s.profile['location']})", s.reasons, card=True)
            for s in suggestions
        ],
        button_text="See your matches", button_url=app_url,
    )
