"""Covers: Strata page, the four new places (art/strata/covers_new.py): one cover board each, built from the desert
cover board (FinalCoverDesert) with the title, name, ink and art swapped. Cover only for now; the book screens come
later, to the right of each cover.

python3 final_cover_new.py <root> karst_xl=<blob> karst_sm=<blob> aurora_xl=... terraces_xl=... lagoon_xl=...
-> <root>/project/FinalCover{Karst,Aurora,Terraces,Lagoon}.dc.html"""
import sys
ROOT, IDS = sys.argv[1], dict(a.split("=") for a in sys.argv[2:])
P = f"{ROOT}/project"
src = open(f"{P}/FinalCoverDesert.dc.html").read()

OLD = dict(label="desert mesas at dusk", title="What the Desert Teaches", author="Lucía Hernández-Brooks",
           ink="#6a3525", xl="19f6a580046781ab16fceb62df36ba82", sm="4ebc99796f0522a5c2f38111689aca0d")

COVERS = [
    dict(key="karst", file="FinalCoverKarst", label="karst river in mist", title="Two Years Upriver",
         author="Wen Zhao", ink="#2f4637"),
    dict(key="aurora", file="FinalCoverAurora", label="winter night, aurora", title="Long Nights, Clear Skies",
         author="Ingrid Solberg", ink="#252a4c"),
    dict(key="terraces", file="FinalCoverTerraces", label="rice terraces at dawn", title="The Patient Field",
         author="Dewi Santoso", ink="#3d5a32"),
    dict(key="lagoon", file="FinalCoverLagoon", label="volcanic lagoon", title="Island Time Isn’t Slow",
         author="Keoni Akana", ink="#1f4f5a"),
]

for c in COVERS:
    assert src.count(OLD["xl"]) and src.count(OLD["sm"])
    h = (src.replace(OLD["label"], c["label"]).replace(OLD["title"], c["title"]).replace(OLD["author"], c["author"])
         .replace(OLD["ink"], c["ink"]).replace(OLD["xl"], IDS[f'{c["key"]}_xl'])
         .replace(OLD["sm"], IDS[f'{c["key"]}_sm']))
    open(f"{P}/{c['file']}.dc.html", "w").write(h)
print("ok")
