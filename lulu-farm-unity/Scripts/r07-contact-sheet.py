#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
import argparse,pathlib
p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('output');a=p.parse_args()
source=pathlib.Path(a.directory);out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=True)
files=sorted(source.glob('*.png'));font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',20)
for i in range(0,len(files),4):
 sheet=Image.new('RGB',(1600,960),(30,36,31));draw=ImageDraw.Draw(sheet)
 for j,f in enumerate(files[i:i+4]):
  x=(j%2)*800;y=(j//2)*480
  im=Image.open(f).convert('RGB');im.thumbnail((800,450));sheet.paste(im,(x,y+30));draw.text((x+10,y+5),f.name,fill='white',font=font)
 sheet.save(out/f'{i//4+1:02}.jpg',quality=93)
print(len(files),'source screenshots in',(len(files)+3)//4,'sheets')
