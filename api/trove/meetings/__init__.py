"""Arranging the reading: shared times, calendar invite, video link and reminders
(docs/trove.md §7, §9.7).

Owns the `meetings` collection: one document per accepted checkout, keyed by the checkout id.
Calls `checkouts.get_checkout_for`, so only the two people on a checkout can see their meeting.
"""
