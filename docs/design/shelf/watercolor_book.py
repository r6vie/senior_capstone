"""Covers: Watercolor page: one book screen per abstract watercolour cover, set to the right of its cover, built
exactly like the strata book screens (final_book_more.py): the book opened on its title page with that cover's page
art (art/watercolor/pages.py) and the book's dark ink. The text sits on the page's paper, so the ink is always the
dark one, never the cream a dark cover top takes. Sample books only: the titles and names match the cover boards.

python3 watercolor_book.py <root> mesa_title=<blob> hills_title=<blob> lake_title=<blob> winter_title=<blob>
  city_title=<blob> blossom_title=<blob> autumn_title=<blob> beach_title=<blob> lighthouse_title=<blob>
-> <root>/project/WCBook{Mesa,Hills,Lake,Winter,City,Blossom,Autumn,Beach,Lighthouse}.dc.html"""
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
    # the second set (Josef, 2026-11-23: "do the book screens for blossom, city and autumn"; art/watercolor/pages2.py)
    dict(key="city", file="WCBookCity", label="Watercolor · city at night on the river", title="After Hours",
         author="Marcus Bell", ink="#2c2d52",
         blurb="Five years running the overnight desk at a city newsroom. What happens between midnight and the "
               "morning edition, how to make a call with half the facts, and keeping a team awake and kind.",
         ch=[("The handover at midnight", "What the day desk leaves behind, and the three questions he always asks."),
             ("Deciding with half the facts", "When to publish, when to wait, and how to say which you chose."),
             ("A small team at 3 a.m.", "Keeping four tired people sharp, honest and on speaking terms."),
             ("Going back to days", "What the night taught him that daylight work forgot.")]),
    dict(key="blossom", file="WCBookBlossom", label="Watercolor · blossom tree by a pond", title="Second Spring",
         author="Aiko Tanaka", ink="#5a3048",
         blurb="I left a career in finance at forty to train as a landscape gardener. What starting over really "
               "costs, learning from people half my age, and building a small practice one garden at a time.",
         ch=[("The year I quit", "The numbers she ran, the ones she ignored, and the conversation at home."),
             ("Apprentice again", "Taking instruction at forty, and what experience is still worth."),
             ("The first paying garden", "Pricing, a nervous client, and the plan that changed halfway."),
             ("Growing slowly on purpose", "Why she still turns down more work than she takes.")]),
    dict(key="autumn", file="WCBookAutumn", label="Watercolor · autumn river with a bridge", title="The Long Way Home",
         author="Emmett Clarke", ink="#5a3420",
         blurb="After ten years in cities I moved back to the small town I grew up in to run the family hardware "
               "store. What changed, what didn't, and how a shop on a quiet street keeps a community going.",
         ch=[("Coming back", "Why he said yes, and the first month of being someone's son again."),
             ("The store as a crossroads", "How a hardware counter became where the town talks."),
             ("Competing with the big box", "What a small shop can do that a warehouse can't."),
             ("Staying", "Planning for the next ten years in a place that changes slowly.")]),
    dict(key="beach", file="WCBookBeach", label="Watercolor · beach at sunset", title="Off the Clock",
         author="Leilani Cruz", ink="#5a2f2a",
         blurb="I burned out at a startup and spent a year running a small surf school instead. What rest actually "
               "takes, teaching beginners to wait for the right wave, and how I came back to work differently.",
         ch=[("The week I stopped", "The signs she ignored, and the conversation that finally made her leave."),
             ("Running a surf school", "Bookings, weather, insurance and a team of four, on very little money."),
             ("Waiting for the wave", "What teaching beginners taught her about pace and patience."),
             ("Going back", "The rules she set for her next job, and the ones she has kept.")]),
    dict(key="lighthouse", file="WCBookLighthouse", label="Watercolor · lighthouse by day with the harbor boats",
         title="Keeping the Light", author="Maren Holt", ink="#2c3e5c",
         blurb="Eight years restoring and running a lighthouse museum on a small island. Raising money for an old "
               "building, keeping volunteers for years, and telling a place's story to people who come by boat.",
         ch=[("Inheriting a ruin", "The survey, the leaking lantern, and the first grant she almost missed."),
             ("Volunteers who stay", "How a crew of retirees and students kept coming back every summer."),
             ("The ferry schedule decides", "Planning everything around the boats and the weather."),
             ("Telling the story", "What visitors remember, and what she cut from the tour.")]),
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
