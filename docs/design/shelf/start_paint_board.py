"""Getting started page: the blank book painting itself, a review board for Josef to workshop the cycle
(art/watercolor/paint_anim.py). StartJoin.dc.html is not touched: this board copies its styles and draws the same
left half (the dot ground, the Librarian's caption box, the book standing on the shelf bar), with the moving cover
in place of the blank one, at desktop (270px) and phone (150px) widths.

python3 start_paint_board.py <StartJoin.dc.html> <out.dc.html> mp4=<blob> webm=<blob> poster=<blob> [scene=<name>]"""
import sys

src, dst = sys.argv[1], sys.argv[2]
ids = dict(a.split("=", 1) for a in sys.argv[3:])
html = open(src).read()
head = html[:html.index("</helmet>")]
head = head.replace(head[head.index("<title>"):head.index("</title>") + 8], "<title>Blank book · painting itself</title>")

css = """
<style>
.kitwrap .demo{display:flex;gap:48px;align-items:flex-start;margin-top:8px}
.kitwrap .stagebox{border:2px solid var(--ink);background:#fff;overflow:hidden;flex:none}
.K3 .wb .fc.paint{padding:0;overflow:hidden}
.K3 .wb .fc.paint video,.K3 .wb .fc.paint img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block;z-index:0}
.K3 .wb .fc.paint::before{z-index:2}
.K3 .wb .fc.paint .nm{position:absolute;z-index:3;left:calc(var(--w,260px)*.15);top:calc(var(--w,260px)*.13);margin:0;
  font:700 calc(var(--w,260px)*.046)/1.2 var(--font-display);letter-spacing:.16em;text-transform:uppercase;color:var(--ink)}
.kitwrap .cyc{list-style:none;margin:0;padding:0;display:grid;gap:10px}
.kitwrap .cyc li{display:grid;grid-template-columns:92px minmax(0,1fr);gap:12px;font:400 15px/1.5 var(--font-sans);color:var(--ink-2)}
.kitwrap .cyc b{font:700 14px/1.5 var(--font-display);letter-spacing:.14em;text-transform:uppercase;color:var(--ink)}
</style>
"""


def book(w):
    return (f'<div class="wb" style="--w:{w}px"><div class="fc paint">'
            f'<video autoplay muted loop playsinline poster="/_blob/{ids["poster"]}" aria-hidden="true">'
            f'<source src="/_blob/{ids["webm"]}" type="video/webm"><source src="/_blob/{ids["mp4"]}" type="video/mp4"></video>'
            f'<p class="nm">Ingrid Solberg</p></div></div>')


def half(w, width, height, pad, cap):
    return (f'<div class="stagebox" style="width:{width}px;height:{height}px"><div class="fr KK K3" style="height:{height}px">'
            f'<section class="au-l dots" style="height:{height}px;border-right:0;padding-top:{pad}px">'
            f'<div class="capbox" style="margin:0 {pad}px"><p style="font-size:{cap}px">You are the author of the book you haven’t written yet.</p></div>'
            f'<div><div class="au-stage">{book(w)}</div><div class="shelfbar" style="margin-bottom:{pad + 16}px"></div></div>'
            f'</section></div></div>')


body = f"""
<div class="kitwrap"><header><span class="caption">Getting started · the blank book, moving</span>
<h1>The unwritten book paints itself</h1>
<p class="lede">A test on one cover, the alpine lake. The cover’s own glazes are laid back down in the order they were painted: each lands where the brush first touches its shape and spreads out wet. The finished cover rests, washes back to the paper, and the next cover begins. Here it loops on the one cover.</p></header>
<h2 class="sec">Desktop · the left half of Join</h2>
<div class="demo">{half(270, 700, 720, 56, 32)}
<div style="display:grid;gap:28px;max-width:560px">
<ul class="cyc">
<li><b>0–22 s</b><span>The glazes go down in painting order: sky, far hills, the peak’s faces, the forest, the lake, the reflection, the wind lifted out.</span></li>
<li><b>22–27 s</b><span>The finished cover rests.</span></li>
<li><b>27–32 s</b><span>It washes back to the paper.</span></li>
<li><b>32–33.5 s</b><span>Clean paper, then the next cover (in the app, a different one each time).</span></li></ul>
<p style="margin:0;font:400 15px/1.55 var(--font-sans);color:var(--ink-2)">The name stands where StartJoin letters it as you type. Reduced motion shows the poster, the finished cover.</p>
</div></div>
<h2 class="sec">Phone · 150px</h2>
<div class="demo">{half(150, 390, 520, 18, 22)}</div>
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":1760,"height":1900}}}}'>
class Component extends DCLogic {{
renderVals() {{
return {{}};
}}
}}
</script>
</body>
</html>
"""
open(dst, "w").write(head + css + "</helmet>\n" + body)
print("ok")
