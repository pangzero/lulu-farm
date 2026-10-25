using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using Object = UnityEngine.Object;

namespace LuluFarm.Editor
{
    /// <summary>
    /// O9: the new Lulu (lulu-game-r01 LOD0 WIP, ~29k triangles) in place of locomotion-r08, for movement checks only.
    /// Same 23-joint skeleton, joint order and Idle/Walk/Run clips as locomotion-r08 and the same rig-local space, so the
    /// prefab reuses the registered Lulu prefab's adapter transform: capsule, camera height and gait calibration are
    /// unchanged. The registered Lulu, its prefab and the registry are not modified; ConfigureAndImport is not run.
    /// Known and accepted by the user for now: the front leg can lift the shorts hem while running (deferred 2026-10-24).
    /// </summary>
    public static partial class FarmProjectBuilder
    {
        const string NewLuluPath = "Assets/Farm/Art/Lulu-game-r01/model.glb";
        const string NewLuluPrefab = "Assets/Farm/Prefabs/Lulu-game-r01.prefab";

        [Serializable] sealed class NewLuluRecord
        {
            public string utc, source = NewLuluPath, prefab = NewLuluPrefab, version = "lulu-game-r01-lod0-wip";
            public Vector3 adapterPosition, adapterScale; public Vector3 newBounds, oldBounds;
            public int triangles, skinnedRenderers; public string[] clips;
            public string note = "Movement check only: not user art acceptance; shorts hem gap while running deferred by the user";
        }

        static GameObject OpusNewLuluR12(Transform parent)
        {
            var source = AssetDatabase.LoadAssetAtPath<GameObject>(NewLuluPath);
            if (source == null) throw new InvalidOperationException("New Lulu not staged: run Scripts/opus-r07-stage-new-lulu.py before O9 generate");
            if (source.GetComponentsInChildren<Renderer>(true).SelectMany(r => r.sharedMaterials)
                .Any(m => m == null || m.shader == null || !m.shader.isSupported || m.GetTag("RenderPipeline", true, "") != "UniversalPipeline"))
                throw new InvalidOperationException("New Lulu imported materials are not URP");
            var old = AssetDatabase.LoadAssetAtPath<GameObject>(Base + "Prefabs/Lulu.prefab");
            var oldAdapter = old != null ? old.transform.Find("VisualAdapter") : null;
            if (oldAdapter == null) throw new InvalidOperationException("Registered Lulu prefab (adapter reference) missing");

            var root = new GameObject("Lulu — game-r01 WIP");
            var adapter = new GameObject("VisualAdapter").transform; adapter.SetParent(root.transform, false);
            adapter.localPosition = oldAdapter.localPosition; adapter.localRotation = oldAdapter.localRotation; adapter.localScale = oldAdapter.localScale;
            var visual = (GameObject)PrefabUtility.InstantiatePrefab(source); visual.name = "Visual"; visual.transform.SetParent(adapter, false);
            foreach (var r in root.GetComponentsInChildren<Renderer>(true))
            { foreach (var m in r.sharedMaterials) if (m != null) m.enableInstancing = true; r.receiveShadows = true; r.shadowCastingMode = ShadowCastingMode.On; }
            Directory.CreateDirectory(Base + "Prefabs");
            PrefabUtility.SaveAsPrefabAsset(root, NewLuluPrefab); Object.DestroyImmediate(root);

            var instance = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(NewLuluPrefab));
            instance.transform.SetParent(parent, false); instance.transform.localPosition = Vector3.zero; instance.transform.localRotation = Quaternion.identity;
            var oldInstance = (GameObject)PrefabUtility.InstantiatePrefab(old);
            var record = new NewLuluRecord { utc = DateTime.UtcNow.ToString("o"), adapterPosition = adapter.localPosition, adapterScale = adapter.localScale,
                newBounds = BoundsOf(instance).size, oldBounds = BoundsOf(oldInstance).size,
                skinnedRenderers = instance.GetComponentsInChildren<SkinnedMeshRenderer>(true).Length,
                triangles = instance.GetComponentsInChildren<SkinnedMeshRenderer>(true).Sum(s => s.sharedMesh != null ? s.sharedMesh.triangles.Length / 3 : 0),
                clips = NewLuluClips().Select(c => c.name + (c.legacy ? " (legacy)" : "")).ToArray() };
            Object.DestroyImmediate(oldInstance);
            if (Mathf.Abs(record.newBounds.y - record.oldBounds.y) > .08f * record.oldBounds.y)
                issues.Add("New Lulu height differs from locomotion-r08 by more than 8 %: " + record.newBounds.y + " vs " + record.oldBounds.y);
            string dir = "Evidence/r07/" + R07Task; Directory.CreateDirectory(dir);
            File.WriteAllText(dir + "/new-lulu-r12.json", JsonUtility.ToJson(record, true));
            return instance;
        }
        static AnimationClip[] NewLuluClips() => AssetDatabase.LoadAllAssetsAtPath(NewLuluPath).OfType<AnimationClip>().ToArray();
    }
}
