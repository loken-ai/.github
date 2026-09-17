# LOKEN brand assets

**LOKEN**, from **Lo**cal + tok**en**: a local inference server for AI models.

## Three assets
| Asset | What it is | Where it goes |
|-------|------------|---------------|
| **Icon** | The mark on a square black tile | App icon, favicon, org avatar |
| **Wordmark** | The word *Loken* alone | Anywhere the mark is already present |
| **Banner** | Mark, word and line on a black panel | Every page header, in either theme |

The mark is a token: a hexagon cut by its three facets, holding the kernel at the centre. Six
cyan nodes sit on the kernel's links, six green nodes on the hexagon's own vertices, and a
thinner mesh ties the two rings together.

The banner carries the line `SELF-HOSTED MULTIMODAL INFERENCE`, what loken is in three words.
It carries its own panel rather than swapping by colour scheme, because the cyan of the hexagon
goes pale on paper. In text, always write **LOKEN** (and `loken` for technical names: the org,
crates, repos).

## Palette
| Role | Hex |
|------|-----|
| Cyan: hexagon, mesh, inner nodes | `#00FFFF` |
| Green: kernel, links, vertex nodes | `#39FF14` |
| Black: ground | `#000000` |
| White: word, kernel halo | `#FFFFFF` |
| Grey: the lockup line | `#888888` |

## Files
- `icon.svg`, `favicon.svg` (full-bleed, for small sizes), `icon-mono.svg` (one ink)
- `wordmark.svg`, `wordmark-dark.svg`: for paper and for dark grounds
- `banner.svg`
- `png/`: `icon-{512,256,180,128}.png`, `favicon-{48,32,16}.png`, `favicon.ico` (16/32/48),
  `icon-mono-512.png`, `wordmark.png`, `wordmark-dark.png`, `banner.png`; `lockup.png` is a
  copy of the banner, kept for READMEs published before the rename
- `png/avatar-512.png`: the **org avatar**. Square to the edge, no rounding of its own:
  GitHub puts the avatar in its own container (square, rounded, or circular depending on the
  surface), so a rounded source would read as a double round and its transparent corners would
  take the colour of the page. Upload it under *Settings, Profile, Upload new picture*.
- `../profile/`: `icon.png` and `banner.png`, the org profile images, copied by the same run

## Generating
`_work/gen.py` is the single source: `python3 gen.py`. The mark is written once as hexagon
radii, node offsets and ring fractions; the SVGs are emitted from it and the PNGs are
rasterised from those SVGs with [resvg](https://github.com/linebender/resvg), which must be on
`PATH`. The word and the lockup line are traced from a system font to outlines at generation time, so
no asset contains text or depends on a font where it is displayed.

Three things are derived rather than typed:

- **the centring.** The mark's ink box, which its vertex nodes set, is centred on the tile with
  its larger side at the extent (`104` on the tile, `116` full-bleed), so the four margins are
  equal by construction.
- **the stroke weights.** The mark is drawn at a fixed scale and the group is scaled to fit;
  stroke widths are divided back out, so a line keeps its weight in every cut.
- **the small cuts.** Below the favicon size the inner outline, the facets and the thin mesh
  turn to mud, so they are dropped; at sixteen pixels a hairline falls under a pixel, so that
  one cut is drawn from a thicker variant.

Run `_work/verify.py` after any change: it checks that no SVG carries text or leaves the
palette, the parts of the mark and of the reduced cut, the one-ink cut, that the wordmark holds
the word alone and the banner its panel, every raster size, that the mark is centred and
survives at sixteen pixels, and that `icon-512.png` is `icon.svg` rasterised.
