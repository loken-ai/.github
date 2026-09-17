#!/usr/bin/env python3
"""LOKEN brand generator: the single source of every logo asset.

The mark is a token: a hexagon cut by its facets, holding a kernel at the centre. Six cyan
nodes sit on the kernel's links, six green nodes on the hexagon's own vertices, and the mesh
between them is drawn in two weights. Cyan and green on black.

The word Loken and the line under it in the lockup are traced to outlines, so no asset
contains text or depends on a font being installed where it is displayed.

Every shape is written once below. The SVGs are emitted from it and the PNGs are rasterised
from those SVGs with resvg, so vector and raster cannot drift. Run from this folder:

    python3 gen.py      # write ../*.svg, ../png/*, ../../profile/*
"""
import math, os, shutil, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
BRAND = os.path.dirname(HERE)
PROFILE = os.path.join(os.path.dirname(BRAND), "profile")

CYAN = "#00FFFF"; GREEN = "#39FF14"; BLACK = "#000000"; WHITE = "#FFFFFF"
FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

WORD = "Loken"
# The line under the word in the lockup: what loken is, in three words. The wordmark carries
# the word alone, so the line lives where the composition has room for it.
SUBLINE = "SELF-HOSTED MULTIMODAL INFERENCE"
SUBTLE = "#888888"

# ---------------------------------------------------------------- the token mark
# Hexagon radii, node offsets and ring radii on a grid centred at (0, 0). Everything the mark
# draws is derived from these, so it scales as one drawing.
HEX = (70.0, 90.0)          # half width and half height of the outer hexagon
HEX_INNER = (60.0, 75.0)    # the inner outline, one facet inside it
KERNEL = 16.0               # the kernel disc; its rings are fractions of it
NODE_IN = 5.0; NODE_OUT = 6.0
LINK_IN = [(0.0, -60.0), (45.0, -35.0), (45.0, 35.0), (0.0, 60.0), (-45.0, 35.0), (-45.0, -35.0)]

def _hex(rx, ry):
    return [(0.0, -ry), (rx, -ry / 2), (rx, ry / 2), (0.0, ry), (-rx, ry / 2), (-rx, -ry / 2)]

def _pts(points):
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in points)

def mark(edge=CYAN, node_in=CYAN, node_out=GREEN, core=GREEN, link=GREEN, mesh=CYAN,
         halo=WHITE, detail=True, weight=1.0, boost=1.0):
    """The mark centred on (0, 0). `detail=False` drops what a small size cannot hold: the
    inner outline, the facets and the thin mesh. `weight` scales stroke widths only; `boost`
    thickens strokes and nodes together, for cuts where a hairline falls under a pixel."""
    weight = weight * boost
    w = lambda v: f"{v * weight:.2f}"
    v = _hex(*HEX)
    out = [f'<polygon points="{_pts(v)}" fill="none" stroke="{edge}" stroke-width="{w(2.5)}"/>']
    if detail:
        out.append(f'<polygon points="{_pts(_hex(*HEX_INNER))}" fill="none" stroke="{edge}" '
                   f'stroke-width="{w(1)}" opacity="0.3"/>')
        for a, b in ((0, 3), (5, 2), (4, 1)):     # the three facets, vertex to opposite vertex
            out.append(f'<line x1="{v[a][0]:.2f}" y1="{v[a][1]:.2f}" x2="{v[b][0]:.2f}" y2="{v[b][1]:.2f}" '
                       f'stroke="{edge}" stroke-width="{w(1)}" opacity="0.2"/>')
    out.append(f'<circle cx="0" cy="0" r="{KERNEL:.2f}" fill="{core}" opacity="0.95"/>')
    out.append(f'<circle cx="0" cy="0" r="{KERNEL:.2f}" fill="none" stroke="{halo}" '
               f'stroke-width="{w(2)}" opacity="0.4"/>')
    for k, sw, op in ((0.625, 1.5, 0.7), (0.3125, 1.0, 0.5)):
        out.append(f'<circle cx="0" cy="0" r="{KERNEL * k:.2f}" fill="none" stroke="{core}" '
                   f'stroke-width="{w(sw)}" opacity="{op}"/>')
    for x, y in LINK_IN:                          # kernel edge to inner node, the bold links
        d = math.hypot(x, y); ox, oy = x / d * KERNEL, y / d * KERNEL
        out.append(f'<line x1="{ox:.2f}" y1="{oy:.2f}" x2="{x:.2f}" y2="{y:.2f}" stroke="{link}" '
                   f'stroke-width="{w(2)}" opacity="0.6"/>')
    if detail:
        for (x, y), (vx, vy) in zip(LINK_IN, v):  # inner node to the vertex it answers
            out.append(f'<line x1="{x:.2f}" y1="{y:.2f}" x2="{vx:.2f}" y2="{vy:.2f}" stroke="{mesh}" '
                       f'stroke-width="{w(1.5)}" opacity="0.35"/>')
        for a, b in ((1, 5), (2, 5)):             # two chords across the token
            out.append(f'<line x1="{LINK_IN[a][0]:.2f}" y1="{LINK_IN[a][1]:.2f}" '
                       f'x2="{v[b][0]:.2f}" y2="{v[b][1]:.2f}" stroke="{mesh}" '
                       f'stroke-width="{w(1.5)}" opacity="0.35"/>')
    for x, y in LINK_IN:
        out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{NODE_IN * boost:.2f}" fill="{node_in}"/>')
    for x, y in v:
        out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{NODE_OUT * boost:.2f}" fill="{node_out}"/>')
    return "".join(out)

def mark_box():
    """Ink box of the mark: a node sits on every hexagon vertex, so the nodes set the extent."""
    rx, ry = HEX
    return (-rx - NODE_OUT, -ry - NODE_OUT, rx + NODE_OUT, ry + NODE_OUT)

# ---------------------------------------------------------------- text, traced to outlines
def _mask(ch, px):
    f = ImageFont.truetype(FONT, px)
    im = Image.new("L", (px * 2, int(px * 2.4)), 0)
    ImageDraw.Draw(im).text((px // 2, px // 2), ch, font=f, fill=255)
    return np.array(im) > 128

def _spread(seed, allowed):
    """Grow `seed` through `allowed` over the eight neighbours, until it stops growing."""
    cur = seed & allowed
    while True:
        g = cur.copy()
        g[1:, :] |= cur[:-1, :]; g[:-1, :] |= cur[1:, :]
        g[:, 1:] |= cur[:, :-1]; g[:, :-1] |= cur[:, 1:]
        g[1:, 1:] |= cur[:-1, :-1]; g[:-1, :-1] |= cur[1:, 1:]
        g[1:, :-1] |= cur[:-1, 1:]; g[:-1, 1:] |= cur[1:, :-1]
        g &= allowed
        if g.sum() == cur.sum(): return g
        cur = g

def _holes(mask):
    """Counters of a glyph: background the outside cannot reach, one array per counter.

    Reachability is decided by growing the background in from the border, not by ink on four
    sides: the open bay of an S, a C or a G has ink on four sides and is not a counter. The
    background spreads over the eight neighbours, since a diagonal pair of ink pixels would
    otherwise seal a bay that the glyph leaves open. The work is done on the glyph's own box,
    padded by one pixel, which is what keeps it cheap."""
    ys, xs = np.where(mask)
    y0, y1, x0, x1 = ys.min() - 1, ys.max() + 2, xs.min() - 1, xs.max() + 2
    box = mask[y0:y1, x0:x1]; bg = ~box
    border = np.zeros_like(bg); border[0, :] = border[-1, :] = True; border[:, 0] = border[:, -1] = True
    enclosed = bg & ~_spread(border, bg)
    out = []
    while enclosed.any():
        y, x = (int(v[0]) for v in np.where(enclosed))
        seed = np.zeros_like(enclosed); seed[y, x] = True
        part = _spread(seed, enclosed)
        full = np.zeros_like(mask); full[y0:y1, x0:x1] = part
        out.append(full); enclosed = enclosed & ~part
    return out

def _trace(mask):
    """Moore boundary of the shape in the mask, as pixel coordinates."""
    P = np.pad(mask, 1); ys, xs = np.where(P); y0 = ys.min(); x0 = int(xs[ys == y0].min())
    nb = [(0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1)]
    start = (y0, x0); cur = start; back = (y0, x0 - 1); cont = [start]
    for _ in range(4_000_000):
        d = (back[0] - cur[0], back[1] - cur[1]); bi = nb.index(d); nxt = None
        for k in range(1, 9):
            idx = (bi + k) % 8; c = (cur[0] + nb[idx][0], cur[1] + nb[idx][1])
            if P[c]:
                nxt = c; back = (cur[0] + nb[(idx - 1) % 8][0], cur[1] + nb[(idx - 1) % 8][1]); break
        if nxt is None: break
        cur = nxt; cont.append(cur)
        if cur == start and len(cont) > 3: break
    return [(x - 1, y - 1) for (y, x) in cont]

def _simplify(pts, eps):
    if len(pts) < 3: return pts
    a = np.array(pts[0], float); b = np.array(pts[-1], float); ab = b - a; L = float(np.hypot(*ab))
    d = np.hypot(*(np.array(pts, float) - a).T) if L == 0 else np.abs(np.cross(ab, np.array(pts, float) - a)) / L
    i = int(np.argmax(d))
    if d[i] > eps: return _simplify(pts[:i + 1], eps)[:-1] + _simplify(pts[i:], eps)
    return [pts[0], pts[-1]]

def text_paths(text, cap, tracking=0.0, px=320, eps=0.5):
    """`text` as outline subpaths at cap height `cap`, `tracking` in units of cap height.

    Returns (path data, advance width). Letters sit on the font's own advances; tracing to
    outlines is what frees every asset from needing the font installed."""
    f = ImageFont.truetype(FONT, px)
    ref = _mask("H", px); rys = np.where(ref.any(axis=1))[0]
    s = cap / (rys.max() - rys.min()); top = rys.min()
    x = 0.0; subs = []
    for ch in text:
        if ch.strip():
            m = _mask(ch, px)
            left = np.where(m.any(axis=0))[0].min()
            place = lambda pts: [(x + (a - left) * s, (b - top) * s) for a, b in pts]
            for shape in [m] + _holes(m):
                subs.append("M" + " L".join(f"{a:.2f},{b:.2f}" for a, b in
                                            place(_simplify(_trace(shape), eps))) + " Z")
        x += f.getlength(ch) * s + tracking * cap
    return " ".join(subs), x - tracking * cap

# ---------------------------------------------------------------- assets
def _svg(w, h, body, background=None):
    bg = f'<rect width="{w:g}" height="{h:g}" fill="{background}"/>' if background else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:g} {h:g}" width="{w:g}" '
            f'height="{h:g}" role="img">\n{bg}{body}\n</svg>\n')

# the tile runs 4..124 on the 128 grid, full-bleed cuts 0..128; the extent is the mark's larger
# side, centred on the tile centre, so the four margins are equal by construction
EXTENT_TILE = 104.0; EXTENT_BLEED = 116.0
FAVICON_BOOST = 2.4      # stroke and node scale for the 16 px cut

def _fit(extent, detail=True, boost=1.0, **colours):
    x0, y0, x1, y1 = mark_box(); s = extent / max(x1 - x0, y1 - y0)
    # strokes are divided back out by the scale, so a line keeps its weight at any tile size
    return (f'<g transform="translate(64,64) scale({s:.4f})">'
            f'{mark(detail=detail, weight=1 / s, boost=boost, **colours)}</g>')

def icon_svg():
    return _svg(128, 128, f'<rect x="4" y="4" width="120" height="120" rx="28" fill="{BLACK}"/>'
                + _fit(EXTENT_TILE))

def favicon_svg(rx=26, boost=1.0):
    """Small sizes: the faint outline, facets and mesh would turn to mud, so they are dropped."""
    return _svg(128, 128, f'<rect x="0" y="0" width="128" height="128" rx="{rx}" fill="{BLACK}"/>'
                + _fit(EXTENT_BLEED, detail=False, boost=boost))

def mono_svg():
    """One ink: every stroke and node in a single colour, the kernel read by its rings."""
    return _svg(128, 128, _fit(EXTENT_TILE, edge=BLACK, node_in=BLACK, node_out=BLACK,
                               core=BLACK, link=BLACK, mesh=BLACK, halo=WHITE))

WORD_CAP = 72.0; PAD = 28.0
SUB_CAP = 13.0; SUB_TRACK = 0.18      # the lockup line: cap height and tracking, in cap units

def wordmark_svg(night=True):
    """The word alone, without the mark: ink for paper, white for black grounds."""
    ink = WHITE if night else "#111111"
    word, ww = text_paths(WORD, WORD_CAP)
    w = ww + 2 * PAD; h = WORD_CAP + 2 * PAD
    body = f'<g transform="translate({PAD:.2f},{PAD:.2f})"><path d="{word}" fill="{ink}" fill-rule="evenodd"/></g>'
    return _svg(round(w, 2), round(h, 2), body)

def lockup_svg(W=680.0, H=520.0):
    """The full composition on its own black ground: the token, the word, the line."""
    x0, y0, x1, y1 = mark_box(); mh = y1 - y0
    cap = 44.0; word, ww = text_paths(WORD, cap)
    sub, sw = text_paths(SUBLINE, SUB_CAP, SUB_TRACK)
    word_gap = 58.0; sub_gap = 26.0
    block = mh + word_gap + cap + sub_gap + SUB_CAP
    cy = (H - block) / 2 + mh / 2; wy = cy + mh / 2 + word_gap
    body = (f'<g transform="translate({W / 2:g},{cy:.2f})">{mark()}</g>'
            f'<g transform="translate({(W - ww) / 2:.2f},{wy:.2f})">'
            f'<path d="{word}" fill="{WHITE}" fill-rule="evenodd"/></g>'
            f'<g transform="translate({(W - sw) / 2:.2f},{wy + cap + sub_gap:.2f})">'
            f'<path d="{sub}" fill="{SUBTLE}" fill-rule="evenodd"/></g>')
    return _svg(W, H, body, background=BLACK)

# ---------------------------------------------------------------- rasterising
RESVG = shutil.which("resvg")

def png(svg_path, out, width):
    if RESVG is None:
        sys.exit("resvg not found on PATH: install it (cargo install resvg) to rasterise the assets")
    subprocess.run([RESVG, "-w", str(width), svg_path, out], check=True)

def write(path, text):
    with open(path, "w") as fh: fh.write(text)

def main():
    pngdir = os.path.join(BRAND, "png"); os.makedirs(pngdir, exist_ok=True)
    svgs = {"icon.svg": icon_svg(), "favicon.svg": favicon_svg(), "icon-mono.svg": mono_svg(),
            "wordmark.svg": wordmark_svg(night=False), "wordmark-dark.svg": wordmark_svg(),
            "lockup.svg": lockup_svg()}
    for name, text in svgs.items(): write(os.path.join(BRAND, name), text)
    b = lambda n: os.path.join(BRAND, n); p = lambda n: os.path.join(pngdir, n)
    for sz in (512, 256, 180, 128): png(b("icon.svg"), p(f"icon-{sz}.png"), sz)
    for sz in (48, 32): png(b("favicon.svg"), p(f"favicon-{sz}.png"), sz)
    # at the smallest cut a hairline falls under a pixel, so it is drawn from a thicker cut
    tiny = os.path.join(HERE, "variants", "favicon-tiny.svg")
    os.makedirs(os.path.dirname(tiny), exist_ok=True)
    write(tiny, favicon_svg(boost=FAVICON_BOOST)); png(tiny, p("favicon-16.png"), 16)
    png(b("icon-mono.svg"), p("icon-mono-512.png"), 512)
    png(b("wordmark.svg"), p("wordmark.png"), 1120)
    png(b("wordmark-dark.svg"), p("wordmark-dark.png"), 1120)
    png(b("lockup.svg"), p("lockup.png"), 1360)
    # the org avatar: square to the edge, since GitHub applies its own crop (square, rounded,
    # circular); a rounded source would read as a double round with page-coloured corners
    avatar = os.path.join(HERE, "variants", "avatar.svg")
    os.makedirs(os.path.dirname(avatar), exist_ok=True)
    write(avatar, favicon_svg(rx=0)); png(avatar, p("avatar-512.png"), 512)
    Image.open(p("favicon-48.png")).save(p("favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
    # the org profile renders profile/README.md, so its images sit beside it
    if os.path.isdir(PROFILE):
        shutil.copyfile(p("icon-512.png"), os.path.join(PROFILE, "icon.png"))
        shutil.copyfile(p("lockup.png"), os.path.join(PROFILE, "lockup.png"))
    print("assets written: brand/, brand/png/, profile/")

if __name__ == "__main__":
    main()
