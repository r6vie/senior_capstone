"""Final designs: book screen B for the desert, coast and autumn-hills covers, each book opened on its title page with
its own page art (art/strata/pages_more.py) and its cover's ink on the boards. Built from FinalBook.dc.html.

python3 final_book_more.py <root> desert_title=<blob> coast_title=<blob> valley_title=<blob>"""
import sys, re
ROOT, IDS = sys.argv[1], dict(a.split("=") for a in sys.argv[2:])
P = f"{ROOT}/project"
src = open(f"{P}/FinalBook.dc.html").read()

A = '<div style="position:absolute;left:0;top:190px">'
B = '<div style="position:absolute;left:0;top:1120px">'
head, rest = src.split('<div style="width:1440px;height:2020px', 1)
rest = '<div style="width:1440px;height:2020px' + rest
opened = rest[rest.index(A) + len(A):rest.index(B)]
opened = opened[:opened.rindex("</div>")]                      # drop the screen wrapper's close
chapter_end = rest.index("</x-dc>")
chapter = rest[rest.index(B) + len(B):chapter_end].rstrip()
chapter = chapter[:-len("</div></div></div>")]                 # the screen wrapper and the board's two
tail = rest[chapter_end:]

OLD = dict(
    title="The Night Shift Knows", author="Maya Okafor",
    blurb="I've worked nights on a surgical ward for two years. This is the hospital the day shift never sees: who "
          "really runs it at 3 a.m., where things go wrong, and how to stay human on the wrong side of the clock.",
    ch=[("Handoffs are where things break",
         "Most mistakes she has seen began in the five minutes between shifts, not in the work itself."),
        ("Charge nurses run the hospital", "Who actually decides which bed a patient gets, and how to ask them nicely."),
        ("When to wake the doctor",
         "The judgement call every night nurse makes alone, and how she learned to trust it."),
        ("Learning to sleep in daylight", "The small routines that got her through two years of nights.")],
    ink="#16302e", title_blob="0046504bae491ceb0e810043d50e0bc2", contents_blob="9c8f634e9fa9f9bc15fee086a2a9a03a")

BOOKS = [
    dict(key="desert", label="Desert mesas at dusk", title="What the Desert Teaches", author="Lucía Hernández-Brooks",
         ink="#6a3525",
         blurb="Three field seasons surveying desert springs for the park service: how the work is really planned, "
               "what heat and distance do to a schedule, and what a slow landscape taught me about patience.",
         ch=[("Water decides everything", "Every route, camp and day's work starts from where the springs are."),
             ("Plan for the day that goes wrong", "The checklist she wishes she'd had in her first season."),
             ("Working alone, safely", "Radios, check-in times, and knowing when to turn back."),
             ("Reading a landscape slowly", "What you only notice on the third visit to the same place.")]),
    dict(key="coast", label="Sea cliffs by moonlight", title="Notes From the Edge", author="Callum O’Donnell",
         ink="#26304f",
         blurb="Five years designing sea defences on a coast that loses a metre a year. What engineering school "
               "leaves out, how decisions get made with a town watching, and when the honest answer is to retreat.",
         ch=[("The sea always wins eventually", "Designing for fifty years when the cliff has other plans."),
             ("Public meetings", "How to explain a hard trade-off to the people who live on the cliff."),
             ("Models and mud", "Where the computer model ends and a site visit begins."),
             ("Managed retreat", "The project he is proudest of, which built almost nothing.")]),
    dict(key="valley", label="Autumn hills", title="A Slow Harvest", author="Mei Lin Okada", ink="#263a2d",
         blurb="I left consulting to run my family's orchard. A season-by-season account of learning a business "
               "that answers to weather, of pricing apples honestly, and of what spreadsheets can't tell you.",
         ch=[("The first bad frost", "What a single cold night in April did to a whole year's plan."),
             ("Selling to people, not markets", "How the farm stand outgrew the wholesale contract."),
             ("Hiring for the harvest", "Finding, keeping and paying a seasonal crew fairly."),
             ("What consulting got right", "The habits from her old job that still earn their keep.")]),
]


def swap(html, b):
    html = html.replace(OLD["title"], b["title"]).replace(OLD["author"], b["author"]).replace(OLD["blurb"], b["blurb"])
    for (ot, ob), (nt, nb) in zip(OLD["ch"], b["ch"]):
        html = html.replace(ot, nt).replace(ob, nb)
    html = html.replace(f'fill="{OLD["ink"]}"', f'fill="{b["ink"]}"')
    html = html.replace(OLD["title_blob"], IDS[f'{b["key"]}_title'])
    return html


TOP, COL = 190, 1520
rows = [f'<div style="position:absolute;left:{c * COL}px;top:{TOP}px">{swap(opened, b)}</div>'
        .replace('Opened: title page and contents</span>', f'{b["label"]}</span>') for c, b in enumerate(BOOKS)]
W, H = 3 * COL - 80, TOP + 920
board = (f'<div style="width:{W}px;height:{H}px;background:var(--paper);color:var(--ink);font-family:var(--font-sans);'
         f'overflow:hidden"><div style="position:relative;height:100%"><div class="board-head"><span class="frame-label">'
         f'Book screen · the pages follow the cover</span><p class="note">Each cover\'s place opened up into a full scene on '
         f'the title page, the cover\'s ink on the boards.</p></div>{"".join(rows)}</div></div>\n')
head = re.sub(r"<title>.*?</title>", "<title>Final: book pages for each cover</title>", head)
tail = tail.replace('"width":1440,"height":2020', f'"width":{W},"height":{H}')
open(f"{P}/FinalBookMore.dc.html", "w").write(head + board + tail)
print("ok", W, H)
