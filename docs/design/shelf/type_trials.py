"""Covers: Strata page: a true-scale shelf comparing three cover typography approaches on the strata art (Josef,
2026-11-21: "I want the shelf to have the realistic dimensions and scale for the in app shelf, not enlarged"). Books
are the app's desktop shelf size (122 x 178 CSS px, web/src/ui/styles.css .book), the shelf name, rule and ledge are
the app's, and the art is the cover's shelf-size render. Built from the FinalCoverForest board's head (tokens and
book styles).

  A  Poster   Barlow Condensed caps, larger and tighter than today; the name right under it, legible.
  B  Literary Newsreader, the app's own book-title face, in sentence case; the name in Plex Sans caps.
  C  Label    the title in a thin framed label at the top; the name on a paper tab at the foot, over the art.

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
/* A Poster */
.ty-a .book-title{font:800 20px/.92 var(--font-display);letter-spacing:.01em;text-transform:uppercase;text-wrap:balance}
.ty-a .book-author{margin-top:7px;font:700 9px/1.25 var(--font-display);letter-spacing:.16em;text-transform:uppercase;
  display:block;-webkit-line-clamp:unset}
/* where the art rises into the name, a paper knockout keeps it legible */
:is(.ty-a,.ty-b) .book-author{align-self:flex-start;width:fit-content;background:var(--white);padding:0 3px 1px;
  margin-left:-3px}
/* B Literary */
.ty-b .book-title{font:600 16.5px/1.06 var(--font-serif);letter-spacing:-.01em;text-wrap:balance}
.ty-b .book-author{margin-top:7px;font:600 8.5px/1.3 var(--font-sans);letter-spacing:.08em;text-transform:uppercase;
  display:block;-webkit-line-clamp:unset}
/* C Label: a framed label at the top, the name on a paper tab cut into the foot of the art */
.ty-c .book-cover{padding:12px 8px 0 19px}
.ty-c .book-title{padding:7px 6px 8px;border:1.5px solid var(--c-ink);background:var(--white);text-align:center;
  font:600 14px/1.1 var(--font-serif);text-wrap:balance}
.ty-c .book-author{position:absolute;left:12px;bottom:0;max-width:calc(100% - 12px);margin:0;padding:5px 8px 4px 8px;
  background:var(--white);border-top:1.5px solid var(--c-ink);border-right:1.5px solid var(--c-ink);
  font:700 8.5px/1.2 var(--font-display);letter-spacing:.16em;text-transform:uppercase;
  display:block;-webkit-line-clamp:unset;overflow:visible}
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
    shelf("B · Literary", [book(k, "b") for k in BOOKS]),
    shelf("C · Label", [book(k, "c") for k in BOOKS]),
]
W, H = 1100, 1290
board = (f'<div style="width:{W}px;height:{H}px;background:var(--paper);color:var(--ink);font-family:var(--font-sans);'
         f'padding:56px 44px;overflow:hidden"><span class="tt-note">Cover type trials · actual shelf size, view at 100%'
         f'</span><div style="margin-top:40px">{"".join(rows)}</div></div>\n')
h = re.sub(r"<title>.*?</title>", "<title>Cover type trials</title>", head)
t = re.sub(r'"width":\d+,"height":\d+', f'"width":{W},"height":{H}', tail)
open(f"{P}/TypeTrials.dc.html", "w").write(h + STYLE + "</helmet>\n\n" + board + t)
print("ok")
