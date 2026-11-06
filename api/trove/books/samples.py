"""Sample books for development, so other features can build before real books exist.

Every sample is invented: no real people. Samples carry `is_sample: True` and fixed ids, so seeding
is repeatable and `remove_samples` touches nothing else. Run them with `python3 scripts/seed.py`.
"""

from datetime import UTC, datetime, timedelta
from uuid import NAMESPACE_URL, uuid5

from pymongo.asynchronous.database import AsyncDatabase

from trove.books.models import DEFAULT_COPIES

# fmt: off
# (author_name, title, cover_style, blurb, [(chapter title, summary, grounding quote), ...])
SAMPLES = [
    ("Maya", "The Night Shift Knows", "cover-1", "What a hospital looks like from the people who keep it running at 3 a.m.", [
        ("Handoffs are where things break", "Most mistakes she has seen began in the five minutes between shifts, not in the work itself.", "Nobody gets hurt during the shift. They get hurt during the handoff."),
        ("Charge nurses run the hospital", "Who actually decides which bed a patient gets, and how to ask them nicely.", "The org chart says one thing. The charge nurse decides."),
        ("Learning to sleep in daylight", "The small routines that got her through two years of nights.", "Blackout curtains were the best money I ever spent."),
    ]),
    ("Dev", "Shipping Code Nobody Notices", "cover-2", "Infrastructure work, and why the best version of it is invisible.", [
        ("The outage that taught me logging", "A twelve-hour incident traced to one missing log line.", "We had every metric except the one that mattered."),
        ("Saying no to a rewrite", "How he argued a team out of starting over, and what they did instead.", "The rewrite is always six months. It is never six months."),
        ("On-call without burning out", "What a sane rotation looks like and how to ask for one.", "If you get paged twice a night, the system is the bug."),
    ]),
    ("Priya", "Lab Notebooks and Late Buses", "cover-3", "Undergraduate research from the first cold email to a first-author poster.", [
        ("The cold email that worked", "What she wrote to a professor she'd never met, and why she thinks it landed.", "I asked about one figure in their paper. Just one."),
        ("Failing experiments on schedule", "Planning a semester around the assumption that half of it won't work.", "I budget for failure now. It shows up on time."),
        ("Presenting to people smarter than you", "Getting through a poster session when a famous name walks up.", "You know your poster better than they do. That's the whole trick."),
    ]),
    ("Sam", "Small Town, Big Contracts", "cover-4", "Running the family construction business while finishing an engineering degree.", [
        ("Bidding on the first public job", "Everything the bid documents didn't say.", "The lowest bid wins, until it doesn't get finished."),
        ("Working for your father", "Where the line between family and business sits, and where it moved.", "At dinner he's Dad. On site he's the client."),
        ("What engineers get wrong about crews", "Why the drawings and the people building them disagree.", "The crew knows the drawing is wrong before you do."),
    ]),
    ("Lena", "Translating for My Parents", "cover-5", "Growing up as the family's interpreter, and how it became a career in health policy.", [
        ("Twelve years old at the doctor's office", "Interpreting a diagnosis she didn't understand herself.", "I knew the words. I didn't know what they meant for us."),
        ("Why forms are policy", "How the design of a single form decides who gets care.", "Every question on a form is a door or a wall."),
        ("Getting into public health from the side door", "The non-obvious route she took into her field.", "I didn't apply to public health. I kept showing up."),
    ]),
    ("Omar", "The Quiet Founder", "cover-6", "Building a company as an introvert, without pretending to be someone else.", [
        ("Pitching without performing", "A pitch style that relies on preparation instead of charisma.", "I can't work a room. I can answer every question."),
        ("Hiring your first five", "The mistakes he made with early hires and what he'd keep.", "The first five people decide what the next fifty are like."),
        ("Shutting down well", "Closing his first company with everyone still speaking to him.", "We ran out of money, not out of respect."),
        ("Starting again", "What changed the second time around.", "The second time I knew what I didn't know."),
    ]),
    ("Grace", "Teaching Kids Who Hate Math", "cover-7", "Eight years in middle-school classrooms, and what finally reaches the students who've given up.", [
        ("The first week decides the year", "What she does in the first five days and why.", "By Friday they've decided whether math is for them."),
        ("Wrong answers are data", "Reading mistakes as information instead of grading them.", "A wrong answer tells me exactly where to start."),
        ("Leaving teaching, and coming back", "Why she left for a tech job and what pulled her back.", "The money was better. The days were emptier."),
    ]),
    ("Theo", "Concerts in Empty Rooms", "cover-8", "A music performance major on practice, nerves and making a living from it.", [
        ("Practicing less, better", "The practice structure that replaced six hours a day.", "Six hours of practice was mostly six hours of habit."),
        ("Stage fright never left", "Playing well while still scared.", "I stopped waiting to stop being nervous."),
        ("The gig economy before it had a name", "Weddings, churches and teaching on the side.", "Every musician I know has four jobs."),
    ]),
    ("Ana", "Supply Chains Are People", "cover-1", "Inside the logistics of a large manufacturer, told through the phone calls that fix things.", [
        ("The spreadsheet that ran a factory", "A single file nobody was allowed to touch, and what happened when it broke.", "It had one owner, and she was on vacation."),
        ("Calling suppliers before you need them", "Relationships that saved a production line during a shortage.", "When parts ran out, the suppliers I'd called just to chat called me back first."),
        ("Why forecasts are always wrong", "Living with bad forecasts instead of chasing perfect ones.", "The forecast isn't wrong. It's a guess with decimals."),
    ]),
    ("Kofi", "From Pre-Med to Product", "cover-2", "Leaving the medical track and finding a place in health tech without a CS degree.", [
        ("Telling my parents", "The conversation he dreaded and how it actually went.", "They were less upset than I was."),
        ("Clinical knowledge is a skill", "Why knowing how clinics work beat knowing how to code.", "I was the only one in the room who'd seen a real chart."),
        ("Learning just enough SQL", "The technical skills he picked up on the job, and which ones mattered.", "I learned SQL to stop waiting for other people's queries."),
    ]),
    ("Hannah", "Arguing for a Living", "cover-3", "Moot court, a public defender's office, and what persuasion looks like when it counts.", [
        ("Preparing the other side's case", "Why she writes the opposing brief before her own.", "If I can't argue their side, I'm not ready to argue mine."),
        ("Clients who don't trust you", "Earning trust with people the system has failed.", "They've met a lot of lawyers. Mostly for five minutes."),
        ("Losing and going back the next day", "Handling losses in a job where most cases are hard.", "You grieve in the car. Then you go in."),
    ]),
    ("Jonah", "Weather Is a Business", "cover-4", "Atmospheric science outside academia: forecasting for farms, airlines and insurers.", [
        ("Who pays for a forecast", "The surprising customers of private weather companies.", "Our best customer sells ice cream."),
        ("Being wrong in public", "How forecasters talk about uncertainty and still get blamed.", "Thirty percent chance of rain means it rains three times out of ten. People hear 'no'."),
        ("Coding your way into meteorology", "Why programming became the job's core skill.", "I write more Python than I look at clouds."),
    ]),
    ("Rosa", "The Second Language Classroom", "cover-5", "Teaching English to adults who arrived with careers already behind them.", [
        ("Students who were surgeons", "Teaching people whose expertise the language barrier hides.", "One student had been a surgeon. Here she was 'beginner level'."),
        ("Grammar is the least of it", "What new arrivals actually need from a language class.", "They need the words for the landlord, not the subjunctive."),
        ("Building a program on no budget", "Volunteers, borrowed rooms and grant writing.", "Every room we used was someone's favor."),
    ]),
    ("Eli", "Designing for the Back Office", "cover-6", "UX design for internal tools: unglamorous software that thousands of people use all day.", [
        ("Watching people work", "Why he sits beside users for a day before designing anything.", "Nobody tells you about the sticky notes on the monitor."),
        ("Saving ten seconds, ten thousand times", "The math that makes small improvements worth fighting for.", "Ten seconds times ten thousand clicks is a full-time job."),
        ("Convincing engineers", "Getting design work prioritized on teams without designers.", "I bring a video of a user struggling. That ends the debate."),
    ]),
    ("Nadia", "Running Toward the Fire", "cover-7", "Emergency management, from campus drills to real evacuations.", [
        ("Plans nobody reads", "Why emergency plans fail, and the one-page version that works.", "A 90-page plan is a plan to read a plan."),
        ("Drills people take seriously", "Making practice feel real enough to matter.", "If the drill is boring, the real thing will be chaos."),
        ("The first big one", "Her first real evacuation, and what she'd do differently.", "Everything we practiced worked. Everything we didn't, didn't."),
    ]),
    ("Chris", "Coaching the Bench", "cover-8", "Assistant coaching in college athletics, and developing players who rarely play.", [
        ("The players who don't start", "Keeping a full roster motivated when most won't get minutes.", "The bench decides the culture more than the starters."),
        ("Recruiting honestly", "What he tells recruits that other coaches won't.", "I tell them exactly how many minutes they'll probably get."),
        ("Film study for everything", "Applying game-film habits to life outside sport.", "I review a bad meeting the way I'd review a bad game."),
    ]),
    ("Ines", "Money for Nonprofits", "cover-1", "Grant writing and fundraising, and the gap between mission and money.", [
        ("Writing for the reviewer", "How a grant reviewer actually reads an application.", "They read forty of these. Make page one do the work."),
        ("Donors want a story, not a chart", "Telling impact without exaggerating it.", "One person's story raised more than our whole annual report."),
        ("Saying no to money", "When a gift costs more than it gives.", "Some grants come with a second job attached."),
    ]),
    ("Ben", "The Accidental Data Scientist", "cover-2", "A physics degree, a failed startup and a career in data that nobody planned.", [
        ("Physics trains you for messy data", "Why lab instincts transferred better than any course.", "In physics you assume the data lies until it proves otherwise."),
        ("The model nobody used", "A technically great model that changed nothing, and why.", "It was accurate. It was also a PDF nobody opened."),
        ("Asking the dumb question", "Getting comfortable asking what a business metric really means.", "Half my job is asking 'what do we mean by customer?'"),
    ]),
    ("Leah", "Growing Food in the City", "cover-3", "Urban farming in Cleveland: vacant lots, neighbors and the economics of lettuce.", [
        ("Starting on a vacant lot", "Soil tests, permits and the neighbor who helped most.", "The soil test came back bad. So we built up, not down."),
        ("Lettuce pays, tomatoes don't", "Which crops make money at small scale.", "Everyone wants to grow tomatoes. Restaurants buy greens."),
        ("Community before customers", "Why the farm's neighbors matter more than its sales.", "The fence is for deer, not for neighbors."),
    ]),
    ("Marcus", "Fixing Old Buildings", "cover-4", "Historic preservation, building codes, and making century-old buildings usable again.", [
        ("Reading a building's history", "What walls, nails and paint layers reveal about a building.", "Every layer of paint is a decade you can date."),
        ("Codes versus character", "Meeting modern safety codes without destroying what makes a building worth saving.", "The fire code and the original stairs both have a point."),
        ("Selling preservation to developers", "The financial case that gets old buildings saved.", "I lead with the tax credit, not the cornices."),
    ]),
]
# fmt: on


def sample_id(index: int) -> str:
    return str(uuid5(NAMESPACE_URL, f"trove-sample-book-{index}"))


def sample_documents(now: datetime) -> list[dict]:
    """Every sample as a `books` document. Shelf order follows SAMPLES, first is newest."""
    documents = []
    for index, (author_name, title, cover_style, blurb, chapters) in enumerate(SAMPLES):
        book_id = sample_id(index)
        documents.append(
            {
                "_id": book_id,
                "author_id": f"sample-author-{index + 1}",
                "author_name": author_name,
                "title": title,
                "cover_style": cover_style,
                "blurb": blurb,
                "chapters": [
                    {
                        "id": f"{book_id}-{number}",
                        "title": chapter_title,
                        "summary": summary,
                        "quotes": [quote],
                    }
                    for number, (chapter_title, summary, quote) in enumerate(chapters, start=1)
                ],
                "copies": DEFAULT_COPIES,
                "status": "on_shelf",
                "is_sample": True,
                "published_at": now - timedelta(hours=index),
                "created_at": now - timedelta(hours=index),
                "updated_at": now,
            }
        )
    return documents


async def seed_samples(database: AsyncDatabase) -> int:
    """Add or refresh every sample book. Running it again updates them instead of duplicating."""
    for document in sample_documents(datetime.now(UTC)):
        # Keep the original dates on reruns, so the shelf order doesn't jump around.
        dates = {key: document.pop(key) for key in ("published_at", "created_at")}
        book_id = document.pop("_id")
        await database.books.update_one(
            {"_id": book_id}, {"$set": document, "$setOnInsert": dates}, upsert=True
        )
    return len(SAMPLES)


async def remove_samples(database: AsyncDatabase) -> int:
    result = await database.books.delete_many({"is_sample": True})
    return result.deleted_count
