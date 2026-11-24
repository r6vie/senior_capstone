"""When the Librarian stops: answers about grief, illness, family trouble and the like get no marks
and no notebook entries (docs/librarian-plan.md, Silence; docs/LIBRARIAN_SPEC.md §4).

Silence is about what an answer is *about*, so the patterns name the subject, not a passing word:
"I miss my mom's lasagna" is a food story. The client runs its own copy of this list so it can go quiet
before any call; this one is the server's layer, and the model can also declare an answer silent.
Missing a joke costs nothing, so when in doubt the pattern errs towards silence.
"""

import re

# Phrases that look like a silent subject and aren't. Blanked out before matching.
HARMLESS = [
    r"oh my god",
    r"death metal",
    r"bored to death",
    r"scared to death",
    r"to death",
    r"dying to",
    r"killing me",
    r"killing it",
    r"killed it",
    r"chronically online",
    r"dead serious",
    r"dead end",
    r"deadline",
    r"dead tired",
    r"drop[- ]dead",
    r"heart of the",
    r"broke(n)? the (build|record|story|news)",
    r"came out (of|on|in|to be|with|fine|well|better|worse|great|late|early|ahead|okay|ok|right)",
    r"transition(ed|ing)? (to|from|into|between)",
]

# Each names a subject that makes an answer silent.
SUBJECTS = {
    "grief or death": r"\b(died|dying|death|deaths|passed away|passing of|funeral|funerals|grief|grieving"
    r"|grieve|bereave\w*|miscarr\w*|stillborn|lost my (mom|dad|mother|father|brother|sister|son|daughter"
    r"|wife|husband|partner|grand\w+|aunt|uncle|cousin|friend|best friend|baby)|suicide|killed (himself"
    r"|herself|themselves))\b",
    "illness": r"\b(cancer|chemo\w*|tumou?r|diagnosed with|terminally ill|depress\w+|anxiety disorder|panic attacks?"
    r"|eating disorder|anorexi\w*|bulimi\w*|bipolar|schizo\w*|ptsd|adhd|autis\w+|seizures?|epilep\w+"
    r"|my illness|chronic (illness|pain)|hospitali[sz]ed|was in the hospital|my surgery|rehab"
    r"|addiction|in recovery|relapse\w*|overdos\w+|in therapy|my therapist|mental health|burn(ed|t)? out|burnout"
    r"|disabilit\w+|disabled)\b",
    "family trouble": r"\b(divorc\w+|custody|estranged|kicked (me )?out|disowned|foster (care|home|family)"
    r"|my parents (split|separated|fought)|separated from my|domestic violence)\b",
    "abuse or self-harm": r"\b(abused|abusive|child abuse|sexual abuse|abuse at home|assault\w*|rape\w*"
    r"|molest\w*|self[- ]harm\w*|cutting myself|hurt myself|harass\w+|stalked|stalker|groomed)\b",
    "heartbreak": r"\b(broke up|breakup|break-up|broken heart|heartbr\w+|my ex\b|dumped me|cheated on)\b",
    "sexuality or gender": r"\b(coming out|came out|my sexuality|my gender|gender identity|transgender|trans\b"
    r"|non-?binary|i'?m gay|being gay|lesbian|bisexual|queer|my pronouns)\b",
    "faith as a struggle": r"\b(lost my faith|crisis of faith|left the church|leaving my religion"
    r"|questioning god)\b",
    "legal or immigration status": r"\b(deport\w*|undocumented|visa status|green card|asylum|refugee\w*"
    r"|immigration status|arrested|incarcerat\w+|prison|jail|probation|parole|convicted|lawsuit)\b",
}

_HARMLESS = re.compile("|".join(f"(?:{p})" for p in HARMLESS), re.IGNORECASE)
_SUBJECTS = {name: re.compile(pattern, re.IGNORECASE) for name, pattern in SUBJECTS.items()}
_APOSTROPHES = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"'})


def subject_of(text: str) -> str | None:
    """The silent subject an answer is about, or None."""
    cleaned = _HARMLESS.sub(" ", text.translate(_APOSTROPHES))
    return next((name for name, pattern in _SUBJECTS.items() if pattern.search(cleaned)), None)


def is_silent(text: str) -> bool:
    return subject_of(text) is not None


# How a silent answer appears in any later Librarian prompt: never its words.
MASKED = "(personal; not shown)"
