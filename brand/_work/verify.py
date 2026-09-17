#!/usr/bin/env python3
"""Check the emitted brand assets. Prints FAIL loudly; exits non-zero on any failure."""
import os, re, subprocess, sys
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen

B = gen.BRAND; P = os.path.join(B, "png"); NS = "{http://www.w3.org/2000/svg}"
PALETTE = {gen.CYAN, gen.GREEN, gen.BLACK, gen.WHITE, gen.SUBTLE, "#111111", "NONE"}
fails = []

def check(cond, label, detail=""):
    print(f"  {'ok  ' if cond else 'FAIL'}  {label}{'  ' + detail if detail else ''}")
    if not cond: fails.append(label)

def colours(root):
    out = set()
    for el in root.iter():
        for a in ("fill", "stroke"):
            if el.get(a): out.add(el.get(a).upper())
    return out

def counts(root):
    return {t: sum(1 for _ in root.iter(NS + t)) for t in ("circle", "line", "polygon", "path", "rect")}

# ---- no asset carries text or asks for a font, and none leaves the palette
for name in sorted(f for f in os.listdir(B) if f.endswith(".svg")):
    root = ET.parse(os.path.join(B, name)).getroot(); raw = open(os.path.join(B, name)).read()
    print(name)
    check("<text" not in raw and "font-family" not in raw, "no text, no font")
    off = colours(root) - PALETTE
    check(not off, "palette only", f"outside: {sorted(off)}" if off else "")

# ---- the mark: its parts, and the small cut dropping what it cannot hold
print("icon.svg / favicon.svg / icon-mono.svg")
icon = counts(ET.parse(os.path.join(B, "icon.svg")).getroot())
fav = counts(ET.parse(os.path.join(B, "favicon.svg")).getroot())
nodes = len(gen.LINK_IN) * 2
check(icon["circle"] == nodes + 4, f"{nodes} nodes and the kernel with its rings", f"got {icon['circle']}")
check(icon["polygon"] == 2 and icon["line"] == 3 + len(gen.LINK_IN) * 2 + 2, "hexagons, facets, links and mesh",
      f"got {icon['polygon']} polygons, {icon['line']} lines")
check(fav["polygon"] == 1 and fav["line"] == len(gen.LINK_IN), "small cut keeps hexagon and links only",
      f"got {fav['polygon']} polygons, {fav['line']} lines")
mono = colours(ET.parse(os.path.join(B, "icon-mono.svg")).getroot())
check(mono <= {gen.BLACK, gen.WHITE, "NONE"}, "one ink", f"got {sorted(mono)}")

# ---- the wordmark carries the word alone, the lockup carries its own ground
print("wordmark.svg / lockup.svg")
for name in ("wordmark.svg", "wordmark-dark.svg"):
    root = ET.parse(os.path.join(B, name)).getroot()
    c = counts(root)
    check(c["path"] == 1 and c["polygon"] == 0 and c["circle"] == 0, f"{name}: the word alone",
          f"got {c}")
for name in ("lockup.svg", "lockup-dark.svg"):
    c = counts(ET.parse(os.path.join(B, name)).getroot())
    check(c["rect"] == 0, f"{name}: transparent ground", f"got {c['rect']} rects")
    check(c["path"] == 2 and c["polygon"] == 2, f"{name}: the mark, the word and the line", f"got {c}")

# ---- traced letters: an open bay is not a counter
print("letter counters")
counters = {ch: len(gen._holes(gen._mask(ch, 200))) for ch in "SCGOED"}
check(counters["S"] == 0 and counters["C"] == 0 and counters["G"] == 0, "open bays are not filled",
      f"got S={counters['S']} C={counters['C']} G={counters['G']}")
check(counters["O"] == 1 and counters["D"] == 1, "closed counters are found",
      f"got O={counters['O']} D={counters['D']}")

# ---- rasters: present at their sizes, centred, and the same drawing as the vector
print("png/")
expect = {f"icon-{s}.png": (s, s) for s in (512, 256, 180, 128)}
expect.update({f"favicon-{s}.png": (s, s) for s in (48, 32, 16)})
expect.update({"icon-mono-512.png": (512, 512), "avatar-512.png": (512, 512)})
for f, size in expect.items():
    path = os.path.join(P, f)
    check(os.path.exists(path) and Image.open(path).size == size, f, f"expected {size}")
for f in ("wordmark.png", "wordmark-dark.png", "lockup.png", "lockup-dark.png", "favicon.ico"):
    check(os.path.exists(os.path.join(P, f)), f)

a = np.array(Image.open(os.path.join(P, "icon-512.png")).convert("RGB")).astype(int)
ink = a.max(axis=2) > 90
ys, xs = np.where(ink)
ml, mr, mt, mb = xs.min(), 511 - xs.max(), ys.min(), 511 - ys.max()
check(abs(ml - mr) <= 2 and abs(mt - mb) <= 2, "the mark is centred on the tile",
      f"left={ml} right={mr} top={mt} bottom={mb}")
tiny = np.array(Image.open(os.path.join(P, "favicon-16.png")).convert("RGB")).astype(int)
check((tiny.max(axis=2) > 120).sum() >= 40, "the mark survives at 16 px",
      f"lit pixels {(tiny.max(axis=2) > 120).sum()}")

probe = os.path.join(HERE, "variants", "verify-icon.png"); os.makedirs(os.path.dirname(probe), exist_ok=True)
subprocess.run([gen.RESVG, "-w", "512", os.path.join(B, "icon.svg"), probe], check=True)
v = np.array(Image.open(probe).convert("RGBA")).astype(int)
r = np.array(Image.open(os.path.join(P, "icon-512.png")).convert("RGBA")).astype(int)
check(np.abs(v - r).max() <= 1, "icon-512.png is icon.svg rasterised")

print()
print("FAILURES: " + ", ".join(fails) if fails else "all checks passed")
sys.exit(1 if fails else 0)
