using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace LuluFarm.Editor
{
    public static class FarmImportDiagnostics
    {
        [Serializable] sealed class MaterialInfo
        {
            public string asset, material, shader, tag, fallbackTag, shaderPath;
            public bool supported;
        }
        [Serializable] sealed class Report
        {
            public string utc, pipeline, qualityPipeline, currentPipeline, gltfPipeline, generator;
            public MaterialInfo[] materials;
        }
        public static void Run()
        {
            var registry = JsonUtility.FromJson<AssetRegistry>(File.ReadAllText("Assets/Farm/Data/asset-registry.json"));
            var report = new Report
            {
                utc = DateTime.UtcNow.ToString("o"),
                pipeline = GraphicsSettings.defaultRenderPipeline?.name,
                qualityPipeline = QualitySettings.renderPipeline?.name,
                currentPipeline = GraphicsSettings.currentRenderPipeline?.name,
                gltfPipeline = GLTFast.RenderPipelineUtils.RenderPipeline.ToString(),
                generator = GLTFast.Materials.MaterialGenerator.GetDefaultMaterialGenerator().GetType().FullName,
                materials = registry.assets.SelectMany(a => AssetDatabase.LoadAllAssetsAtPath(a.path).OfType<Material>()
                    .Select(m => new MaterialInfo { asset = a.id, material = m.name, shader = m.shader?.name,
                        shaderPath = AssetDatabase.GetAssetPath(m.shader), tag = m.GetTag("RenderPipeline", false, "missing"),
                        fallbackTag = m.GetTag("RenderPipeline", true, "missing"), supported = m.shader != null && m.shader.isSupported })).ToArray()
            };
            Directory.CreateDirectory("Evidence");
            File.WriteAllText("Evidence/import-material-diagnostics.json", JsonUtility.ToJson(report, true));
        }
    }
}
