# Design decisions

Decisions Josef has made about Trove's look and feel. Newest first.

## 2026-11-19: strata, finished (canvas page "Final designs"), waiting for Josef

- **Josef:** strata has potential but the execution felt unpolished, game-like, and the arrangement not thoughtful.
  An engraved-line evolution was tried and rejected ("much closer to the original blocky strata").
- **Done** (`docs/design/art/strata/final.py`): the same slabs, finished. No bevel; a hairline paper seam between
  courses; little colour jitter. One muted family of inks, the sun the only warm note. Composed: one hero peak on the
  right third with shoulders, the sun set against its flank, sage framing the left, stone and haze stepping back,
  mist between planes, a calm lake with a glint path under the sun, firs built from courses in a varied cluster.
  Boards `FinalCover` and `FinalBook` (book screen B with the art).
- **Round 2 (Josef: sloppy, pyramids, prefers round 3's colours; then: keep the style, improve only the scene).**
  A masonry rewrite of the blocks was tried and rejected. Kept the round 1 finish; round 3's inks are back; the
  massif is a broad summit with a rounded shoulder and a second summit, the sun in the notch, a coral peak in the
  middle distance; firs laid without ragged ends.
- **Round 3, the cover first (Josef: members pick a cover; the inside scenery follows it, so the cover must be loved).**
  The cover is now composed for its own shape: one big centred massif with a notched summit and a stone cap, a large
  sun behind it like a halo, haze low on both sides, a still lake mirroring the peak, two small firs. Drawn at 2x.
  The book's inside pages are to follow from the cover (not yet redone to match).
- **Josef's rule: blocks touch by default.** No paper seam between courses and no holes where two forms meet (they
  share one boundary in the renderer, `render(touch=True)`). Spacing is allowed only as a design choice: the sparse
  river or lake, mist between ridges, an edge against open sky.
- **Then: slabs stay slightly 3D, with small uniform joints.** Each slab has a faint lit top edge, a soft underside
  and a faint end shade, and a uniform hairline joint (1px at 2x, half a CSS px) under every course and at the end of
  every slab, so each reads as its own piece. Holes and uneven gaps stay out; the joint is the same everywhere.
  Then (Josef: too much white) the joint is no longer bare paper but the slab's own ink lightened 45% toward paper.
- **Round 4 (Josef: preferred the Fresh directions strata).** The finish experiments (touching blocks, joints, tinted
  seams, muted inks) are set aside for this art: `final.py` now draws with round 3's renderer settings, inks and
  elements exactly (bevelled slabs, jitter, ragged ends, groves, `render(touch=False)`), and only the scenes are
  new: the cover's single clean summit with the sun beside it, and the title page's massif, coral peak, sage slope
  and groves. The renderer options added along the way stay available but off for this art.
- **Round 5, laid clean (Josef: messy, weird shapes; plan it properly).** Same look and inks; a `clean` mode in the
  renderer: no slab shorter than a slab and a half, touching forms share one boundary (no holes, no slivers of the
  form behind), tiny leftovers merge into a neighbour and lone specks are dropped, ragged steps only against open
  sky. Skylines from smooth noise (`Ridge(smooth=True)`), calmer tone flicker, the snow cap a snowline under the
  summit, no stripe on the small peaks, clean feet (the cover's art ends on a straight line, the page's runs off
  the page). Checked by zoom on the summit, sun edge, middle peak and foot before publishing.
- **Cover typography (Josef):** the title set left, the full name right under it at the top (class `cov-final`), so
  the art fills the rest of the cover and runs off its foot. The art is recomposed for the taller space. Fixed-tier
  flag as before: the system sets the name at the foot; this moves it under the title.
- **Three more strata covers (Josef: start building variety).** Same style and type, each its own terrain and palette,
  each cover ink taken from its art: desert mesas at dusk (terracotta, sand, plum, gold sun), sea cliffs by
  moonlight (chalk, indigo, teal sea, pale moon), an autumn terraced valley (gold, olive, rust, violet haze, a
  river). Boards `FinalCoverDesert`, `FinalCoverCoast`, `FinalCoverValley`. A long name that meets the art sits on
  the system's white knockout (seen at shelf size on the desert cover).
- **Josef: sea cliffs good; desert and valley reworked. New process rule:** after every art round a fresh critic
  subagent reviews the new art against the approved strata cover and book-screen art, its fixes are implemented,
  and only then is the art placed on the canvas. Round 1 of that: desert ("ship after fixes"): a flat-capped butte
  with sheer walls and a talus skirt, a stepped near-black aubergine shadow edge, a coral sun behind its upper
  shoulder, rose dusk light on the cap, a joined violet back plane, sand only at the foot in broken courses.
  Valley ("needs a rethink"): now autumn terraces as the hero, a stepped hillside with one colour per terrace from
  olive to rust and a pale lip on each, a near-black pine ridge with an amber sun behind its shoulder, the river in
  broken courses at the foot, no lilac hills. New renderer pieces: `River`, `Mesa(talus, top_tint, shadow_slope)`,
  `Terraces(beds, lip)`.
- **Josef: the terraced valley is unusable; rethink it.** Now "autumn hills". A first rolling-hills attempt went to a
  fresh critic ("needs a rethink": the sun merged into the ochre hill, too many inks, flat bands, poplars like
  ladders, holes, a third disc in the set). Rebuilt to its brief: no disc; three rounded domes on one value ladder
  (pale gold at the back as the glow, its crest at half the cover's height; rust running off the left in one face;
  deep forest in front); a clump of four tapering dark poplars on the front crest as the focal point; the title in
  forest green. Renderer: `Ridge(round=True)` for domes; a layer can allow narrower pieces (`min_run`) so trees
  taper to a tip.
- **Desert refinement (Josef: one more pass; no purple).** The violet back plane is now warm peach haze. A fresh
  critic then asked for polish: sheer walls with one ledge, a clean three-step maroon shadow side, no speckle on the
  lit face, a lighter coral-gold sun raised and set behind the right wall, full-width peach haze mesas behind with
  the small butte pushed into them, calm sand over a dark umber base, the picture lifted to meet the type. Done,
  then rebalanced by eye (a broad butte, not a tower). Renderer: `Mesa(wall_ledge, wobble, speckle, shadow_steps,
  ragged)`, `render(jitter)` per cover.
- **Desert, back to the tilt (Josef: the block was worse; wants more of the earlier tilt, plus a smaller foreground
  cliff).** The butte leans right (`Mesa(lean)`), walls stepping out gently down to a four-ledge scree skirt, the
  shade edge a stepped diagonal; a smaller darker cliff in the right foreground. A critic's polish (told to keep the
  tilt): cap no wider than the body, pale gold sun as a clean disc, the foreground cliff at 70% height with three
  clean shade steps, no pink sliver, darker bedding courses on the lit face, warm haze in place of the last mauve,
  a thinner umber base and warmer sand slabs.
- **Book pages follow each cover (Josef: "make the book screen pages follow these covers").** Desert, coast and
  autumn hills each get title-page and contents art (`art/strata/pages_more.py`): the cover's place seen wider at
  the cover's slab size, the hero on the right third, the text over open paper. A fresh critic then asked for more
  presence and framing: heroes raised, a low cliff framing the desert's left, the headland running off the edge with
  bigger stacks and a dark rock at the foot, the gold hill flattened so it reads as a hill and not a rising sun.
  Board `FinalBookMore`: each book opened and on a chapter, the cover's ink on the boards.
- **Pages are full scenes, not zooms of the cover (Josef: the reference page adds far more scenery; one page is
  enough; much more elaborate, cooler environments; redo the desert, its hero not a tower).** Only the title page
  gets art now. Coast: a lighthouse and keeper's cottage on the headland, an arch, a broken line of stacks and a
  misted far stack, headlands receding left, foam at the feet, the moon low under cloud with its path on the sea,
  cloud banks, rocks in both lower corners. Autumn hills: two lilac tiers in mist, a striped gold field beside a
  smaller gold hill, an olive slope with an orange grove, a river with poplars winding out between the rust hill
  and the forest, a cumulus and streaks of cloud. Desert, rebuilt: a wide low mesa and its bench with the sun
  setting behind the right shoulder under cloud streaks, the stepped haze cliff, buttes, pinnacles, an arch, a dry
  wash between dunes, scrub. A fresh critic reviewed the first draft (too few planes, a tower, flat fields); its
  fixes are in. Board `FinalBookMore`: one opened book per cover. The covers are unchanged.
- **The canvas page is now "Covers: Strata", one page per art direction.** Each row is a cover with its book
  screen to the right (`FinalCover`/`FinalBook`, then desert, coast, autumn hills). One book screen per book: the
  title-page art is reused inside the chapters, so no second variant (the contents band) is drawn. `FinalBookMore`
  is gone. Desert page: no clouds. Autumn page: clouds lower and on both sides, clear of the text.
- **Four new strata places, covers only for now (Josef picked all four of the proposed sceneries; book screens
  later).** `art/strata/covers_new.py`, boards `FinalCoverKarst`, `FinalCoverAurora`, `FinalCoverTerraces`,
  `FinalCoverLagoon` on "Covers: Strata", one row each under the autumn hills, the book-screen slot to the right
  left empty. Karst: one tall rounded tower, paler towers stepping back by value, a sampan on a calm river. Winter
  night: the night sky starts exactly at the aurora's upper edge, plain paper above it (Josef), a tall snow peak, a
  frozen lake, a cabin with the one warm window, firs. Rice terraces, rethought after Josef rejected the striped
  ridge: shelves seen from the front, each a flooded pool holding the dawn sky (rose high up, gold low down) with a
  thin dark bank below, the banks bending in a slow wave like contour lines, the low sun on the left. Volcanic
  lagoon: a green cone lit from the left with a short plume clear of the title, a muted teal lagoon, a sandbar and
  two palms. Each round went through a fresh critic with every approved cover and page as reference (Josef: show it
  all the approved pieces, not only the original strata).
- **Winter and lagoon revised, and the karst book screen (Josef).** Winter: the hills lower and soft-shouldered but
  uneven (not domes, "so they don't look like igloos"); the aurora one smooth curve whose curtain and the sky beneath
  it dissolve upward into paper; a log cabin built of level blocks (lit gable wall, dark side wall, shingle roof with
  snow along its top and eave steps, chimney, the one warm window, a door). Lagoon: a lopsided cone with a dark
  barren summit over green skirts, ravines, a small amber vent and a plume clear of the title; palms drawn as blocks
  in the manner of the desert page (a trunk stepping sideways a slab at a time, a crown of level courses). Karst book
  screen (`art/strata/pages_new.py`, board `FinalBookKarst` beside its cover): towers in five planes into haze with
  thin stepped clouds, three tall towers right of the text stepping darker toward us, the water mirroring them with
  their shade broken on it, stepped paddies, a two-tier pavilion, bamboo, a sampan with its boatman and a far boat.
  Each went through a fresh critic.
- **Karst page and volcano fixed (Josef).** Karst page: every back plane's foot runs down behind the paddies over a
  continuous haze floor, so no paper shows under the towers. Volcano redone lower and less sharp: a blunt summit
  on bulging slopes with a shoulder on each side, so its outline steps in and out instead of running straight.
- **Rice terraces, third composition; winter cabin redone (Josef).** The terraces were too uniform; a version
  borrowing the autumn hills' three domes was rejected as a copy ("the cover must still be deeply original"). Now a
  terraced valley seen head on: level flooded terraces step down from both edges into a V, each slope with its own
  uneven heights and reach, the left slope (facing away from the light) darker with deep green banks, the right lit;
  the low sun sits in the notch over a pale blue-grey lake with its path down the water; a hut on the right slope, a
  tree on the left (`StepValley`). Winter: the aurora lower, its upper edge fraying into paper through long
  horizontal gaps, the night a step lighter; the cabin rebuilt larger on a 6 px cell grid (log courses in two tones,
  a snow-edged gable, a snow roof plane against a stand of dark firs, a stone chimney with grey smoke, a lit window,
  a door with a snow step, a dimmer side window, a woodpile of pale log ends, drifts).
- **Terraces texture, cabin roof (Josef).** The stepped valley's shape stays; the terraces "looked like cake", so each
  pool is now water, not a layer: pale sky blue in long runs with openings through it, rose and gold glints gathering
  near the sun, a single green bank under each. The cabin's roof vanished, white snow on white snow: it is now a dark
  shingle gable with only a thin line of snow along its top, on walls laid as log beds, so the whole roof reads.
- **Terraces after two critic rounds (Josef: "too bland, too thin lines", send to the critic twice).** The V stays.
  Round 1: one value band and pencil-thin banks; fixed with deep terraces (a flooded pool of 2 to 5 courses, a dark
  lip, a 2-course earth riser), a near-black anchor, a butter sun half behind two violet ridges, a deep ink-teal lake
  with the sun broken across it. Round 2: it still read as a lake with striped banks; fixed by closing the V partway
  down so the foreground is paddies, the lake a small wedge in the notch, every terrace bowed down toward the middle
  like a contour line and deeper as it nears, the shaded slope violet-grey water on moss risers and the lit slope
  butter and peach water on olive, seedling rows and a bent planter in a straw hat in the near paddies, a stilted
  thatch hut and a dark tree on the crests (`Paddies`).
  Then (Josef: "getting there"): the planter removed, the seedling rows dropped, and each slope's inner edge run as
  one smooth diagonal through the terraces' edges, so the V's profile no longer steps terrace by terrace.
- **Autumn book page (Josef).** The orange grove on the olive slope is scattered, five trees at different heights and
  sizes instead of a line; the river now leaves the hills at the valley floor and winds down toward us with a gentler
  bend, instead of starting up on the slope. The poplars are unchanged.
- **Winter without the cabin; terraces lower with bushes (Josef).** The cabin is gone from the winter cover (the firs
  stay). The rice terraces sit 34 px lower, and clumps of leafy bushes stand on the terraces to break the stripes: a
  broad clump across the shaded left slope, smaller ones on both sides.
- **Desert cover: the butte lowered (Josef: more space for the author).** The butte's top and the sun behind it sit
  16 px lower (world units), leaving a clear band of white under the name.
- **Book screens for the winter, terraces and lagoon covers (Josef: build them out).** `art/strata/pages_new.py`,
  boards `FinalBookAurora`, `FinalBookTerraces`, `FinalBookLagoon` beside their covers. Winter: the aurora lying low
  under the text and sweeping up beside it on the right, hung as separate curtains, night and a few pale stars
  beneath; a tall snow peak and a long range of soft, uneven hills; a frozen lake with the aurora faint in the ice
  and two cracks; far firs along the shore, dark groves in both lower corners. Terraces: the left slope low under
  the text, the right climbing high to the stilted hut; three violet ridges and the sun in the notch over the lake,
  mist across the left; lips lighter and broken so they read as banks; the slopes meet on a stepped diagonal;
  bushes and dark trees on the terraces. Lagoon: the volcano on the right (dark summit, glowing vent, plume leaning
  away), an older island and a small far one, clouds, deep water past a broken line of surf on the reef, pale
  shallows with coral heads, a sandbar with block palms and an outrigger canoe. A fresh critic reviewed the drafts;
  its main fixes are in.
- **The three pages reworked (Josef: none great; every main peak lower).** Winter: the tallest peak and the spike
  on the right are gone, the aurora is one smooth curtain lying low with no gaps, and the lake is now a fjord, dark
  calm water winding back between steep snow walls through a bright snowfield. Terraces: a whole country of hills,
  not two striped slopes: far ridges and the sun, two small finely terraced hills, a lake, three more small hills in
  sage, ochre and peach, a big left hill broken by a forested gully, a right hill of large wide terraces with the
  hut and a waterfall, broad paddies and coconut palms in front. Lagoon: a lower volcano, misty far islands and a
  low jungle island, the reef closing the lagoon in an arc of sand and surf with two palm motu on it, a sand shoal,
  a dense palm forest on the near beach with the canoe. A fresh critic reviewed them; its main fixes are in.
  Then (Josef: the lagoon "so much better"; no critic pass): the palm forest broken up into two loose, staggered
  rows on uneven ground, irregular gaps, each palm its own height, crown and lean, undergrowth between.
- **Rice page: hills meet the ground (Josef: they looked like eggs).** Every terraced hill now has a bell profile
  (a round hill with power 2.2, a third wider) whose flanks flare into the ground instead of dropping straight; the
  coconut palms are replaced by broad shade trees on dark trunks; the waterfall on the right hill is gone; the hut
  sits on the crest.
  Then (Josef: the bottom too straight) the foreground paddies are fields whose edges swell and dip across the page
  (`FieldRows`), each field its own depth, its bank following the wave.
- **Covers keep room for a one-line name at shelf size (Josef, a rule for every new cover from now on).** Measured
  on the boards: at shelf size a three-line title and a one-line name reach world y ~171 of the 236 x 344 cover,
  left of x ~200, so there the art stays below y ~180; only the right edge may rise higher. The rice terraces cover
  is rebuilt to it and to match its book page, still minimal: two bell-shaped terraced hills spreading into the
  ground (peach on the left, a taller gold one on the right with the stilted hut), the sun between violet ridges over
  a small dark lake, wavy fields in front. The volcano cover is lowered for it: the summit, shoulders and bands sit
  32 units lower, the plume starts at the vent and bends right under the name line.
  Then the rice cover tightened (Josef): drawn through a slightly smaller window of the scene (`VIEW`, the cover's
  proportions, about 13% closer); the two hills closer together; less of the fields at the foot; the sun higher and
  larger; the lake's yellow glints and sun path replaced by a paler teal. The name line still clears at shelf size.
- **Three fixes (Josef).** Winter cover: the aurora no longer trails off on the left (one even depth edge to edge);
  "Long Nights, Clear Skies" wraps to four lines at shelf size, so the curtain sits just under that name line and the
  snow hills come down to leave the night between. Mountain lake page: pale lake water lies behind the mountains'
  misty feet, so no paper shows between them and the lake. Desert cover: low sage-olive scrub clumps on the sand, as
  on its book page.
- **Purple in the aurora (Josef), cover and page.** The curtain runs green at the hem, teal, then violet and a soft
  purple in its upper body before it dissolves; the colours climb faster than the height and fade less toward paper,
  so the purple reads.
- **Desert cover: an arch (Josef).** The tilted butte is replaced by a great rock arch of the same rock, the low sun
  seen through its opening (drawn in front of the haze cliff and behind the arch), with one thin spire beside it;
  both stay under the shelf-size name line.
  Then recomposed for balance (Josef): the arch narrower and taller with a tall slim opening, as on the book page, in
  the deeper terracotta, on the left third; the sun setting in the middle; one thin spire on the right; a dry wash
  winding from the foot up toward the sun, scrub along its banks; the near cliff gone.
  Then layered (Josef): the spire moved left and forward, standing on the sand in front of the haze and the sun's
  edge; a blocky cliff in the right foreground running off the edge, so arch, spire and block step toward us.
  Then rebalanced after a critic pass (Josef: still unbalanced). The critic: three equal dark verticals read as a
  fence, the sun was wedged between arch and spire, the weight tipped like a seesaw. Now the arch is the one dark
  focal mass on the left; the spire a lighter, smaller partner close beside it; the sun moved right and set low in a
  pale haze band that rises from left to right to cradle it; a low, darker umber block with a stepped top anchors the
  lower right; the dry wash ends under the arch's opening; three lighter scrub clumps.
  Then (Josef: arch better): the arch throws a shadow right across the sand, darker slabs; the foreground cliff is a
  step lighter and wider.
- **Three relatable covers to finish the collection (Josef picked them: lakefront city at dusk, prairie farm at
  harvest, bay bridge at sunset).** `art/strata/covers_us.py`, boards `FinalCoverCity`, `FinalCoverPrairie`,
  `FinalCoverBay` on "Covers: Strata" under the lagoon, covers only for now. Josef asked for a faster polish loop with
  a critic that judges as he does: his preferences are written down in `art/strata/CRITIC.md` (every rejection made
  in this collection, as rules), each cover was self-checked against it and then went through two rounds with a
  critic briefed as Josef. City: one dominant tower with a setback crown on the right, the rest uneven, a pale far
  skyline with the sun half set into it, warm-lit and slate faces, a warm reflection under the tower, a dark shore
  wedge. Prairie: the low sun half behind a windbreak in irregular groups, a gambrel barn (rust, never the UI red)
  with a domed silo, both throwing shadow right, crop rows and furrow lines converging on the barn, a curving road,
  fence posts at uneven intervals as the dark anchor. Bay: a suspension bridge in muted rust at an angle, the near
  tower tall on the right, a solid deck, the main cable a clean curve dipping below the sun, soft dark hills, a warm
  reflection, a low dark bluff in the corner.
  Then (Josef: city good; barn needs detail, fix the fence; bridge wonky), with a Josef-eye check: the barn larger,
  a gambrel with one continuous cream trim along its roof, a plain framed double door with a dark seam, a small
  hayloft, side windows, board seams; the fence a near run along the lower left, four posts and two continuous rails;
  the bridge rebuilt clean: a level deck with a dark underside, one continuous cable from a shore anchor over the far
  tower, sagging below the sun and easing up to land on the near tower's top, even hangers, one low continuous shore.
  Then (Josef, 2026-11-21: doesn't like the farm and the bridge; remove them, do a forest instead): the prairie and
  bay covers and their boards are gone; `FinalCoverForest` ("Room to Grow", Noah Bergstrom, ink #283d2e) takes the
  slot under the city. A fir forest on a bright morning seen from a trail across a meadow: the trail, an opening in
  the trees and the low sun in it on one axis; one old fir on the right edge, the only thing above the name line,
  with uneven tiers, a missing and a long bough, its trunk and shadow showing; a mid stand in uneven clumps with one
  tall fir leading; small pale firs in the opening; a fir pair and ferns as the lower-left anchor; the meadow edge
  undulating. Two Josef-eye critic rounds. (A first try of bare trunks dissolving into haze read as poles.)
  Then (Josef: build the book screens for city and forest): `art/strata/pages_us.py`, boards `FinalBookCity` and
  `FinalBookForest` right of their covers. City: a long skyline across the lake, the main tower with setbacks and a
  dark spire on the right, the rest in three groups of uneven width built as clean blocks (lit two thirds, slate
  third, shade its own layer so the edge runs straight), a pale far skyline with the sun half set into it, a
  breakwater and lighthouse, three sailboats, the lakefront park with promenade, lamps and trees. Forest: a snow-capped
  ridge far off on the right, haze firs in clumps, the forest in three groups with an opening where the sun sits, the
  meadow with the trail, a meandering creek under a plank footbridge, a copse out in the meadow, the old fir on the
  right edge, young firs, a boulder and ferns in the lower left. Two Josef-eye critic rounds. Pages render a little
  past both edges and are cropped, so no slab start jitters off the page edge.
  Then (Josef: more detail on the city's buildings): facades as a detail layer over each tower's faces: punched
  window grids on most (the shaded face's windows one value darker than its wall), ribbon windows on two with a
  blank spandrel every fourth floor and a base band, vertical fins on the main tower and two others, a sky-lobby band
  and a podium on the main tower, rooftop boxes and masts, and lit windows only in a few groups of two or three in a
  muted warm ink. One Josef-eye critic pass (it caught noisy shaded faces, cake-like ribbons, a jagged overlap and
  stray yellow specks).
- **Book pages flush to the page edge (Josef: apply the city and forest fix to all book screens).** The renderer
  used to jitter where a run starts and ends, also at the page's sides, which left small uneven paper notches along
  the left and right edges. `render(..., flush=True)` stretches a run's outermost column to the edge after the row
  is laid, so it consumes the same random draws: the lake, desert, coast, valley, karst, winter, terraces and lagoon
  pages are pixel-identical inside and only their side edges changed (checked by diff).
- **Cover type trials at true shelf size (Josef: unsure the typography does the art justice; wants three approaches on
  a shelf at the real in-app scale, will pick one).** Board `TypeTrials` on "Covers: Strata" (`shelf/type_trials.py`):
  the app's desktop shelf book (122 x 178 CSS px), shelf name, rule and ledge, at 1:1. A first shelf has three arts
  with one approach each, then one shelf per approach across five covers. A Poster: Barlow Condensed 800 caps 20px,
  the name in Barlow 700 9px under it. B Literary: Newsreader 600 16.5px (the app's book-title face), the name in
  Plex Sans 600 caps 8.5px. C Label: the title in a thin framed label (Newsreader 600 14px), the name on a paper tab
  cut into the foot of the art. A and B put a paper knockout behind the name where older art rises into it. Not a
  decision yet: Josef picks.
  Then (Josef: drop B and C): B and C are now A with the name moved. B: the name in the bottom left corner, on a paper
  knockout over the art. C: the name above the title (three-line titles then run into the taller older art).
- **Shelf book size trials (Josef: the books are so pretty they should be larger in the app, which also helps
  legibility).** Board `SizeTrials` on "Covers: Strata" (`shelf/size_trials.py`): a 1440 px desktop page at actual
  size with three shelves of the strata covers: today's `.book` 122 x 178 (gap 28), 150 x 219 (gap 32) and 176 x 257
  (gap 36), the poster type scaled with the book. Book size is fixed tier (system.md "Book"); not changed until Josef
  picks a size, then the change goes to the design system and the app through the orchestrator.
  Then (Josef, 2026-11-21: "Let's go with largest"): the shelf book is 176 x 257 with a 36px gap (system.md "Book",
  fixed tier, changed with his yes). The type on the cover scales with it (poster type: title 29px, name 13px). Phone
  and the smaller sizes are not decided yet. The hinge (spine) is being reconsidered next.
- **Spine options at 176 x 257 (Josef: should the spine take so much space on the left? three options).** Board
  `SpineTrials` (`shelf/spine_trials.py`), actual size: today's hinge scaled (line at 17px, type at 29px); A narrow
  hinge (a thinner line at 8px, type at 18px); B ink spine (no line, a solid 8px strip of the cover's ink along the
  left edge, type at 18px); C no hinge (outline and dot shadow carry the book, type at 14px). Not decided yet.
  Then (Josef picked A): the narrow hinge. On the 176 x 257 shelf book, a 1.5px ink line 8px in from the left edge,
  the type starting 18px in (system.md "Book", fixed tier, changed with his yes).
- **Strata cover type: A, the name under the title (Josef, 2026-11-21).** From the type trials: the poster type with
  the name right under the title, at the new shelf size: title Barlow Condensed 800 caps 29px, line-height 0.92,
  +0.01em; the name Barlow Condensed 700 caps 13px, +0.16em, 10px under the title, on a white knockout where the art
  rises into it (system.md type roles). Name at the foot and name on top were not chosen.
  Then (Josef: update the cover boards): every cover board on "Covers: Strata" shows the new shelf book (176 x 257,
  the narrow hinge, the new type) under a large cover that is the same book scaled x2.68 (title 78px, name 35px, the
  hinge 21px in), so the large cover previews the shelf exactly. The small book uses the large render to stay crisp.
- **Long fields replace the rice terraces (Josef, 2026-11-21: "not a fan of the rice terraces actually, can we turn
  them into long fields instead?").** `art/strata/fields.py`, same boards (`FinalCoverTerraces`, `FinalBookTerraces`,
  now labelled "long fields at harvest"), same book. The land is a height field seen from above its near edge, so
  long strips of crops (wheat, sage, green, ochre, pale; ploughed earth on the page only) run across it in perspective
  and drape over the swells, shaded where they fall away to the right; a few field boundaries converge on the
  horizon; hedgerows on some strip edges only, never in shade; a low warm sun over a lilac range on the left. Cover:
  one broad swell on the right with a lone tree, a deep green near field. Page: three swells, a lane winding to a
  white farmhouse with a low brown gable roof, trees along the hedgerows, a big tree on the right crest, a deep green
  near field with a tree group. Two Josef-eye critic rounds. The sample blurb still mentions terraces.
- **Comparison shelves removed (Josef).** The type, size and spine trial boards and their scripts are gone now that
  the choices are made (176 x 257 book, narrow hinge, poster type with the name under the title); they stay in git
  history (commits fc05fa5, d22d257, b1882e5).
- **Fields cover: one clear identity (Josef: the page is better, the cover has no clear identity).** The cover is now
  one long field of ripe wheat (golds only) running from the near edge back over the green land to a hedge just
  below a lone dark tree on the crest of the swell; its crop rows converge on the tree; the low sun sits just left of
  the tree, so the two are one focal point; greens either side in strips of uneven width, darkest in the near left.
  The page is unchanged. One Josef-eye critic pass (it found the first version read as a dirt road).
  Then (Josef: no, take the book page as the inspiration: fields clearly separated, bushes in the lines): the single
  wheat field is gone. The cover is the page's farmland kept small: every near field closed by dark hedges on all
  sides, three boundaries converging on the horizon, bushes standing where hedgerows meet, one smooth swell on the
  right with a big tree on its crest, the low sun over the lilac range on the left, a deep green near field. One
  Josef-eye critic pass (it found the fields read as stripes until the boundaries were drawn wide enough to render).
  Then (Josef: polish the book page: a nicely curving road, refined fields, the hill's tree too large, maybe add
  another): the lane is one smooth S-curve (a Catmull-Rom curve through four points) widening from 8 at the house to
  32 at the near edge; the fields are broader and closed by hedges like the cover, four boundaries converging, bushes
  where hedgerows meet; the crest carries three trees of clearly different sizes in a dark ink, each with a short
  shadow; the farmhouse sits a little nearer, whiter, with a broad overhanging rust-brown roof, one door, and a dark
  tree behind its shaded side. One Josef-eye critic pass.
  Then (Josef: the house smaller with slightly more detail): about half its old size (36 x 24 world px), built row
  by row on the page's 4 px slab grid so every piece survives: ridge and chimney, roof, a dark eave overhanging both
  walls, then the lit gable with a two-row door and a window and the shaded side with a small window. Each part is
  its own layer, because within one layer a slab takes a single colour and swallowed the door and windows.
- **Strata art set 1 approved for the app (Josef, 2026-11-21: "this is officially the first set of art ready to be
  implemented into the app, each book should get one at random so that the sample test libraries have some varying
  art").** Ten places, each a cover and a title page: lake, desert, coast, valley, karst, winter, fields, lagoon, city,
  forest. Packaged in `art/strata/set-1/`: the exact canvas files (`covers/`, `pages/`), `manifest.json` (key, name,
  cover ink, files), a contact sheet, and a README with the implementation spec (176 x 257 shelf book, narrow hinge,
  poster type with the name under the title, page art behind the opened book's title page). Each book picks its art
  deterministically from its id, so its cover and page always match and stay the same across reloads.
- **Watercolor covers, first three (Josef, 2026-11-21: a new page, 10 watercolour books over time, the first three
  obsessed over, covers only).** New canvas page "Covers: Watercolor", boards `WCCoverLighthouse` ("Keeping the
  Light", Maren Holt), `WCCoverHarbor` ("Harbor Season", Sofia Marchetti), `WCCoverAutumn` ("The Long Way Home",
  Emmett Clarke); `art/watercolor/` (engine `paint.py`, scenes `covers.py`). Illustrated watercolour, not photographic
  (rejected before) and not abstract: glazes, wet-in-wet, pooled edges, granulation, bare paper as white. Every object
  is painted "loose", built from overlapping wet patches the way foliage is, because clean shapes under a paper
  texture read as clip-art. Lighthouse: a white tower on a grassy point, surf lifted round three rock groups, a pale
  sky with clouds left as paper. Harbor: two wooden boats close in the foreground, a white village on its own
  headland behind with a small campanile. Autumn: a river under a stone arch bridge, golden crowns flowered at their
  edges, the big tree on the right. Same cover object and type as strata. Two Josef-eye critic rounds, their fixes
  applied but not re-reviewed; the critics found the objects stiffer than the washes, so this is round 1 for Josef.
  Then (Josef: "all look pretty, push all, but this time, we wont make the top of the cover white, it can be some
  light (or even dark) color and title will adjust by itself so that there is some variety in the library"; and keep
  round 1 on the board): round 2 is painted edge to edge, on new boards `WCCover{Lighthouse,Harbor,Autumn}2` in a row
  under round 1, which stays as it was (its code is in commit 5813d6b). The lighthouse at dusk (indigo melting to
  rose and gold, the lantern glowing), the harbor under a light morning sky (smaller boats on their reflections,
  muted roofs, a masthead and stay), the autumn river in a golden haze (it now meanders, reflects the sky and runs
  under a real stone arch). **The title adjusts by itself:** `art/watercolor/ink.py` measures the paint behind the
  title (world x 18-200, y 20-175) and picks cream (#f6efe0) on a dark top or the book's dark ink on a light one,
  whichever contrasts more (here 7.2, 6.1 and 6.7 to 1); the name has no knockout, it sits on the paint. This changes
  the fixed cover type's colour rule for these covers, with Josef's yes. One Josef-eye critic round on round 2, its
  fixes applied.
  Then (Josef: "rework the autumn cover, the bridge is kinda half there and half not, cut off, and trees are lazy,
  polish it all up"): a new board `WCCoverAutumn3` beside round 2's autumn, which stays. The glazes are transparent,
  so the old bridge let the trees behind show through half of it; the bridge is now lifted back to paper first and
  built over it: a humped stone bridge with splayed ends sunk into bushes, coursed and single stones, a coping and a
  ring of voussoirs, the river and its far bank seen through the arch, and the arch's ring closed in its reflection.
  Trees are built by `tree()`: a tapering trunk forking into curved limbs that split again, the crown dabbed as
  clumps at and along the limbs with sky between them, the whole crown glazed darker toward its lower right, the
  limbs showing only below the crown; each throws its shadow right. Two unequal firs behind the bridge's left end
  are the cool dark. The river widens toward us with soft wet edges and darker water under the banks; a low rose
  cloud band sits under the title. `paint.rough` now replicates the edge instead of pulling in paper, which left a
  row of white dashes along the cover's bottom edge (the lighthouse has it too; it is fixed there only when that
  cover is re-rendered). Two Josef-eye critic rounds; the second still asked for more (fewer stain-ring edges in
  the oak's clumps, a darker overall value range); its main points were applied and not re-reviewed.
  Then (Josef: river edges "more smooth and not jagged"): both banks are Catmull-Rom curves through the river's
  points, with only a slow wobble and no fine ragging on the water's edge.
  Then (Josef, 2026-11-23: "remove the two older autumn covers"): `WCCoverAutumn` and `WCCoverAutumn2` are off the
  canvas; `WCCoverAutumn3` takes round 2's place in its row.
  Then (Josef, 2026-11-23: "remove the full screen harbor"): `WCCoverHarbor2` is off the canvas; round 1's
  white-top harbor stays, and the autumn moves left to close the row.
- **Lighthouse lantern (Josef: "fix the yellow square in the lighthouse").** The dusk sky skipped a 16 x 12 rectangle
  round the lantern, larger than the lantern, so a square of paper stood there and the glow glazed it yellow. The sky
  now skips only the lantern's own shape (lamp room, gallery, roof). The cap and gallery are a dark Payne's grey,
  and the lamp room is lit from inside, with two glazing bars and a lifted lamp. The re-render also carries the
  `paint.rough` edge fix, so the white dashes along the bottom edge are gone. Board `WCCoverLighthouse2` updated.
- **Watercolour goes abstract (Josef, 2026-11-23: "going forward, prioritize abstraction with the watercolors like
  seen here", the round 1 lighthouse headland, "much nicer than the full detail in the autumn. Produce 4 completely
  new feeling covers").** The rule for watercolour covers from here on: every region is a few large wet patches side
  by side and over each other, each with a pooled rim; flat fills; objects as single silhouettes; no stonework, limbs,
  leaf dabs or ripple marks; where planes meet, a hair of paper rather than glazes stacking to mud. Four new covers
  in `art/watercolor/abstract.py`, a new row on "Covers: Watercolor":
  `WCCoverMesa` ("The High Desert", Lucia Navarro: a deep cobalt dusk over a terracotta butte in uneven strata, one
  violet shade face, cream title at 7.4:1), `WCCoverHills` ("Slow Harvest", Tomas Rinaldi: a pale lemon morning over
  patchwork hills in sage, ochre, apricot and mauve, three cypresses and a small house; olive title at 7.6:1),
  `WCCoverLake` ("Above the Tree Line", Ingrid Solberg: a cerulean sky, a massif with two summits on the right, the
  forest as three dark masses, the mountain mirrored loose in teal water; blue title at 5.4:1), `WCCoverWinter`
  ("First Snow", Hannah Lindqvist: a mauve dusk with a low pale sun, firs as loose glazes, the snow carried by big
  pale violet and blue patches; plum title at 5.6:1). Two Josef-eye critic rounds; the second round's fixes are
  applied and not re-reviewed.
  Then (Josef: "not a fan of the color rectangles on the snow"): the snow's patches are gone. The snow now takes one
  soft cool glaze that deepens toward us with no edge at all, and two long arched drift shadows that swell in the
  middle and lift to nothing at both ends, crisp along the top and melting below.
  Then (Josef: "now they're too jagged, I want some more gentle splotches"): the drift strokes are gone. Over the
  soft glaze, seven rounded splotches of lavender, mauve and blue are dropped in wet, soft-edged with no pooled rim,
  overlapping and of different sizes; the lone fir's shadow is a soft splotch too.
- **Book screens for the abstract watercolours (Josef: "the more elaborate book screens for these 4 new designs, same
  principles as the book screen for the strata covers").** Boards `WCBook{Mesa,Hills,Lake,Winter}` on "Covers:
  Watercolor", built like the strata book screens (`shelf/watercolor_book.py` reuses `final_book_more.py`): the book
  opened on its title page, the page art from `art/watercolor/pages.py` (570 x 684, 1140 x 1368 px). Same principles
  as strata: the same place as the cover as a much richer scene, the text corner (x 0-470, y 0-350) left as paper,
  the art climbing on the right. In watercolour the sky has no top edge: it is a wet wash bleeding out into the paper
  on a gentle diagonal toward the text (the paint engine now renders at page size, `paint.configure`). Mesa: a
  second butte and a spire, talus skirts, a broad pale dry wash, sage clusters, a juniper and a dark rock shelf in
  front. Hills: a hill town with a short campanile, a pale road widening toward us lined with cypresses in groups,
  olive trees, lavender rows, a dark near field. Lake: a broad massif with a shoulder, a cabin and jetty, a canoe,
  the mountains mirrored loose in the water, boulders and a dark fir in front. Winter: the low sun, a dark forest
  band, one dominant fir with smaller ones behind, a cabin with a lit window on the rise, a few fence posts, a big
  spruce and rocks in front, the snow in soft splotches. The text on the page takes each book's dark ink. Two
  Josef-eye critic rounds; the second round's fixes are applied and not re-reviewed. Kept against the critic: the
  hair of paper between the hills' bands, the trait of the headland Josef pointed to.
  Then (Josef: "the houses are too blocky", and the hill town "these too"): every house is now `cottage()` in
  `pages.py`, a small house seen three-quarter on and painted by hand: the gable end toward us and lit, the side
  wall turning away into shade, one roof plane, a dark verge, wobbling edges, each part a couple of loose patches.
  The lake cabin, the winter cabin (snow on the roof, a lit window) and the farmhouse use it; the hill town is a
  huddle of five small pale cottages with tiled roofs and a campanile with a pointed cap. And (Josef: "arranged
  like the strata board, with book and book screen next to each other"): one row per book, the cover at x 0 and its
  book screen at x 680, mesa, hills, lake, winter; the earlier covers without book screens in one row beneath.
  Then (Josef: the winter cabin "still floating over the edge, move it to the right"): it moved right onto the
  rise and sits at the lowest snow under its whole footprint, so no corner hangs over the slope.
- **Four more abstract watercolour covers (Josef: "create 4 new gorgeous original covers").** In
  `art/watercolor/abstract2.py`, each a feeling the set did not have, on a row under the paired books on "Covers:
  Watercolor" (the earlier covers moved one row down): `WCCoverCity` ("After Hours", Marcus Bell: an indigo night
  over a skyline of uneven towers with setbacks and one spire, warm windows lifted out in clusters, the tallest tower
  catching the last glow, its lights broken in the river; cream title 5.0:1), `WCCoverBlossom` ("Second Spring", Aiko
  Tanaka: a blush sky, one blossom tree leaning in from the right, its crown soft pink and mauve clouds of patches, a
  pond with an uneven shore holding the pink; plum title 8.6:1), `WCCoverPrairie` ("Weather the Season", Caleb Hart:
  a dark storm sky, one billowing storm mass on the right over a band of low gold light, a barn under a gambrel roof
  and a windbreak, a pale track into golden fields; cream title 6.0:1), `WCCoverBeach` ("Off the Clock", Leilani
  Cruz: a coral sunset, a large sinking sun crossed by a cloud bar, a gold path on the violet sea, warm sand cooling
  toward us, one palm in a single curve with broad drooping fronds; brown title 5.9:1). Two Josef-eye critic rounds;
  the second round's fixes are applied and not re-reviewed. Kept against the critic: the city's dark navy top, where
  the title turns cream by itself.
  Then (Josef: city good; the blossom "needs some more volume, it's like weirdly L-shaped"; the storm field okay but
  "weird yellow shine behind the barn on the field"; the beach palm "looks ugly", "at least 2 palm trees", the trunk
  "too straight", the top "weirdly shaped", the light on the water not under the sun): the blossom crown is one full
  rounded mass, lit on its upper left and turning mauve to its lower right; the prairie's low light is a band in the
  sky only, nothing on the field; the beach has two palms, a big one curving in from the right and a smaller one on
  the left, each trunk one strong curve tapering upward, each crown a fan of fronds that rise and droop to fine tips;
  the path of light now runs straight down from the sun.
  Then (Josef: "a little more mass to the sides of the cherry blossom", "the palm trees still don't look great"):
  the crown has four more patches at its sides; each palm leaf is now a long crescent, broad in the middle and
  drooping to a fine tip, its leaflets hanging below, the lower leaves in shade, on a thicker bowed trunk.
  Then (Josef: the palms "still looking a little weird", "nice and abstract and pretty", "both of them on the right
  side"): both palms stand on the right, the tall one bowing left over the beach and a smaller one leaning right
  behind it; each leaf is one tapered brushstroke that rises, arches and droops to a point, the crown one dark wet
  silhouette with lighter green in the upper leaves.
- **Autumn simplified into the abstract language (Josef: "simplify the autumn cover so that it uses the abstract
  painting methods ... a little better and isn't so overly detailed ... I do like the color scheme ... the river is
  very defined as opposed to the nice abstract blotches ... I do like the trees").** `WCCoverAutumn3` keeps its
  colours and every tree; the river is an uneven wet shape filled with loose gold, violet and blue-grey patches; the
  banks are one warm wash with a few large patches; the bridge is a few washes with a shaded right side, without the
  stone courses, single stones, coping, voussoirs or ripple lines; its reflection and the trees' reflections are soft
  blotches.
- **Winter page: even aurora, lake back (Josef).** The aurora keeps one depth from edge to edge (the cover's taper
  toward the left end is switched off on the page) and dissolves upward through a much taller zone, a slower
  gradient into paper. The fjord is gone: a lake of dark night ice lies between the hills again, the back hills
  mirrored in it, the aurora faint in the ice, the snow hills in front on either side and a near snow shore.
- **Lagoon page: water filled (Josef: too much white on the right edge).** The reef and lagoon rows now run well past
  both edges and leave no open gaps, so only the pale glints remain.
  Then shade under the palm forest (Josef): darker sand slabs pooled at each palm's foot, thrown a little right, away
  from the light.
- **Cover typography follows the gouache poster, set left (Josef: "redo the cover typography everywhere to match
  closer to 4 · Gouache poster, keep it left justified and name right under").** A fixed-tier change with Josef's
  yes: on the strata covers (`cov-final`, all eight boards on "Covers: Strata") the title is Barlow Condensed 800 in
  caps, +0.025em, line-height 0.95 (58 px on the large cover, 19 px on the shelf), set left in the cover's ink on the
  white knockout; the full name sits right under it in Barlow Condensed 600 caps, +0.24em, as a chip of the cover's
  ink with white letters (16 px large, 7.5 px shelf). The gouache cover's own rules stay as they were. The design
  system's type roles note the exception.
  Follow-up (Josef: lower edges of some titles clipped; no names in blocks): the clipping came from the title's white
  knockout, whose box is taller than the 0.95 line, so each line's box covered the foot of the line above. The title
  has no knockout now (the art never reaches it). The name is plain Barlow Condensed 700 caps, +0.24em, in the
  cover's ink, on the white knockout only.
- **Book screens for the city, blossom and autumn covers (Josef: "do the book screens for blossom, city and
  autumn").** Boards `WCBook{City,Blossom,Autumn}` on "Covers: Watercolor", built like the first four
  (`shelf/watercolor_book.py`), the page art from `art/watercolor/pages2.py`. Each sits to the right of its cover:
  city, blossom and autumn now take the paired rows under winter; prairie and beach (no book screens) one row below,
  the round 1 and lighthouse covers in the last row. City: the indigo night climbing the right with a pale moon, a
  few overlapping towers rising to one spire, soft lights only near it, a long low bridge on broad arches with an
  uneven string of lamps, broken streaks in the river, a deep violet embankment in front. Blossom: grouped blossom
  and green trees on the far bank, a pond with an irregular shore holding the pink, a small footbridge as one solid
  arc between grassy banks, the great tree's crown climbing the right side and reaching out low over the water,
  petals drifting. Autumn: the same golden haze and violet wood, a long flat stone arch in the middle distance with
  a dark fir beyond, the river winding wide toward us in loose gold and violet patches, a broken reflection, trees on
  both banks and the great oak rising on the right. One Josef-eye critic round; its fixes are applied (fewer towers
  and lights, no black quay or lamps, clustered far trees, no railings on the footbridge, a flatter arch, the house
  removed) and not re-reviewed.
  Then (Josef: one part of the blossom tree "unusually faded", "looks like a mistake"; the grass "a little too dark in
  places"; the autumn bridge "less steep at the ends"): the crown no longer fades out softly where it nears the text
  corner (the patches are placed clear of it instead), the grass patches are lighter and fewer with no dark near
  corner, and the bridge is a flat crown easing down into long low ramps at both ends.
- **The daytime lighthouse with the harbor's boats (Josef: "a new version of the day lighthouse that takes the boats
  from harbor and put the cover next to the existing ones (not replace)").** Board `WCCoverLighthouse3` at the end of
  the lighthouse row, the same book ("Keeping the Light", Maren Holt). `art/watercolor/lighthouse_boats.py`: round
  1's lighthouse as it was (commit 5813d6b), plus the round 1 harbor's two wooden fishing boats in the open water on
  the left, kept out of the sea's glazes. After one Josef-eye critic round (the boats at full size pulled focus and
  looked pasted in), they are smaller and step back into depth, the big one near with a shorter mast and no stay, the
  small one beyond it; the hulls are a solid weathered blue-grey and a faded ochre, each with a soft shadow at the
  waterline. Fixes not re-reviewed.
  Then (Josef: "I think I liked the pre-critic pass on the boats"): the boats are back at the harbor's size and
  colours, with the mast's stay; and (Josef: "refine the house ... to be more like the harbor houses") the keeper's
  cottage is painted like the harbor's houses: a pale lit front, a cool shaded side, a terracotta tile roof in
  patches, an eave shadow, two small windows and a door. Round 1's lighthouse board is unchanged.
- **Beach recoloured (Josef: "less all-orange and more gorgeous", then "add some sunset illuminated clouds", then "a
  little less dark, a little more light and orange in the sky ... keep some violet but less night").** The sky now
  stops at the horizon (its washes had been running down over the sea and sand, which is what made everything
  orange): a soft violet top warming through coral to a high peach glow, a cream sun with a peach halo, and five
  long cloud banks of soft puffs, violet on top and lit coral and peach underneath, under the title on the left and
  higher only at the right edge. Below the horizon the light comes from the sky: deep blue at the horizon, slate
  blue, muted aqua only in the shallows, blush beside the sun's path, the path itself broken peach and rose-gold
  dashes; pale cream and pink sand with lavender shadows; the palms (same shapes) dark violet silhouettes. The title
  now takes the dark ink, 4.8:1. One Josef-eye critic round on the first recolour (the sea read as midday, the path
  khaki, the palms translucent), all applied; the clouds and the lighter sky came after it and were not reviewed.
- **Book screens for the beach and the daytime lighthouse (Josef: "now make the book screen for the beach and the
  updated lighthouse").** Boards `WCBookBeach` and `WCBookLighthouse`, each beside its cover in a paired row under the
  autumn row; the prairie cover (no book screen) one row below, the round 1, harbor and dusk lighthouse covers in the
  last row. Page art in `art/watercolor/pages2.py`. Beach: the soft violet dusk warming to coral and peach, two long
  cloud banks lit coral underneath and one higher on the right, a big half-sunk sun, a far mauve point of land, a
  small sailboat, the sea in slate-blue patches with the sun's path broken peach dashes, foam in broken runs, pale
  sand with lavender shade under two palms. Lighthouse: the cover's day scene wider, a pale cerulean sky with clouds
  left as paper, the headland climbing on the right with the white tower and its lantern (only its own shape kept
  from the sky, no paper box), the keeper's cottage and a shed painted like the harbor's houses, rocks and soft surf
  at the cliff's foot, the harbor's two boats at the cover's proportions, gulls, deeper water in front. One Josef-eye
  critic round, the boats and palms held as Josef set them; its fixes are applied (the far point made clearly land,
  the grass tufts replaced by soft shade, one cloud strip dropped; the surf soft and wet and clear of the small
  boat's bow, fewer ripples, a deeper near plane) and not re-reviewed.

## 2026-11-19: the book screen is B, the book opens (approved)

- **Josef approved book screen B** (`FreshReaderOpen`) and asked for it to go to implementation **without art**: the art
  inside the book and on the covers is still to be decided. The build spec is in `docs/design/system.md`,
  "Handoff: the open book (book screen B)".
- **Josef: opening is 3D.** Clicking a book on the shelf zooms in on it and opens it up in 3D. He wants a demo before
  anything is pushed, and will likely workshop it with the implementation session.

## 2026-11-19: three ways to show one book (the book screen)

- **Josef:** not yet sure how the book focus screen should work. Besides the full book page, two more UI approaches,
  one of them the current app's mechanic (the book opens to its pages) optimised and polished.
- **Canvas page "Fresh directions",** to the right of the strata row, under the note "Book screen":
  - **A, the book page** (`FreshBookStrata`): a page of its own with the book's landscape, the cover as a window
    onto it, the chapters below. Linkable and shareable.
  - **B, the book opens** (`FreshReaderOpen`): the current `BookReader` mechanic rebuilt. Title page with the art
    on the left, contents with one-line summaries on the right; choosing a chapter turns the page and moves the
    contents to the left page. Chapter tabs in the top bar, arrow keys, a lifted page corner. Ask to check out sits
    under the book, the same on every page. Round 2: the open book sits over the shelf shaded in dots, as in C,
    instead of the dark backdrop; the top bar and the button strip are paper.
    Round 3: the page keeps the library's header, and everything for the book is inside the book: Close and the page
    tabs as running heads, page turns at the feet, Ask to check out on the title page and under the contents.
  - **Josef removed "I have one like this" (sparks)** from the book screens (B and C). `docs/trove.md` still plans
    sparks (I5); that product change is the orchestrator's to make in the plan.
  - **Round 4, B built as a book** to be animated as paper: cover boards in the book's own ink, a spine at head and
    foot, stacked page edges, top pages bowing into the gutter (shaded in dots). No page feet (the tabs at the head do
    that job), no redundant page labels, and the shelf behind at 60% opacity.
  - **Josef's rule, from now on:** no explanatory sentences in the UI (such as "A thirty-minute video call, if the
    author says yes."). Good UI should not need a sentence for each interaction. Removed from B and C.
  - **Ask to check out is never under a chapter** (Josef: it reads as checking out that one chapter). In B it sits on
    the title page and under the contents on the left page, so it always belongs to the whole book.
  - **Josef removed C** (pulled from the shelf). The choice is now between A and B.
  - **Round 5, B made minimal for 3D:** each page is one flat plane carrying its own content, so a turn rotates the
    plane about the spine and the content moves with it. Under the pages, one board in the book's ink, the spine at
    head and foot, one sheet of page edge. The round 4 curves and stacked edges are gone.
  - **Round 6, strata art drawn for B** (`docs/design/art/strata/book_b.py`): composed for the title page, not cut from
    A's panorama. The page's text holds the upper left; the teal peak and sun climb the right edge, ranges step back
    to a hazy distance, a lake with reflections and an islet crosses the foot, groves frame both shores. The
    contents spread shows the same place from further back under the list and the button.
  - **C, pulled from the shelf** (`FreshReaderPanel`): a side panel over the shelf, which stays in place shaded in
    dots with the book's slot left open. Previous and Next step along the shelf; chapters open in place; a link to
    the full page (A).
- Generated by `docs/design/shelf/reader_boards.py`. Not decided: which one (or which mix) the app uses.

## 2026-11-19: typography for each cover direction, waiting for Josef

- **Josef:** adapt the typography on each cover so it looks polished and well rounded.
- **Done on the canvas page "Fresh directions"** (boards `Fresh`, `FreshLand`, `FreshNew`), in CSS on the live
  title and name, still only the three house faces. Each cover has its own setting:
  marbled paper, one bookbinder's label holding the centred title and the name under a short rule; letterpress, the
  name now tracked rule to rule under a heavy and a hairline rule (`press2.py`), so it reads on the shelf;
  block print, title and name centred on the block; gouache, the title in Barlow Condensed caps in the poster's navy
  and the name reversed out of a navy strip; coloured pencil, a lighter Newsreader in graphite with the name under the
  title; watercolour, Newsreader italic in the indigo of the washes, centred, name under it; cut paper, centred navy
  title and the name in cream on the dark paper at the foot; stipple, the title in spaced caps and three gold dots
  above the name. Titles use balanced line breaks.
- **Fixed-tier flag:** the book title is fixed as Newsreader 600 in ink, top left, and the name as Plex caps at the
  foot. These covers change face, weight, case, colour, alignment and the name's place. Needs Josef's yes before any
  of it goes into the app. The cover inks are art colours taken from each picture; none is the UI red.

## 2026-11-19: two more directions (cut paper, stipple) and three touch-ups, waiting for Josef

- **Josef:** the watercolour is too realistic, like a photograph, so it reads cheap; the coloured pencil is too
  simple; the gouache poster is too childish and its shapes too simple. Two new polished directions, and touch up
  those three.
- **Touch-ups, board `FreshLand`:** gouache round 2 (`gouache2.py`: an alpine lake drawn like a travel poster, with
  shaded peaks, streak clouds and framing pines); pencil round 3 (`pencil3.py`: deeper tones, a cabin and jetty, a
  far shore of firs, reeds, two more pencils); watercolour round 2 (`wash2.py`: the scene as single brushstrokes
  with bare paper between them, not a rendered view).
- **New, board `FreshNew`:** 7. **Layered cut paper** (`papercut.py`): the white cover is the top sheet of a stack,
  cut away to show the layers; moon, stars and window are holes to a glow. 8. **Stippled ink** (`stipple.py`): dots
  only, in two inks, the site's dot shading taken all the way.
- **Flag:** the cut-paper cover uses soft shadows between sheets. The system rule is dot tone for shade, never
  blur; that rule is about the UI, but Josef should decide whether cover art may break it.

## 2026-11-19: two landscape covers that clear to white (gouache, coloured pencil), waiting for Josef

- **Josef:** two more directions with environment art in different styles, edge to edge, that fade or cut to white
  so the title sits on white uninterrupted.
- **Canvas page "Fresh directions"**, board `FreshLand`, at 472 and 122 px wide:
  4. **Gouache poster** (`gouache.py`): dawn over a river town; the sky's top band ends in a hard cloud line (the cut).
  5. **Coloured pencil** (`pencil.py`): a farm road to a lit house; strokes thin out to bare paper (the fade).
- **Pencil, round 2 (`pencil2.py`):** Josef found round 1 interesting but childlike. Redrawn with four muted
  pencils, one hatching direction, tone from line density, crisp ridgelines that dissolve into paper, and one warm
  mark (a lamp and its reflection). The scene is now a lake at dusk. Round 1 (`pencil.py`) is kept for reference.
- **6. Loose watercolour (`wash.py`), added at Josef's request:** one wet-in-wet dusk sky over still water, its top
  edge drying ragged on bare paper. Unlike direction G (sun, three ridges, SVG filters) the sky is the subject and
  the paint is modelled as pigment on paper (pooled edges, granulation, backruns, dry-brush sparkle).
- **Title and name:** the title is the standard Newsreader title on plain white. The name at the foot sits on a
  white knockout over the art, as on the Strata covers.
- **Fixed-tier flag, waiting for Josef:** art on the white book object, as with every cover direction so far.

## 2026-11-19: three fresh cover directions (marbled paper, letterpress, block print), waiting for Josef

- **Josef:** pause the voxel covers. Three other directions tied to paper, books, drawing or painting, one cover
  each, each going somewhere different, thinking about what the site should feel like and what the visuals are for.
- **What the covers are for (my reading, for Josef to correct):** make what a person knows feel like a made object
  worth picking up; tell books apart on a shelf at 122 px; let a member express themselves by choice, never by
  status; stay calm beside the white UI and its one red action.
- **Canvas page "Fresh directions"**, board `Fresh`, each at 472 and 122 px wide on "The Night Shift Knows":
  1. **Marbled paper** (`marble.py`): a full sheet with the title and name on pasted labels. No two sheets match.
  2. **Letterpress** (`press.py`): the title in wood type is the picture, in two inks. Art comes only from the
     author's own words, which fits the grounding rule.
  3. **Block print** (`block.py`): a carved night scene in black and one second colour.
- **Fixed-tier flags, waiting for Josef:** all three put art on the white book object. Marbled paper covers the
  whole cover and moves the title onto a label. Letterpress replaces the Newsreader title with printed display
  type (the live title stays for screen readers). No cover ink is the UI red.
- **Open product question:** who picks what (palette, inks, scene), unchanged from direction H.

## 2026-11-18: cover direction H, round 3: back to Strata, solid and detailed, waiting for Josef

- **Josef:** the 3D voxel look doesn't work well. Go back to the Strata slabs and refine them with more detail and a
  more solid feel. The voxel page stays on the canvas for reference only.
- **Now (`docs/design/art/strata/`):** courses sit tight with no paper between them; each slab has a lit top edge, a
  shaded underside and occasional seams, so it reads as laid stone. Courses are finer (2px on the shelf, 1.5px on
  small books). New detail: strata bands on a peak, a pale far ridge for depth, water that mirrors the peaks above it,
  and groves standing on trunks. Mist pales slabs toward paper before any go missing.
- **Shown:** canvas page "Strata covers", board `StrataCover2`: design 1 ("the lake", `cover_lake.py`) at four sizes,
  and the seven other designs redrawn with the same renderer.
- **Still open:** the Fixed-tier yes for art on the book object, and who picks a design.

## 2026-11-18: cover direction H, round 2: voxel scenes (replaces the 2D Strata look), waiting for Josef

- **Josef on round 1:** too rough and basic. These are book covers, not page art: eventually dozens of designs
  members pick from, each leaving room for the title. Make it much closer to the reference, a 3D scene of small
  cubes, polish it, present a book design, and iterate until it is as good as the original.
- **Now:** the art is a real voxel scene rendered in Blender (`docs/design/art/voxel/`): about 96,000 slab cubes,
  a raking sun from the left, white sky, rendered on white. Design 1, "the valley", is on the canvas page "Voxel
  covers", board `VoxelValley`, at 472, 236, 122 and 92 px wide and on a shelf beside white books.
- **Cover layout:** the top third is empty sky for the title, the art sits in the middle, and the foot is white for
  the full name. Title and name keep white knockouts for long text at small sizes.
- **Still open:** everything listed under round 1 (the Fixed-tier yes for art on the book object, who picks a
  design). The Strata page stays on the canvas for reference.

## 2026-11-18: cover direction H, Strata (stacked-slab landscapes), waiting for Josef

- **Josef:** experiment with the stacked-slab landscape art from his references (mountains, water and trees built
  from horizontal bars), refined, on the cover and inside the book too, so the white UI lets the art be the hero.
- **Canvas page "Strata covers"**, boards `StrataBook` (one book opened: the cover is a window onto its landscape,
  which runs across the top of the book page), `StrataShelf` (nine covers on a shelf, one book at three sizes, how
  the art is made) and `StrataPlaces` (phone book page, the interview reveal, the checkout once the author says yes,
  the meeting waiting room). Source: `docs/design/art/strata/`.
- **Refined from the reference:** one course height per size (4px book page, 2px shelf) instead of mixed noise; seven
  ink families; light from the left with a clean shadow face; mist made by leaving bricks out, never blur.
- **Needs Josef's yes (Fixed tier):** the book object is "white, outlined, a dot shadow, title and full name only".
  Strata keeps all of that and adds art on the cover, so it changes a Fixed rule. Title and name sit on white
  knockouts where they meet the art.
- **Product questions for Josef, not decided:** who picks a book's landscape (the member, Trove, or the member from
  a short set); whether the reveal's three titles share one landscape or each gets its own; whether the art appears
  beyond the book page (checkout, meeting) at all.
- **Cover art is not UI:** coral (`#E87457` family) is the warm note and is not the UI red.

Pending Josef's feedback.

## 2026-11-09: close-out of the quality notes for the frames

- **Closed (R5-12):** the line under Chapters on the review and on My book now reads "“Show what you said” opens your own words behind
  each chapter. Only you see those." on every frame that carries it, matching the build. The old line called the public summaries private.
- **Everything else tagged Design in rounds 1 to 6 was already applied** to the frames (rounds 1, 2 and 4) or fixed in the build (round 5
  re-check); round 6 has no Design items.
- **Copy the build still owes, written here so it is built from one place** (both are UI items, not frame work):
  - R6-03: when words were left out for a name, say which ones: "I left this out because it named someone or somewhere: Geauga,
    County, Fair. Change those and I'll try again." "Say it again" opens the field with the member's words in it. My book uses the
    same sentence above the question panel.
  - R6-08: the undo question is one sentence for both kinds of change: "Undo these changes? Your book goes back to how it was."
    Add "I won't suggest them again" only when the changes were additions.

## 2026-11-08: quality round 4 applied to the frames (T40)

- **Interview A:** Shape now has two frames (field empty: the red Yes alone; correction typed: red "Send my correction" and a quiet "Yes,
  that's me, ignore this"); the exit link has a words-in-the-field frame ("Send this, then show me my book"); "Back to the question"
  replaces Continue / Continue later; "Saved" no longer sits beside an empty field. New board "A · Other states" draws not enough
  material, writing after a return, a failed load, answer saved but next question missing, the review after rewriting (go back to
  the last version; a rewrite that came back too close) and the other two titles. New board "A · Phone" draws start, reveal (title
  clear of the radio) and review (title, then book at small size, then back cover and stacked quiet links).
- **My book and the rest:** sparks list under the red button when no book exists (R4-06); finding titles and writing book states; undo
  copy with the date (R4-05); the reading caption is Plex 14px sentence case (R4-11); the wait and failed panels lose their headings
  (R4-12); a new chapter hides Now on phones (R4-13); "Nothing from these questions changes your book" (R4-08); a removal's back cover
  card says "Rewritten without this chapter" (R4-10); the back cover is always open and never underlined (R4-03); G4 note fixed (R4-15).
- **Samples (R4-18):** the back cover no longer ends "If you're…, I can tell you…", and sample questions ask one thing without "first".
- **CoverDirections:** it never held the old persona; its sample authors now show full names.

## 2026-11-08: quality round 2 applied to the frames (T39)

- **Applied:** R2-01 (a Removing change type; a back cover that fails says so on its own card, the old one stays, they can still
  confirm), R2-03 (a quiet "Undo these changes" on the done screen and on My book after an update; the book stores its previous
  version until the next change), R2-04, R2-05 (no "round" on screen: "For your next questions", "questions in progress"), R2-06 (the
  reading question is hidden on My book while questions or changes are open), R2-07 (the reason sits under the chip; on a phone
  Proposed only, with "See what's there now"), R2-08 (sparks listed in the interview-in-progress state; the start screen's extra
  line only when sparks exist), R2-09 (the spark control is a 14px sentence-case text link, no plus or tick), R2-10, the copy sheet
  (Changed chapter, "That's enough. Write the changes", a frame for words still in the field, shorter bands, the reading-question
  variant of "nothing came of it"), R2-11 to R2-15, R2-18, R2-23. R2-16 and R2-17 are in `system.md` Additions.
- **Not frame work:** R2-19 (slant on the built interview band), R2-20 to R2-22 are UI or API; nothing drawn changes. R2-02 is code.
- **Judgment:** the shelf line sits once in the proposed-changes note rather than twice; the plus mark on the spark control is
  dropped at that weight.

## 2026-11-08: the sample member is fully invented

- The earlier sample member was modelled on a real alum's news story. Replaced everywhere in the frames (`GrowingG1`, `G3`, `G5`,
  `InterviewA`) by Nora Valdez, an invented person with invented material of the same length: first-person chapters, a back cover,
  the three titles. Nothing in the frames comes from a real person.

## 2026-11-08: growing books and interview frames revised after quality round 1 (T37)

- **Applied from `qc/round-1.md`:** R1-04 (the back cover is a change like any other, written before the confirm step, with its own
  failed state), R1-32 (Remove this chapter on My book, confirm step), R1-33 (the note under the reading answer), R1-34 (the
  reading names the reader, to the author only), R1-36 (writing and failed states on My book and in the round), R1-39 (interview in
  progress and titles waiting), R1-40 (real-length text from a finished book, added words underlined), R1-41, R1-42 (Skip only
  while the answer is empty, with its own frame), R1-44, R1-45 (44px targets), R1-59, R1-60, R1-61, R1-62, R1-64.
- **Interview A also:** start screen (R1-18), review screen (R1-19, R1-21, R1-22, with Remove in place per R1-20), phase names
  First look, Deeper, Check (R1-28), done screen (R1-30). The sample member is now Nora Valdez, a fully invented person (pinball restoration, invented text of real length) so every frame uses real text.
  Directions B and C are left as drawn.
- **Design calls:** undecided changes count as not approved and are listed as "Not decided" under "Stays as it is"; "Not now" on the
  question screen goes back, "No thanks" on My book dismisses; one exit per screen; "the shelf has not changed" once in the band and
  once on confirm. Route is `/my-book`.

## 2026-11-08: growing books frames (T33), under the suspended gate

- **I4 frames go to build as they stand** (`InterviewA2`: Skip, sharper angle). Josef suspended frame approval for the
  unattended run, so this is not an approval of the frames. He reviews the built screens afterwards.
- **T33 frames drawn** on the new canvas page "Growing books", five boards, desktop and phone: My book (no book, draft, on the
  shelf, a round open, changes waiting), adding to your book (reopen, a question with Skip, the wait), proposed changes
  (decide, confirm, confirm with nothing approved, done, nothing came of it), "I have one like this" (every state, in three
  unrelated rows), the reading question (ask, the wait, one proposed change). New patterns in `system.md` Additions.
- **Design calls:** Approve/Decline is a toggle pair that fills ink, never red. The confirm step lists titles by group with no
  numbers. The reading question sits beside the book on My book as a quiet panel; Answer is secondary so the one red action
  stays the book's next step. The wait has no spinner or bar. A round that yields nothing says so and returns to My book.

## 2026-11-07: I4, Skip idea approved; frames under review

- **Josef approved the Skip idea only.** The `InterviewA2` frames (Skip, CHEM 223 angle, student-org angle) are drafts under
  his review and are not approved yet.

## 2026-11-07: "Skip" replaces "Ask me another way"

- **Josef (spec b0aa08d):** the button is "Skip". It goes straight to the next question, for one the member would rather not
  answer or has nothing to say to. Quiet, beside Speak, never red. Skips are never shown or counted: no "skipped" state and
  no tally. Frame 1 of `InterviewA2` shows it; the change-of-angle frames stay, with Skip in the action row.

## 2026-11-07: the interview adapts (I4), revised after Josef's review

- **First draft dropped (e46fe34, six frames):** the mirror ("feels like flattery"), the situation cards and "Help me find
  it" with its "last Saturday" question. Josef: don't design for scared people; these are professionals; help them with
  better questions, not easier ones. Spec: trove.md §4 and §9.9 (7289adb).
- **Now three frames on `InterviewA2`:** "Ask me another way" (quiet, beside Speak, on every question; red stays on Send
  answer), and two frames of the change of angle: a sharper question on the band anchored in a real context ("In your CHEM
  223 project, what did you have to figure out that the lab manual didn't tell you?"), then the same pattern in another
  context (a student org). The screen is identical whether the member pressed the button or the answers ran thin, so
  nothing marks them as struggling. No reassurance or praise anywhere.
- **Copy check of direction A:** removed "Take a moment with each" (reveal) and "as you would to a friend" (recording).
  Everything else is plain and direct. Not approved yet.

## 2026-11-07: books show the full name

- **Orchestrator, after Josef talked to the advisor (ce8f005, trove.md §3 and §9.1):** a book shows the author's full name,
  not just the first name. Nothing else from the résumé (no headline, employer, genre or count).
- **Fit:** the name stays Plex 600, 9.5px, caps, +0.12em, now at line-height 1.3. It wraps (also at a hyphen) and stops at
  3 lines with an ellipsis. "ALEXANDRA OKONKWO-BRENNAN" takes 3 lines on the shelf and small books, 2 on the large one
  (measured in the app with real fonts; the first canvas check said 2, 3, 1). The aria-label carries the whole name. Updated in system.md, tokens.css and the design-system boards.

## 2026-11-06: interview screens (T5), three directions

- **Orchestrator T5:** static desktop screens for the interview in the manga system, three directions, nothing on hold
  drawn (no margin notes, bursts, card drawer, bookmark tabs, pencil-to-ink spine, stamp or live filler cleanup).
- **New canvas page "Interview"**, boards `InterviewA`, `InterviewB`, `InterviewC`. Each shows nine frames: start,
  question (typing, recording, transcript, later in the Dig with the exit link), shape moment, reveal (three white-cover
  titles), book review, coming back. A: the question on a black band. B: a literal comic page (see below). C: speech bubble on a screentone ground, phase as a top rail.
- **Rules kept:** first names only, no counts or percentages, phase as a label (Sweep, Dig, Shape), "Saved" tiny and
  silent, one red action per screen (Stop while recording), halo dots never behind running text.

- **Josef: replace B with something more literally comic.** B is now "Comic page": every screen is a page of
  heavy-bordered panels on white gutters, narration caption boxes (The Librarian, You, What I heard, Previously), the
  Librarian's question in a speech balloon on a screentone panel, the member answering from a balloon. Phase is a
  tag in the page header, the reveal is three cover panels, chapters are panels.

**Chosen: direction A (the question band).** B (comic page) and C (speech bubble) stay on the canvas for reference.
Build spec: `docs/design/shelf/project/InterviewA.dc.html`, ten frames at 1280x800.
- **Done frame approved as drawn** ("Your book is on the shelf.", "Go to the shelf", quiet "See my book").
- **Resume frame:** "Start that part again" is removed. It now has "Continue" (red) and a quiet "Continue later", which
  leaves the interview.

## 2026-11-06: cover direction G, watercolor landscapes (from Josef's reference)

- **Josef:** use the reference (red watercolor sun, blue misty ridges, reflection) as the art style for the book
  covers, three covers, and not only Japanese.
- **Board `CoverLandscape`** on the Covers page: `Alpine lake` (vermilion sun, blue ridges, pines), `Headland`
  (amber sun, teal sea, lighthouse, sailboat), `Mesa` (gold moon, terracotta mesas, rain pool, saguaros). No torii,
  bamboo or characters. Same system for all: title on white at the top, a large sun or moon, three layered ridges
  that thin into mist, a rippled reflection, a gradient mask to white under the title, paper grain.
- **Personalization:** the member picks the place and palette, never the topic. The scene set can grow.
- **Cost note:** SVG filters again; render each cover once to a 244x356 WebP.
- **Cover art is not UI:** the lake sun is a vermilion (`#E4442E`) close to, but not, the UI red.

Pending Josef's feedback.

## 2026-11-06: cover direction F, cherry blossom watercolor

- **Josef:** a cherry blossom watercolor cover: paint over the white cover that fades upward with no cut between the
  title area and the picture. Polished and beautiful.
- **Board `CoverWatercolor`** on the Covers page. A pastel two-color wash, a plum branch, layered blossoms and
  drifting petals, masked to white by the title; five palettes (sakura, wisteria, apricot, rain, matcha), mirrored
  branches and a seed per cover. Build steps are shown. Titles take each palette's dark color (AA on white).
- **Cost note:** the art uses SVG filters, so render each cover once to a 244x356 WebP instead of live on the shelf.


## 2026-11-06: cover directions, round 1

- **Josef:** explore the book cover. White ground for contrast, title at the top, titles can carry color, art
  from Japanese art forms, personalized by choice (not by what the book says), designed for the size it shows at.
- **New canvas page "Covers"**, board `CoverDirections`: five directions, each shown at 236x344, 122x178 (five
  variants) and 92x136: A seigaiha waves, B sumi-e bamboo wash, C sashiko stitched cloth (asanoha, shippo, kikko,
  yabane, uroko), D kamon crest, E ukiyo-e Fuji with bokashi sky.
- **Cover rules in the exploration:** title top in Newsreader 600 in the cover color (all cover colors have AA
  contrast on white and avoid the UI red); art in the lower 36%; first name at the foot; vector art so it is sharp
  at 2x (244x356); no Japanese characters. Cover art needs a Fixed-tier decision before joining system.md.

Pending Josef's pick (one, or a mix).

## 2026-11-06: the design system (Manga screentone), and the docs enforce it

- **Chosen:** manga B2 (top navigation, B's banner and shelves, the red framed button) is the reference screen.
  Black ink on white paper, dot tone for shade, one burst, one red for the primary action only.
- **New canvas page "Design system":** the reference shelf and a sign-in screen, then Foundations, Components
  (actions and forms; content and structure) and How to use it. Authoritative rulebook: `docs/design/system.md`.
  Reference CSS: `docs/design/system/tokens.css`.
- **Red changed to `#D42A27`** so white text passes AA (5.0:1).
- **Balance:** rules sit in three tiers: fixed (human's yes), defaults (follow or explain), free (design new
  things, record them under Additions). CLAUDE.md, CONTRIBUTING.md, architecture.md and plan.md now point to it.
- **Not done:** `web/src/ui/styles.css` still has the old placeholder tokens. UI Implementation ports
  `tokens.css` into it (the old `--color-*` and `--space-*` names are aliased, so it is a drop-in).

## 2026-11-06: identities, pick a craft idea before the layout

- **Josef:** C (circulation desk) has a real identity but feels too simple. Decide the material, pattern and
  craft idea first, then the layout. Explore printed media across eras and art styles (text, cartography,
  literature) as small mood boards.
- **New canvas page "Identities"**, six boards (`Ident1`..`Ident6`), each with a plate, what we borrow,
  palette, type and a shelf fragment with white books: 01 four-colour pulp (comic halftone), 02 survey
  chart (nautical cartography), 03 banded paperback (1930s-60s Penguin-style grid), 04 wood-type
  broadside (letterpress), 05 riso zine (two-ink overprint), 06 engraved plate (natural history).

- **Round 2 (Josef: 03 too basic, 04 ugly):** replaced 03 with bookcloth and foil (woven navy cloth, gold
  foil stamping, ribbon marker, marbled endpaper) and 04 with cyanotype blueprint (drawing sheet, dimension
  lines, title block, one amber). Polished 01 (comic panels and gutters), 02 (soundings, shallows, cartouche,
  scale bar), 05 (registration marks, test strip, halftone) and 06 (second row of specimens, scale bar).
  Every board now has a Textures row, a layer to mix and match across identities.

- **Round 3 (Josef: not 03 and 04):** replaced them with other countries' comic textures: 03 manga
  screentone (Japan: dot tones, focus lines, slanted gutters, one red hanko seal) and 04 ligne claire
  (Franco-Belgian: even line, flat colour, brick and roof-tile patterns, flat shadows). Bookcloth and
  cyanotype are dropped.

- **Round 4 (Josef: 04 ligne claire looks like kindergarten):** replaced 04 with Bauhaus primer (1920s German
  design school: circle, square and triangle in vermilion, ochre and Prussian blue, overprint, lowercase
  Jost, one diagonal black bar for the call to action, a visible grid). Textures: overprint, concentric arcs,
  quarter tiles, rule and bar. Ligne claire is dropped.

- **Manga screens (Josef: pick manga screentone, no Japanese letters):** new canvas page "Manga screens",
  three desktop layouts of the shelf page, all Latin type only (Barlow Condensed, Newsreader, Plex), no
  hanko character, one red square used only for the main action: `MangaA` the page (slanted-gutter panels,
  focus lines behind the Librarian pick), `MangaB` the strip (black rail, one dark band, long shelves on
  inked ledges), `MangaC` the spread (open book: pick and contents left, two shelves right, index tabs).

- **Manga B polish and B2 (Josef: polish B, add a version under it with navigation up top like A):** B's banner
  is now a black band with a slanted lower edge and a double rule, a dotted halo and fanned lines behind the
  book, a larger title, a ruled reason line and a "thirty-minute video call" note. `MangaB2` keeps B's banner
  and long shelves but moves the navigation to the top bar, as in A, so the shelves get the full width
  (nine books a row). B's side rail stays on `MangaB` for comparison.

- **"Ask to check out" button (Josef: too decorative, red at rest):** `MangaBtn` shows four flat red buttons with
  rest, hover and pressed on the dark band and on paper: flat red, red with an ink frame, red with a plain
  arrow, and red with Plex sentence-case type. No shadows, tilt or texture. Red stays reserved for this one
  action on any screen.

- **Button chosen:** option 2 (red, thin ink frame; white frame on the dark banner) is now on `MangaB2`.

Pending Josef's pick (one, or a blend).

## 2026-11-06: direction 5, working tool (a clean break from the material looks)

- **Feedback:** the marble, cloth, shadow and daylight directions all read as games or toys. Trove is
  professional software and should feel mature and considered. Start over.
- **Now:** a neutral white and gray interface with one deep blue (#17406B) for the single main action,
  IBM Plex Sans for the interface and Newsreader only for book titles. Left sidebar (Shelf, My book,
  Checkouts, Past meets), a small topic search in the top bar, a quiet Librarian recommendation row,
  shelves as rows of books standing on a thin ledge, and a persistent detail panel on the right
  (chapters, Ask to check out). No decoration, no texture.
- **Books are plain white** (spine hinge, page edge, soft shadow) until Josef settles the cover design.
- New canvas page "Working tool": `ToolShelf` (interactive), `ToolPhone`.
- Josef: "structure and layout are right, but boring and basic." Two static desktop options added to the
  page for character, energy and warmth: `ToolDark` (B, after hours: dark ink room, amber lamplight on
  white books, a 3D-tilted Librarian pick) and `ToolCirc` (C, circulation desk: ink rules, highlighter
  yellow, stamp blue, mono labels, index-card recommendation).

Pending Josef's review.

## 2026-11-06: direction 4, daylight library (from Josef's photo of a Scandinavian library)

- **Reference:** a pale-wood Scandinavian public library: curved ribs overhead, tall arched windows
  with slender slats, low slanted display units with books face out, sun striping the room.
- **Feedback on the first attempt:** it copied nothing of the photo (stepped blocky units, huge empty
  areas), had no real light, and the brown read greenish. Rebuilt.
- **Now:** honey and peach birch (never beige or olive), gold-white daylight, a vault of diagonal
  ribs as the header, two arched windows (the Librarian's pick stands in the first), full-width
  slanted shelf units with six books each, and diagonal stripes of sun across the whole page. Dense
  by default: no staggered empty steps.
- **Search is a small field in the ceiling.**
- Artboards on the Designs page, row 5: `ScandiPage` (interactive), `ScandiPhone`, `ScandiNotes`.

Pending Josef's review.

## 2026-11-05: back to layout, in black and white

- **None of the Carrara, light-and-shadow or cloth-and-oak looks is the one.** They stay on the
  canvas's first page ("Designs") for reference.
- **Start from form only.** New canvas page "Wireframes": four black-and-white layouts of the shell
  homepage, plain shapes, no material or color: `WireA` (feature, then shelves), `WireB` (side
  rail), `WireC` (bookcase), `WireD` (black split).

Pending Josef's pick.

## 2026-11-05: direction 3, the Carrara page

- **Chosen: option A, the polished white Carrara ledge.** B and C stay on the canvas for reference.
- **Keep the marble shiny and thick,** a little thinner than the study (front edge 50px down to
  42px). Thickness is a tweak on the artboard (slim, regular, thick) for Josef to try.
- **Experiment with reflections:** the books mirror into the polished top, and a lifted book's
  reflection drops away from it. Strength is a tweak (off, soft, mirror).
- **Bring in the light and shadow work from direction 2:** one light from the upper left, depth
  with meaning (carved nav and search, raised buttons, the open book held over the wall), and
  window light only on the Librarian's pick.
- **Search lives in the header,** small. The page opens on the Librarian's pick.
- Artboard: `MarblePage.dc.html`, row 4 of the canvas.

Pending Josef's review.

## 2026-11-05: direction 3 (marble)

- **Search is never the main element of the shelf page.** Making the search bar the hero repeated
  FoundersCircle, which the team disliked. Search stays available but secondary.
- **Direction 2 (light and shadow) is not the one** either; it stays on the canvas for reference.
- **New idea: marble is the material of the shelves.** First step: one shelf with a few books, in
  three options, before any full page. Third row of the canvas: `MarbleA` (polished Carrara
  ledge), `MarbleB` (green marble niche), `MarbleC` (honed pink slab with arch and cube bookends).

Pending Josef's pick.

## 2026-11-05: the shelf page, direction 2 (light and shadow)

- **Direction 1 (cloth and oak) is not the one.** It stays on the canvas for reference.
- **Avoid the tells of AI-made design.** The list is in `docs/design/ai-tells.md`. It guides
  choices without banning basic elements.
- **New direction: shadow is the star.** Very minimal, mostly warm whites; light and shadow
  carry the structure. Slightly retro, slightly Bauhaus, sparing with color. Functional, not a
  gimmick: every depth means something (carved, wall, resting, lifted, held, pressed).
- Built as the second row of the same canvas: `ShadowShelf`, `ShadowPhone`, `ShadowSystem`.

Pending Josef's review.

## 2026-11-05: the shelf page

- **Rejected:** the three poster-style directions from T1 (flat SVG-like covers, layouts designed to
  be looked at rather than used). Removed from `docs/design/`; they're in git history at `bc87a6f`.
- **Start from the user and the interface,** then the look. The shelf is a working screen: search a
  topic, browse, open a book to see its chapters, ask to check it out.
- **One direction only,** polished, built as a canvas of screens rather than a single HTML page:
  `docs/design/shelf/` (published at https://claude.ai/artifact/33uQU8UKZ4gtxcv4ZNof1D).
- **Books are objects, between 2D and 3D.** They have depth, light and shadow and must run efficiently in a
  browser. The design fakes the depth in CSS; the 3D build belongs to UI Implementation, using the
  book object artboard as the spec.
- **Feel:** modern, but serif and library-like, in warm colors.

Pending Josef's review of the new canvas.

## 2026-11-23: brand, round 1 (logo and identity)

- **Josef asked** for a logo and the whole brand identity on a new canvas page, starting from the mission and the
  feeling, then ideas, critique, and three kept. New page **Brand**: `BrandThink` (mission, feeling, what any mark
  must do, twelve ideas with a verdict each) and three identities, each with hero lockups on paper and ink, the mark
  from 220px to 16px, app icons, browser tabs, construction, colour and type, the top bar, and marketing (poster,
  Instagram post and story, email header, a handout or merch) plus three headlines.
  - **A · Bookmark:** a book's edge with a ribbon hanging from it, which is also the T. Wordmark Trove in Newsreader
    600 on a rule with the ribbon slipping out under it.
  - **B · Facing pages:** an open book whose inner page edges are two profiles face to face; the spine is the gap.
    Wordmark lowercase italic Newsreader.
  - **C · The blank cover:** the app's own book object (outline, hinge, dot shadow) with an untitled cover; below
    48px the shadow drops and the hinge and title bar thicken. Wordmark Barlow Condensed 800 caps.
- **Rules the marks keep:** ink only, never red (red is the one action); square; dot tone for shade; the brand is ink
  and paper, and marketing borrows colour from real covers rather than inventing a brand hue.
- **Critic round** (fresh subagent): fixed the clipped Voice rows, C's copy-icon look at small sizes, the speed lines
  in C's story (now a dot field), harsher B profiles (redrawn softer), the gap under A's ribbon, a deeper swallowtail,
  C's shelf post now uses the mark's own cover, a smaller red swatch, and copy that invented product (a bookmark
  feature, a call length, naming two members who met). Not taken: the critic wanted the search pill and round avatar
  squared, but the system allows exactly those two pills; it wanted C's wordmark in Newsreader, kept in Barlow so the
  three directions differ in voice. Its pick was B, after a hand-drawn pass on the profiles.
- Source: `docs/design/shelf/brand_boards.py`.

## 2026-11-23: brand, round 2

- **Josef:** none of round 1 ("all of them are too basic"); new fonts are welcome, and the site's fonts may switch to
  move away from the AI-generated look. Round 2 sits under round 1 on the Brand page: `Brand2Think` (why round 1
  was basic, the faces we'd leave: Inter, Space Grotesk, Fraunces, Instrument Serif, and today's Plex and Barlow)
  and three identities, each with a made thing at the centre, its own typefaces, and the shelf retyped in them.
  - **A · The Magpie:** Trove as the publisher of unwritten books, with a colophon: a linocut magpie (wedge tail,
    gouge cuts) on a closed book, in an oval with TROVE and CLEVELAND · MMXXVI. On dark grounds the bird stays black
    on a cream plate. Gloock, Literata, Hanken Grotesk; ink, warm paper, a blue-green tail sheen.
  - **B · Overprint:** riso teal and yellow; two books leaning together overprint green, and the wordmark is printed
    in both inks so the overlap shows. Big Shoulders Display (Chicago civic signage) and Libre Franklin. The
    Librarian's band is newsprint so the red button sits on a calm ground.
  - **C · Wet Ink:** an open book of two watercolour washes, painted with the cover engine
    (`art/watercolor/brandmark.py`, transparent PNGs), the overlap a darker lens at the spine; a flat two-colour
    version at 32px and below. Libre Caslon Display/Text and Schibsted Grotesk; blue-black ink. **Product question,
    shown only as a proposal:** a mark painted per member from their own cover.
- Every site mock keeps red only for "Ask to check out".
- **Critic rounds:** two. Fixed a percentage-padding bug that stretched the shelf covers; bylines now match the
  covers; the colophon's lettering got its own channel; the magpie was redrawn (wedge tail, cuts, chunkier book)
  and small sizes cropped tight; B moved off Bricolage (itself a startup default) and off blue-and-yellow (a flag);
  C's mark was repainted as a gull-wing open book; invented features and job titles were taken out of the copy.
  The critics split: the first picked C, the second A.
- Source: `docs/design/shelf/brand2_boards.py`.

## 2026-11-23: the dusk lighthouse's beam and book screen; the city bridge; the winter firs

- **Beam (Josef: "add a beam of light from the lighthouse at dusk").** `covers.lighthouse`: the beam is lifted out of
  the wet sky (paper showing through, not yellow laid on blue), a narrow core in a wider glow, broken in patches,
  dipping toward the sea and fading before the left edge, just under the title; warm only near the lamp; a short stub
  on the right. Cream title still 6.1:1.
- **Book screen ("then make a book screen for it").** `WCBookLighthouse2` beside the cover, both moved to a new row
  (y 13200); page art `pages2.lighthouse_dusk`: the cover's dusk wider, night gathered round the tower so the beam
  has a dark sky to cut through, the beam at the cover's angle and spent inside the blue, stars, lit cottage, flat
  bottomed rocks lit top-left. Same book text as the daytime lighthouse.
- **City page ("make the bridge go all the way to the right side").** The deck, piers, arches and lamps run edge to
  edge; the spans widen toward the right so it isn't a picket fence.
- **Winter cover ("the bottom of the trees are kind of weirdly translucent").** Each fir is lifted to paper and given
  one even dark ground before its patches, so it is as deep in the snow as against the sky; snow lifted over each
  foot and a violet shadow thrown right.
- Critic round: one (beam airbrushed and muddy, page beam a stain, a star on the beam, smudge rocks, even arches,
  skirt-like bottom tiers); all fixed. Checked in local renders, not on the live canvas.

## 2026-11-23: brand 2C (Wet Ink), typography and marketing refined

- **Josef: "refine the typography and marketing for 2C, keep the logo".** The painted mark is unchanged.
- **Wordmark tuned:** the T–r gap closed by 5.5% and the word tracked −1.2%; a stacked lockup with the tagline "the
  book you haven't written yet" in Caslon italic under a hairline as wide as the word; rules for clear space
  (the o's height), smallest sizes and colour.
- **Type system:** seven jobs (Display 72, Page title 44, Section 30 in Caslon Display; Voice 21 italic and Reading 17
  in Caslon Text; Interface 15 and Label 12 caps in Schibsted Grotesk), plus book-typography rules: old-style
  figures on, real quotes and dashes, italic not bold for emphasis, caps only for short tracked labels.
- **Marketing as one campaign:** three posters on one grid (headlines anchored up from a shared footer, each in a
  different colourway of the mark), a three-slide carousel, a 9:16 story, an email, a bookmark, a launch invitation
  with placeholders, and a tote. The per-member mark is no longer shown as a proposal; the colourways are campaign
  colourways.
- **Critic round:** one; fixed folios, the slide-3 rules, the quote's attribution, the bookmark rag, the invitation's
  missing wordmark, the email's ground and body face, the tagline's width, poster double branding. Kept against it:
  "A thirty-minute video call" beside the button in the site mock, as the design system's shelf spec has it.

## 2026-11-23: dusk lighthouse, stars on the cover and a lighter page top

- **Josef (relayed by the stipple session):** "like the dots in the night sky. Add them to the book cover as well a
  little bit, but reduce the amount of darkness up in the top part of the book screen for the lighthouse, since the
  text is then hard to read." Cover: nine lifted pinpricks of stars, clear of the title, the name and the beam
  (cream title still 6.1:1). Book screen: the sky climbs less high on the right (bleed climb 320 → 250), its top
  wash is lighter, the dark round the tower smaller and lower, and the stars moved down into what dark remains.
  Checked in local renders only.
