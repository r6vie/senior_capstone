"""The wording of each email Trove sends. Keep each one short and in the product's voice."""

from trove.notifications.email import Email


def checkout_requested(
    reader_name: str, book_title: str, message: str, checkouts_url: str, answer_days: int
) -> Email:
    return Email(
        subject=f"{reader_name} would like to check out your book",
        heading="Someone would like to check out your book",
        paragraphs=[
            f'{reader_name} would like to check out "{book_title}". Here is their note:',
            f"If you don't answer within {answer_days} days, the checkout closes quietly.",
        ],
        quote=message,
        button_text="Accept or decline",
        button_url=checkouts_url,
    )


def verification_code(code: str, verify_url: str) -> Email:
    return Email(
        subject=f"Your Trove code: {code}",
        heading="Confirm your case.edu email",
        paragraphs=[
            f"Your code is {code}.",
            "It works for 15 minutes. If you didn't sign up for Trove, ignore this email.",
        ],
        button_text="Enter your code",
        button_url=verify_url,
        show_unsubscribe=False,
    )


def welcome(first_name: str, app_url: str) -> Email:
    return Email(
        subject="Welcome to Trove",
        heading="Welcome to Trove",
        paragraphs=[f"Hi {first_name},", "Your account is ready. Next: find the book you'd write."],
        button_text="Open Trove",
        button_url=app_url,
    )


def meeting_reminder(
    other_name: str,
    book_title: str,
    when: str,
    meeting_url: str,
    video_link: str | None,
    place_note: str | None,
) -> Email:
    paragraphs = [f'You are meeting {other_name} about "{book_title}" on {when}.']
    if video_link:
        paragraphs.append(f"Video link: {video_link}")
    if place_note:
        paragraphs.append(f"Where: {place_note}")
    return Email(
        subject=f"Reminder: you meet {other_name} soon",
        heading="Your meeting is coming up",
        paragraphs=paragraphs,
        button_text="See the details",
        button_url=meeting_url,
    )
