#!/usr/bin/env python3
"""LOKEN brand generator — single source of truth for the logo assets.

The mark is a token chain: five discrete circles tracing an L — three down the stem, three
across the base, sharing the corner — white on the indigo tile, the first one emerald. The
emerald circle is the brand device, and it carries into the wordmark as the counter of the O:
the same shape, the same ink, so the mark and the word read as one system.

The mark is generated from `chain()`, which is the only place its geometry is written; the
wordmark's five letters are traced from Quicksand-Bold to outlines. Nothing depends on a font
being installed where it is displayed. Run from this folder:

    python3 gen.py preview   # write review variants + preview.html into _work/
    python3 gen.py final     # write final assets into ../ (brand root), ../png/ and ../../profile/

WIP files live under _work/ (scratch — can be gitignored). Final assets go to brand/.
"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import math

HERE = os.path.dirname(os.path.abspath(__file__))
BRAND = os.path.dirname(HERE)
FONT = "/usr/share/fonts/truetype/quicksand/Quicksand-Bold.ttf"
FONT_TAG = "/usr/share/fonts/truetype/quicksand/Quicksand-Medium.ttf"
# the wordmark, and which letter carries the emerald counter. It has to be a letter that HAS
# one: L has no enclosed counter, so pointing at it dropped the accent from the wordmark
# entirely. The O is the only counter in LOKEN — and it is a circle, the mark's own shape.
WORD = "LOKEN"; ACC = 1
N = 1024; k = N / 128.0
def S(v): return v * k
IND_T=(55,48,163); IND_B=(49,46,129); EMLT=(52,211,153); EMDK=(5,150,105); TAG=(4,120,87)
HEX_INK="#312E81"; HEX_EM_ON_TILE="#34D399"; HEX_EM_ON_PAPER="#059669"; HEX_TAG="#047857"
TAGLINE = "LOCAL · MULTIMODAL · GREEN"

_sys = sys; _sys.setrecursionlimit(100000)

# ---------------------------------------------------------------- token chain mark (procedural)
def chain(extent=80.0):
    """The mark: five tokens tracing an L, as [(cx, cy, r, is_accent)] on the 128-unit grid.

    THE geometry — the SVG paths and the PNG both read it here, so the two cannot drift.

    Three tokens down the stem, three across the base, sharing the corner one. Radius and
    spacing are fractions of `extent` rather than typed numbers, which is what makes the two
    properties below hold at every size instead of only at the one that was eyeballed:

      spacing 0.35e, radius 0.15e  ->  0.05e of ground between neighbours. Tangent discs read
      as one poured shape; the gap is what makes them five countable tokens.
      total 2*spacing + 2*radius = e, first centre at 64 - spacing  ->  the ink's bounding box
      is [64-e/2, 64+e/2] on both axes, i.e. centred on the tile by construction.
    """
    r = 0.15 * extent; s = 0.35 * extent; x0 = y0 = 64.0 - s
    return [(x0,      y0,       r, True),    # stem top — the accent token
            (x0,      y0 + s,   r, False),   # stem middle
            (x0,      y0 + 2*s, r, False),   # the corner
            (x0 + s,  y0 + 2*s, r, False),   # base middle
            (x0 + 2*s, y0 + 2*s, r, False)]  # base end

def _circle_d(cx, cy, r):
    """One token as an SVG subpath: two half-arcs, an exact circle — not a polygon."""
    return (f"M{cx-r:.2f},{cy:.2f} A{r:.2f},{r:.2f} 0 1,0 {cx+r:.2f},{cy:.2f}"
            f" A{r:.2f},{r:.2f} 0 1,0 {cx-r:.2f},{cy:.2f} Z")

def _holes(mask):
    """Enclosed regions in a rasterised mask.

    A non-filled pixel is inside a counter when the shape closes over it on all four sides.
    Exact for letterform counters; it would under-report a crescent-shaped hole.
    """
    L=np.maximum.accumulate(mask,axis=1); R=np.maximum.accumulate(mask[:,::-1],axis=1)[:,::-1]
    U=np.maximum.accumulate(mask,axis=0); D=np.maximum.accumulate(mask[::-1],axis=0)[::-1]
    return (~mask)&L&R&U&D

# ---------------------------------------------------------------- the tile mark (PNG)
def icon(glyph_col=(255,255,255), counter_col=EMLT,
         tile_grad=True, fbleed=False, rx=28, tile=True, extent=80.0):
    c=Image.new('RGBA',(N,N),(0,0,0,0))
    if tile:
        tm=Image.new('L',(N,N),0)
        box=[0,0,N-1,N-1] if fbleed else [S(4),S(4),S(124),S(124)]
        ImageDraw.Draw(tm).rounded_rectangle(box,radius=S(rx),fill=255)
        if tile_grad:
            yy,xx=np.mgrid[0:N,0:N]; t=yy/(N-1); arr=np.zeros((N,N,3),np.uint8)
            for i in range(3): arr[:,:,i]=(IND_T[i]+(IND_B[i]-IND_T[i])*t).astype(np.uint8)
            c.paste(Image.fromarray(arr,'RGB'),(0,0),tm)
        else:
            c.paste(Image.new('RGB',(N,N),IND_B),(0,0),tm)
    d=ImageDraw.Draw(c)
    for cx,cy,r,accent in chain(extent):
        # a one-ink cut passes counter_col=None; the accent token then takes the body ink
        # rather than disappearing, which is what dropped the fifth token from the mono mark
        col = (counter_col or glyph_col) if accent else glyph_col
        d.ellipse([S(cx-r),S(cy-r),S(cx+r),S(cy+r)], fill=col)
    return c

# ---------------------------------------------------------------- contour tracing
def _mask_hi(target_h_units, res_px=1000):
    """render the glyph big, return (mask bool, bbox) at high res for tracing."""
    _,bb=_render_glyph(700); gh=bb[3]-bb[1]
    im,bb=_render_glyph(int(round(700*(res_px)/gh)))
    a=np.array(im)>128
    ys,xs=np.where(a); return a,(xs.min(),ys.min(),xs.max(),ys.max())

def _trace(mask):
    P=np.pad(mask,1); ys,xs=np.where(P); y0=ys.min(); x0=int(xs[ys==y0].min())
    start=(y0,x0); nb=[(0,-1),(-1,-1),(-1,0),(-1,1),(0,1),(1,1),(1,0),(1,-1)]
    cur=start; back=(y0,x0-1); cont=[start]; steps=0
    while steps<5_000_000:
        steps+=1; d=(back[0]-cur[0],back[1]-cur[1]); bi=nb.index(d); nxt=None
        for kk in range(1,9):
            idx=(bi+kk)%8; c=(cur[0]+nb[idx][0],cur[1]+nb[idx][1])
            if P[c]: nxt=c; back=(cur[0]+nb[(idx-1)%8][0],cur[1]+nb[(idx-1)%8][1]); break
        if nxt is None: break
        cur=nxt; cont.append(cur)
        if cur==start and steps>3: break
    return [(x-1,y-1) for (y,x) in cont]

def _dp(pts,eps):
    if len(pts)<3: return pts
    a=np.array(pts[0],float); b=np.array(pts[-1],float); ab=b-a; L=np.hypot(*ab)
    if L==0: d=np.hypot(*(np.array(pts,float)-a).T)
    else: d=np.abs(np.cross(ab,np.array(pts,float)-a))/L
    idx=int(np.argmax(d))
    if d[idx]>eps: return _dp(pts[:idx+1],eps)[:-1]+_dp(pts[idx:],eps)
    return [pts[0],pts[-1]]

def _sub(P): return "M"+" L".join(f"{x:.2f},{y:.2f}" for x,y in P)+" Z"

def glyph_path(extent=80.0):
    """The mark at overall size `extent`: (body_d, accent_d, token count, bbox).

    Body and accent are separate so the accent can be overpainted in a second ink; the tokens
    are disjoint, so filling body+accent under evenodd gives the whole mark in one colour.
    """
    cs=chain(extent)
    body=" ".join(_circle_d(cx,cy,r) for cx,cy,r,a in cs if not a)
    accent=" ".join(_circle_d(cx,cy,r) for cx,cy,r,a in cs if a)
    xs=[cx+sg*r for cx,_,r,_ in cs for sg in (-1,1)]
    ys=[cy+sg*r for _,cy,r,_ in cs for sg in (-1,1)]
    return body,accent,len(cs),(min(xs),min(ys),max(xs),max(ys))

# ---------------------------------------------------------------- the wordmark, as outlines
def _word_masks(word, px=500):
    """each letter rasterised in the SAME frame, laid out on the font's own advances"""
    f=ImageFont.truetype(FONT,px)
    C=(int(f.getlength(word)+px*2), int(px*2.5)); X0=Y0=px*0.5
    out=[]
    for i,ch in enumerate(word):
        im=Image.new("L",C,0)
        ImageDraw.Draw(im).text((X0+f.getlength(word[:i]),Y0),ch,font=f,fill=255)
        out.append((ch,np.array(im)>128))
    return out

def word_paths(word, cap_h, ox, oy, eps=0.6):
    """Outline every letter at cap height cap_h, positioned at (ox, oy).

    Returns (letters, width) where letters is [(ch, outer_d, hole_d|None)]. Tracing to
    outline paths allows colourizing the accent letter and eliminates font dependencies.
    """
    masks=_word_masks(word)
    union=np.zeros_like(masks[0][1])
    for _,m in masks: union|=m
    ys,xs=np.where(union); x0,y0,x1,y1=xs.min(),ys.min(),xs.max(),ys.max()
    sc=cap_h/(y1-y0)
    place=lambda pts:[(ox+(x-x0)*sc, oy+(y-y0)*sc) for (x,y) in pts]
    letters=[]
    for ch,m in masks:
        outer=_sub(place(_dp(_trace(m),eps)))
        h=_holes(m)
        letters.append((ch,outer,_sub(place(_dp(_trace(h),eps))) if h.any() else None))
    return letters,(x1-x0)*sc

def _word_svg(word, cap_h, ox, oy, ink=HEX_INK, acc=HEX_EM_ON_PAPER):
    letters,w=word_paths(word,cap_h,ox,oy)
    body="".join(f'\n  <path d="{o}{" "+h if h else ""}" fill="{ink}" fill-rule="evenodd"/>'
                 for _,o,h in letters)
    counter="".join(f'\n  <path d="{h}" fill="{acc}"/>'
                    for i,(_,_,h) in enumerate(letters) if h and i==ACC)
    return body+counter, w

# ---------------------------------------------------------------- SVG assets
TILE='<linearGradient id="t" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3730A3"/><stop offset="1" stop-color="#312E81"/></linearGradient>'
def _svg_icon(d,hole,fbleed=False,rx=28):
    box='x="0" y="0" width="128" height="128"' if fbleed else 'x="4" y="4" width="120" height="120"'
    fill='#312E81' if fbleed else 'url(#t)'
    counter=f'\n  <path d="{hole}" fill="{HEX_EM_ON_TILE}"/>' if hole else ''
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">\n'
            f'  <defs>{TILE}</defs>\n  <rect {box} rx="{rx}" fill="{fill}"/>\n'
            f'  <path d="{d}{" "+hole if hole else ""}" fill="#FFFFFF" fill-rule="nonzero"/>'
            f'{counter}\n</svg>\n')

def _svg_mono(d,hole):
    """Monochrome mark: every token and bar in a single ink."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">\n'
            f'  <path d="{d}{" "+hole if hole else ""}" fill="#059669" fill-rule="nonzero"/>\n</svg>\n')

def _svg_tagline(x,y,size,spacing,anchor="start"):
    return (f'\n  <text x="{x}" y="{y}" text-anchor="{anchor}" font-family="system-ui,sans-serif"'
            f' font-weight="500" font-size="{size}" letter-spacing="{spacing}" fill="{HEX_TAG}">'
            f'{TAGLINE}</text>')

def _svg_lockup(d,hole):
    body,w=_word_svg(WORD,72,192,46)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {int(192+w+24)} 200" '
            f'width="{int(192+w+24)}" height="200">\n'
            f'  <defs>{TILE}</defs>\n'
            f'  <g transform="translate(24,36)"><rect x="0" y="0" width="128" height="128" rx="28" fill="url(#t)"/>'
            f'<path d="{d}{" "+hole if hole else ""}" fill="#FFFFFF" fill-rule="nonzero"/>'
            + (f'<path d="{hole}" fill="{HEX_EM_ON_TILE}"/>' if hole else '')
            + f'</g>{body}'
            + _svg_tagline(194,150,15,4.4) + '\n</svg>\n')

def _svg_wordmark():
    body,w=_word_svg(WORD,104,40,38)
    W=int(w+80)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} 200" width="{W}" height="200">'
            f'{body}' + _svg_tagline(W/2,178,17,5.2,anchor="middle") + '\n</svg>\n')

# ---------------------------------------------------------------- PNG wordmark
def _wordmark(W,H,with_icon=False,ic=None):
    """Render wordmark in Quicksand-Bold with accent letter's counter highlighted."""
    im=Image.new('RGBA',(W,H),(0,0,0,0)); dd=ImageDraw.Draw(im)
    f=ImageFont.truetype(FONT,200); fs=ImageFont.truetype(FONT_TAG,30)
    xoff=0
    if with_icon and ic is not None:
        im.alpha_composite(ic.resize((240,240),Image.LANCZOS),(30,60)); xoff=300
    ww=dd.textlength(WORD,font=f)
    x=(xoff+((W-xoff)-ww)//2) if not with_icon else xoff+20
    dd.text((x,70),WORD,font=f,fill=IND_B)
    # the accent letter, in the same frame so it lands exactly on its wordmark position
    lm=Image.new('L',(W,H),0)
    ImageDraw.Draw(lm).text((x+dd.textlength(WORD[:ACC],font=f),70),WORD[ACC],font=f,fill=255)
    h=_holes(np.array(lm)>128)
    if h.any(): im.paste(Image.new('RGBA',(W,H),EMDK+(255,)),(0,0),
                         Image.fromarray(h.astype(np.uint8)*255))
    tag="  ".join(TAGLINE.split(" ")); tw=dd.textlength(tag,font=fs)
    dd.text(((xoff+((W-xoff)-tw)//2) if not with_icon else xoff+22,300),tag,font=fs,fill=TAG)
    return im

# ---------------------------------------------------------------- outputs
def final():
    png=os.path.join(BRAND,"png"); os.makedirs(png,exist_ok=True)
    d,hole,n,bb=glyph_path(80.0); df,holef,_,_=glyph_path(86.0)
    cs=chain(80.0); gap=(cs[1][1]-cs[0][1])-2*cs[0][2]
    # the tile runs 4..124, so equal margins on the four sides IS the centring test — report
    # them rather than a centre coordinate, because unequal margins are the visible defect
    ml,mr,mt,mb = bb[0]-4, 124-bb[2], bb[1]-4, 124-bb[3]
    ok = "OK" if max(abs(ml-mr),abs(mt-mb)) < 0.01 else "*** UNEQUAL ***"
    print(f"token chain: {n} tokens, accent={'yes' if hole else 'NO'}, gap between tokens={gap:.1f}\n"
          f"  margins  left={ml:.1f} right={mr:.1f} | top={mt:.1f} bottom={mb:.1f}  -> {ok}")
    open(os.path.join(BRAND,"icon.svg"),"w").write(_svg_icon(d,hole))
    open(os.path.join(BRAND,"favicon.svg"),"w").write(_svg_icon(df,holef,fbleed=True,rx=26))
    open(os.path.join(BRAND,"icon-mono.svg"),"w").write(_svg_mono(d,hole))
    open(os.path.join(BRAND,"lockup.svg"),"w").write(_svg_lockup(d,hole))
    open(os.path.join(BRAND,"wordmark.svg"),"w").write(_svg_wordmark())
    # the full-bleed cuts carry the larger mark (86 vs 80), matching favicon.svg — passing the
    # extent here is what keeps the PNG and the SVG the same drawing
    ic=icon(); fv=icon(tile_grad=False,fbleed=True,rx=26,extent=86.0)
    mo=icon(glyph_col=EMDK,counter_col=None,tile=False)
    for sz in (512,256,180,128): ic.resize((sz,sz),Image.LANCZOS).save(f"{png}/icon-{sz}.png")
    for sz in (48,32,16): fv.resize((sz,sz),Image.LANCZOS).save(f"{png}/favicon-{sz}.png")
    mo.resize((512,512),Image.LANCZOS).save(f"{png}/icon-mono-512.png")
    # the org/profile avatar: square to the edge, no rounding of our own. GitHub puts the
    # avatar in its own container shape, so a rounded source would read as a double round and
    # its transparent corners would take the colour of whatever page it sits on.
    icon(tile_grad=True,fbleed=True,rx=0,extent=86.0).resize((512,512),Image.LANCZOS).save(f"{png}/avatar-512.png")
    fv.resize((48,48),Image.LANCZOS).save(f"{png}/favicon.ico",sizes=[(16,16),(32,32),(48,48)])
    _wordmark(1120,360).save(f"{png}/wordmark.png"); _wordmark(1360,360,True,ic).save(f"{png}/lockup.png")
    # the org profile renders profile/README.md, so its images must resolve beside it —
    # generated here rather than copied by hand, so there is one source, not two
    prof=os.path.join(os.path.dirname(BRAND),"profile")
    if os.path.isdir(prof):
        ic.resize((512,512),Image.LANCZOS).save(f"{prof}/icon.png")
        _wordmark(1360,360,True,ic).save(f"{prof}/lockup.png")
        print("profile images → profile/")
    print("final assets → brand/ + brand/png/")

def preview():
    o=os.path.join(HERE,"variants"); os.makedirs(o,exist_ok=True)
    icon().resize((512,512),Image.LANCZOS).save(f"{o}/accent.png")
    icon(counter_col=None).resize((512,512),Image.LANCZOS).save(f"{o}/plain.png")
    icon(glyph_col=EMDK,counter_col=None,tile=False).resize((512,512),Image.LANCZOS).save(f"{o}/mono.png")
    icon(tile_grad=False,fbleed=True,rx=26,extent=86.0).resize((512,512),Image.LANCZOS).save(f"{o}/fav.png")
    html="""<!doctype html><meta charset=utf-8><title>LOKEN Chain</title>
<body style="font-family:system-ui;background:#fafafb;margin:0;padding:32px">
<h2>LOKEN — Token Chain (5 circles in L shape), emerald accent</h2>
<div style="display:flex;gap:24px;align-items:flex-end;flex-wrap:wrap">
<div style=text-align:center><div style="background:#fff;padding:14px;border-radius:16px;box-shadow:0 1px 6px #0001"><img src=variants/accent.png width=120></div>accent (top circle emerald)</div>
<div style=text-align:center><div style="background:#fff;padding:14px;border-radius:16px;box-shadow:0 1px 6px #0001"><img src=variants/plain.png width=120></div>plain (all white)</div>
<div style=text-align:center><div style="background:#fff;padding:14px;border-radius:16px;box-shadow:0 1px 6px #0001"><img src=variants/mono.png width=120></div>one ink</div>
<div style=text-align:center><div style="background:#0b1020;padding:14px;border-radius:16px"><img src=variants/accent.png width=120></div>on dark</div>
<div style=text-align:center><img src=variants/accent.png width=48><br><img src=variants/fav.png width=32><br><img src=variants/fav.png width=16><div style=font-size:12px;opacity:.5>small</div></div>
</div></body>"""
    open(os.path.join(HERE,"preview.html"),"w").write(html)
    print("preview → _work/preview.html")

if __name__=="__main__":
    mode=sys.argv[1] if len(sys.argv)>1 else "preview"
    if mode=="preview": preview()
    elif mode=="final": final()
    else: print("usage: gen.py [preview|final]")
