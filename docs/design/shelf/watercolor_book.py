"""Covers: Watercolor page: one book screen per abstract watercolour cover, set to the right of its cover, built
exactly like the strata book screens (final_book_more.py): the book opened on its title page with that cover's page
art (art/watercolor/pages.py) and the book's dark ink. The text sits on the page's paper, so the ink is always the
dark one, never the cream a dark cover top takes. Sample books only: the titles and names match the cover boards.

python3 watercolor_book.py <root> mesa_title=<blob> hills_title=<blob> lake_title=<blob> winter_title=<blob>
-> <root>/project/WCBook{Mesa,Hills,Lake,Winter}.dc.html"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv, _args = sys.argv[:2], sys.argv
import final_book_more as fb                       # reuse its template slicing; it writes nothing without blobs
sys.argv = _args
import re

ROOT, IDS = sys.argv[1], dict(a.split("=") for a in sys.argv[2:])
P = f"{ROOT}/project"

BOOKS = [
    dict(key="mesa", file="WCBookMesa", label="Watercolor · desert butte at dusk", title="The High Desert",
         author="Lucia Navarro", ink="#3a2c3a",
         blurb="Four years as a backcountry ranger in canyon country. How a remote district is really run, what heat "
               "and distance do to every plan, and what a slow, enormous landscape taught me about my own work.",
         ch=[("Distance is the first rule", "Every patrol, rescue and day off starts from how far everything is."),
             ("Plan for the day that goes wrong", "The checklist she wishes she'd carried in her first summer."),
             ("Talking to visitors", "How to say no kindly, and when a warning actually lands."),
             ("Learning to stay", "Why she kept signing on for one more season.")]),
    dict(key="hills", file="WCBookHills", label="Watercolor · patchwork hills", title="Slow Harvest",
         author="Tomas Rinaldi", ink="#4a4a2e",
         blurb="I took over my grandfather's vineyard with an engineering degree and no idea how to farm. What the "
               "old growers knew that my models didn't, pricing honestly, and building a business on a slow crop.",
         ch=[("The first harvest, mostly wrong", "What he measured, what he missed, and the frost nobody forecast."),
             ("Listening to the old growers", "Why the neighbours' rules of thumb kept beating his spreadsheets."),
             ("Selling to people, not distributors", "How the farm table outgrew the wholesale contract."),
             ("Patience as a strategy", "Planting vines he won't harvest for five years.")]),
    dict(key="lake", file="WCBookLake", label="Watercolor · alpine lake", title="Above the Tree Line",
         author="Ingrid Solberg", ink="#23415a",
         blurb="Six summers running a mountain hut above a glacier lake. How a tiny team keeps a remote place going, "
               "what weather does to every plan, and why guests listen to the mountain before they listen to you.",
         ch=[("Opening the hut", "Digging out, hauling in, and the first week before anyone arrives."),
             ("Weather decides", "Reading the sky, and the calls she made to turn people back."),
             ("Four people, sixty guests", "Running a kitchen, a rescue radio and a schedule at altitude."),
             ("Closing for winter", "What gets left ready, and what she takes home each year.")]),
    dict(key="winter", file="WCBookWinter", label="Watercolor · winter dusk", title="First Snow",
         author="Hannah Lindqvist", ink="#3e2b45",
         blurb="Three winters teaching in a small northern town. How to plan when the weather cancels the plan, "
               "teaching kids who know the snow better than you do, and what a long dark season does for a community.",
         ch=[("Arriving before the snow", "The first month, the first storm, and the boots she should have bought."),
             ("Snow days", "Lessons that work when half the class can't make it in."),
             ("The town in the dark", "How the long nights brought people together, not apart."),
             ("The spring she left", "Handing over a classroom, and what she still carries from it.")]),
]

W, H = 1440, 1090
for b in BOOKS:
    if f'{b["key"]}_title' not in IDS:
        continue
    fb.IDS = IDS
    board = (f'<div style="width:{W}px;height:{H}px;background:var(--paper);color:var(--ink);font-family:var(--font-sans);'
             f'overflow:hidden"><div style="position:relative;height:100%"><span class="frame-label" '
             f'style="position:absolute;left:44px;top:56px">Book screen · {b["label"]}</span>'
             f'<div style="position:absolute;left:0;top:100px">{fb.swap(fb.opened, b)}</div></div></div>\n')
    h = re.sub(r"<title>.*?</title>", f"<title>Book screen · {b['label']}</title>", fb.head)
    t = fb.tail.replace('"width":1440,"height":2020', f'"width":{W},"height":{H}')
    open(f"{P}/{b['file']}.dc.html", "w").write(h + board + t)
print("ok")
