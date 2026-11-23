"""Covers: Watercolor page: one cover board per watercolour book (art/watercolor/covers.py), built from the strata
cover board (FinalCoverForest: the 176 x 257 shelf book, the narrow hinge and the approved cover type, under a large
cover that is the same book scaled) with the label, title, name, ink and art swapped. The covers are painted edge to
edge (Josef, 2026-11-21), so the ink is chosen from the paint behind the title (art/watercolor/ink.py): cream on a
dark top, the book's own dark ink on a light one.

python3 watercolor_boards.py <root> lighthouse=<blob> autumn3=<blob> mesa=<blob> hills=<blob> lake=<blob> winter=<blob> city=<blob> blossom=<blob> prairie=<blob> beach=<blob>
-> <root>/project/WCCover{Lighthouse,Harbor,Autumn}2.dc.html (round 2, painted to the top). Round 1's boards
(WCCover{Lighthouse,Harbor,Autumn}, white tops) stay on the canvas as Josef asked; their art is no longer rendered by
covers.py, which now paints the round 2 skies."""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "art", "watercolor"))
from ink import ink_for                                          # the title adjusts to the paint behind it
ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "art", "watercolor", "out")

ROOT, IDS = sys.argv[1], dict(a.split("=") for a in sys.argv[2:])
P = f"{ROOT}/project"
src = open(f"{P}/FinalCoverForest.dc.html").read()
blob = re.findall(r'class="cover-art" src="/_blob/([0-9a-f]{32})"', src)[0]
OLD = dict(label="Strata · fir forest in morning light", title="Room to Grow", author="Noah Bergstrom", ink="#283d2e")

BOOKS = [
    dict(key="lighthouse", file="WCCoverLighthouse2", label="Watercolor · lighthouse at dusk, painted to the top",
         title="Keeping the Light", author="Maren Holt", ink="#2c3e5c"),
    # the harbor painted to the top is removed (Josef, 2026-11-23); round 1's harbor board stays
    # the autumn rework (Josef: the bridge was half there and cut off, the trees lazy); the round 1 and 2 autumn
    # boards are removed (Josef, 2026-11-23)
    dict(key="autumn3", art="autumn", file="WCCoverAutumn3",
         label="Watercolor · autumn river, the bridge and trees reworked", title="The Long Way Home",
         author="Emmett Clarke", ink="#5a3420"),
    # the abstract set (Josef, 2026-11-23: abstraction like the round 1 headland; art/watercolor/abstract.py)
    dict(key="mesa", file="WCCoverMesa", label="Watercolor, abstract · desert butte at dusk",
         title="The High Desert", author="Lucia Navarro", ink="#3a2c3a"),
    dict(key="hills", file="WCCoverHills", label="Watercolor, abstract · patchwork hills with cypresses",
         title="Slow Harvest", author="Tomas Rinaldi", ink="#4a4a2e"),
    dict(key="lake", file="WCCoverLake", label="Watercolor, abstract · alpine lake",
         title="Above the Tree Line", author="Ingrid Solberg", ink="#23415a"),
    dict(key="winter", file="WCCoverWinter", label="Watercolor, abstract · winter dusk with firs",
         title="First Snow", author="Hannah Lindqvist", ink="#3e2b45"),
    # the abstract set, second four (art/watercolor/abstract2.py)
    dict(key="city", file="WCCoverCity", label="Watercolor, abstract · city at night on the river",
         title="After Hours", author="Marcus Bell", ink="#2c2d52"),
    dict(key="blossom", file="WCCoverBlossom", label="Watercolor, abstract · blossom tree by a pond",
         title="Second Spring", author="Aiko Tanaka", ink="#5a3048"),
    dict(key="prairie", file="WCCoverPrairie", label="Watercolor, abstract · prairie storm",
         title="Weather the Season", author="Caleb Hart", ink="#33364a"),
    dict(key="beach", file="WCCoverBeach", label="Watercolor, abstract · beach at sunset",
         title="Off the Clock", author="Leilani Cruz", ink="#5a2f2a"),
]

for b in BOOKS:
    if b["key"] not in IDS:
        continue
    h = src
    ink, lum, contrast = ink_for(os.path.join(ART, f"{b.get('art', b['key'])}-xl.png"), b["ink"])
    print(b["key"], ink, round(lum, 3), round(contrast, 2))
    for k in ("label", "title", "author"):
        assert OLD[k] in h, k
        h = h.replace(OLD[k], b[k])
    h = h.replace(OLD["ink"], ink)
    h = h.replace(blob, IDS[b["key"]])
    h = re.sub(r"<title>.*?</title>", f"<title>{b['label']}</title>", h)
    # painted edge to edge, so the name has no knockout: it sits on the paint like the title
    h = h.replace("</helmet>", "<style>.cov-final .book-author .ko{background:transparent}</style>\n</helmet>", 1)
    open(f"{P}/{b['file']}.dc.html", "w").write(h)
print("ok")
