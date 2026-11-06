# The shelf page

Canvas: https://claude.ai/artifact/33uQU8UKZ4gtxcv4ZNof1D (private until shared).
`project/` holds the canvas exactly as published: one `.dc.html` file per artboard plus `canvas.json`.

| Artboard | What it shows |
|---|---|
| `Main.dc.html` | The desktop shelf, fluid and interactive: click a book to open its preview under the shelf; "Not for me" cycles the Librarian's pick |
| `PhoneShelf.dc.html` | The same page at 390px with a bottom tab bar |
| `PhoneBook.dc.html` | A book opened from the shelf on a phone, as a bottom sheet |
| `BookObject.dc.html` | The book object: states, cover templates, cloth colors, and notes for the 3D build |

### Direction 2: light and shadow (second row)

| Artboard | What it shows |
|---|---|
| `ShadowShelf.dc.html` | The desktop shelf, fluid and interactive. Books stand in niches cut into the wall; click one and it pulls forward while its chapters open on a sheet laid over the wall. "Suggest another" cycles the Librarian's pick |
| `ShadowPhone.dc.html` | The same page at 390px |
| `ShadowSystem.dc.html` | The six depths and what each means, the light, the rules, color and type |

Warm whites only, one light from the upper left, Jost for everything and Libre Caslon italic for
the Librarian's voice. Book covers are white boards with a title pressed in and one printed
geometric shape (the only color), assigned by Trove. The Librarian's pick stands in a patch of
window light. The tells this direction avoids are listed in `docs/design/ai-tells.md`.

## How the page works for the member (direction 1)

1. **Search by topic** first, with a few suggested topics. Never by name.
2. **The Librarian recommends** one book with the reason; "Not for me" asks for another.
3. **Shelves** of six books stand on oak ledges; shelf names are placeholders.
4. **Click a book** and it lifts off the shelf; a preview opens under that shelf with the chapters
   ("What you could talk about") and **Ask to check out**, plus what a checkout means.

## The look

Warm paper, oak shelving, cloth-bound books with foil titles, and a green reading-lamp corner for
the Librarian. Newsreader (serif) for titles and headings, Instrument Sans for the interface.
Cloth color and cover template are assigned by Trove, so no book can be louder than another.
