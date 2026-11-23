"""Finding books: shelves by category, smart search, "the Librarian recommends" and
recommending a book to someone (docs/trove.md §5).

Owns `recommendations`, the signed-in member's short-lived Librarian pick, and `match_profiles`,
the grounded signals extracted from public book text. Reads book content through `trove.books`;
it never reads the books collection directly.
"""
