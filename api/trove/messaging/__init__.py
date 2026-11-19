"""The message thread inside each checkout (docs/trove.md §6, §9.8). No messages outside a checkout.

Owns the `messages` and `message_threads` collections. A thread opens when the author accepts; the
reader's checkout note is shown as its first message. Other features use `trove.messaging.service`:
`post_note` (a short app note, such as a confirmed meeting time) and `checkouts_with_new_messages`
(the private "New message" marker).
"""
