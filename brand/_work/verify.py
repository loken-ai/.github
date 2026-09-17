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
fails = []

def check(cond, label, detail=""):
    print(f"  {'ok  ' if cond else 'FAIL'}  {label}{'  ' + detail if detail else ''}")
    if not cond: fails.append(label)

def ink_box(root):
    """Ink box of an SVG: every path point and every solid circle; halos (url fills) excluded."""
    xs, ys = [], []
    for el in root.iter():
        fill = el.get("fill", "")
        if el.tag == NS + "path":
            v = [float(n) for n in re.findall(r"-?\d+\.?\d*", el.get("d"))]
            xs += v[0::2]; ys += v[1::2]
        elif el.tag == NS + "circle" and not fill.startswith("url("):
            cx, cy, r = (float(el.get(k)) for k in ("cx", "cy", "r"))
            xs += [cx - r, cx + r]; ys += [cy - r, cy + r]
    return min(xs), min(ys), max(xs), max(ys)

# ---- no asset carries text or asks for a font
for name in sorted(f for f in os.listdir(B) if f.endswith(".svg")):
    text = open(os.path.join(B, name)).read()
    print(name)
    check("<text" not in text and "font-family" not in text, "no text, no font")

# ---- the mark: centred on its tile at the declared extent, one lit token
for name, lo, hi, extent in (("icon.svg", 4, 124, gen.EXTENT_TILE), ("favicon.svg", 0, 128, gen.EXTENT_BLEED),
                             ("icon-mono.svg", 0, 128, gen.EXTENT_TILE)):
    root = ET.parse(os.path.join(B, name)).getroot()
    print(name)
    x0, y0, x1, y1 = ink_box(root)
    ml, mr, mt, mb = x0 - lo, hi - x1, y0 - lo, hi - y1
    check(abs(ml - mr) < 0.05 and abs(mt - mb) < 0.05, "equal margins",
          f"left={ml:.2f} right={mr:.2f} top={mt:.2f} bottom={mb:.2f}")
    check(abs(max(x1 - x0, y1 - y0) - extent) < 0.05, f"extent {extent:g}", f"got {max(x1 - x0, y1 - y0):.2f}")
    solid = [c.get("fill") for c in root.iter(NS + "circle") if not c.get("fill").startswith("url(")]
    check(len(solid) == len(gen.TOKENS), f"{len(gen.TOKENS)} tokens", f"got {len(solid)}")
    lit = [f for f in solid if f in (gen.EMERALD_ON_TILE, gen.EMERALD_ON_PAPER)]
    if "mono" in name:
        inks = {el.get("fill") for el in root.iter() if el.get("fill")}
        check(len(inks) == 1, "one ink", f"got {sorted(inks)}")
    else:
        check(len(lit) == 1 and solid.index(lit[0]) == gen.LIT, "exactly one lit token, the second emitted")

# ---- rasters: present at their sizes, and the same drawing as the vector
print("png/")
expect = {f"icon-{s}.png": (s, s) for s in (512, 256, 180, 128)}
expect.update({f"favicon-{s}.png": (s, s) for s in (48, 32, 16)})
expect.update({"icon-mono-512.png": (512, 512), "avatar-512.png": (512, 512)})
for f, size in expect.items():
    path = os.path.join(P, f)
    check(os.path.exists(path) and Image.open(path).size == size, f, f"expected {size}")
for f in ("wordmark.png", "lockup.png", "lockup-dark.png", "favicon.ico"):
    check(os.path.exists(os.path.join(P, f)), f)
fav = np.array(Image.open(os.path.join(P, "favicon-16.png")).convert("RGB")).astype(int)
check((fav.max(axis=2) > 170).sum() >= 12, "the mark survives at 16 px")

probe = os.path.join(HERE, "variants", "verify-icon.png"); os.makedirs(os.path.dirname(probe), exist_ok=True)
subprocess.run([gen.RESVG, "-w", "512", os.path.join(B, "icon.svg"), probe], check=True)
a = np.array(Image.open(probe).convert("RGBA")).astype(int); b = np.array(Image.open(os.path.join(P, "icon-512.png")).convert("RGBA")).astype(int)
check(np.abs(a - b).max() <= 1, "icon-512.png is icon.svg rasterised")

print()
print("FAILURES: " + ", ".join(fails) if fails else "all checks passed")
sys.exit(1 if fails else 0)
