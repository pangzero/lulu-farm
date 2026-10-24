using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using Object = UnityEngine.Object;

namespace LuluFarm.Editor
{
    public static class FarmDecorScatter
    {
        const int Seed=240724;
        sealed class Segment {public Vector2 a,b;}
        [Serializable] public sealed class Instance {
            public string id,role;public Vector3 position;public float yaw,scale,roadClearance,footprintRadius;
            public int residentTriangles,peakLodTriangles,colliders;
        }
        [Serializable] sealed class Record {
            public string utc,status="authored_pending_route_and_Opus_review";
            public string rule="Seed 240724; road center distance >= .9 + .4 + prop radius; fields/pasture/pond/building/dock exclusions + .4 + radius; existing placements retained";
            public int seed=Seed,requested,rejected,instances,trees,smallProps,residentTriangles,peakLodTrianglesSum,uniqueMeshes,uniqueMeshTriangles;
            public string geometry="existing registered prefab mesh/material/LOD references; instance sums are not visible frame cost";
            public Instance[] placements;
        }
        public static void Build(Transform world,Transform landscape,Func<string,Vector3,Transform,float,float,GameObject> place)
        {
            var random=new System.Random(Seed);float Next(float a,float b)=>a+(float)random.NextDouble()*(b-a);
            var root=new GameObject("R07_DeterministicDecor").transform;root.SetParent(landscape,false);
            var road=landscape.GetComponentsInChildren<MeshFilter>(true).Single(f=>f.sharedMesh!=null&&f.sharedMesh.name=="RoadNetwork");
            var segments=new List<Segment>();var vertices=road.sharedMesh.vertices;
            for(int i=0;i<vertices.Length;i+=56){var a=road.transform.TransformPoint((vertices[i]+vertices[i+3])*.5f);var b=road.transform.TransformPoint((vertices[i+1]+vertices[i+2])*.5f);segments.Add(new Segment{a=new Vector2(a.x,a.z),b=new Vector2(b.x,b.z)});}
            var forbidden=new List<Rect>{Rect.MinMaxRect(-11.9f,-2.9f,-5.1f,6.3f),Rect.MinMaxRect(-3.6f,-6.5f,6,1.9f),Rect.MinMaxRect(7.4f,-2.7f,14.93f,6.03f)};
            foreach(string group in new[]{"HouseAndProduce","Pond"})
            {
                var parent=world.Find(group);if(parent==null)continue;
                foreach(Transform child in parent)
                if(group=="HouseAndProduce"||child.name.StartsWith("S04")||child.name.StartsWith("S07")||child.name.StartsWith("S08"))
                {var b=FarmProjectBuilder.BoundsOf(child.gameObject);forbidden.Add(Rect.MinMaxRect(b.min.x,b.min.z,b.max.x,b.max.z));}
            }
            var existingTrees=landscape.GetComponentsInChildren<LODGroup>(true).Where(g=>g.name=="E08"||g.name=="E09").Select(g=>new Vector2(g.transform.position.x,g.transform.position.z)).ToList();
            var placements=new List<Instance>();var occupied=new List<Vector3>();var meshes=new HashSet<Mesh>();int requested=0,rejected=0;
            var radii=new Dictionary<string,float>();
            float Radius(string id){
                if(radii.TryGetValue(id,out float value))return value;
                var prefab=AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Farm/Prefabs/"+id+".prefab");
                if(prefab==null)throw new InvalidOperationException("Missing registered scatter prefab "+id);
                var sample=(GameObject)PrefabUtility.InstantiatePrefab(prefab);
                try{var b=FarmProjectBuilder.BoundsOf(sample);float x=Mathf.Max(Mathf.Abs(b.min.x),Mathf.Abs(b.max.x));float z=Mathf.Max(Mathf.Abs(b.min.z),Mathf.Abs(b.max.z));value=Mathf.Sqrt(x*x+z*z);radii[id]=value;return value;}
                finally{Object.DestroyImmediate(sample);}
            }
            float RoadDistance(Vector2 p){float d=float.MaxValue;foreach(var s in segments){var v=s.b-s.a;float t=Mathf.Clamp01(Vector2.Dot(p-s.a,v)/v.sqrMagnitude);d=Mathf.Min(d,Vector2.Distance(p,s.a+v*t));}return d;}
            bool Add(string id,Vector2 p,string role,bool tree=false)
            {
                requested++;float scale=Next(.85f,1.15f),radius=Radius(id)*scale;
                if(RoadDistance(p)<1.3f+radius){rejected++;return false;}
                foreach(var zone in forbidden)if(new Rect(zone.xMin-.4f-radius,zone.yMin-.4f-radius,zone.width+.8f+radius*2,zone.height+.8f+radius*2).Contains(p)){rejected++;return false;}
                if(existingTrees.Any(v=>Vector2.Distance(v,p)<(tree?3.2f:1.0f))||occupied.Any(v=>Vector2.Distance(new Vector2(v.x,v.z),p)<v.y+radius+.15f)){rejected++;return false;}
                float yaw=Next(0,360);var instance=place(id,new Vector3(p.x,0,p.y),root,yaw,scale);
                if(instance==null)throw new InvalidOperationException("Missing registered scatter asset "+id);
                foreach(var c in instance.GetComponentsInChildren<Collider>(true))Object.DestroyImmediate(c);
                if(tree){var c=instance.AddComponent<CapsuleCollider>();c.center=new Vector3(0,.62f,0);c.height=1.24f;c.radius=.21f;FarmOcclusionSetup.Configure(instance,true);existingTrees.Add(p);}
                occupied.Add(new Vector3(p.x,radius,p.y));
                var renderers=instance.GetComponentsInChildren<MeshRenderer>(true);int resident=0;
                foreach(var r in renderers){var m=r.GetComponent<MeshFilter>()?.sharedMesh;if(m==null)continue;meshes.Add(m);resident+=Triangles(m);}
                var lod=instance.GetComponent<LODGroup>();int peak=lod==null?resident:lod.GetLODs().Max(l=>l.renderers.Where(r=>r!=null).Sum(r=>Triangles(r.GetComponent<MeshFilter>()?.sharedMesh)));
                placements.Add(new Instance{id=id,role=role,position=instance.transform.position,yaw=yaw,scale=scale,roadClearance=RoadDistance(p)-.9f-radius,footprintRadius=radius,residentTriangles=resident,peakLodTriangles=peak,colliders=instance.GetComponentsInChildren<Collider>(true).Length});return true;
            }
            // Nominal .4 per metre on each usable road side; hard exclusions can reduce final density.
            foreach(var s in segments){var delta=s.b-s.a;float length=delta.magnitude;var tangent=delta/length;var normal=new Vector2(-tangent.y,tangent.x);
                for(float t=Next(.3f,1.2f);t<length;t+=Next(2.2f,2.9f))foreach(int side in new[]{-1,1}){
                    string id=random.NextDouble()<.55?"E10":"E11";float offset=1.4f+Radius(id)*1.15f;
                    Add(id,s.a+tangent*t+normal*side*(offset+Next(-.10f,.18f)),"road_edge");
                }}
            // Fence perimeter proposals keep clear of fields/animal activity rather than filling the pen.
            foreach(var line in new[]{new Vector4(-4.6f,-6.5f,-4.6f,1.9f),new Vector4(-3.6f,-7.5f,6,-7.5f),new Vector4(-12.5f,-2.5f,-12.5f,5.9f),new Vector4(-11.5f,7,-5.5f,7)}){
                var a=new Vector2(line.x,line.y);var b=new Vector2(line.z,line.w);float length=Vector2.Distance(a,b);
                for(float t=.7f;t<length;t+=Next(2.3f,3))Add(random.NextDouble()<.5?"E10":"E11",Vector2.Lerp(a,b,t/length)+new Vector2(Next(-.15f,.15f),Next(-.15f,.15f)),"fence_outer");}
            // Outer ring at 3–5 m arc intervals, jittered independently of older trees.
            var corners=new[]{new Vector2(-18.5f,-13.2f),new Vector2(18.5f,-13.2f),new Vector2(18.5f,13.2f),new Vector2(-18.5f,13.2f)};
            for(int i=0;i<4;i++){var a=corners[i];var b=corners[(i+1)%4];float length=Vector2.Distance(a,b);
                for(float t=Next(.5f,1.5f);t<length;t+=Next(3.3f,4.8f))Add(random.NextDouble()<.28?"E09":"E08",Vector2.Lerp(a,b,t/length)+new Vector2(Next(-.35f,.35f),Next(-.35f,.35f)),"outer_tree",true);}
            for(int i=0;i<70;i++)Add(i%9==0?"E13":"E11",new Vector2(Next(-16,16),Next(-11,11)),"grass_scatter");
            foreach(var p in new[]{new Vector2(-2.8f,5.9f),new Vector2(2.8f,8.8f),new Vector2(-2.2f,9.4f),new Vector2(1.3f,9.6f),new Vector2(-2.6f,4.6f),new Vector2(3,4.3f)})
                Add("E11",p+new Vector2(Next(-.15f,.15f),Next(-.15f,.15f)),"house_flowers");
            var record=new Record{utc=DateTime.UtcNow.ToString("o"),requested=requested,rejected=rejected,instances=placements.Count,trees=placements.Count(p=>p.role=="outer_tree"),smallProps=placements.Count(p=>p.role!="outer_tree"),residentTriangles=placements.Sum(p=>p.residentTriangles),peakLodTrianglesSum=placements.Sum(p=>p.peakLodTriangles),uniqueMeshes=meshes.Count,uniqueMeshTriangles=meshes.Sum(Triangles),placements=placements.ToArray()};
            string dir="Evidence/r07/"+FarmProjectBuilder.R07Task;Directory.CreateDirectory(dir);File.WriteAllText(dir+"/decor-metrics.json",JsonUtility.ToJson(record,true));
        }
        static int Triangles(Mesh m){if(m==null)return 0;int count=0;for(int i=0;i<m.subMeshCount;i++)count+=(int)m.GetIndexCount(i)/3;return count;}
    }
}
