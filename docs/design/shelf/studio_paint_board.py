"""Picks and the design studio: the covers animating in (demo). Josef, 2026-11-23: watercolour and strata covers both
animate when they appear as your picks and when you choose a design in the studio, "all nice and unified", on the
same clock; the studio's version is quicker. Watercolour paints itself in (art/watercolor/paint_anim.py), strata
builds itself slab by slab (art/strata/strata_anim.py). For review each clip holds its finished cover, then loops.

python3 studio_paint_board.py <out.dc.html> wc_reveal=<blob> wc_quick=<blob> st_reveal=<blob> st_quick=<blob>"""
import sys

dst = sys.argv[1]
ids = dict(a.split("=", 1) for a in sys.argv[2:])
FONTS = ("https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700;800&amp;family=Newsreader:ital,"
         "opsz,wght@0,6..72,400..700;1,6..72,400..500&amp;family=IBM+Plex+Sans:wght@400;500;600&amp;display=swap")


def book(blob, title, name, ink, knockout):
    ko = "background:#fff;padding:0 3px 1px;margin-left:-3px;" if knockout else ""
    return (f'<div class="bk" aria-label="{title}, by {name}"><video autoplay muted loop playsinline aria-hidden="true" '
            f'src="/_blob/{blob}"></video><span class="tt" style="color:{ink}">{title}</span>'
            f'<span class="nm" style="color:{ink};{ko}">{name}</span></div>')


WC = ("Above the Tree Line", "Ingrid Solberg", "#23415a", False)
ST = ("The Night Shift Knows", "Maya Okafor", "#16302e", True)

html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Picks and the studio · covers animating in</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<link rel="stylesheet" href="{FONTS}">
<style>
body{{margin:0}}
.sp{{width:1760px;box-sizing:border-box;padding:56px 64px 72px;background:#FAFAF7;color:#111;font-family:'IBM Plex Sans',sans-serif}}
.sp .cap{{display:inline-block;padding:6px 10px;background:#111;color:#FAFAF7;font:700 13px/1 'Barlow Condensed';letter-spacing:.14em;text-transform:uppercase}}
.sp h1{{margin:18px 0 10px;font:600 54px/1.04 'Newsreader',serif;letter-spacing:-.015em}}
.sp .lede{{margin:0;font:400 18px/1.5 'IBM Plex Sans';max-width:980px}}
.sp h2{{margin:56px 0 22px;font:700 20px/1 'Barlow Condensed';letter-spacing:.14em;text-transform:uppercase}}
.sp .row{{display:flex;gap:72px;align-items:flex-start}}
.sp figure{{margin:0;display:grid;gap:22px}}
.sp figcaption{{font:400 15px/1.5 'IBM Plex Sans';color:#55554F;max-width:300px}}
.sp figcaption b{{display:block;color:#111;font:700 14px/1.3 'Barlow Condensed';letter-spacing:.14em;text-transform:uppercase;margin-bottom:4px}}
.bk{{position:relative;width:236px;height:344px;box-sizing:border-box;border:3px solid #111;border-radius:3px 6px 6px 3px;overflow:hidden;
  background:#fff;padding:27px 17px 19px 24px;display:flex;flex-direction:column;isolation:isolate}}
.bk::before{{content:"";position:absolute;left:11px;top:0;bottom:0;width:2px;background:#111;z-index:2}}
.bk::after{{content:"";position:absolute;z-index:-2;left:8px;top:8px;right:-8px;bottom:-8px}}
.bk video{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0}}
.bk .tt{{position:relative;z-index:1;font:800 39px/.92 'Barlow Condensed';letter-spacing:.01em;text-transform:uppercase;text-wrap:balance}}
.bk .nm{{position:relative;z-index:1;align-self:flex-start;margin-top:13px;font:700 17px/1.25 'Barlow Condensed';letter-spacing:.16em;text-transform:uppercase}}
.sp .rules{{display:grid;grid-template-columns:repeat(3,1fr);gap:32px;margin-top:56px}}
.sp .rules div{{border-top:2px solid #111;padding-top:12px;font:400 15px/1.55 'IBM Plex Sans';color:#55554F}}
.sp .rules b{{display:block;color:#111;font:700 14px/1.3 'Barlow Condensed';letter-spacing:.14em;text-transform:uppercase;margin-bottom:6px}}
</style>
</helmet>
<div class="sp"><span class="cap">Picks and the design studio · demo</span>
<h1>Covers that make themselves as they appear</h1>
<p class="lede">The same clock for both styles. Watercolour paints itself in, glaze by glaze. Strata builds itself: each layer of the scene is laid far to near, course by course up from its foot, every slab dropping into place. Strata stays off the sign-in page; it animates for your picks and in the design studio. Each clip here holds on the finished cover, then repeats.</p>
<h2>Your picks and the book reveal · full timing</h2>
<div class="row">
<figure>{book(ids["wc_reveal"], *WC)}<figcaption><b>Watercolour · paints in</b>All glazes landed by about 12 s; ends on the finished cover at 13.5 s.</figcaption></figure>
<figure>{book(ids["st_reveal"], *ST)}<figcaption><b>Strata · builds in</b>The sun, the far haze, the mountain from its foot up, the lake, the shore and trees. Every slab in by about 12 s; the same 13.5 s.</figcaption></figure>
</div>
<h2>The design studio · quick, when you choose a design</h2>
<div class="row">
<figure>{book(ids["wc_quick"], *WC)}<figcaption><b>Watercolour · quick</b>The same painting at 0.3 of the time: about 4 s.</figcaption></figure>
<figure>{book(ids["st_quick"], *ST)}<figcaption><b>Strata · quick</b>The same build at 0.3 of the time: about 4 s.</figcaption></figure>
</div>
<div class="rules">
<div><b>Ends on the cover itself</b>The last frame is the cover image, pixel for pixel, so the video hands over to the still with no jump.</div>
<div><b>Reduced motion</b>Shows the finished cover straight away.</div>
<div><b>Not on the sign-in page</b>Strata only animates for picks and in the studio; the sign-in loop is watercolour only.</div>
</div></div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":1760,"height":1640}}}}'>
class Component extends DCLogic {{
renderVals() {{
return {{}};
}}
}}
</script>
</body>
</html>
"""
open(dst, "w").write(html)
print("ok")
