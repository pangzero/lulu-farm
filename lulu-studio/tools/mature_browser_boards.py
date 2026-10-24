from pathlib import Path
from PIL import Image,ImageDraw
import sys
R=Path(__file__).resolve().parents[1]/'review/crop-mature-remaining-20261018/browser'
for slug in sys.argv[1:]:
 versions=['original','toon-r03','game-r02'] if slug=='rose' else ['original','toon-r01','game-r01']
 names=[slug+'-'+v+'-quarter' for v in versions]+[slug+'-game-'+v for v in ['front','side','back','top','clay-back','grid','farm']]
 b=Image.new('RGB',(1536,1248),'white');d=ImageDraw.Draw(b)
 for k,name in enumerate(names):
  p=R/(name+'.png')
  if not p.exists():continue
  im=Image.open(p);im=im.crop((20,285,1260,984)).resize((512,288));x=k%3*512;y=k//3*312;b.paste(im,(x,y+24));d.text((x+8,y+7),name,fill='black')
 b.save(R/(slug+'-web-review.jpg'))
