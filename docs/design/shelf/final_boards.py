"""Final designs page: the evolved strata cover and book screen B with its art. Built from the Fresh boards."""
import sys, re
ROOT, IDS = sys.argv[1], dict(a.split("=") for a in sys.argv[2:])
P = f"{ROOT}/project"
c = open(f"{P}/FreshStrata.dc.html").read()
c = c.replace("/_blob/ae3f9e8e460ccc6deee4a4dfa0621a5a", f"/_blob/{IDS['coverxl']}").replace("/_blob/6207834eb207b12eb62aa34a93a8b5bc", f"/_blob/{IDS['coversm']}")
c = re.sub(r"<title>.*?</title>", "<title>Final: the strata cover</title>", c)
c = c.replace("9 · Strata, round 3", "Strata · the cover")
c = re.sub(r'<div style="display: flex; flex-direction: column; gap: 10px">.*?</div></div>\n</div>',
           '</div>\n</div>', c, flags=re.S)
open(f"{P}/FinalCover.dc.html", "w").write(c)
b = open(f"{P}/FreshReaderOpen.dc.html").read()
b = b.replace("/_blob/ede1dc6f6fa9f61603504ed3344e31b4", f"/_blob/{IDS['title']}").replace("/_blob/ed2bfb959d58c167e78b4ec053a02f42", f"/_blob/{IDS['contents']}")
b = re.sub(r"<title>.*?</title>", "<title>Final: book screen B</title>", b)
b = b.replace('<span class="frame-label">B · The book opens</span>', '<span class="frame-label">Book screen · the book opens, with strata</span>')
b = re.sub(r'<p class="note">Book screen B ·.*?</p>', '<p class="note">Strata, finished: calm slabs on paper seams, one muted family of inks, one hero peak with the sun set against it, planes stepping back into haze, firs built tier by tier.</p>', b, flags=re.S)
# the two-screen book board is now only the template for final_book_more.py, which builds one screen per cover
import os
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "book_template.dc.html"), "w").write(b)
print("ok", IDS)
