using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEditor.Build.Reporting;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;
using Object = UnityEngine.Object;

namespace LuluFarm.Editor
{
    [Serializable] public sealed class AssetRecord
    {
        public string id, name, type, species, stage, path, beforePath, source, sourceSHA256, importSHA256, sourceKind, version, technical, visual, userArt, device;
        public float worldHeight,adapterScale,sourceSpaceScale=1;public Vector3 adapterOffset,sourceSpaceOffset; public string[] lodPaths;
        public bool temporaryMotionAuthorized;
    }
    [Serializable] public sealed class AssetRegistry { public int schema; public AssetRecord[] assets; }
    [Serializable] public sealed class ImportFinding { public string id,path; public int triangles,renderers,materials;public Vector3 center,size;public string[] warnings; }
    [Serializable] public sealed class ImportReport { public string utc, editor;public ImportFinding[] findings;public string status; }
    [Serializable] public sealed class AcceptancePair { public string id,beforePrefab,afterPrefab; }
    [Serializable] public sealed class AcceptancePairs { public AcceptancePair[] pairs; }
    [Serializable] public sealed class IntegrationStamp { public string registrySHA256,utc,status;public string[] issues; }

    public static partial class FarmProjectBuilder
    {
        const string Base = "Assets/Farm/";
        static AssetRegistry registry;
        static readonly Dictionary<string,GameObject> prefabs = new Dictionary<string,GameObject>();
        static readonly List<string> issues = new List<string>();
        static Material grass, path, water, clay;
        static Transform world;
        static readonly float BankRadius=1.2f/(Mathf.PI*.5f);
        const float PondMinX=7.4f,PondMinZ=-2.7f;
        static float PondMaxX=>PondMinX+6f+2f*BankRadius;
        static float PondMaxZ=>PondMinZ+7.2f+2f*BankRadius;
        static float DockZ=>PondMinZ+BankRadius+2.4f;
        static Vector2 PondCenter=>new Vector2((PondMinX+PondMaxX)*.5f,(PondMinZ+PondMaxZ)*.5f);
        static bool CanIntegrate(AssetRecord a)
        {
            if(a.id=="Lulu"&&a.temporaryMotionAuthorized)return true;
            string status=(a.visual??"").ToLowerInvariant();
            return !new[]{"failed","failure","rejected","do_not_promote","revision_required","needs_rework","not_passed","blocked"}.Any(status.Contains);
        }

        // glTFast chooses and caches its material generator on first use. A project's
        // first refresh can run before URP is configured, so those imported materials
        // must be refreshed in a subsequent editor session with URP already active.
        [MenuItem("Farm/01a Refresh imported materials for active URP")]
        public static void RefreshMaterialsAndImport()
        {
            if (!(GraphicsSettings.defaultRenderPipeline is UniversalRenderPipelineAsset))
                throw new InvalidOperationException("Configure URP first, then reopen the Editor before refreshing glTF materials.");
            var entries = JsonUtility.FromJson<AssetRegistry>(File.ReadAllText(Base + "Data/asset-registry.json")).assets;
            var paths = entries.SelectMany(a => new[] { a.path, a.beforePath }.Concat(a.lodPaths ?? Array.Empty<string>()))
                .Where(p => !string.IsNullOrEmpty(p)).Distinct().ToArray();
            int inspected = 0;
            foreach (string assetPath in paths)
            {
                var materials = AssetDatabase.LoadAllAssetsAtPath(assetPath).OfType<Material>().ToArray();
                if (materials.Length == 0 || materials.Any(m => m.shader == null || !m.shader.isSupported || m.GetTag("RenderPipeline", true, "") != "UniversalPipeline"))
                {
                    AssetDatabase.ImportAsset(assetPath, ImportAssetOptions.ForceUpdate | ImportAssetOptions.ForceSynchronousImport);
                }
                if (++inspected % 4 == 0) EditorUtility.UnloadUnusedAssetsImmediate();
            }
            ConfigureAndImport();
        }

        [MenuItem("Farm/01 Configure and import")]
        public static void ConfigureAndImport()
        {
            foreach(var d in new[]{"Materials","Prefabs","Scenes","Settings","Data"}) Directory.CreateDirectory(Base+d);
            Directory.CreateDirectory("Evidence");
            PlayerSettings.companyName="Lulu Studio";PlayerSettings.productName="噜噜农场";
            PlayerSettings.bundleVersion="0.1.0"; PlayerSettings.colorSpace=ColorSpace.Linear;
            PlayerSettings.defaultScreenWidth=1280; PlayerSettings.defaultScreenHeight=720;
            PlayerSettings.fullScreenMode=FullScreenMode.Windowed;PlayerSettings.runInBackground=true;
            PlayerSettings.SetApplicationIdentifier(UnityEditor.Build.NamedBuildTarget.Android,"com.lulustudio.farm");
            PlayerSettings.SetApplicationIdentifier(UnityEditor.Build.NamedBuildTarget.Standalone,"com.lulustudio.farm");
            PlayerSettings.Android.minSdkVersion=AndroidSdkVersions.AndroidApiLevel26;
            PlayerSettings.Android.targetArchitectures=AndroidArchitecture.ARM64;
            PlayerSettings.defaultInterfaceOrientation=UIOrientation.LandscapeLeft;
            PlayerSettings.allowedAutorotateToLandscapeLeft=true;PlayerSettings.allowedAutorotateToLandscapeRight=true;
            PlayerSettings.allowedAutorotateToPortrait=false;PlayerSettings.allowedAutorotateToPortraitUpsideDown=false;
            var settings = new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/ProjectSettings.asset").FirstOrDefault());
            if(settings.targetObject!=null){var input=settings.FindProperty("activeInputHandler");if(input!=null){input.intValue=1;settings.ApplyModifiedPropertiesWithoutUndo();}}
            ConfigureRenderPipeline();
            registry=JsonUtility.FromJson<AssetRegistry>(File.ReadAllText(Base+"Data/asset-registry.json"));
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            var findings=new List<ImportFinding>();var comparisons=new List<AcceptancePair>();prefabs.Clear();issues.Clear();int importedCount=0;
            foreach(var a in registry.assets)
            {
                if(!CanIntegrate(a))
                {issues.Add(a.id+": excluded failed visual candidate "+a.version);continue;}
                GameObject source=AssetDatabase.LoadAssetAtPath<GameObject>(a.path);
                if(source==null){issues.Add(a.id+": importer returned no GameObject");continue;}
                if(source.GetComponentsInChildren<Renderer>(true).SelectMany(r=>r.sharedMaterials)
                    .Any(m=>m==null||m.shader==null||!m.shader.isSupported||m.GetTag("RenderPipeline",true,"")!="UniversalPipeline"))
                {issues.Add(a.id+": imported materials are not URP; reopen editor and run Farm/01a Refresh imported materials for active URP");continue;}
                GameObject root=new GameObject(a.id+" — "+a.name);
                var adapter=new GameObject("VisualAdapter");adapter.transform.SetParent(root.transform,false);
                var visual=(GameObject)PrefabUtility.InstantiatePrefab(source);visual.name="Visual";visual.transform.SetParent(adapter.transform,false);
                Bounds b=BoundsOf(root);
                if(a.id=="S05" && b.center.x<-.2f){adapter.transform.localRotation=Quaternion.Euler(0,180,0);b=BoundsOf(root);}
                if(a.adapterScale>0)
                {adapter.transform.localScale=Vector3.one*a.adapterScale;adapter.transform.localPosition=a.adapterOffset;}
                else if(a.type!="reused")
                {
                    float scale=a.worldHeight>0&&b.size.y>.00001f?a.worldHeight/b.size.y:1;
                    adapter.transform.localScale=Vector3.one*scale;
                    b=BoundsOf(root);adapter.transform.position-=new Vector3(b.center.x,b.min.y,b.center.z);
                }
                foreach(var r in root.GetComponentsInChildren<Renderer>(true))
                {
                    foreach(var m in r.sharedMaterials)if(m!=null)m.enableInstancing=true;
                    r.receiveShadows=true;
                    if(a.type=="crop"||a.id=="E11")r.shadowCastingMode=ShadowCastingMode.On;
                }
                BuildLOD(a,root,adapter.transform,visual);
                var renderers=root.GetComponentsInChildren<Renderer>(true);
                int tris=root.GetComponentsInChildren<MeshFilter>(true).Sum(m=>m.sharedMesh!=null?m.sharedMesh.triangles.Length/3:0)+root.GetComponentsInChildren<SkinnedMeshRenderer>(true).Sum(m=>m.sharedMesh!=null?m.sharedMesh.triangles.Length/3:0);
                b=BoundsOf(root);
                var f=new ImportFinding{id=a.id,path=a.path,triangles=tris,renderers=renderers.Length,materials=renderers.SelectMany(r=>r.sharedMaterials).Distinct().Count(),center=b.center,size=b.size,warnings=renderers.Any(r=>r.sharedMaterials.Any(m=>m==null))?new[]{"missing material"}:Array.Empty<string>()};
                findings.Add(f);
                string candidatePath=Base+"Prefabs/"+a.id+".prefab";
                PrefabUtility.SaveAsPrefabAsset(root,candidatePath);
                if(!string.IsNullOrEmpty(a.beforePath))
                {
                    var beforeSource=AssetDatabase.LoadAssetAtPath<GameObject>(a.beforePath);
                    if(beforeSource!=null)
                    {
                        Directory.CreateDirectory(Base+"Prefabs/Comparisons");
                        var beforeRoot=new GameObject(a.id+" — unchanged source comparison");
                        var beforeAdapter=new GameObject("VisualAdapter");beforeAdapter.transform.SetParent(beforeRoot.transform,false);
                        beforeAdapter.transform.localPosition=adapter.transform.localPosition;beforeAdapter.transform.localRotation=adapter.transform.localRotation;beforeAdapter.transform.localScale=adapter.transform.localScale;
                        var beforeVisual=(GameObject)PrefabUtility.InstantiatePrefab(beforeSource);beforeVisual.transform.SetParent(beforeAdapter.transform,false);
                        beforeVisual.transform.localScale=Vector3.one*(a.sourceSpaceScale>0?a.sourceSpaceScale:1);
                        beforeVisual.transform.localPosition=a.sourceSpaceOffset;
                        string beforePrefab=Base+"Prefabs/Comparisons/"+a.id+".prefab";
                        PrefabUtility.SaveAsPrefabAsset(beforeRoot,beforePrefab);Object.DestroyImmediate(beforeRoot);
                        comparisons.Add(new AcceptancePair{id=a.id,beforePrefab=beforePrefab,afterPrefab=candidatePath});
                    }
                    else issues.Add(a.id+" before source could not be imported");
                }
                Object.DestroyImmediate(root);
                if(++importedCount%4==0){AssetDatabase.SaveAssets();EditorUtility.UnloadUnusedAssetsImmediate();}
            }
            AssetDatabase.SaveAssets();
            File.WriteAllText("Evidence/import-report.json",JsonUtility.ToJson(new ImportReport{utc=DateTime.UtcNow.ToString("o"),editor=Application.unityVersion,findings=findings.ToArray(),status=issues.Count==0?"imported_pending_visual_review":"import_errors"},true));
            File.WriteAllLines("Evidence/import-issues.txt",issues);
            File.WriteAllText(Base+"Data/acceptance-comparisons.json",JsonUtility.ToJson(new AcceptancePairs{pairs=comparisons.ToArray()},true));
            WriteStamp("Evidence/import-stamp.json",issues.Count==0?"imported_pending_visual_review":"import_errors");
            if(issues.Count>0)throw new Exception(string.Join("\n",issues));
        }

        static void WriteStamp(string file,string status)
        {File.WriteAllText(file,JsonUtility.ToJson(new IntegrationStamp{registrySHA256=RegistryHash(),utc=DateTime.UtcNow.ToString("o"),status=status,issues=issues.ToArray()},true));}
        static void RequireCurrentStamp(string file,string expected)
        {
            if(!File.Exists(file))throw new InvalidOperationException("Required executed integration step is missing: "+file);
            var stamp=JsonUtility.FromJson<IntegrationStamp>(File.ReadAllText(file));
            if(stamp.registrySHA256!=RegistryHash()||stamp.status!=expected||(stamp.issues!=null&&stamp.issues.Length>0))
                throw new InvalidOperationException("Integration step is stale or has errors: "+file+". Rerun the preceding Farm menu step.");
        }

        static string RegistryHash()
        {using(var hash=System.Security.Cryptography.SHA256.Create())return BitConverter.ToString(hash.ComputeHash(File.ReadAllBytes(Base+"Data/asset-registry.json"))).Replace("-","").ToLowerInvariant();}
        static void BuildLOD(AssetRecord a,GameObject root,Transform adapter,GameObject visual)
        {
            if(a.lodPaths==null||a.lodPaths.Length==0)return;
            var levels=new List<LOD>();var first=visual.GetComponentsInChildren<Renderer>(true);
            float near=a.type=="crop"?(a.stage=="seedling"?.035f:.14f):.22f;
            levels.Add(new LOD(near,first));
            var bones=visual.GetComponentsInChildren<Transform>(true).GroupBy(t=>t.name).ToDictionary(g=>g.Key,g=>g.First());
            for(int i=0;i<a.lodPaths.Length;i++)
            {
                var source=AssetDatabase.LoadAssetAtPath<GameObject>(a.lodPaths[i]);if(source==null){issues.Add(a.id+" missing LOD source "+a.lodPaths[i]);continue;}
                var level=(GameObject)PrefabUtility.InstantiatePrefab(source);level.name="LOD"+(i+1);level.transform.SetParent(adapter,false);
                bool valid=true;
                foreach(var skin in level.GetComponentsInChildren<SkinnedMeshRenderer>(true))
                {
                    var rebound=skin.bones.Select(b=>b!=null&&bones.TryGetValue(b.name,out var target)?target:null).ToArray();
                    if(rebound.Any(b=>b==null)){issues.Add(a.id+" LOD skeleton mismatch; level excluded");valid=false;break;}
                    skin.bones=rebound;if(skin.rootBone!=null&&bones.TryGetValue(skin.rootBone.name,out var rootBone))skin.rootBone=rootBone;
                }
                if(!valid){Object.DestroyImmediate(level);continue;}
                foreach(var animation in level.GetComponentsInChildren<Animation>(true))Object.DestroyImmediate(animation);
                foreach(var animator in level.GetComponentsInChildren<Animator>(true))Object.DestroyImmediate(animator);
                float far=a.stage=="seedling"?.003f:.008f;
                float threshold=i==a.lodPaths.Length-1?far:Mathf.Lerp(near,far,(i+1f)/(a.lodPaths.Length+1f));
                levels.Add(new LOD(threshold,level.GetComponentsInChildren<Renderer>(true)));
            }
            var group=root.AddComponent<LODGroup>();group.fadeMode=LODFadeMode.None;group.SetLODs(levels.ToArray());group.RecalculateBounds();
        }

        static void ConfigureRenderPipeline()
        {
            var renderer=AssetDatabase.LoadAssetAtPath<UniversalRendererData>(Base+"Settings/FarmRenderer.asset");
            if(renderer==null){renderer=ScriptableObject.CreateInstance<UniversalRendererData>();AssetDatabase.CreateAsset(renderer,Base+"Settings/FarmRenderer.asset");}
            ResourceReloader.ReloadAllNullIn(renderer,"Packages/com.unity.render-pipelines.universal");
            renderer.postProcessData=AssetDatabase.LoadAssetAtPath<PostProcessData>("Packages/com.unity.render-pipelines.universal/Runtime/Data/PostProcessData.asset");
            if(renderer.postProcessData==null)throw new InvalidOperationException("URP renderer post-process resources were not resolved.");
            EditorUtility.SetDirty(renderer);
            var desktop=Pipeline("DesktopURP",DesktopContactRenderer(renderer),1f,4,40,2048);
            if(R07Rendering)ConfigureR07Desktop(desktop);
            var mobile=Pipeline("MobileURP",renderer,.85f,2,24,1024);
            GraphicsSettings.defaultRenderPipeline=desktop;
            QualitySettings.SetQualityLevel(0,false);QualitySettings.renderPipeline=mobile;
            QualitySettings.skinWeights=SkinWeights.FourBones;QualitySettings.globalTextureMipmapLimit=0;
            if(QualitySettings.names.Length>1){QualitySettings.SetQualityLevel(1,false);QualitySettings.renderPipeline=desktop;QualitySettings.skinWeights=SkinWeights.FourBones;QualitySettings.globalTextureMipmapLimit=0;}
            var quality=new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/QualitySettings.asset").FirstOrDefault());
            if(quality.targetObject!=null)
            {
                var list=quality.FindProperty("m_QualitySettings");
                if(list!=null&&list.arraySize>=2){list.GetArrayElementAtIndex(0).FindPropertyRelative("name").stringValue="Mobile";list.GetArrayElementAtIndex(1).FindPropertyRelative("name").stringValue="Desktop";quality.ApplyModifiedPropertiesWithoutUndo();}
            }
            grass=Mat("Grass",new Color(.48f,.69f,.20f),.14f);path=Mat("WarmPath",new Color(.82f,.62f,.34f),.08f);clay=Mat("NeutralClay",new Color(.52f,.52f,.52f),.12f);
            water=AssetDatabase.LoadAssetAtPath<Material>(Base+"Materials/PondWater.mat");
            if(water==null){water=new Material(Shader.Find("LuluFarm/PondWater"));AssetDatabase.CreateAsset(water,Base+"Materials/PondWater.mat");}
        }
        static UniversalRenderPipelineAsset Pipeline(string name,UniversalRendererData data,float scale,int msaa,float distance,int resolution)
        {
            string location=Base+"Settings/"+name+".asset";
            var a=AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(location);
            if(a==null){a=UniversalRenderPipelineAsset.Create(data);AssetDatabase.CreateAsset(a,location);}
            a.renderScale=scale;a.msaaSampleCount=msaa;a.shadowDistance=distance;a.supportsHDR=false;
            var serial=new SerializedObject(a);serial.FindProperty("m_MainLightRenderingMode").intValue=(int)LightRenderingMode.PerPixel;serial.FindProperty("m_AdditionalLightsRenderingMode").intValue=(int)LightRenderingMode.Disabled;serial.FindProperty("m_MainLightShadowsSupported").boolValue=true;serial.FindProperty("m_SoftShadowsSupported").boolValue=true;serial.ApplyModifiedPropertiesWithoutUndo();
            a.mainLightShadowmapResolution=resolution;
            var rendererList=serial.FindProperty("m_RendererDataList");rendererList.arraySize=1;rendererList.GetArrayElementAtIndex(0).objectReferenceValue=data;serial.ApplyModifiedPropertiesWithoutUndo();
            a.useSRPBatcher=true;a.shadowCascadeCount=2;EditorUtility.SetDirty(a);return a;
        }
        static Material Mat(string name,Color color,float smooth)
        {
            string p=Base+"Materials/"+name+".mat";var m=AssetDatabase.LoadAssetAtPath<Material>(p);
            if(m==null){m=new Material(Shader.Find("Universal Render Pipeline/Lit"));AssetDatabase.CreateAsset(m,p);}
            m.SetColor("_BaseColor",color);m.SetFloat("_Smoothness",smooth);m.SetFloat("_Metallic",0);m.enableInstancing=true;return m;
        }
        public static Bounds BoundsOf(GameObject go)
        {
            var rs=go.GetComponentsInChildren<Renderer>(true);if(rs.Length==0)return new Bounds(go.transform.position,Vector3.zero);
            Bounds b=rs[0].bounds;foreach(var r in rs.Skip(1))b.Encapsulate(r.bounds);return b;
        }
        static GameObject Place(string id,Vector3 pos,Transform parent,float yaw=0,float scale=1)
        {
            if(registry==null||!registry.assets.Any(a=>a.id==id&&CanIntegrate(a)))
            {issues.Add("Placement excluded by current registry: "+id);return null;}
            if(!prefabs.TryGetValue(id,out var p)){p=AssetDatabase.LoadAssetAtPath<GameObject>(Base+"Prefabs/"+id+".prefab");if(p!=null)prefabs[id]=p;}
            if(p==null){issues.Add("Missing placement "+id);return null;}
            var go=(GameObject)PrefabUtility.InstantiatePrefab(p);go.transform.SetParent(parent,false);go.transform.localPosition=pos;go.transform.localRotation=Quaternion.Euler(0,yaw,0);go.transform.localScale=Vector3.one*scale;return go;
        }
        static Transform Group(string name){var g=new GameObject(name);g.transform.SetParent(world,false);return g.transform;}
        static void Box(Transform parent,string name,Vector3 center,Vector3 size)
        {var g=new GameObject(name);g.transform.SetParent(parent,false);g.transform.localPosition=center;var c=g.AddComponent<BoxCollider>();c.size=size;}
        static void Footprint(GameObject go,float fraction=.8f)
        {
            if(go==null)return;
            var renderers=go.GetComponentsInChildren<Renderer>(true);if(renderers.Length==0)return;
            Bounds local=new Bounds();bool first=true;
            foreach(var renderer in renderers)
            {
                var b=renderer.localBounds;
                for(int i=0;i<8;i++)
                {
                    Vector3 p=go.transform.InverseTransformPoint(renderer.transform.TransformPoint(new Vector3((i&1)==0?b.min.x:b.max.x,(i&2)==0?b.min.y:b.max.y,(i&4)==0?b.min.z:b.max.z)));
                    if(first){local=new Bounds(p,Vector3.zero);first=false;}else local.Encapsulate(p);
                }
            }
            var g=new GameObject("SimpleCollision");g.transform.SetParent(go.transform,false);var c=g.AddComponent<BoxCollider>();c.center=local.center;c.size=new Vector3(local.size.x*fraction,local.size.y*.9f,local.size.z*fraction);
        }

        [MenuItem("Farm/02 Build full farm scene")]
        public static void BuildFarm()
        {
            RequireCurrentStamp("Evidence/import-stamp.json","imported_pending_visual_review");
            if(!Application.isBatchMode&&!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo())return;
            if(Application.isBatchMode&&Enumerable.Range(0,SceneManager.sceneCount).Any(i=>SceneManager.GetSceneAt(i).isDirty))
                throw new InvalidOperationException("Refusing to replace unsaved scenes in batch farm generation.");
            registry=JsonUtility.FromJson<AssetRegistry>(File.ReadAllText(Base+"Data/asset-registry.json"));
            ConfigureRenderPipeline();issues.Clear();prefabs.Clear();
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
            world=new GameObject("FarmWorld — overview layout r01").transform;
            var landscape=Group("Landscape");CreateGround(landscape);CreatePaths(landscape);
            var houseGroup=Group("HouseAndProduce");
            var house=Place("S01",new Vector3(0,0,6.3f),houseGroup,180);HouseCollision(house);if(house!=null)FarmOcclusionSetup.Configure(house,false);
            var produce=Place("S03",new Vector3(4.3f,0,5.8f),houseGroup,180);Footprint(produce);
            Footprint(Place("S11",new Vector3(2.8f,0,4.7f),houseGroup,25),.92f);
            Footprint(Place("S12",new Vector3(-10.8f,0,5.1f),houseGroup,25),.8f);
            var fields=Group("Fields");var crops=new List<FarmCropStage>();
            string[] names={"cabbage","tomato","corn","cucumber","pumpkin","sunflower","wheat","bokchoy","rose","strawberry","cauliflower","watermelon","tulip","lettuce","cabbage","tomato","corn","pumpkin","wheat","lettuce"};
            for(int i=0;i<20;i++)
            {
                var cell=new GameObject("Plot_"+(i+1).ToString("00")+"_"+names[i]);cell.transform.SetParent(fields,false);cell.transform.position=new Vector3(-10.3f+(i%4)*1.2f,0,4.1f-(i/4)*1.2f);
                var soil=Place("E01",Vector3.zero,cell.transform);
                if(soil!=null)
                {
                    var lod=soil.GetComponent<LODGroup>();
                    var soilRenderers=lod!=null?lod.GetLODs()[0].renderers:soil.GetComponentsInChildren<Renderer>(true);
                    foreach(var r in soilRenderers.Where(r=>r.name.Contains("edge rail")||r.name.Contains("corner joint")))
                    {
                        // Keep the raised wood contacts while the central soil uses a cheap walk plane.
                        // The authored rails remain collidable when their render LOD changes.
                        var collider=r.gameObject.AddComponent<BoxCollider>();collider.center=r.localBounds.center;collider.size=r.localBounds.size;
                    }
                }
                Box(cell.transform,"SoilWalkSurface",new Vector3(0,-.055f,0),new Vector3(1.2f,.1f,1.2f));
                var stage=cell.AddComponent<FarmCropStage>();stage.assetId="Plot"+i;stage.species=names[i];
                stage.seedling=Place(names[i]+"-seedling",Vector3.zero,cell.transform);stage.mature=Place(names[i]+"-mature",Vector3.zero,cell.transform);
                stage.seedlingSourceVersion=Record(names[i]+"-seedling")?.version;stage.matureSourceVersion=Record(names[i]+"-mature")?.version;
                stage.SetMature(i%4!=1&&i%5!=3);crops.Add(stage);
            }
            // Reuse the approved fence on the field's north, west and south sides;
            // leave the east side open to the connecting path and crop inspection lane.
            var fieldBoundary=Group("FieldBoundary");
            FenceLine(fieldBoundary,new Vector3(-5.5f,0,5.9f),5,180,false);
            FenceLine(fieldBoundary,new Vector3(-11.5f,0,5.9f),7,90,false);
            FenceLine(fieldBoundary,new Vector3(-11.5f,0,-2.5f),5,0,true);
            var pasture=Group("Pasture");
            FenceLine(pasture,new Vector3(1.2f,0,-6.5f),4,180,false);
            FenceLine(pasture,new Vector3(-3.6f,0,-6.5f),7,-90,false);
            FenceLine(pasture,new Vector3(-3.6f,0,1.9f),8,0,false);
            FenceLine(pasture,new Vector3(6,0,1.9f),7,90,false);
            FenceLine(pasture,new Vector3(6,0,-6.5f),2,180,true);
            var gate=Place("S06",new Vector3(2.4f,0,-6.5f),pasture);
            if(gate!=null)foreach(var part in gate.GetComponentsInChildren<MeshRenderer>())Footprint(part.gameObject,.96f);
            // Two source-derived rails bridge the measured gap. Keep their original Y/Z section and shared fence posts.
            foreach(var span in new[]{new Vector2(1.31f,1.598f),new Vector2(3.202f,3.49f)})
            {
                var rails=Place("S05-rail-connector",new Vector3((span.x+span.y)*.5f,0,-6.5f),pasture);
                if(rails!=null){rails.transform.localScale=new Vector3((span.y-span.x)/1.2f,1,1);Box(rails.transform,"ShortRailCollision",new Vector3(0,.46f,0),new Vector3(1.2f,.9f,.14f));}
            }
            // S02 pasture barn sits in the north half, door to -Z toward the pasture gate.
            // The whole footprint is solid: the modelled door is decorative and has no interior.
            var barn=Place("S02",new Vector3(1.8f,0,-.1f),pasture,180);Footprint(barn,.98f);
            Footprint(Place("S09",new Vector3(4.4f,0,-1.9f),pasture,90),.94f);Footprint(Place("E15",new Vector3(4.6f,0,.7f),pasture,25),.85f);
            string[] animals={"cow","sheep","chicken","pig","duck"};
            // The sheep moved south of the barn front; its r06 spot (1,0,-1.5) is inside the barn footprint.
            Vector3[] animalPositions={new Vector3(-1.7f,0,-.3f),new Vector3(.6f,0,-2.9f),new Vector3(-2.2f,0,-4.2f),new Vector3(.7f,0,-4.3f),new Vector3(3.8f,0,-4.4f)};
            for(int i=0;i<animals.Length;i++){var a=Place(animals[i],animalPositions[i],pasture,150+i*35);Footprint(a,.7f);}
            BuildPond(Group("Pond"));
            LandscapeInstances(landscape);
            PolishLandscape(landscape);
            if(R07Task=="D4"||R07Task=="D6")FarmDecorScatter.Build(world,landscape,Place);
            Lighting();
            var player=new GameObject("LuluPlayer");player.transform.position=new Vector3(0,.05f,3.15f);
            var orientation=new GameObject("PlayerOrientation");orientation.transform.SetParent(player.transform,false);
            var lulu=Place("Lulu",Vector3.zero,orientation.transform,0);
            var cameraGO=new GameObject("Main Camera",typeof(Camera),typeof(AudioListener));cameraGO.tag="MainCamera";
            Camera camera=cameraGO.GetComponent<Camera>();camera.fieldOfView=52;camera.nearClipPlane=.1f;camera.farClipPlane=120;camera.clearFlags=CameraClearFlags.Skybox;camera.backgroundColor=new Color(.58f,.80f,.91f);
            cameraGO.transform.position=player.transform.position+new Vector3(0,3.6f,-4.5f);cameraGO.transform.LookAt(player.transform.position+Vector3.up*.7f);
            if(lulu!=null)
            {
                var rt=FarmRuntimeBootstrap.Attach(player,orientation.transform,camera,new Bounds(Vector3.zero,new Vector3(33,20,23)));
                rt.crops=crops.ToArray();rt.sceneRevision="integration-r07-"+R07Task;rt.assetRegistryRevision=RegistryHash();rt.uiFont=AssetDatabase.LoadAssetAtPath<Font>(Base+"Fonts/NotoSansCJKsc-Regular.otf");
                rt.gameObject.AddComponent<FarmPresentationModeR07>().runtime=rt;
                if(R07Rendering){var renderQuality=rt.gameObject.AddComponent<FarmRenderQualityR07>();renderQuality.runtime=rt;renderQuality.globalVolume=UnityEngine.Object.FindFirstObjectByType<Volume>();camera.allowHDR=true;camera.GetUniversalAdditionalCameraData().renderPostProcessing=true;}
                rt.mobilePipeline=AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(Base+"Settings/MobileURP.asset");rt.desktopPipeline=AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(Base+"Settings/DesktopURP.asset");
                var clips=AssetDatabase.LoadAllAssetsAtPath(Record("Lulu").path).OfType<AnimationClip>().ToArray();
                rt.idleClip=clips.FirstOrDefault(c=>c.name.Contains("Idle"));rt.walkClip=clips.FirstOrDefault(c=>c.name.Contains("Walk"));rt.runClip=clips.FirstOrDefault(c=>c.name.Contains("Run"));
                if(rt.idleClip==null||rt.walkClip==null||rt.runClip==null)issues.Add("Full farm needs actual imported Idle/Walk/Run clips.");
                SetupWardrobe(lulu,rt);
                if(R07Task=="D6")FarmLivingSetupR07.Build(world,rt);
                rt.routeMarkers=new[]{Marker("主屋前",0,3.15f),Marker("田地",-6,2),Marker("牧场入口",2.4f,-7.2f),Marker("饲料槽",4.3f,-2.8f),Marker("池塘",6.7f,DockZ),Marker("码头",8.6f,DockZ),Marker("渔产摊位",10,-5.7f),Marker("主屋背面",0,9.5f),Marker("返回",0,3.15f)};
                if(R07Task=="D6")FarmRouteClearanceR07.Configure(rt);
            }
            foreach(var marker in issues)Debug.LogWarning(marker);
            if(!EditorSceneManager.SaveScene(SceneManager.GetActiveScene(),Base+"Scenes/FarmWorld.unity"))issues.Add("Full farm scene save failed.");
            EditorBuildSettings.scenes=new[]{new EditorBuildSettingsScene(Base+"Scenes/FarmWorld.unity",true)};
            AssetDatabase.SaveAssets();File.WriteAllLines("Evidence/scene-build-issues.txt",issues);
            WriteStamp("Evidence/scene-generation-status.json",issues.Count==0?"generated_pending_actual_play_and_visual_checks":"scene_generation_errors");
            if(issues.Count>0)throw new InvalidOperationException(string.Join("\n",issues));
        }
        static AssetRecord Record(string id)=>registry.assets.FirstOrDefault(a=>a.id==id);
        static FarmRouteMarker Marker(string name,float x,float z)=>new FarmRouteMarker{name=name,position=new Vector3(x,0,z),radius=1.0f};
        static void FenceLine(Transform parent,Vector3 start,int count,float yaw,bool endcap=true)
        {
            var direction=Quaternion.Euler(0,yaw,0)*Vector3.right;
            for(int i=0;i<count;i++)Place("S05",start+direction*1.2f*i,parent,yaw);
            if(endcap)Place("S05-endcap",start+direction*1.2f*count,parent,yaw);
            var mid=start+direction*.6f*count;var g=new GameObject("FenceCollision");g.transform.SetParent(parent,false);g.transform.localPosition=mid;g.transform.localRotation=Quaternion.Euler(0,yaw,0);var c=g.AddComponent<BoxCollider>();c.center=new Vector3(0,.46f,0);c.size=new Vector3(1.2f*count,.92f,.16f);
        }
        static void SetupWardrobe(GameObject lulu,FarmRuntimeBootstrap rt)
        {
            var renderers=lulu.GetComponentsInChildren<SkinnedMeshRenderer>(true).Where(x=>x.name.IndexOf("Shorts",StringComparison.OrdinalIgnoreCase)>=0).ToArray();
            if(renderers.Length==0){issues.Add("Shorts renderer missing");return;}
            var blue=Fabric("BlueStars","blue-stars.png");var melon=Fabric("Watermelon","watermelon.png");
            var wardrobe=lulu.AddComponent<FarmWardrobe>();wardrobe.bindings=renderers.Select(r=>new FarmWardrobeBinding{renderer=r,original=r.sharedMaterials,blueStars=Enumerable.Repeat(blue,r.sharedMaterials.Length).ToArray(),watermelon=Enumerable.Repeat(melon,r.sharedMaterials.Length).ToArray()}).ToArray();rt.wardrobe=wardrobe;
        }
        static Material Fabric(string name,string tex)
        {var m=AssetDatabase.LoadAssetAtPath<Material>(Base+"Materials/"+name+".mat");if(m==null){m=new Material(Shader.Find("LuluFarm/FabricUV"));AssetDatabase.CreateAsset(m,Base+"Materials/"+name+".mat");}m.SetTexture("_BaseMap",AssetDatabase.LoadAssetAtPath<Texture2D>(Base+"Art/Wardrobe/"+tex));return m;}
        static List<Vector2> PondLoop(float expansion=0)
        {
            float minX=PondMinX-expansion,maxX=PondMaxX+expansion,minZ=PondMinZ-expansion,maxZ=PondMaxZ+expansion,r=BankRadius+expansion;
            var points=new List<Vector2>();
            Vector2[] centers={new Vector2(maxX-r,maxZ-r),new Vector2(minX+r,maxZ-r),new Vector2(minX+r,minZ+r),new Vector2(maxX-r,minZ+r)};
            for(int c=0;c<4;c++)for(int i=0;i<=12;i++){float a=(c*90+i*7.5f)*Mathf.Deg2Rad;points.Add(centers[c]+new Vector2(Mathf.Cos(a),Mathf.Sin(a))*r);}
            return points;
        }
        static Mesh MeshAsset(string name,List<Vector3> vertices,List<int> triangles)
        {
            var mesh=new Mesh{name=name};mesh.SetVertices(vertices);mesh.SetTriangles(triangles,0);mesh.RecalculateNormals();mesh.RecalculateBounds();
            if(name=="GroundWithSoilAndPondOpenings"||name=="RoadNetwork")mesh.SetUVs(0,vertices.Select(p=>new Vector2(p.x,p.z)).ToList());
            string p=Base+"Data/"+name+".asset";var existing=AssetDatabase.LoadAssetAtPath<Mesh>(p);
            if(existing!=null){EditorUtility.CopySerialized(mesh,existing);Object.DestroyImmediate(mesh);mesh=existing;}else AssetDatabase.CreateAsset(mesh,p);return mesh;
        }
        static GameObject MeshObject(Transform parent,string name,Mesh mesh,Material material,bool collide)
        {var go=new GameObject(name,typeof(MeshFilter),typeof(MeshRenderer));go.transform.SetParent(parent,false);go.GetComponent<MeshFilter>().sharedMesh=mesh;go.GetComponent<MeshRenderer>().sharedMaterial=material;if(collide)go.AddComponent<MeshCollider>().sharedMesh=mesh;return go;}
        static void CreateGround(Transform parent)
        {
            // Horizontal bands retain a continuous grass surface with real openings under soil and water.
            // Source soil is recessed below Y=0; drawing a grass plane underneath it would cover the soil.
            // E05 turf extends .60 outward, with its last .35 at Y=0. Open the
            // whole footprint so the generated plane cannot Z-fight the turf.
            var loop=PondLoop(.60f);var v=new List<Vector3>();var t=new List<int>();
            var zLevels=loop.Select(p=>p.y).Concat(new[]{-60f,-1.3f,4.7f,60f}).OrderBy(z=>z).ToList();
            var zs=new List<float>();foreach(float z in zLevels)if(zs.Count==0||z-zs[zs.Count-1]>.00001f)zs.Add(z);
            for(int i=0;i<zs.Count-1;i++)
            {
                float za=zs[i],zb=zs[i+1],mid=(za+zb)*.5f;
                bool hasPond=mid>loop.Min(p=>p.y)&&mid<loop.Max(p=>p.y);
                if(hasPond)
                {
                    Vector2 atA=PondSpan(loop,za),atB=PondSpan(loop,zb);
                    GroundBand(v,t,za,zb,-60,-60,atA.x,atB.x,mid>-1.3f&&mid<4.7f);
                    GroundBand(v,t,za,zb,atA.y,atB.y,60,60,false);
                }
                else GroundBand(v,t,za,zb,-60,-60,60,60,mid>-1.3f&&mid<4.7f);
            }
            MeshObject(parent,"ContinuousGroundWithSoilAndPondOpenings",MeshAsset("GroundWithSoilAndPondOpenings",v,t),grass,true);
            Box(parent,"NorthBoundary",new Vector3(0,1,12),new Vector3(34,2,.2f));Box(parent,"SouthBoundary",new Vector3(0,1,-12),new Vector3(34,2,.2f));Box(parent,"EastBoundary",new Vector3(17,1,0),new Vector3(.2f,2,24));Box(parent,"WestBoundary",new Vector3(-17,1,0),new Vector3(.2f,2,24));
        }
        static Vector2 PondSpan(List<Vector2> loop,float z)
        {
            var xs=new List<float>();
            for(int i=0;i<loop.Count;i++)
            {
                Vector2 a=loop[i],b=loop[(i+1)%loop.Count];
                if(z<Mathf.Min(a.y,b.y)-.00002f||z>Mathf.Max(a.y,b.y)+.00002f)continue;
                if(Mathf.Abs(b.y-a.y)<.00001f){xs.Add(a.x);xs.Add(b.x);}
                else xs.Add(Mathf.Lerp(a.x,b.x,Mathf.Clamp01((z-a.y)/(b.y-a.y))));
            }
            if(xs.Count<2)throw new InvalidOperationException("Pond contour cannot be intersected at "+z);
            return new Vector2(xs.Min(),xs.Max());
        }
        static void GroundBand(List<Vector3> v,List<int> t,float za,float zb,float leftA,float leftB,float rightA,float rightB,bool cutField)
        {
            if(cutField)
            {GroundBand(v,t,za,zb,leftA,leftB,-10.9f,-10.9f,false);GroundBand(v,t,za,zb,-6.1f,-6.1f,rightA,rightB,false);return;}
            int k=v.Count;v.AddRange(new[]{new Vector3(leftA,0,za),new Vector3(leftB,0,zb),new Vector3(rightB,0,zb),new Vector3(rightA,0,za)});
            t.AddRange(new[]{k,k+1,k+2,k,k+2,k+3});
        }
        static void CreatePaths(Transform parent)
        {
            Vector2[][] routes={new[]{new Vector2(-14,-8.3f),new Vector2(15.5f,-8.3f)},new[]{new Vector2(-5,-8.3f),new Vector2(-5,3.2f),new Vector2(0,3.2f),new Vector2(5.5f,3.2f),new Vector2(6.2f,6.1f)},new[]{new Vector2(6.5f,-8.3f),new Vector2(6.5f,3.2f)},new[]{new Vector2(2.4f,-8.3f),new Vector2(2.4f,-6.2f)},new[]{new Vector2(6.5f,-4.3f),new Vector2(11,-4.3f)},new[]{new Vector2(0,3.2f),new Vector2(0,4.7f)}};
            var v=new List<Vector3>();var t=new List<int>();int segment=0;
            foreach(var route in routes)for(int i=0;i<route.Length-1;i++)
            {
                Vector2 a=route[i],b=route[i+1],d=(b-a).normalized,n=new Vector2(-d.y,d.x)*.9f;int k=v.Count;float y=.006f+segment++*.0002f;
                v.AddRange(new[]{new Vector3(a.x+n.x,y,a.y+n.y),new Vector3(b.x+n.x,y,b.y+n.y),new Vector3(b.x-n.x,y,b.y-n.y),new Vector3(a.x-n.x,y,a.y-n.y)});t.AddRange(new[]{k,k+1,k+2,k,k+2,k+3});
                foreach(var end in new[]{a,b})
                {k=v.Count;v.Add(new Vector3(end.x,y,end.y));for(int q=0;q<=24;q++){float angle=q*Mathf.PI*2/24;v.Add(new Vector3(end.x+Mathf.Cos(angle)*.9f,y,end.y+Mathf.Sin(angle)*.9f));}for(int q=0;q<24;q++)t.AddRange(new[]{k,k+q+2,k+q+1});}
            }
            MeshObject(parent,"ContinuousWarmRoadNetwork",MeshAsset("RoadNetwork",v,t),path,false);
        }
        static void BuildPond(Transform parent)
        {
            var loop=PondLoop();var v=new List<Vector3>{new Vector3(PondCenter.x,-.105f,PondCenter.y)};var tri=new List<int>();foreach(var p in loop)v.Add(new Vector3(p.x,-.105f,p.y));for(int i=0;i<loop.Count;i++)tri.AddRange(new[]{0,1+(i+1)%loop.Count,1+i});
            var surface=MeshObject(parent,"PondWater_Continuous",MeshAsset("PondSurface",v,tri),water,false);surface.GetComponent<Renderer>().shadowCastingMode=ShadowCastingMode.Off;
            // The bank backing closes terrain gaps; selected E05/E06 derivatives provide the art surface.
            var bankMat=Mat("BankBacking",new Color(.54f,.58f,.35f),.12f);var outer=PondLoop(.60f);v.Clear();tri.Clear();
            for(int i=0;i<loop.Count;i++){v.Add(new Vector3(loop[i].x,-.28f,loop[i].y));v.Add(new Vector3(outer[i].x,-.065f,outer[i].y));}
            for(int i=0;i<loop.Count;i++){int a=i*2,b=(i+1)%loop.Count*2;tri.AddRange(new[]{a,b+1,a+1,a,b,b+1});}
            MeshObject(parent,"BankBacking",MeshAsset("BankBacking",v,tri),bankMat,false);
            // Collision follows the level upper turf; the inner guard stops the
            // capsule before the visible sloped section and open water.
            var innerWalk=PondLoop(.15f);v.Clear();tri.Clear();
            for(int i=0;i<loop.Count;i++){v.Add(new Vector3(innerWalk[i].x,0,innerWalk[i].y));v.Add(new Vector3(outer[i].x,0,outer[i].y));}
            for(int i=0;i<loop.Count;i++){int a=i*2,b=(i+1)%loop.Count*2;tri.AddRange(new[]{a,b+1,a+1,a,b,b+1});}
            var bankWalk=new GameObject("UpperBankWalkCollision",typeof(MeshCollider));bankWalk.transform.SetParent(parent,false);bankWalk.GetComponent<MeshCollider>().sharedMesh=MeshAsset("UpperBankWalkCollision",v,tri);
            // Water is not walkable. Thin shore colliders block falling in except the dock entry.
            for(int i=0;i<loop.Count;i++)
            {
                Vector2 a=loop[i],b=loop[(i+1)%loop.Count],mid=(a+b)*.5f;
                if(Vector2.Distance(a,b)<.001f)continue;
                if(Mathf.Abs(a.x-PondMinX)<.001f&&Mathf.Abs(b.x-PondMinX)<.001f)
                {
                    ShoreGuard(parent,"WestSouth",new Vector2(PondMinX,Mathf.Min(a.y,b.y)),new Vector2(PondMinX,DockZ-1.2f));
                    ShoreGuard(parent,"WestNorth",new Vector2(PondMinX,DockZ+1.2f),new Vector2(PondMinX,Mathf.Max(a.y,b.y)));
                }
                else ShoreGuard(parent,i.ToString(),a,b);
            }
            // Measured on the selected S07 GLB: long axis X, deck Y=0.072–0.078 after this uniform scale/offset.
            // Fixed source geometry spans the shore at X=7.3; Unity contact probes must still verify the import.
            var dock=Place("S07",new Vector3(8.5f,-.5915f,DockZ),parent,0,1.15f/(Record("S07")?.worldHeight??.7f));
            if(dock!=null)Box(parent,"DockDeckCollision",new Vector3(8.5f,.015f,DockZ),new Vector3(2.4f,.12f,1.4f));
            Box(parent,"DockNorthEdgeGuard",new Vector3(8.5f,.36f,DockZ+.73f),new Vector3(2.4f,.9f,.12f));
            Box(parent,"DockSouthEdgeGuard",new Vector3(8.5f,.36f,DockZ-.73f),new Vector3(2.4f,.9f,.12f));
            ShoreGuard(parent,"DockNorthShoulder",new Vector2(PondMinX,DockZ+.73f),new Vector2(PondMinX,DockZ+1.2f));
            ShoreGuard(parent,"DockSouthShoulder",new Vector2(PondMinX,DockZ-1.2f),new Vector2(PondMinX,DockZ-.73f));
            Box(parent,"DockEndGuard",new Vector3(9.7f,.36f,DockZ),new Vector3(.12f,.9f,1.58f));
            foreach(float x in new[]{7.42f,9.58f})foreach(float side in new[]{-.81f,.81f})
            {
                var post=new GameObject("DockPostCollision");post.transform.SetParent(parent,false);post.transform.localPosition=new Vector3(x,.29f,DockZ+side);
                var capsule=post.AddComponent<CapsuleCollider>();capsule.radius=.24f;capsule.height=.58f;
            }
            // Both registered LODs: lowest interior floor is local Y=.09205.
            // Keep it 6 mm above the -.105 water plane, with the outer hull submerged.
            Place("S08",new Vector3(10.9f,-.191f,-1),parent,25);
            var stall=Place("S04",new Vector3(10,0,-4.1f),parent,180);Footprint(stall,.72f);
            Place("E14",new Vector3(12.4f,-.09f,3.3f),parent,35);Place("E14",new Vector3(12.7f,-.09f,-1.5f),parent,-20,.75f);
            Place("E16",new Vector3(13.2f,-.20f,.4f),parent,160,.7f);
            foreach(var p in new[]{new Vector2(8.7f,5.9f),new Vector2(11.4f,6f),new Vector2(14.6f,4.5f),new Vector2(14.8f,1.5f),new Vector2(14.4f,-1.7f),new Vector2(11.8f,-2.5f),new Vector2(7.5f,-1.7f),new Vector2(7.5f,3.1f)})
                Place("E12",new Vector3(p.x,-.07f,p.y),parent,(p.x+p.y)*17,.85f+Mathf.Abs(Mathf.Sin(p.x))*.2f);
            for(int i=0;i<5;i++)
            {float x=PondMinX+BankRadius+.6f+i*1.2f;Place("E05",new Vector3(x,0,PondMaxZ),parent,180);Place("E05",new Vector3(x,0,PondMinZ),parent,0);}
            for(int i=0;i<6;i++)
            {float z=PondMinZ+BankRadius+.6f+i*1.2f;Place("E05",new Vector3(PondMaxX,0,z),parent,-90);if(i!=1&&i!=2)Place("E05",new Vector3(PondMinX,0,z),parent,90);}
            // glTFast changes handedness on X: the preserved corner occupies the local (-X,-Z) quadrant.
            Place("E05-corner",new Vector3(PondMinX+BankRadius,0,PondMinZ+BankRadius),parent,0);
            Place("E05-corner",new Vector3(PondMaxX-BankRadius,0,PondMinZ+BankRadius),parent,-90);
            Place("E05-corner",new Vector3(PondMaxX-BankRadius,0,PondMaxZ-BankRadius),parent,180);
            Place("E05-corner",new Vector3(PondMinX+BankRadius,0,PondMaxZ-BankRadius),parent,90);
        }
        static void ShoreGuard(Transform parent,string suffix,Vector2 a,Vector2 b)
        {
            if(Vector2.Distance(a,b)<.001f)return;var mid=(a+b)*.5f;
            var guard=new GameObject("ShoreGuard_"+suffix);guard.transform.SetParent(parent,false);guard.transform.localPosition=new Vector3(mid.x,.42f,mid.y);
            guard.transform.localRotation=Quaternion.LookRotation(new Vector3(b.x-a.x,0,b.y-a.y));
            guard.AddComponent<BoxCollider>().size=new Vector3(.14f,.85f,Vector2.Distance(a,b)+.03f);
        }
        static void LandscapeInstances(Transform parent)
        {
            Vector3[] trees={new Vector3(-14,0,-9.5f),new Vector3(-10.8f,0,-10),new Vector3(-5.8f,0,-10.4f),new Vector3(6,0,-10),new Vector3(12.6f,0,-10),new Vector3(15.7f,0,-6),new Vector3(15.7f,0,8),new Vector3(9,0,9.5f),new Vector3(4,0,10),new Vector3(-4.2f,0,9.2f),new Vector3(-9,0,8.6f),new Vector3(-14.1f,0,6),new Vector3(-14.5f,0,.5f),new Vector3(-4,0,1.2f)};
            for(int i=0;i<trees.Length;i++){var tree=Place(i%4==1?"E09":"E08",trees[i],parent,i*39,.85f+(i%3)*.08f);if(tree!=null){Box(tree.transform,"TrunkCollision",new Vector3(0,.65f,0),new Vector3(.42f,1.3f,.42f));FarmOcclusionSetup.Configure(tree,true);}}
            Vector3[] clusters={new Vector3(-3.2f,0,5),new Vector3(2.6f,0,5),new Vector3(-4.2f,0,-7),new Vector3(6.1f,0,-7.3f),new Vector3(-12,0,-2),new Vector3(-12,0,5),new Vector3(-6,0,6),new Vector3(6,0,7.5f),new Vector3(15.5f,0,-3.5f),new Vector3(-12.7f,0,-9.5f)};
            for(int i=0;i<clusters.Length;i++){Place("E10",clusters[i],parent,i*32);Place("E11",clusters[i]+new Vector3(.4f,0,-.3f),parent,i*41,.75f);}
            foreach(var position in new[]{new Vector3(-1.4f,0,4.1f),new Vector3(5.2f,0,-9.5f)})
            {
                var lantern=Place("S10",position,parent);
                if(lantern==null)continue;
                // Measured lower source geometry: decorated base occupies roughly 0.98 x 0.85 at height 0.5.
                Box(lantern.transform,"LanternBaseCollision",new Vector3(-.103f,.25f,0),new Vector3(.98f,.5f,.85f));
                Box(lantern.transform,"LanternPoleCollision",new Vector3(-.103f,.95f,0),new Vector3(.28f,1.9f,.28f));
            }
            Place("E13",new Vector3(13.6f,0,5.8f),parent,30);Place("E13",new Vector3(14.7f,0,-1.8f),parent,80);
        }
        static void Lighting()
        {
            RenderSettings.ambientMode=AmbientMode.Trilight;RenderSettings.ambientSkyColor=new Color(.62f,.73f,.82f);RenderSettings.ambientEquatorColor=new Color(.54f,.60f,.57f);RenderSettings.ambientGroundColor=new Color(.32f,.36f,.26f);RenderSettings.ambientIntensity=1;
            RenderSettings.fog=true;RenderSettings.fogMode=FogMode.Linear;RenderSettings.fogStartDistance=30;RenderSettings.fogEndDistance=75;RenderSettings.fogColor=new Color(.62f,.80f,.85f);
            var sun=new GameObject("WarmDaylight",typeof(Light));sun.transform.rotation=Quaternion.Euler(48,-35,0);var light=sun.GetComponent<Light>();light.type=LightType.Directional;light.color=new Color(1,.95f,.85f);light.intensity=1.15f;light.shadows=LightShadows.Soft;light.shadowStrength=.65f;light.shadowBias=.05f;light.shadowNormalBias=.2f;RenderSettings.sun=light;
            var probes=new GameObject("FarmLightProbes",typeof(LightProbeGroup)).GetComponent<LightProbeGroup>();var pos=new List<Vector3>();for(int x=-14;x<=14;x+=4)for(int z=-10;z<=10;z+=4){pos.Add(new Vector3(x,.6f,z));pos.Add(new Vector3(x,2.4f,z));}probes.probePositions=pos.ToArray();
            if(R07Rendering){
                RenderSettings.ambientSkyColor=Hex("#C3DCF2");RenderSettings.ambientEquatorColor=Hex("#DCE8C9");RenderSettings.ambientGroundColor=Hex("#83A062");RenderSettings.ambientIntensity=1.05f;
                light.color=Hex("#FFF0DA");light.intensity=1.25f;light.shadowStrength=.55f;
                RenderSettings.fogColor=Hex("#C9E0E6");RenderSettings.fogStartDistance=32;RenderSettings.fogEndDistance=80;
                CreateR07Volume();WriteR07RenderSettings();
            }
        }
        [MenuItem("Farm/03 Build macOS development package")]
        public static void BuildMac()
        {
            RequireCurrentStamp("Evidence/scene-generation-status.json","generated_pending_actual_play_and_visual_checks");
            PreparePlayerRendering();
            Directory.CreateDirectory("Builds/macOS");
            var report=BuildPipeline.BuildPlayer(new BuildPlayerOptions{scenes=new[]{Base+"Scenes/FarmWorld.unity"},locationPathName="Builds/macOS/LuluFarm.app",target=BuildTarget.StandaloneOSX,options=BuildOptions.Development});
            SaveBuildReport(report,"macOS");
        }
        [MenuItem("Farm/04 Build Android development APK")]
        public static void BuildAndroid()
        {
            RequireCurrentStamp("Evidence/scene-generation-status.json","generated_pending_actual_play_and_visual_checks");
            PreparePlayerRendering();
            Directory.CreateDirectory("Builds/Android");PlayerSettings.SetScriptingBackend(UnityEditor.Build.NamedBuildTarget.Android,ScriptingImplementation.IL2CPP);
            EditorUserBuildSettings.buildAppBundle=false;
            var report=BuildPipeline.BuildPlayer(new BuildPlayerOptions{scenes=new[]{Base+"Scenes/FarmWorld.unity"},locationPathName="Builds/Android/LuluFarm-development.apk",target=BuildTarget.Android,options=BuildOptions.Development});SaveBuildReport(report,"Android");
        }
        static void PreparePlayerRendering()
        {
            // HUD is constructed at runtime, so its shader has no serialized scene reference.
            // Keep that exact built-in shader in players as well as the Editor.
            var graphics = new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/GraphicsSettings.asset")[0]);
            var shaders = graphics.FindProperty("m_AlwaysIncludedShaders");
            var uiShader = UnityEngine.Canvas.GetDefaultCanvasMaterial().shader;
            if(uiShader==null)throw new InvalidOperationException("Default UI shader is missing.");
            bool found=false;
            for(int i=0;i<shaders.arraySize;i++)if(shaders.GetArrayElementAtIndex(i).objectReferenceValue==uiShader)found=true;
            if(!found){int index=shaders.arraySize;shaders.InsertArrayElementAtIndex(index);shaders.GetArrayElementAtIndex(index).objectReferenceValue=uiShader;}
            graphics.ApplyModifiedPropertiesWithoutUndo();
            PlayerSettings.enableFrameTimingStats=true;
            AssetDatabase.SaveAssets();
            File.WriteAllText("Evidence/player-rendering-configuration.json",JsonUtility.ToJson(new PlayerRenderingEvidence{uiShader=uiShader.name,frameTimingEnabled=PlayerSettings.enableFrameTimingStats},true));
        }
        [Serializable] sealed class PlayerRenderingEvidence{public string uiShader;public bool frameTimingEnabled;}
        static void SaveBuildReport(BuildReport report,string platform)
        {
            var s=report.summary;Directory.CreateDirectory("Evidence");
            File.WriteAllText("Evidence/build-"+platform+".json",JsonUtility.ToJson(new BuildEvidence{platform=platform,result=s.result.ToString(),bytes=(long)s.totalSize,seconds=s.totalTime.TotalSeconds,errors=(int)s.totalErrors,warnings=(int)s.totalWarnings,output=s.outputPath,device="not_tested"},true));
            if(s.result!=BuildResult.Succeeded)throw new Exception(platform+" build "+s.result);
        }
        [Serializable] sealed class BuildEvidence{public string platform,result,output,device;public long bytes;public double seconds;public int errors,warnings;}
    }
}
