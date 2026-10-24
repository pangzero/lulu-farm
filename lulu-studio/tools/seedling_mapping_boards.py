from pathlib import Path
import json
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];O=R/'review/seedling-meshy-mapping-20261018'
for row in json.loads((O/'mapping.json').read_text()):
 s=row['id'];vcurrent=row.get('current_version','meshy-toon-r01')
 for mode in ['material','clay']:
  paths=[O/s/v/f'{mode}-{w}.png' for v in ['original',vcurrent] for w in ['front','side','back','quarter','top']]
  if all(p.exists() for p in paths):
   b=Image.new('RGB',(1920,816),'white');d=ImageDraw.Draw(b)
   for i,p in enumerate(paths):x=i%5*384;y=i//5*408;d.text((x+8,y+6),s+'/'+p.parent.name+'/'+p.stem,fill='black');b.paste(Image.open(p).resize((384,384)),(x,y+24))
   b.save(O/s/f'{mode}-comparison.jpg')
paths=[O/r['id']/r.get('current_version','meshy-toon-r01')/'material-quarter.png' for r in json.loads((O/'mapping.json').read_text())]
if all(p.exists() for p in paths):
 b=Image.new('RGB',(2048,2048),'white');d=ImageDraw.Draw(b)
 for i,p in enumerate(paths):x=i%4*512;y=i//4*512;b.paste(Image.open(p).resize((488,488)),(x,y+24));d.text((x+8,y+5),p.parent.parent.name,fill='black')
 b.save(O/'all-14-quarters.jpg')
print('Updated available boards')
