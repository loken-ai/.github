#!/usr/bin/env python3
"""Check the emitted brand assets. Prints FAIL loudly; exits non-zero on any failure.

Beyond structure, two properties of the mark are measured on the render itself: what wins where
an edge crosses a tile, and the colour at the vertices where two edges meet. Both were wrong at
some point and were invisible to a glance.
"""
import os, re, subprocess, sys
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen

B = gen.BRAND; P = os.path.join(B, "png"); NS = "{http://www.w3.org/2000/svg}"
SCRATCH = os.path.join(HERE, "variants"); os.makedirs(SCRATCH, exist_ok=True)
PALETTE = set(gen.TILE) | set(gen.KERNEL) | {gen.WALL, gen.FRAME, gen.NIGHT, gen.TILE_EDGE,
                                            gen.INK_NIGHT, gen.INK_PAPER, gen.SUBTLE, "#14161C"}
fails = []

def check(cond, label, detail=""):
    print(f"  {'ok  ' if cond else 'FAIL'}  {label}{'  ' + detail if detail else ''}")
    if not cond: fails.append(label)

def counts(root):
    return {t: sum(1 for _ in root.iter(NS + t)) for t in ("polygon", "line", "path", "rect", "linearGradient")}

# ---- no asset carries text or asks for a font
for name in sorted(f for f in os.listdir(B) if f.endswith(".svg")):
    raw = open(os.path.join(B, name)).read()
    print(name)
    check("<text" not in raw and "font-family" not in raw, "no text, no font")

# ---- the mark: its parts, and the palette its flat fills use
print("icon.svg")
root = ET.parse(os.path.join(B, "icon.svg")).getroot(); c = counts(root)
tiles = 8
check(c["polygon"] == 3 + tiles * 3, "three walls and eight tiles", f"got {c['polygon']} polygons")
check(c["line"] == len(gen.EDGES) - 3, "nine edges, the three at the near corner left out",
      f"got {c['line']} lines")
fills = {el.get("fill") for el in root.iter(NS + "polygon")}
check(fills <= PALETTE, "flat fills stay in the palette", f"outside: {sorted(fills - PALETTE)}")
lit = [el for el in root.iter(NS + "polygon") if el.get("fill") == gen.KERNEL[0]]
check(len(lit) == 1, "one tile is the kernel's", f"got {len(lit)}")
mono = {el.get("fill") for el in ET.parse(os.path.join(B, "icon-mono.svg")).getroot().iter(NS + "polygon")}
check(mono <= {"#14161C", gen.WALL}, "one ink", f"got {sorted(mono)}")

# ---- the wordmark carries the written word alone; the banner carries mark, word and line
print("wordmark.svg / banner.svg")
for name in ("wordmark.svg", "wordmark-dark.svg"):
    c = counts(ET.parse(os.path.join(B, name)).getroot())
    check(c["path"] == 1 and c["polygon"] == 0 and c["line"] == 0, f"{name}: the written word alone",
          f"got {c}")
c = counts(ET.parse(os.path.join(B, "banner.svg")).getroot())
check(c["rect"] == 1 and c["path"] == 2 and c["polygon"] == 3 + tiles * 3,
      "banner: its ground, the mark, the word and the line", f"got {c}")

# ---- letters: an open bay is not a counter
print("letter counters")
n = {ch: len(gen._holes(gen._mask(ch, 200))) for ch in "SCGOED"}
check(n["S"] == 0 and n["C"] == 0 and n["G"] == 0, "open bays are not filled",
      f"S={n['S']} C={n['C']} G={n['G']}")
check(n["O"] == 1 and n["D"] == 1, "closed counters are found", f"O={n['O']} D={n['D']}")

# ---- rasters
print("png/")
expect = {f"icon-{s}.png": (s, s) for s in (512, 256, 180, 128)}
expect.update({f"favicon-{s}.png": (s, s) for s in (48, 32, 16)})
expect.update({"icon-mono-512.png": (512, 512), "avatar-512.png": (512, 512)})
for f, size in expect.items():
    path = os.path.join(P, f)
    check(os.path.exists(path) and Image.open(path).size == size, f, f"expected {size}")
for f in ("wordmark.png", "wordmark-dark.png", "banner.png", "lockup.png", "favicon.ico"):
    check(os.path.exists(os.path.join(P, f)), f)
check(open(os.path.join(P, "lockup.png"), "rb").read() == open(os.path.join(P, "banner.png"), "rb").read(),
      "png/lockup.png is the banner, for links published before the rename")

a = np.array(Image.open(os.path.join(P, "icon-512.png")).convert("RGB")).astype(int)
ink = np.abs(a - np.array([int(gen.NIGHT[i:i + 2], 16) for i in (1, 3, 5)])).max(axis=2) > 24
ys, xs = np.where(ink)
ml, mr, mt, mb = xs.min(), 511 - xs.max(), ys.min(), 511 - ys.max()
check(abs(ml - mr) <= 2 and abs(mt - mb) <= 2, "the mark is centred on the tile",
      f"left={ml} right={mr} top={mt} bottom={mb}")
tiny = np.array(Image.open(os.path.join(P, "favicon-16.png")).convert("RGB")).astype(int)
check((tiny.max(axis=2) > 120).sum() >= 40, "the mark survives at 16 px",
      f"lit pixels {(tiny.max(axis=2) > 120).sum()}")
probe = os.path.join(SCRATCH, "verify-icon.png")
subprocess.run([gen.RESVG, "-w", "512", os.path.join(B, "icon.svg"), probe], check=True)
v = np.array(Image.open(probe).convert("RGBA")).astype(int)
r = np.array(Image.open(os.path.join(P, "icon-512.png")).convert("RGBA")).astype(int)
check(np.abs(v - r).max() <= 1, "icon-512.png is icon.svg rasterised")

# ---- depth, measured on the render: no edge crosses a tile it should pass behind
print("depth")
img = np.array(Image.open(os.path.join(P, "icon-512.png")).convert("RGB")).astype(int)
defs, art, box = gen.mark()
bw = box[2] - box[0]; bh = box[3] - box[1]; s = gen.EXTENT_TILE / max(bw, bh)
cx = (box[0] + box[2]) / 2; cy = (box[1] + box[3]) / 2
px = lambda gp: (int(round((64 + (gp[0] - cx) * s) * 4)), int(round((64 + (gp[1] - cy) * s) * 4)))

def kind_at(gp):
    x, y = px(gp)
    patch = img[y - 2:y + 3, x - 2:x + 3].reshape(-1, 3)
    p = patch[np.abs(patch - np.array([59, 111, 224])).sum(axis=1).argmin()]
    if abs(p[2] - p[0]) > 60 and p[2] > 120: return "frame"
    if p[1] > 80 and p[2] > 80 and p[0] < 120: return "tile"
    if min(p) > 200: return "wall"
    return "other"

n_grid = 2; off = (gen.N - n_grid) / 2
faces = []
for i in range(n_grid):
    for j in range(n_grid):
        for k in range(n_grid):
            lit = (i, j, k) == gen.LIT
            z = k + off + (gen.LIFT if lit else 0)
            ii, jj = i + off, j + off
            faces.append(([gen.iso(ii, jj, z + 1), gen.iso(ii + 1, jj, z + 1),
                           gen.iso(ii + 1, jj + 1, z + 1), gen.iso(ii, jj + 1, z + 1)],
                          ii + jj + z + 1.5))

def crossings(p, q, poly):
    out = []
    for a, b in zip(poly, poly[1:] + poly[:1]):
        d1 = (q[0] - p[0], q[1] - p[1]); d2 = (b[0] - a[0], b[1] - a[1])
        den = d1[0] * d2[1] - d1[1] * d2[0]
        if abs(den) < 1e-9: continue
        t = ((a[0] - p[0]) * d2[1] - (a[1] - p[1]) * d2[0]) / den
        u = ((a[0] - p[0]) * d1[1] - (a[1] - p[1]) * d1[0]) / den
        if 0.05 < t < 0.95 and 0 < u < 1: out.append(t)
    return out

bad = 0
for ai, bi in gen.EDGES:
    A, Bc = gen.CORNERS[ai], gen.CORNERS[bi]
    if gen.NEAR_CORNER in (A, Bc): continue
    pa = [c * gen.N for c in A]; pb = [c * gen.N for c in Bc]
    p = gen.iso(*pa); q = gen.iso(*pb)
    for poly, fdepth in faces:
        for t in crossings(p, q, poly):
            mid = [pa[m] + (pb[m] - pa[m]) * t for m in range(3)]
            want = "frame" if sum(mid) > fdepth else "tile"
            got = kind_at((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
            if got not in (want, "other"): bad += 1
check(bad == 0, "every edge crossing a tile lands on the right side of it", f"{bad} wrong")

# ---- the joins: a vertex must carry the colour the depth model gives, not a darker blend
span = 3 * gen.N
worst = 0
for corner in gen.CORNERS:
    if corner in (gen.NEAR_CORNER, (0, 0, 0)): continue      # the far corner sits behind the tiles
    d = sum(c * gen.N for c in corner)
    want = [int(v) for v in bytes.fromhex(gen._mix(gen.FRAME, gen.NIGHT, gen.FADE * (1 - d / span))[1:])]
    x, y = px(gen.iso(*[c * gen.N for c in corner]))
    patch = img[y - 2:y + 3, x - 2:x + 3].reshape(-1, 3)
    got = patch[np.abs(patch - np.array(want)).sum(axis=1).argmin()]
    worst = max(worst, max(abs(int(g) - w) for g, w in zip(got, want)))
check(worst <= 12, "no join is darker than the edges that meet there", f"largest gap {worst}")

print()
print("FAILURES: " + ", ".join(fails) if fails else "all checks passed")
sys.exit(1 if fails else 0)
