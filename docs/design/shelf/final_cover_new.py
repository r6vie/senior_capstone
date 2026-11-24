"""Covers: Strata page, the four new places (art/strata/covers_new.py): one cover board each, built from the desert
cover board (FinalCoverDesert) with the title, name, ink and art swapped. Cover only for now; the book screens come
later, to the right of each cover.

python3 final_cover_new.py <root> karst_xl=<blob> karst_sm=<blob> aurora_xl=... terraces_xl=... lagoon_xl=...
-> <root>/project/FinalCover{Karst,Aurora,Terraces,Lagoon}.dc.html"""
import sys
ROOT, IDS = sys.argv[1], dict(a.split("=") for a in sys.argv[2:])
P = f"{ROOT}/project"
src = open(f"{P}/FinalCoverDesert.dc.html").read()
import re
_imgs = re.findall(r'class="cover-art" src="/_blob/([0-9a-f]{32})"', src)    # the desert board's current art

OLD = dict(label="desert mesas at dusk", title="What the Desert Teaches", author="Lucía Hernández-Brooks",
           ink="#6a3525", xl=_imgs[0], sm=_imgs[-1])

COVERS = [
    dict(key="karst", file="FinalCoverKarst", label="karst river in mist", title="Two Years Upriver",
         author="Wen Zhao", ink="#2f4637"),
    dict(key="aurora", file="FinalCoverAurora", label="winter night, aurora", title="Long Nights, Clear Skies",
         author="Ingrid Solberg", ink="#252a4c"),
    dict(key="terraces", file="FinalCoverTerraces", label="rice terraces at dawn", title="The Patient Field",
         author="Dewi Santoso", ink="#3d5a32"),
    dict(key="lagoon", file="FinalCoverLagoon", label="volcanic lagoon", title="Island Time Isn’t Slow",
         author="Keoni Akana", ink="#1f4f5a"),
    dict(key="city", file="FinalCoverCity", label="lakefront city at dusk", title="Small Bets, Big City",
         author="Danielle Owens", ink="#2f3448"),
    dict(key="forest", file="FinalCoverForest", label="fir forest in morning light", title="Room to Grow",
         author="Noah Bergstrom", ink="#283d2e"),
]

for c in COVERS:
    if f'{c["key"]}_xl' not in IDS:
        continue
    # since 2026-11-21 the small (176 px) book shows the large render too, so the board may hold only the xl id
    assert src.count(OLD["xl"])
    h = (src.replace(OLD["label"], c["label"]).replace(OLD["title"], c["title"]).replace(OLD["author"], c["author"])
         .replace(OLD["ink"], c["ink"]).replace(OLD["xl"], IDS[f'{c["key"]}_xl'])
         .replace(OLD["sm"], IDS.get(f'{c["key"]}_sm', IDS[f'{c["key"]}_xl'])))
    open(f"{P}/{c['file']}.dc.html", "w").write(h)
print("ok")
