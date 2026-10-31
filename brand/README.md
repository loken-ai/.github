# LOKEN brand assets

**LOKEN**, from **Lo**cal + tok**en**: a local inference server for AI models.

## The mark, the word, the banner
| Asset | What it is | Where it goes |
|-------|------------|---------------|
| **Icon** | The mark on a dark square tile | App icon, favicon, org avatar |
| **Wordmark** | The word *loken*, written | Anywhere the mark is already present |
| **Banner** | Mark, word and line on a dark panel | Every page header, in either theme |

The mark is an open box seen in isometry: the floor and the two far walls are white, the
outline fades toward the back, and the front is left open. Inside sits a block of 8 tiles, grown to fill the box,
and the tile the kernel is working on stands raised and takes the mint. The box is the machine,
the tiles are the work, and nothing crosses the boundary.

The word is written with a broad nib in one gesture. It is a mark, not a spelling: in text,
write **LOKEN** (and `loken` for technical names: the org, crates, repos). It is never reduced:
below about thirty pixels its thin strokes vanish, so the favicon and the avatar take the mark
alone.

The banner carries the line `SELF-HOSTED MULTIMODAL INFERENCE`, what loken is in three words,
set in geometric capitals: the line belongs to the mark, not to the writing.

## Palette
| Role | Hex |
|------|-----|
| Box outline, mixed toward the ground with depth | `#3B6FE0` |
| Tile: top, right, left face | `#12A8B6` `#0C8794` `#0A6B76` |
| The kernel's tile | `#34D399` `#25B584` `#1B9068` |
| Box faces and tile outlines | `#FFFFFF` |
| Ground | `#0B1020` |
| Written word | `#14161C` on paper, `#F2F4F8` on dark |
| The banner line | `#888888` |

## Files
- `icon.svg`, `favicon.svg` (full-bleed, for small sizes), `icon-mono.svg` (one ink)
- `wordmark.svg`, `wordmark-dark.svg`: the written word, for paper and for dark grounds
- `banner.svg`
- `png/`: `icon-{512,256,180,128}.png`, `favicon-{48,32,16}.png`, `favicon.ico` (16/32/48),
  `icon-mono-512.png`, `wordmark.png`, `wordmark-dark.png`, `banner.png`; `lockup.png` is a
  copy of the banner, kept for READMEs published before the rename
- `png/avatar-512.png`: the **org avatar**. Square to the edge, no rounding of its own:
  GitHub puts the avatar in its own container (square, rounded, or circular depending on the
  surface), so a rounded source would read as a double round and its transparent corners would
  take the colour of the page. Upload it under *Settings, Profile, Upload new picture*.
- `../profile/`: `icon.png` and `banner.png`, the org profile images, copied by the same run
- `components/`: the 7 component icons and favicons, described below

## The components
Each component wears the mark of the server with 2 changes.

- The frame and the raised tile take the hue of the component. The block stays teal.
- The big left face of the block becomes one dark screen. The glyph of the component is drawn on it in the hue of the raised tile, laid in the plane of the face.

| Component | Hue | Glyph |
|-----------|-----|-------|
| loken | mint, the original | none, the grid of tiles stays |
| lokraft | 265 degrees, violet | chat bubble |
| lokode | 40 degrees, amber | prompt |
| lokprof | 8 degrees, coral | stopwatch |
| benchmarks | 85 degrees, lime | 3 rising bars |
| lokpit | 325 degrees, magenta | 3 linked nodes |
| alma | 205 degrees, sky blue | sound wave |

A hue is the hue of the original colour turned to the angle, with its lightness and saturation kept.

The favicon of a component is a separate flat drawing. A solid hexagon in the hue carries the glyph cut out in the ground colour. The favicon of loken is a flat cube, its 3 faces in the tile colours and the kernel's tile on top. The isometric mark loses its glyph below 32 px, and the flat one keeps it down to 16 px.

Files, in `components/`: `<name>.svg`, `<name>-favicon.svg`, and in `components/png/` the icons at 512, 256 and 128 px and the favicons at 48, 32 and 16 px. `components/loken.svg` is `icon.svg`.

The block of the server mark is drawn at 1.3 times its first size about the centre of the box. That is the largest size that stays inside the outline, and `BLOCK_SCALE` in `gen.py` holds it.

## Generating
`_work/gen.py` is the single source: `python3 gen.py`. The box, its tiles and the written word
are geometry written once there; the SVGs are emitted from it and the PNGs are rasterised from
those SVGs with [resvg](https://github.com/linebender/resvg), which must be on `PATH`. The
banner line is traced from a system font to outlines at generation time, so no asset contains
text or depends on a font where it is displayed.

Four things are derived rather than typed, and each one replaced a rule that had to be written
by hand and was wrong twice:

- **the drawing order.** Every tile face carries the depth of its cell, and the whole mark is
  sorted by it. Classifying edges as front or back by hand put the frame over the tiles once,
  and under them the next time.
- **which edges are drawn.** The three edges meeting the corner nearest the viewer are left
  out: they are the only ones that would cross the contents. The rest never do, so each is one
  stroke rather than a run of segments.
- **the depth cue.** An edge's colour is the outline mixed toward the ground by its depth,
  rather than an opacity. Two translucent strokes meeting at a vertex add up, which made every
  join darker than the edges that formed it.
- **the centring.** The mark's ink box is centred on the tile with its larger side at the
  extent (`100` on the tile, `112` full-bleed), so the four margins are equal by construction.

## Verifying
`_work/verify.py` after any change. It checks the structure (no text or font, the palette of
the flat fills, three walls and eight tiles, nine edges, a single kernel tile, a genuinely
monochrome one-ink cut, every raster size, the mark centred, legible at 16 px, and
`icon-512.png` being `icon.svg` rasterised), the letter counters (S, C and G have none, O and D
have one), and two properties of the drawing measured on the render itself:

- where an edge crosses a tile, the pixel must belong to whichever of the two is nearer;
- at each visible vertex, the pixel must be the colour the depth model gives, so no join is
  darker than the edges meeting there.

For each component it also checks:
- the enlarged block, raised tile included, stays inside the box
- the icon has 3 walls, 8 tiles, 9 edges, one screen and one raised tile in the hue
- its flat fills stay in the palette and the mark is centred on the tile
- the favicon is flat and survives at 16 px with its glyph cut out
- the 7 favicons differ from each other at 16 px
