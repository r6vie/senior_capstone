"""Accounts and sign-in: email + password, revocable bearer sessions, and attempt limits.

Also the member's settings: the contact details shared on a yes (`contact_details_of`), the
email switch, and deleting the account (other features clean up through `on_account_deleted`).

Owns the `users`, `sessions` and `auth_attempts` collections. Other features get the signed-in
user with `Depends(get_current_user)` from `trove.auth.service`; they never read these
collections directly.

Open product question (docs/trove.md §2): how CWRU membership is verified.
"""
