"""Builds index.html for the shelf directions review from one shared list of sample books.

Run: python3 docs/design/shelf-directions/build.py
Each direction's markup comes from its own section below and its styles from its own CSS file,
so one direction can be lifted out without the others.
"""

from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent

# (title, first name, color slot 1-8, cover ornament, pile offset 1-4). Colors and offsets are
# assigned by Trove, so they carry no meaning about the author.
BOOKS = {
    "hana": ("Why I Turned Down Grad School Twice", "Hana", 6, "dot", 2),
    "dana": ("How to Leave a Job Without Burning the Bridge", "Dana", 1, "rule", 1),
    "marcus": ("Switching Off Pre-Med Before Telling Your Parents", "Marcus", 4, "diamond", 3),
    "luis": ("Teaching Yourself to Code at Thirty-Four", "Luis", 2, "double", 2),
    "jamal": ("Living With an Engineering Degree You Don't Use", "Jamal", 7, "dot", 4),
    "priya": ("What Nineteen-Year-Olds Actually Think of Your App", "Priya", 3, "double", 2),
    "grace": ("How a Hospital Actually Decides What to Buy", "Grace", 8, "rule", 4),
    "noor": ("Getting a Grant Reviewer to Keep Reading", "Noor", 5, "diamond", 1),
    "ben": ("Negotiating a First Offer With No Leverage", "Ben", 6, "rule", 3),
    "aisha": ("Running a Student Org When Nobody Shows Up", "Aisha", 2, "dot", 3),
    "elena": ("The First Ninety Days of Running a Lab", "Elena", 4, "double", 1),
    "ray": ("What Cleveland Taught Me About Starting Small", "Ray", 1, "diamond", 4),
    "rosa": ("Being the First in Your Family to Do Any of This", "Rosa", 3, "rule", 2),
}
PALE = {4, 8}  # cloth colors light enough to need dark lettering

SHELVES = [
    ("Changing course", ["dana", "marcus", "luis", "jamal"]),
    ("How things really work", ["priya", "grace", "noor", "ben"]),
    ("Starting from zero", ["aisha", "elena", "ray", "rosa"]),
]
PICK = "hana"
REASON = "You told the Librarian you're deciding about a PhD. Hana weighed the same choice, twice."
ASK = "What do you want to talk about?"
HINT = "Try: leaving a PhD, a first salary, moving home to Cleveland"
TRIES = ["changing majors", "first-gen", "hospital jobs", "starting a club"]
NAV = ["Shelf", "My book", "Checkouts", "Past meets"]

SEARCH_ICON = (
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"></circle>'
    '<path d="m20 20-3.5-3.5"></path></svg>'
)


def e(text: str) -> str:
    return escape(text, quote=True)


def nav(prefix: str, tag: str = "nav") -> str:
    items = "".join(
        f'<span class="{"is-on" if i == 0 else ""}">{e(n)}</span>' for i, n in enumerate(NAV)
    )
    return f'<{tag} class="{prefix}">{items}</{tag}>'


def tries(prefix: str) -> str:
    spans = "".join(f"<span>{e(t)}</span>" for t in TRIES)
    return f'<div class="{prefix}-try">Or browse: {spans}</div>'


# ---------------------------------------------------------------- Direction A: Face Out


def a_cover(key: str, size: str = "") -> str:
    title, name, color, orn, _ = BOOKS[key]
    pale = " is-pale" if color in PALE else ""
    return (
        f'<div class="da-cover k{color}{pale} {size}" role="img" aria-label="{e(title)}, by {e(name)}">'
        f'<p class="da-cover-title">{e(title)}</p><i class="da-orn o-{orn}"></i>'
        f'<p class="da-cover-name">{e(name)}</p></div>'
    )


def a_pick(cover_size: str) -> str:
    title, name, *_ = BOOKS[PICK]
    return (
        f'<aside class="da-pick">{a_cover(PICK, cover_size)}<div>'
        f'<p class="da-label">The Librarian recommends</p><h3>{e(title)}</h3>'
        f'<p class="da-by">by {e(name)}</p><p class="da-reason">{e(REASON)}</p></div></aside>'
    )


def a_desktop() -> str:
    shelves = "".join(
        f'<section class="da-shelf"><div class="da-bay"><span class="da-tag">Placeholder shelf</span>'
        f'<h2>{e(label)}</h2><span class="da-more">See the whole shelf</span></div>'
        f'<div class="da-row">{"".join(a_cover(k) for k in keys)}</div><div class="da-ledge"></div></section>'
        for label, keys in SHELVES
    )
    return (
        f'<div class="da"><header class="da-top"><span class="da-mark">Trove</span>{nav("da-nav")}</header>'
        f'<section class="da-intro"><div><h2 class="da-ask">{e(ASK)}</h2>'
        f'<div class="da-field">{SEARCH_ICON}<span>{e(HINT)}</span></div>{tries("da")}</div>'
        f"{a_pick('sm')}</section>"
        f'<div class="da-shelves">{shelves}</div></div>'
    )


def a_phone() -> str:
    label, keys = SHELVES[0]
    return (
        f'<div class="da phone-screen"><div class="phone-body">'
        f'<header class="da-m-top"><span class="da-mark">Trove</span></header>'
        f'<div class="da-m-body"><div><h2 class="da-ask">{e(ASK)}</h2>'
        f'<div class="da-field">{SEARCH_ICON}<span>A topic, not a name</span></div></div>'
        f"{a_pick('sm')}"
        f'<section class="da-m-shelf"><header><h2>{e(label)}</h2><span class="da-tag">Placeholder shelf</span></header>'
        f'<div class="da-m-row">{"".join(a_cover(k) for k in keys)}</div><div class="da-ledge"></div></section>'
        f'</div></div>{nav("da-tabs")}</div>'
    )


def a_anatomy() -> str:
    return (
        f'<div class="anatomy"><div class="anatomy-book da">{a_cover("marcus", "lg")}</div><dl>'
        "<div><dt>Title</dt><dd>Set large; it's the only thing that competes for attention.</dd></div>"
        "<div><dt>First name</dt><dd>Small capitals at the foot, the way a publisher sets the author.</dd></div>"
        "<div><dt>Cloth and ornament</dt><dd>Assigned by Trove from eight colors and four marks. "
        "Variety for the eye, no meaning.</dd></div>"
        "<div><dt>Nothing else</dt><dd>No photo, year, job, chapter count or badge.</dd></div></dl></div>"
    )


# ---------------------------------------------------------------- Direction B: Catalog Card


def b_card(key: str, size: str = "") -> str:
    title, name, *_ = BOOKS[key]
    return (
        f'<div class="db-card {size}" role="img" aria-label="{e(title)}, by {e(name)}">'
        f'<span class="db-card-name">{e(name)}</span><p class="db-card-title">{e(title)}</p></div>'
    )


def b_note() -> str:
    title, name, *_ = BOOKS[PICK]
    return (
        f'<aside class="db-note"><p class="db-note-head">The Librarian recommends</p>'
        f'<h3>{e(title)}</h3><p class="db-by">by {e(name)}</p><p class="db-reason">{e(REASON)}</p></aside>'
    )


def b_plate(label: str) -> str:
    return f'<span class="db-plate">{e(label)}<small>placeholder</small></span>'


def b_desktop() -> str:
    drawers = "".join(
        f'<section><div class="db-drawer-head">{b_plate(label)}<span class="db-more">Open the drawer &rarr;</span></div>'
        f'<div class="db-cards">{"".join(b_card(k) for k in keys)}</div></section>'
        for label, keys in SHELVES
    )
    return (
        f'<div class="db"><header class="db-top"><span class="db-mark">Trove</span>{nav("db-nav")}</header>'
        f'<section class="db-intro"><div><h2 class="db-ask">{e(ASK)}</h2>'
        f'<div class="db-field"><span>{e(HINT)}</span><b>SEARCH</b></div>{tries("db")}</div>{b_note()}</section>'
        f'<div class="db-drawers">{drawers}</div></div>'
    )


def b_phone() -> str:
    label, keys = SHELVES[0]
    return (
        f'<div class="db phone-screen"><div class="phone-body">'
        f'<header class="db-m-top"><span class="db-mark">Trove</span></header>'
        f'<div class="db-m-body"><div><h2 class="db-ask">{e(ASK)}</h2>'
        f'<div class="db-field"><span>A topic, not a name</span><b>SEARCH</b></div></div>{b_note()}'
        f'<section>{b_plate(label)}<div class="db-m-cards">{"".join(b_card(k) for k in keys)}</div></section>'
        f'</div></div>{nav("db-tabs")}</div>'
    )


def b_anatomy() -> str:
    return (
        f'<div class="anatomy"><div class="anatomy-book wide db">{b_card("jamal", "lg")}</div><dl>'
        "<div><dt>Typed first name</dt><dd>Above the red line, where a catalog card puts its heading.</dd></div>"
        "<div><dt>Title on the ruled lines</dt><dd>Reads like it was written down, not designed.</dd></div>"
        "<div><dt>Rod hole</dt><dd>The one detail that says catalog card. Every card is the same 3&times;5.</dd></div>"
        "<div><dt>Nothing else</dt><dd>No color, no cover art, so there's nothing to compare but the words.</dd></div>"
        "</dl></div>"
    )


# ---------------------------------------------------------------- Direction C: The Stack


def c_spine(key: str, size: str = "", offset: bool = True) -> str:
    title, name, color, _, w = BOOKS[key]
    w_class = f" w{w}" if offset else ""
    return (
        f'<div class="dc-spine s{color}{w_class} {size}" role="img" aria-label="{e(title)}, by {e(name)}">'
        f'<span class="dc-spine-title">{e(title)}</span><span class="dc-spine-name">{e(name)}</span></div>'
    )


def c_lamp() -> str:
    return (
        f'<aside class="dc-lamp"><p class="dc-label">The Librarian recommends</p>'
        f"{c_spine(PICK, offset=False)}<p class=\"dc-reason\">{e(REASON)}</p></aside>"
    )


def c_stack(label: str, keys: list[str], more: bool = True) -> str:
    more_link = '<span class="dc-more">See the whole stack</span>' if more else ""
    return (
        f'<section class="dc-stack"><header><span class="dc-tag">Placeholder shelf</span><h2>{e(label)}</h2></header>'
        f'<div class="dc-pile">{"".join(c_spine(k) for k in keys)}</div>{more_link}</section>'
    )


def c_desktop() -> str:
    return (
        f'<div class="dc"><header class="dc-top"><span class="dc-mark">Trove</span>{nav("dc-nav")}</header>'
        f'<section class="dc-intro"><div><h2 class="dc-ask">{e(ASK)}</h2>'
        f'<div class="dc-field">{SEARCH_ICON}<span>{e(HINT)}</span></div>{tries("dc")}</div>{c_lamp()}</section>'
        f'<div class="dc-stacks">{"".join(c_stack(label, keys) for label, keys in SHELVES)}</div></div>'
    )


def c_phone() -> str:
    label, keys = SHELVES[0]
    label2, keys2 = SHELVES[1]
    return (
        f'<div class="dc phone-screen"><div class="phone-body">'
        f'<header class="dc-m-top"><span class="dc-mark">Trove</span></header>'
        f'<div class="dc-m-body"><div><h2 class="dc-ask">{e(ASK)}</h2>'
        f'<div class="dc-field">{SEARCH_ICON}<span>A topic, not a name</span></div></div>{c_lamp()}'
        f"{c_stack(label, keys, more=False)}{c_stack(label2, keys2, more=False)}"
        f'</div></div>{nav("dc-tabs")}</div>'
    )


def c_anatomy() -> str:
    return (
        f'<div class="anatomy"><div class="anatomy-book wide dc" style="padding:18px;border-radius:8px">'
        f'{c_spine("priya", "lg", offset=False)}</div><dl>'
        "<div><dt>Title along the spine</dt><dd>Narrow capitals-and-lowercase, read left to right, never rotated.</dd></div>"
        "<div><dt>First name at the tail</dt><dd>Where a publisher's name sits on a real spine.</dd></div>"
        "<div><dt>Headbands and offset</dt><dd>Thin bands at each end; piles sit a little uneven. Random, never ranked.</dd></div>"
        "<div><dt>Nothing else</dt><dd>A spine has no room for status, which is the point.</dd></div>"
        "</dl></div>"
    )


# ---------------------------------------------------------------- The review document


def browser(label: str, screen: str) -> str:
    return (
        f'<div class="stage"><p class="stage-note">Desktop, 1120px wide. Scrolls sideways on narrow screens.</p>'
        f'<div class="browser"><div class="browser-bar"><i></i><i></i><i></i><span>Trove / Shelf &middot; {e(label)}</span></div>'
        f"{screen}</div></div>"
    )


def rationale(rows: list[tuple[str, str]]) -> str:
    items = "".join(f"<div><dt>{e(k)}</dt><dd>{v}</dd></div>" for k, v in rows)
    return f'<dl class="rationale">{items}</dl>'


def direction(letter: str, anchor: str, name: str, idea: str, desktop: str, phone: str, anatomy: str, rows) -> str:
    return (
        f'<section class="doc-section" id="{anchor}"><span class="eyebrow">3 &middot; Direction {letter}</span>'
        f'<div class="dir-head"><span class="dir-letter">{letter}</span><h2 class="doc-h2">{e(name)}</h2><p>{idea}</p></div>'
        f"{browser(name, desktop)}"
        f'<div class="detail"><div class="phone" aria-label="Phone, 360px wide">{phone}</div>'
        f'<div><h3 class="doc-h3">A closed book on this shelf</h3>{anatomy}{rationale(rows)}</div></div></section>'
    )


A_ROWS = [
    ("Idea", "The display shelf near a library's entrance, where a few books stand face out. Every book gets a "
     "cloth-bound cover that Trove sets in type. The metaphor is strongest here."),
    ("Type", "Young Serif for titles: round, warm, a little old-fashioned, and still readable at 13px on a phone. "
     "Commissioner for everything you operate."),
    ("Color", "A reading-room green-grey ground. Eight muted cloth colors for covers, assigned by Trove. "
     "The only accent is the bottle green of the first cloth."),
    ("Best at", "It looks like nothing else. Covers give each book a presence, so a sophomore's book stands as "
     "tall as anyone's. It is the most likely to make an alumnus stop and look."),
    ("Worst at", "Fewest books per screen. Long titles get small inside a 2:3 cover. Authors may ask to choose "
     "their color, which brings personal branding back in."),
]
B_ROWS = [
    ("Idea", "The card catalog. Each book is a ruled 3&times;5 card with its title written on the lines; shelves "
     "are drawers with label plates. The metaphor shapes the page; there's no art at all."),
    ("Type", "Newsreader for titles and the Librarian's voice. Courier Prime for typed labels, as on a "
     "typewritten catalog card."),
    ("Color", "Cool card stock and ink blue. The catalog card's red heading line is the only warm note."),
    ("Best at", "The words carry everything, which is the most literary and the most equal. It's calm, closest "
     "to Substack's feel, and the easiest to build."),
    ("Worst at", "Can feel archival or cold, and students may never have used a card catalog. Less to look at "
     "means less pull to come back. Risks reading as a stationery theme."),
]
C_ROWS = [
    ("Idea", "Books lying flat in a pile, spine toward you, so every title reads left to right. A shelf becomes a "
     "stack: a list that still looks like books."),
    ("Type", "Archivo, narrowed, for spines, the way spine lettering is condensed to fit. Newsreader italic for "
     "the Librarian, so the one voice that recommends sounds human."),
    ("Color", "An evening reading lamp: deep blue ground, dusky spine colors, and one warm lamp color kept for "
     "the Librarian and the current page."),
    ("Best at", "Most titles per screen and the fastest to scan. Best on phones by far, and the same spine works "
     "for search results."),
    ("Worst at", "Dark-first can read as an app for late nights rather than a welcoming place. Spines have less "
     "personality than covers. A pile has a top, which could read as a ranking."),
]


def page() -> str:
    research = f"""
<section class="doc-section" id="research"><span class="eyebrow">1 &middot; Investigation</span>
<h2 class="doc-h2">Who opens this page, and what they feel</h2>
<div class="cols">
  <div><h3 class="doc-h3">Students</h3>
  <p>They open a networking app feeling like they're asking for something. They expect to be ignored, worry they
  have nothing to say, and dread the cold message. Handshake and LinkedIn make them applicants.</p>
  <p class="need"><b>The shelf has to show</b> their own book on the same shelf, dressed the same, and let them be
  curious instead of strategic.</p></div>
  <div><h3 class="doc-h3">Alumni</h3>
  <p>They open it braced for asks. Most want to give back, but fear a flood, another profile to keep up, and being
  treated as a door to a job. Most of what they know isn't on their résumé, and nobody asks about it.</p>
  <p class="need"><b>The shelf has to show</b> people, not candidates, and nothing that asks them to perform.</p></div>
  <div><h3 class="doc-h3">What brings alumni back</h3>
  <p>Being asked about the specific thing they know, by someone who read their title. A shelf worth browsing for
  themselves: alumni are readers too, and a student's book about what nineteen-year-olds think is useful to them.</p>
  <p class="need"><b>And nothing to maintain:</b> no posts, no counts to check, no inbox pressure. Coming back should
  feel like stopping by, not catching up.</p></div>
</div>
<h3 class="doc-h3" style="margin-top:44px">What the shelf is for</h3>
<p class="prose" style="color:var(--doc-muted)">Browsing until one title makes you ask a question, then meeting
the person who could answer it. It's neither of the two things networking pages usually are.</p>
<div class="table-scroll"><table class="compare">
<thead><tr><th></th><th>A feed</th><th>A directory</th><th class="hl">A shelf</th></tr></thead>
<tbody>
<tr><th>You come to</th><td>Catch up</td><td>Look someone up</td><td class="hl">Browse</td></tr>
<tr><th>Ordered by</th><td>Newest and loudest</td><td>Name, title, employer</td><td class="hl">The Librarian, a handful at a time</td></tr>
<tr><th>You find people by</th><td>What they posted</td><td>Who they are</td><td class="hl">What they could tell you</td></tr>
<tr><th>It ends</th><td>Never</td><td>When you find the name</td><td class="hl">When one book is worth 30 minutes</td></tr>
<tr><th>It rewards</th><td>Performing</td><td>Status</td><td class="hl">Curiosity</td></tr>
</tbody></table></div>
</section>"""

    feeling = """
<section class="doc-section" id="feeling"><span class="eyebrow">2 &middot; The feeling</span>
<p class="feeling">Curious, unhurried, <em>among equals.</em></p>
<p class="prose lede">An afternoon in the stacks with nothing assigned, pulling out a book because its title made
you wonder. Nobody is watching, nothing is ranked, and the author is a person you could actually go and talk to.</p>
<h3 class="doc-h3" style="margin-top:36px">It must never feel like</h3>
<dl class="pairs">
  <div><dt>LinkedIn</dt><dd>Polish, titles, employers, counts. The place you perform.</dd></div>
  <div><dt>A dating app</dt><dd>Faces, swiping, judging people at a glance.</dd></div>
  <div><dt>A recruiting tool</dt><dd>Filters, pipelines, people sorted into candidates.</dd></div>
  <div><dt>A feed</dt><dd>Endless, newest first, loud.</dd></div>
  <div><dt>A themed bookshop</dt><dd>Fake wood, leather and quaintness. A gimmick alumni won't take seriously.</dd></div>
</dl>
<h3 class="doc-h3" style="margin-top:44px">Principles</h3>
<dl class="pairs">
  <div><dt>The title is the face</dt><dd>Lead with the title. The first name is small. No photos.</dd></div>
  <div><dt>Every book gets the same frame</dt><dd>Same size, same type, color assigned by Trove. Nothing a VP's book
  can have that a sophomore's can't.</dd></div>
  <div><dt>A visit can end</dt><dd>Shelves are finite. No infinite scroll, no "new" or "trending", nothing that ticks.</dd></div>
  <div><dt>Library as structure, not costume</dt><dd>Borrow how a library works (shelves, checkout, the Librarian).
  Skip the wood grain.</dd></div>
  <div><dt>One voice recommends</dt><dd>Only the Librarian suggests, and always with the reason a person would give.</dd></div>
</dl>
</section>"""

    compare = """
<section class="doc-section" id="compare"><span class="eyebrow">4 &middot; Side by side</span>
<h2 class="doc-h2">How they compare</h2>
<div class="table-scroll"><table class="compare">
<thead><tr><th></th><th>A &middot; Face Out</th><th>B &middot; Catalog Card</th><th>C &middot; The Stack</th></tr></thead>
<tbody>
<tr><th>Metaphor</th><td>Strong: you see books</td><td>Medium: you see the catalog</td><td>Light: you see spines</td></tr>
<tr><th>Books per desktop screen</th><td>About 8</td><td>About 12</td><td>About 15</td></tr>
<tr><th>Title readability</th><td>Good, smaller on long titles</td><td>Best</td><td>Very good</td></tr>
<tr><th>Feels equal</th><td>Yes, if Trove assigns colors</td><td>Most equal</td><td>Yes, if piles are never ranked</td></tr>
<tr><th>On a phone</th><td>Good, as a sideways row</td><td>Fair, cards are big</td><td>Best</td></tr>
<tr><th>Memorable</th><td class="hl">Most</td><td>Least</td><td>Middle</td></tr>
<tr><th>Main risk</th><td>Low density; color requests</td><td>Cold, archival</td><td>Night-app mood; pile reads as ranking</td></tr>
</tbody></table></div>
<div class="recommend">
<p class="big">Build A, Face Out, and borrow C's spine for lists.</p>
<p>A is the one where the shelf looks like nothing else: a row of books you'd want to pick up, all dressed alike,
none louder than another. That's the first impression that makes an alumnus stay and a student feel they belong.</p>
<p>Its weakness is density, and C solves it. Use C's spine as the list form for search results, "See the whole
shelf" and long lists on phones. Keep B's typed Librarian slip in mind if A's recommendation panel starts to feel
like an ad.</p>
</div>
</section>"""

    questions = """
<section class="doc-section" id="questions"><span class="eyebrow">5 &middot; For Josef</span>
<h2 class="doc-h2">Questions these designs raise</h2>
<ol class="questions">
<li><b>Student or alum on the cover?</b> The plan leaves a stage marker open (§3). None of these show one, so
student and alumni books are indistinguishable. Recommendation: keep it that way on the shelf.</li>
<li><b>Who picks a book's cover color?</b> A and C assume Trove assigns it. Recommendation: Trove assigns, so covers
can't become personal branding.</li>
<li><b>How is a shelf ordered?</b> These assume a fresh order on each visit, with the Librarian quietly favoring books
that get fewer requests (§9.6). Recommendation: yes, and never by popularity or recency.</li>
<li><b>Dark mode at launch?</b> A and B are light-only, C is dark-only. Recommendation: pick the direction first,
then design its other theme.</li>
</ol>
</section>"""

    directions = (
        direction("A", "face-out", "Face Out",
                  "Books stand face out on a ledge, like the display shelf by a library's door. Covers set in type, "
                  "cloth colors assigned by Trove.",
                  a_desktop(), a_phone(), a_anatomy(), A_ROWS)
        + direction("B", "catalog-card", "Catalog Card",
                    "Every book is a typed 3&times;5 catalog card, filed in a labelled drawer. No cover art; the words "
                    "do all the work.",
                    b_desktop(), b_phone(), b_anatomy(), B_ROWS)
        + direction("C", "the-stack", "The Stack",
                    "Books lie flat in piles, spine out, so every title reads left to right. A shelf you can scan like "
                    "a list.",
                    c_desktop(), c_phone(), c_anatomy(), C_ROWS)
    )

    fonts = (
        "https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..700"
        "&family=Commissioner:wght@400;500;600&family=Courier+Prime:wght@400;700"
        "&family=Hanken+Grotesk:wght@400;500;600;700"
        "&family=Newsreader:ital,opsz,wght@0,6..72,400..600;1,6..72,400..500"
        "&family=Young+Serif&display=swap"
    )
    return f"""<title>Trove Shelf Directions</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{fonts}">
<!-- Generated by build.py. Each direction's styles live in their own file. -->
<link rel="stylesheet" href="base.css">
<link rel="stylesheet" href="direction-a.css">
<link rel="stylesheet" href="direction-b.css">
<link rel="stylesheet" href="direction-c.css">

<main class="doc">
<header>
<span class="eyebrow">Task T1 &middot; The shelf page &middot; November 5, 2026</span>
<h1 class="doc-h1">Three directions for the shelf</h1>
<p class="lede">The shelf is Trove's home screen, where members browse books and pick one worth a 30-minute
conversation. This page sets out who it's for, the feeling it should have, and three ways to build it.
All books, names and shelf labels are samples; shelf categories are placeholders until they're decided.</p>
</header>
{research}
{feeling}
{directions}
{compare}
{questions}
</main>
"""


if __name__ == "__main__":
    (HERE / "index.html").write_text(page(), encoding="utf-8")
    print(f"Wrote {HERE / 'index.html'}")
