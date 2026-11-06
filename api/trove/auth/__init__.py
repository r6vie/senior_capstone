"""Accounts and sign-in: email + password, revocable bearer sessions, and attempt limits.

Owns the `users`, `sessions` and `auth_attempts` collections. Other features get the signed-in
user with `Depends(get_current_user)` from `trove.auth.service`; they never read these
collections directly.

Open product question (docs/trove.md §2): how CWRU membership is verified.
"""
