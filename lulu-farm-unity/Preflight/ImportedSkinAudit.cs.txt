// Activate only when Unity is idle: copy to Assets/Farm/Editor/ImportedSkinAudit.cs.
// Menu: Farm/Diagnostics/Audit original Lulu imported skin data.
// Read-only: never calls Mesh setters, SaveAssets, Reimport or changes the open scene.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using GltfRoot = GLTFast.Schema.Root;
using GltfAccessor = GLTFast.Schema.Accessor;

namespace LuluFarm.Editor
{
    public static class ImportedSkinAudit
    {
        const string Source = "Assets/Farm/Art/Comparisons/Lulu/model.gltf";
        const double Epsilon = 0.00001;
        static readonly string[] ExpectedParts = { "Head", "Orange", "Body", "Shorts", "Leg_R", "Leg_L", "Arm_R", "Arm_L" };

        [Serializable] sealed class AttributeLayout
        {
            public string semantic, format;
            public int dimension, stream, offset, stride;
        }
        [Serializable] sealed class Part
        {
            public string sourceMesh, importedMesh, rendererPath;
            public int sourceMeshIndex, primitive, sourceVertices, importedVertices, bones, bindposes;
            public bool vertexOrderMatches, cpuAttributesMatch, documentedSkinStreamLayout;
            public double maxPositionError, maxUV0Error, maxUV1Error, maxColorError, maxWeightError, maxWeightSumError;
            public int checkedVertices, uv1Vertices, mismatchedActiveJointSets, invalidJointIndices, invalidSourceWeightSums;
            public int nonFiniteComponents, invalidWeightValues;
            public string status = "not_checked";
            public AttributeLayout[] layout;
            public string[] errors, layoutIssues;
        }
        [Serializable] sealed class BufferHash { public string path, sha256; }
        [Serializable] sealed class Report
        {
            public string utc, unityVersion, gltfPackageVersion, source, sourceSHA256, status;
            public string scope = "CPU imported vertex data and declared stream layout only; does not certify GPU skinning or visual acceptance";
            public string gpuSkinning = "not_run", visual = "not_viewed", userArt = "pending";
            public string conventions = "glTFast: position.x negated; UV.v = 1 - source.v; colors remain linear; skin weights compared by joint after source normalization (slot reordering allowed)";
            public double tolerance = Epsilon;
            public int expectedParts = 8, checkedParts;
            public bool allCPUDataMatches, allLayoutsMatchDocumentedSkinStreams;
            public Part[] parts;
            public BufferHash[] buffers;
            public string[] errors;
        }

        [MenuItem("Farm/Diagnostics/Audit original Lulu imported skin data")]
        public static void Run()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling || EditorApplication.isUpdating)
                throw new InvalidOperationException("Run the skin-data audit in idle Edit Mode after import and compilation finish.");
            var report = new Report { utc = DateTime.UtcNow.ToString("o"), unityVersion = Application.unityVersion, source = Source };
            var parts = new List<Part>();
            var errors = new List<string>();
            try
            {
                report.sourceSHA256 = Hash(Source);
                var package = UnityEditor.PackageManager.PackageInfo.FindForAssembly(typeof(GltfRoot).Assembly);
                report.gltfPackageVersion = package != null ? package.version : "unknown";
                var text = File.ReadAllText(Source);
                if (text.Contains("\"sparse\"") || text.Contains("KHR_draco_mesh_compression") || text.Contains("EXT_meshopt_compression"))
                    throw new NotSupportedException("This audit deliberately rejects sparse/compressed accessors instead of silently comparing incomplete data.");
                var gltf = JsonUtility.FromJson<GltfRoot>(text);
                var buffers = ReadBuffers(gltf, report);
                var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(Source);
                if (prefab == null) throw new InvalidOperationException("The original Lulu glTF has no imported GameObject asset.");
                var renderers = prefab.GetComponentsInChildren<SkinnedMeshRenderer>(true);
                var seen = new List<string>();
                for (int mi = 0; mi < gltf.meshes.Length; mi++)
                {
                    var sourceMesh = gltf.meshes[mi];
                    for (int pi = 0; pi < sourceMesh.primitives.Length; pi++)
                    {
                        var attr = sourceMesh.primitives[pi].attributes;
                        if (attr.COLOR_0 < 0 || attr.JOINTS_0 < 0 || attr.WEIGHTS_0 < 0) continue;
                        var part = new Part { sourceMesh = sourceMesh.name, sourceMeshIndex = mi, primitive = pi };
                        parts.Add(part);
                        seen.Add(sourceMesh.name);
                        try { CheckPart(gltf, buffers, renderers, mi, pi, part); }
                        catch (Exception ex) { part.status = "failed"; part.errors = new[] { ex.GetType().Name + ": " + ex.Message }; }
                    }
                }
                if (seen.Count != ExpectedParts.Length || ExpectedParts.Any(x => seen.Count(y => y == x) != 1))
                    errors.Add("Expected exactly one colored skinned primitive for each of the eight known original Lulu parts; source structure changed or parsing was incomplete.");
            }
            catch (Exception ex) { errors.Add(ex.GetType().Name + ": " + ex.Message); }
            report.parts = parts.ToArray();
            report.checkedParts = parts.Count;
            report.errors = errors.ToArray();
            report.allCPUDataMatches = errors.Count == 0 && parts.Count == 8 && parts.All(p => p.cpuAttributesMatch);
            report.allLayoutsMatchDocumentedSkinStreams = errors.Count == 0 && parts.Count == 8 && parts.All(p => p.documentedSkinStreamLayout);
            report.status = !report.allCPUDataMatches ? "cpu_data_failed_or_incomplete"
                : !report.allLayoutsMatchDocumentedSkinStreams ? "cpu_data_matches_skin_stream_layout_requires_gpu_validation"
                : "cpu_data_and_declared_layout_match_gpu_visual_unverified";
            var directory = Path.Combine("Evidence", "imported-skin-audit-" + DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fff"));
            Directory.CreateDirectory(directory);
            var path = Path.Combine(directory, "original-lulu-skin-data.json");
            File.WriteAllText(path, JsonUtility.ToJson(report, true));
            Debug.Log("Original Lulu skin audit: " + report.status + "; " + Path.GetFullPath(path));
        }

        static void CheckPart(GltfRoot gltf, byte[][] buffers, SkinnedMeshRenderer[] renderers, int mi, int pi, Part result)
        {
            var sourceMesh = gltf.meshes[mi];
            var a = sourceMesh.primitives[pi].attributes;
            int count = gltf.accessors[a.POSITION].count;
            result.sourceVertices = count;
            var matches = renderers.Where(r => r.sharedMesh != null && r.sharedMesh.vertexCount == count && HasAncestor(r.transform, sourceMesh.name)).ToArray();
            if (matches.Length != 1) throw new InvalidOperationException("Expected exactly one renderer with source node ancestor and primitive vertex count; found " + matches.Length + ". No positional guess was made.");
            var renderer = matches[0];
            var mesh = renderer.sharedMesh;
            result.importedMesh = mesh.name;
            result.rendererPath = HierarchyPath(renderer.transform);
            result.importedVertices = mesh.vertexCount;
            result.bones = renderer.bones.Length;
            result.bindposes = mesh.bindposes.Length;
            result.layout = mesh.GetVertexAttributes().Select(d => new AttributeLayout {
                semantic = d.attribute.ToString(), format = d.format.ToString(), dimension = d.dimension,
                stream = mesh.GetVertexAttributeStream(d.attribute), offset = mesh.GetVertexAttributeOffset(d.attribute),
                stride = mesh.GetVertexBufferStride(mesh.GetVertexAttributeStream(d.attribute))
            }).ToArray();
            var layoutIssues = new List<string>();
            foreach (var d in result.layout)
            {
                int expected = d.semantic == "Position" || d.semantic == "Normal" || d.semantic == "Tangent" ? 0
                    : d.semantic == "BlendWeight" || d.semantic == "BlendIndices" ? 2 : 1;
                if (d.stream != expected) layoutIssues.Add(d.semantic + " expected stream " + expected + ", actual " + d.stream);
            }
            result.layoutIssues = layoutIssues.ToArray();
            result.documentedSkinStreamLayout = layoutIssues.Count == 0;
            if (!mesh.isReadable) throw new InvalidOperationException("Imported mesh is not CPU readable; do not change import settings automatically.");

            var sourceNodes = gltf.nodes.Where(n => n.mesh == mi && n.skin >= 0).ToArray();
            if (sourceNodes.Length != 1) throw new InvalidOperationException("Source mesh-to-skin mapping is ambiguous.");
            var joints = gltf.skins[sourceNodes[0].skin].joints;
            var errors = new List<string>();
            if (joints.Length != result.bones || joints.Length != result.bindposes) errors.Add("Source joint count, imported bones and bindposes differ.");
            for (int j = 0; j < Math.Min(joints.Length, result.bones); j++)
                if (renderer.bones[j] == null || renderer.bones[j].name != gltf.nodes[joints[j]].name)
                    errors.Add("Bone mapping differs at source skin joint " + j);

            var positions = mesh.vertices;
            var colors = mesh.colors;
            var uv0 = new List<Vector2>(); mesh.GetUVs(0, uv0);
            var uv1 = new List<Vector2>(); if (a.TEXCOORD_1 >= 0) mesh.GetUVs(1, uv1);
            var weights = mesh.boneWeights;
            if (positions.Length != count || colors.Length != count || uv0.Count != count || weights.Length != count || (a.TEXCOORD_1 >= 0 && uv1.Count != count))
                throw new InvalidOperationException("Imported attribute lengths do not match the source primitive vertex count.");
            if (sourceMesh.name == "Shorts" && a.TEXCOORD_1 < 0) errors.Add("Shorts FabricUV second coordinates are absent from the source.");
            var pos = new Access(gltf, buffers, a.POSITION);
            var c = new Access(gltf, buffers, a.COLOR_0);
            var u0 = new Access(gltf, buffers, a.TEXCOORD_0);
            var u1 = a.TEXCOORD_1 >= 0 ? new Access(gltf, buffers, a.TEXCOORD_1) : null;
            var ji = new Access(gltf, buffers, a.JOINTS_0);
            var we = new Access(gltf, buffers, a.WEIGHTS_0);
            if (pos.dimension != 3 || u0.dimension != 2 || (u1 != null && u1.dimension != 2) || (c.dimension != 3 && c.dimension != 4) || ji.dimension != 4 || we.dimension != 4)
                throw new InvalidOperationException("Source semantic accessor dimensions are unexpected.");
            if (new[] { pos, c, u0, ji, we }.Any(x => x.count != count) || (u1 != null && u1.count != count))
                throw new InvalidOperationException("Source semantic accessor counts disagree.");
            var expectedWeights = new double[joints.Length];
            var actualWeights = new double[joints.Length];
            var rawWeights = new double[4];
            for (int v = 0; v < count; v++)
            {
                var p = positions[v];
                Error(ref result.maxPositionError, p.x, -pos.Read(v, 0), result);
                Error(ref result.maxPositionError, p.y, pos.Read(v, 1), result);
                Error(ref result.maxPositionError, p.z, pos.Read(v, 2), result);
                CheckUV(uv0[v], u0, v, ref result.maxUV0Error, result);
                if (u1 != null) { CheckUV(uv1[v], u1, v, ref result.maxUV1Error, result); result.uv1Vertices++; }
                for (int k = 0; k < 4; k++) Error(ref result.maxColorError, colors[v][k], k < c.dimension ? c.Read(v, k) : 1, result);
                Array.Clear(expectedWeights, 0, expectedWeights.Length);
                Array.Clear(actualWeights, 0, actualWeights.Length);
                double total = 0;
                for (int k = 0; k < 4; k++)
                {
                    rawWeights[k] = we.Read(v, k); total += rawWeights[k];
                    if (!Finite(rawWeights[k]) || rawWeights[k] < 0) result.invalidWeightValues++;
                }
                if (!Finite(total) || total <= 0) result.invalidSourceWeightSums++;
                for (int k = 0; k < 4; k++)
                {
                    int index = checked((int)ji.Read(v, k));
                    if (index < 0 || index >= joints.Length) result.invalidJointIndices++;
                    else if (total > 0) expectedWeights[index] += rawWeights[k] / total;
                }
                var w = weights[v];
                AddWeight(actualWeights, w.boneIndex0, w.weight0, result);
                AddWeight(actualWeights, w.boneIndex1, w.weight1, result);
                AddWeight(actualWeights, w.boneIndex2, w.weight2, result);
                AddWeight(actualWeights, w.boneIndex3, w.weight3, result);
                bool indexMismatch = false;
                double actualSum = 0;
                for (int j = 0; j < joints.Length; j++)
                {
                    Error(ref result.maxWeightError, actualWeights[j], expectedWeights[j], result);
                    if ((expectedWeights[j] > Epsilon) != (actualWeights[j] > Epsilon)) indexMismatch = true;
                    actualSum += actualWeights[j];
                }
                if (indexMismatch) result.mismatchedActiveJointSets++;
                Error(ref result.maxWeightSumError, actualSum, 1, result);
                result.checkedVertices++;
            }
            result.vertexOrderMatches = result.maxPositionError <= Epsilon && result.nonFiniteComponents == 0;
            if (!result.vertexOrderMatches) errors.Add("Position/order check failed. This audit does not remap reordered vertices; attribute differences do not alone prove data corruption.");
            result.cpuAttributesMatch = errors.Count == 0 && result.vertexOrderMatches && result.maxUV0Error <= Epsilon && result.maxUV1Error <= Epsilon
                && result.maxColorError <= Epsilon && result.maxWeightError <= Epsilon && result.maxWeightSumError <= Epsilon
                && result.mismatchedActiveJointSets == 0 && result.invalidJointIndices == 0 && result.invalidSourceWeightSums == 0 && result.invalidWeightValues == 0;
            result.errors = errors.ToArray();
            result.status = !result.cpuAttributesMatch ? "cpu_data_mismatch" : result.documentedSkinStreamLayout ? "cpu_data_and_layout_match_gpu_unverified" : "cpu_data_matches_layout_mismatch_gpu_unverified";
        }

        static void CheckUV(Vector2 actual, Access source, int v, ref double max, Part report)
        { Error(ref max, actual.x, source.Read(v, 0), report); Error(ref max, actual.y, 1 - source.Read(v, 1), report); }
        static bool Finite(double value) { return !double.IsNaN(value) && !double.IsInfinity(value); }
        static void Error(ref double max, double actual, double expected, Part report)
        { if (!Finite(actual) || !Finite(expected)) report.nonFiniteComponents++; else max = Math.Max(max, Math.Abs(actual - expected)); }
        static void AddWeight(double[] values, int index, double weight, Part report)
        { if (!Finite(weight)) { report.nonFiniteComponents++; return; } if (weight < 0) report.invalidWeightValues++; if (index < 0 || index >= values.Length) report.invalidJointIndices++; else values[index] += weight; }
        static bool HasAncestor(Transform t, string name) { for (; t != null; t = t.parent) if (t.name == name) return true; return false; }
        static string HierarchyPath(Transform t) { return t.parent == null ? t.name : HierarchyPath(t.parent) + "/" + t.name; }
        static string Hash(string path) { using (var sha = SHA256.Create()) using (var stream = File.OpenRead(path)) return BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", "").ToLowerInvariant(); }

        static byte[][] ReadBuffers(GltfRoot gltf, Report report)
        {
            var buffers = new byte[gltf.buffers.Length][];
            var hashes = new List<BufferHash>();
            var directory = Path.GetFullPath(Path.GetDirectoryName(Source));
            for (int i = 0; i < buffers.Length; i++)
            {
                var uri = gltf.buffers[i].uri;
                if (string.IsNullOrEmpty(uri) || uri.Contains(":") || Path.IsPathRooted(uri)) throw new NotSupportedException("Only local external glTF buffers are supported by this audit.");
                var path = Path.GetFullPath(Path.Combine(directory, Uri.UnescapeDataString(uri)));
                if (!path.StartsWith(directory + Path.DirectorySeparatorChar, StringComparison.Ordinal)) throw new InvalidOperationException("Buffer path escapes the source directory.");
                buffers[i] = File.ReadAllBytes(path);
                if (buffers[i].Length != gltf.buffers[i].byteLength) throw new InvalidOperationException("Buffer byte length differs from glTF declaration.");
                hashes.Add(new BufferHash { path = path, sha256 = Hash(path) });
            }
            report.buffers = hashes.ToArray();
            return buffers;
        }

        sealed class Access
        {
            readonly byte[] data;
            readonly int offset, stride, component, size;
            readonly bool normalized;
            public readonly int dimension, count;
            public Access(GltfRoot gltf, byte[][] buffers, int index)
            {
                if (index < 0 || index >= gltf.accessors.Length) throw new InvalidOperationException("Missing or out-of-range accessor.");
                GltfAccessor a = gltf.accessors[index];
                if (a.bufferView < 0 || a.bufferView >= gltf.bufferViews.Length) throw new NotSupportedException("Accessor has no ordinary buffer view.");
                var view = gltf.bufferViews[a.bufferView];
                component = (int)a.componentType;
                size = component == 5120 || component == 5121 ? 1 : component == 5122 || component == 5123 ? 2 : component == 5125 || component == 5126 ? 4 : 0;
                dimension = a.GetAttributeType().ToString() == "VEC2" ? 2 : a.GetAttributeType().ToString() == "VEC3" ? 3 : a.GetAttributeType().ToString() == "VEC4" ? 4 : 0;
                if (size == 0 || dimension == 0) throw new NotSupportedException("Unsupported component or vector accessor type.");
                count = a.count; normalized = a.normalized; stride = view.byteStride > 0 ? view.byteStride : size * dimension;
                data = buffers[view.buffer]; offset = checked(view.byteOffset + a.byteOffset);
                long end = (long)offset + (long)(count - 1) * stride + size * dimension;
                if (count <= 0 || stride < size * dimension || offset < view.byteOffset || end > (long)view.byteOffset + view.byteLength || end > data.Length)
                    throw new InvalidOperationException("Accessor buffer bounds or stride are invalid.");
                if (!BitConverter.IsLittleEndian) throw new NotSupportedException("This glTF audit expects a little-endian host.");
            }
            public double Read(int vertex, int channel)
            {
                int i = checked(offset + vertex * stride + channel * size);
                switch (component)
                {
                    case 5120: return normalized ? Math.Max(-1, unchecked((sbyte)data[i]) / 127.0) : unchecked((sbyte)data[i]);
                    case 5121: return normalized ? data[i] / 255.0 : data[i];
                    case 5122: return normalized ? Math.Max(-1, BitConverter.ToInt16(data, i) / 32767.0) : BitConverter.ToInt16(data, i);
                    case 5123: return normalized ? BitConverter.ToUInt16(data, i) / 65535.0 : BitConverter.ToUInt16(data, i);
                    case 5125: return BitConverter.ToUInt32(data, i);
                    case 5126: return BitConverter.ToSingle(data, i);
                    default: throw new NotSupportedException();
                }
            }
        }
    }
}
