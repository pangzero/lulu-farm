from PIL import Image,ImageDraw
from pathlib import Path
R=Path('/Users/haowen/GameProject/farm-game/lulu-studio/review/unity-integration-20261018/lulu');dst=R/'locomotion-r04'
views=['front','side','back','quarter','top']
for mode in ['color','clay']:
 sheet=Image.new('RGB',(1200,2100),'#f4f3eb');d=ImageDraw.Draw(sheet)
 for col,(rev,label) in enumerate([('locomotion-r02','locomotion-master'),('locomotion-r04','game-lod0'),('locomotion-r04','game-lod1')]):
  for row,v in enumerate(views):
   p=R/rev/label/f'Rest-001-{v}-{mode}.png'
   if not p.exists():continue
   im=Image.open(p).convert('RGB').resize((400,400));sheet.paste(im,(col*400,row*420+20));d.text((col*400+8,row*420+5),f'{label} / {v}',fill='#252c28')
 sheet.save(dst/f'five-view-{mode}-comparison.jpg',quality=92)
# Frame contact preserves same time phase in each column.
for clip,n in [('Walk',18),('Run',12)]:
 sheet=Image.new('RGB',(1200,1680),'#f4f3eb');d=ImageDraw.Draw(sheet)
 for col,(rev,label) in enumerate([('locomotion-r02','locomotion-master'),('locomotion-r04','game-lod0'),('locomotion-r04','game-lod1')]):
  for row,f in enumerate([1,1+n//4,1+n//2,1+n*3//4]):
   p=R/rev/label/f'{clip}-{f:03d}-quarter-color.png'
   if not p.exists():continue
   im=Image.open(p).convert('RGB').resize((400,400));sheet.paste(im,(col*400,row*420+20));d.text((col*400+8,row*420+5),f'{label} / {clip} frame{f}',fill='#252c28')
 sheet.save(dst/f'{clip.lower()}-phase-comparison.jpg',quality=92)
