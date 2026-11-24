"""Finding books: shelves by category, smart search, "the Librarian recommends" and
recommending a book to someone (docs/trove.md §5).

Owns `recommendations`, the signed-in member's short-lived, grounded Librarian pick. Claude chooses
among eligible books using author-approved public text; discovery validates the choice and evidence.
Reads book content through `trove.books`; it never reads the books collection directly. Legacy
`match_profiles` records are touched only for account-deletion cleanup.
"""
