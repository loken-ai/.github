#!/usr/bin/env python3
"""LOKEN brand generator: the single source of every logo asset.

The mark is an open box seen in isometry: three white faces, the floor and the two far walls,
an outline that fades toward the back, and inside a block of eight tiles. The tile the kernel
works on is raised and takes the mint. The box is the machine, the tiles are the work, and the
front is open because nothing leaves and nothing is hidden.

The word loken is written with a broad nib, in one gesture. The line under it in the banner is
traced from a system font to outlines, so no asset contains text or depends on a font being
installed where it is displayed.

Everything is written once below. The SVGs are emitted from it and the PNGs are rasterised from
those SVGs with resvg, so vector and raster cannot drift. Run from this folder:

    python3 gen.py      # write ../*.svg, ../png/*, ../../profile/*
"""
import math, os, re, shutil, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
BRAND = os.path.dirname(HERE)
PROFILE = os.path.join(os.path.dirname(BRAND), "profile")

# ---------------------------------------------------------------- palette
FRAME = "#3B6FE0"                                   # the box outline, at the front
TILE = ("#12A8B6", "#0C8794", "#0A6B76")            # a tile: top face, right face, left face
KERNEL = ("#34D399", "#25B584", "#1B9068")          # the tile the kernel is working on
WALL = "#FFFFFF"                                    # the three faces seen from inside
TILE_EDGE = "#FFFFFF"                               # the outline of every tile
NIGHT = "#0B1020"                                   # the ground the mark is built for
INK_NIGHT = "#F2F4F8"; INK_PAPER = "#14161C"; SUBTLE = "#888888"
FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

WORD = "loken"
# The line under the word in the banner: what loken is, in three words.
SUBLINE = "SELF-HOSTED MULTIMODAL INFERENCE"

# ---------------------------------------------------------------- the box and its tiles
S3 = math.sqrt(3) / 2
U = 26.0                 # one cell of the box, in drawing units
N = 3                    # the box is N cells on a side
LIFT = 0.22              # how far the kernel's tile stands off the block
INSET = 0.0              # tiles touch; the white outline is what counts them
TILE_EDGE_W = 1.1
FRAME_W = 4.6
FADE = 0.62              # how far the back of the box is mixed into the ground
NEAR_CORNER = (1, 1, 1)  # the corner facing the viewer; its edges would cross the contents
LIT = (1, 0, 1)          # which tile of the block the kernel is on

CORNERS = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]
EDGES = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]

def iso(i, j, k):
    """Grid to screen. Depth grows with i + j + k, which is what orders the drawing."""
    return ((i - j) * S3 * U, (i + j) * U / 2 - k * U)

def _mix(a, b, t):
    """Colour a mixed toward colour b by t."""
    pa = [int(a[i:i + 2], 16) for i in (1, 3, 5)]; pb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02X%02X%02X" % tuple(round(pa[m] + (pb[m] - pa[m]) * t) for m in range(3))

def _poly(pts, fill, stroke=None, sw=0.0):
    p = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
    s = f' stroke="{stroke}" stroke-width="{sw:.2f}" stroke-linejoin="round"' if stroke else ""
    return f'<polygon points="{p}" fill="{fill}"{s}/>'

def walls(colour=WALL):
    """The three faces the viewer looks at from inside: the floor and the two far walls."""
    P = lambda i, j, k: iso(i * N, j * N, k * N)
    faces = [[P(0, 0, 0), P(1, 0, 0), P(1, 1, 0), P(0, 1, 0)],
             [P(0, 0, 0), P(1, 0, 0), P(1, 0, 1), P(0, 0, 1)],
             [P(0, 0, 0), P(0, 1, 0), P(0, 1, 1), P(0, 0, 1)]]
    return "".join(_poly(f, colour) for f in faces)

def frame(ground, w=FRAME_W, fade=FADE, ink=FRAME):
    """The box outline: one line per edge, its depth carried by the colour.

    The three edges meeting the near corner are left out: they would cross the tiles. Depth is
    mixed toward the ground rather than set as opacity, so every stroke is opaque and two edges
    meeting at a vertex read exactly like the edges themselves."""
    span = 3 * N; defs = []; lines = []
    for idx, (a, b) in enumerate(EDGES):
        A, B = CORNERS[a], CORNERS[b]
        if NEAR_CORNER in (A, B): continue
        pa = [c * N for c in A]; pb = [c * N for c in B]
        p = iso(*pa); q = iso(*pb)
        c1 = _mix(ink, ground, fade * (1 - sum(pa) / span))
        c2 = _mix(ink, ground, fade * (1 - sum(pb) / span))
        gid = f"e{idx}"
        defs.append(f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" '
                    f'x1="{p[0]:.2f}" y1="{p[1]:.2f}" x2="{q[0]:.2f}" y2="{q[1]:.2f}">'
                    f'<stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/>'
                    f'</linearGradient>')
        lines.append(f'<line x1="{p[0]:.2f}" y1="{p[1]:.2f}" x2="{q[0]:.2f}" y2="{q[1]:.2f}" '
                     f'stroke="url(#{gid})" stroke-width="{w:.2f}" stroke-linecap="round"/>')
    return "<defs>" + "".join(defs) + "</defs>", "".join(lines)

def tile_faces(i, j, k, cols, inset=INSET, edge=TILE_EDGE, sw=TILE_EDGE_W):
    """One tile as its three visible faces, each carrying its own depth."""
    a = inset; b = 1 - inset
    P = lambda di, dj, dk: iso(i + a + (b - a) * di, j + a + (b - a) * dj, k + a + (b - a) * dk)
    top = [P(0, 0, 1), P(1, 0, 1), P(1, 1, 1), P(0, 1, 1)]
    right = [P(1, 0, 1), P(1, 0, 0), P(1, 1, 0), P(1, 1, 1)]
    left = [P(0, 1, 1), P(1, 1, 1), P(1, 1, 0), P(0, 1, 0)]
    d = i + j + k
    return [(d + 1.5, _poly(top, cols[0], edge, sw)), (d + 1.42, _poly(right, cols[1], edge, sw)),
            (d + 1.4, _poly(left, cols[2], edge, sw))]

def mark(ground=NIGHT, n=2, frame_w=FRAME_W, edge_w=TILE_EDGE_W, one_ink=None):
    """The whole mark, drawn far to near. `one_ink` flattens it to a single colour."""
    if one_ink:
        wall_c = "#FFFFFF"; tile_c = (one_ink, one_ink, one_ink); kern_c = (one_ink,) * 3
        frame_defs, frame_art = "", "".join(
            f'<line x1="{iso(*[c * N for c in CORNERS[a]])[0]:.2f}" y1="{iso(*[c * N for c in CORNERS[a]])[1]:.2f}" '
            f'x2="{iso(*[c * N for c in CORNERS[b]])[0]:.2f}" y2="{iso(*[c * N for c in CORNERS[b]])[1]:.2f}" '
            f'stroke="{one_ink}" stroke-width="{frame_w:.2f}" stroke-linecap="round"/>'
            for a, b in EDGES if NEAR_CORNER not in (CORNERS[a], CORNERS[b]))
        edge_c = "#FFFFFF"
    else:
        wall_c = WALL; tile_c = TILE; kern_c = KERNEL; edge_c = TILE_EDGE
        frame_defs, frame_art = frame(ground, frame_w)
    prims = []
    off = (N - n) / 2
    for i in range(n):
        for j in range(n):
            for k in range(n):
                lit = (i, j, k) == LIT
                prims += tile_faces(i + off, j + off, k + off + (LIFT if lit else 0),
                                    kern_c if lit else tile_c, edge=edge_c, sw=edge_w)
    prims.sort(key=lambda p: p[0])
    art = walls(wall_c) + frame_art + "".join(s for _, s in prims)
    pts = [iso(i * N, j * N, k * N) for i in (0, 1) for j in (0, 1) for k in (0, 1)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    pad = frame_w / 2
    return frame_defs, art, (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)

# ---------------------------------------------------------------- the written word
NIB_ANGLE = -38.0        # the nib edge, fixed for the whole word so the ink shares one hand
HAIRLINE = 0.22          # thinnest stroke as a fraction of the nib width
NIB = 10.0
WORD_PATH = ("M0,98 C14,94 30,70 36,42 C40,20 34,6 28,10 C20,16 20,50 24,80 C26,96 34,102 44,98 "
             "C50,95 54,90 58,84 C60,70 70,60 80,60 C92,60 96,76 92,88 C88,100 72,102 68,92 "
             "C64,82 70,64 84,62 C92,62 98,66 104,68 C112,50 116,24 116,12 C116,2 106,4 106,18 "
             "C106,40 106,70 106,100 C106,86 110,66 124,64 C136,62 136,78 116,82 C128,84 132,98 142,99 "
             "C150,100 160,90 166,84 C172,80 184,74 180,66 C176,58 158,64 158,84 C158,100 176,102 186,94 "
             "C190,88 194,74 196,62 C196,76 196,90 196,100 C198,80 204,62 218,62 C232,62 230,80 230,96 "
             "C231,102 238,102 244,96")

def _cubics(d):
    nums = [float(v) for v in re.findall(r"-?\d+\.?\d*", d)]
    cur = (nums[0], nums[1]); out = []
    for i in range(2, len(nums), 6):
        p1, p2, p3 = (nums[i], nums[i + 1]), (nums[i + 2], nums[i + 3]), (nums[i + 4], nums[i + 5])
        out.append((cur, p1, p2, p3)); cur = p3
    return out

def _samples(d, step=1.2):
    pts = []
    for p0, p1, p2, p3 in _cubics(d):
        est = math.dist(p0, p1) + math.dist(p1, p2) + math.dist(p2, p3)
        n = max(4, int(est / step))
        for k in range(0 if not pts else 1, n + 1):
            t = k / n; u = 1 - t
            pts.append((u**3 * p0[0] + 3*u*u*t * p1[0] + 3*u*t*t * p2[0] + t**3 * p3[0],
                        u**3 * p0[1] + 3*u*u*t * p1[1] + 3*u*t*t * p2[1] + t**3 * p3[1]))
    return pts

def _nib_quads(d, width, angle=NIB_ANGLE):
    """The ink a broad nib leaves along a path, as quads wound the same way: a nonzero fill of
    them paints their union, with no boolean operation."""
    a = math.radians(angle); h = width / 2
    vx, vy = h * math.cos(a), h * math.sin(a)
    pts = _samples(d); quads = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        q = [(x0 - vx, y0 - vy), (x1 - vx, y1 - vy), (x1 + vx, y1 + vy), (x0 + vx, y0 + vy)]
        area = sum(q[m][0] * q[(m + 1) % 4][1] - q[(m + 1) % 4][0] * q[m][1] for m in range(4))
        quads.append(q if area > 0 else q[::-1])
    return quads

def written(ink, cap, nib=NIB):
    """The word at cap height `cap`: (svg, width, height). A narrow crossing nib keeps the
    hairlines from vanishing."""
    quads = _nib_quads(WORD_PATH, nib) + _nib_quads(WORD_PATH, nib * HAIRLINE, NIB_ANGLE + 90)
    xs = [x for q in quads for x, _ in q]; ys = [y for q in quads for _, y in q]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    s = cap / (y1 - y0)
    d = "".join("M" + " ".join(f"{(x - x0) * s:.2f},{(y - y0) * s:.2f}" for x, y in q) + "Z" for q in quads)
    return f'<path d="{d}" fill="{ink}" fill-rule="nonzero"/>', (x1 - x0) * s, cap

# ---------------------------------------------------------------- the line, traced to outlines
def _mask(ch, px):
    f = ImageFont.truetype(FONT, px)
    im = Image.new("L", (px * 2, int(px * 2.4)), 0)
    ImageDraw.Draw(im).text((px // 2, px // 2), ch, font=f, fill=255)
    return np.array(im) > 128

def _spread(seed, allowed):
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

    The background spreads over the eight neighbours, since a diagonal pair of ink pixels would
    otherwise seal a bay that the glyph leaves open: the open bay of an S, a C or a G has ink on
    four sides and is not a counter."""
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
    """`text` as outline subpaths at cap height `cap`, `tracking` in units of cap height."""
    f = ImageFont.truetype(FONT, px)
    rys = np.where(_mask("H", px).any(axis=1))[0]
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
SUB_CAP = 15.0; SUB_TRACK = 0.18

def _svg(w, h, body, background=None):
    bg = f'<rect width="{w:g}" height="{h:g}" fill="{background}"/>' if background else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:g} {h:g}" width="{w:g}" '
            f'height="{h:g}" role="img">\n{bg}{body}\n</svg>\n')

# the tile runs 4..124 on the 128 grid, full-bleed cuts 0..128; the extent is the mark's larger
# side, centred on the tile centre, so the four margins are equal by construction
EXTENT_TILE = 100.0; EXTENT_BLEED = 112.0

def _fit(extent, ground=NIGHT, **kw):
    defs, art, box = mark(ground=ground, **kw)
    bw = box[2] - box[0]; bh = box[3] - box[1]; s = extent / max(bw, bh)
    cx = (box[0] + box[2]) / 2; cy = (box[1] + box[3]) / 2
    return defs + (f'<g transform="translate(64,64) scale({s:.4f}) '
                   f'translate({-cx:.2f},{-cy:.2f})">{art}</g>')

def icon_svg():
    return _svg(128, 128, f'<rect x="4" y="4" width="120" height="120" rx="28" fill="{NIGHT}"/>'
                + _fit(EXTENT_TILE))

def favicon_svg(rx=26, boost=1.0):
    """Small sizes: the tile outlines and the box edges thicken, or they fall under a pixel."""
    return _svg(128, 128, f'<rect x="0" y="0" width="128" height="128" rx="{rx}" fill="{NIGHT}"/>'
                + _fit(EXTENT_BLEED, frame_w=FRAME_W * boost, edge_w=TILE_EDGE_W * boost))

def mono_svg():
    """One ink: the box and the tiles in a single colour, told apart by their white outlines."""
    return _svg(128, 128, _fit(EXTENT_TILE, one_ink="#14161C"))

WORD_CAP = 96.0; PAD = 28.0

def wordmark_svg(night=False):
    ink = INK_NIGHT if night else INK_PAPER
    word, ww, wh = written(ink, WORD_CAP)
    w = ww + 2 * PAD; h = wh + 2 * PAD
    return _svg(round(w, 2), round(h, 2),
                f'<g transform="translate({PAD:.2f},{PAD:.2f})">{word}</g>')

def banner_svg(W=1280.0, H=420.0, rx=24.0):
    """The header image: mark, written word and line on the dark ground the mark is built for."""
    defs, art, box = mark(ground=NIGHT)
    bw = box[2] - box[0]; bh = box[3] - box[1]; s = 280.0 / max(bw, bh)
    cx = (box[0] + box[2]) / 2; cy = (box[1] + box[3]) / 2
    word, ww, wh = written(INK_NIGHT, 104.0)
    sub, sw = text_paths(SUBLINE, SUB_CAP, SUB_TRACK)
    gap = 64.0; sub_gap = 30.0
    block = bw * s + gap + max(ww, sw)
    mx = (W - block) / 2 + bw * s / 2
    tx = (W - block) / 2 + bw * s + gap
    ty = (H - (wh + sub_gap + SUB_CAP)) / 2
    return _svg(W, H, defs +
                f'<rect x="0" y="0" width="{W:g}" height="{H:g}" rx="{rx:g}" fill="{NIGHT}"/>'
                f'<g transform="translate({mx:.2f},{H / 2:g}) scale({s:.4f}) '
                f'translate({-cx:.2f},{-cy:.2f})">{art}</g>'
                f'<g transform="translate({tx:.2f},{ty:.2f})">{word}</g>'
                f'<g transform="translate({tx:.2f},{ty + wh + sub_gap:.2f})">'
                f'<path d="{sub}" fill="{SUBTLE}" fill-rule="evenodd"/></g>')

# ---------------------------------------------------------------- rasterising
RESVG = shutil.which("resvg")
FAVICON_BOOST = 1.8      # stroke scale for the smallest cut

def png(svg_path, out, width):
    if RESVG is None:
        sys.exit("resvg not found on PATH: install it (cargo install resvg) to rasterise the assets")
    subprocess.run([RESVG, "-w", str(width), svg_path, out], check=True)

def write(path, text):
    with open(path, "w") as fh: fh.write(text)

def main():
    pngdir = os.path.join(BRAND, "png"); os.makedirs(pngdir, exist_ok=True)
    svgs = {"icon.svg": icon_svg(), "favicon.svg": favicon_svg(), "icon-mono.svg": mono_svg(),
            "wordmark.svg": wordmark_svg(), "wordmark-dark.svg": wordmark_svg(night=True),
            "banner.svg": banner_svg()}
    for name, text in svgs.items(): write(os.path.join(BRAND, name), text)
    b = lambda n: os.path.join(BRAND, n); p = lambda n: os.path.join(pngdir, n)
    for sz in (512, 256, 180, 128): png(b("icon.svg"), p(f"icon-{sz}.png"), sz)
    for sz in (48, 32): png(b("favicon.svg"), p(f"favicon-{sz}.png"), sz)
    png(b("icon-mono.svg"), p("icon-mono-512.png"), 512)
    png(b("wordmark.svg"), p("wordmark.png"), 1120)
    png(b("wordmark-dark.svg"), p("wordmark-dark.png"), 1120)
    png(b("banner.svg"), p("banner.png"), 1280)
    # published READMEs still link png/lockup.png; it carries the banner
    shutil.copyfile(p("banner.png"), p("lockup.png"))
    scratch = os.path.join(HERE, "variants"); os.makedirs(scratch, exist_ok=True)
    # at the smallest cut a hairline falls under a pixel, so it is drawn from a thicker one
    tiny = os.path.join(scratch, "favicon-tiny.svg")
    write(tiny, favicon_svg(boost=FAVICON_BOOST)); png(tiny, p("favicon-16.png"), 16)
    # the org avatar: square to the edge, since GitHub applies its own crop (square, rounded,
    # circular); a rounded source would read as a double round with page-coloured corners
    avatar = os.path.join(scratch, "avatar.svg")
    write(avatar, favicon_svg(rx=0)); png(avatar, p("avatar-512.png"), 512)
    Image.open(p("favicon-48.png")).save(p("favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
    if os.path.isdir(PROFILE):
        shutil.copyfile(p("icon-512.png"), os.path.join(PROFILE, "icon.png"))
        shutil.copyfile(p("banner.png"), os.path.join(PROFILE, "banner.png"))
    print("assets written: brand/, brand/png/, profile/")

if __name__ == "__main__":
    main()
