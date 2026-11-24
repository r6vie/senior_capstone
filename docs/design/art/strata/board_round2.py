"""Strata round 2 board: one refined cover at four sizes, and the shelf of eight refined covers."""
import json, sys
sys.path.insert(0, ".")
from boards import page, ROOT

A = json.load(open(sys.argv[1]))  # name -> url (blob or local path)
EXTRA = """<style>
.book-xl{width:472px;height:688px}
.book-xl::before{left:18px;top:18px;right:-18px;bottom:-18px;background-size:9px 9px;background-image:radial-gradient(circle,var(--fg) 2.3px,transparent 2.9px)}
.book-xl .book-cover{padding:56px 36px 34px 78px;border-width:4px}
.book-xl .book-cover::before{left:46px;width:3px}
.book-xl .book-title{font-size:54px;line-height:1.08}
.book-xl .book-author{font-size:18px}
.book-xl .cover-art{left:-4px;top:-4px;width:calc(100% + 8px);height:calc(100% + 8px)}
</style>"""
BOOKS = [
    ("The Night Shift Knows", "Maya Okafor", "lake-md"),
    ("Shipping Code Nobody Notices", "Dev Raman", "coast-md"),
    ("Lab Notebooks and Late Buses", "Priya Natarajan", "ranges-md"),
    ("Small Town, Big Contracts", "Sam Kowalski", "islands-md"),
    ("Translating for My Parents", "Lena Morales", "twins-md"),
    ("Why I Turned Down Grad School Twice", "Hana Sato", "summit-md"),
    ("From Orchestra Pit to Product Manager", "Kiera Lindgren", "terraces-md"),
    ("Starting a Podcast With No Audience", "Alexandra Okonkwo-Brennan", "dusk-md"),
]


def b(size, art, title="The Night Shift Knows", name="Maya Okafor"):
    cls = "book" + (f" book-{size}" if size else "")
    return (f'<div class="{cls}" aria-label="{title}, by {name}"><span class="book-cover">'
            f'<img class="cover-art" src="{A[art]}" alt=""><span class="book-title"><span class="ko">{title}</span></span>'
            f'<span class="book-author"><span class="ko">{name}</span></span></span></div>')


body = f"""
<div style="width: 1440px; height: 1000px; background: var(--paper); color: var(--ink); font-family: var(--font-sans); padding: 56px 64px; display: flex; gap: 88px; align-items: flex-start; overflow: hidden">
<div style="display: flex; flex-direction: column; gap: 14px">
<span class="frame-label">Cover · large, as on the book page</span>
{b("xl", "lake-xl")}
</div>
<div style="display: flex; flex-direction: column; gap: 56px; padding-top: 30px">
<div style="display: flex; flex-direction: column; gap: 14px">
<span class="frame-label">Feature and shelf sizes</span>
<div style="display: flex; align-items: flex-end; gap: 48px">{b("lg", "lake-lg")}{b("", "lake-md")}{b("sm", "lake-sm")}</div>
</div>
<div style="display: flex; flex-direction: column; gap: 14px; width: 760px">
<span class="frame-label">The other seven designs, redrawn the same way</span>
<div style="display: grid; grid-template-columns: repeat(4, 122px); gap: 36px 28px">{"".join(b("", a, t, n) for t, n, a in BOOKS[1:])}</div>
</div>
</div>
</div>
"""
src = page("Strata cover, round 2", 1440, 1000, body).replace("</helmet>", EXTRA + "\n</helmet>")
out = sys.argv[2]
open(out, "w").write(src)
print("ok")
