"""Email: one layout for every message, at-most-once delivery, and signed unsubscribe links.

Owns the `notifications` collection. Features send email by adding a template to
`templates.py` and a `notify_*` function to `service.py`, then calling it from their router
(usually as a FastAPI background task, so email trouble never fails the request).
"""
