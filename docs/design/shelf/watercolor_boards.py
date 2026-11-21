"""Covers: Watercolor page: one cover board per watercolour book (art/watercolor/covers.py), built from the strata
cover board (FinalCoverForest: the 176 x 257 shelf book, the narrow hinge and the approved cover type, under a large
cover that is the same book scaled) with the label, title, name, ink and art swapped.

python3 watercolor_boards.py <root> lighthouse=<blob> harbor=<blob> autumn=<blob>
-> <root>/project/WCCover{Lighthouse,Harbor,Autumn}.dc.html"""
import re
import sys

ROOT, IDS = sys.argv[1], dict(a.split("=") for a in sys.argv[2:])
P = f"{ROOT}/project"
src = open(f"{P}/FinalCoverForest.dc.html").read()
blob = re.findall(r'class="cover-art" src="/_blob/([0-9a-f]{32})"', src)[0]
OLD = dict(label="Strata · fir forest in morning light", title="Room to Grow", author="Noah Bergstrom", ink="#283d2e")

BOOKS = [
    dict(key="lighthouse", file="WCCoverLighthouse", label="Watercolor · lighthouse on the headland",
         title="Keeping the Light", author="Maren Holt", ink="#2c3e5c"),
    dict(key="harbor", file="WCCoverHarbor", label="Watercolor · hillside harbor town",
         title="Harbor Season", author="Sofia Marchetti", ink="#2f4a63"),
    dict(key="autumn", file="WCCoverAutumn", label="Watercolor · autumn river",
         title="The Long Way Home", author="Emmett Clarke", ink="#5a3420"),
]

for b in BOOKS:
    if b["key"] not in IDS:
        continue
    h = src
    for k in ("label", "title", "author", "ink"):
        assert OLD[k] in h, k
        h = h.replace(OLD[k], b[k])
    h = h.replace(blob, IDS[b["key"]])
    h = re.sub(r"<title>.*?</title>", f"<title>{b['label']}</title>", h)
    # the watercolour paper is a warm off-white, so the name's knockout takes the paper's colour, not pure white
    h = h.replace("</helmet>", "<style>.cov-final .book-author .ko{background:#fdfcf8}</style>\n</helmet>", 1)
    open(f"{P}/{b['file']}.dc.html", "w").write(h)
print("ok")
