# LOKEN — brand assets

**LOKEN** — from **Lo**cal + tok**en** — a local, multimodal, energy-aware inference engine.
Logo: a **token chain** — five separate circles tracing an L, three down the stem and three
across the base sharing the corner — in white on the indigo tile, the first one emerald. The
tokens never touch: the ground between them is what makes them five countable units rather
than one poured shape. The mark is **procedurally generated**, not traced from a font glyph;
the PNGs render the same geometry.

> The emerald token is a **logo device.** In text, always write **LOKEN** (and `loken` for
> technical names — the org, crates, repos). It carries into the wordmark as the counter of
> the **O** — the same circle, the same ink — so the mark and the word read as one system. The
> L cannot carry it: it has no enclosed counter. The one-colour cut is the exception, where
> every token takes the single ink, because one ink cannot carry a second.

## Palette
| Role | Hex |
|------|-----|
| Indigo (tile) | `#3730A3` → `#312E81` |
| Emerald (accent) | `#34D399` → `#059669` |
| Emerald deep (tagline) | `#047857` |

Tagline: `LOCAL · MULTIMODAL · GREEN`

## Files
- `icon.svg` — primary mark (token chain on the indigo tile)
- `favicon.svg` — full-bleed mark for tiny sizes
- `wordmark.svg` — the LOKEN wordmark
- `lockup.svg` — icon + wordmark
- `icon-mono.svg` — single-colour (stamp / print / 1-colour contexts)
- `png/` — `icon-{512,256,180,128}.png`, `favicon-{48,32,16}.png`, `favicon.ico` (16/32/48),
  `icon-mono-512.png`, `wordmark.png`, `lockup.png`
- `png/avatar-512.png` — the **org avatar**. Square to the edge, no rounding of its own:
  GitHub puts the avatar in its own container (square, rounded, or circular depending on the
  surface), so a rounded source would read as a double round and its transparent corners would
  take the colour of the page. Checked against all three crops; the chain survives the circle.
  There is no API for it — upload it under *Settings → Profile → Upload new picture*.
- `../profile/` — `icon.png` and `lockup.png`, the org profile images, emitted by the same run

## Generating
Assets are produced by **`_work/gen.py`** (single source of truth): `python3 gen.py final`.
The mark's geometry is written once, in `chain()`; the SVG paths and the PNG both read it
there, so the vector and the raster cannot drift apart. The wordmark's five letters are set in
Quicksand-Bold and traced to outlines, so **no asset depends on a font being installed where
it is displayed**. The only `<text>` left in any SVG is the tagline.

Three things are derived rather than typed, which is what keeps them true at every size
instead of only at the one that was eyeballed:

- **the margins.** Radius is `0.15e` and centre spacing `0.35e`, so the mark's total extent is
  exactly `e` and its first centre sits at `64 - 0.35e`. The ink's bounding box is therefore
  symmetric about the tile centre by construction — the run prints the four margins and says
  `UNEQUAL` if they ever diverge. At `e=80`: **20 / 20 / 20 / 20**.
- **the gap.** Spacing minus two radii leaves `0.05e` of ground between neighbours — **4 units**
  at `e=80`. Tangent discs read as one poured shape; the gap is what makes them countable.
- **the accent letter.** `ACC` has to name a letter that *has* a counter. Pointing it at the L,
  which has none, dropped the emerald from the wordmark silently — no error, just an asset
  with the brand device missing. It names the **O**.

Re-run `_work/verify.py` if the geometry, the word, or the tracer changes: it parses the
emitted SVG back and checks the token count, that no two tokens touch, the extent, and the
four margins.

## Notes
- **The SVGs are vector throughout**; PNGs are rasterised with Pillow (no system SVG renderer
  here), which is also why the vector output is verified against the PNG rather than viewed.
