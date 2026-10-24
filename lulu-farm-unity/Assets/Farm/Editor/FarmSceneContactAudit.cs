using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.SceneManagement;
using Object = UnityEngine.Object;

namespace LuluFarm.Editor
{
    // Tests assembled collision and source geometry together. This never substitutes for playing the route.
    public static class FarmSceneContactAudit
    {
        [Serializable] sealed class Probe
        {
            public string id,status,expected,actual;
            public Vector3 position;
            public float collisionY,visualY,separation;
        }
        [Serializable] sealed class Report
        {
            public string utc,scene,editor,status;
            public string visual="not_viewed",manualRoute="not_executed_by_this_check",device="not_tested";
            public Probe[] probes;
        }
        [MenuItem("Farm/08 Audit assembled contact and collision")]
        public static void Run()
        {
            var scene=SceneManager.GetActiveScene();
            var roots=scene.GetRootGameObjects();
            var transforms=roots.SelectMany(root=>root.GetComponentsInChildren<Transform>(true)).ToArray();
            var rt=roots.SelectMany(root=>root.GetComponentsInChildren<FarmRuntimeBootstrap>(true)).FirstOrDefault();
            if(rt==null||!scene.name.Contains("FarmWorld"))throw new InvalidOperationException("Open the assembled FarmWorld scene before this check.");
            Physics.SyncTransforms();var probes=new List<Probe>();
            var plots=roots.SelectMany(root=>root.GetComponentsInChildren<FarmCropStage>(true)).ToArray();
            if(plots.Length==0)probes.Add(MissingProbe("crop_plots_required","FarmWorld crop plots with both stages"));
            foreach(var plot in plots)
            {
                Vector3 pos=plot.transform.position;
                probes.Add(GroundProbe(plot.name+"_soil",pos,"SoilWalkSurface"));
                if(plot.seedling==null||plot.mature==null)probes.Add(MissingProbe(plot.name+"_stages_required","Both seedling and mature root objects"));
                foreach(var plant in new[]{plot.seedling,plot.mature})if(plant!=null)
                {
                    var bounds=FarmProjectBuilder.BoundsOf(plant);
                    float separation=bounds.min.y-pos.y;
                    probes.Add(new Probe{id=plot.name+"_"+plant.name+"_root",position=pos,expected="Root at the soil datum within 0.01 units",actual=separation.ToString("F5"),separation=separation,status=Mathf.Abs(separation)<.01f?"pass":"fail"});
                }
            }
            foreach(var pos in new[]{new Vector3(-12,0,0),new Vector3(-5,0,3),new Vector3(0,0,-8.3f)})
                probes.Add(GroundProbe("continuous_ground_"+pos,pos,"ContinuousGroundWithSoilAndPondOpenings"));
            var water=transforms.FirstOrDefault(t=>t.name=="PondWater_Continuous");
            if(water!=null&&water.GetComponent<Renderer>()!=null)
            {
                var center=water.GetComponent<Renderer>().bounds.center;
                bool hit=Physics.Raycast(new Vector3(center.x,4,center.z),Vector3.down,out var result,10,~(1<<28),QueryTriggerInteraction.Ignore);
                probes.Add(new Probe{id="pond_not_walkable",position=center,expected="No ground collider below pond centre",actual=hit?result.collider.name:"no collider",status=hit?"fail":"pass"});
            }
            else probes.Add(MissingProbe("pond_water_required","PondWater_Continuous with Renderer in FarmWorld"));
            var gate=rt.routeMarkers?.FirstOrDefault(m=>m!=null&&m.name=="牧场入口");
            var gateAsset=FindAssetInstance("S06",transforms);
            var controller=rt.playerRoot!=null?rt.playerRoot.GetComponent<CharacterController>():null;
            if(gate==null)probes.Add(MissingProbe("gate_route_marker_required","牧场入口 route marker"));
            if(gateAsset==null)probes.Add(MissingProbe("gate_asset_required","S06 gate instance in FarmWorld"));
            if(controller==null)probes.Add(MissingProbe("player_capsule_required","Authored player CharacterController"));
            if(gate!=null&&gateAsset!=null&&controller!=null)
            {
                var pos=new Vector3(gate.position.x,0,-6.5f);
                float half=Mathf.Max(0,controller.height*.5f-controller.radius);
                Vector3 center=pos+controller.center;
                var colliders=Physics.OverlapCapsule(center-Vector3.up*half,center+Vector3.up*half,controller.radius,~(1<<28),QueryTriggerInteraction.Ignore);
                colliders=colliders.Where(c=>c.transform!=rt.playerRoot.transform&&!c.transform.IsChildOf(rt.playerRoot.transform)&&c.name!="ContinuousGroundWithSoilAndPondOpenings").ToArray();
                probes.Add(new Probe{id="gate_capsule_clearance",position=pos,expected="Clear actual player capsule, diameter "+(controller.radius*2).ToString("F3")+" height "+controller.height.ToString("F3"),actual=string.Join(",",colliders.Select(c=>c.name)),status=colliders.Length==0?"pass":"fail"});
            }
            var dock=FindAssetInstance("S07",transforms);
            var dockMarker=rt.routeMarkers?.FirstOrDefault(m=>m!=null&&m.name=="码头");
            if(dock==null)probes.Add(MissingProbe("dock_asset_required","S07 dock instance in FarmWorld"));
            if(dockMarker==null)probes.Add(MissingProbe("dock_route_marker_required","码头 route marker"));
            if(dock!=null&&dockMarker!=null)
            {
                Vector3 center=dockMarker.position;
                foreach(float x in new[]{7.5f,8.1f,8.6f,9.2f})
                {
                    var pos=new Vector3(x,center.y,center.z);
                    Ray ray=new Ray(pos+Vector3.up*4,Vector3.down);
                    bool hasCollision=Physics.Raycast(ray,out var hit,10,~(1<<28),QueryTriggerInteraction.Ignore);
                    float surface=MeshSurfaceY(dock,ray);
                    float difference=hasCollision&&!float.IsNaN(surface)?hit.point.y-surface:999;
                    probes.Add(new Probe{id="dock_deck_"+x,position=pos,expected="Collision follows visible deck within 0.04 units",actual=hasCollision?hit.collider.name:"missing",collisionY=hasCollision?hit.point.y:0,visualY=float.IsNaN(surface)?-999:surface,separation=difference,status=Mathf.Abs(difference)<=.04f?"pass":"fail"});
                }
            }
            var report=new Report{utc=DateTime.UtcNow.ToString("o"),scene=scene.path,editor=Application.unityVersion,probes=probes.ToArray(),status=probes.Count>0&&probes.All(p=>p.status=="pass")?"technical_probes_pass_manual_visual_pending":"technical_probe_failures"};
            Directory.CreateDirectory("Evidence");File.WriteAllText("Evidence/scene-contact-audit.json",JsonUtility.ToJson(report,true));
            Debug.Log("Scene contact audit: "+report.status);
        }
        static Probe MissingProbe(string id,string expected)=>new Probe{id=id,expected=expected,actual="missing",status="fail"};
        static GameObject FindAssetInstance(string id,Transform[] transforms)=>transforms.FirstOrDefault(t=>t.name==id||t.name.StartsWith(id+" — ",StringComparison.Ordinal))?.gameObject;
        static Probe GroundProbe(string id,Vector3 position,string expected)
        {
            bool hit=Physics.Raycast(position+Vector3.up*3,Vector3.down,out var result,6,~(1<<28),QueryTriggerInteraction.Ignore);
            return new Probe{id=id,position=position,expected=expected,actual=hit?result.collider.name:"missing",collisionY=hit?result.point.y:0,status=hit&&result.collider.name==expected?"pass":"fail"};
        }
        static float MeshSurfaceY(GameObject root,Ray ray)
        {
            float y=float.NegativeInfinity;
            foreach(var filter in root.GetComponentsInChildren<MeshFilter>(true))
            {
                if(filter.sharedMesh==null)continue;
                var probe=new GameObject("TemporaryContactProbe"){hideFlags=HideFlags.HideAndDontSave};
                try
                {
                    probe.transform.SetPositionAndRotation(filter.transform.position,filter.transform.rotation);probe.transform.localScale=filter.transform.lossyScale;
                    var collider=probe.AddComponent<MeshCollider>();collider.sharedMesh=filter.sharedMesh;
                    if(collider.Raycast(ray,out var hit,10))y=Mathf.Max(y,hit.point.y);
                }
                finally{Object.DestroyImmediate(probe);}
            }
            return float.IsNegativeInfinity(y)?float.NaN:y;
        }
    }
}
