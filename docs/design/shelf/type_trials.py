"""Covers: Strata page: a true-scale shelf comparing three cover typography approaches on the strata art (Josef,
2026-11-21: "I want the shelf to have the realistic dimensions and scale for the in app shelf, not enlarged"). Books
are the app's desktop shelf size (122 x 178 CSS px, web/src/ui/styles.css .book), the shelf name, rule and ledge are
the app's, and the art is the cover's shelf-size render. Built from the FinalCoverForest board's head (tokens and
book styles).

  A  Poster        Barlow Condensed caps, larger and tighter than today; the name right under it, legible.
  B  Name at foot  A, with the name in the bottom left corner on a paper knockout over the art.
  C  Name on top   A, with the name set above the title.
(Round 1 had a Newsreader "Literary" B and a framed "Label" C; Josef dropped both for these two variants of A.)

python3 type_trials.py <root> -> <root>/project/TypeTrials.dc.html"""
import re
import sys

ROOT = sys.argv[1]
P = f"{ROOT}/project"
src = open(f"{P}/FinalCoverForest.dc.html").read()
head = src[:src.index("</helmet>")]
tail = src[src.index("</x-dc>"):]

BOOKS = {
    "desert": ("What the Desert Teaches", "Lucía Hernández-Brooks", "#6a3525", "7b2a3b7043bb5bf080a9abbc8208ec29"),
    "forest": ("Room to Grow", "Noah Bergstrom", "#283d2e", "36fdd5c3e43a5d934efece7910485b24"),
    "city": ("Small Bets, Big City", "Danielle Owens", "#2f3448", "c493f39525ed78bb92b885e67be913e3"),
    "lake": ("The Night Shift Knows", "Maya Okafor", "#16302e", "af326be27e3bdd8b1a9250d40825bd6f"),
    "aurora": ("Long Nights, Clear Skies", "Ingrid Solberg", "#252a4c", "cad4c12d033de0a0c11e4290b7a42c61"),
}

STYLE = """<style>
/* Type trials at shelf size. Every value is the real CSS px size on the app's desktop shelf. */
.tt .book-cover{padding:14px 9px 10px 20px}
.tt .book-title,.tt .book-author{position:relative;z-index:1;color:var(--c-ink)}
/* A Poster, and the base of B and C */
.tt .book-title{font:800 20px/.92 var(--font-display);letter-spacing:.01em;text-transform:uppercase;text-wrap:balance}
.tt .book-author{font:700 9px/1.25 var(--font-display);letter-spacing:.16em;text-transform:uppercase;
  display:block;-webkit-line-clamp:unset;
  /* where the art rises into the name, a paper knockout keeps it legible */
  align-self:flex-start;width:fit-content;background:var(--white);padding:0 3px 1px;margin-left:-3px}
.ty-a .book-author{margin-top:7px}
/* B: the name in the bottom left corner, over the art */
.ty-b .book-cover{padding-bottom:8px}
.ty-b .book-author{margin-top:auto;padding:2px 4px 1px;margin-left:-4px}
/* C: the name above the title */
.ty-c .book-cover{padding-top:11px}
.ty-c .book-author{order:-1;margin:0 0 5px -3px}
.tt-note{font:600 14px/1.2 var(--font-display);letter-spacing:.14em;text-transform:uppercase;color:var(--ink-2)}
.tt .shelf-name{margin:0;font:800 30px/1 var(--font-display);letter-spacing:.04em;text-transform:uppercase}
.tt .shelf-books{padding-bottom:0;margin-bottom:-1px;align-items:flex-end}
.shelf-row.tt + .shelf-row.tt{margin-top:64px}
</style>
"""


def book(key, ty):
    title, author, ink, blob = BOOKS[key]
    return (f'<div class="book tt ty-{ty}" style="--c-ink:{ink}" aria-label="{title}, by {author}"><span '
            f'class="book-cover"><img class="cover-art" src="/_blob/{blob}" alt=""><span class="book-title">{title}'
            f'</span><span class="book-author">{author}</span></span></div>')


def shelf(name, books):
    return (f'<section class="shelf-row tt"><div class="shelf-head"><h2 class="shelf-name">{name}</h2></div>'
            f'<div class="shelf-books">{"".join(books)}</div><div class="ledge"></div></section>')


rows = [
    shelf("Three approaches", [book("desert", "a"), book("forest", "b"), book("city", "c")]),
    shelf("A · Poster", [book(k, "a") for k in BOOKS]),
    shelf("B · Name at foot", [book(k, "b") for k in BOOKS]),
    shelf("C · Name on top", [book(k, "c") for k in BOOKS]),
]
W, H = 1100, 1290
board = (f'<div style="width:{W}px;height:{H}px;background:var(--paper);color:var(--ink);font-family:var(--font-sans);'
         f'padding:56px 44px;overflow:hidden"><span class="tt-note">Cover type trials · actual shelf size, view at 100%'
         f'</span><div style="margin-top:40px">{"".join(rows)}</div></div>\n')
h = re.sub(r"<title>.*?</title>", "<title>Cover type trials</title>", head)
t = re.sub(r'"width":\d+,"height":\d+', f'"width":{W},"height":{H}', tail)
open(f"{P}/TypeTrials.dc.html", "w").write(h + STYLE + "</helmet>\n\n" + board + t)
print("ok")
