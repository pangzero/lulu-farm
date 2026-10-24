using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering.Universal;
namespace LuluFarm.Editor
{
 public static partial class FarmProjectBuilder
 {
  static UniversalRendererData DesktopContactRenderer(UniversalRendererData mobile)
  {
   const string file="Assets/Farm/Settings/FarmDesktopRenderer.asset";
   var renderer=AssetDatabase.LoadAssetAtPath<UniversalRendererData>(file);
   if(renderer==null){renderer=Object.Instantiate(mobile);renderer.name="FarmDesktopRenderer";AssetDatabase.CreateAsset(renderer,file);}
   var feature=renderer.rendererFeatures.Find(f=>f is ScreenSpaceAmbientOcclusion) as ScreenSpaceAmbientOcclusion;
   if(feature==null){feature=ScriptableObject.CreateInstance<ScreenSpaceAmbientOcclusion>();feature.name="Soft contact shadows";AssetDatabase.AddObjectToAsset(feature,renderer);renderer.rendererFeatures.Add(feature);}
   var so=new SerializedObject(feature);var settings=so.FindProperty("m_Settings");
   settings.FindPropertyRelative("Intensity").floatValue=.45f;
   settings.FindPropertyRelative("Radius").floatValue=.16f;
   settings.FindPropertyRelative("DirectLightingStrength").floatValue=.12f;
   settings.FindPropertyRelative("Falloff").floatValue=25;
   settings.FindPropertyRelative("Downsample").boolValue=true;
   // Reconstruct normals from depth to include the imported glTF shaders consistently.
   settings.FindPropertyRelative("Source").enumValueIndex=0;
   settings.FindPropertyRelative("NormalSamples").enumValueIndex=1;
   settings.FindPropertyRelative("Samples").enumValueIndex=1;
   settings.FindPropertyRelative("BlurQuality").enumValueIndex=0;
   settings.FindPropertyRelative("AfterOpaque").boolValue=true;
   so.ApplyModifiedPropertiesWithoutUndo();feature.SetActive(true);feature.Create();
   EditorUtility.SetDirty(feature);EditorUtility.SetDirty(renderer);
   return renderer;
  }
 }
}
