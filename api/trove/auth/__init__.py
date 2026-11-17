"""Accounts and sign-in: email + password, revocable bearer sessions, and attempt limits.

Also the member's settings: the contact details shared on a yes (`contact_details_of`), the
email switch, and deleting the account (other features clean up through `on_account_deleted`).

Owns the `users`, `sessions`, `auth_attempts` and `invites` collections. Other features get the signed-in
user with `Depends(get_current_user)` from `trove.auth.service`; they never read these
collections directly.

Membership (docs/trove.md §9.2): students confirm a 6-digit code sent to their case.edu email
(`verification.py`); alumni sign up with a single-use invite from a verified member (`invites.py`).
Accounts made before this existed count as verified.
"""
