"""Finding the member's book: the AI interview, optional résumé reading, the three-title reveal,
and growing the book afterwards: adding to it, sparks, and the question after a reading (docs/trove.md §4).

Owns the `interviews`, `sparks` and `reading_questions` collections. The engine (`engine.py`, owned by Trove AI) writes the questions
and the book; `service.py` keeps the state and creates the book through `trove.books.service`.
"""
