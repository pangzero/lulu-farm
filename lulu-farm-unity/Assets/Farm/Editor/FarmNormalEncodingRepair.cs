using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

namespace LuluFarm.Editor
{
    public static class FarmNormalEncodingRepair
    {
        [Serializable] public class Change {public string path,before,after; public bool linear;}
        [Serializable] public class Report { public string utc; public string reason="glTFast6.20 Normal.cginc consumes raw RG; preserve source RGB, avoid Unity NormalMap channel swizzle"; public string originalFiles="unmodified"; public string lulu="excluded_user_frozen"; public Change[] changes; }
        public static void Run()
        {
            var changes=new List<Change>();
            foreach(var guid in AssetDatabase.FindAssets("t:Texture2D",new[]{"Assets/Farm/Art"}))
            {
                string path=AssetDatabase.GUIDToAssetPath(guid);
                if(!path.Contains("_normal")||path.Contains("/Lulu/"))continue;
                var importer=(TextureImporter)AssetImporter.GetAtPath(path);
                string before=importer.textureType.ToString();
                importer.textureType=TextureImporterType.Default; importer.sRGBTexture=false;
                importer.SaveAndReimport();
                changes.Add(new Change{path=path,before=before,after=importer.textureType.ToString(),linear=!importer.sRGBTexture});
            }
            Directory.CreateDirectory("Evidence");
            File.WriteAllText("Evidence/gltf-normal-encoding-repair.json",JsonUtility.ToJson(new Report{utc=DateTime.UtcNow.ToString("o"),changes=changes.ToArray()},true));
            ShadowDiagnostic.RunBatch();
        }
    }
}
