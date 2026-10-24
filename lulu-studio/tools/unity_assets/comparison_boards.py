from pathlib import Path
from PIL import Image,ImageDraw
import sys
R=Path(__file__).resolve().parents[2];O=R/'review/unity-integration-20261018/assets';items=sys.argv[1:]
for j in range(0,len(items),3):
 c=Image.new('RGB',(1024,1584),'white');d=ImageDraw.Draw(c)
 for n,item in enumerate(items[j:j+3]):
  p=O/item
  for i,f in enumerate(['original-material-quarter.png','material-quarter.png']):
   im=Image.open(p/f).resize((512,512));c.paste(im,(i*512,n*528+16));d.text((i*512+8,n*528+2),item+(' ORIGINAL' if i==0 else ' CANDIDATE'),fill='black')
 c.save(O/f'facility-comparison-{j//3+1}.jpg')
