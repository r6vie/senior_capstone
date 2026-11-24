"""Brand round 2 for the canvas page "Brand" (Josef, 2026-11-23: round 1 was "too basic"; new fonts are welcome, to move
the site away from the AI-generated look).

python3 docs/design/shelf/brand2_boards.py [--preview DIR --art ART_ROOT]

Brand2Think says what changed and why; Brand2A..C are three identities, each with its own typefaces, colour, a
crafted mark, the site set in it, and marketing.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from brand_boards import ART, LOCAL_ART, PROJECT  # noqa: E402

PAINTED = {  # brand round 2, identity C: the mark painted per member (art/watercolor/brandmark.py)
    "lake": "97debc3b6fd8667339b8021cc1df06f9",
    "coast": "6a62a3fbbb6d3db21fdf532dff8f2cfc",
    "forest": "9675b8a1a88c3b88ff5de795ddde075b",
    "dusk": "7991735ec57e9b75671e3ca9bdbc5215",
    "mesa": "f4c919d0bb76f25c07677d8573b031c8",
}

GF = "https://fonts.googleapis.com/css2?"
FONTS = {
    "think": GF + "family=Gloock&amp;family=Big+Shoulders+Display:wght@800;900&amp;family=Libre+Franklin:wght@400;600"
    "&amp;family=Libre+Caslon+Display&amp;family=Libre+Caslon+Text:ital@0;1&amp;family=Hanken+Grotesk:wght@400;500;600;700"
    "&amp;family=Literata:ital,opsz,wght@1,7..72,400&amp;display=swap",
    "A": GF + "family=Gloock&amp;family=Literata:ital,opsz,wght@0,7..72,400;1,7..72,400"
    "&amp;family=Hanken+Grotesk:wght@400;500;600;700&amp;display=swap",
    "B": GF + "family=Big+Shoulders+Display:wght@500;700;800;900&amp;family=Libre+Franklin:ital,wght@0,400;0,500;0,600;0,700;1,400&amp;display=swap",
    "C": GF + "family=Libre+Caslon+Display&amp;family=Libre+Caslon+Text:ital,wght@0,400;0,700;1,400"
    "&amp;family=Schibsted+Grotesk:wght@400;500;600;700&amp;display=swap",
}

_n = [0]


def uid(p):
    _n[0] += 1
    return f"{p}{_n[0]}"


# ---------------------------------------------------------------- A · the magpie

MAG_BODY = (
    "M34 63.5 L50 56.5 C52 47 62 45 70 48.5 C78 52 82 60 86 68 C100 80 116 90 130 99 L189 130 L195 137 L186 154"
    " L124 114 C114 122 104 128 94 128 C78 128 66 118 62 104 C58 92 56 80 56 72 C54 68 52 66.5 50 66.5 Z"
)
MAG_TAIL = "M128 98 L189 130 L195 137 L186 154 L122 113 Z"
MAG_BOOK = (
    "M46 148 H174 V151.5 H47 C41 151.5 38.5 157 38.5 162.5 C38.5 168 41 173.5 47 173.5 H174 V177 H46"
    " C37 177 32 170 32 162.5 C32 155 37 148 46 148 Z"
)
# Gouge cuts: the slivers of paper a linocut tool leaves, following the form of breast, wing and tail.
MAG_CUTS = (
    "M60 72 L64 70.6 L61.4 86 Z",
    "M58.6 90 L62 88.6 L63 100 Z",
    "M140 108 L176 129 L175 131 Z",
    "M146 116 L181 137.6 L179.6 139.4 Z",
    "M108 103 L132 113 L131.4 114.6 Z",
)


def magpie_g(ink, paper, sheen=None, book=True):
    tail = f'<path d="{MAG_TAIL}" fill="{sheen}"/>' if sheen else ""
    b = (
        f'<path d="{MAG_BOOK}" fill="{ink}"/>'
        f'<path d="M46 156.5 H170 M46 162.5 H170 M46 168.5 H170" stroke="{ink}" stroke-width="1.6"/>'
        if book else ""
    )
    return (
        f'<path d="{MAG_BODY}" fill="{ink}"/>{tail}'
        f'<path d="M89 126 L87 147 M98 126 L100 147" stroke="{ink}" stroke-width="3.2" fill="none"/>'
        f'<path d="M80 147 H107" stroke="{ink}" stroke-width="3" fill="none"/>{b}'
        f'<path d="M90 90 C106 101 126 111 152 123" stroke="{paper}" stroke-width="1.3" fill="none" stroke-linecap="round"/>'
        f'<circle cx="63" cy="56.5" r="2.2" fill="{paper}"/>'
        f'<path d="M70 104 C74 116 86 124 98 124 C108 122 114 116 116 110 C104 108 88 104 78 98 Z" fill="{paper}"/>'
        f'<path d="M82 77 C96 84 110 92 122 99 C112 99.5 98 94 85 85 Z" fill="{paper}"/>'
        + "".join(f'<path d="{c}" fill="{paper}"/>' for c in MAG_CUTS)
    )


def magpie(size, ink="#141414", paper="#F6F2E9", sheen=None, book=True, bg=None):
    bgr = f'<rect width="200" height="200" fill="{bg}"/>' if bg else ""
    if book:
        vb, w = "24 36 176 146", size * (176 / 146)
    elif size <= 40:   # small: the whole bird, cropped tight, so it is not a speck
        vb, w = "31 44 166 106", size * (166 / 106)
    else:
        vb, w = "28 38 172 120", size * (172 / 120)
    return (f'<svg width="{w:.0f}" height="{size}" viewBox="{vb}" aria-hidden="true">{bgr}'
            f'{magpie_g(ink, paper, sheen, book)}</svg>')


def colophon(size, ink="#141414", paper="#F6F2E9", sheen=None):
    """The magpie on its book inside a publisher's oval, the name round the top and the place round the foot."""
    top, bot = uid("ct"), uid("cb")
    return (
        f'<svg width="{size*0.86:.0f}" height="{size}" viewBox="0 0 172 200" aria-hidden="true">'
        f'<ellipse cx="86" cy="100" rx="82" ry="96" fill="{paper}" stroke="{ink}" stroke-width="3.4"/>'
        f'<ellipse cx="86" cy="100" rx="62" ry="76" fill="none" stroke="{ink}" stroke-width="1.1"/>'
        f'<path id="{top}" d="M19 100 A67 81 0 0 1 153 100" fill="none"/>'
        f'<path id="{bot}" d="M13 100 A73 87 0 0 0 159 100" fill="none"/>'
        f'<text font-family="Gloock" font-size="16" letter-spacing="4.5" fill="{ink}" text-anchor="middle">'
        f'<textPath href="#{top}" startOffset="50%">TROVE</textPath></text>'
        f'<text font-family="Hanken Grotesk" font-weight="600" font-size="6.6" letter-spacing="2.4" fill="{ink}" '
        f'text-anchor="middle"><textPath href="#{bot}" startOffset="50%">CLEVELAND · MMXXVI</textPath></text>'
        f'<g transform="translate(19 37) scale(0.58)">{magpie_g(ink, paper, sheen)}</g></svg>'
    )


# ---------------------------------------------------------------- B · overprint

BLUE, SUN, RPAPER = "#00838A", "#FFE800", "#F3EFE4"   # riso teal and yellow; they overprint green


def grain_defs(fid):
    return (
        f'<filter id="{fid}" x="0" y="0" width="100%" height="100%">'
        '<feTurbulence type="fractalNoise" baseFrequency="1.3" numOctaves="2" seed="4" result="n"/>'
        '<feColorMatrix in="n" type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 -0.9 1.3" result="m"/>'
        '<feComposite in="SourceGraphic" in2="m" operator="in"/></filter>'
    )


def two_books(size, a=BLUE, b=SUN, grain=True):
    """Two books leaning into each other, printed in two inks; where they overlap the inks make a third colour."""
    if size <= 32:   # small: one teal book, so the mark reads as a book and not a striped flag
        return (f'<svg width="{size}" height="{size}" viewBox="0 0 120 120" aria-hidden="true">'
                f'<g transform="translate(60 60) rotate(-8)"><rect x="-30" y="-46" width="60" height="92" fill="{a}"/>'
                f'<rect x="-21" y="-46" width="6" height="92" fill="{RPAPER}"/></g></svg>')
    fid = uid("gr")
    f = f' filter="url(#{fid})"' if grain else ""
    book = (
        '<rect x="-24" y="-38" width="48" height="76"/>'
    )
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 120 120" aria-hidden="true" style="isolation:isolate">'
        f'<defs>{grain_defs(fid)}</defs>'
        f'<g{f} style="mix-blend-mode:multiply" fill="{a}" transform="translate(46 62) rotate(-11)">{book}'
        f'<rect x="-17" y="-38" width="2.4" height="76" fill="{RPAPER}"/><path d="M16 -34 V34 M19.5 -34 V34" stroke="{RPAPER}" stroke-width="1.2"/></g>'
        f'<g{f} style="mix-blend-mode:multiply" fill="{b}" transform="translate(74 62) rotate(11)">{book}'
        f'<rect x="-17" y="-38" width="2.4" height="76" fill="#fff" fill-opacity=".55"/><path d="M16 -34 V34 M19.5 -34 V34" stroke="#fff" stroke-opacity=".6" stroke-width="1.2"/></g></svg>'
    )


def ov_word(px, a=BLUE, b=SUN, dx=0.03, dy=0.022):
    return (
        f'<span class="ovw" style="font-size:{px}px"><span style="color:{b};transform:translate({px*dx:.1f}px,{px*dy:.1f}px)">trove</span>'
        f'<span style="color:{a}">trove</span></span>'
    )


# ---------------------------------------------------------------- C · wet ink

def painted(key, w):
    return f'<img class="pm" src="/_blob/{PAINTED[key]}" alt="" style="width:{w}px;height:auto">'


def _wet_page(side):
    """The painted page's outline (art/watercolor/brandmark.py), as a flat path for sizes where paint turns to mud."""
    import math
    ox, n = 100 + side * 90, 16
    head = [(ox + (100 - ox) * i / n, 26 + 30 * (i / n) ** 1.6 - 6 * math.sin(math.pi * i / n)) for i in range(n + 1)]
    foot = [(ox + (100 - ox) * i / n, 116 + 20 * (i / n) ** 1.6 - 5 * math.sin(math.pi * i / n)) for i in range(n + 1)]
    inner = [(100 - side * (3 + 7 * math.sin(math.pi * i / n)), head[-1][1] + (foot[-1][1] - head[-1][1]) * i / n)
             for i in range(n + 1)]
    pts = head + inner + foot[::-1]
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + " Z"


def wet_flat(size, ink="#1C2230", a="#E6C487", b="#5B74B8"):
    """The house mark at 32px and under: the same open book with the paint flattened, the two page colours and the
    dark lens where they overlap, so it stays the painted mark rather than a stock icon."""
    cid = uid("wf")
    left, right = _wet_page(-1), _wet_page(1)
    return (f'<svg width="{size*1.43:.0f}" height="{size}" viewBox="6 18 188 128" aria-hidden="true">'
            f'<defs><clipPath id="{cid}"><path d="{right}"/></clipPath></defs>'
            f'<path d="{left}" fill="{a}"/><path d="{right}" fill="{b}"/>'
            f'<path d="{left}" fill="{ink}" fill-opacity=".8" clip-path="url(#{cid})"/></svg>')


def wet_lock(px, key="lake", ink="#1C2230", stacked=True):
    if stacked:
        return (f'<span class="wl" style="font-size:{px}px;color:{ink}">{painted(key, int(px*1.9))}'
                f'<span class="wlw">Trove</span></span>')
    face = "" if px >= 40 else "font-family:'Libre Caslon Text';"   # the display cut goes spindly below ~40px
    return (f'<span class="wl wlh" style="font-size:{px}px;color:{ink}">{painted(key, int(px*1.45))}'
            f'<span class="wlw" style="{face}">Trove</span></span>')


# ---------------------------------------------------------------- shared

def cover(key, w, font, weight, tt="none", ls="0", lh=".95", size=0.15, shadow=None, rot=0):
    blob, ink, title, name = ART[key]
    sh = f"box-shadow:6px 6px 0 {shadow};" if shadow else ""
    return (
        f'<div class="cv" style="width:{w}px;height:{w*1.457:.0f}px;padding:{w*.11:.0f}px {w*.07:.0f}px {w*.06:.0f}px {w*.11:.0f}px;{sh}transform:rotate({rot}deg)" aria-label="{title}, by {name}">'
        f'<img src="/_blob/{blob}" alt="">'
        f'<span class="ct" style="color:{ink};font-family:{font};font-weight:{weight};text-transform:{tt};letter-spacing:{ls};'
        f'line-height:{lh};font-size:{w*size:.1f}px">{title}</span>'
        f'<span class="cn" style="color:{ink};background:{"transparent" if ink.lower() == "#f6efe0" else "#fff"};'
        f'font-size:{max(6.5, w*0.058):.1f}px">{name}</span></div>'
    )


BASE = """
body{margin:0}
.b2{width:1760px;padding:72px 80px 96px;background:var(--pg);color:var(--ink);font-family:var(--ui);font-size:16px;line-height:1.5}
.b2,.b2 *{box-sizing:border-box}
:where(.b2) :is(h1,h2,h3,p,ul,ol,figure,blockquote){margin:0;padding:0}
.ey{font:600 13px var(--ui);letter-spacing:.16em;text-transform:uppercase;color:var(--ink2)}
.h1{font-family:var(--disp);font-size:84px;line-height:1;letter-spacing:-.01em;margin-top:16px;font-weight:var(--dw,400)}
.lede{font-family:var(--voice);font-style:italic;font-size:26px;line-height:1.35;max-width:980px;margin-top:20px}
.story{margin-top:16px;max-width:980px;font-size:17px;color:var(--ink2)}
.sec{margin-top:88px}
.sh{display:flex;align-items:baseline;gap:20px;border-top:2px solid var(--ink);padding-top:14px;margin-bottom:32px}
.sh b{font-family:var(--disp);font-weight:var(--dw,400);font-size:36px;line-height:1}
.sh span{color:var(--ink2);font-size:15px}
.cap{display:block;margin-top:10px;font:600 12px var(--ui);letter-spacing:.14em;text-transform:uppercase;color:var(--ink2)}
.row{display:flex;gap:44px;align-items:flex-end;flex-wrap:wrap}
.cv{position:relative;flex:none;border:1.5px solid var(--ink);display:flex;flex-direction:column;background:#fff;overflow:hidden}
.cv img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.cv::before{content:"";position:absolute;left:4.5%;top:0;bottom:0;width:1.5px;background:rgba(0,0,0,.55);z-index:1}
.cv .ct{position:relative;z-index:2;text-wrap:balance;max-width:90%}
.cv .cn{position:relative;z-index:2;align-self:flex-start;margin-top:.8em;padding:0 .35em 0 0;font-family:var(--ui);font-weight:700;letter-spacing:.14em;text-transform:uppercase;line-height:1.3}
.spec{display:grid;grid-template-columns:repeat(3,1fr);gap:36px}
.spec>div{border-top:1.5px solid var(--ink);padding-top:14px}
.spec .big{margin-top:14px;line-height:1}
.spec p{margin-top:12px;font-size:14px;color:var(--ink2);max-width:440px}
.sws{display:flex;gap:18px;flex-wrap:wrap}
.sw{width:168px}
.sw i{display:block;height:110px;border:1.5px solid var(--ink)}
.sw b{display:block;margin-top:10px;font:700 13px var(--ui);letter-spacing:.12em;text-transform:uppercase}
.sw span{display:block;font-size:13px;color:var(--ink2);line-height:1.35}
/* the site, set in this identity */
.site{border:2px solid var(--ink);background:var(--pg);overflow:hidden}
.s-top{display:flex;align-items:center;gap:40px;height:76px;padding:0 40px;border-bottom:1.5px solid var(--ink)}
.s-top nav{display:flex;gap:28px;font:var(--navf);letter-spacing:var(--navls,0);text-transform:var(--navtt,none)}
.s-top nav b{font-weight:inherit;padding:6px 0}
.s-top nav b[aria-current]{border-bottom:2px solid var(--ink)}
.s-search{margin-left:auto;width:240px;height:42px;border:1.5px solid var(--ink);border-radius:999px;display:flex;align-items:center;padding:0 18px;font-size:14px;color:var(--ink2);background:#fff}
.s-av{width:42px;height:42px;border-radius:999px;border:1.5px solid var(--ink);display:grid;place-items:center;font-weight:700;background:#fff}
.s-band{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:40px;padding:44px 40px 48px;background:var(--band);color:var(--bandfg)}
.s-cap{font:600 13px var(--ui);letter-spacing:.16em;text-transform:uppercase;opacity:.8}
.s-title{font-family:var(--disp);font-weight:var(--dw,400);font-size:56px;line-height:1.02;margin-top:14px;max-width:760px}
.s-by{margin-top:12px;font:600 14px var(--ui);letter-spacing:.12em;text-transform:uppercase;opacity:.8}
.s-voice{margin-top:20px;font-family:var(--voice);font-style:italic;font-size:22px;line-height:1.38;max-width:720px}
.s-act{margin-top:28px;display:flex;align-items:center;gap:20px}
.s-btn{display:inline-flex;align-items:center;height:50px;padding:0 26px;background:#D42A27;color:#fff;font:var(--btnf);letter-spacing:var(--btnls,0);text-transform:var(--btntt,none)}
.s-note{font-size:14px;opacity:.8}
.s-shelf{padding:34px 40px 40px}
.s-sh{display:flex;align-items:baseline;gap:18px;margin-bottom:22px}
.s-sh b{font-family:var(--disp);font-weight:var(--dw,400);font-size:32px;line-height:1}
.s-sh i{flex:1;height:1.5px;background:var(--ink);align-self:center}
.s-sh span{font-size:14px}
.s-books{display:flex;gap:30px}
.mk{display:grid;grid-template-columns:repeat(12,1fr);gap:28px;align-items:start}
.pst{position:relative;overflow:hidden;border:1.5px solid var(--ink)}
.voice{display:grid;grid-template-columns:repeat(3,1fr);gap:32px}
.voice div{border-top:2px solid var(--ink);padding-top:16px;font-family:var(--disp);font-weight:var(--dw,400);font-size:34px;line-height:1.08}
.voice span{display:block;margin-top:12px;font:400 14px/1.45 var(--ui);color:var(--ink2)}
.btab{display:inline-flex;align-items:center;gap:10px;height:40px;padding:0 14px;background:#fff;border:1.5px solid #ccc;border-bottom:none;border-radius:8px 8px 0 0;font:13px system-ui}
.btab svg,.btab img{width:16px;height:16px}
.ovw{position:relative;display:inline-block;font-family:'Big Shoulders Display';font-weight:900;letter-spacing:.005em;line-height:.9;isolation:isolate}
.ovw span{display:block;position:relative;mix-blend-mode:multiply}
.ovw span:first-child{position:absolute;left:0;top:0}
.pm{display:block;object-fit:contain}
.wl{display:inline-flex;flex-direction:column;align-items:center;gap:.06em;line-height:1}
.wlh{flex-direction:row;gap:.22em}
.wlw{font-family:'Libre Caslon Display';letter-spacing:-.005em;line-height:.9}
.ico{width:120px;height:120px;border-radius:27px;display:grid;place-items:center;overflow:hidden}
"""


def doc(title, fonts, vars_css, extra_css, body, height):
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
<link rel="stylesheet" href="{fonts}">
<style>
{BASE}
.b2{{{vars_css}}}
{extra_css}
</style>
</helmet>
<div class="b2" style="height:{height}px;overflow:hidden">
{body}
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":1760,"height":{height}}}}}'>
class Component extends DCLogic {{
renderVals() {{
return {{}};
}}
}}
</script>
</body>
</html>
"""


def site(logo, books_html, shelf_name, title, voice, author):
    return f"""<div class="site"><div class="s-top">{logo}<nav><b aria-current="page">Shelf</b><b>My book</b><b>Checkouts</b><b>Past meets</b></nav>
<span class="s-search">Search by topic</span><span class="s-av">H</span></div>
<div class="s-band"><div><span class="s-cap">The Librarian recommends</span><div class="s-title">{title}</div><div class="s-by">by {author}</div>
<p class="s-voice">{voice}</p><div class="s-act"><span class="s-btn">Ask to check out</span><span class="s-note">A thirty-minute video call</span></div></div>
<div style="display:grid;place-items:center">{books_html[0]}</div></div>
<div class="s-shelf"><div class="s-sh"><b>{shelf_name}</b><i></i><span>See all</span></div><div class="s-books">{books_html[1]}</div></div></div>"""


def spec(cols):
    return '<div class="spec">' + "".join(
        f'<div><span class="cap" style="margin-top:0">{h}</span><div class="big" style="{st}">{sample}</div><p>{why}</p></div>'
        for h, st, sample, why in cols) + "</div>"


def swatches(items):
    return '<div class="sws">' + "".join(
        f'<div class="sw"><i style="background:{c}"></i><b>{n}</b><span>{r}</span></div>' for c, n, r in items) + "</div>"


def header(letter, name, idea, story):
    return (f'<span class="ey">Brand · round 2 · identity {letter}</span><h1 class="h1">{name}</h1>'
            f'<p class="lede">{idea}</p><p class="story">{story}</p>')


# ---------------------------------------------------------------- boards

def board_a():
    ink, paper, sheen, cream = "#141414", "#F6F2E9", "#1F5C66", "#EFE8D8"
    vars_css = (f"--pg:{paper};--ink:{ink};--ink2:#5B574E;--disp:'Gloock',Georgia,serif;--voice:'Literata',Georgia,serif;"
                f"--ui:'Hanken Grotesk',system-ui,sans-serif;--band:{ink};--bandfg:{paper};"
                "--navf:600 15px 'Hanken Grotesk';--navls:.04em;--btnf:600 16px 'Hanken Grotesk';--btnls:.02em")
    extra = ".wa2{font-family:'Gloock';line-height:1;letter-spacing:-.01em}.lkA{display:inline-flex;align-items:center;gap:.25em}"

    def lock(px, c=ink, p=paper, s=None):
        m = magpie(int(px*1.15), ink, paper, s)
        if c != ink:   # on a dark ground the bird stays black, on a cream plate, or it reads as a gull
            m = f'<span style="display:grid;place-items:center;width:{px*1.9:.0f}px;height:{px*1.9:.0f}px;border-radius:50%;background:{paper}">{magpie(int(px*1.05), ink, paper, s)}</span>'
        return f'<span class="lkA">{m}<span class="wa2" style="font-size:{px}px;color:{c}">Trove</span></span>'

    hero = f"""<section class="sec" style="margin-top:56px"><div style="display:grid;grid-template-columns:1.1fr 1fr;border:2px solid {ink};height:640px">
<div style="display:grid;place-items:center;background:{paper}">{colophon(470, ink, paper)}</div>
<div style="display:grid;place-items:center;background:{ink}">{lock(120, paper, ink, sheen)}</div></div></section>"""
    marks = f"""<section class="sec"><div class="sh"><b>The mark</b><span>The colophon for print and covers; the magpie alone for small places</span></div>
<div class="row">
<figure>{colophon(260, ink, paper)}<span class="cap">Colophon</span></figure>
<figure>{magpie(150)}<span class="cap">Magpie · 150</span></figure>
<figure>{magpie(150, ink, paper, sheen)}<span class="cap">With the sheen</span></figure>
<figure>{magpie(64, book=False)}<span class="cap">64</span></figure>
<figure>{magpie(32, book=False)}<span class="cap">32</span></figure>
<figure>{magpie(16, book=False)}<span class="cap">16</span></figure>
<figure><div class="ico" style="background:{paper};border:1.5px solid {ink}">{magpie(70, ink, paper, sheen)}</div><span class="cap">App icon</span></figure>
<figure><div class="ico" style="background:{cream};border:1.5px solid {ink}">{magpie(80, ink, cream, book=False)}</div><span class="cap">App icon · bird</span></figure>
</div><div style="margin-top:28px"><span class="btab">{magpie(16, book=False)}Trove · Shelf</span></div></section>"""
    story_sec = f"""<section class="sec"><div class="sh"><b>Why a magpie</b><span>Every publisher has a colophon; Trove publishes the books nobody has written yet</span></div>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:36px;font-size:17px">
<p><b style="font-family:Gloock;font-weight:400;font-size:26px;display:block;margin-bottom:6px">It keeps a trove.</b>Magpies are known for gathering bright things into one place. That is the shelf: what each member knows, kept where others can find it.</p>
<p><b style="font-family:Gloock;font-weight:400;font-size:26px;display:block;margin-bottom:6px">It is curious and it talks.</b>One of the cleverest birds, and a noisy, social one. Curiosity and conversation are the whole product.</p>
<p><b style="font-family:Gloock;font-weight:400;font-size:26px;display:block;margin-bottom:6px">It is black and white.</b>The ink-and-paper look stays, with one hidden colour: the blue-green sheen a magpie’s tail shows in the light. The thief story is folklore; the real bird keeps what it finds interesting, which is the point.</p></div></section>"""
    typ = f"""<section class="sec"><div class="sh"><b>Type</b><span>Three faces with a hand in them, none of the AI-site defaults</span></div>
{spec([
        ("Display · Gloock", "font-family:Gloock;font-size:88px", "Trove",
         "A high-contrast display serif with soft, inky joins: it looks printed, not rendered. Titles, the wordmark, shelf names."),
        ("Reading · Literata", "font-family:Literata;font-style:italic;font-size:34px;line-height:1.25",
         "Somebody here knows what you are trying to figure out.",
         "A book face made for long reading on screens. Italic for the Librarian’s voice; roman for blurbs and chapters."),
        ("Interface · Hanken Grotesk", "font-family:'Hanken Grotesk';font-weight:600;font-size:40px",
         "Ask to check out",
         "A plain grotesk with a little warmth, in place of Plex. Buttons, labels, forms."),
    ])}</section>"""
    col = f"""<section class="sec"><div class="sh"><b>Colour</b><span>Black and white with one sheen</span></div>
{swatches([(ink, "Ink", "The magpie, the type"), (paper, "Paper", "Warmer than now: an uncoated sheet"), (cream, "Board", "Panels and covers' ground"),
           (sheen, "Sheen", "The tail’s blue-green. Once per piece, never a button"), ("#D42A27", "Red", "Still only the one action")])}</section>"""
    books = (cover("lake", 236, "Gloock", 400, size=0.15, rot=2),
             "".join(cover(k, 176, "Gloock", 400, size=0.15) for k in ("desert", "coast", "forest", "beach", "city", "mesa")))
    site_sec = f"""<section class="sec"><div class="sh"><b>The site in it</b><span>The shelf, retyped: Gloock titles on the covers too</span></div>
{site(lock(34), books, "Changing course", "Above the Tree Line", "Six summers guiding in the Brooks Range, and what that does to how you plan anything.", "Ingrid Solberg")}</section>"""
    mkt = f"""<section class="sec"><div class="sh"><b>Marketing</b><span>Campus launch</span></div>
<div class="mk">
<div style="grid-column:span 4"><div class="pst" style="height:760px;background:{paper};padding:48px 40px;display:flex;flex-direction:column">
<div style="font-family:Gloock;font-size:64px;line-height:1">You are the author of the book you haven’t written yet.</div>
<div style="margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end">{colophon(250, ink, paper)}<span style="font:600 13px 'Hanken Grotesk';letter-spacing:.14em;text-transform:uppercase">trove · case.edu</span></div>
</div><span class="cap">Poster · 18×24</span></div>
<div style="grid-column:span 4;display:grid;gap:28px">
<div><div class="pst" style="height:420px;background:{ink};display:grid;place-items:center"><div style="width:250px;height:250px;border-radius:50%;background:{paper};display:grid;place-items:center;margin-top:-90px">{magpie(160, ink, paper, sheen)}</div>
<div style="position:absolute;left:32px;bottom:26px;font-family:Gloock;font-size:30px;color:{paper}">Somebody here knows. Go and ask.</div></div><span class="cap">Instagram post</span></div>
<div><div class="pst" style="height:280px;background:{cream};display:flex;align-items:center;gap:32px;padding:0 36px">{cover("coast", 140, "Gloock", 400, size=.15)}
<div><div style="font-family:Gloock;font-size:34px;line-height:1.05">New on the shelf</div><div style="font-family:Literata;font-style:italic;font-size:19px;margin-top:10px">Notes From the Edge, by Callum O’Donnell</div></div></div><span class="cap">Email · a new book</span></div>
</div>
<div style="grid-column:span 4;display:grid;gap:28px">
<div><div class="pst" style="height:430px;background:{cream};display:grid;place-items:center">
<div style="width:250px;height:330px;background:{paper};border:1.5px solid {ink};position:relative;display:grid;place-items:center">
<div style="position:absolute;top:-56px;left:50%;width:120px;height:76px;margin-left:-60px;border:3px solid {ink};border-bottom:none;border-radius:60px 60px 0 0"></div>{colophon(200, ink, paper)}</div></div><span class="cap">Tote</span></div>
<div style="display:flex;gap:28px;align-items:center"><div style="width:180px;height:180px;border-radius:999px;background:{cream};border:1.5px solid {ink};display:grid;place-items:center">{magpie(110, ink, cream, sheen, book=False)}</div>
<div><div style="width:150px;height:210px;background:{paper};border:1.5px solid {ink};display:grid;place-items:center">{colophon(120, ink, paper)}</div></div></div>
<span class="cap" style="margin-top:-18px">Sticker · bookplate for the launch table</span></div>
</div></section>"""
    voice = """<section class="sec"><div class="sh"><b>Voice</b></div><div class="voice">
<div>Somebody here knows. Go and ask.<span>The shelf and the checkout in six words.</span></div>
<div>You are the author of the book you haven’t written yet.<span>The mission line, on the poster.</span></div>
<div>Check out a person.<span>Short enough for a sticker.</span></div></div></section>"""
    body = header("A", "The Magpie",
                  "Trove as the publisher of books nobody has written yet, with a publisher's colophon: a magpie standing on a closed book.",
                  "Every press has its animal on the spine. A magpie gathers bright things into one place, is curious, and talks, "
                  "which is the trove, the reading and the checkout in one bird. It is drawn like a linocut: solid ink, white "
                  "cut out for the belly and shoulder, one cut line along the wing.") + hero + story_sec + marks + typ + col + site_sec + mkt + voice
    return doc("Brand round 2 · A · The Magpie", FONTS["A"], vars_css, extra, body, 5100)


def board_b():
    ink = "#1B1B26"
    vars_css = (f"--pg:{RPAPER};--ink:{ink};--ink2:#5E5B66;--disp:'Big Shoulders Display',sans-serif;--dw:800;"
                f"--voice:'Libre Franklin',sans-serif;--ui:'Libre Franklin',system-ui,sans-serif;--band:#E6E0CF;--bandfg:{ink};"
                "--navf:600 15px 'Libre Franklin';--btnf:700 16px 'Libre Franklin'")
    extra = """
.b2 .h1{font-weight:900;letter-spacing:0}
.b2 .lede{font-style:normal;font-weight:400;}
.b2 .sh b,.b2 .s-title,.b2 .s-sh b,.b2 .voice div{letter-spacing:.005em}
.b2 .s-voice{font-style:normal;font-weight:400}
.halo{background-image:radial-gradient(var(--c) 1.4px,transparent 1.7px);background-size:7px 7px}
"""
    hero = f"""<section class="sec" style="margin-top:56px"><div style="position:relative;border:2px solid {ink};height:640px;background:{RPAPER};overflow:hidden;isolation:isolate">
<div class="halo" style="--c:{SUN};position:absolute;right:-220px;top:-120px;width:560px;height:560px;border-radius:50%;mix-blend-mode:multiply"></div>
<div style="position:absolute;left:90px;top:0;bottom:0;display:flex;align-items:center;gap:36px">{two_books(330)}{ov_word(290)}</div></div></section>"""
    marks = f"""<section class="sec"><div class="sh"><b>The mark</b><span>Two books lean into each other; where they overlap, the two inks make a third</span></div>
<div class="row">
<figure>{two_books(240)}<span class="cap">240</span></figure>
<figure>{two_books(120)}<span class="cap">120</span></figure>
<figure>{two_books(64, grain=False)}<span class="cap">64</span></figure>
<figure>{two_books(32, grain=False)}<span class="cap">32</span></figure>
<figure>{two_books(16, grain=False)}<span class="cap">16</span></figure>
<figure><div class="ico" style="background:{RPAPER};border:1.5px solid {ink}">{two_books(100)}</div><span class="cap">App icon</span></figure>
<figure><div class="ico" style="background:{BLUE}">{two_books(100, "#FFFFFF", SUN)}</div><span class="cap">App icon · blue</span></figure>
<figure>{ov_word(110)}<span class="cap">Wordmark</span></figure>
</div><div style="margin-top:28px"><span class="btab">{two_books(16, grain=False)}Trove · Shelf</span></div></section>"""
    why = f"""<section class="sec"><div class="sh"><b>Why two inks</b><span>Risograph: two drums, one sheet, never quite in register</span></div>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:36px;font-size:17px">
<p><b style="font-weight:800;font-size:26px;display:block;margin-bottom:6px;font-variation-settings:'wdth' 75">Two people, one sheet.</b>Each ink is a person. Neither is on top; where they cross, the colour that appears belongs to neither of them.</p>
<p><b style="font-weight:800;font-size:26px;display:block;margin-bottom:6px;font-variation-settings:'wdth' 75">Made, not rendered.</b>Riso is the zine and campus-flyer press: grain, slight misregistration, ink that sits on the paper. The opposite of a smooth AI gradient.</p>
<p><b style="font-weight:800;font-size:26px;display:block;margin-bottom:6px;font-variation-settings:'wdth' 75">Loud on a wall.</b>The one direction that wins a crowded campus noticeboard, while the product inside stays calm.</p></div></section>"""
    typ = f"""<section class="sec"><div class="sh"><b>Type</b><span>A display face and a text face</span></div>
{spec([
        ("Display · Big Shoulders 900", "font-family:'Big Shoulders Display';font-weight:900;font-size:100px",
         "trove", "Drawn from Chicago’s civic signage: a Great Lakes city face, tall and plain. Lowercase for the name."),
        ("Headlines · Big Shoulders 800", "font-family:'Big Shoulders Display';font-weight:800;font-size:46px;line-height:1.02",
         "Two people and a book.", "Headlines, shelf names and book titles on covers."),
        ("Text · Libre Franklin", "font-family:'Libre Franklin';font-weight:400;font-size:19px;line-height:1.5",
         "Franklin Gothic is the American newspaper and poster sans. Plain text for anything you read to do a task.",
         "Replaces Plex, Newsreader and Barlow."),
    ])}</section>"""
    col = f"""<section class="sec"><div class="sh"><b>Colour</b><span>Two inks and their overlap, on newsprint</span></div>
{swatches([(BLUE, "Riso teal", "Ink one"), (SUN, "Sunflower", "Ink two"), ("#008400", "Overlap", "Appears wherever the two inks cross, the wordmark included"),
           (RPAPER, "Newsprint", "The ground"), (ink, "Ink", "Body text"), ("#D42A27", "Red", "Still only the one action; the band is newsprint so it sits on a calm ground")])}</section>"""
    books = (cover("city", 236, "'Big Shoulders Display'", 800, size=0.16, lh=".9", shadow=SUN, rot=-2),
             "".join(cover(k, 176, "'Big Shoulders Display'", 800, size=0.16, lh=".9", shadow=s)
                     for k, s in (("desert", BLUE), ("coast", SUN), ("forest", BLUE), ("beach", SUN), ("lake", BLUE), ("mesa", SUN))))
    site_sec = f"""<section class="sec"><div class="sh"><b>The site in it</b><span>Big Shoulders titles; the Librarian’s band on newsprint so the red button has a calm ground; cover shadows in the two inks</span></div>
{site(f'<span style="display:inline-flex;align-items:center;gap:10px">{two_books(40, grain=False)}{ov_word(38)}</span>', books, "Changing course", "After Hours",
      "Nine years running a night kitchen, and how to build a team that works when nobody is watching.", "Marcus Bell")}</section>"""
    mkt = f"""<section class="sec"><div class="sh"><b>Marketing</b><span>Campus launch</span></div>
<div class="mk">
<div style="grid-column:span 4"><div class="pst" style="height:760px;background:{RPAPER};isolation:isolate">
<div class="halo" style="--c:{BLUE};position:absolute;left:-120px;top:250px;width:460px;height:460px;border-radius:50%;mix-blend-mode:multiply"></div>
<div style="position:absolute;left:41px;top:45px;font:800 96px/.86 'Big Shoulders Display';letter-spacing:-.03em;color:{SUN}">check out<br>a person.</div>
<div style="position:absolute;left:36px;top:40px;font:800 96px/.86 'Big Shoulders Display';letter-spacing:-.03em;color:{BLUE}">check out<br>a person.</div>
<div style="position:absolute;right:20px;bottom:130px">{two_books(230)}</div>
<div style="position:absolute;left:0;bottom:0;right:0;padding:18px 36px 26px;background:{RPAPER};border-top:1.5px solid {ink};display:flex;justify-content:space-between;align-items:flex-end">{ov_word(52)}<span style="font:700 14px 'Big Shoulders Display'">trove · case.edu</span></div>
</div><span class="cap">Poster · 18×24, two-colour riso</span></div>
<div style="grid-column:span 4;display:grid;gap:28px">
<div><div class="pst" style="height:420px;background:{SUN};display:flex;align-items:center;justify-content:center;gap:24px">{cover("lake", 150, "'Big Shoulders Display'", 800, size=.16, lh=".9", shadow=BLUE, rot=-4)}{cover("desert", 150, "'Big Shoulders Display'", 800, size=.16, lh=".9", shadow=BLUE, rot=3)}
<div style="position:absolute;left:28px;bottom:22px;font:800 30px 'Big Shoulders Display';color:{BLUE}">new on the shelf</div></div><span class="cap">Instagram post</span></div>
<div><div class="pst" style="width:236px;height:420px;background:{BLUE};color:#fff;padding:26px 22px;display:flex;flex-direction:column;justify-content:space-between">
<div style="font:800 38px/.98 'Big Shoulders Display';font-variation-settings:'wdth' 75">no feed. no followers.<br><span style="color:{SUN}">just books.</span></div>
<div style="align-self:center">{two_books(170, "#FFFFFF", SUN)}</div></div><span class="cap">Instagram story · 9:16</span></div>
</div>
<div style="grid-column:span 4;display:grid;gap:28px">
<div><div class="pst" style="height:430px;background:#E9E4D6;display:grid;place-items:center">
<div style="width:250px;height:330px;background:{RPAPER};border:1.5px solid {ink};position:relative;display:grid;place-items:center">
<div style="position:absolute;top:-56px;left:50%;width:120px;height:76px;margin-left:-60px;border:3px solid {ink};border-bottom:none;border-radius:60px 60px 0 0"></div>{two_books(170)}</div></div><span class="cap">Tote</span></div>
<div style="display:flex;gap:28px;align-items:center"><div style="width:180px;height:180px;border-radius:999px;background:{RPAPER};border:1.5px solid {ink};display:grid;place-items:center">{two_books(120)}</div>
<div style="width:200px;height:120px;background:{BLUE};display:grid;place-items:center">{ov_word(64, "#fff", SUN)}</div></div>
<span class="cap" style="margin-top:-18px">Sticker · zine cover</span></div>
</div></section>"""
    voice = """<section class="sec"><div class="sh"><b>Voice</b></div><div class="voice">
<div>check out a person.<span>Lowercase, loud, short.</span></div>
<div>no feed. no followers. just books.<span>What Trove refuses, on a story.</span></div>
<div>two people and a book.<span>The mark, said out loud.</span></div></div></section>"""
    body = header("B", "Overprint",
                  "A riso-printed identity in two inks. The mark is two books leaning into each other; where they overlap, a third colour appears that neither ink has alone.",
                  "That overlap is what a checkout makes: something new between two people. Grain and misregistration make it "
                  "feel printed on campus; the type is Great Lakes civic signage and the American newspaper sans, not this "
                  "year’s startup faces.") + hero + why + marks + typ + col + site_sec + mkt + voice
    return doc("Brand round 2 · B · Overprint", FONTS["B"], vars_css, extra, body, 5100)


def board_c():
    ink, paper = "#1C2230", "#FBF9F4"
    vars_css = (f"--pg:{paper};--ink:{ink};--ink2:#5A5E68;--disp:'Libre Caslon Display',Georgia,serif;--voice:'Libre Caslon Text',Georgia,serif;"
                f"--ui:'Schibsted Grotesk',system-ui,sans-serif;--band:#F1ECE2;--bandfg:{ink};"
                "--navf:500 15px 'Schibsted Grotesk';--navls:.02em;--btnf:600 16px 'Schibsted Grotesk'")
    extra = """
"""
    hero = f"""<section class="sec" style="margin-top:56px"><div style="border:2px solid {ink};height:660px;background:{paper};display:grid;place-items:center">{wet_lock(140, "lake", ink)}</div></section>"""
    variants = "".join(f'<figure>{painted(k, 200)}<span class="cap">{k}</span></figure>' for k in PAINTED)
    marks = f"""<section class="sec"><div class="sh"><b>The mark</b><span>Painted, not drawn: an open book of two wet washes. Proposal: each member’s mark takes the two colours of their own cover</span></div>
<div class="row" style="gap:28px">{variants}</div>
<div class="row" style="margin-top:44px">
<figure>{painted("lake", 120)}<span class="cap">120</span></figure>
<figure>{painted("lake", 64)}<span class="cap">64</span></figure>
<figure>{wet_flat(32)}<span class="cap">32 · flat</span></figure>
<figure>{wet_flat(16)}<span class="cap">16 · flat</span></figure>
<figure><div class="ico" style="background:{paper};border:1.5px solid {ink}">{painted("dusk", 96)}</div><span class="cap">App icon</span></figure>
<figure>{wet_lock(56, "coast", ink, stacked=False)}<span class="cap">Horizontal</span></figure>
</div><div style="margin-top:28px"><span class="btab">{wet_flat(16)}Trove · Shelf</span></div></section>"""
    why = f"""<section class="sec"><div class="sh"><b>Why paint</b><span>The covers are already watercolour; the brand comes from the same brush</span></div>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:36px;font-size:17px">
<p><b style="font-family:'Libre Caslon Display';font-weight:400;font-size:30px;display:block;margin-bottom:6px">No two alike (a proposal).</b>The site carries one house mark. As a proposal, each member’s could be painted in their own cover’s colours: a family, not a stamp.</p>
<p><b style="font-family:'Libre Caslon Display';font-weight:400;font-size:30px;display:block;margin-bottom:6px">Where they meet, it deepens.</b>The two pages overlap at the spine, and the glazes stack into a third, darker colour: the conversation.</p>
<p><b style="font-family:'Libre Caslon Display';font-weight:400;font-size:30px;display:block;margin-bottom:6px">Visibly by hand.</b>Pooled edges, uneven pigment, paper tooth. Nothing about it can be mistaken for a template.</p></div></section>"""
    typ = f"""<section class="sec"><div class="sh"><b>Type</b><span>A literary serif with a working sans</span></div>
{spec([
        ("Display · Libre Caslon Display", "font-family:'Libre Caslon Display';font-size:96px", "Trove",
         "Caslon is the face of English-language books for three centuries; the display cut is sharp and elegant at size. The wordmark, titles, shelf names."),
        ("Reading · Libre Caslon Text", "font-family:'Libre Caslon Text';font-style:italic;font-size:30px;line-height:1.3",
         "A book you read by talking to its author.", "The text cut for blurbs and chapters; the italic is the Librarian’s voice."),
        ("Interface · Schibsted Grotesk", "font-family:'Schibsted Grotesk';font-weight:600;font-size:40px",
         "Ask to check out", "A newspaper-born grotesk, sturdy and slightly condensed, in place of Plex for anything you do."),
    ])}</section>"""
    col = f"""<section class="sec"><div class="sh"><b>Colour</b><span>Blue-black ink on paper; everything else comes from the members' paints</span></div>
{swatches([(ink, "Iron-gall ink", "Type and the wordmark"), (paper, "Cold-press", "The ground"), ("#F1ECE2", "Wash", "Panels, the Librarian’s band"),
           ("#5B74B8", "Ultramarine", "From the covers"), ("#C98A5A", "Sienna", "From the covers"), ("#78A9A6", "Teal", "From the covers"),
           ("#D42A27", "Red", "Still only the one action")])}</section>"""
    books = (cover("beach", 236, "'Libre Caslon Display'", 400, size=0.16, lh="1", rot=2),
             "".join(cover(k, 176, "'Libre Caslon Display'", 400, size=0.16, lh="1") for k in ("lake", "forest", "city", "mesa", "desert", "coast")))
    site_sec = f"""<section class="sec"><div class="sh"><b>The site in it</b><span>Caslon titles everywhere, the Librarian’s band a pale wash instead of black</span></div>
{site(wet_lock(34, "lake", ink, stacked=False), books, "Changing course", "Off the Clock",
      "From back-to-back meetings to running a surf school, and what a week looks like when you design it yourself.", "Leilani Cruz")}</section>"""
    mkt = f"""<section class="sec"><div class="sh"><b>Marketing</b><span>Campus launch</span></div>
<div class="mk">
<div style="grid-column:span 4"><div class="pst" style="height:760px;background:{paper};padding:48px 40px;display:flex;flex-direction:column">
{painted("forest", 470)}
<div style="font-family:'Libre Caslon Display';font-size:58px;line-height:1.02;margin-top:30px">Somebody here knows what you’re trying to figure out.</div>
<div style="margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end">{wet_lock(40, "forest", ink, stacked=False)}<span style="font:600 13px 'Schibsted Grotesk';letter-spacing:.12em;text-transform:uppercase">trove · case.edu</span></div>
</div><span class="cap">Poster · 18×24</span></div>
<div style="grid-column:span 4;display:grid;gap:28px">
<div><div class="pst" style="height:420px;background:#F1ECE2;display:grid;grid-template-columns:repeat(3,1fr);gap:8px;padding:28px">
{"".join(f'<div style="display:grid;place-items:center">{painted(k, 120)}</div>' for k in ("lake","coast","forest","dusk","mesa","lake"))}
<div style="position:absolute;left:28px;bottom:20px;font-family:'Libre Caslon Text';font-style:italic;font-size:20px">Six covers, six pairs of colours.</div></div><span class="cap">Instagram post · if members get their own marks</span></div>
<div><div class="pst" style="height:280px;background:{paper};display:flex;align-items:center;gap:30px;padding:0 34px">{painted("coast", 170)}
<div><div style="font-family:'Libre Caslon Display';font-size:36px;line-height:1.05">Your book is on the shelf.</div></div></div><span class="cap">Email header · in the proposal, the mark is painted from the member’s cover</span></div>
</div>
<div style="grid-column:span 4;display:grid;gap:28px">
<div><div class="pst" style="height:430px;background:#E8E2D4;display:grid;place-items:center">
<div style="width:250px;height:330px;background:{paper};border:1.5px solid {ink};position:relative;display:grid;place-items:center">
<div style="position:absolute;top:-56px;left:50%;width:120px;height:76px;margin-left:-60px;border:3px solid {ink};border-bottom:none;border-radius:60px 60px 0 0"></div>{wet_lock(62, "dusk", ink)}</div></div><span class="cap">Tote</span></div>
<div style="display:flex;gap:24px;align-items:center">
<div style="width:240px;height:170px;background:#fff;border:1.5px solid {ink};padding:16px 18px;display:flex;flex-direction:column;justify-content:space-between">
<div style="display:flex;justify-content:space-between;align-items:flex-start">{painted("mesa", 64)}<span style="font:600 11px 'Schibsted Grotesk';letter-spacing:.12em;text-transform:uppercase">Author</span></div>
<div style="font-family:'Libre Caslon Display';font-size:24px">Lucia Navarro</div></div>
<div style="width:150px;height:150px;border-radius:999px;background:{paper};border:1.5px solid {ink};display:grid;place-items:center">{painted("lake", 110)}</div></div>
<span class="cap" style="margin-top:-18px">Name card in the member’s own mark · sticker</span></div>
</div></section>"""
    voice = """<section class="sec"><div class="sh"><b>Voice</b></div><div class="voice">
<div>A book you read by talking to its author.<span>The checkout, without the jargon.</span></div>
<div>Nobody here is performing.<span>What Trove refuses, said once.</span></div>
<div>Every book on the shelf is the same size.<span>The level shelf, said plainly.</span></div></div></section>"""
    body = header("C", "Wet Ink",
                  "A painted mark: an open book of two watercolour washes that overlap and deepen at the spine. The site has one house mark; as a proposal, each member’s could be painted from their own cover.",
                  "The covers are already painted with Trove’s own watercolour engine, so the brand comes from the same brush. "
                  "The wordmark is set in Caslon, the classic face of printed books, in blue-black ink. The mark is a living "
                  "system: the site shows a house version, and each member gets their own.") + hero + why + marks + typ + col + site_sec + mkt + voice
    return doc("Brand round 2 · C · Wet Ink", FONTS["C"], vars_css, extra, body, 5100)


def board_think():
    vars_css = ("--pg:#FAFAF7;--ink:#141414;--ink2:#55554F;--disp:'Gloock',Georgia,serif;--voice:'Literata',Georgia,serif;"
                "--ui:'Hanken Grotesk',system-ui,sans-serif")
    extra = """
.cols{display:grid;grid-template-columns:repeat(2,1fr);gap:48px}
.lst{list-style:none;display:grid;gap:16px;font-size:18px}
.lst li{border-top:1.5px solid var(--ink);padding-top:12px}
.lst b{display:block;font-family:Gloock;font-weight:400;font-size:26px;line-height:1.1;margin-bottom:4px}
.avoid{display:grid;grid-template-columns:repeat(6,1fr);gap:0;border:1.5px solid var(--ink)}
.avoid div{padding:18px;border-right:1.5px solid var(--ink);background:#fff}
.avoid div:last-child{border-right:none}
.avoid em{display:block;font-style:normal;font-size:30px;line-height:1.1;text-decoration:line-through;text-decoration-thickness:2px;color:#55554F}
.avoid span{display:block;margin-top:8px;font-size:13px;color:#55554F}
.three{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:28px}
.three>div{border:2px solid var(--ink);background:#fff;padding:28px;min-height:420px;display:flex;flex-direction:column;gap:16px}
.three .tp{font-size:15px;color:#55554F}
"""
    avoid = [
        ("font-family:Inter,system-ui;font-weight:600", "Inter", "The default of every generated app"),
        ("font-family:'Space Grotesk',system-ui;font-weight:600", "Space Grotesk", "The 'techy' default"),
        ("font-family:Fraunces,Georgia,serif;font-style:italic", "Fraunces", "The 'warm' AI serif"),
        ("font-family:'Instrument Serif',Georgia,serif", "Instrument Serif", "The 2025 landing page"),
        ("font-family:'IBM Plex Sans',system-ui", "IBM Plex", "Ours today: clean, anonymous"),
        ("font-family:'Barlow Condensed',sans-serif;font-weight:800;text-transform:uppercase", "Barlow", "Ours today: sporty caps"),
    ]
    avoid_html = "".join(f'<div><em style="{st}">{n}</em><span>{why}</span></div>' for st, n, why in avoid)
    three = f"""
<div><span class="ey">A · publisher</span>{colophon(180)}<b style="font-family:Gloock;font-weight:400;font-size:40px;line-height:1">The Magpie</b>
<p class="tp">A colophon: a magpie on a closed book, cut like a linocut. Gloock, Literata, Hanken Grotesk. Black and white with a blue-green sheen.</p></div>
<div><span class="ey">B · print shop</span><div style="display:flex;align-items:center;gap:18px">{two_books(150)}{ov_word(80)}</div><b style="font-family:'Big Shoulders Display';font-weight:800;font-size:44px;line-height:1">Overprint</b>
<p class="tp">Two riso inks, teal and yellow; two books leaning together make green where they overlap. Big Shoulders and Libre Franklin.</p></div>
<div><span class="ey">C · the brush</span><div style="display:flex;align-items:center;gap:6px">{painted("lake", 150)}{painted("coast", 110)}{painted("forest", 80)}</div><b style="font-family:'Libre Caslon Display';font-weight:400;font-size:44px;line-height:1">Wet Ink</b>
<p class="tp">A painted open book, a different pair of colours for every member. Libre Caslon and Schibsted Grotesk, blue-black ink.</p></div>"""
    body = f"""<span class="ey">Brand · round 2 · what changed</span><h1 class="h1">Less logo, more craft</h1>
<p class="lede">Josef: all three were too basic, and the fonts can change to move the site away from the AI-generated look.</p>
<section class="sec"><div class="cols">
<div><div class="sh"><b>Why round 1 was basic</b></div><ul class="lst">
<li><b>One idea, one flat shape.</b>A T, a silhouette, a rectangle: an icon, not an identity.</li>
<li><b>Borrowed type.</b>The wordmarks were the site's own fonts, so nothing in them was ownable.</li>
<li><b>No colour, no hand.</b>Ink on paper only; nothing that could only have been made by someone.</li></ul></div>
<div><div class="sh"><b>What round 2 does</b></div><ul class="lst">
<li><b>A made thing at the centre.</b>A drawn bird, a two-ink print, a painted wash: each shows a hand.</li>
<li><b>Its own typefaces.</b>Each direction brings a family with character, and shows the site retyped in it.</li>
<li><b>Colour with a reason.</b>A sheen, two inks, or the members' own paints. Red stays only for the one action.</li></ul></div>
</div></section>
<section class="sec"><div class="sh"><b>Faces we're leaving</b><span>What reads as generated, and what we use today</span></div><div class="avoid">{avoid_html}</div></section>
<section class="sec"><div class="sh"><b>The three</b><span>Full boards to the right</span></div><div class="three">{three}</div></section>"""
    fonts = FONTS["think"] + "&amp;family=Inter:wght@600&amp;family=Space+Grotesk:wght@600&amp;family=Fraunces:ital@1&amp;family=Instrument+Serif&amp;family=IBM+Plex+Sans&amp;family=Barlow+Condensed:wght@800"
    return doc("Brand round 2 · what changed", fonts, vars_css, extra, body, 1720)


BOARDS = {
    "Brand2Think.dc.html": board_think,
    "Brand2A.dc.html": board_a,
    "Brand2B.dc.html": board_b,
    "Brand2C.dc.html": board_c,
}


def main():
    prev = Path(sys.argv[sys.argv.index("--preview") + 1]) if "--preview" in sys.argv else None
    art = Path(sys.argv[sys.argv.index("--art") + 1]) if "--art" in sys.argv else None
    here_art = Path(__file__).parent.parent / "art" / "watercolor" / "out"
    for name, fn in BOARDS.items():
        html = fn()
        (PROJECT / name).write_text(html)
        if prev:
            prev.mkdir(parents=True, exist_ok=True)
            p = html
            for key, (blob, *_r) in ART.items():
                if art:
                    p = p.replace(f"/_blob/{blob}", str(art / LOCAL_ART[key]))
            for key, blob in PAINTED.items():
                p = p.replace(f"/_blob/{blob}", str(here_art / f"brand-{key}.webp"))
            (prev / name.replace(".dc.html", ".html")).write_text(p)
        print("wrote", name)


if __name__ == "__main__":
    main()
