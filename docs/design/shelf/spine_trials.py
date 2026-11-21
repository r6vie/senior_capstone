"""Covers: Strata page: spine (hinge) options at the chosen shelf size, 176 x 257, at true scale (Josef,
2026-11-21: "should we reconsider the spine taking up so much valuable space on the left? Give me 3 options").
Today the hinge line sits 17px in and the type starts 29px in. Three options, each a shelf of the strata covers:
  A  Narrow hinge  the line moves to 8px, thinner; the type starts at 18px.
  B  Ink spine     no line: a solid strip of the cover's own ink, 8px wide, binds the left edge; type at 18px.
  C  No hinge      no line at all; the outline and the dot shadow carry the book; type at 14px, as on the right.
Built like size_trials.py.

Derived from: shelf book sizes at true scale (Josef, 2026-11-21: "the books are so pretty we should make
them larger in the app, which will also help with legibility"). A 1440 px desktop page with the app's gutter, shelf
name, rule and ledge; three shelves of the strata covers: today's .book (122 x 178) and two larger sizes on the same
aspect, with the poster type (type_trials.py A) scaled with the book. Rows overflow to the right as in the app, so
the next book peeks in. The art is the large cover render, so it stays crisp at every size.

python3 spine_trials.py <root> -> <root>/project/SpineTrials.dc.html"""
import re
import sys

ROOT = sys.argv[1]
P = f"{ROOT}/project"
src = open(f"{P}/FinalCoverForest.dc.html").read()
head = src[:src.index("</helmet>")]
tail = src[src.index("</x-dc>"):]

BOOKS = [
    ("Room to Grow", "Noah Bergstrom", "#283d2e", "f555c336b0c5f0fc55b7aae44dad590e"),
    ("What the Desert Teaches", "Lucía Hernández-Brooks", "#6a3525", "49a3b7b996be6b7bb76cfea36a94ef45"),
    ("Small Bets, Big City", "Danielle Owens", "#2f3448", "e3a296be11254b8759058aa95983a0eb"),
    ("The Patient Field", "Dewi Santoso", "#3d5a32", "e06812a20fe342d8e6031d95a4541715"),
    ("Two Years Upriver", "Wen Zhao", "#2f4637", "b2e965ae5ad858def0fa23d0e1201ced"),
    ("Island Time Isn’t Slow", "Keoni Akana", "#1f4f5a", "4810d19da6f67fa9787d2f71aa1ba1c6"),
    ("The Night Shift Knows", "Maya Okafor", "#16302e", "0d3aba83ca6b95a037082a747edafeef"),
    ("Long Nights, Clear Skies", "Ingrid Solberg", "#252a4c", "21379c317bb8427aa44329c749315ee9"),
    ("A Slow Harvest", "Mei Lin Okada", "#263a2d", "06e7111a35d637b327da5d3a4af62d4d"),
    ("Notes From the Edge", "Callum O’Donnell", "#26304f", "09eabf0d3c4a573f24c3190ca05b4b95"),
]

# (label, width, gap): height keeps the cover's 236 x 344 aspect
SPINES = [("Today · hinge at 17", "now"), ("A · Narrow hinge", "a"), ("B · Ink spine", "b"), ("C · No hinge", "c")]

STYLE = """<style>
/* Shelf size trials. Every value is the real CSS px size on the app's 1440 desktop page; --k scales the book. */
.st .book{width:calc(122px * var(--k));height:calc(178px * var(--k))}
.st .book-cover{padding:calc(14px * var(--k)) calc(9px * var(--k)) calc(10px * var(--k)) calc(20px * var(--k))}
.st .book-cover::before{left:calc(12px * var(--k))}
.st .book-title,.st .book-author{position:relative;z-index:1;color:var(--c-ink)}
.st .book-title{font:800 calc(20px * var(--k))/.92 var(--font-display);letter-spacing:.01em;text-transform:uppercase;
  text-wrap:balance}
.st .book-author{margin-top:calc(7px * var(--k));font:700 calc(9px * var(--k))/1.25 var(--font-display);
  letter-spacing:.16em;text-transform:uppercase;display:block;-webkit-line-clamp:unset;
  align-self:flex-start;width:fit-content;background:var(--white);padding:0 3px 1px;margin-left:-3px}
/* spines: today's scaled hinge, then the three options */
.sp-now .book-cover::before{left:17px;width:2px}
.sp-a .book-cover{padding-left:18px}
.sp-a .book-cover::before{left:8px;width:1.5px}
.sp-b .book-cover{padding-left:18px}
.sp-b .book-cover::before{left:0;width:8px;background:var(--c-ink);z-index:1}
.sp-c .book-cover{padding-left:14px}
.sp-c .book-cover::before{display:none}
.st-note{font:600 14px/1.2 var(--font-display);letter-spacing:.14em;text-transform:uppercase;color:var(--ink-2)}
.st .shelf-name{margin:0;font:800 30px/1 var(--font-display);letter-spacing:.04em;text-transform:uppercase}
.st .shelf-books{overflow:hidden;padding:0 4px;margin-right:-44px;align-items:flex-end}
.st .ledge{margin:0 -44px 0 -8px}
.shelf-row.st + .shelf-row.st{margin-top:64px}
</style>
"""


def book(b):
    title, author, ink, blob = b
    return (f'<div class="book" style="--c-ink:{ink};flex:none" aria-label="{title}, by {author}"><span '
            f'class="book-cover"><img class="cover-art" src="/_blob/{blob}" alt=""><span class="book-title">{title}'
            f'</span><span class="book-author">{author}</span></span></div>')


def shelf(name, sp):
    return (f'<section class="shelf-row st sp-{sp}" style="--k:{176 / 122:.4f}"><div class="shelf-head"><h2 '
            f'class="shelf-name">{name}</h2></div><div class="shelf-books" style="gap:36px">'
            f'{"".join(book(b) for b in BOOKS)}</div><div class="ledge"></div></section>')


W, H = 1440, 1650
board = (f'<div style="width:{W}px;height:{H}px;background:var(--paper);color:var(--ink);font-family:var(--font-sans);'
         f'padding:56px 44px;overflow:hidden"><span class="st-note">Spine options · 176 × 257 books on a 1440 px desktop page at actual '
         f'size, view at 100%</span><div style="margin-top:40px">{"".join(shelf(*s) for s in SPINES)}</div></div>\n')
h = re.sub(r"<title>.*?</title>", "<title>Spine options</title>", head)
t = re.sub(r'"width":\d+,"height":\d+', f'"width":{W},"height":{H}', tail)
open(f"{P}/SpineTrials.dc.html", "w").write(h + STYLE + "</helmet>\n\n" + board + t)
print("ok")
