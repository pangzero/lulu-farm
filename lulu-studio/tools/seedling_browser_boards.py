from pathlib import Path
import json
from PIL import Image,ImageDraw
O=Path(__file__).resolve().parents[1]/'review/seedling-meshy-mapping-20261018';checks=json.loads((O/'browser/current-checks.json').read_text())
for row in json.loads((O/'mapping.json').read_text()):
 s=row['id'];rs=[r for r in checks if r['canvas'].get('crop')==s];b=Image.new('RGB',(1536,936),'white');d=ImageDraw.Draw(b)
 for i,r in enumerate(rs):
  x=i%3*512;y=i//3*312;im=Image.open(O/'browser'/r['screenshot']);im=im.crop((20,260,1260,960)).resize((512,288));b.paste(im,(x,y+24));d.text((x+7,y+6),r['screenshot'],fill='black')
 b.save(O/'browser'/f'{s}-board.jpg')
print('14 browser boards')
