import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'public/models/farm-assets/B05/meshy-r01/rose-mature.glb'));o=next(o for o in bpy.context.scene.objects if o.type=='MESH');world=o.matrix_world.copy();p=np.array([world@v.co for v in o.data.vertices])*.47;lo=p.min(0);hi=p.max(0);p-=np.array([(lo[0]+hi[0])/2,(lo[1]+hi[1])/2,lo[2]]);mat=o.data.materials[0];bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');im=bs.inputs['Base Color'].links[0].from_node.image;pix=np.empty(len(im.pixels),np.float32);im.pixels.foreach_get(pix);w,h=im.size;pix=pix.reshape(h,w,4);uv=o.data.uv_layers.active.data;pts=[]
# DIAGNOSTIC ONLY: color samples locate known flowers; production will use explicit spatial organ volumes.
for f in list(o.data.polygons)[::30]:
 q=sum((uv[j].uv for j in f.loop_indices),Vector((0,0)))/len(f.loop_indices);col=pix[min(h-1,int(q.y*h)),min(w-1,int(q.x*w))]
 if col[0]>col[1]*1.6 and col[2]>col[1]*1.3:pts.append(p[list(f.vertices)].mean(0))
x=np.array(pts);centers=np.array([[-.05,0,.78],[-.23,-.1,.5],[.23,0,.65]])
for _ in range(20):
 labels=np.linalg.norm(x[:,None]-centers[None],axis=2).argmin(1);centers=np.array([x[labels==k].mean(0) for k in range(3)])
rows=[]
for k,c in enumerate(centers):
 pts=x[labels==k];rows.append({'center':c.tolist(),'q02':np.quantile(pts,.02,axis=0).tolist(),'q98':np.quantile(pts,.98,axis=0).tolist(),'count':len(pts)})
print('ROSE_ORGAN_LOCATION_STUDY',json.dumps(rows),flush=True);(R/'review/unity-integration-20261018/assets/rose-organ-study.json').write_text(json.dumps(rows,indent=2))
