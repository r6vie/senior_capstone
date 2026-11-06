"""The book: one per member. Title, author's first name, cover and chapters (docs/trove.md §3).

Owns the `books` collection. Other features use the contract functions in `trove.books.service`:
`get_public_book`, `get_book_of` and `list_shelf`. Readers only ever see the author's first name:
never a last name, contact details or copy counts.

Sample books for development live in `samples.py`; `python3 scripts/seed.py` adds them.
"""
