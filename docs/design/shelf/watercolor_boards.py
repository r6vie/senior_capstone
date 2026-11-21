"""Covers: Watercolor page: one cover board per watercolour book (art/watercolor/covers.py), built from the strata
cover board (FinalCoverForest: the 176 x 257 shelf book, the narrow hinge and the approved cover type, under a large
cover that is the same book scaled) with the label, title, name, ink and art swapped. The covers are painted edge to
edge (Josef, 2026-11-21), so the ink is chosen from the paint behind the title (art/watercolor/ink.py): cream on a
dark top, the book's own dark ink on a light one.

python3 watercolor_boards.py <root> lighthouse=<blob> harbor=<blob> autumn=<blob>
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
    dict(key="harbor", file="WCCoverHarbor2", label="Watercolor · harbor in the morning, painted to the top",
         title="Harbor Season", author="Sofia Marchetti", ink="#2f4a63"),
    dict(key="autumn", file="WCCoverAutumn2", label="Watercolor · autumn river in golden haze, painted to the top",
         title="The Long Way Home", author="Emmett Clarke", ink="#5a3420"),
]

for b in BOOKS:
    if b["key"] not in IDS:
        continue
    h = src
    ink, lum, contrast = ink_for(os.path.join(ART, f"{b['key']}-xl.png"), b["ink"])
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
