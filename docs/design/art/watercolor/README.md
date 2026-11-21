# Watercolor covers

A second cover series (Josef, 2026-11-21: "a new page and we will slowly make 10 watercolor theme books, make the
first three and obsess over them, only covers, not book screens yet"). Shown on the canvas page "Covers: Watercolor".

Illustrated watercolour, not a photograph (an earlier photographic wash was rejected as reading cheap) and not
abstract strokes: a clear subject built from transparent glazes, wet-in-wet skies, pooled hard edges, granulation,
and bare paper doing every white. Same cover object and type as the strata set (the 176 x 257 shelf book, the narrow
hinge, the poster type with the name under the title); the name's knockout takes the paper's warm off-white.

| File | What |
|---|---|
| `paint.py` | The engine: pigment glazed onto cold-press paper (Beer-Lambert glazing, two-scale ragged edges, pooled rims, uneven settling with faint backruns, granulation, dry brush, lifting, wet-in-wet softening, `loose()` for building any shape from overlapping wet patches like foliage) |
| `covers.py` | The covers: `lighthouse`, `harbor`, `autumn` (`python3 covers.py [name ...]` -> `out/<name>-xl.png` 944 x 1376 and `-sm.png`) |

Layout rule as for strata: the title and name sit on bare paper at the top; left of world x ~200 the paint stays below
y ~180, only the right edge rises higher.
