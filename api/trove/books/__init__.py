"""The book: one per member. Title, author's full name, cover and chapters (docs/trove.md §3).

Owns the `books` collection. Other features use the contract functions in `trove.books.service`:
`get_public_book`, `get_book_of` and `list_shelf`. Readers see the author's full name, but never
their employer, title, links, contact details or copy counts.

Sample books for development live in `samples.py`; `python3 scripts/seed.py` adds them.
"""
