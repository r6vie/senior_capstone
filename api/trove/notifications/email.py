"""The layout every email shares. A new email is a function that returns an `Email`; no HTML to write.

Anything a member typed (names, messages) is escaped in the HTML version.
"""

from dataclasses import dataclass, field
from html import escape

ACCENT = "#0b5c6b"
MUTED = "#5d6b7c"
BORDER = "#d9dee5"


@dataclass
class Section:
    title: str
    items: list[str] = field(default_factory=list)


@dataclass
class Email:
    subject: str
    heading: str
    paragraphs: list[str]
    button_text: str
    button_url: str
    quote: str | None = None  # something another member wrote, shown as a block quote
    sections: list[Section] = field(default_factory=list)
    show_unsubscribe: bool = True  # False for account emails every member needs

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
            parts.append(
                f"<blockquote style='margin:1rem 0;padding-left:1rem;border-left:3px solid {BORDER}'>"
                f"{escape(self.quote)}</blockquote>"
            )
        for section in self.sections:
            bullets = "".join(f"<li>{escape(item)}</li>" for item in section.items)
            parts.append(
                f"<p><strong>{escape(section.title)}</strong></p>"
                + (f"<ul>{bullets}</ul>" if bullets else "")
            )
        parts.append(
            f"<p><a href='{escape(self.button_url)}' style='display:inline-block;background:{ACCENT};color:#fff;"
            "padding:.7rem 1.2rem;border-radius:6px;text-decoration:none;font-weight:600'>"
            f"{escape(self.button_text)}</a></p>"
        )
        if self.show_unsubscribe:
            parts.append(
                f"<p style='font-size:.8rem;color:{MUTED}'>You get these emails because you have a Trove "
                f"account. <a href='{escape(unsubscribe_url)}'>Unsubscribe</a></p>"
            )
        return (
            "<div style='font-family:system-ui,Segoe UI,sans-serif;max-width:32rem;margin:auto;color:#1b2430'>"
            + "".join(parts)
            + "</div>"
        )
