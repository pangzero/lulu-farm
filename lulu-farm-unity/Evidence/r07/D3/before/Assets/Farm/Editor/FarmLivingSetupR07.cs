using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using Object = UnityEngine.Object;

namespace LuluFarm.Editor
{
    public static class FarmLivingSetupR07
    {
        const string Folder="Assets/Farm/GeneratedR07/Ambient";
        [Serializable] sealed class MaterialRecord {public string asset,source,derived;public float mode,phase;}
        [Serializable] sealed class Record {public string utc,method="Independent scene material derivatives and vertex-only motion; original meshes, imported materials and all Lulu objects unchanged";public int vegetationInstances,animals,butterflies=4,ripples=3;public MaterialRecord[] materials;public string sound="Procedurally synthesized original WAVs; no third-party recording. See audio-source.json";}
        public static void Build(Transform world,FarmRuntimeBootstrap runtime)
        {
            Directory.CreateDirectory(Folder);AssetDatabase.Refresh();
            var shader=Shader.Find("LuluFarm/LivingSurface-r07");if(shader==null)throw new InvalidOperationException("LivingSurface-r07 shader missing");
            var records=new List<MaterialRecord>();var cache=new Dictionary<string,Material>();int vegetation=0,animals=0;
            string[] plantIds={"E08","E09","E10","E11","E12"},animalIds={"cow","sheep","chicken","pig","duck"};
            foreach(var lod in world.GetComponentsInChildren<LODGroup>(true))
            {
                string id=lod.name;bool plant=plantIds.Contains(id),animal=animalIds.Contains(id);if(!plant&&!animal)continue;
                if(plant)vegetation++;else animals++;
                var occluder=lod.GetComponent<FarmCameraOccluder>();
                foreach(var r in lod.GetComponentsInChildren<MeshRenderer>(true))
                {
                    var old=r.sharedMaterials;var current=new Material[old.Length];
                    for(int i=0;i<old.Length;i++){
                        var source=old[i];AssetDatabase.TryGetGUIDAndLocalFileIdentifier(source,out string guid,out long localId);
                        string key=id+"-"+guid+"-"+localId;
                        if(!cache.TryGetValue(key,out var material)){
                            string path=Folder+"/"+key+".mat";material=AssetDatabase.LoadAssetAtPath<Material>(path);
                            if(material==null){material=new Material(shader);AssetDatabase.CreateAsset(material,path);}else material.shader=shader;
                            string cp=new[]{"_BaseColorFactor","baseColorFactor","_BaseColor","baseColor","_Color"}.FirstOrDefault(source.HasProperty);
                            string tp=new[]{"_BaseColorTexture","baseColorTexture","_BaseMap","_MainTex"}.FirstOrDefault(p=>source.HasProperty(p)&&source.GetTexture(p)!=null);
                            // Cow head-interior closure is an intentional untextured colour material.
                            material.SetColor("_BaseColor",cp==null?Color.white:source.GetColor(cp));material.SetTexture("_BaseMap",tp==null?Texture2D.whiteTexture:source.GetTexture(tp));material.SetTextureScale("_BaseMap",tp==null?Vector2.one:source.GetTextureScale(tp));material.SetTextureOffset("_BaseMap",tp==null?Vector2.zero:source.GetTextureOffset(tp));
                            string np=new[]{"normalTexture","_NormalTexture","_BumpMap"}.FirstOrDefault(p=>source.HasProperty(p)&&source.GetTexture(p)!=null);
                            material.SetTexture("_NormalMap",np==null?null:source.GetTexture(np));material.SetFloat("_NormalScale",np==null?0:.25f);
                            string rough=new[]{"roughnessFactor","_RoughnessFactor"}.FirstOrDefault(source.HasProperty);
                            material.SetFloat("_Smoothness",rough==null?(plant?.16f:.1f):1-source.GetFloat(rough));material.SetFloat("_SpecularFactor",source.HasProperty("specularFactor")?source.GetFloat("specularFactor"):plant?.48f:.4f);
                            material.SetFloat("_MotionMode",plant?1:2);bool tree=id=="E08"||id=="E09";
                            material.SetFloat("_WindStart",tree?1.15f:.07f);material.SetFloat("_WindTop",tree?3.2f:id=="E12"?1.2f:.7f);material.SetFloat("_Amplitude",tree?.025f:id=="E11"?.007f:.012f);
                            var mesh=r.GetComponent<MeshFilter>().sharedMesh;material.SetFloat("_FloorY",mesh.bounds.min.y);
                            float phase=(float)new System.Random(240724+Mathf.Max(0,Array.IndexOf(animalIds,id))*127).NextDouble()*Mathf.PI*2;material.SetFloat("_Phase",phase);
                            material.SetVector("_HeadPivot",new Vector4(0,.05f,.25f,0));material.SetVector("_HeadLimits",new Vector4(.05f,.5f,-.15f,.15f));
                            material.enableInstancing=true;EditorUtility.SetDirty(material);cache.Add(key,material);
                            records.Add(new MaterialRecord{asset=id,source=AssetDatabase.GetAssetPath(source),derived=path,mode=plant?1:2,phase=phase});
                        }current[i]=material;
                    }
                    r.sharedMaterials=current;
                    // Keep Opus-owned transparency behavior; only restore to the new opaque scene derivative.
                    if(occluder!=null)foreach(var binding in occluder.bindings)if(binding.renderer==r)binding.opaqueMaterials=current;
                }
            }
            var root=new GameObject("R07_AmbientMotion").transform;root.SetParent(world,false);
            var ambient=root.gameObject.AddComponent<FarmAmbientR07>();ambient.runtime=runtime;
            var wing=Wing();var butterflyList=new List<Transform>();
            Vector3[] anchors={new Vector3(-2.8f,.75f,5),new Vector3(-12.8f,.6f,3.6f),new Vector3(5.2f,.7f,8.1f),new Vector3(14.7f,.65f,5.4f)};
            for(int i=0;i<4;i++){
                var butterfly=new GameObject("Butterfly_"+i).transform;butterfly.SetParent(root,false);butterfly.localPosition=anchors[i];
                var mat=Unlit("Butterfly_"+i,Color.HSVToRGB(.09f+i*.16f,.45f,.95f),false);
                foreach(int side in new[]{-1,1}){var go=new GameObject("Wing_"+side,typeof(MeshFilter),typeof(MeshRenderer));go.transform.SetParent(butterfly,false);go.transform.localPosition=new Vector3(side*.035f,0,0);go.GetComponent<MeshFilter>().sharedMesh=wing;go.GetComponent<MeshRenderer>().sharedMaterial=mat;go.GetComponent<MeshRenderer>().shadowCastingMode=ShadowCastingMode.Off;}
                butterflyList.Add(butterfly);
            }ambient.butterflies=butterflyList.ToArray();
            var ring=Ring();var ringMaterial=Unlit("SoftWaterRing",new Color(.76f,.95f,1,.1f),true);var rippleList=new List<Renderer>();
            foreach(var p in new[]{new Vector3(11.7f,-.098f,1.4f),new Vector3(13.8f,-.098f,4.1f),new Vector3(9.6f,-.098f,-1.7f)}){
                var go=new GameObject("OccasionalRipple",typeof(MeshFilter),typeof(MeshRenderer));go.transform.SetParent(root,false);go.transform.localPosition=p;go.GetComponent<MeshFilter>().sharedMesh=ring;
                var renderer=go.GetComponent<MeshRenderer>();renderer.sharedMaterial=ringMaterial;renderer.shadowCastingMode=ShadowCastingMode.Off;renderer.enabled=false;rippleList.Add(renderer);
            }ambient.ripples=rippleList.ToArray();
            ambient.birds=Sound(root,"Birds",new Vector3(0,2,2),"bird-chirps.wav",.045f,false);
            ambient.water=Sound(root,"PondWater",new Vector3(11,0,1.6f),"soft-water.wav",.12f,true);
            Shader.SetGlobalFloat("_FarmR07WindEnabled",0);Shader.SetGlobalFloat("_FarmR07MotionEnabled",0);Shader.SetGlobalFloat("_FarmR07Time",0);
            string output="Evidence/r07/D6";Directory.CreateDirectory(output);File.WriteAllText(output+"/ambient-metrics.json",JsonUtility.ToJson(new Record{utc=DateTime.UtcNow.ToString("o"),vegetationInstances=vegetation,animals=animals,materials=records.ToArray()},true));
        }
        static AudioSource Sound(Transform parent,string name,Vector3 pos,string file,float volume,bool spatial){
            var go=new GameObject(name,typeof(AudioSource));go.transform.SetParent(parent,false);go.transform.localPosition=pos;var a=go.GetComponent<AudioSource>();
            a.clip=AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/Farm/Audio/R07/"+file);if(a.clip==null)throw new InvalidOperationException("Missing original synthesized audio "+file);
            a.loop=true;a.playOnAwake=false;a.volume=volume;a.spatialBlend=spatial?1:0;a.minDistance=2;a.maxDistance=16;return a;
        }
        static Material Unlit(string name,Color color,bool transparent){string file=Folder+"/"+name+".mat";var m=AssetDatabase.LoadAssetAtPath<Material>(file);if(m==null){m=new Material(Shader.Find("Universal Render Pipeline/Unlit"));AssetDatabase.CreateAsset(m,file);}m.SetColor("_BaseColor",color);m.SetFloat("_Cull",0);
            if(transparent){m.SetFloat("_Surface",1);m.SetFloat("_Blend",0);m.SetFloat("_SrcBlend",(float)BlendMode.SrcAlpha);m.SetFloat("_DstBlend",(float)BlendMode.OneMinusSrcAlpha);m.SetFloat("_ZWrite",0);m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");m.renderQueue=3001;}EditorUtility.SetDirty(m);return m;}
        static Mesh SaveMesh(string name,List<Vector3> v,List<int> t){string file=Folder+"/"+name+".asset";var m=AssetDatabase.LoadAssetAtPath<Mesh>(file);if(m==null){m=new Mesh();AssetDatabase.CreateAsset(m,file);}m.Clear();m.SetVertices(v);m.SetTriangles(t,0);m.RecalculateNormals();m.RecalculateBounds();EditorUtility.SetDirty(m);return m;}
        static Mesh Wing(){var v=new List<Vector3>{Vector3.zero};var t=new List<int>();for(int i=0;i<=16;i++){float a=i*Mathf.PI*2/16;v.Add(new Vector3(Mathf.Cos(a)*.035f,Mathf.Sin(a)*.055f,0));if(i<16)t.AddRange(new[]{0,i+1,i+2});}return SaveMesh("ButterflyWing",v,t);}
        static Mesh Ring(){var v=new List<Vector3>();var t=new List<int>();for(int i=0;i<=48;i++){float a=i*Mathf.PI*2/48;foreach(float r in new[]{.94f,1f})v.Add(new Vector3(Mathf.Cos(a)*r,0,Mathf.Sin(a)*r));if(i<48){int k=i*2;t.AddRange(new[]{k,k+2,k+1,k+1,k+2,k+3});}}return SaveMesh("WaterRippleRing",v,t);}
    }
}
