from pathlib import Path
import sys
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];O=R/'review/crop-mature-remaining-20261018'
for slug in sys.argv[1:]:
 versions=['original','toon-r03','game-r02'] if slug=='rose' else ['original','toon-r01','game-r01']
 for mode in ['material','clay']:
  paths=[O/slug/v/f'{mode}-{view}.png' for v in versions for view in ['front','side','back','quarter','top']]
  if not all(p.exists() for p in paths):continue
  b=Image.new('RGB',(1920,1224),'white');d=ImageDraw.Draw(b)
  for k,p in enumerate(paths):
   x=k%5*384;y=k//5*408;d.text((x+8,y+6),f'{slug} / {p.parent.name} / {p.stem}',fill='black');b.paste(Image.open(p).resize((384,384)),(x,y+24))
  b.save(O/slug/f'{mode}-comparison-board.jpg')
 # 768-pixel detail, version pair.
 for mode in ['material','clay']:
  paths=[O/slug/v/f'{mode}-detail.png' for v in versions]
  if all(p.exists() for p in paths):
   b=Image.new('RGB',(2304,800),'white');d=ImageDraw.Draw(b)
   for i,p in enumerate(paths):b.paste(Image.open(p),(i*768,32));d.text((i*768+10,10),slug+' / '+p.parent.name,fill='black')
   b.save(O/slug/f'{mode}-detail-comparison.jpg')
 for view in ['planting-3x3-lulu','farm-distance']:
  paths=[O/slug/v/(view+'.png') for v in versions[1:]]
  if all(p.exists() for p in paths):
   size=Image.open(paths[0]).size;b=Image.new('RGB',(size[0]*2,size[1]+24),'white');d=ImageDraw.Draw(b)
   for i,p in enumerate(paths):b.paste(Image.open(p),(size[0]*i,24));d.text((size[0]*i+10,7),slug+' / '+p.parent.name,fill='black')
   b.save(O/slug/(view+'-comparison.jpg'))
print('Ready boards updated')
