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
expect.update({f"favicon-{s}.png": (s, s) for s in (64, 48, 32, 16)})
expect.update({"icon-mono-512.png": (512, 512), "avatar-512.png": (512, 512)})
for f, size in expect.items():
    path = os.path.join(P, f)
    check(os.path.exists(path) and Image.open(path).size == size, f, f"expected {size}")
for f in ("wordmark.png", "wordmark-dark.png", "banner.png", "lockup.png", "favicon.ico"):
    check(os.path.exists(os.path.join(P, f)), f)
ico = Image.open(os.path.join(P, "favicon.ico"))
check(set(ico.ico.sizes()) == {(16, 16), (32, 32), (48, 48)}
      and all(np.array_equal(np.array(ico.ico.getimage((z, z)).convert("RGBA")),
                             np.array(Image.open(os.path.join(P, f"favicon-{z}.png")).convert("RGBA")))
              for z in (16, 32, 48)),
      "favicon.ico holds the 16, 32 and 48 px cuts, none scaled from another")
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

# ---- depth, measured on the render of each isometric cut: no edge crosses a tile it should
# pass behind, and no join is darker than the edges that meet there
print("depth")
def depth_checks(label, raster, scale, extent):
    img = np.array(Image.open(raster).convert("RGB")).astype(int)
    defs, art, box = gen.mark()
    bw = box[2] - box[0]; bh = box[3] - box[1]; s = extent / max(bw, bh)
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
    mid_c = gen.N / 2; sc = scale
    scaled = lambda v: mid_c + (v - mid_c) * sc        # the block is scaled about the centre of the box
    faces = []
    for i in range(n_grid):
        for j in range(n_grid):
            for k in range(n_grid):
                lit = (i, j, k) == gen.LIT
                z = k + off + (gen.LIFT if lit else 0)
                ii, jj = i + off, j + off
                top = lambda a, b: gen.iso(scaled(a), scaled(b), scaled(z + 1))
                faces.append(([top(ii, jj), top(ii + 1, jj), top(ii + 1, jj + 1), top(ii, jj + 1)],
                              3 * mid_c + (ii + jj + z + 1.5 - 3 * mid_c) * sc))

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
    check(bad == 0, f"{label}: every edge crossing a tile lands on the right side of it", f"{bad} wrong")

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
    check(worst <= 12, f"{label}: no join is darker than the edges that meet there", f"largest gap {worst}")

depth_checks("icon", os.path.join(P, "icon-512.png"), gen.BLOCK_SCALE, gen.EXTENT_TILE)
small_probe = os.path.join(SCRATCH, "verify-favicon.png")
subprocess.run([gen.RESVG, "-w", "512", os.path.join(B, "favicon.svg"), small_probe], check=True)
depth_checks("favicon", small_probe, gen.SMALL_SCALE, gen.EXTENT_BLEED)

# ---- the components: the mark of the server worn with a hue and a screen, in 3 cuts
print("components/")
CD = os.path.join(B, "components"); CP = os.path.join(CD, "png")
HEX = lambda c: np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)])

def hull(points):
    pts = sorted(set(points))
    def half(seq):
        out = []
        for q in seq:
            while len(out) >= 2 and (out[-1][0] - out[-2][0]) * (q[1] - out[-2][1]) - (out[-1][1] - out[-2][1]) * (q[0] - out[-2][0]) <= 0:
                out.pop()
            out.append(q)
        return out[:-1]
    return half(pts) + half(pts[::-1])

box_hull = hull([gen.iso(*[c * gen.N for c in corner]) for corner in gen.CORNERS])
def inside(pt, poly):
    return all((b[0] - a[0]) * (pt[1] - a[1]) - (b[1] - a[1]) * (pt[0] - a[0]) >= -1e-6
               for a, b in zip(poly, poly[1:] + poly[:1]))

for label, sc_ in (("the block of the small cut", gen.SMALL_SCALE), ("the block of the icon", gen.BLOCK_SCALE)):
    corners = []
    for i in (gen.LO, gen.HI):
        for j in (gen.LO, gen.HI):
            for k in (gen.LO, gen.HI + gen.LIFT):
                c = gen.N / 2
                corners.append(gen.iso(c + (i - c) * sc_, c + (j - c) * sc_, c + (k - c) * sc_))
    check(all(inside(q, box_hull) for q in corners), f"{label}, raised tile included, stays inside the box")

rd = lambda *p: open(os.path.join(*p)).read()
check(rd(CD, "loken.svg") == rd(B, "icon.svg"), "loken: the component icon is icon.svg")
check(rd(CD, "loken-small.svg") == rd(B, "favicon.svg"), "loken: the small cut is favicon.svg")
check(np.array_equal(np.array(Image.open(os.path.join(CP, "loken-tiny-16.png"))),
                     np.array(Image.open(os.path.join(P, "favicon-16.png")))),
      "loken: the 16 px cut is favicon-16.png")

SIZES = {"": (512, 256, 128), "-small": (64, 48, 32), "-tiny": (16,)}
tinies = {}; smalls = {}
for name, (hue, _) in gen.COMPONENTS.items():
    kernel, frame_ink = gen.component_colours(name)
    allowed = PALETTE | set(kernel) | {gen.SCREEN}
    for suffix, sizes in SIZES.items():
        path = os.path.join(CD, f"{name}{suffix}.svg"); tag = f"{name}{suffix}"
        check(os.path.exists(path), f"{tag}.svg exists")
        raw = rd(path)
        check("<text" not in raw and "font-family" not in raw, f"{tag}: no text, no font")
        root = ET.parse(path).getroot(); c = counts(root)
        if suffix == "-tiny":
            shapes = [el.get("fill") for el in root.iter(NS + "polygon")]
            check(len(shapes) == (3 if hue is None else 1) and not list(root.iter(NS + "linearGradient")),
                  f"{tag}: flat", f"got {len(shapes)} polygons")
        else:
            want = 3 + tiles * 3 + (0 if hue is None else 1)
            check(c["polygon"] == want and c["line"] == len(gen.EDGES) - 3,
                  f"{tag}: walls, tiles{'' if hue is None else ', screen'} and 9 edges", f"got {c}")
            fills = {el.get("fill") for el in root.iter(NS + "polygon")}
            check(fills <= allowed, f"{tag}: flat fills stay in the palette", f"outside: {sorted(fills - allowed)}")
            lit = [el for el in root.iter(NS + "polygon") if el.get("fill") == kernel[0]]
            check(len(lit) == 1, f"{tag}: one tile is the kernel's", f"got {len(lit)}")
        for sz in sizes:
            f = os.path.join(CP, f"{tag}-{sz}.png")
            check(os.path.exists(f) and Image.open(f).size == (sz, sz), f"{tag}-{sz}.png")
    a = np.array(Image.open(os.path.join(CP, f"{name}-512.png")).convert("RGB")).astype(int)
    ink = np.abs(a - HEX(gen.NIGHT)).max(axis=2) > 24
    ys, xs = np.where(ink)
    ml, mr, mt, mb = xs.min(), 511 - xs.max(), ys.min(), 511 - ys.max()
    check(abs(ml - mr) <= 2 and abs(mt - mb) <= 2, f"{name}: the icon is centred on the tile",
          f"left={ml} right={mr} top={mt} bottom={mb}")
    t16 = np.array(Image.open(os.path.join(CP, f"{name}-tiny-16.png")).convert("RGB")).astype(int)
    tinies[name] = t16
    smalls[name] = np.array(Image.open(os.path.join(CP, f"{name}-small-32.png")).convert("RGB")).astype(int)
    drawn = (np.abs(t16 - HEX(gen.NIGHT)).max(axis=2) > 24).sum()
    check(drawn >= 100, f"{name}: the 16 px cut survives", f"drawn pixels {drawn}")
    if hue is not None:
        hexcol = HEX(gen.hue_of(gen.KERNEL[0], hue))
        body = np.abs(t16 - hexcol).max(axis=2) < 40
        cut = np.abs(t16 - HEX(gen.NIGHT)).max(axis=2) < 40
        yy, xx = np.where(body)
        inner = cut[yy.min():yy.max() + 1, xx.min():xx.max() + 1].sum()
        check(inner >= 8, f"{name}: the glyph is cut out of the hexagon at 16 px", f"{inner} ground pixels")

# two marks are told apart when enough pixels differ clearly, not when the mean differs: the
# frame, the kernel's tile and the screen are a small part of a small icon
for label, group in (("16 px cuts", tinies), ("32 px cuts", smalls)):
    names = list(group); worst = None
    for x in range(len(names)):
        for y in range(x + 1, len(names)):
            n = int((np.abs(group[names[x]] - group[names[y]]).max(axis=2) > 64).sum())
            if worst is None or n < worst[0]: worst = (n, names[x], names[y])
    check(worst[0] >= 40, f"the {label} differ from each other",
          f"closest pair {worst[1]} and {worst[2]}: {worst[0]} pixels differ clearly")

print()
print("FAILURES: " + ", ".join(fails) if fails else "all checks passed")
sys.exit(1 if fails else 0)
