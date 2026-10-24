"""Continuous smooth-union garment field, evaluated in Blender's bundled NumPy."""
def build_garment(mesh,material,bpy,np):
 step=.010
 axes=[np.arange(-.68,.681,step),np.arange(-.62,.561,step),np.arange(.075,.686,step)]
 grid=np.stack(np.meshgrid(*axes,indexing='ij'),axis=-1)
 def ellipsoid(c,r):
  q=grid-np.array(c);r=np.array(r)
  k0=np.linalg.norm(q/r,axis=-1);k1=np.linalg.norm(q/(r*r),axis=-1)
  return k0*(k0-1)/np.maximum(k1,1e-7)
 def smooth_min(a,b,k):
  h=np.clip(.5+.5*(b-a)/k,0,1)
  return b*(1-h)+a*h-k*h*(1-h)
 field=ellipsoid((0,-.035,.500),(.568,.400,.270))
 for side in [-1,1]:
  field=smooth_min(field,ellipsoid((side*.29,-.075,.290),(.218,.235,.225)),.12)
 # Curved waist and slightly dished hems, with a small rounded cloth edge.
 top=grid[...,2]-(.578+.012*(grid[...,0]/.57)**2)
 bottom=.115+.025*((np.maximum(np.abs(grid[...,0]),.12)-.29)/.225)**2+.018*((grid[...,1]+.09)/.265)**2-grid[...,2]
 field=-smooth_min(-field,-top,.018)
 field=-smooth_min(-field,-bottom,.030)
 # Rounded U opening is part of the continuous field, with a soft intersection
 # instead of the former Boolean's planar interior ledge.
 q=np.stack([np.abs(grid[...,0])-(.1175-.042),np.abs(grid[...,2]-.025)-(.220-.042)],axis=-1)
 hole=np.linalg.norm(np.maximum(q,0),axis=-1)+np.minimum(np.max(q,axis=-1),0)-.042
 field=-smooth_min(-field,hole,.025)
 offsets=np.array([(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)])
 shape=np.array(field.shape)-1
 values=np.stack([field[o[0]:o[0]+shape[0],o[1]:o[1]+shape[1],o[2]:o[2]+shape[2]].ravel() for o in offsets],axis=1)
 active=(values.min(axis=1)<0)&(values.max(axis=1)>=0)
 base=np.stack(np.meshgrid(*(np.arange(n) for n in shape),indexing='ij'),axis=-1).reshape(-1,3)[active]
 values=values[active];positions=np.array([a[0] for a in axes])+(base[:,None,:]+offsets[None,:,:])*step
 tetra=[(0,5,1,6),(0,1,2,6),(0,2,3,6),(0,3,7,6),(0,7,4,6),(0,4,5,6)]
 edges=[(0,1),(1,2),(2,0),(0,3),(1,3),(2,3)]
 table=[[],[0,3,2],[0,1,4],[1,4,2,2,4,3],[1,2,5],[0,3,5,0,5,1],[0,2,5,0,5,4],[5,4,3],[3,4,5],[4,5,0,5,2,0],[1,5,0,5,3,0],[5,2,1],[3,4,2,2,4,1],[4,1,0],[2,3,0],[]]
 triangles=[]
 for tet in tetra:
  val=values[:,tet];pos=positions[:,tet,:];cases=((val<0)*np.array([1,2,4,8])).sum(axis=1)
  for case in range(1,15):
   mask=cases==case
   if not mask.any():continue
   v=val[mask];p=pos[mask];out=[]
   for edge in table[case]:
    a,b=edges[edge];t=v[:,a]/(v[:,a]-v[:,b]);out.append(p[:,a]+(p[:,b]-p[:,a])*t[:,None])
   triangles.append(np.stack(out,axis=1).reshape(-1,3))
 raw=np.concatenate(triangles);vertices,index=np.unique(np.round(raw,6),axis=0,return_inverse=True)
 faces=index.reshape(-1,3)
 faces=faces[(faces[:,0]!=faces[:,1])&(faces[:,1]!=faces[:,2])&(faces[:,0]!=faces[:,2])]
 obj=mesh('Shorts_Tailored',vertices.tolist(),faces.tolist(),material)
 bpy.context.view_layer.objects.active=obj;obj.select_set(True)
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT')
 return obj
