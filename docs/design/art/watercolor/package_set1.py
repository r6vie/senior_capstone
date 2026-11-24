"""Package watercolour set 1 for the app (Josef, 2026-11-23: the ten watercolour books that have book screens go to
UI implementation, in their own "watercolor" category beside "strata").

python3 package_set1.py -> set-1/covers/<key>.webp, set-1/pages/<key>.webp, set-1/manifest.json, set-1/contact-sheet.png

Covers are the 944 x 1376 renders scaled to 472 x 688 (the 236 x 344 cover at 2x, as strata set 1); pages are the
1140 x 1368 renders as they are. Re-render first (covers.py, lighthouse_boats.py, abstract.py, abstract2.py,
pages.py, pages2.py); every render is seeded, so it matches the canvas."""
import json
import os
import sys
from PIL import Image

sys.path.insert(0, ".")
from ink import ink_for

OUT = "set-1"
# key, name, cover render, page render, the book's own dark ink (the cover's title takes cream or this, by the paint)
ARTS = [
    ("mesa", "Desert butte at dusk", "mesa-xl", "page-mesa", "#3a2c3a"),
    ("hills", "Patchwork hills", "hills-xl", "page-hills", "#4a4a2e"),
    ("lake", "Alpine lake", "lake-xl", "page-lake", "#23415a"),
    ("winter", "Winter dusk with firs", "winter-xl", "page-winter", "#3e2b45"),
    ("city", "City at night on the river", "city-xl", "page-city", "#2c2d52"),
    ("blossom", "Blossom tree by a pond", "blossom-xl", "page-blossom", "#5a3048"),
    ("autumn", "Autumn river with a bridge", "autumn-xl", "page-autumn", "#5a3420"),
    ("beach", "Beach at sunset", "beach-xl", "page-beach", "#5a2f2a"),
    ("lighthouse-day", "Lighthouse by day with the harbor boats", "lighthouse-boats-xl", "page-lighthouse", "#2c3e5c"),
    ("lighthouse-dusk", "Lighthouse at dusk with its beam", "lighthouse-xl", "page-lighthouse-dusk", "#2c3e5c"),
]

os.makedirs(f"{OUT}/covers", exist_ok=True)
os.makedirs(f"{OUT}/pages", exist_ok=True)
arts, sheet_c, sheet_p = [], [], []
for key, name, cov, page, dark in ARTS:
    c = Image.open(f"out/{cov}.png").convert("RGB")
    assert c.size == (944, 1376), (cov, c.size)
    c = c.resize((472, 688), Image.LANCZOS)
    c.save(f"{OUT}/covers/{key}.webp", quality=90, method=6)
    p = Image.open(f"out/{page}.png").convert("RGB")
    assert p.size == (1140, 1368), (page, p.size)
    p.save(f"{OUT}/pages/{key}.webp", quality=90, method=6)
    ink, _lum, contrast = ink_for(f"out/{cov}.png", dark)
    arts.append(dict(key=key, name=name, coverInk=ink, pageInk=dark, coverInkContrast=round(float(contrast), 2),
                     cover=f"covers/{key}.webp", page=f"pages/{key}.webp"))
    sheet_c.append(c.resize((236, 344)))
    sheet_p.append(p.resize((236, 283)))

json.dump(dict(set="watercolor-1", category="watercolor", approved="2026-11-23", approvedBy="Josef",
               cover=dict(file="472x688 webp, the 236x344 cover world at 2x, painted edge to edge",
                          shelfBook="176x257 CSS px", largeBook="236x344 CSS px"),
               page=dict(file="1140x1368 webp, the 570x684 title page at 2x",
                         fills="the left (title) page of the opened book, behind the text"),
               arts=arts), open(f"{OUT}/manifest.json", "w"), indent=2)
sheet = Image.new("RGB", (10 * 246 + 10, 344 + 283 + 30), "white")
for i, (c, p) in enumerate(zip(sheet_c, sheet_p)):
    sheet.paste(c, (10 + i * 246, 10))
    sheet.paste(p, (10 + i * 246, 364))
sheet.save(f"{OUT}/contact-sheet.png")
for a in arts:
    print(a["key"], a["coverInk"], a["coverInkContrast"])
