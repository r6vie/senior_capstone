import sys
sys.path.insert(0, ".")
import boards
from boards import page, ROOT

XL = "/_blob/2d5e74e7345b1b6040d7541341b7a796"
MD = "/_blob/b16ee09387420d4a5df9e3c8c0f05812"
EXTRA = """<style>
.book-xl{width:472px;height:688px}
.book-xl::before{left:18px;top:18px;right:-18px;bottom:-18px;background-size:9px 9px;background-image:radial-gradient(circle,var(--fg) 2.3px,transparent 2.9px)}
.book-xl .book-cover{padding:56px 36px 34px 78px;border-width:4px}
.book-xl .book-cover::before{left:46px;width:3px}
.book-xl .book-title{font-size:54px;line-height:1.08}
.book-xl .book-author{font-size:18px}
.book-xl .cover-art{left:-4px;top:-4px;width:calc(100% + 8px);height:calc(100% + 8px)}
.cover-art{object-fit:cover}
</style>"""


def b(size, art, tag="div"):
    cls = "book" + (f" book-{size}" if size else "")
    return (f'<{tag} class="{cls}" aria-label="The Night Shift Knows, by Maya Okafor"><span class="book-cover">'
            f'<img class="cover-art" src="{art}" alt=""><span class="book-title"><span class="ko">The Night Shift Knows</span></span>'
            f'<span class="book-author"><span class="ko">Maya Okafor</span></span></span></{tag}>')


def white(title, name):
    return (f'<div class="book" aria-label="{title}, by {name}"><span class="book-cover"><span class="book-title">{title}</span>'
            f'<span class="book-author">{name}</span></span></div>')


body = f"""
<div style="width: 1440px; height: 900px; background: var(--paper); color: var(--ink); font-family: var(--font-sans); padding: 56px 64px; display: flex; gap: 88px; align-items: flex-start; overflow: hidden">
<div style="display: flex; flex-direction: column; gap: 14px">
<span class="frame-label">Cover · large, as on the book page</span>
{b("xl", XL)}
</div>
<div style="display: flex; flex-direction: column; gap: 56px; padding-top: 30px">
<div style="display: flex; flex-direction: column; gap: 14px">
<span class="frame-label">Feature and shelf sizes</span>
<div style="display: flex; align-items: flex-end; gap: 48px">{b("lg", XL)}{b("", MD)}{b("sm", MD)}</div>
</div>
<div style="display: flex; flex-direction: column; gap: 14px; width: 640px">
<span class="frame-label">On a shelf (the others still white)</span>
<div class="shelf-books">{white("Shipping Code Nobody Notices", "Dev Raman")}{b("", MD)}{white("Lab Notebooks and Late Buses", "Priya Natarajan")}{white("Small Town, Big Contracts", "Sam Kowalski")}</div>
<div class="ledge" style="margin: 18px 0 0 -8px"></div>
</div>
</div>
</div>
"""
src = page("Voxel cover", 1440, 900, body).replace("</helmet>", EXTRA + "\n</helmet>")
(ROOT / "project" / "VoxelValley.dc.html").write_text(src)
print("ok")
