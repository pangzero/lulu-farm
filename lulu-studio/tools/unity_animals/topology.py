import bpy,bmesh,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];aid=sys.argv[sys.argv.index('--')+1];REV='game-r04';S=R/'assets-source/unity-animals'/REV/aid;V=R/'review/unity-integration-20261018/animals'/REV/aid;out={}
for label in ['source-import','lod0','lod1']:
 bpy.ops.wm.open_mainfile(filepath=str(S/(label+'.blend')));values=[]
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=max(max(o.dimensions)*1e-6,1e-7));values.append({'name':o.name,'vertices_after_seam_weld':len(bm.verts),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'zero_area_faces':sum(f.calc_area()<1e-12 for f in bm.faces)});bm.free()
 out[label]=values
(V/'topology.json').write_text(json.dumps({'models':out,'note':'Diagnostics after local UV-seam weld. Source itself can contain multiple touching parts; this is not a watertight-manifold claim.'},indent=2));print('TOPOLOGY',aid,out)
