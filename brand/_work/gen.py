#!/usr/bin/env python3
"""LOKEN brand generator: the single source of every logo asset.

The mark is a looped l written with a broad nib on the indigo tile. Its exit stroke is
emitted as four shrinking tokens, the second one lit in emerald. The wordmark is the word
loken written with the same nib; its last stroke rises from ink to emerald and sets down a
light. No asset carries text or depends on an installed font.

Every shape is vector geometry written once below. SVGs are emitted from it and PNGs are
rasterised from those SVGs with resvg, so vector and raster are the same drawing. Run from
this folder:

    python3 gen.py      # write ../*.svg, ../png/*, ../../profile/*
"""
import math, os, re, shutil, subprocess, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BRAND = os.path.dirname(HERE)
PROFILE = os.path.join(os.path.dirname(BRAND), "profile")

INDIGO_TOP = "#3730A3"; INDIGO = "#312E81"; WHITE = "#FFFFFF"
EMERALD_ON_TILE = "#34D399"; EMERALD_ON_PAPER = "#059669"
INK_ON_NIGHT = "#ECEBFA"

# ---------------------------------------------------------------- broad-nib geometry
NIB_ANGLE = -38.0      # degrees; the nib edge, fixed for every stroke so all ink shares one hand
HAIRLINE = 0.22        # thinnest stroke as a fraction of the nib width

def _cubics(d):
    """Parse an absolute M/C path into [(p0, p1, p2, p3)]."""
    nums = [float(v) for v in re.findall(r"-?\d+\.?\d*", d)]
    cur = (nums[0], nums[1]); out = []
    for i in range(2, len(nums), 6):
        p1, p2, p3 = (nums[i], nums[i + 1]), (nums[i + 2], nums[i + 3]), (nums[i + 4], nums[i + 5])
        out.append((cur, p1, p2, p3)); cur = p3
    return out

def _samples(d, step=1.2):
    """Points along the path, at most `step` units apart (chord estimate per cubic)."""
    pts = []
    for p0, p1, p2, p3 in _cubics(d):
        est = math.dist(p0, p1) + math.dist(p1, p2) + math.dist(p2, p3)
        n = max(4, int(est / step))
        for k in range(0 if not pts else 1, n + 1):
            t = k / n; u = 1 - t
            pts.append((u**3 * p0[0] + 3*u*u*t * p1[0] + 3*u*t*t * p2[0] + t**3 * p3[0],
                        u**3 * p0[1] + 3*u*u*t * p1[1] + 3*u*t*t * p2[1] + t**3 * p3[1]))
    return pts

def nib(d, width, angle=NIB_ANGLE):
    """Outline of a broad nib of `width` dragged along path `d`, as quads [(4 points)].

    Each quad spans two neighbouring samples; all are wound the same way, so a nonzero fill of
    their concatenation paints exactly the union, the swept ink, with no boolean operation.
    """
    a = math.radians(angle); h = width / 2
    vx, vy = h * math.cos(a), h * math.sin(a)
    pts = _samples(d); quads = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        q = [(x0 - vx, y0 - vy), (x1 - vx, y1 - vy), (x1 + vx, y1 + vy), (x0 + vx, y0 + vy)]
        area = sum(q[i][0] * q[(i + 1) % 4][1] - q[(i + 1) % 4][0] * q[i][1] for i in range(4))
        quads.append(q if area > 0 else q[::-1])
    return quads

class Drawing:
    """Ink primitives in their own units, with the ink box they cover."""
    def __init__(self):
        self.items = []; self.box = [math.inf, math.inf, -math.inf, -math.inf]
    def _grow(self, x, y):
        b = self.box; b[0] = min(b[0], x); b[1] = min(b[1], y); b[2] = max(b[2], x); b[3] = max(b[3], y)
    def stroke(self, d, width, paint):
        """A nib stroke; a narrow crossing nib gives the hairlines a floor of HAIRLINE x width."""
        q = nib(d, width) + nib(d, width * HAIRLINE, NIB_ANGLE + 90); self.items.append(("quads", q, paint))
        for quad in q:
            for x, y in quad: self._grow(x, y)
    def disc(self, x, y, r, paint):
        self.items.append(("disc", x, y, r, paint)); self._grow(x - r, y - r); self._grow(x + r, y + r)
    def glow(self, x, y, r, gid):
        """A halo; it does not count toward the ink box, so it never shifts the centring."""
        self.items.append(("glow", x, y, r, gid))
    def svg(self, dx, dy, s):
        """The primitives mapped by (x, y) -> (dx + s*x, dy + s*y)."""
        f = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")
        out = []
        for it in self.items:
            if it[0] == "quads":
                d = "".join("M" + " ".join(f"{f(dx + s*x)},{f(dy + s*y)}" for x, y in q) + "Z" for q in it[1])
                out.append(f'<path d="{d}" fill="{it[2]}" fill-rule="nonzero"/>')
            elif it[0] == "disc":
                out.append(f'<circle cx="{f(dx + s*it[1])}" cy="{f(dy + s*it[2])}" r="{f(s*it[3])}" fill="{it[4]}"/>')
            else:
                out.append(f'<circle cx="{f(dx + s*it[1])}" cy="{f(dy + s*it[2])}" r="{f(s*it[3])}" fill="url(#{it[4]})"/>')
        return "".join(out)
    def fit(self, cx, cy, extent):
        """Transform that centres the ink box on (cx, cy) with its larger side equal to extent."""
        w = self.box[2] - self.box[0]; h = self.box[3] - self.box[1]; s = extent / max(w, h)
        return cx - s * (self.box[0] + w / 2), cy - s * (self.box[1] + h / 2), s

# ---------------------------------------------------------------- the mark
LOOP_L = ("M18,100 C32,96 48,72 54,44 C58,22 52,8 46,12 C38,18 38,52 42,82 C44,98 52,104 62,100 "
          "C70,97 76,90 80,82")
TOKENS = [(87, 71, 5.6), (92, 59, 4.7), (96, 48, 3.9), (99, 38, 3.2)]
LIT = 1                  # the token that glows: the second one emitted

def mark(ink=WHITE, lit=EMERALD_ON_TILE, halo=True):
    """The looped l and its token stream. `lit=None` gives the one-ink cut."""
    m = Drawing(); m.stroke(LOOP_L, 10.0, ink)
    for i, (x, y, r) in enumerate(TOKENS):
        if i == LIT and lit:
            if halo: m.glow(x, y, r * 2.4, "halo")
            m.disc(x, y, r + 0.6, lit)
        else:
            m.disc(x, y, r, ink)
    return m

# ---------------------------------------------------------------- the wordmark
WORD = ("M0,98 C14,94 30,70 36,42 C40,20 34,6 28,10 C20,16 20,50 24,80 C26,96 34,102 44,98 "
        "C50,95 54,90 58,84 C60,70 70,60 80,60 C92,60 96,76 92,88 C88,100 72,102 68,92 "
        "C64,82 70,64 84,62 C92,62 98,66 104,68 C112,50 116,24 116,12 C116,2 106,4 106,18 "
        "C106,40 106,70 106,100 C106,86 110,66 124,64 C136,62 136,78 116,82 C128,84 132,98 142,99 "
        "C150,100 160,90 166,84 C172,80 184,74 180,66 C176,58 158,64 158,84 C158,100 176,102 186,94 "
        "C190,88 194,74 196,62 C196,76 196,90 196,100 C198,80 204,62 218,62 C232,62 230,80 230,96 "
        "C231,102 238,102 244,96")
WORD_TAIL = "M244,96 C256,84 266,62 274,42"
WORD_LIGHT = (278, 34, 5.0)

def word(ink, light):
    """The written word, its rising tail and the light it sets down; the box covers the letters."""
    w = Drawing(); w.stroke(WORD, 7.0, ink)
    letters = list(w.box)
    w.stroke(WORD_TAIL, 5.0, "url(#tail)")
    x, y, r = WORD_LIGHT; w.glow(x, y, r * 3.2, "light"); w.disc(x, y, r, light)
    return w, letters

# ---------------------------------------------------------------- SVG assets
def _defs(emerald, ink=None, tail_box=None, tile=True):
    d = []
    if tile:
        d.append(f'<linearGradient id="t" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{INDIGO_TOP}"/>'
                 f'<stop offset="1" stop-color="{INDIGO}"/></linearGradient>')
    d.append(f'<radialGradient id="halo"><stop offset="0" stop-color="{emerald}" stop-opacity=".6"/>'
             f'<stop offset="1" stop-color="{emerald}" stop-opacity="0"/></radialGradient>')
    if tail_box:
        x1, y1, x2, y2 = tail_box
        d.append(f'<radialGradient id="light"><stop offset="0" stop-color="{emerald}" stop-opacity=".5"/>'
                 f'<stop offset="1" stop-color="{emerald}" stop-opacity="0"/></radialGradient>'
                 f'<linearGradient id="tail" gradientUnits="userSpaceOnUse" x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}">'
                 f'<stop offset="0" stop-color="{ink}"/><stop offset=".55" stop-color="{emerald}" stop-opacity=".8"/>'
                 f'<stop offset="1" stop-color="{emerald}" stop-opacity="0"/></linearGradient>')
    return "<defs>" + "".join(d) + "</defs>"

def _svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:g} {h:g}" width="{w:g}" height="{h:g}">\n'
            f'{body}\n</svg>\n')

# the tile is 4..124 on the 128 grid; full-bleed cuts use 0..128. The extent is the larger side
# of the ink box, centred on the tile centre, so the margins are equal by construction.
EXTENT_TILE = 84.0; EXTENT_BLEED = 92.0

def icon_svg():
    m = mark(); dx, dy, s = m.fit(64, 64, EXTENT_TILE)
    return _svg(128, 128, _defs(EMERALD_ON_TILE) +
                '<rect x="4" y="4" width="120" height="120" rx="28" fill="url(#t)"/>' + m.svg(dx, dy, s))

def favicon_svg(rx=26, gradient=False):
    m = mark(); dx, dy, s = m.fit(64, 64, EXTENT_BLEED)
    fill = "url(#t)" if gradient else INDIGO
    return _svg(128, 128, _defs(EMERALD_ON_TILE) +
                f'<rect x="0" y="0" width="128" height="128" rx="{rx}" fill="{fill}"/>' + m.svg(dx, dy, s))

def mono_svg():
    m = mark(ink=EMERALD_ON_PAPER, lit=None); dx, dy, s = m.fit(64, 64, EXTENT_TILE)
    return _svg(128, 128, m.svg(dx, dy, s))

def _tail_box(dx, dy, s):
    (x1, y1), (x2, y2) = _cubics(WORD_TAIL)[0][0], _cubics(WORD_TAIL)[0][3]
    return (dx + s * x1, dy + s * y1, dx + s * x2, dy + s * y2)

WORD_HEIGHT = 108.0      # letter box height in lockup units, against a tile side of 128
GAP = 36.0               # tile edge to first letter
PAD = 24.0

def wordmark_svg(night=False):
    ink = INK_ON_NIGHT if night else INDIGO; em = EMERALD_ON_TILE if night else EMERALD_ON_PAPER
    w, letters = word(ink, em); s = WORD_HEIGHT / (letters[3] - letters[1])
    dx = PAD - s * letters[0]; dy = PAD - s * letters[1]
    W = dx + s * w.box[2] + PAD; H = PAD * 2 + WORD_HEIGHT
    top = min(0.0, dy + s * w.box[1] - PAD)          # the light may rise above the letters
    return _svg(W, H - top, f'<g transform="translate(0,{-top:.2f})">' +
                _defs(em, ink, _tail_box(dx, dy, s), tile=False) + w.svg(dx, dy, s) + "</g>")

def lockup_svg(night=False):
    ink = INK_ON_NIGHT if night else INDIGO; em = EMERALD_ON_TILE if night else EMERALD_ON_PAPER
    m = mark(); mx, my, ms = m.fit(64, 64, EXTENT_TILE)
    w, letters = word(ink, em); s = WORD_HEIGHT / (letters[3] - letters[1])
    ox = PAD + 128 + GAP; dx = ox - s * letters[0]; dy = PAD + 64 - s * (letters[1] + letters[3]) / 2
    W = dx + s * w.box[2] + PAD; H = PAD * 2 + 128
    top = min(0.0, dy + s * w.box[1] - PAD)
    defs = _defs(em, ink, _tail_box(dx, dy, s)).replace('id="halo"><stop offset="0" stop-color="' + em,
                                                        'id="halo"><stop offset="0" stop-color="' + EMERALD_ON_TILE)
    return _svg(W, H - top, f'<g transform="translate(0,{-top:.2f})">' + defs +
                f'<g transform="translate({PAD:g},{PAD:g})">'
                '<rect x="0" y="0" width="128" height="128" rx="28" fill="url(#t)"/>'
                f'{m.svg(mx, my, ms)}</g>{w.svg(dx, dy, s)}</g>')

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
            "wordmark.svg": wordmark_svg(), "wordmark-dark.svg": wordmark_svg(night=True),
            "lockup.svg": lockup_svg(), "lockup-dark.svg": lockup_svg(night=True)}
    for name, text in svgs.items(): write(os.path.join(BRAND, name), text)
    b = lambda n: os.path.join(BRAND, n); p = lambda n: os.path.join(pngdir, n)
    for sz in (512, 256, 180, 128): png(b("icon.svg"), p(f"icon-{sz}.png"), sz)
    for sz in (48, 32, 16): png(b("favicon.svg"), p(f"favicon-{sz}.png"), sz)
    png(b("icon-mono.svg"), p("icon-mono-512.png"), 512)
    png(b("wordmark.svg"), p("wordmark.png"), 1120)
    png(b("lockup.svg"), p("lockup.png"), 1360)
    png(b("lockup-dark.svg"), p("lockup-dark.png"), 1360)
    # the org avatar: square to the edge, since GitHub applies its own crop (square, rounded,
    # circular); a rounded source would read as a double round with page-coloured corners
    avatar = os.path.join(HERE, "variants", "avatar.svg"); os.makedirs(os.path.dirname(avatar), exist_ok=True)
    write(avatar, favicon_svg(rx=0, gradient=True)); png(avatar, p("avatar-512.png"), 512)
    Image.open(p("favicon-48.png")).save(p("favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
    # the org profile renders profile/README.md, so its images sit beside it
    if os.path.isdir(PROFILE):
        shutil.copyfile(p("icon-512.png"), os.path.join(PROFILE, "icon.png"))
        shutil.copyfile(p("lockup.png"), os.path.join(PROFILE, "lockup.png"))
        shutil.copyfile(p("lockup-dark.png"), os.path.join(PROFILE, "lockup-dark.png"))
    print("assets written: brand/, brand/png/, profile/")

if __name__ == "__main__":
    main()
