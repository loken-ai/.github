# LOKEN brand assets

**LOKEN**, from **Lo**cal + tok**en**: a local, multimodal, energy-aware inference engine.

## The mark and the wordmark
Two assets with two roles, never composed into a lockup.

- **The mark** is the square: a looped **l**, written with a broad nib on the indigo tile. Its
  exit stroke does not end in ink: it is emitted as four tokens, each smaller than the last,
  and the second one is lit in emerald. It is the icon, favicon and avatar.
- **The wordmark** is the word *loken* written with the same nib, in one gesture. Its exit
  stroke is emitted as the same four tokens, with the same one lit. It heads READMEs and pages.

There is no tagline. In text, always write **LOKEN** (and `loken` for technical names: the
org, crates, repos).

## Palette
| Role | Hex |
|------|-----|
| Indigo (tile, ink on paper) | `#3730A3` to `#312E81` |
| Emerald on the tile and on dark grounds | `#34D399` |
| Emerald on paper, one-ink cut | `#059669` |
| Ink on dark grounds | `#ECEBFA` |

## Files
- `icon.svg`: primary mark on the indigo tile
- `favicon.svg`: full-bleed mark for tiny sizes
- `icon-mono.svg`: one-ink cut; the lit token takes the same ink, without its halo
- `wordmark.svg`, `wordmark-dark.svg`: the written word, for light and dark grounds
- `png/`: `icon-{512,256,180,128}.png`, `favicon-{48,32,16}.png`, `favicon.ico` (16/32/48),
  `icon-mono-512.png`, `wordmark.png`, `wordmark-dark.png`
- `png/avatar-512.png`: the **org avatar**. Square to the edge, no rounding of its own:
  GitHub puts the avatar in its own container (square, rounded, or circular depending on the
  surface), so a rounded source would read as a double round and its transparent corners would
  take the colour of the page. Upload it under *Settings, Profile, Upload new picture*.
- `../profile/`: `icon.png`, `wordmark.png` and `wordmark-dark.png`, the org profile images,
  copied by the same run

READMEs pick the wordmark by theme with a `<picture>` element and a
`prefers-color-scheme: dark` source.

## Generating
`_work/gen.py` is the single source: `python3 gen.py`. Every stroke is a path written once
there; the SVGs are emitted from it and the PNGs are rasterised from those SVGs with
[resvg](https://github.com/linebender/resvg), which must be on `PATH`. No asset contains text or
depends on a font.

A stroke is drawn as a broad nib at a fixed angle dragged along its path, plus a narrow
crossing nib that keeps the hairlines from vanishing. The sweep is emitted as quads between
neighbouring samples, all wound the same way, so a nonzero fill paints their union exactly.

Two things are derived rather than typed:

- **the centring.** The mark's ink box (stroke and tokens; halos excluded) is centred on the
  tile, with its larger side set to the extent (`84` on the tile, `92` full-bleed). The margins
  are equal by construction.
- **the wordmark tokens.** The mark's token stream, taken relative to the end of its l, is
  carried to the end of the word and scaled by the ratio of the two l heights, so both end
  the same way at their own size.

Run `_work/verify.py` after any change: it checks that no SVG carries text, the margins and
extent of each cut, the token count and the single lit token on the mark and the wordmark, that the wordmark has
no tile and no lockup exists, the one-ink cut, every raster
size, that the mark survives at 16 px, and that `icon-512.png` is `icon.svg` rasterised.
