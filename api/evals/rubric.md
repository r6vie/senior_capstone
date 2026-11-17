# The editor's rubric

For a person judging a Trove book and the interview behind it. Judge it the way a sharp nonfiction editor
would: plain, specific, confident, curious, never hyped. The bar is the contents page of a good business or
science book. These are real professionals and students; a book that merely flatters them or sounds nice fails.

What the product is: every member of a university network is the author of a book they haven't written. An AI
interview finds what they know that others don't. The book is a title, a short back cover and 3-5 chapter
summaries. A reader who likes it books a 30-minute video call with the author. So each chapter is really a
conversation worth having. Everything in the book must trace to the member's own answers.

Score each 1-5. Use the whole scale; a 3 means "would ship, nobody would talk about it".

| # | Dimension | 1 | 3 | 5 |
|---|---|---|---|---|
| 1 | **Would a reader book 30 minutes?** | No reason to meet this person | A reader facing this exact thing might | I'd book it even if it's outside my field |
| 2 | **Specificity** | Could be anyone's | Some concrete details, some filler | Every line has a detail only this person could give |
| 3 | **Sounds like the author** | Generic LinkedIn or AI voice | Clean, but the author's voice comes and goes | I can hear the person; their odd phrases survive |
| 4 | **Distinct chapters** | One idea, renamed | Two chapters blur | Each is a different conversation I could choose between |
| 5 | **Title pull** | Generic or a label | Accurate, mild interest | I want to know what it means; the three options are truly different books |
| 6 | **Question sharpness** (the interview) | Generic, repeated, or leaves the best material on the table | Competent, a few doors missed | Each question follows the strongest word; the member says things they hadn't planned to |
| 7 | **No unsupported claims** | Invents outcomes, feelings or lessons | A few stretches beyond what was said | Everything traces to an answer |

Readers see only the back cover, the chapter titles and the summaries. The quotes are the author's alone. So judge dimensions 1, 3 and 5 from the reader's page (`python -m evals.saved reader`), and the rest from the full packet.

For each score, quote the line that most justifies it. Name:
- the single worst sentence in the book, and what's wrong with it;
- the best material in the transcript that didn't make it into the book;
- every **door left unopened**: an answer with something promising that the next question walked past (give the turn number and the words);
- every question you'd cut or change, and why, with your replacement;
- what you'd change first, as an editor, if you could only change one thing.

Be harsh, and be specific. Compliments don't help. Don't assume the system is doing well.
