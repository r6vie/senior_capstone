"""Getting started page: the covers animating in (board StudioPaint). Josef, 2026-11-23: the slow timing is only for
watercolour on the sign-in intro (board StartPaint); the book reveal, your picks and the design studio all use the
fast version, for watercolour and strata alike. Watercolour paints itself in (art/watercolor/paint_anim.py), strata
builds itself bottom to top, each slab settling into place (art/strata/strata_anim.py). For review each clip holds
its finished cover for 2 s, then repeats.

python3 studio_paint_board.py <out.dc.html> wc=<blob> lake=<blob> desert=<blob> ... (one per strata key)"""
import sys

dst = sys.argv[1]
ids = dict(a.split("=", 1) for a in sys.argv[2:])
FONTS = ("https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700;800&amp;family=Newsreader:ital,"
         "opsz,wght@0,6..72,400..700;1,6..72,400..500&amp;family=IBM+Plex+Sans:wght@400;500;600&amp;display=swap")

# strata set 1: key, title, full name, cover ink (from the canvas boards and set-1/manifest.json)
STRATA = [("lake", "The Night Shift Knows", "Maya Okafor", "#16302e"),
          ("desert", "What the Desert Teaches", "Lucía Hernández-Brooks", "#6a3525"),
          ("coast", "Notes From the Edge", "Callum O’Donnell", "#26304f"),
          ("valley", "A Slow Harvest", "Mei Lin Okada", "#263a2d"),
          ("karst", "Two Years Upriver", "Wen Zhao", "#2f4637"),
          ("winter", "Long Nights, Clear Skies", "Ingrid Solberg", "#252a4c"),
          ("lagoon", "Island Time Isn’t Slow", "Keoni Akana", "#1f4f5a"),
          ("city", "Small Bets, Big City", "Danielle Owens", "#2f3448"),
          ("forest", "Room to Grow", "Noah Bergstrom", "#283d2e"),
          ("fields", "The Patient Field", "Dewi Santoso", "#3d5a32")]


def book(blob, title, name, ink, knockout, cls="bk"):
    ko = "background:#fff;padding:0 3px 1px;margin-left:-3px;" if knockout else ""
    return (f'<div class="{cls}" aria-label="{title}, by {name}"><video autoplay muted loop playsinline aria-hidden="true" '
            f'src="/_blob/{blob}"></video><span class="tt" style="color:{ink}">{title}</span>'
            f'<span class="nm" style="color:{ink};{ko}">{name}</span></div>')


grid = "".join(book(ids[k], t, n, c, True, "bk sm") for k, t, n, c in STRATA)

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
.sp .lede{{margin:0;font:400 18px/1.5 'IBM Plex Sans';max-width:1000px}}
.sp h2{{margin:56px 0 22px;font:700 20px/1 'Barlow Condensed';letter-spacing:.14em;text-transform:uppercase}}
.sp .row{{display:flex;gap:72px;align-items:flex-start}}
.sp .grid{{display:grid;grid-template-columns:repeat(5,176px);gap:44px 60px}}
.sp figure{{margin:0;display:grid;gap:22px}}
.sp figcaption{{font:400 15px/1.5 'IBM Plex Sans';color:#55554F;max-width:300px}}
.sp figcaption b{{display:block;color:#111;font:700 14px/1.3 'Barlow Condensed';letter-spacing:.14em;text-transform:uppercase;margin-bottom:4px}}
.bk{{position:relative;width:236px;height:344px;box-sizing:border-box;border:3px solid #111;border-radius:3px 6px 6px 3px;overflow:hidden;
  background:#fff;padding:27px 17px 19px 24px;display:flex;flex-direction:column;isolation:isolate}}
.bk::before{{content:"";position:absolute;left:11px;top:0;bottom:0;width:2px;background:#111;z-index:2}}
.bk video{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0}}
.bk .tt{{position:relative;z-index:1;font:800 39px/.92 'Barlow Condensed';letter-spacing:.01em;text-transform:uppercase;text-wrap:balance}}
.bk .nm{{position:relative;z-index:1;align-self:flex-start;margin-top:13px;font:700 17px/1.25 'Barlow Condensed';letter-spacing:.16em;text-transform:uppercase}}
.bk.sm{{width:176px;height:257px;border-width:2px;padding:20px 13px 14px 18px}}
.bk.sm::before{{left:8px;width:1.5px}}
.bk.sm .tt{{font-size:29px}}
.bk.sm .nm{{margin-top:10px;font-size:13px}}
.sp .rules{{display:grid;grid-template-columns:repeat(3,1fr);gap:32px;margin-top:56px}}
.sp .rules div{{border-top:2px solid #111;padding-top:12px;font:400 15px/1.55 'IBM Plex Sans';color:#55554F}}
.sp .rules b{{display:block;color:#111;font:700 14px/1.3 'Barlow Condensed';letter-spacing:.14em;text-transform:uppercase;margin-bottom:6px}}
</style>
</helmet>
<div class="sp"><span class="cap">Picks, the reveal and the design studio</span>
<h1>Covers that make themselves as they appear</h1>
<p class="lede">One fast timing, about 4 seconds, wherever a cover appears for you: the book reveal, your picks and the design studio. Watercolour paints itself in, glaze by glaze. Strata builds itself from the foot of the cover to the top, racing up at first and slowing as it climbs, each slab drifting down into its course, the top ones settling slowest. The slow, 25-second painting is only for watercolour on the sign-in intro (the board to the left). Each clip here holds on its finished cover for 2 seconds, then repeats.</p>
<h2>The two styles side by side</h2>
<div class="row">
<figure>{book(ids["wc"], "Above the Tree Line", "Ingrid Solberg", "#23415a", False)}<figcaption><b>Watercolour · paints in</b>About 4 s, ending on the finished cover.</figcaption></figure>
<figure>{book(ids["lake"], "The Night Shift Knows", "Maya Okafor", "#16302e", True)}<figcaption><b>Strata · builds in</b>About 4 s, every slab settled by 3.5 s, ending on the cover pixel for pixel.</figcaption></figure>
</div>
<h2>Strata · all ten covers, at shelf size</h2>
<div class="grid">{grid}</div>
<div class="rules">
<div><b>Ends on the cover itself</b>The last frame is the cover image, so the video hands over to the still with no jump.</div>
<div><b>Reduced motion</b>Shows the finished cover straight away.</div>
<div><b>Never on the sign-in intro</b>Strata animates only in the reveal, the picks and the studio; the intro loop is watercolour only.</div>
</div></div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":1760,"height":1880}}}}'>
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
