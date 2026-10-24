import json,sys
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];O=R/'review/unity-integration-20261018/assets';d=json.loads((R/'public/models/unity-integration/manifest.json').read_text());keys=sys.argv[1:]
for n in range(0,len(keys),3):
 c=Image.new('RGB',(1280,1200),'white');dr=ImageDraw.Draw(c)
 for i,k in enumerate(keys[n:n+3]):
  r=next(x for x in d['assets'] if x['id']==k);o=O/k/r['selected_version']
  for j,f in enumerate(['planting-3x3-lulu.png','farm-distance.png']):
   im=Image.open(o/f);im.thumbnail((640,370));c.paste(im,(j*640,i*400+25));dr.text((j*640+8,i*400+5),k+' '+f,fill='black')
 c.save(O/f'mature-planting-board-{n//3+1}.jpg')
