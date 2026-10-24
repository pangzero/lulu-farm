"""Editable vector eye drawn from the original turnaround's screen-left eye.

This is a deterministic vector asset, rasterized for a mesh UV texture. It has
no socket shading, baked crease or normal/displacement channel.
"""
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw

SEGMENTS=[
    ((.045,.62),(.04,.35),(.23,.08),(.55,.06)),
    ((.55,.06),(.82,.025),(1.01,.25),(.965,.55)),
    ((.965,.55),(.93,.82),(.69,.97),(.39,.94)),
    ((.39,.94),(.19,.92),(.055,.82),(.045,.62)),
]

def generate(folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    n=1536;t=np.linspace(0,1,100)
    points=[]
    for v in SEGMENTS:
        a,b,c,d=np.array(v);p=(1-t[:,None])**3*a+3*(1-t[:,None])**2*t[:,None]*b+3*(1-t[:,None])*t[:,None]**2*c+t[:,None]**3*d
        points.extend((p*n).tolist())
    mask=Image.new('L',(n,n));draw=ImageDraw.Draw(mask);draw.polygon([tuple(p) for p in points],fill=255)
    outline=Image.new('L',(n,n));ImageDraw.Draw(outline).line([tuple(p) for p in points]+[tuple(points[0])],fill=255,width=round(n*.008),joint='curve')
    yy,xx=np.mgrid[:n,:n];u=(xx+.5)/n;v=(yy+.5)/n
    col=np.zeros((n,n,3),float);col[:]=[255,253,239]
    iris=((u-.62)/.35)**2+((v-.50)/.44)**2<1
    g=np.clip((u-.27)/.70,0,1)
    blue=np.array([109,159,218])[None,None,:]*(1-g[...,None])+np.array([48,91,149])[None,None,:]*g[...,None]
    col[iris]=blue[iris]
    pupil=((u-.695)/.28)**2+((v-.545)/.36)**2<1
    col[pupil]=np.c_[np.full(pupil.sum(),3),np.full(pupil.sum(),7),np.full(pupil.sum(),12)]
    highlight=((u-.79)/.086)**2+((v-.305)/.075)**2<1
    col[highlight&iris]=[255,255,253]
    stroke=np.asarray(outline).astype(float)/255
    col=col*(1-stroke[...,None])+np.array([47,54,52])*stroke[...,None]
    rgba=np.dstack([np.clip(col,0,255).astype('uint8'),np.asarray(mask)])
    image=Image.fromarray(rgba).resize((768,768),Image.Resampling.LANCZOS)
    image.save(folder/'lulu-eye-reference-right.png')
    path='M .045 .62 C .04 .35 .23 .08 .55 .06 C .82 .025 1.01 .25 .965 .55 C .93 .82 .69 .97 .39 .94 C .19 .92 .055 .82 .045 .62 Z'
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1" width="768" height="768">
<defs><clipPath id="eye"><path d="{path}"/></clipPath><linearGradient id="blue"><stop stop-color="#6d9fda"/><stop offset="1" stop-color="#305b95"/></linearGradient></defs>
<g clip-path="url(#eye)"><path d="{path}" fill="#fffdef"/><ellipse cx=".62" cy=".50" rx=".35" ry=".44" fill="url(#blue)"/><ellipse cx=".695" cy=".545" rx=".28" ry=".36" fill="#03070c"/><ellipse cx=".79" cy=".305" rx=".086" ry=".075" fill="#fffffd"/></g><path d="{path}" fill="none" stroke="#2f3634" stroke-width=".008"/>
</svg>'''
    (folder/'lulu-eye-reference-right.svg').write_text(svg)
    return image
