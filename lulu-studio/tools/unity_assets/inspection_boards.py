from pathlib import Path
from PIL import Image,ImageDraw
import sys
R=Path(__file__).resolve().parents[2]
for item in sys.argv[1:]:
 p=R/'review/unity-integration-20261018/assets'/item;c=Image.new('RGB',(1920,808),'white');d=ImageDraw.Draw(c)
 for j,mode in enumerate(['material','clay']):
  for i,v in enumerate(['front','side','back','quarter','top']):
   f=p/f'{mode}-{v}.png'
   if not f.exists():continue
   im=Image.open(f).resize((384,384));c.paste(im,(i*384,j*404+20));d.text((i*384+10,j*404+3),mode+' '+v,fill='black')
 c.save(p/'inspection-board.jpg')
