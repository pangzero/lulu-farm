using System;
using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace LuluFarm.Editor
{
    public static partial class FarmProjectBuilder
    {
        static bool R07Rendering=>R07Task!="D5";
        static Color Hex(string value){ColorUtility.TryParseHtmlString(value,out var color);return color;}
        static void ConfigureR07Desktop(UniversalRenderPipelineAsset desktop)
        {
            desktop.shadowDistance=40;desktop.shadowCascadeCount=4;desktop.supportsHDR=true;
            var p=new SerializedObject(desktop);p.FindProperty("m_SoftShadowQuality").intValue=(int)SoftShadowQuality.Medium;p.ApplyModifiedPropertiesWithoutUndo();EditorUtility.SetDirty(desktop);
            var renderer=AssetDatabase.LoadAssetAtPath<UniversalRendererData>(Base+"Settings/FarmDesktopRenderer.asset");
            foreach(var feature in renderer.rendererFeatures)
            if(feature is ScreenSpaceAmbientOcclusion)
            {
                var so=new SerializedObject(feature);var s=so.FindProperty("m_Settings");
                s.FindPropertyRelative("Intensity").floatValue=.45f;s.FindPropertyRelative("Radius").floatValue=.25f;
                s.FindPropertyRelative("DirectLightingStrength").floatValue=.15f;s.FindPropertyRelative("Downsample").boolValue=false;
                s.FindPropertyRelative("AfterOpaque").boolValue=false;so.ApplyModifiedPropertiesWithoutUndo();feature.SetActive(true);feature.Create();EditorUtility.SetDirty(feature);
            }
            EditorUtility.SetDirty(renderer);
        }
        static Volume CreateR07Volume()
        {
            const string file="Assets/Farm/Settings/FarmGlobalVolume-r03.asset";
            var profile=AssetDatabase.LoadAssetAtPath<VolumeProfile>(file);
            if(profile==null){profile=ScriptableObject.CreateInstance<VolumeProfile>();profile.name="FarmGlobalVolume-r03";AssetDatabase.CreateAsset(profile,file);}
            var tone=VolumePart<Tonemapping>(profile);tone.mode.Override(TonemappingMode.Neutral);
            var adjust=VolumePart<ColorAdjustments>(profile);adjust.postExposure.Override(.10f);adjust.contrast.Override(6);adjust.saturation.Override(8);
            var smh=VolumePart<ShadowsMidtonesHighlights>(profile);smh.shadows.Override(new Vector4(.97f,1,1.05f,0));
            var bloom=VolumePart<Bloom>(profile);bloom.threshold.Override(1);bloom.intensity.Override(.2f);bloom.scatter.Override(.6f);
            var vignette=VolumePart<Vignette>(profile);vignette.intensity.Override(.16f);vignette.smoothness.Override(.4f);
            foreach(var c in profile.components)EditorUtility.SetDirty(c);EditorUtility.SetDirty(profile);
            var volume=new GameObject("FarmGlobalVolume-r03",typeof(Volume)).GetComponent<Volume>();volume.isGlobal=true;volume.priority=10;volume.sharedProfile=profile;
            return volume;
        }
        static T VolumePart<T>(VolumeProfile profile) where T:VolumeComponent
        {
            if(!profile.TryGet<T>(out var part)){part=profile.Add<T>(true);AssetDatabase.AddObjectToAsset(part,profile);}
            part.active=true;return part;
        }
        static void WriteR07RenderSettings()
        {
            string dir="Evidence/r07/"+R07Task;Directory.CreateDirectory(dir);
            File.WriteAllText(dir+"/render-settings.json",JsonUtility.ToJson(new R07RenderEvidence {
                utc=DateTime.UtcNow.ToString("o"),ambientSky=RenderSettings.ambientSkyColor,ambientEquator=RenderSettings.ambientEquatorColor,
                ambientGround=RenderSettings.ambientGroundColor,ambientIntensity=RenderSettings.ambientIntensity,
                lightColor=RenderSettings.sun.color,lightIntensity=RenderSettings.sun.intensity,shadowStrength=RenderSettings.sun.shadowStrength,
                fogColor=RenderSettings.fogColor,fogStart=RenderSettings.fogStartDistance,fogEnd=RenderSettings.fogEndDistance},true));
        }
        [Serializable] sealed class R07RenderEvidence {
            public string utc,spec="Docs/r07-ground-shading-spec.md C",status="configured_requires_Opus_review";
            public Color ambientSky,ambientEquator,ambientGround,lightColor,fogColor;
            public float ambientIntensity,lightIntensity,shadowStrength,fogStart,fogEnd;
            public int shadowCascades=4,shadowDistance=40;public string shadowQuality="Medium",tonemapping="Neutral";
            public float ssaoIntensity=.45f,ssaoRadius=.25f,ssaoDirect=.15f,exposure=.10f,contrast=6,saturation=8,bloomThreshold=1,bloomIntensity=.2f,bloomScatter=.6f,vignette=.16f,vignetteSmoothness=.4f;
            public bool ssaoDownsample=false,ssaoAfterOpaque=false,desktopHDR=true,mainCameraPostProcessing=true,mobileSSAO=false,mobileBloom=false;
            public Vector4 shadows=new Vector4(.97f,1,1.05f,0);
        }
    }
}
