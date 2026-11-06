# Shelf page: three design directions (T1)

Review page: https://claude.ai/artifact/BnDvoYhnXb7BJx84iouvTc (private to Josef until shared).
Static HTML and CSS only. All books, names and shelf labels are samples; shelf categories are
placeholders until they're decided (docs/trove.md §5).

## Files

- `index.html`: the review page. Generated: edit `build.py`, then run
  `python3 docs/design/shelf-directions/build.py`.
- `build.py`: the sample books and each direction's markup, one section per direction.
- `base.css`: the review document only. The directions don't use it.
- `direction-a.css`, `direction-b.css`, `direction-c.css`: one self-contained stylesheet per
  direction, scoped to `.da`, `.db` and `.dc`. To iterate on one direction, take its CSS file and its
  section of `build.py`.

## The feeling

**Curious, unhurried, among equals.** An afternoon in the stacks with nothing assigned, pulling out a
book because its title made you wonder. Nobody is watching, nothing is ranked, and the author is a
person you could go and talk to.

It must never feel like LinkedIn (polish, titles, counts), a dating app (faces, swiping), a recruiting
tool (filters, candidates), a feed (endless, newest first), or a themed bookshop (fake wood, quaint).

## Principles

1. **The title is the face.** Lead with the title. The first name is small. No photos.
2. **Every book gets the same frame.** Same size, same type, color assigned by Trove.
3. **A visit can end.** Finite shelves, no infinite scroll, no "new" or "trending".
4. **Library as structure, not costume.** Borrow how a library works; skip the wood grain.
5. **One voice recommends.** Only the Librarian suggests, always with a reason.

## The directions

- **A, Face Out.** Books stand face out on a ledge, like a library's display shelf. Typographic cloth
  covers (Young Serif titles, Commissioner UI) in eight muted colors assigned by Trove, on a
  reading-room green-grey. Best: memorable, books feel present and equal. Worst: low density; long
  titles get small; authors may want to pick their color.
- **B, Catalog Card.** Each book is a ruled 3x5 catalog card with a red heading line and a rod hole,
  filed in labelled drawers. Newsreader titles, Courier Prime typed labels, cool card stock and ink
  blue. Best: the most literary and the most equal. Worst: can feel archival and cold; less pull to
  return.
- **C, The Stack.** Books lie flat in piles, spine out, titles read left to right. Narrow Archivo on
  dusky spines over a deep blue "reading lamp" ground (dark-first). Best: densest, fastest to scan,
  best on phones. Worst: night-app mood; spines carry less personality; a pile can look ranked.

## Recommendation

Build **A, Face Out**, and use C's spine as the list form for search results, "See the whole shelf"
and long lists on phones.

## Open questions for Josef

1. Show student or alum on a book? None of the designs do (docs/trove.md §3). Recommend: not on the shelf.
2. Who picks a cover color? Recommend: Trove assigns it.
3. Shelf order? Recommend: fresh each visit, with the Librarian favoring books that get fewer requests.
4. Dark mode at launch? Recommend: pick the direction first, then design its other theme.
