from PIL import Image,ImageDraw
from pathlib import Path
R=Path('/Users/haowen/GameProject/farm-game/lulu-studio/review/unity-integration-20261018/animals/game-r04');views=['front','side','back','quarter','top']
for p in R.iterdir():
 if not p.is_dir() or not (p/'lod1'/'top-clay.png').exists():continue
 out=Image.new('RGB',(1280,1680),'#eee');d=ImageDraw.Draw(out)
 for row,(v,mat) in enumerate([(v,m) for v in ['source','lod0','lod1'] for m in ['color','clay']]):
  for col,view in enumerate(views):
   im=Image.open(p/v/(view+'-'+mat+'.png')).convert('RGB').resize((256,256));out.paste(im,(col*256,row*280+24));d.text((col*256+5,row*280+5),p.name+' '+v+' '+mat+' '+view,fill='black')
 out.save(p/'source-lod-comparison.jpg',quality=94)
