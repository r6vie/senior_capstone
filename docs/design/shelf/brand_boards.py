"""Brand identity boards for the canvas page "Brand".

python3 docs/design/shelf/brand_boards.py            writes the four boards into project/
python3 docs/design/shelf/brand_boards.py --preview DIR   also writes browser previews with local art

BrandThink is the thinking (mission, feeling, twelve ideas and their critique); BrandA..C are the
three identities we kept, each with its mark, wordmark, rules, the product top bar and marketing.
"""

import sys
from pathlib import Path

HERE = Path(__file__).parent
PROJECT = HERE / "project"

FONTS = (
    "https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700;800"
    "&amp;family=Newsreader:ital,opsz,wght@0,6..72,400..700;1,6..72,400..600"
    "&amp;family=IBM+Plex+Sans:wght@400;500;600&amp;display=swap"
)

# Cover art already on the canvas (asset ids), with the cover's title ink.
ART = {
    "lake": ("1e9415fdd6e49a24e90cb5befd197f98", "#23415a", "Above the Tree Line", "Ingrid Solberg"),
    "beach": ("6e8e94c8767e382846a8d452de106a3b", "#5a2f2a", "Off the Clock", "Leilani Cruz"),
    "city": ("dc709e43fb65e3f96dfe30808af36cd5", "#f6efe0", "After Hours", "Marcus Bell"),
    "desert": ("49a3b7b996be6b7bb76cfea36a94ef45", "#6a3525", "What the Desert Teaches", "Lucía Hernández-Brooks"),
    "coast": ("09eabf0d3c4a573f24c3190ca05b4b95", "#26304f", "Notes From the Edge", "Callum O’Donnell"),
    "forest": ("f555c336b0c5f0fc55b7aae44dad590e", "#283d2e", "Room to Grow", "Noah Bergstrom"),
    "mesa": ("f43fbf5c4f4949ffce7e9a58bd5951f1", "#f6efe0", "The High Desert", "Lucia Navarro"),
    "lighthouse": ("21768e812b25b73340d604b551450974", "#2c3e5c", "Keeping the Light", "Maren Holt"),
}
LOCAL_ART = {
    "lake": "watercolor/out/lake-full-xl.webp",
    "beach": "watercolor/out/beach-full-xl.webp",
    "city": "watercolor/out/city-full-xl.webp",
    "desert": "strata/out/more-desert-xl.webp",
    "coast": "strata/out/more-coast-xl.webp",
    "forest": "strata/out/us-forest-xl.webp",
    "mesa": "watercolor/out/mesa-full-xl.webp",
    "lighthouse": "watercolor/out/lighthouse-full-xl.webp",
}

INK, PAPER, SUNK, INK2, RULE = "#111111", "#FAFAF7", "#F0F0EB", "#55554F", "#C9C9C6"

_uid = [0]


def uid(p):
    _uid[0] += 1
    return f"{p}{_uid[0]}"


# ---------------------------------------------------------------- marks

def mark_ribbon(size, fg=INK, bg="none"):
    """A: the bookmark. A book's edge with a ribbon hanging from it, which is also a T."""
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 100 100" aria-hidden="true">'
        + (f'<rect width="100" height="100" fill="{bg}"/>' if bg != "none" else "")
        + f'<rect x="12" y="16" width="76" height="13" fill="{fg}"/>'
        f'<path d="M41 29H59V88L50 74L41 88Z" fill="{fg}"/></svg>'
    )


# One profile, facing right, drawn down the inner edge of the left page. The right page is its mirror,
# so the gutter between them is the spine and the two pages are two people face to face.
_PROFILE = (
    "M45 15 C47.5 21 49.2 27 50 32 C50.4 34.5 50 36 50.6 37.6 C52.4 40.4 54.6 42.6 55.8 44.6"
    " C56.6 46 55.8 47.6 54 47.8 L52.8 48.2 C53.2 49.4 54.2 50 54.4 51.2 C54.5 52.2 53.4 52.8 53.2 53.4"
    " C53.6 54 54.2 54.8 53.9 55.8 C53.6 56.8 52.2 57.2 51.8 58 C51.6 59.2 53.4 60.4 53.6 62.4"
    " C53.8 64.6 52 66.2 49.4 66.8 C48.4 68.6 48.2 75 49 86"
)


def _page_left():
    return (
        "M6 21 C18 15 32 13 45 15 " + _PROFILE[len("M45 15 "):] +
        " C34 82 18 82 6 88 Z"
    )


def mark_faces(size, fg=INK, bg="none", w=None):
    w = w or size * 1.2
    left = _page_left()
    return (
        f'<svg width="{w:.0f}" height="{size}" viewBox="0 0 120 100" aria-hidden="true">'
        + (f'<rect width="120" height="100" fill="{bg}"/>' if bg != "none" else "")
        + f'<path d="{left}" fill="{fg}"/>'
        f'<path d="{left}" fill="{fg}" transform="translate(120 0) scale(-1 1)"/></svg>'
    )


def mark_blank(size, fg=INK, card="#FFFFFF", bg="none", dots=True):
    small = size < 48
    """C: the blank cover. Trove's own book object, with the title not written yet."""
    pid = uid("dt")
    shadow = "" if small else (
        f'<defs><pattern id="{pid}" width="4.2" height="4.2" patternUnits="userSpaceOnUse">'
        f'<circle cx="2.1" cy="2.1" r="1.25" fill="{fg}"/></pattern></defs>'
        f'<rect x="30" y="17" width="58" height="78" fill="url(#{pid})"/>'
        if dots
        else f'<rect x="30" y="17" width="58" height="78" fill="{fg}"/>'
    )
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 100 100" aria-hidden="true">'
        + (f'<rect width="100" height="100" fill="{bg}"/>' if bg != "none" else "")
        + shadow
        + f'<rect x="17.5" y="7.5" width="59" height="79" fill="{card}" stroke="{fg}" stroke-width="5"/>'
        + (f'<rect x="25" y="10" width="6" height="74" fill="{fg}"/>' if small else f'<rect x="26" y="10" width="3.2" height="74" fill="{fg}"/>')
        + (f'<rect x="38" y="23" width="28" height="9" fill="{fg}"/></svg>' if small else f'<rect x="36" y="24" width="28" height="6.5" fill="{fg}"/></svg>')
    )


# ---------------------------------------------------------------- wordmarks

def word_a(px, fg=INK, ribbon=True):
    """Trove in Newsreader on the book's bottom edge, with the ribbon slipping out under the v."""
    r = (
        f'<svg class="rb" style="left:58.5%;width:{px*0.17:.1f}px;height:{px*0.42:.1f}px" viewBox="0 0 18 42">'
        f'<path d="M0 0H18V42L9 31L0 42Z" fill="{fg}"/></svg>'
        if ribbon
        else ""
    )
    return (
        f'<span class="wa" style="font-size:{px}px;color:{fg};--rl:{max(2, px*0.045):.1f}px">'
        f'<span class="wt">Trove</span>{r}</span>'
    )


def word_b(px, fg=INK):
    return f'<span class="wb" style="font-size:{px}px;color:{fg}">trove</span>'


def word_c(px, fg=INK):
    return f'<span class="wc" style="font-size:{px}px;color:{fg}">TROVE</span>'


def lock_a(px, fg=INK):
    return f'<span class="lk">{mark_ribbon(int(px*1.05), fg)}<span class="wt-a" style="font-size:{px}px;color:{fg}">Trove</span></span>'


def lock_b(px, fg=INK):
    return f'<span class="lk lkb">{mark_faces(int(px*0.92), fg)}{word_b(px, fg)}</span>'


def lock_c(px, fg=INK, card="#FFFFFF"):
    return f'<span class="lk lkc">{mark_blank(int(px*1.12), fg, card)}{word_c(px, fg)}</span>'


# ---------------------------------------------------------------- shared pieces

def cover(key, w, rot=0, shadow=True):
    blob, ink, title, name = ART[key]
    fs = w * 0.165
    return (
        f'<div class="cv{" sh" if shadow else ""}" style="width:{w}px;height:{w*1.457:.0f}px;--ci:{ink};'
        f'transform:rotate({rot}deg)" aria-label="{title}, by {name}">'
        f'<img src="/_blob/{blob}" alt="">'
        f'<span class="ct" style="font-size:{fs:.1f}px">{title}</span>'
        f'<span class="cn" style="font-size:{max(6, w*0.06):.1f}px;background:{"transparent" if ink.lower() == "#f6efe0" else "#fff"}">{name}</span></div>'
    )


def topbar(logo_html, dark=False):
    return (
        f'<div class="tb{" tbd" if dark else ""}">{logo_html}'
        '<nav><b aria-current="page">Shelf</b><b>My book</b><b>Checkouts</b><b>Past meets</b></nav>'
        '<span class="sr">Search by topic</span><span class="av">H</span></div>'
    )


def browser_tab(icon_svg, dark=False):
    return (
        f'<div class="btab{" btd" if dark else ""}"><span class="bi">{icon_svg}</span>'
        '<span class="bl">Trove · Shelf</span><span class="bx">×</span></div>'
    )


def swatch(hexv, name, role, dark_text=False):
    col = INK if dark_text else "#FFFFFF"
    return (
        f'<div class="sw"><div class="swc" style="background:{hexv};color:{col}">{hexv.upper()}</div>'
        f'<b>{name}</b><span>{role}</span></div>'
    )


CSS = """
body{margin:0}
.bb{--ink:#111;--paper:#FAFAF7;--sunk:#F0F0EB;--ink2:#55554F;--rule:#C9C9C6;
 --cond:'Barlow Condensed','Arial Narrow',sans-serif;--ser:'Newsreader',Georgia,serif;--sans:'IBM Plex Sans',system-ui,sans-serif;
 width:1760px;padding:72px 80px 96px;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.5}
.bb,.bb *{box-sizing:border-box}
:where(.bb) :is(h1,h2,h3,p,ul,ol,figure){margin:0;padding:0}
.eyebrow{font:700 15px var(--cond);letter-spacing:.16em;text-transform:uppercase;color:var(--ink2)}
.h1{font:600 64px/1.02 var(--ser);letter-spacing:-.015em;margin-top:14px}
.lede{font:400 22px/1.4 var(--ser);max-width:900px;margin-top:18px}
.sec{margin-top:72px}
.sh2{display:flex;align-items:baseline;gap:18px;border-top:3px solid var(--ink);padding-top:14px;margin-bottom:28px}
.sh2 b{font:800 30px/1 var(--cond);letter-spacing:.04em;text-transform:uppercase}
.sh2 span{font-size:15px;color:var(--ink2)}
.note{font-size:14px;color:var(--ink2);max-width:520px}
.cap{font:600 13px var(--cond);letter-spacing:.14em;text-transform:uppercase;color:var(--ink2);margin-top:10px}
.tone{background-image:radial-gradient(var(--ink) 1.1px,transparent 1.3px);background-size:6px 6px}
.tone-f{background-image:radial-gradient(var(--ink) .9px,transparent 1.1px);background-size:5px 5px}

/* wordmarks */
.wa{position:relative;display:inline-block;line-height:1}
.wa .wt{display:block;font-family:var(--ser);font-weight:600;letter-spacing:-.02em;line-height:.9;padding:0 .04em;border-bottom:var(--rl) solid currentColor}
.wa .rb{position:absolute;top:100%;display:block;margin-top:calc(var(--rl) * -1)}
.wt-a{font-family:var(--ser);font-weight:600;letter-spacing:-.02em;line-height:1}
.wb{font-family:var(--ser);font-style:italic;font-weight:500;letter-spacing:-.01em;line-height:1}
.wc{font-family:var(--cond);font-weight:800;letter-spacing:.05em;line-height:.9}
.lk{display:inline-flex;align-items:center;gap:.28em}
.lkb{gap:.42em}.lkc{gap:.22em}

/* book cover */
.cv{position:relative;flex:none;background:#fff;border:2px solid var(--ink);display:flex;flex-direction:column;justify-content:flex-start;padding:9% 7% 6% 11%;overflow:visible}
.cv img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0}
.cv::before{content:"";position:absolute;left:4.5%;top:0;bottom:0;width:1.5px;background:var(--ink);z-index:1}
.cv.sh::after{content:"";position:absolute;inset:0;transform:translate(8px,8px);z-index:-1;background-image:radial-gradient(var(--ink) 1px,transparent 1.2px);background-size:5px 5px}
.cv .ct{position:relative;z-index:2;color:var(--ci);font-family:var(--cond);font-weight:800;line-height:.92;letter-spacing:.01em;text-transform:uppercase;text-wrap:balance;max-width:86%}
.cv .cn{position:relative;z-index:2;align-self:flex-start;margin-top:.7em;padding:0 .3em 0 0;line-height:1.3;color:var(--ci);font-family:var(--cond);font-weight:700;letter-spacing:.16em;text-transform:uppercase}

/* product */
.tb{display:flex;align-items:center;gap:36px;height:72px;padding:0 36px;background:var(--paper);border:2px solid var(--ink)}
.tb nav{display:flex;gap:26px}
.tb nav b{font:600 17px var(--cond);letter-spacing:.12em;text-transform:uppercase;padding:6px 0}
.tb nav b[aria-current]{border-bottom:3px solid var(--ink)}
.tb .sr{margin-left:auto;width:230px;height:40px;border:2px solid var(--ink);border-radius:999px;display:flex;align-items:center;padding:0 16px;font-size:14px;color:var(--ink2);background:#fff}
.tb .av{width:40px;height:40px;border-radius:999px;border:2px solid var(--ink);display:grid;place-items:center;font:700 16px var(--cond);background:#fff}
.tbd{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.tbd nav b[aria-current]{border-color:var(--paper)}
.tbd .sr,.tbd .av{background:var(--ink);border-color:var(--paper);color:var(--rule)}
.btab{display:inline-flex;align-items:center;gap:10px;height:40px;padding:0 14px;background:#fff;border:1.5px solid var(--rule);border-bottom:none;border-radius:8px 8px 0 0;font-size:13px}
.btab .bi{display:grid;place-items:center;width:16px;height:16px}
.btab .bi svg{width:16px;height:16px}
.btab .bx{color:var(--ink2);margin-left:18px}
.btd{background:#2a2a2a;border-color:#2a2a2a;color:#eee}
.btd .bx{color:#aaa}

/* swatches */
.sws{display:flex;gap:16px}
.sw{width:150px}
.swc{height:96px;display:flex;align-items:flex-end;padding:8px 10px;font:600 13px var(--cond);letter-spacing:.1em;border:1.5px solid var(--ink)}
.sw b{display:block;margin-top:8px;font:700 14px var(--cond);letter-spacing:.12em;text-transform:uppercase}
.sw span{font-size:13px;color:var(--ink2);line-height:1.35;display:block}

.row{display:flex;gap:40px;align-items:flex-start}
.panel{border:2px solid var(--ink);background:#fff}
.dk{background:var(--ink);color:var(--paper)}
.pt{font:600 13px var(--cond);letter-spacing:.14em;text-transform:uppercase}
"""


def board(title, body_html, height):
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
<link rel="stylesheet" href="{FONTS}">
<style>
{CSS}
</style>
</helmet>
<div class="bb" style="height:{height}px;overflow:hidden">
{body_html}
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


# ---------------------------------------------------------------- the thinking board

def sk(svg_inner, vb="0 0 100 100"):
    return f'<svg width="120" height="120" viewBox="{vb}" aria-hidden="true">{svg_inner}</svg>'


IDEAS = [
    # (name, sketch svg, idea, critique, verdict)
    ("Open book", sk('<path d="M8 30Q30 22 50 32Q70 22 92 30V78Q70 70 50 80Q30 70 8 78Z" fill="none" stroke="#111" stroke-width="5"/><path d="M50 32V80" stroke="#111" stroke-width="4"/>'),
     "The plain sign for a book.", "Every library, e-reader and course site already owns it. It says books, not people.", "Cut"),
    ("Treasure chest", sk('<rect x="14" y="44" width="72" height="40" fill="none" stroke="#111" stroke-width="5"/><path d="M14 44Q14 20 50 20Q86 20 86 44" fill="none" stroke="#111" stroke-width="5"/><rect x="44" y="50" width="12" height="14" fill="#111"/>'),
     "Read “trove” literally: a hoard of treasure.", "Pirates and loot boxes. Treasure you own is status, the opposite of lending what you know.", "Cut"),
    ("Key and keyhole", sk('<circle cx="50" cy="38" r="16" fill="#111"/><path d="M42 48L36 84H64L58 48Z" fill="#111"/>'),
     "Unlock what is in you.", "A cliché, and it reads as security or a password manager.", "Cut"),
    ("Quill", sk('<path d="M78 10Q30 22 26 80L32 82Q44 40 78 10Z" fill="#111"/><path d="M26 80L20 92" stroke="#111" stroke-width="4"/>'),
     "The author's pen.", "Antique, and it suggests the member writes. The interview writes; the member talks.", "Cut"),
    ("Spines on a shelf", sk('<rect x="12" y="40" width="12" height="46" fill="#111"/><rect x="28" y="22" width="12" height="64" fill="#111"/><rect x="44" y="52" width="12" height="34" fill="#111"/><rect x="60" y="30" width="12" height="56" fill="#111"/><rect x="76" y="46" width="12" height="40" fill="#111"/>'),
     "Members as books standing side by side.", "Uneven spines read as a bar chart: a ranking. Trove has no counts, so its mark can't look like one.", "Cut"),
    ("Speech bubble book", sk('<path d="M12 20H88V68H40L24 84V68H12Z" fill="none" stroke="#111" stroke-width="5"/><path d="M50 22V66" stroke="#111" stroke-width="4"/>'),
     "A book you talk with.", "Two ideas glued together; it lands as a chat app, and Trove has no cold messages.", "Cut"),
    ("Hidden gem", sk('<path d="M20 38L34 18H66L80 38L50 86Z" fill="none" stroke="#111" stroke-width="5"/><path d="M20 38H80M34 18L42 38L50 86L58 38L66 18" fill="none" stroke="#111" stroke-width="3"/>'),
     "Everyone is a hidden gem; dot tone as the facets.", "Jewellery and crypto. Also a compliment, and compliments are a kind of rating.", "Cut"),
    ("Due-date stamp", sk('<circle cx="50" cy="50" r="38" fill="none" stroke="#111" stroke-width="5"/><circle cx="50" cy="50" r="28" fill="none" stroke="#111" stroke-width="2"/><rect x="30" y="44" width="40" height="12" fill="#111"/>'),
     "The library stamp you get when you check out.", "Warm and true to checkouts, but it is about borrowing, not authorship, and it slides into retro pastiche.", "Cut"),
    ("Collegiate monogram", sk('<path d="M18 14H82V54Q82 78 50 90Q18 78 18 54Z" fill="none" stroke="#111" stroke-width="5"/><path d="M34 32H66M50 32V72" stroke="#111" stroke-width="7"/>'),
     "A crest, because it starts at CWRU.", "Crests are about rank and belonging to the right club. Trove is a level shelf; a VP and a first-year sit side by side.", "Cut"),
    ("Bookmark T", mark_ribbon(120),
     "A ribbon hanging from the edge of a book. It holds a place, and it is the T.", "Simple enough for a 16px tab, and it names a quiet act: holding a place in someone's book.", "Keep · A"),
    ("Facing pages", mark_faces(100, w=120),
     "An open book whose two pages are two profiles, face to face. The spine is the space between them.", "The whole product in one shape: a book that is a conversation. Needs careful drawing so the faces read small.", "Keep · B"),
    ("The blank cover", mark_blank(120),
     "Trove's own book object, outline and dot shadow, with the title not written yet.", "Comes straight out of the screentone system, and it says the tagline: the book you haven't written yet.", "Keep · C"),
]


def think_board():
    feel = [
        ("Curious", "Not clever"), ("Generous", "Not transactional"), ("Level", "Not ranked"),
        ("Unhurried", "Not urgent"), ("Human", "Not AI sparkle"), ("Bookish", "Not dusty"),
    ]
    feel_html = "".join(
        f'<div class="fl"><b>{a}</b><span>{b}</span></div>' for a, b in feel
    )
    ideas_html = "".join(
        f'<div class="id{" keep" if v.startswith("Keep") else ""}"><div class="ik">{s}</div>'
        f'<div class="it"><div class="ih"><b>{n}</b><em>{v}</em></div><p class="ii">{i}</p><p class="ic">{c}</p></div></div>'
        for n, s, i, c, v in IDEAS
    )
    kept = [
        ("A", "Bookmark", mark_ribbon(150), "The act", "Marking someone's book to come back to. Quiet, literary, works at every size."),
        ("B", "Facing pages", mark_faces(130, w=156), "The meeting", "A book that is two people talking. The warmest and most ownable of the three."),
        ("C", "The blank cover", mark_blank(150), "The promise", "The book you haven't written yet. The most native to the screentone system we already have."),
    ]
    kept_html = "".join(
        f'<div class="kp"><div class="kpm">{m}</div><div class="kpt"><span class="eyebrow">{l} · {t}</span>'
        f'<b>{n}</b><p>{d}</p></div></div>'
        for l, n, m, t, d in kept
    )
    extra = """
<style>
.ms{display:grid;grid-template-columns:1fr 1fr;gap:56px}
.ms blockquote{margin:0;font:600 44px/1.12 var(--ser);letter-spacing:-.015em}
.ms p{font-size:17px;line-height:1.55;max-width:720px}
.ms p+p{margin-top:14px}
.fls{display:grid;grid-template-columns:repeat(6,1fr);gap:0;border:2px solid var(--ink)}
.fl{padding:26px 22px;border-right:2px solid var(--ink);background:#fff}
.fl:last-child{border-right:none}
.fl b{display:block;font:600 34px/1 var(--ser);letter-spacing:-.01em}
.fl span{display:block;margin-top:12px;font:600 14px var(--cond);letter-spacing:.14em;text-transform:uppercase;color:var(--ink2);text-decoration:line-through;text-decoration-thickness:2px}
.ids{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}
.id{display:flex;gap:20px;padding:20px;border:2px solid var(--ink);background:#fff;min-height:200px}
.id .ik{flex:none;width:120px;height:120px;display:grid;place-items:center;opacity:.32}
.id.keep{border-width:3px;box-shadow:8px 8px 0 -0px transparent;position:relative}
.id.keep::after{content:"";position:absolute;inset:0;transform:translate(8px,8px);z-index:-1;background-image:radial-gradient(var(--ink) 1px,transparent 1.2px);background-size:5px 5px}
.id.keep .ik{opacity:1}
.ih{display:flex;align-items:baseline;justify-content:space-between;gap:12px}
.ih b{font:800 22px/1.05 var(--cond);letter-spacing:.04em;text-transform:uppercase}
.ih em{font:700 13px var(--cond);letter-spacing:.14em;text-transform:uppercase;font-style:normal;color:var(--ink2);white-space:nowrap}
.keep .ih em{color:var(--ink);border-bottom:3px solid var(--ink)}
.ii{margin-top:8px;font:400 17px/1.35 var(--ser)}
.ic{margin-top:8px;font-size:14px;color:var(--ink2);line-height:1.45}
.kps{display:grid;grid-template-columns:repeat(3,1fr);gap:28px}
.kp{display:flex;gap:28px;align-items:center;padding:28px;border:3px solid var(--ink);background:#fff}
.kpm{flex:none;width:160px;display:grid;place-items:center}
.kpt b{display:block;font:600 36px/1.05 var(--ser);margin-top:6px}
.kpt p{margin-top:10px;font-size:15px;color:var(--ink2)}
.rules{display:grid;grid-template-columns:repeat(4,1fr);gap:20px}
.rules div{border-top:2px solid var(--ink);padding-top:12px;font-size:15px}
.rules b{display:block;font:700 15px var(--cond);letter-spacing:.14em;text-transform:uppercase;margin-bottom:6px}
</style>"""
    body = f"""{extra}
<span class="eyebrow">Brand · round 1 · the thinking</span>
<h1 class="h1">Who Trove is, before what it looks like</h1>
<p class="lede">Mission first, then the feeling, then twelve ideas for a mark and an honest note on each. Three survive; each has its own board to the right.</p>

<section class="sec"><div class="sh2"><b>The mission</b><span>From docs/trove.md</span></div>
<div class="ms"><blockquote>You are the author of the book you haven't written yet.</blockquote>
<div><p>Trove helps CWRU students and alumni meet. An interview finds what each member knows that others don't and turns it into a book: a title and chapters, all in their own words. Other members browse the shelf and check a book out, which means a short video call with its author.</p>
<p>It is deliberately not LinkedIn. No feed, no followers, no counts, no polish. A first-year's book and a VP's book look identical on the shelf. Meeting comes first; opportunities follow from people who were curious about each other.</p></div></div></section>

<section class="sec"><div class="sh2"><b>The feeling</b><span>What a member should feel on first sight, and what we refuse</span></div>
<div class="fls">{feel_html}</div></section>

<section class="sec"><div class="sh2"><b>What any mark must do</b></div>
<div class="rules">
<div><b>Ink, never red</b>Red is the one action on each screen. If the logo were red, it would be a second button.</div>
<div><b>Work at 16px</b>A browser tab and a phone icon first, a poster second.</div>
<div><b>Say people, not status</b>No crests, ranks, charts or trophies. Nothing that suggests who is ahead.</div>
<div><b>Belong to the system</b>Ink on paper, square corners, dot tone for shade. The covers bring the colour.</div>
</div></section>

<section class="sec"><div class="sh2"><b>Twelve ideas</b><span>Sketched, then judged against the mission</span></div>
<div class="ids">{ideas_html}</div></section>

<section class="sec"><div class="sh2"><b>The three we keep</b><span>Each answers the mission from a different side</span></div>
<div class="kps">{kept_html}</div></section>
"""
    return board("Brand · the thinking", body, 2580)


# ---------------------------------------------------------------- identity boards

def identity(letter, name, idea, story, hero_paper, hero_ink, marks_row, construction, typeset,
             product_logo, product_logo_dark, favicon, marketing, voice, height):
    body = f"""
<style>
.hero{{display:grid;grid-template-columns:1fr 1fr;border:3px solid var(--ink);height:560px}}
.hero>div{{display:grid;place-items:center;position:relative}}
.hero .hp{{background:var(--paper)}}
.hero .hk{{background:var(--ink)}}
.hero .tag{{position:absolute;left:28px;bottom:22px;font:600 13px var(--cond);letter-spacing:.14em;text-transform:uppercase;color:var(--ink2)}}
.hero .hk .tag{{color:var(--rule)}}
.mr{{display:flex;gap:44px;align-items:flex-end}}
.mr figure{{display:flex;flex-direction:column;align-items:flex-start}}
.ic{{width:120px;height:120px;border-radius:26px;display:grid;place-items:center;overflow:hidden}}
.cons{{display:grid;grid-template-columns:520px 1fr;gap:56px;align-items:start}}
.grid{{position:relative;width:520px;height:520px;background:#fff;border:2px solid var(--ink);
 background-image:linear-gradient(var(--rule) 1px,transparent 1px),linear-gradient(90deg,var(--rule) 1px,transparent 1px);background-size:26px 26px}}
.grid>svg{{position:absolute;inset:0}}
.cl{{list-style:none;display:grid;gap:18px}}
.cl li{{border-top:2px solid var(--ink);padding-top:10px;font-size:16px;max-width:620px}}
.cl b{{display:block;font:700 15px var(--cond);letter-spacing:.14em;text-transform:uppercase;margin-bottom:4px}}
.tys{{display:grid;grid-template-columns:repeat(3,1fr);gap:28px}}
.ty{{border-top:2px solid var(--ink);padding-top:14px}}
.ty .s{{margin-top:10px}}
.prod{{display:grid;gap:20px}}
.mk{{display:grid;grid-template-columns:repeat(12,1fr);gap:28px;align-items:start}}
.poster{{position:relative;overflow:hidden;border:2px solid var(--ink)}}
.mx-cap{{font:600 13px var(--cond);letter-spacing:.14em;text-transform:uppercase;color:var(--ink2);margin-top:10px}}
.voice{{display:grid;grid-template-columns:repeat(3,1fr);gap:28px}}
.voice div{{border-top:3px solid var(--ink);padding-top:16px;font:600 30px/1.12 var(--ser);letter-spacing:-.01em}}
.voice span{{display:block;margin-top:10px;font:400 14px/1.45 var(--sans);color:var(--ink2);letter-spacing:0}}
</style>
<span class="eyebrow">Brand · identity {letter}</span>
<h1 class="h1">{name}</h1>
<p class="lede">{idea}</p>
<p class="note" style="margin-top:14px;max-width:900px;font-size:16px">{story}</p>

<section class="sec"><div class="hero"><div class="hp">{hero_paper}<span class="tag">Primary · ink on paper</span></div>
<div class="hk">{hero_ink}<span class="tag">Reversed · paper on ink</span></div></div></section>

<section class="sec"><div class="sh2"><b>The mark at every size</b><span>Tab, phone, avatar, poster</span></div>
<div class="mr">{marks_row}</div>
<div style="display:flex;gap:24px;margin-top:36px;align-items:flex-end">{favicon}</div></section>

<section class="sec"><div class="sh2"><b>Construction</b><span>How it is drawn and why</span></div>
<div class="cons">{construction}</div></section>

<section class="sec"><div class="sh2"><b>Colour and type</b><span>The brand is ink and paper; the members' covers bring the colour</span></div>
<div class="sws">{swatch(INK, "Ink", "The logo, always", False)}{swatch(PAPER, "Paper", "The ground", True)}{swatch("#FFFFFF", "White", "Things you can pick up", True)}{swatch(SUNK, "Paper sunk", "Quiet grounds", True)}
<div class="sw"><div class="swc tone" style="background-color:#fff"></div><b>Dot tone</b><span>Shade and shadow, never a blur</span></div>
<div class="sw" style="width:90px"><div class="swc" style="background:#D42A27;color:#fff;height:40px;margin-top:56px">RED</div><b>Red</b><span>Only the one action. Never the logo.</span></div>
<div class="sw" style="width:auto;display:flex;gap:8px;align-items:flex-start">{"".join(f'<div style="width:46px;height:96px;background:{c};border:1.5px solid var(--ink)"></div>' for c in ["#23415a","#5a2f2a","#6a3525","#26304f","#283d2e","#2c3e5c"])}<div style="width:190px;margin-left:8px"><b style="margin-top:0">Cover inks</b><span>Each book's own colour. Marketing borrows them from real covers, never invents a brand hue.</span></div></div>
</div>
<div class="tys" style="margin-top:44px">{typeset}</div></section>

<section class="sec"><div class="sh2"><b>In the product</b><span>The top bar, on paper and on ink</span></div>
<div class="prod">{topbar(product_logo)}{topbar(product_logo_dark, True)}</div></section>

<section class="sec"><div class="sh2"><b>Marketing</b><span>Campus launch: posters, social, the thing you hand someone</span></div>
{marketing}</section>

<section class="sec"><div class="sh2"><b>Voice</b><span>Headlines this identity would carry</span></div>
<div class="voice">{voice}</div></section>
"""
    return board(f"Brand {letter} · {name}", body, height)


def favicons(mark_fn):
    return (
        browser_tab(mark_fn(16)) + browser_tab(mark_fn(16, "#EEEEEE"), True)
    )


def marks_row(mk, ink_mk, labels=("Poster · 220", "Avatar · 96", "Icon · 48", "Nav · 32", "Tab · 16")):
    sizes = [220, 96, 48, 32, 16]
    out = "".join(f'<figure>{mk(s)}<span class="cap">{l}</span></figure>' for s, l in zip(sizes, labels))
    out += f'<figure><div class="ic" style="background:#111">{ink_mk(76)}</div><span class="cap">App icon · dark</span></figure>'
    out += f'<figure><div class="ic" style="background:#FAFAF7;border:2px solid #111">{mk(76)}</div><span class="cap">App icon · light</span></figure>'
    return out


def type_cols(wordmark_html, wordmark_note):
    return (
        f'<div class="ty"><span class="pt">Wordmark</span><div class="s">{wordmark_html}</div><p class="note" style="margin-top:44px">{wordmark_note}</p></div>'
        '<div class="ty"><span class="pt">Headlines · Newsreader</span><div class="s" style="font:600 40px/1.05 var(--ser);letter-spacing:-.015em">Check out a person.</div>'
        '<div class="s" style="font:italic 400 22px/1.35 var(--ser)">The Librarian’s voice, in italic.</div></div>'
        '<div class="ty"><span class="pt">Labels · Barlow Condensed · Body · Plex Sans</span>'
        '<div class="s" style="font:800 30px/1 var(--cond);letter-spacing:.04em;text-transform:uppercase">Changing course</div>'
        '<div class="s" style="font-size:16px">Plex Sans for anything you read to do a task, at 15–16px.</div></div>'
    )


def board_a():
    hero_paper = word_a(200)
    hero_ink = word_a(200, "#FAFAF7")
    cons = (
        '<div class="grid">' + mark_ribbon(520, "#111") + "</div>"
        '<ul class="cl">'
        "<li><b>The edge</b>A book's edge seen from below: one bar, 76 wide, 13 high. It is also the T's arm.</li>"
        "<li><b>The ribbon</b>18 wide, hanging 57, with a swallowtail cut 9.5 deep: the ribbon you leave where a "
        "conversation should start. It is also the T's stem.</li>"
        "<li><b>The wordmark</b>Trove in Newsreader 600, the face of every book title, set on a rule (the book's "
        "foot) with the same ribbon slipping out under the v. Use the full wordmark wherever there's room; the mark "
        "alone for tabs, icons and avatars.</li>"
        "<li><b>Never</b>Colour the ribbon red, tilt it, animate it swinging, or add a second ribbon.</li></ul>"
    )
    mkt = f"""
<div class="mk">
 <div style="grid-column:span 4"><div class="poster" style="width:100%;height:740px;background:#FAFAF7">
  <svg style="position:absolute;left:78%;top:0" width="64" height="420" viewBox="0 0 64 420"><path d="M0 0H64V420L32 386L0 420Z" fill="#111"/></svg>
  <div style="position:absolute;left:36px;right:36px;top:60px;font:600 56px/1.02 var(--ser);letter-spacing:-.02em;max-width:320px">Every book has a place to start.</div>
  <div style="position:absolute;left:36px;bottom:150px;width:290px;font:400 19px/1.4 var(--ser)">Somebody at Case knows exactly what you're trying to figure out. Their book is on the shelf.</div>
  <div style="position:absolute;left:36px;right:36px;bottom:36px;display:flex;justify-content:space-between;align-items:flex-end;border-top:2px solid #111;padding-top:18px">{word_a(44)}<span class="pt">trove · case.edu</span></div>
 </div><p class="mx-cap">Campus poster · 18×24</p></div>
 <div style="grid-column:span 4;display:grid;gap:28px">
  <div><div class="poster" style="height:470px;background:#111;display:flex;align-items:center;justify-content:center;gap:34px">
   {cover("lake", 168, -3)}{cover("desert", 168, 2)}
   <svg style="position:absolute;left:0;right:0;top:0;margin:auto" width="40" height="150" viewBox="0 0 40 150"><path d="M0 0H40V150L20 136L0 150Z" fill="#FAFAF7"/></svg>
   <div style="position:absolute;left:28px;bottom:24px;font:600 15px var(--cond);letter-spacing:.14em;text-transform:uppercase;color:#C9C9C6">Two new books on the shelf</div>
  </div><p class="mx-cap">Instagram post · new on the shelf</p></div>
  <div><div class="poster" style="height:206px;background:#fff;display:flex;align-items:center;padding:0 36px;gap:28px">
   {mark_ribbon(110)}<div style="font:600 32px/1.08 var(--ser);letter-spacing:-.01em">Your book is on the shelf.<span style="display:block;margin-top:8px;font:400 15px var(--sans);color:#55554F">Email header · sent when a member finishes the interview</span></div></div></div>
 </div>
 <div style="grid-column:span 4;display:flex;gap:28px;align-items:flex-start">
  <div><div class="poster" style="width:150px;height:560px;background:#FAFAF7;display:flex;flex-direction:column;align-items:center;padding:34px 18px;gap:24px">
   {mark_ribbon(80)}<div style="font:600 25px/1.1 var(--ser);text-align:center;letter-spacing:-.01em">You are the author of the book you haven't written yet.</div>
   <div style="margin-top:auto;width:96px;height:96px" class="tone"></div><span class="pt" style="text-align:center">Scan to find yours</span>
  </div><p class="mx-cap">Bookmark handout</p></div>
  <div style="flex:1"><div class="poster" style="height:560px;background:#E8E4D8;display:grid;place-items:center">
   <div style="width:220px;height:300px;background:#FAFAF7;border:2px solid #111;position:relative;display:grid;place-items:center">
    <div style="position:absolute;top:-60px;left:50%;width:120px;height:80px;margin-left:-60px;border:3px solid #111;border-bottom:none;border-radius:60px 60px 0 0"></div>{word_a(60)}</div>
  </div><p class="mx-cap">Tote for the launch table</p></div>
 </div>
</div>"""
    voice = (
        "<div>Every book has a place to start.<span>Poster headline. The ribbon marks the place.</span></div>"
        "<div>Check out a person.<span>The plainest statement of the product; works on a sticker.</span></div>"
        "<div>Read the person, not the profile.<span>The difference from LinkedIn in six words.</span></div>"
    )
    return identity(
        "A", "Bookmark",
        "A ribbon hanging from the edge of a book: it holds a place, and it is the T.",
        "A bookmark holds the place where reading stops and talking starts. "
        "The mark is the quietest of the three and the most literary: no illustration, just an edge and a ribbon, and it "
        "holds at 16px. Its risk is that it is calm enough to be forgettable, so the marketing leans on the ribbon "
        "hanging into the frame as the brand's one gesture.",
        hero_paper, hero_ink,
        marks_row(lambda s: mark_ribbon(s), lambda s: mark_ribbon(s, "#FAFAF7")),
        cons,
        type_cols(word_a(84), "Newsreader 600, −2% tracking, on a rule as thick as the ribbon is narrow ÷ 4."),
        word_a(30), word_a(30, "#FAFAF7"),
        favicons(lambda s, c="#111": mark_ribbon(s, c)),
        mkt, voice, 4300,
    )


def board_b():
    hero_paper = lock_b(150)
    hero_ink = lock_b(150, "#FAFAF7")
    cons = (
        '<div class="grid">' + mark_faces(430, "#111", w=516) + "</div>"
        '<ul class="cl">'
        "<li><b>Two pages</b>An open book seen from the front, the outer corners low and the heads rising to the gutter.</li>"
        "<li><b>Two people</b>The inner edge of each page is one profile: brow, nose, lips, chin. The right page is the left "
        "mirrored, so neither speaker is first. The spine is the space between them.</li>"
        "<li><b>The gap</b>At the noses the pages come within 4 of 120: close enough to read as talking, never touching.</li>"
        "<li><b>The wordmark</b>trove in Newsreader italic 500, lowercase: the Librarian's voice, said rather than announced.</li>"
        "<li><b>Never</b>Give the faces eyes, colour one page differently, or put a face on only one side.</li></ul>"
    )
    big = mark_faces(330, "#111", w=396)
    mkt = f"""
<div class="mk">
 <div style="grid-column:span 4"><div class="poster" style="width:100%;height:740px;background:#FAFAF7">
  <div style="position:absolute;left:0;right:0;top:70px;display:grid;place-items:center">{big}</div>
  <div style="position:absolute;left:36px;right:36px;bottom:120px;font:600 50px/1.04 var(--ser);letter-spacing:-.02em">Every book here is a conversation.</div>
  <div style="position:absolute;left:36px;right:36px;bottom:36px;display:flex;justify-content:space-between;align-items:center;border-top:2px solid #111;padding-top:16px">{word_b(40)}<span class="pt">trove · case.edu</span></div>
 </div><p class="mx-cap">Campus poster · 18×24</p></div>
 <div style="grid-column:span 4;display:grid;gap:28px">
  <div><div class="poster" style="height:470px;background:#111;display:flex;align-items:center;justify-content:center;gap:0">
   {cover("coast", 170, -4, False)}<div style="width:70px;display:grid;place-items:center">{mark_faces(44, "#FAFAF7", w=53)}</div>{cover("forest", 170, 4, False)}
   <div style="position:absolute;left:28px;bottom:24px;font:italic 500 22px var(--ser);color:#FAFAF7">Two books. One conversation.</div>
  </div><p class="mx-cap">Instagram post</p></div>
  <div><div class="poster" style="height:206px;background:#fff;display:flex;align-items:center;padding:0 36px;gap:28px">
   {mark_faces(100, w=120)}<div style="font:600 30px/1.1 var(--ser);letter-spacing:-.01em">Ingrid said yes.<span style="display:block;margin-top:8px;font:400 15px var(--sans);color:#55554F">Email header · a checkout was accepted</span></div></div></div>
 </div>
 <div style="grid-column:span 4;display:grid;gap:28px">
  <div><div class="poster" style="height:380px;background:#111;color:#FAFAF7;padding:34px;display:flex;flex-direction:column">
   <span class="pt" style="color:#C9C9C6">Instagram story</span>
   <div style="font:600 40px/1.06 var(--ser);letter-spacing:-.015em;margin-top:22px">Not followers.<br>Not a feed.<br><i style="font-weight:500">Two people and a book.</i></div>
   <div style="margin-top:auto;display:flex;align-items:center;gap:14px">{lock_b(34, "#FAFAF7")}</div>
  </div></div>
  <div style="display:flex;gap:28px">
   <div><div style="width:200px;height:200px;border-radius:999px;background:#FAFAF7;border:3px solid #111;display:grid;place-items:center">{mark_faces(96, w=115)}</div><p class="mx-cap">Sticker</p></div>
   <div><div style="width:200px;height:200px;background:#111;display:grid;place-items:center;border-radius:999px">{word_b(64, "#FAFAF7")}</div><p class="mx-cap">Pin</p></div>
  </div>
 </div>
</div>"""
    voice = (
        "<div>Every book here is a conversation.<span>The mark, said out loud.</span></div>"
        "<div>Not followers. Not a feed. Two people and a book.<span>What Trove refuses, and what's left.</span></div>"
        "<div>A book you read by talking to its author.<span>The checkout, without the jargon.</span></div>"
    )
    return identity(
        "B", "Facing pages",
        "An open book whose two pages are two people face to face; the spine is the space between them.",
        "Trove's whole idea in one shape: a book you read by talking to its author. It is the warmest and most ownable "
        "of the three, and the only one that shows two people as equals. Its risk is drawing: the profiles must read "
        "at 32px and stay dignified, never cartoonish. It also leans on a well-known figure-ground trick, so the "
        "profiles have to be ours.",
        hero_paper, hero_ink,
        marks_row(lambda s: mark_faces(s, w=s*1.2), lambda s: mark_faces(s*0.82, "#FAFAF7", w=s*0.98)),
        cons,
        type_cols(word_b(96), "Newsreader italic 500, lowercase, −1% tracking. Beside the mark, cap-height ≈ the page height × 0.5."),
        lock_b(30), lock_b(30, "#FAFAF7"),
        favicons(lambda s, c="#111": mark_faces(s, c, w=s)),
        mkt, voice, 4300,
    )


def board_c():
    hero_paper = lock_c(150)
    hero_ink = lock_c(150, "#FAFAF7", "#111111")
    cons = (
        '<div class="grid">' + mark_blank(520) + "</div>"
        '<ul class="cl">'
        "<li><b>The book object</b>The same book as on the shelf: white, a heavy ink outline, the hinge line just inside "
        "the left edge, and a dot shadow down and to the right.</li>"
        "<li><b>The title</b>One short bar where a title would go: written soon, not yet. It is the mark's only detail.</li>"
        "<li><b>Small sizes</b>Below 48px the shadow goes and the hinge and title bar get heavier, because dots turn grey and a second outline reads as a copy icon.</li>"
        "<li><b>The wordmark</b>TROVE in Barlow Condensed 800 caps, the shelf-name face, tracked +5%.</li>"
        "<li><b>Never</b>Write a title on the logo's cover, colour it, or swap the dots for a blur shadow.</li></ul>"
    )
    mkt = f"""
<div class="mk">
 <div style="grid-column:span 4"><div class="poster" style="width:100%;height:740px;background:#FAFAF7">
  <div class="tone-f" style="position:absolute;left:58px;top:56px;width:300px;height:438px;z-index:0;transform:translate(10px,10px)"></div>
  <div style="position:absolute;left:58px;top:56px;width:300px;height:438px;background:#fff;border:3px solid #111;z-index:1">
   <div style="position:absolute;left:14px;top:0;bottom:0;width:2px;background:#111"></div>
   <div style="position:absolute;left:44px;right:30px;top:40px;display:grid;gap:30px">{''.join('<div style="height:0;border-bottom:3px dotted #111"></div>' for _ in range(3))}</div>
   <div style="position:absolute;left:44px;bottom:30px;width:150px;border-bottom:3px dotted #111"></div>
  </div>
  <div style="position:absolute;left:36px;right:36px;bottom:120px;font:600 46px/1.04 var(--ser);letter-spacing:-.02em">Your title goes here. We'll help you find it.</div>
  <div style="position:absolute;left:36px;right:36px;bottom:36px;display:flex;justify-content:space-between;align-items:center;border-top:2px solid #111;padding-top:16px">{lock_c(36)}<span class="pt">trove · case.edu</span></div>
 </div><p class="mx-cap">Campus poster · 18×24</p></div>
 <div style="grid-column:span 4;display:grid;gap:28px">
  <div><div class="poster" style="height:470px;background:#F0F0EB;display:flex;align-items:center;justify-content:center;gap:26px">
   {cover("lake", 132, 0)}{cover("city", 132, 0)}
   <div style="width:132px;height:192px;background:#fff;border:3px solid #111;position:relative;flex:none">
    <div style="position:absolute;left:6px;top:0;bottom:0;width:1.5px;background:#111"></div>
    <div style="position:absolute;left:22px;top:20px;width:62px;height:9px;background:#111"></div>
    <div class="tone-f" style="position:absolute;inset:0;transform:translate(8px,8px);z-index:-1"></div>
   </div>
   <div style="position:absolute;left:28px;bottom:24px;font:800 22px var(--cond);letter-spacing:.04em;text-transform:uppercase">Yours goes here</div>
  </div><p class="mx-cap">Instagram post · the shelf with a gap</p></div>
  <div><div class="poster" style="height:206px;background:#fff;display:flex;align-items:center;padding:0 36px;gap:28px">
   {mark_blank(110)}<div style="font:600 30px/1.1 var(--ser);letter-spacing:-.01em">Your interview is ready when you are.<span style="display:block;margin-top:8px;font:400 15px var(--sans);color:#55554F">Email header · invitation</span></div></div></div>
 </div>
 <div style="grid-column:span 4;display:grid;gap:28px">
  <div><div class="poster" style="height:380px;background:#111;color:#FAFAF7;padding:34px;display:flex;flex-direction:column;position:relative">
   <div style="position:absolute;right:0;top:0;width:55%;height:100%;background-image:radial-gradient(#FAFAF7 1px,transparent 1.2px);background-size:6px 6px;opacity:.35;-webkit-mask-image:linear-gradient(90deg,transparent,#000);mask-image:linear-gradient(90deg,transparent,#000)"></div>
   <span class="pt" style="color:#C9C9C6;position:relative">Instagram story</span>
   <div style="position:relative;font:800 58px/.92 var(--cond);letter-spacing:.02em;text-transform:uppercase;margin-top:22px">No feed.<br>No followers.<br>Just books.</div>
   <div style="position:relative;margin-top:auto">{lock_c(30, "#FAFAF7", "#111111")}</div>
  </div></div>
  <div style="display:flex;gap:28px;align-items:flex-end">
   <div><div style="width:210px;height:136px;background:#fff;border:2px solid #111;padding:14px 16px;display:flex;flex-direction:column;gap:6px">
    <div style="display:flex;justify-content:space-between;align-items:center">{word_c(22)}<span class="pt">Author</span></div>
    <div style="border-bottom:2px dotted #111;height:26px"></div><div style="border-bottom:2px dotted #111;height:22px"></div>
   </div><p class="mx-cap">Name tag · launch night</p></div>
   <div><div style="width:150px;height:150px;display:grid;place-items:center">{mark_blank(140)}</div><p class="mx-cap">Sticker</p></div>
  </div>
 </div>
</div>"""
    voice = (
        "<div>Your title goes here. We'll help you find it.<span>The poster line: the interview finds the book.</span></div>"
        "<div>No feed. No followers. Just books.<span>In shelf-name caps: what Trove refuses, said once.</span></div>"
        "<div>A first-year and a VP, on the same shelf.<span>The level playing field, said plainly.</span></div>"
    )
    return identity(
        "C", "The blank cover",
        "Trove's own book object, outline, hinge and dot shadow, with the title not written yet.",
        "The tagline turned into a picture: the book you haven't written yet. It is drawn from the screentone system we "
        "already ship, so the logo, the shelf and the covers are one family, and the dotted lines become a whole "
        "campaign (fill in the blank). Its risk is that a blank rectangle is generic, so the hinge and the dot shadow "
        "have to stay, and it must never be drawn without them.",
        hero_paper, hero_ink,
        marks_row(lambda s: mark_blank(s, dots=s >= 48), lambda s: mark_blank(s, "#FAFAF7", "#111111", dots=s >= 48)),
        cons,
        type_cols(word_c(110), "Barlow Condensed 800 caps, +5% tracking; the mark sits on the baseline at 1.1× cap height."),
        lock_c(28), lock_c(28, "#FAFAF7", "#111111"),
        favicons(lambda s, c="#111": mark_blank(s, c, dots=False)),
        mkt, voice, 4300,
    )


BOARDS = {
    "BrandThink.dc.html": think_board,
    "BrandA.dc.html": board_a,
    "BrandB.dc.html": board_b,
    "BrandC.dc.html": board_c,
}


def main():
    preview = None
    if "--preview" in sys.argv:
        preview = Path(sys.argv[sys.argv.index("--preview") + 1])
        preview.mkdir(parents=True, exist_ok=True)
    art_root = Path(sys.argv[sys.argv.index("--art") + 1]) if "--art" in sys.argv else None
    for name, fn in BOARDS.items():
        html = fn()
        (PROJECT / name).write_text(html)
        if preview:
            p = html
            for key, (blob, *_rest) in ART.items():
                if art_root:
                    p = p.replace(f"/_blob/{blob}", str(art_root / LOCAL_ART[key]))
            (preview / name.replace(".dc.html", ".html")).write_text(p)
        print("wrote", name)


if __name__ == "__main__":
    main()
