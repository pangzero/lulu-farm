import bpy,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[2];bpy.ops.wm.open_mainfile(filepath=str(R/'assets-source/unity-animals/game-r02/cow/source-import.blend'));im=bpy.data.images['Image_3'];p=np.empty(len(im.pixels),np.float32);im.pixels.foreach_get(p);p=p.reshape(-1,4);v,c=np.unique(np.round(p[:,:3].mean(1),6),return_counts=True);ix=np.argsort(c)[-30:];print(list(zip(v[ix],c[ix])));(R/'review/unity-integration-20261018/animals/cow-source-texture.png').write_bytes(im.packed_file.data)
