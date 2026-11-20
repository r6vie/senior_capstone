"""Book screen B (the book opens) and C (pulled from the shelf). Head CSS is taken from FreshBookStrata."""
import re, sys
SRC = sys.argv[1]; OUT = sys.argv[2]
src = open(SRC).read()
head = src[: src.index("</helmet>")]
head = re.sub(r"<title>.*?</title>", "<title>{TITLE}</title>", head)
BAND = "/_blob/a738d6db7ccf4a04fecfd50298474562"
COVER_SM = "/_blob/6207834eb207b12eb62aa34a93a8b5bc"

T, A = "The Night Shift Knows", "Maya Okafor"
BLURB = ("I've worked nights on a surgical ward for two years. This is the hospital the day shift never sees: "
         "who really runs it at 3 a.m., where things go wrong, and how to stay human on the wrong side of the clock.")
CH = [("Handoffs are where things break", "Most mistakes she has seen began in the five minutes between shifts, not in the work itself."),
      ("Charge nurses run the hospital", "Who actually decides which bed a patient gets, and how to ask them nicely."),
      ("When to wake the doctor", "The judgement call every night nurse makes alone, and how she learned to trust it."),
      ("Learning to sleep in daylight", "The small routines that got her through two years of nights.")]

CSS = """
<style>
/* Book screens B and C. New pieces are marked; everything else is the system's. */
.cov-cut{--c-ink:#262b5e;--c-2:#8b5d7d}
.cov-cut .ko{background:transparent}
.cov-cut .book-title{text-align:left;color:var(--c-ink);font-weight:600;letter-spacing:-.02em;line-height:1.02}
.cov-cut .book-author{align-self:auto;text-align:left;margin-top:.8em;color:var(--c-2);font-size:7.5px;letter-spacing:.28em}
.board-head{display:flex;flex-direction:column;gap:8px;padding:28px 44px 0;height:150px;box-sizing:border-box}
.board-head .note{max-width:1100px;margin:0}
.scr{position:relative;width:1440px;height:880px;overflow:hidden}
.scr.rd::after{content:"";position:absolute;z-index:10;inset:0;border:var(--line) solid var(--ink);pointer-events:none}
.scr-label{position:absolute;left:44px;top:-30px}

/* ---------- B: the book opens ---------- */
.rd{background:var(--paper);color:var(--ink)}
/* the backdrop is the shelf gone dark: fine dots in paper, very sparse, never a blur */
/* B over the shelf: the shelf stays where it was, shaded in dots as in C; the bars that carry text are paper */
.sh-dim.full{right:0}
.rd-bar{position:absolute;z-index:6;left:0;right:0;top:0;height:64px;background:var(--paper);border-bottom:var(--line) solid var(--ink);display:flex;align-items:center;gap:24px;padding:0 32px}
.rd-bar .button-quiet{color:var(--ink)}
.rd-tabs{display:flex;gap:4px;margin:0 auto;font:600 15px/1 var(--font-display);letter-spacing:.12em;text-transform:uppercase}
.rd-tabs a{display:inline-grid;place-items:center;min-width:44px;height:44px;padding:0 12px;color:var(--ink-2);text-decoration:none;border-bottom:3px solid transparent}
.rd-tabs a[aria-current]{color:var(--ink);border-bottom-color:var(--ink)}
.rd-keys{font:400 13px/1 var(--font-sans);color:var(--ink-2);width:220px;text-align:right}
.rd-keys kbd{display:inline-grid;place-items:center;min-width:22px;height:22px;margin:0 2px;border:1.5px solid var(--ink-2);font:600 11px/1 var(--font-sans)}
.rd-book{position:absolute;z-index:5;left:140px;top:86px;width:1160px;height:668px;display:grid;grid-template-columns:1fr 1fr}
/* the page block: two sheets of edge under the open pages */
.rd-book::before,.rd-book::after{content:"";position:absolute;border:var(--line) solid var(--ink)}
.rd-book::before{inset:10px -10px -10px 10px;background:var(--paper-sunk)}
.rd-book::after{inset:5px -5px -5px 5px;background:var(--white)}
.rd-page{position:relative;z-index:1;overflow:hidden;background:var(--white);color:var(--ink);border:var(--line) solid var(--ink);display:flex;flex-direction:column;padding:52px 56px 0}
.rd-left{border-right:0;padding-right:64px;background:var(--paper)}
.rd-right{padding-left:64px}
/* the gutter: shade where the pages bow into the spine, in dots */
.rd-gutter{position:absolute;z-index:2;left:calc(50% - 26px);top:0;bottom:0;width:52px;pointer-events:none;
  background:radial-gradient(circle,var(--ink) .9px,transparent 1.3px) 0 0/5px 5px;
  -webkit-mask-image:linear-gradient(90deg,transparent,#000 46%,#000 54%,transparent);mask-image:linear-gradient(90deg,transparent,#000 46%,#000 54%,transparent)}
.rd-gutter::after{content:"";position:absolute;left:25px;top:0;bottom:0;width:2px;background:var(--ink)}
.rd-art{position:absolute;left:-60px;bottom:-14px;height:340px;width:auto;display:block}
.rd-art.short{height:262px;bottom:44px;left:-20px}
.rd-title{margin:0;font:600 46px/1.04 var(--font-serif);letter-spacing:-.015em;text-wrap:balance}
.rd-blurb{margin:18px 0 0;font:400 16px/1.55 var(--font-sans);max-width:420px}
.rd-foot{position:absolute;left:0;right:0;bottom:16px;display:flex;justify-content:space-between;align-items:center;padding:0 60px 0 22px;height:56px;font:600 13px/1 var(--font-display);letter-spacing:.14em;text-transform:uppercase;color:var(--ink-2)}
.rd-foot a{color:var(--ink);text-decoration:none;display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:0 8px}
.rd-foot .off{color:var(--rule)}
.rd-folio{font:500 13px/1 var(--font-serif);letter-spacing:0;text-transform:none;color:var(--ink-2)}
/* the corner of the right page lifts: the page can be turned */
.rd-curl{position:absolute;z-index:3;right:0;bottom:0;width:44px;height:44px;
  background:linear-gradient(-45deg,var(--paper) 0 49%,transparent 50%),radial-gradient(circle,var(--ink) 1px,transparent 1.4px) 0 0/4px 4px,var(--paper-sunk)}
.rd-curl::after{content:"";position:absolute;inset:0;background:linear-gradient(-45deg,transparent 48.5%,var(--ink) 49%,var(--ink) 51%,transparent 51.5%)}
.toc{list-style:none;margin:20px 0 0;padding:0;display:grid}
.toc li{display:grid;grid-template-columns:40px 1fr 24px;gap:0 6px;align-items:baseline;padding:16px 10px 16px 12px;margin:0 -10px 0 -12px;border-top:2.5px dotted var(--ink)}
.toc li:last-child{border-bottom:2.5px dotted var(--ink)}
.toc b{font:700 22px/1 var(--font-display)}
.toc h3{margin:0;font:600 21px/1.2 var(--font-serif)}
.toc p{grid-column:2;margin:5px 0 0;font:400 14px/1.45 var(--font-sans);color:var(--ink-2)}
.toc i{font-style:normal;font:700 20px/1 var(--font-display);text-align:right}
.toc li.is-hover{background:var(--paper-sunk)}
.toc li.is-hover h3{text-decoration:underline;text-decoration-thickness:2px;text-underline-offset:4px}
.toc.compact li{padding:11px 10px 11px 12px}
.toc.compact h3{font-size:17px}
.toc.compact b{font-size:18px}
.toc li[aria-current]{background:var(--ink);color:var(--white)}
.toc li[aria-current] i{color:var(--white)}
.ch-num{font:800 120px/.8 var(--font-display);margin:0 0 18px}
.ch-title{margin:0;font:600 38px/1.1 var(--font-serif);letter-spacing:-.01em;text-wrap:balance}
.ch-body{margin:22px 0 0;font:400 19px/1.55 var(--font-serif);max-width:420px}
.spark{display:flex;flex-direction:column;gap:8px;margin-top:30px;padding-top:22px;border-top:2.5px dotted var(--ink)}
.spark .button{align-self:flex-start;min-height:44px;font-size:15px;padding:0 18px}
.spark .note{margin:0;font-size:13px}
.rd-act{position:absolute;z-index:6;left:0;right:0;bottom:0;height:96px;background:var(--paper);border-top:var(--line) solid var(--ink);display:flex;justify-content:center;align-items:center;gap:20px}
.rd-act .note{color:var(--ink-2)}
.rd-act .button-primary{border-color:var(--red)}

/* ---------- C: pulled from the shelf ---------- */
.sh{background:var(--paper)}
.sh-top{display:flex;align-items:center;gap:36px;height:64px;padding:0 36px}
.sh-row{position:absolute;left:44px;width:1360px}
.sh-row .shelf-name{font-size:24px}
.sh-row .shelf-books{gap:28px}
.sh-row .book{width:122px;height:178px}
/* where the book was: its place on the shelf stays open while it is out */
.slot{flex:none;width:122px;height:178px;border:2.5px dotted var(--ink);display:grid;place-items:center;font:600 12px/1.2 var(--font-display);letter-spacing:.14em;text-transform:uppercase;color:var(--ink-2);text-align:center}
.sh-dim{position:absolute;z-index:4;inset:0;right:600px;background:radial-gradient(circle,var(--ink) .9px,transparent 1.3px) 0 0/5px 5px;opacity:.4}
.pn{position:absolute;z-index:5;top:0;right:0;bottom:0;width:600px;background:var(--white);border-left:var(--line-heavy) solid var(--ink);display:flex;flex-direction:column}
.pn::before{content:"";position:absolute;top:0;bottom:0;left:-15px;width:12px;background:radial-gradient(circle,var(--ink) 1.3px,transparent 1.7px) 0 0/5px 5px}
.pn-bar{display:flex;align-items:center;gap:4px;height:60px;padding:0 16px;border-bottom:var(--line) solid var(--ink)}
.pn-bar .button{min-height:44px;padding:0 12px;font-size:15px}
.pn-bar .sp{flex:1}
.pn-hero{position:relative;height:318px;flex:none}
.pn-hero .art{position:absolute;left:0;right:0;top:0;height:200px;overflow:hidden;background:var(--paper);border-bottom:var(--line) solid var(--ink)}
.pn-hero img.band{position:absolute;height:300px;left:-150px;top:-62px}
.pn-hero .book{position:absolute;left:40px;top:118px}
.pn-head{position:absolute;left:196px;top:220px;right:28px}
.pn-head h1{margin:0;font:600 32px/1.06 var(--font-serif);letter-spacing:-.01em;text-wrap:balance}
.pn-head .byline{margin-top:12px}
.pn-body{padding:0 40px 0;display:flex;flex-direction:column;gap:20px;overflow:hidden}
.pn-body > p{margin:0;font:400 16px/1.55 var(--font-sans)}
.pn-act{display:flex;align-items:center;gap:16px}
.acc{list-style:none;margin:0;padding:0}
.acc li{border-top:2.5px dotted var(--ink)}
.acc li:last-child{border-bottom:2.5px dotted var(--ink)}
.acc .row{display:grid;grid-template-columns:30px 1fr 20px;align-items:center;min-height:52px;gap:6px}
.acc b{font:700 18px/1 var(--font-display)}
.acc h3{margin:0;font:600 18px/1.25 var(--font-serif)}
.acc i{font-style:normal;font:700 18px/1 var(--font-display);text-align:right}
.acc .open{padding:0 0 16px 36px;display:grid;gap:10px}
.acc .open p{margin:0;font:400 15px/1.5 var(--font-sans);color:var(--ink-2)}
.acc .open .button{justify-self:start;min-height:40px;padding:0 14px;font-size:14px}
.pn-full{margin-top:auto;padding:14px 40px 18px;border-top:var(--line) solid var(--ink);display:flex;justify-content:space-between;align-items:center}
.pn-full .note{margin:0;font-size:13px}

/* B round 3: the book carries its own controls */
.sh-dim.full{top:64px}
.rd-head{position:absolute;top:10px;left:22px;right:22px;height:44px;display:flex;align-items:center}
.rd-head-r{justify-content:flex-end;left:30px}
.rd-close{display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:0 8px;margin-left:-8px;color:var(--ink);text-decoration:none;font:600 14px/1 var(--font-display);letter-spacing:.14em;text-transform:uppercase}
.rd-close span{text-decoration:underline;text-decoration-thickness:2px;text-underline-offset:4px}
.rd .rd-tabs{margin:0;font-size:14px}
.rd .rd-tabs a{min-width:36px;height:40px;padding:0 9px}
.rd-page{padding-top:76px}
.rd-title{font-size:42px}
.rd-ask{display:flex;flex-direction:column;align-items:flex-start;gap:10px;margin-top:22px}
.rd-ask .note{margin:0;font-size:13px}
.rd-ask-ch{margin-top:30px;padding-top:22px;border-top:2.5px dotted var(--ink)}
.rd-book{top:124px}
.rd-art{height:250px;bottom:-12px;left:0}

/* the shelf behind the open book steps back */
.rd .sh-row{opacity:.6}
/* B round 4: a real book. Two cover boards and a spine under a block of pages; the top pages bow down into the
   gutter, and the page edges stack at the fore-edge and foot. Flat ink and paper, shade in dots, no blur.
   Geometry (book box 1180 x 724, gutter at x 590) is shared by the SVG and the clip paths below. */
.rd-book{left:130px;top:114px;width:1180px;height:724px;display:block}
.rd-book::before,.rd-book::after{content:none}
.rd-book svg{position:absolute;inset:0;width:1180px;height:724px;overflow:visible}
.rd-book .bk-front{z-index:3;pointer-events:none}
.rd-page{position:absolute;top:0;height:724px;width:590px;border:0;background:var(--paper);padding:100px 56px 0 84px}
.rd-left{left:0;clip-path:path("M 28,30 C 200,20 470,16 560,28 Q 584,36 590,54 L 590,712 Q 584,700 560,694 C 470,686 200,690 28,696 Z")}
.rd-right{left:590px;padding:100px 84px 0 64px;clip-path:path("M 562,30 C 390,20 120,16 30,28 Q 6,36 0,54 L 0,712 Q 6,700 30,694 C 120,686 390,690 562,696 Z")}
.rd-head{top:34px;left:76px;right:76px}
.rd-head-r{left:60px}
.rd-foot{bottom:40px;padding:0 84px 0 76px}
.rd-right .rd-foot{padding:0 84px 0 56px}
.rd-art{left:28px;bottom:24px;height:250px}
.rd-art.short{left:28px;bottom:24px;height:250px}
.rd-gutter{top:56px;bottom:14px;left:calc(50% - 30px);width:60px;z-index:2}
.rd-gutter::after{content:none}
.rd-curl{right:28px;bottom:28px;width:40px;height:40px;
  background:linear-gradient(-45deg,var(--white) 0 49%,transparent 50%),radial-gradient(circle,var(--ink) 1px,transparent 1.4px) 0 0/4px 4px,var(--paper-sunk)}
</style>
"""

def cover(cls, img, title, author, extra=""):
    return (f'<div class="book {cls}"{extra} aria-label="{title}, by {author}"><span class="book-cover"><img class="cover-art" src="{img}" alt="">'
            f'<span class="book-title"><span class="ko">{title}</span></span><span class="book-author"><span class="ko">{author}</span></span></span></div>')

def board(title, w, h, body):
    return (head.replace("{TITLE}", title) + CSS + "</helmet>\n" +
            f'<div style="width:{w}px;height:{h}px;background:var(--paper);color:var(--ink);font-family:var(--font-sans);overflow:hidden">' +
            body + "</div>\n</x-dc>\n" +
            f"<script type=\"text/x-dc\" data-dc-script data-props='{{\"$preview\":{{\"width\":{w},\"height\":{h}}}}}'>\n"
            "class Component extends DCLogic {\nrenderVals() {\nreturn {};\n}\n}\n</script>\n</body>\n</html>\n")

# ---------------- the shelf behind B and C ----------------
SHELF1 = [("cov-pencil", "/_blob/44e221e431b65fd97ac2bb011b12692a", "Cold Calls That Worked", "Daniel Reyes-Whitfield"),
          None,
          ("cov-wash", "/_blob/bf227d05c72ce22a5d848159b75e091c", "Field Notes From a Food Truck", "Priya Raman"),
          ("cov-cut", "/_blob/e6735f1a2d0f8252ddcd9aec399cfe7e", "What Bridges Remember", "Tom Abernathy"),
          ("cov-stipple", "/_blob/1de1c8ff20f8bb8256e28ba474e3e5f8", "Desert Survey Season", "Lena Okonkwo"),
          ("cov-gouache", "/_blob/f064d27d44fa3f1ad23222f3fd176bb7", "The Last Lab Rotation", "Sam Lindqvist")]
SHELF2 = [("cov-stipple", "/_blob/1de1c8ff20f8bb8256e28ba474e3e5f8", "Teaching Kids to Code", "Ana Beltrán"),
          ("cov-gouache", "/_blob/f064d27d44fa3f1ad23222f3fd176bb7", "Starting a Clinic From Zero", "Kofi Mensah"),
          ("cov-pencil", "/_blob/44e221e431b65fd97ac2bb011b12692a", "Two Years in Patent Law", "Grace Liu"),
          ("cov-cut", "/_blob/e6735f1a2d0f8252ddcd9aec399cfe7e", "Night Classes", "Marcus Bell"),
          ("cov-wash", "/_blob/bf227d05c72ce22a5d848159b75e091c", "The Quiet Startup", "Hana Sato"),
          ("cov-pencil", "/_blob/44e221e431b65fd97ac2bb011b12692a", "Mapping the Lake", "Jonah Price")]
def shelf(name, books, top):
    bs = "".join('<div class="slot" aria-label="The book you are reading came from here">Out<br>reading</div>' if b is None
                 else cover(*b) for b in books)
    return (f'<div class="sh-row" style="top:{top}px"><div class="shelf-head"><h2 class="shelf-name">{name}</h2><a href="#">See all</a></div>'
            f'<div class="shelf-books">{bs}</div><div class="ledge" style="margin-top:0"></div></div>')

SHELF_BG = shelf("Shift work", SHELF1, 110) + shelf("Starting out", SHELF2, 420)
# ---------------- B ----------------
HEADER = ('<header class="sh-top"><span class="wordmark">Trove</span><nav class="nav" aria-label="Main"><a href="#" aria-current="page">Shelf</a>'
          '<a href="#">My book</a><a href="#">Checkouts</a><a href="#">Past meets</a></nav>'
          '<input class="search" style="margin-left:auto" type="search" placeholder="Search by topic" aria-label="Search by topic"><span class="avatar">J</span></header>')

def tabs(cur):
    t = "".join(f'<a href="#"{" aria-current=\"page\"" if cur == k else ""}>{lab}</a>'
                for k, lab in [(0, "Contents")] + [(i, str(i)) for i in range(1, 5)])
    return f'<nav class="rd-tabs" aria-label="Pages of this book">{t}</nav>'

# the book's own controls are its running heads: close on the left page, the page tabs on the right
HEAD_L = '<div class="rd-head"><a href="#" class="rd-close">✕ <span>Close the book</span></a></div>'
def head_r(cur):
    return f'<div class="rd-head rd-head-r">{tabs(cur)}</div>'

def ask(note=True):
    return ('<div class="rd-ask"><a class="button button-primary" href="#">Ask to check out</a>'
            + '</div>')

def toc(active=None, hover=None, compact=False, summaries=True):
    out = f'<ol class="toc{" compact" if compact else ""}">'
    for i, (t, s) in enumerate(CH, 1):
        attr = ' aria-current="page"' if active == i else (' class="is-hover"' if hover == i else "")
        out += f'<li{attr}><b>{i}</b><h3>{t}</h3><i>›</i>' + (f"<p>{s}</p>" if summaries else "") + "</li>"
    return out + "</ol>"

spread1 = (
    '<section class="rd-page rd-left" aria-label="Title page">' + HEAD_L +
    f'<h1 class="rd-title">{T}</h1><p class="byline" style="margin:14px 0 0">by {A}</p>'
    f'<p class="rd-blurb">{BLURB}</p>' + ask() +
    f'<img class="rd-art" src="{BAND}" alt="">'
    '</section>'
    '<section class="rd-page rd-right" aria-label="Contents">' + head_r(0)
    + toc(hover=2) +
    '<div class="rd-curl" aria-hidden="true"></div>'
    '</section><div class="rd-gutter" aria-hidden="true"></div>')

spread2 = (
    '<section class="rd-page rd-left" aria-label="Contents">' + HEAD_L
    + toc(active=2, compact=True, summaries=False) + ask() +
    f'<img class="rd-art short" src="{BAND}" alt="">'
    '</section>'
    '<section class="rd-page rd-right" aria-label="Chapter 2">' + head_r(2) +
    f'<div class="ch-num" aria-hidden="true">2</div><h2 class="ch-title">{CH[1][0]}</h2>'
    f'<p class="ch-body">{CH[1][1]}</p>'
    '<div class="rd-curl" aria-hidden="true"></div>'
    '</section><div class="rd-gutter" aria-hidden="true"></div>')

B_NOTE = ("Book screen B · the book opens over the shelf, under the library's header. Everything for the book is in the "
          "book: Close and the page tabs at the head of the pages, Ask to check out on the title page and under the contents, always about the whole book. "
          "Built as a book, to be animated as paper: cover boards, a spine at head and foot, stacked page edges, pages bowing "
          "into the gutter.")

LP = "M 28,30 C 200,20 470,16 560,28 Q 584,36 590,54 L 590,712 Q 584,700 560,694 C 470,686 200,690 28,696 Z"
RP = "M 1152,30 C 980,20 710,16 620,28 Q 596,36 590,54 L 590,712 Q 596,700 620,694 C 710,686 980,690 1152,696 Z"
COVER = "#16302e"   # the book's own cover ink (strata), never the UI red
def _stack(path, dx):
    # the page block: the same page, stepped out at the fore-edge and down at the foot
    return "".join(f'<path d="{path}" transform="translate({dx*k},{3*k})" fill="var(--white)" stroke="var(--ink)" stroke-width="1.5"/>'
                   for k in (4, 3, 2, 1))
BOOK_BACK = (
    '<svg class="bk-back" viewBox="0 0 1180 724" aria-hidden="true">'
    # the spine, seen at head and foot where the boards wrap round it
    f'<path d="M 560,8 Q 590,-6 620,8 L 620,720 Q 590,740 560,720 Z" fill="{COVER}" stroke="var(--ink)" stroke-width="2"/>'
    # the two boards, a little larger than the pages
    f'<path d="M 590,12 L 14,12 Q 4,12 4,22 L 4,708 Q 4,718 14,718 L 590,722 Z" fill="{COVER}" stroke="var(--ink)" stroke-width="2"/>'
    f'<path d="M 590,12 L 1166,12 Q 1176,12 1176,22 L 1176,708 Q 1176,718 1166,718 L 590,722 Z" fill="{COVER}" stroke="var(--ink)" stroke-width="2"/>'
    + _stack(LP, -4) + _stack(RP, 4) + '</svg>')
BOOK_FRONT = (
    '<svg class="bk-front" viewBox="0 0 1180 724" aria-hidden="true">'
    f'<path d="{LP}" fill="none" stroke="var(--ink)" stroke-width="2"/><path d="{RP}" fill="none" stroke="var(--ink)" stroke-width="2"/>'
    # the gutter: where the two pages meet the spine
    '<path d="M 590,54 L 590,712" stroke="var(--ink)" stroke-width="2"/></svg>')

def b_screen(label, spread, top):
    return (f'<div style="position:absolute;left:0;top:{top}px"><span class="frame-label scr-label">{label}</span>'
            f'<div class="scr rd">{HEADER}{SHELF_BG}<div class="sh-dim full" aria-hidden="true"></div><div class="rd-book">{BOOK_BACK}{spread}{BOOK_FRONT}</div></div></div>')
bodyB = ('<div style="position:relative;height:100%">'
         f'<div class="board-head"><span class="frame-label">B · The book opens</span><p class="note">{B_NOTE}</p></div>'
         + b_screen("Opened: title page and contents", spread1, 190)
         + b_screen("A chapter: contents move left, the chapter faces them", spread2, 1120)
         + "</div>")
open(f"{OUT}/FreshReaderOpen.dc.html", "w").write(board("Book screen B: the book opens", 1440, 2020, bodyB))

# ---------------- C ----------------
acc = '<ol class="acc">'
for i, (t, s) in enumerate(CH, 1):
    if i == 1:
        acc += (f'<li><div class="row"><b>{i}</b><h3>{t}</h3><i>–</i></div><div class="open"><p>{s}</p>'
                '</div></li>')
    else:
        acc += f'<li><div class="row"><b>{i}</b><h3>{t}</h3><i>+</i></div></li>'
acc += "</ol>"
panel = ('<aside class="pn" aria-labelledby="pn-title">'
         '<div class="pn-bar"><a class="button button-quiet" href="#">‹ Previous</a><a class="button button-quiet" href="#">Next ›</a>'
         '<span class="sp"></span><a class="button button-quiet" href="#">Close ✕</a></div>'
         f'<div class="pn-hero"><div class="art"><img class="band" src="{BAND}" alt=""></div>'
         + cover("cov-strata", COVER_SM, T, A) +
         f'<div class="pn-head"><h1 id="pn-title">{T}</h1><p class="byline">by {A}</p></div></div>'
         f'<div class="pn-body"><p>{BLURB}</p>'
         '<div class="pn-act"><a class="button button-primary" href="#">Ask to check out</a></div>'
         '<h2 class="shelf-name" style="font-size:20px;margin-top:6px">What you could talk about</h2>' + acc + '</div>'
         '<div class="pn-full" style="justify-content:flex-end"><a class="button button-quiet" href="#" style="font-size:15px">Open the full page ›</a></div>'
         '</aside>')
C_NOTE = ("Book screen C · pulled from the shelf. For browsing: the book slides out to a reading panel and the shelf "
          "stays where it was, shaded in dots, with the book's place left open. Previous and Next step along the same shelf "
          "(and the arrow keys), so a member can read ten books without losing their place. The chapters open in place; "
          "Ask to check out is in reach without scrolling. The full book page (A) stays as the page a link opens.")
bodyC = ('<div style="position:relative;height:100%">'
         f'<div class="board-head"><span class="frame-label">C · Pulled from the shelf</span><p class="note">{C_NOTE}</p></div>'
         '<div style="position:absolute;left:0;top:190px"><span class="frame-label scr-label">On the shelf, Next steps to the next book</span>'
         '<div class="scr sh"><header class="sh-top"><span class="wordmark">Trove</span><nav class="nav" aria-label="Main"><a href="#" aria-current="page">Shelf</a><a href="#">My book</a><a href="#">Checkouts</a><a href="#">Past meets</a></nav>'
         '<input class="search" style="margin-left:auto" type="search" placeholder="Search by topic" aria-label="Search by topic"><span class="avatar">J</span></header>'
         + shelf("Shift work", SHELF1, 110) + shelf("Starting out", SHELF2, 420) +
         '<div class="sh-dim" aria-hidden="true"></div>' + panel + '</div></div></div>')
open(f"{OUT}/FreshReaderPanel.dc.html", "w").write(board("Book screen C: pulled from the shelf", 1440, 1090, bodyC))
