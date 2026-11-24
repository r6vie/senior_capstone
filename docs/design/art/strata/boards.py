"""Writes the three Strata boards for the design canvas (page "Strata")."""

import pathlib

REPO = pathlib.Path(__file__).resolve().parents[4]
ROOT = pathlib.Path(__file__).parent / "canvas"  # publish root for the design canvas; not committed
(ROOT / "project").mkdir(parents=True, exist_ok=True)

A = {
    "pano": "/_blob/4be7c66e3adfcc920c4f27eb36e6b72e",
    "lake-lg": "/_blob/bba2432b060dd330440db8f1fd03cd93",
    "lake-md": "/_blob/0885aaebb587405b289c4d1361577f32",
    "lake-sm": "/_blob/642bf744059f1c1c13a05e6c884a5677",
    "coast-md": "/_blob/09bdd48489e9f631df55899fd4e01892",
    "ranges-md": "/_blob/879aa0e6aee03cb7c52cad64bf0e805c",
    "islands-md": "/_blob/7d1ef31ee1e9be2a1832a120d33d34fe",
    "twins-md": "/_blob/018e9b2bffd9bf84e7574000b5e9cc5b",
    "summit-md": "/_blob/33ebc6fcf483e6f9a24f28131e1da37c",
    "terraces-md": "/_blob/87923710e5503711b5331187bf72a3f4",
    "dusk-md": "/_blob/8fd208fa9dcb221c08185ff6b48e7ce9",
    "coast-lg": "/_blob/056e58ea96959a36952698c2eee82eb1",
    "summit-lg": "/_blob/493053c350b7eac89177f456c7fc96a2",
    "ranges-lg": "/_blob/3efa3dac56dada56cd7bac5059d4ad44",
    "pano-phone": "/_blob/59b79f66123752e527534f647296a9f1",
    "lake-phone": "/_blob/3ee2f7a01e4c4ed73a5a6d188d540386",
}

TOKENS = (REPO / "docs/design/system/tokens.css").read_text()

STRATA_CSS = """
body{margin:0}
*,*::before,*::after{box-sizing:border-box}
/* Strata covers. The art is a picture laid under the cover's title and name; the book object is unchanged:
   white, outlined, hinge, dot shadow, title and full name only. */
.book-cover{background:var(--white)}
.book-cover::before{z-index:2}
.book-title,.book-author{position:relative;z-index:1}
/* A long title or name may meet the art: each line sits on a white knockout, as text on tone does elsewhere. */
.ko{background:var(--white);box-decoration-break:clone;-webkit-box-decoration-break:clone;padding:0 3px;margin:0 -3px}
.cover-art{position:absolute;z-index:0;left:calc(-1 * var(--line));top:calc(-1 * var(--line));width:calc(100% + 2 * var(--line));height:calc(100% + 2 * var(--line));display:block}
.book-lg .cover-art{left:calc(-1 * var(--line-heavy));top:calc(-1 * var(--line-heavy));width:calc(100% + 2 * var(--line-heavy));height:calc(100% + 2 * var(--line-heavy))}
.byline{font:600 13px/1.3 var(--font-sans);letter-spacing:.12em;text-transform:uppercase;color:var(--ink-2)}
.frame-label{font:600 14px/1.2 var(--font-display);letter-spacing:.14em;text-transform:uppercase;color:var(--ink-2)}
.frame{position:relative;overflow:hidden;border:var(--line) solid var(--ink);background:var(--paper)}
.note{font:400 14px/1.5 var(--font-sans);color:var(--ink-2)}
.ch{display:grid;gap:6px;padding:20px 0;border-top:2.5px dotted var(--ink)}
.ch h3{margin:0;font:600 22px/1.2 var(--font-serif)}
.ch p{margin:0;font:400 16px/1.5 var(--font-sans);color:var(--ink-2)}
.ink-chip{display:inline-block;width:28px;height:10px;margin-right:2px}
.search{font-family:var(--font-sans)}
"""

FONTS = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700;800&amp;family=Newsreader:ital,opsz,wght@0,6..72,400..700;1,6..72,400..500&amp;family=IBM+Plex+Sans:wght@400;500;600&amp;display=swap">'


def page(title, w, h, body):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
{FONTS}
<style>
{TOKENS}
{STRATA_CSS}
</style>
</helmet>
{body}
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":{w},"height":{h}}}}}'>
class Component extends DCLogic {{
renderVals() {{
return {{}};
}}
}}
</script>
</body>
</html>
"""


def topbar(current="Shelf"):
    items = "".join(
        f'<a href="#"{" aria-current=\"page\"" if n == current else ""}>{n}</a>'
        for n in ("Shelf", "My book", "Checkouts", "Past meets")
    )
    return f"""<header style="display: flex; align-items: center; gap: 36px; height: 48px; padding: 16px 36px 0">
<span class="wordmark">Trove</span>
<nav class="nav" aria-label="Main">{items}</nav>
<input class="search" style="margin-left: auto" type="search" placeholder="Search by topic" aria-label="Search by topic">
<span class="avatar" aria-label="Your account">J</span>
</header>"""


def book(title, name, art, size="", tag="a"):
    cls = "book" + (f" book-{size}" if size else "")
    href = ' href="#"' if tag == "a" else ""
    return (
        f'<{tag} class="{cls}"{href} aria-label="{title}, by {name}">'
        f'<span class="book-cover"><img class="cover-art" src="{A[art]}" alt="">'
        f'<span class="book-title"><span class="ko">{title}</span></span><span class="book-author"><span class="ko">{name}</span></span></span></{tag}>'
    )


CHAPTERS = [
    ("Handoffs are where things break",
     "Most mistakes she has seen began in the five minutes between shifts, not in the work itself."),
    ("Charge nurses run the hospital", "Who actually decides which bed a patient gets, and how to ask them nicely."),
    ("Learning to sleep in daylight", "The small routines that got her through two years of nights."),
]


def chapters_html():
    return "".join(f'<div class="ch"><h3>{t}</h3><p>{s}</p></div>' for t, s in CHAPTERS)


# ---------- 1. The book page, desktop ----------
BOOK = page("Strata book page", 1440, 1140, f"""
<div style="width: 1440px; height: 1140px; background: var(--paper); color: var(--ink); font-family: var(--font-sans); overflow: hidden">
{topbar()}
<section style="position: relative; width: 1440px; height: 620px; margin-top: 16px" aria-labelledby="book-title">
<img src="{A['pano']}" alt="" style="position: absolute; left: 0; top: 0; width: 1440px; height: 620px; display: block">
<div style="position: absolute; left: 128px; top: 64px" aria-hidden="true">{book("The Night Shift Knows", "Maya Okafor", "lake-lg", "lg", "div")}</div>
<div style="position: absolute; left: 448px; top: 56px; width: 600px; display: flex; flex-direction: column; align-items: flex-start; gap: 16px">
<a class="button button-quiet" href="#" style="margin-left: -12px">Back to the shelf</a>
<h1 id="book-title" class="page-title" style="font-size: 54px">The Night Shift Knows</h1>
<p class="byline" style="margin: 0">by Maya Okafor</p>
<p style="margin: 0; max-width: 470px; font-size: 17px; line-height: 1.5">What a hospital looks like from the people who keep it running at 3 a.m.</p>
<div style="display: flex; align-items: center; gap: 20px; margin-top: 8px">
<a class="button button-primary" href="#">Ask to check out</a>
<span class="note">A thirty-minute video call, if the author says yes.</span>
</div>
</div>
</section>
<section style="width: 640px; margin: 40px 0 0 448px" aria-labelledby="ch-head">
<h2 id="ch-head" class="shelf-name" style="font-size: 24px; margin-bottom: 16px">What you could talk about</h2>
{chapters_html()}
</section>
</div>
""")


# ---------- 2. On the shelf, and the art drawn per size ----------
SHELF_BOOKS = [
    ("The Night Shift Knows", "Maya Okafor", "lake-md"),
    ("Shipping Code Nobody Notices", "Dev Raman", "coast-md"),
    ("Lab Notebooks and Late Buses", "Priya Natarajan", "ranges-md"),
    ("Small Town, Big Contracts", "Sam Kowalski", "islands-md"),
    ("Translating for My Parents", "Lena Morales", "twins-md"),
    ("Why I Turned Down Grad School Twice", "Hana Sato", "summit-md"),
    ("From Orchestra Pit to Product Manager", "Kiera Lindgren", "terraces-md"),
    ("Starting a Podcast With No Audience", "Alexandra Okonkwo-Brennan", "dusk-md"),
    ("Teaching Yourself to Code at Thirty-Four", "Luis Ortega", "coast-md"),
]
INKS = [
    ("Cobalt", ["#A9C7E4", "#7FAAD6", "#5389C4", "#3369AC", "#1F4E8E"]),
    ("Teal", ["#6E9CB0", "#4F8399", "#2F5C62", "#1C3631", "#0E1D1A"]),
    ("Sage", ["#A8B4A7", "#8E9C8E", "#56675D", "#40524A", "#2E3E37"]),
    ("Stone", ["#EEEBE4", "#D4CFC3", "#B9B2A5", "#9E978A", "#837C70"]),
    ("Coral", ["#F2A48C", "#EE8A6E", "#E87457", "#9A4A35", "#5F2A1F"]),
    ("Ochre", ["#E6CB97", "#DAB477", "#C99C5A", "#83613A", "#634829"]),
    ("Leaf", ["#93B47A", "#6F9A5A", "#4F7D45", "#284A2B", "#1B3520"]),
]


def inks_html():
    rows = []
    for name, cs in INKS:
        chips = "".join(f'<span class="ink-chip" style="background: {c}"></span>' for c in cs)
        rows.append(f'<div style="display: flex; align-items: center; gap: 12px"><span class="frame-label" style="width: 64px">{name}</span><span>{chips}</span></div>')
    return "".join(rows)


SHELF = page("Strata on the shelf", 1440, 1180, f"""
<div style="width: 1440px; height: 1180px; background: var(--paper); color: var(--ink); font-family: var(--font-sans); overflow: hidden">
{topbar()}
<section style="padding: 48px 44px 0" aria-labelledby="shelf1">
<div class="shelf-head"><h2 id="shelf1" class="shelf-name">Changing course</h2><a href="#">See all</a></div>
<div class="shelf-books">{"".join(book(t, n, a) for t, n, a in SHELF_BOOKS)}</div>
<div class="ledge" style="margin: 18px -44px 0 -8px"></div>
</section>
<section style="display: flex; gap: 64px; padding: 88px 44px 0">
<div style="display: flex; flex-direction: column; gap: 20px">
<span class="frame-label">One book, drawn for the size it shows at</span>
<div style="display: flex; align-items: flex-end; gap: 44px">
{book("The Night Shift Knows", "Maya Okafor", "lake-lg", "lg", "div")}
{book("The Night Shift Knows", "Maya Okafor", "lake-md", "", "div")}
{book("The Night Shift Knows", "Maya Okafor", "lake-sm", "sm", "div")}
</div>
<p class="note" style="max-width: 560px; margin: 16px 0 0">The same place each time, redrawn rather than shrunk: 4px courses on the large book and the book page,
2px on the shelf and small sizes, so a slab never turns to grey fuzz. Each cover is a 1 to 4 KB image.</p>
</div>
<div class="panel" style="flex: 1; display: flex; flex-direction: column; gap: 14px; align-self: flex-start">
<h3>How the art is made</h3>
<p style="margin: 0">Every shape is cut into courses of one height and laid in bricks of random length. Edges step instead of curving.</p>
<p style="margin: 0">Light comes from the left. Each peak has a lit face and a shadow face, and the stepped edge on the shadow side is inked darkest.</p>
<p style="margin: 0">Mist and distance are bricks left out and paled toward paper. No blur, gradient or glow, as with dot tone.</p>
<p style="margin: 0">Seven ink families. Coral is the warm note and is not the UI red: the red stays the one thing to do next.</p>
<div style="display: grid; gap: 8px; margin-top: 6px">{inks_html()}</div>
</div>
</section>
</div>
""")


# ---------- 3. More places ----------
def strip(h, pos="50% 100%"):
    return f'<img src="{A["pano"]}" alt="" style="position: absolute; left: 0; bottom: 0; width: 100%; height: {h}px; object-fit: cover; object-position: {pos}; display: block">'


REVEAL = [
    ("The Night Shift Knows", "lake-lg", "You kept coming back to the minutes between shifts."),
    ("What the Charge Nurse Decides", "ranges-lg", "Your best stories were about who really runs the floor."),
    ("Sleeping in Daylight", "summit-lg", "You were most specific about getting through two years of nights."),
]


def reveal_html():
    cards = "".join(
        f'<div style="display: flex; flex-direction: column; gap: 14px; width: 236px">{book(t, "Maya Okafor", a, "lg", "div")}'
        f'<p class="voice" style="margin: 10px 0 0; font-size: 17px">{why}</p>'
        f'<button class="button button-secondary" type="button">Choose this one</button></div>'
        for t, a, why in REVEAL
    )
    return cards


PLACES = page("Strata in more places", 1440, 2040, f"""
<div style="width: 1440px; height: 2040px; background: var(--paper-sunk); color: var(--ink); font-family: var(--font-sans); padding: 44px; box-sizing: border-box; display: flex; gap: 56px; overflow: hidden">

<div style="display: flex; flex-direction: column; gap: 12px">
<span class="frame-label">Phone · the book page</span>
<div class="frame" style="width: 390px; height: 844px">
<header style="display: flex; align-items: center; justify-content: space-between; height: 56px; padding: 0 16px">
<span class="wordmark" style="font-size: 22px">Trove</span>
<span class="avatar" aria-label="Your account">J</span>
</header>
<div style="position: relative; height: 436px; overflow: hidden">
<img src="{A['pano-phone']}" alt="" style="position: absolute; left: -80px; top: -32px; width: 1080px; height: 465px; display: block">
<div class="book book-lg" style="position: absolute; left: 16px; top: 16px; width: 177px; height: 258px" aria-hidden="true">
<span class="book-cover" style="padding: 22px 12px 12px 30px"><img class="cover-art" src="{A['lake-phone']}" alt="">
<span class="book-title" style="font-size: 20px">The Night Shift Knows</span><span class="book-author" style="font-size: 10px">Maya Okafor</span></span></div>
</div>
<div style="display: flex; flex-direction: column; gap: 12px; padding: 0 16px">
<h1 class="page-title" style="font-size: 34px">The Night Shift Knows</h1>
<p class="byline" style="margin: 0">by Maya Okafor</p>
<p style="margin: 0; font-size: 16px">What a hospital looks like from the people who keep it running at 3 a.m.</p>
<a class="button button-primary" href="#" style="width: 100%; box-sizing: border-box">Ask to check out</a>
<span class="note">A thirty-minute video call, if the author says yes.</span>
</div>
</div>
<p class="note" style="width: 390px; margin: 8px 0 0">The cover is still a window onto the same place, drawn at three-quarter size, so the courses stay 3px.</p>
</div>

<div style="display: flex; flex-direction: column; gap: 12px; flex: 1">
<span class="frame-label">Interview · the reveal (titles and reasons are placeholders)</span>
<div class="frame" style="height: 700px; padding: 44px; box-sizing: border-box">
<h2 class="page-title" style="font-size: 40px; margin-bottom: 32px">Three books you could write</h2>
<div style="display: flex; gap: 56px">{reveal_html()}</div>
</div>

<span class="frame-label" style="margin-top: 36px">Checkouts · the author said yes (copy is placeholder)</span>
<div class="frame" style="height: 440px; padding: 44px; box-sizing: border-box">
<div style="display: flex; gap: 36px; align-items: flex-start">
{book("The Night Shift Knows", "Maya Okafor", "lake-md", "", "div")}
<div style="display: flex; flex-direction: column; gap: 12px; max-width: 520px">
<h2 class="page-title" style="font-size: 36px">Maya Okafor said yes</h2>
<p style="margin: 0; font-size: 16px">You can see each other's email now. Write to agree on a time for the call.</p>
<p style="margin: 0; font: 600 16px/1.4 var(--font-sans)">[Maya's email, shown here]</p>
<div><a class="button button-secondary" href="#">Copy her email</a></div>
</div>
</div>
{strip(150, "50% 96%")}
</div>

<span class="frame-label" style="margin-top: 36px">Meeting · waiting for the author (copy is placeholder)</span>
<div class="frame" style="height: 560px; padding: 44px; box-sizing: border-box">
<div style="display: flex; gap: 44px; align-items: flex-start">
<div class="tone-mid" style="width: 360px; height: 220px; border: var(--line) solid var(--ink); display: grid; place-items: center">
<span style="background: var(--white); padding: 4px 10px; font-weight: 600">Your camera</span></div>
<div style="display: flex; flex-direction: column; gap: 12px">
<p class="frame-label" style="margin: 0">The Night Shift Knows</p>
<h2 class="page-title" style="font-size: 36px">Waiting for Maya Okafor</h2>
<p style="margin: 0; font-size: 16px">She will see you as soon as she joins.</p>
<div style="margin-top: 8px"><a class="button button-primary" href="#">Join the call</a></div>
</div>
</div>
{strip(220, "50% 100%")}
</div>
</div>
</div>
""")

for name, src in (("StrataBook", BOOK), ("StrataShelf", SHELF), ("StrataPlaces", PLACES)):
    (ROOT / "project" / f"{name}.dc.html").write_text(src)
print("written")
