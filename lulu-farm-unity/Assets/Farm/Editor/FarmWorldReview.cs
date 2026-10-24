using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace LuluFarm.Editor
{
    public static class FarmWorldReview
    {
        [Serializable] public sealed class Shot { public string name; public Vector3 position, target; public string file; public int width=1600, height=900; public float fov=52; }
        [Serializable] public sealed class Report { public string utc, engine, scene, status="rendered_pending_visual_review"; public string scope="actual_Unity_offscreen_scene_render_not_manual_gameplay"; public Shot[] shots; }
        public static void GenerateAndReview()
        {
            FarmProjectBuilder.BuildFarm();
            Render();
            FarmAcceptanceRunner.ValidateSceneAndAssets();
            FarmSceneContactAudit.Run();
        }
        public static void Render()
        {
            EditorSceneManager.OpenScene("Assets/Farm/Scenes/FarmWorld.unity");
            string folder="Evidence/world-review-"+DateTime.UtcNow.ToString("yyyyMMdd-HHmmss"); Directory.CreateDirectory(folder);
            bool async=EditorSettings.asyncShaderCompilation; EditorSettings.asyncShaderCompilation=false;
            var cameraGO=new GameObject("WorldReviewCamera"); var camera=cameraGO.AddComponent<Camera>();
            camera.clearFlags=CameraClearFlags.Skybox; camera.backgroundColor=new Color(.58f,.80f,.91f);
            camera.nearClipPlane=.08f; camera.farClipPlane=160; camera.fieldOfView=52;
            var all=new[]{
                S("overview",new Vector3(24,24,-30),new Vector3(0,0,1)),
                S("overview-close-diagnostic",new Vector3(8,15,-16),new Vector3(1.5f,0,.5f)),
                S("spawn",new Vector3(0,3.65f,-1.03f),new Vector3(0,.745f,3.15f)),
                S("fields",new Vector3(-5,4,-6),new Vector3(-8,.5f,1.7f)),
                S("pasture",new Vector3(2.4f,3.65f,-10.8f),new Vector3(1.2f,.7f,-2.5f)),
                S("pond",new Vector3(6.2f,4,-5.1f),new Vector3(11,.1f,1.7f)),
                S("house-front",new Vector3(-4.4f,3.7f,-.2f),new Vector3(0,1.9f,6.3f)),
                S("house-back",new Vector3(4.4f,4,12),new Vector3(0,1.9f,6.3f)),
                S("pond-east",new Vector3(19,3.7f,4),new Vector3(10,.5f,1)),
                S("field-fence",new Vector3(-14,2.6f,-4),new Vector3(-8,.5f,2)),
                S("dock",new Vector3(6.7f,2.8f,-3),new Vector3(9,.4f,.5f)),
                S("landscape-back",new Vector3(-8,4,13),new Vector3(0,.5f,1))
            };
            try
            {
                foreach(var s in all)
                {
                    camera.transform.position=s.position; camera.transform.LookAt(s.target); camera.aspect=(float)s.width/s.height;
                    var rt=RenderTexture.GetTemporary(s.width,s.height,24,RenderTextureFormat.ARGB32);
                    var old=RenderTexture.active; Texture2D tex=null;
                    try
                    {
                        RenderPipeline.SubmitRenderRequest(camera,new UniversalRenderPipeline.SingleCameraRequest{destination=rt});
                        RenderTexture.active=rt; tex=new Texture2D(s.width,s.height,TextureFormat.RGB24,false);
                        tex.ReadPixels(new Rect(0,0,s.width,s.height),0,0); tex.Apply(); s.file=folder+"/"+s.name+".png";
                        File.WriteAllBytes(s.file,tex.EncodeToPNG());
                    }
                    finally{RenderTexture.active=old; RenderTexture.ReleaseTemporary(rt);if(tex!=null)UnityEngine.Object.DestroyImmediate(tex);}
                }
                File.WriteAllText(folder+"/review-settings.json",JsonUtility.ToJson(new Report{utc=DateTime.UtcNow.ToString("o"),engine=Application.unityVersion,scene="FarmWorld",shots=all},true));
                File.WriteAllText("Evidence/latest-world-review.txt",folder);
            }
            finally {UnityEngine.Object.DestroyImmediate(cameraGO);EditorSettings.asyncShaderCompilation=async;}
        }
        static Shot S(string name,Vector3 p,Vector3 t)=>new Shot{name=name,position=p,target=t};
    }
}
