using System;
using System.IO;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace LuluFarm.Editor
{
    public static class FarmReviewShotsR07
    {
        [Serializable] sealed class ShotList {public FarmWorldReview.Shot[] shots;}
        [Serializable] sealed class Settings {public string utc,method="Actual Unity StandardRequest (updates volume framework); HDR camera with post-processing into SDR sRGB ARGB32 target; diagnostic camera only";public bool postProcessing=true,hdr=true;public int width=1600,height=900;public float actualVignette,actualBloom,actualExposure;public string actualTonemapping;public FarmWorldReview.Shot[] shots;}
        public static void CaptureCurrent()
        {
            string task=FarmProjectBuilder.R07Task;
            string source="Evidence/r07/"+task+"/fixed/review-settings.json";
            string folder="Evidence/r07/"+task+"/fixed-pp-on";
            Capture(source,folder);
        }
        public static void Capture(string source,string folder)
        {
            EditorSceneManager.OpenScene("Assets/Farm/Scenes/FarmWorld.unity");Directory.CreateDirectory(folder);
            var shots=new List<FarmWorldReview.Shot>(JsonUtility.FromJson<ShotList>(File.ReadAllText(source)).shots);
            shots.Add(S("close-house-road",new Vector3(-1.9f,1.5f,2.2f),new Vector3(.2f,0,3.3f)));
            shots.Add(S("close-pasture-gate",new Vector3(3.5f,1.5f,-9.3f),new Vector3(2.4f,0,-6.6f)));
            shots.Add(S("close-pond-road",new Vector3(6,1.5f,-2.2f),new Vector3(6.9f,0,.3f)));
            shots.Add(S("close-house-shadow",new Vector3(2.8f,2.8f,10.4f),new Vector3(.4f,1.2f,7.6f)));
            shots.Add(S("close-tree-shadow",new Vector3(-2.6f,2,-.4f),new Vector3(-4,0,1.2f)));
            shots.Add(S("close-field-shadow",new Vector3(-6.5f,1.6f,1),new Vector3(-8.2f,.2f,1.7f)));
            bool previous=EditorSettings.asyncShaderCompilation;EditorSettings.asyncShaderCompilation=false;
            var go=new GameObject("R07_ReviewCamera",typeof(Camera));var camera=go.GetComponent<Camera>();
            camera.clearFlags=CameraClearFlags.Skybox;camera.nearClipPlane=.08f;camera.farClipPlane=160;camera.allowHDR=true;
            camera.GetUniversalAdditionalCameraData().renderPostProcessing=true;
            try {
                foreach(var s in shots){
                    camera.transform.position=s.position;camera.transform.LookAt(s.target);camera.fieldOfView=s.fov;camera.aspect=(float)s.width/s.height;
                    var rt=RenderTexture.GetTemporary(s.width,s.height,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.sRGB);
                    var old=RenderTexture.active;Texture2D texture=null;
                    try {
                        // The locked URP SingleCameraRequest omits UpdateVolumeFramework.
                        // StandardRequest runs that same volume update as the real player camera.
                        RenderPipeline.SubmitRenderRequest(camera,new RenderPipeline.StandardRequest{destination=rt});
                        RenderTexture.active=rt;texture=new Texture2D(s.width,s.height,TextureFormat.RGB24,false);
                        texture.ReadPixels(new Rect(0,0,s.width,s.height),0,0);texture.Apply();s.file=folder+"/"+s.name+".png";File.WriteAllBytes(s.file,texture.EncodeToPNG());
                    }finally{RenderTexture.active=old;RenderTexture.ReleaseTemporary(rt);if(texture!=null)UnityEngine.Object.DestroyImmediate(texture);}
                }
                var stack=VolumeManager.instance.stack;
                File.WriteAllText(folder+"/review-settings.json",JsonUtility.ToJson(new Settings{utc=DateTime.UtcNow.ToString("o"),actualVignette=stack.GetComponent<Vignette>().intensity.value,actualBloom=stack.GetComponent<Bloom>().intensity.value,actualExposure=stack.GetComponent<ColorAdjustments>().postExposure.value,actualTonemapping=stack.GetComponent<Tonemapping>().mode.value.ToString(),shots=shots.ToArray()},true));
            }finally{UnityEngine.Object.DestroyImmediate(go);EditorSettings.asyncShaderCompilation=previous;}
        }
        static FarmWorldReview.Shot S(string name,Vector3 p,Vector3 t)=>new FarmWorldReview.Shot{name=name,position=p,target=t};
    }
}
