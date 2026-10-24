using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace LuluFarm.Editor
{
    /// <summary>Opt-in setup for selected house/tree instances; source/imported materials are retained.</summary>
    public static class FarmOcclusionSetup
    {
        const string Folder = "Assets/Farm/Materials/OcclusionFade";
        const string CrownName = "CameraOnlyCrown";
        static readonly string[] ColorProperties = { "_BaseColorFactor", "baseColorFactor", "_BaseColor", "baseColor", "_Color" };
        static readonly string[] TextureProperties = { "_BaseColorTexture", "baseColorTexture", "_BaseMap", "_MainTex", "_BaseColorMap" };

        public static FarmCameraOccluder Configure(GameObject root, bool tree)
        {
            if (root == null) throw new ArgumentNullException(nameof(root));
            if (Application.isPlaying) throw new InvalidOperationException("Configure occlusion in the Editor before entering play mode.");
            var shader = Shader.Find("Universal Render Pipeline/Lit");
            if (shader == null) throw new InvalidOperationException("URP Lit is unavailable; configure URP before creating occlusion variants.");
            Directory.CreateDirectory(Folder);
            AssetDatabase.Refresh();
            var renderers = root.GetComponentsInChildren<Renderer>(true).Where(r => r is MeshRenderer || r is SkinnedMeshRenderer).ToArray();
            if (renderers.Length == 0) throw new InvalidOperationException("Occlusion target has no mesh renderers: " + root.name);
            var old = root.GetComponent<FarmCameraOccluder>();
            var bindings = new List<FarmOcclusionBinding>();
            foreach (var renderer in renderers)
            {
                // Reconfiguration uses preserved opaque originals, never yesterday's faded array.
                var existing = old != null && old.bindings != null ? old.bindings.FirstOrDefault(b => b.renderer == renderer) : null;
                var originals = existing != null ? existing.opaqueMaterials : renderer.sharedMaterials;
                if (originals == null || originals.Length == 0 || originals.Any(m => m == null))
                    throw new InvalidOperationException("Missing original material on " + renderer.name);
                bindings.Add(new FarmOcclusionBinding { renderer = renderer, opaqueMaterials = originals,
                    fadedMaterials = originals.Select(m => MakeFade(m, shader)).ToArray() });
            }
            var component = old != null ? old : root.AddComponent<FarmCameraOccluder>();
            component.bindings = bindings.ToArray();
            component.targetRenderer = bindings[0].renderer;
            component.opaqueMaterials = bindings[0].opaqueMaterials;
            component.fadedMaterials = bindings[0].fadedMaterials;
            component.fadedOpacity = .07f;
            component.transitionSeconds = .12f;
            if (tree)
            {
                Transform crownTransform = root.transform.Find(CrownName);
                if (crownTransform == null)
                { crownTransform = new GameObject(CrownName).transform; crownTransform.SetParent(root.transform, false); }
                crownTransform.localPosition = Vector3.zero; crownTransform.localRotation = Quaternion.identity; crownTransform.localScale = Vector3.one;
                crownTransform.gameObject.layer = 28;
                var crown = crownTransform.GetComponent<SphereCollider>();
                if (crown == null) crown = crownTransform.gameObject.AddComponent<SphereCollider>();
                Bounds local = LocalBounds(root.transform, renderers);
                crown.center = new Vector3(local.center.x, local.min.y + local.size.y * .68f, local.center.z);
                crown.radius = Mathf.Max(.2f, Mathf.Max(local.extents.x, local.extents.z) * .96f);
                crown.isTrigger = false;
                // Tree trunks remain physical blockers and are not ignored with their canopy proxy.
                component.occlusionColliders = new Collider[] { crown };
            }
            else
            {
                component.occlusionColliders = root.GetComponentsInChildren<Collider>(true)
                    .Where(c => !c.isTrigger && c.GetComponentInParent<FarmCameraOccluder>() == component).ToArray();
                if (component.occlusionColliders.Length == 0)
                    Debug.LogWarning("Occlusion configured without a collider. Call Footprint before Configure for " + root.name);
            }
            EditorUtility.SetDirty(component);
            AssetDatabase.SaveAssets();
            return component;
        }

        static Material MakeFade(Material source, Shader shader)
        {
            string guid; long localId;
            if (!AssetDatabase.TryGetGUIDAndLocalFileIdentifier(source, out guid, out localId) || string.IsNullOrEmpty(guid))
                throw new InvalidOperationException("Save the original material before creating a traceable fade variant: " + source.name);
            string location = Folder + "/" + guid + "-" + localId + ".mat";
            Material fade = AssetDatabase.LoadAssetAtPath<Material>(location);
            // O6/O7: these transparent fades are superseded by the dither fades (FarmOcclusionDitherR08) and the files are
            // protected D5–D6 outputs. Rewriting them here changed _SrcBlend/premultiply versus the stored, URP-validated
            // bytes (O6 attempt-02). Reuse an existing file read-only; only a missing one is created.
            if (fade != null && FarmProjectBuilder.R07Opus) return fade;
            if (fade == null)
            { fade = new Material(shader) { name = source.name + " — camera fade" }; AssetDatabase.CreateAsset(fade, location); }
            else fade.shader = shader;
            string colorProperty = ColorProperties.FirstOrDefault(source.HasProperty);
            Color color = colorProperty != null ? source.GetColor(colorProperty) : Color.white;
            string textureProperty = TextureProperties.FirstOrDefault(p => source.HasProperty(p) && source.GetTexture(p) != null);
            if (textureProperty == null)
                textureProperty = source.GetTexturePropertyNames().FirstOrDefault(p =>
                    (p.IndexOf("basecolor", StringComparison.OrdinalIgnoreCase) >= 0 || p.IndexOf("albedo", StringComparison.OrdinalIgnoreCase) >= 0)
                    && source.GetTexture(p) != null);
            if (textureProperty == null && colorProperty == null)
                Debug.LogWarning("Fade could not identify a base-color property; review this conversion explicitly: " + source.name + " / " + source.shader.name);
            color.a = .07f;
            fade.SetColor("_BaseColor", color);
            fade.SetTexture("_BaseMap", textureProperty != null ? source.GetTexture(textureProperty) : null);
            fade.SetTextureScale("_BaseMap", textureProperty != null ? source.GetTextureScale(textureProperty) : Vector2.one);
            fade.SetTextureOffset("_BaseMap", textureProperty != null ? source.GetTextureOffset(textureProperty) : Vector2.zero);
            fade.SetFloat("_Metallic", 0); fade.SetFloat("_Smoothness", .08f);
            fade.SetFloat("_Surface", 1); fade.SetFloat("_Blend", 0); fade.SetFloat("_AlphaClip", 0);
            fade.SetFloat("_SrcBlend", (float)BlendMode.SrcAlpha); fade.SetFloat("_DstBlend", (float)BlendMode.OneMinusSrcAlpha);
            fade.SetFloat("_SrcBlendAlpha", (float)BlendMode.One); fade.SetFloat("_DstBlendAlpha", (float)BlendMode.OneMinusSrcAlpha);
            bool twoSided = source.doubleSidedGI || (source.HasProperty("_Cull") && Mathf.Approximately(source.GetFloat("_Cull"), 0)) ||
                (source.HasProperty("_CullMode") && Mathf.Approximately(source.GetFloat("_CullMode"), 0));
            fade.SetFloat("_ZWrite", 0); fade.SetFloat("_Cull", (float)(twoSided ? CullMode.Off : CullMode.Back));
            fade.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            fade.DisableKeyword("_ALPHAPREMULTIPLY_ON"); fade.DisableKeyword("_ALPHATEST_ON"); fade.DisableKeyword("_ALPHAMODULATE_ON");
            fade.SetOverrideTag("RenderType", "Transparent"); fade.renderQueue = (int)RenderQueue.Transparent;
            fade.SetShaderPassEnabled("ShadowCaster", false);
            fade.SetShaderPassEnabled("DepthOnly", false);
            fade.SetShaderPassEnabled("DepthNormals", false);
            fade.enableInstancing = true;
            EditorUtility.SetDirty(fade);
            return fade;
        }

        static Bounds LocalBounds(Transform root, Renderer[] renderers)
        {
            Bounds bounds = default; bool first = true;
            foreach (var renderer in renderers)
            {
                var local = renderer.localBounds;
                for (int i = 0; i < 8; i++)
                {
                    var corner = new Vector3((i & 1) == 0 ? local.min.x : local.max.x,
                        (i & 2) == 0 ? local.min.y : local.max.y, (i & 4) == 0 ? local.min.z : local.max.z);
                    Vector3 point = root.InverseTransformPoint(renderer.transform.TransformPoint(corner));
                    if (first) { bounds = new Bounds(point, Vector3.zero); first = false; } else bounds.Encapsulate(point);
                }
            }
            return bounds;
        }
    }
}
