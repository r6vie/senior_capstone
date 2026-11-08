"""Checking out a book: check out with a message, cancel, accept or decline (docs/trove.md §6, §9.6).

Owns the `checkouts` collection. Other features use the contract functions in
`trove.checkouts.service`: `get_checkout_for` (messaging, meetings) and `fully_checked_out` (the
shelf hides books whose copies are all out). Readers never see copy or checkout counts.

Not built yet: the reveal on accept (C2), messages (C3), "Did you meet?" and returning a copy (C4).
"""
