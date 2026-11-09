from trove.interview import resume_terms

RESUME = """Dana Whitfield
Experience
Brindle Foods LLC, Operations Lead, 2019 to 2021
Built the night shift schedule at the Akron plant
Education
Case Western Reserve University, 2023
"""
SALT = "interview-1"


def terms() -> list[str]:
    return resume_terms.resume_terms(RESUME, SALT)


def test_terms_are_hashes_so_the_resume_cant_be_read_back():
    joined = " ".join(terms())
    assert "Brindle" not in joined
    assert "brindle" not in joined
    assert "2019" not in joined


def test_a_resume_only_term_is_redacted_from_a_question():
    only = resume_terms.only_in_resume(terms(), ["I ran the night shift."], SALT)
    question = "What happened at Brindle Foods in 2019, when you left?"
    assert (
        resume_terms.redact(question, only, SALT) == "What happened at that one in that one, when you left?"
    )


def test_a_term_the_member_said_is_theirs():
    only = resume_terms.only_in_resume(terms(), ["I worked at Brindle for two years."], SALT)
    assert "Brindle" in resume_terms.redact("How was Brindle?", only, SALT)
    assert not resume_terms.mentions("Brindle taught me.", only, SALT)
    assert resume_terms.mentions("Foods taught me.", only, SALT)


def test_ordinary_words_and_the_campus_arent_terms():
    only = resume_terms.only_in_resume(terms(), [], SALT)
    assert not resume_terms.mentions("Education and Experience at Case Western in the Fall.", only, SALT)
    # "Built" starts a line, which is usually a verb and not a name.
    assert not resume_terms.mentions("Built it myself.", only, SALT)


def test_output_is_checked_for_terms():
    only = resume_terms.only_in_resume(terms(), [], SALT)
    assert resume_terms.mentions("The moment Brindle felt like a business.", only, SALT)
    assert resume_terms.mentions("I left in 2021.", only, SALT)
    assert not resume_terms.mentions("I left the following spring.", only, SALT)


def test_a_different_interview_has_different_hashes():
    assert set(terms()).isdisjoint(resume_terms.resume_terms(RESUME, "interview-2"))


def test_a_first_word_set_apart_by_punctuation_is_a_term():
    terms_found = resume_terms.resume_terms("Gopala, Cleveland\nBuilt the schedule", SALT)
    only = resume_terms.only_in_resume(terms_found, [], SALT)
    assert resume_terms.mentions("Gopala taught me.", only, SALT)
    assert not resume_terms.mentions("Built it myself.", only, SALT)
