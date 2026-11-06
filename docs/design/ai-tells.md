# Tells of AI-made UI: what Trove's designs avoid

The chosen look and its rules are in [system.md](system.md); this file is the check against defaults.

Collected 2026-11-05 from design writing on "AI slop" (sources at the end). Most sources are blogs
and tool vendors, so treat this as a strong guide, not law. Every item is fine as a deliberate,
reasoned choice; it becomes a tell when it's a default. The test, from pixelslop: **did a person
make this choice, or did the tool fall back to a default?**

Basic elements (buttons, fields, lists, a card where something really is a separate object) are
still allowed. What's ruled out is the reflex.

## Typography
- One generic face for everything (Inter, Roboto, Arial, Open Sans, system-ui) with no display face.
- Monospace on labels or headings that aren't code, for a "tech" feel.
- Gradient text on headlines or numbers.
- One word in a headline picked out in italic, bold or color.
- A tracked all-caps eyebrow over every heading.
- 01 / 02 / 03 numbering on things that aren't a sequence; labels that repeat the heading.
- Round, default type scales (12/14/16/18/24/30/36/48) instead of a chosen ratio.

## Color
- Purple-to-blue or indigo gradients; Tailwind's indigo-500 as the accent.
- Near-black with neon or a single acid accent; cyan on black.
- Pure #000 or #fff grounds.
- **The second wave:** cream (about #F4F1EA) with terracotta or clay (about #D97757). Swapping
  purple for this just moves to the next default. (Trove's direction 1 sat close to it.)
- A different accent for every card or tab; status dots on everything.
- Grey secondary text on colored or dark grounds.

## Layout
- Centered hero, pill badge, two buttons, logo row, three feature cards, CTA.
- Three identical rounded cards in a row with a thin-line icon on top.
- Everything centered; the same 24 or 32px gap everywhere, with no rhythm.
- Big hero metrics with a row of supporting stats.
- Heading, paragraph, button repeated section after section.
- "Broadsheet cosplay": hairline rules, zero radius and dense columns on content that isn't editorial.

## Components
- Every container a card; cards inside cards.
- The same radius (8-20px) and the same soft shadow on every card.
- An icon in a colored circle above every heading.
- Every button the same weight, with no primary and secondary.
- Emoji as icons; generic line icons that could belong to any product.
- An arrow glyph welded onto every link.
- Modals for tasks that could happen in place.
- A thick colored border down one side of a card.
- Decorative sparklines that show no data.

## Depth, shadow and effects (most relevant to the shadow direction)
- **One identical shadow on everything** (`rgba(0,0,0,.1)`, `shadow-md`). Elevation that doesn't
  follow hierarchy.
- Soft shadows on every container just to separate it.
- Glassmorphism: blurred translucent panels, frosted layers, glow borders.
- Colored glows and halos around cards or buttons; aurora or radial glow behind the hero.
- Decorative gradient washes on cards.

## Motion
- Bounce or elastic easing.
- The same fade-and-slide-up on every section; count-up numbers.
- The same hover zoom on every image.
- Animation on load instead of in response to the person.

## Copy
- Weightless headlines ("Build faster. Ship smarter.") and words like empower, elevate, streamline.
- Filler buttons: Get started, Learn more, Try now.
- Invented numbers, lorem ipsum, "Coming soon".
- Copy that could belong to any product.

## What to do instead
- Name the default, then replace it with a choice that comes from Trove's own world.
- A short palette with roles; one or two faces with a set scale.
- Vary radius and elevation by meaning. Shadows follow one light source and encode hierarchy.
- Remove glass unless depth means something.
- Break the three-card reflex with asymmetry and real rhythm.
- Buttons say what they do. Delete numbers nobody can source.
- One motion moment, triggered by the person.

## Sources
- pixelslop, AI slop pattern catalog: https://cdn.jsdelivr.net/npm/pixelslop@0.3.8/dist/skill/resources/ai-slop-patterns.md
- The Fountain Institute, 7 tells that a UI is AI-generated: https://pages.thefountaininstitute.com/posts/7-tells-that-a-ui-is-ai-generated
- 925studios, AI slop fonts and gradients: https://www.925studios.co/blog/ai-slop-design-tells
- Capital & Compute, How to fix AI slop in web design, tell by tell: https://capitalandcompute.net/blog/fix-ai-slop-design/
- Why every AI-built website looks the same (Tailwind's indigo-500): https://dev.to/alanwest/why-every-ai-built-website-looks-the-same-blame-tailwinds-indigo-500-3h2p
- Why your AI keeps building the same purple gradient website: https://prg.sh/ramblings/Why-Your-AI-Keeps-Building-the-Same-Purple-Gradient-Website
- How to detect AI slop in your design: https://github.com/Laith0003/ux-skill/wiki/How-to-detect-AI-slop-in-your-design
