"""Keeping résumé facts out of the book, without keeping the résumé (docs/trove.md §4).

A résumé guides questions, so its words can reach a question. Book-writing reads those questions, so
a company named only in the résumé could end up in the book. To stop that, the proper nouns and years
in the résumé are kept as salted hashes: enough to recognize a word, not to read one. The résumé text
itself is deleted on its own schedule.
"""

import hashlib
import re

# Capitalized words too ordinary to count: headings, months, titles, and this app's own setting.
COMMON = frozenset(
    "a an and at by for from in of on or the to with i we my our "  # noqa: SIM905
    "about activities address awards bachelor bs ba ms phd certifications contact coursework education email "
    "experience gpa honors interests languages leadership linkedin master objective phone present profile "
    "projects publications references research resume skills summary technical volunteer work "
    "january february march april may june july august september october november december "
    "jan feb mar apr jun jul aug sep sept oct nov dec spring summer fall autumn winter "
    "assistant associate director engineer intern lead manager member president senior junior student "
    "case western reserve university cwru cleveland ohio".split()
)
REDACTED = "that one"
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9&-]*|(?:19|20)\d\d")
_YEAR = re.compile(r"(?:19|20)\d\d\Z")


def _hash(word: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{word.casefold()}".encode()).hexdigest()


def _is_term(word: str) -> bool:
    if _YEAR.match(word):
        return True
    return word[0].isupper() and word.casefold() not in COMMON


def resume_terms(text: str, salt: str) -> list[str]:
    """Hashes of the résumé's proper nouns and years. A capitalized first word of a line is usually a
    verb ("Built…"), so it counts only when the next word is capitalized too ("Acme Corp")."""
    terms = set()
    for line in text.splitlines():
        words = _WORD.findall(line)
        for index, word in enumerate(words):
            if index == 0 and not _YEAR.match(word) and not (len(words) > 1 and _is_term(words[1])):
                continue
            if _is_term(word):
                terms.add(_hash(word, salt))
    return sorted(terms)


def only_in_resume(terms: list[str], answers: list[str], salt: str) -> set[str]:
    """The terms the member never said themselves. Anything they said is theirs to use."""
    said = {_hash(word, salt) for answer in answers for word in _WORD.findall(answer)}
    return set(terms) - said


def redact(question: str, terms: set[str], salt: str) -> str:
    """The question with those terms taken out."""
    replaced = _WORD.sub(
        lambda found: REDACTED if _is_term(found[0]) and _hash(found[0], salt) in terms else found[0],
        question,
    )
    return re.sub(rf"{REDACTED}(?:[ ,]+{REDACTED})+", REDACTED, replaced)


def mentions(text: str, terms: set[str], salt: str) -> bool:
    return any(_is_term(word) and _hash(word, salt) in terms for word in _WORD.findall(text))
