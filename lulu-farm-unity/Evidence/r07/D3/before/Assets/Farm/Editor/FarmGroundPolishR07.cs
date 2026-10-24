using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using Object = UnityEngine.Object;
namespace LuluFarm.Editor {
 public static partial class FarmProjectBuilder {
    static bool R07Ground=>R07Task=="D3"||R07Task=="D4"||R07Task=="D6";
    static string ConfigureGroundR03(Transform landscape) {
        var targets=landscape.GetComponentsInChildren<MeshFilter>(true).Where(m=>m.sharedMesh!=null).ToArray();
        var road=targets.Single(m=>m.sharedMesh.name=="RoadNetwork");
        var ground=targets.Single(m=>m.sharedMesh.name=="GroundWithSoilAndPondOpenings");
        var shader=Shader.Find("LuluFarm/FarmGround-r03");if(shader==null)throw new InvalidOperationException("FarmGround-r03 shader missing");
        Vector4 rect;int segments;var mask=PolishRoadMaskR03(road,out rect,out segments);
        var material=PolishSurfaceMaterial("Ground-polish-r03",shader,grass.GetColor("_BaseColor"),path.GetColor("_BaseColor"),
            new Color(.40f,.63f,.17f),new Color(.55f,.75f,.23f),mask,rect,true);
        material.SetColor("_GrassWarm",new Color(.64f,.76f,.27f));material.SetFloat("_FineGrain",.012f);EditorUtility.SetDirty(material);
        ground.GetComponent<Renderer>().sharedMaterial=material;
        road.GetComponent<MeshRenderer>().enabled=false;
        string folder="Evidence/r07/"+R07Task;Directory.CreateDirectory(folder);
        File.WriteAllText(folder+"/ground-settings.json",JsonUtility.ToJson(new GroundR03Record{utc=DateTime.UtcNow.ToString("o"),segments=segments,maskRect=rect,roadVertices=road.sharedMesh.vertexCount,groundVertices=ground.sharedMesh.vertexCount},true));
        return "Ground-polish-r03: road and shoulder blended directly into the ground; original road mesh retained, renderer disabled; Opus review pending";
    }
    [Serializable] sealed class GroundR03Record {
        public string utc,spec="Docs/r07-ground-shading-spec.md B",shader="LuluFarm/FarmGround-r03",material="Ground-polish-r03",mask="RoadEdgeMask-r03.png";
        public bool roadRendererEnabled=false,roadGeometryRetained=true;public int segments,roadVertices,groundVertices,width=2048,height=1024;public Vector4 maskRect;
        public float transitionStart=.66f,transitionEnd=.98f,wander1=.045f,wander2=.025f,fineGrain=.012f;
    }
        static Texture2D PolishRoadMaskR03(MeshFilter road, out Vector4 worldRect, out int segmentCount)
        {
            // Read the actual generated mesh, not a second hand-maintained list of routes.
            // CreatePaths currently emits four quad vertices and two 26-vertex end caps per segment.
            var vertices = road.sharedMesh.vertices;
            const int stride = 56;
            if (vertices.Length == 0 || vertices.Length % stride != 0)
                throw new InvalidOperationException("Road mesh layout changed; update mask extraction explicitly instead of painting a stale route mask.");
            var segments = new List<Vector4>();
            float minX = float.MaxValue, minZ = float.MaxValue, maxX = float.MinValue, maxZ = float.MinValue;
            foreach (var vertex in vertices)
            {
                var p = road.transform.TransformPoint(vertex);
                minX = Mathf.Min(minX, p.x); minZ = Mathf.Min(minZ, p.z); maxX = Mathf.Max(maxX, p.x); maxZ = Mathf.Max(maxZ, p.z);
            }
            for (int i = 0; i < vertices.Length; i += stride)
            {
                var a0 = road.transform.TransformPoint(vertices[i]); var b0 = road.transform.TransformPoint(vertices[i+1]);
                var b1 = road.transform.TransformPoint(vertices[i+2]); var a1 = road.transform.TransformPoint(vertices[i+3]);
                if (Mathf.Abs(Vector3.Distance(a0, a1) - 1.8f) > .002f || Mathf.Abs(Vector3.Distance(b0, b1) - 1.8f) > .002f)
                    throw new InvalidOperationException("Road width differs from the measured 1.8-unit road. Recompute edge parameters before applying the mask.");
                Vector3 a = (a0+a1)*.5f, b = (b0+b1)*.5f;
                segments.Add(new Vector4(a.x,a.z,b.x,b.z));
            }
            minX -= 1; minZ -= 1; maxX += 1; maxZ += 1;
            worldRect = new Vector4(minX, minZ, 1/(maxX-minX), 1/(maxZ-minZ)); segmentCount = segments.Count;
            const int width = 2048, height = 1024;
            var image = new Texture2D(width, height, TextureFormat.RGB24, false, true);
            var pixels = new Color32[width * height];
            for (int y = 0; y < height; y++) for (int x = 0; x < width; x++)
            {
                Vector2 p = new Vector2(Mathf.Lerp(minX,maxX,(x+.5f)/width), Mathf.Lerp(minZ,maxZ,(y+.5f)/height));
                float distance = float.MaxValue;
                foreach (var segment in segments)
                {
                    Vector2 a = new Vector2(segment.x,segment.y), b = new Vector2(segment.z,segment.w), direction = b-a;
                    float along = Mathf.Clamp01(Vector2.Dot(p-a,direction)/Mathf.Max(.0001f,direction.sqrMagnitude));
                    distance = Mathf.Min(distance,Vector2.Distance(p,a+direction*along));
                }
                // O4/B2 two-scale edge wander, with independent green-channel shoulder weight.
                distance += .045f*Mathf.Sin(p.x*1.7f+.6f)*Mathf.Sin(p.y*1.3f-.2f) + .025f*Mathf.Sin(p.x*4.1f+1.9f)*Mathf.Sin(p.y*3.7f+.4f);
                float value = 1-Mathf.SmoothStep(0,1,Mathf.InverseLerp(.66f,.98f,distance));
                byte channel = (byte)Mathf.RoundToInt(value*255);
                float shoulder=Mathf.SmoothStep(0,1,Mathf.InverseLerp(.98f,1.25f,distance))*(1-Mathf.SmoothStep(0,1,Mathf.InverseLerp(1.25f,1.55f,distance)));
                pixels[y*width+x] = new Color32(channel,(byte)Mathf.RoundToInt(shoulder*255),0,255);
            }
            image.SetPixels32(pixels); image.Apply(false, false);
            string folder = Base + "Materials/LandscapePolish"; Directory.CreateDirectory(folder);
            string file = folder + "/RoadEdgeMask-r03.png";
            byte[] bytes = image.EncodeToPNG(); Object.DestroyImmediate(image);
            if (!File.Exists(file) || !File.ReadAllBytes(file).SequenceEqual(bytes)) File.WriteAllBytes(file, bytes);
            AssetDatabase.ImportAsset(file, ImportAssetOptions.ForceSynchronousImport);
            var importer = (TextureImporter)AssetImporter.GetAtPath(file);
            importer.textureType = TextureImporterType.Default; importer.sRGBTexture = false;
            importer.wrapMode = TextureWrapMode.Clamp; importer.filterMode = FilterMode.Trilinear; importer.anisoLevel = 2;
            importer.mipmapEnabled = true; importer.maxTextureSize = 2048; importer.textureCompression = TextureImporterCompression.Uncompressed;
            importer.SaveAndReimport();
            return AssetDatabase.LoadAssetAtPath<Texture2D>(file);
        }
 }
}
