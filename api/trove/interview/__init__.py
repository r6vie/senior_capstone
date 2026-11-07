"""Finding the member's book: the AI interview, optional résumé reading, and the three-title
reveal (docs/trove.md §4).

Owns the `interviews` collection. The engine (`engine.py`, owned by Trove AI) writes the questions
and the book; `service.py` keeps the state and creates the book through `trove.books.service`.
"""
