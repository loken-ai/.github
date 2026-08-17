#!/usr/bin/env python3
"""Check the assets that are about to be committed. Prints FAIL loudly; exits non-zero."""
import re, sys, os
from PIL import Image
import numpy as np

B=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]

def circles_of(d):
    """(cx, cy, r) of every token in a path — an arc pair per circle, centre bisecting each chord"""
    toks=re.findall(r'[MLAZmlaz]|-?\d*\.?\d+',d); i=0; cur=None; out=[]
    while i<len(toks):
        t=toks[i]
        if t in "MLml": cur=(float(toks[i+1]),float(toks[i+2])); i+=3
        elif t in "Aa":
            r=float(toks[i+1]); x,y=float(toks[i+6]),float(toks[i+7])
            out.append(((cur[0]+x)/2,(cur[1]+y)/2,r)); cur=(x,y); i+=8
        else: i+=1
    return out[::2]          # two half-arcs per circle; keep one entry each

def token_gaps(d):
    """clear ground between each pair of tokens — negative means they overlap, 0 means tangent"""
    cs=circles_of(d)
    return [((x2-x1)**2+(y2-y1)**2)**0.5-(r1+r2)
            for (x1,y1,r1),(x2,y2,r2) in zip(cs,cs[1:])] or [999]

def path_bbox(d):
    """Extent of an SVG path, honouring arc geometry.

    Reading every float in the `d` string is what made the first version of this check accuse
    correct files: `A12.00,12.00 0 1,0 ...` contributes two radii that are not coordinates.
    Commands are consumed with their real arity, and an arc's bulge is recovered from its
    chord — an arc's endpoints alone understate a circle by its whole vertical extent.
    """
    toks=re.findall(r'[MLAZmlaz]|-?\d*\.?\d+',d)
    i=0; cur=None; xs=[]; ys=[]
    def add(x,y): xs.append(x); ys.append(y)
    while i<len(toks):
        t=toks[i]
        if t in "MLml":
            x,y=float(toks[i+1]),float(toks[i+2]); add(x,y); cur=(x,y); i+=3
        elif t in "Aa":
            r=float(toks[i+1]); x,y=float(toks[i+6]),float(toks[i+7])
            cx,cy=((cur[0]+x)/2,(cur[1]+y)/2)      # semicircle: centre bisects the chord
            add(cx-r,cy-r); add(cx+r,cy+r); add(x,y)
            cur=(x,y); i+=8
        else: i+=1
    return min(min(xs),min(ys)), max(max(xs),max(ys))
def check(cond,label,detail=""):
    print(f"  {'ok  ' if cond else 'FAIL'}  {label}{'  '+detail if detail else ''}")
    if not cond: fails.append(label)

# ---- the SVG mark: structure, fill rule, and extent -------------------------------------
for name,exp_extent in (("icon.svg",80.0),("favicon.svg",86.0),("icon-mono.svg",80.0),):
    svg=open(f"{B}/{name}").read()
    print(f"{name}")
    paths=re.findall(r'<path d="([^"]+)"([^/]*)/>',svg)
    mark=paths[0]
    subs=[s for s in mark[0].split("M") if s.strip()]
    bars=sum(1 for s in subs if "A" not in s); circles=sum(1 for s in subs if "A" in s)
    check(circles==5,"5 tokens (incl. the accent)",f"got {circles}")
    check(bars==0,"no connectors — the tokens stand apart",f"got {bars}")
    gaps=token_gaps(mark[0])
    check(min(gaps)>0.5,"tokens do not touch",f"min gap {min(gaps):.1f}")
    lo,hi=path_bbox(mark[0])
    tile_lo,tile_hi=(0,128) if "favicon" in name else (4,124)
    if "mono" in name: tile_lo,tile_hi=(64-64,64+64)
    ml,mr=lo-tile_lo,tile_hi-hi
    check(abs(ml-mr)<0.05,"equal margins",f"left/top={ml:.1f} right/bottom={mr:.1f}")
    check(abs((hi-lo)-exp_extent)<0.05,f"extent {exp_extent:g}",f"got {hi-lo:.1f}")

# ---- the one-ink cut must still have five tokens ----------------------------------------
print("icon-mono-512.png")
a=np.array(Image.open(f"{B}/png/icon-mono-512.png").convert("RGBA"))
ink=a[:,:,3]>128
# count connected blobs the cheap way: the mark is one piece now, so instead assert the ink
# reaches the accent token's corner, which is what vanished when counter_col=None
top=np.where(ink.any(axis=1))[0].min(); left=np.where(ink.any(axis=0))[0].min()
check(ink[top:top+40, left:left+40].any(),"accent token present in the one-ink cut")

# ---- SVG vs PNG, if anything here can rasterise ------------------------------------------
print("svg -> png agreement")
try:
    import cairosvg, io
    png=cairosvg.svg2png(url=f"{B}/icon.svg",output_width=512,output_height=512)
    v=np.array(Image.open(io.BytesIO(png)).convert("RGBA"))[:,:,:3]
    p=np.array(Image.open(f"{B}/png/icon-512.png").convert("RGBA"))[:,:,:3]
    # compare the white ink only
    vm=(v>200).all(axis=2); pm=(p>200).all(axis=2)
    iou=(vm&pm).sum()/max(1,(vm|pm).sum())
    check(iou>=0.98,"IoU vector vs raster",f"{iou:.4f}")
except ImportError:
    print("  n/a   no SVG rasteriser available — structure checked above instead")

print()
print("FAILURES: "+", ".join(fails) if fails else "all checks passed")
sys.exit(1 if fails else 0)
