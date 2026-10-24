#!/usr/bin/env python3
"""Register the user's facility/environment downloads without changing GLB bytes.

This is a file/resource inventory, not a modeling, optimization or art-acceptance
pipeline. Existing targets with different content are never replaced.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
import itertools
import json
from pathlib import Path
import re
import shutil
import struct

from PIL import Image


PROJECT = Path(__file__).resolve().parents[1]
REVIEW = PROJECT / "review/facilities-meshy-import-20261018"
DEST = PROJECT / "public/models/facilities-meshy/meshy-r01"
REFERENCE = PROJECT.parent / "art-concepts/remaining-assets-original-crops-20261018/manifest.json"

# Names are explicit, so older B03/B14 exports and crop/animal downloads cannot be
# accidentally promoted by their modification times.
SOURCES = {
    "S01": ("Farm_House", "central-house"),
    "S02": ("Pasture_Shelter", "pasture-shelter"),
    "S03": ("Vegetable_Stand", "produce-stall"),
    "S04": ("Fish_Stall", "fish-stall"),
    "S06": ("Wooden_Fence_Gate", "pasture-gate"),
    "S07": ("Wooden_Pier", "dock"),
    "S08": ("Small_Wooden_Boat", "rowboat"),
    "S09": ("Animal_Feeder_Trough", "feed-trough"),
    "S10": ("Farm_Street_Lantern", "lantern-post"),
    "S11": ("Vegetable_Crates", "wooden-crates"),
    "S12": ("Blue_Watering_Can", "watering-can"),
    "E03": ("Lawn_Base", "grass-tile"),
    "E04": ("Farm_Ground_Base", "path-tile-provisional"),
    "E06": ("Riverbank_Base", "shore-corner"),
    "E08": ("Cartoon_Tree", "round-tree"),
    "E09": ("Pear_Tree", "pear-tree"),
    "E10": ("Green_Bush", "shrub"),
    "E11": ("Daisy_Flower_Bush", "white-flowers"),
    "E12": ("Bulrush_Cattail_Plant", "reeds"),
    "E14": ("Water_Lily_Pad", "water-lily"),
    "E15": ("Straw_Hay_Bale", "hay-bale"),
    "E16": ("Blue_Cartoon_Fish", "blue-fish"),
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def multiply(a, b):
    return [sum(a[k * 4 + r] * b[c * 4 + k] for k in range(4))
            for c in range(4) for r in range(4)]


IDENTITY = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]


def local_matrix(node):
    if "matrix" in node:
        return node["matrix"]
    x, y, z, w = node.get("rotation", [0, 0, 0, 1])
    sx, sy, sz = node.get("scale", [1, 1, 1])
    tx, ty, tz = node.get("translation", [0, 0, 0])
    return [
        (1-2*y*y-2*z*z)*sx, (2*x*y+2*z*w)*sx, (2*x*z-2*y*w)*sx, 0,
        (2*x*y-2*z*w)*sy, (1-2*x*x-2*z*z)*sy, (2*y*z+2*x*w)*sy, 0,
        (2*x*z+2*y*w)*sz, (2*y*z-2*x*w)*sz, (1-2*x*x-2*y*y)*sz, 0,
        tx, ty, tz, 1,
    ]


def transform(matrix, point):
    return [sum(matrix[c * 4 + r] * point[c] for c in range(3)) + matrix[12+r]
            for r in range(3)]


def inspect_glb(path: Path) -> dict:
    raw = path.read_bytes()
    magic, version, length = struct.unpack_from("<4sII", raw, 0)
    if magic != b"glTF" or version != 2 or length != len(raw):
        raise ValueError(f"Invalid GLB header: {path}")
    chunks = []
    cursor = 12
    while cursor < len(raw):
        size, kind = struct.unpack_from("<II", raw, cursor)
        start = cursor + 8
        if start + size > len(raw):
            raise ValueError(f"Chunk extends beyond file: {path}")
        chunks.append((kind, raw[start:start+size]))
        cursor = start + size
    js = json.loads(next(data for kind, data in chunks if kind == 0x4E4F534A))
    binary = next((data for kind, data in chunks if kind == 0x004E4942), b"")
    uris = [item["uri"] for key in ("buffers", "images") for item in js.get(key, [])
            if "uri" in item and not item["uri"].startswith("data:")]
    warnings = []
    for view in js.get("bufferViews", []):
        if view.get("buffer", 0) != 0 or view.get("byteOffset", 0) + view["byteLength"] > len(binary):
            raise ValueError(f"Buffer view invalid or external: {path}")
    triangles = 0
    primitives = 0
    vertices = 0
    mesh_triangles = []
    mesh_bounds = []
    accessors = js.get("accessors", [])
    for mesh in js.get("meshes", []):
        bounds = []
        mesh_tri = 0
        for primitive in mesh["primitives"]:
            primitives += 1
            position = accessors[primitive["attributes"]["POSITION"]]
            vertices += position["count"]
            if "min" not in position or "max" not in position:
                raise ValueError(f"POSITION accessor lacks bounds: {path}")
            bounds.extend(itertools.product(*zip(position["min"], position["max"])))
            count = accessors[primitive["indices"]]["count"] if "indices" in primitive else position["count"]
            mode = primitive.get("mode", 4)
            if mode == 4:
                if count % 3:
                    warnings.append("Triangle primitive index count is not a multiple of three")
                mesh_tri += count // 3
            elif mode in (5, 6):
                mesh_tri += max(0, count - 2)
            else:
                warnings.append(f"Non-triangle primitive mode {mode}")
        triangles += mesh_tri
        mesh_triangles.append(mesh_tri)
        mesh_bounds.append(bounds)
    world_points = []
    instanced_triangles = 0
    node_transforms = []

    def visit(index, parent, ancestry):
        nonlocal instanced_triangles
        if index in ancestry:
            raise ValueError(f"Cyclic node hierarchy: {path}")
        node = js["nodes"][index]
        matrix = multiply(parent, local_matrix(node))
        if "mesh" in node:
            mesh = node["mesh"]
            instanced_triangles += mesh_triangles[mesh]
            world_points.extend(transform(matrix, point) for point in mesh_bounds[mesh])
            node_transforms.append({"node": index, "mesh": mesh, "world_matrix": matrix})
        for child in node.get("children", []):
            visit(child, matrix, ancestry | {index})

    if js.get("scenes"):
        scene_index = js.get("scene", 0)
        for index in js["scenes"][scene_index].get("nodes", []):
            visit(index, IDENTITY, set())
    else:
        children = {i for n in js.get("nodes", []) for i in n.get("children", [])}
        for index in range(len(js.get("nodes", []))):
            if index not in children:
                visit(index, IDENTITY, set())
    bbox = None
    if world_points:
        lo = [min(p[axis] for p in world_points) for axis in range(3)]
        hi = [max(p[axis] for p in world_points) for axis in range(3)]
        bbox = {"min": lo, "max": hi,
                "size": [hi[i] - lo[i] for i in range(3)],
                "center": [(hi[i] + lo[i]) / 2 for i in range(3)],
                "coordinates": "glTF scene world coordinates; Y-up; original units",
                "method": "POSITION accessor min/max transformed by default-scene node matrices; conservative for rotated meshes"}
    images = []
    texture_roles = {}
    for mat in js.get("materials", []):
        pbr = mat.get("pbrMetallicRoughness", {})
        for role, info in [("baseColor", pbr.get("baseColorTexture")),
                           ("metallicRoughness", pbr.get("metallicRoughnessTexture")),
                           ("normal", mat.get("normalTexture")),
                           ("occlusion", mat.get("occlusionTexture")),
                           ("emissive", mat.get("emissiveTexture"))]:
            if info:
                texture = js["textures"][info["index"]]
                texture_roles.setdefault(texture.get("source"), set()).add(role)
    for index, item in enumerate(js.get("images", [])):
        result = {"index": index, "mime_type": item.get("mimeType"),
                  "roles": sorted(texture_roles.get(index, set())),
                  "embedded": "bufferView" in item}
        if "bufferView" in item:
            view = js["bufferViews"][item["bufferView"]]
            start = view.get("byteOffset", 0)
            image_bytes = binary[start:start + view["byteLength"]]
            with Image.open(io.BytesIO(image_bytes)) as image:
                image.load()
                result.update({"width": image.width, "height": image.height,
                               "mode": image.mode, "format": image.format,
                               "bytes": len(image_bytes), "decoded": True,
                               "sha256": hashlib.sha256(image_bytes).hexdigest()})
        else:
            result.update({"uri": item.get("uri"), "decoded": False})
        images.append(result)
    return {
        "triangles": triangles, "scene_triangles": instanced_triangles,
        "vertices": vertices, "meshes": len(js.get("meshes", [])),
        "primitives": primitives, "materials": len(js.get("materials", [])),
        "textures": len(js.get("textures", [])), "images": images,
        "image_count": len(images), "bbox": bbox, "node_transforms": node_transforms,
        "animations": len(js.get("animations", [])), "skins": len(js.get("skins", [])),
        "external_uris": uris, "extensions_used": js.get("extensionsUsed", []),
        "generator": js.get("asset", {}).get("generator"),
        "parse_check": "pass", "warnings": warnings,
        "technical_scope": "GLB header/chunk/buffer bounds, declared resource statistics, default-scene accessor bounds, and full embedded-image decoding only; no topology, scale alignment or visual acceptance claimed",
    }


def matches(name, stem):
    original = re.fullmatch(r"Meshy_AI_" + re.escape(stem) + r"_\d+_image-to-3d-texture(?: \(\d+\))?\.glb", name)
    renamed = re.fullmatch(re.escape(stem.replace("_", " ")) + r"(?: \(\d+\))?\.glb", name)
    return bool(original or renamed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--downloads", type=Path, default=Path.home() / "Downloads")
    args = parser.parse_args()
    previous_path = PROJECT / "public/models/facilities-meshy/manifest.json"
    previous = json.loads(previous_path.read_text()) if previous_path.exists() else {}
    refs = {a["id"]: a for a in json.loads(REFERENCE.read_text())["assets"]}
    files = sorted(args.downloads.glob("*.glb"))
    relevant = [p for p in files if any(matches(p.name, stem) for stem, _ in SOURCES.values())]
    hashes = {p: digest(p) for p in relevant}
    grouped = {}
    for path, sha in hashes.items():
        grouped.setdefault(sha, []).append(path)
    assets, missing = [], []
    DEST.mkdir(parents=True, exist_ok=True)
    REVIEW.mkdir(parents=True, exist_ok=True)
    for identifier, (stem, slug) in SOURCES.items():
        candidates = [p for p in relevant if matches(p.name, stem)]
        if not candidates:
            missing.append({"id": identifier, "name": refs[identifier]["name"],
                            "batch": refs[identifier]["batch"],
                            "status": "not_found_in_downloads", "expected_source_stem": stem,
                            "reference": str(REFERENCE.parent / refs[identifier]["file"])})
            continue
        unique = {hashes[p] for p in candidates}
        if len(unique) != 1:
            raise RuntimeError(f"Different contents found for {identifier}; choose an explicit revision before import: {candidates}")
        sha = next(iter(unique))
        aliases = sorted(grouped[sha])
        # The original un-suffixed Meshy name is canonical; renamed/download
        # copies still appear in full in provenance.
        source = sorted(candidates, key=lambda p: (not p.name.startswith("Meshy_AI_"), " (" in p.name, p.name))[0]
        target = DEST / f"{identifier.lower()}-{slug}.glb"
        if target.exists():
            if digest(target) != sha:
                raise RuntimeError(f"Refusing to overwrite different content: {target}")
        else:
            shutil.copy2(source, target)
        if digest(target) != sha:
            raise RuntimeError(f"Copy failed checksum: {target}")
        metrics = inspect_glb(target)
        mapping_confidence = "filename_and_reference_id"
        mapping_note = "Mapped from explicit user-download subject name; actual art and shape acceptance pending."
        if identifier == "E04":
            mapping_confidence = "provisional_pending_geometry_visual_check"
            mapping_note = "Farm Ground Base is provisionally assigned to E04, not counted as accepted path geometry. Its embedded base color was actually viewed and is entirely ochre/tan, consistent with the path concept palette, but a UV atlas cannot establish tile outline, posts, road function or seamlessness. Confirm in the actual GLB preview."
        if identifier == "E06":
            mapping_note = "Riverbank Base provisionally fills the E06 reference slot; confirm it is an elbow/corner rather than another straight bank, and validate compatibility with existing B03 before use."
            mapping_confidence = "provisional_pending_geometry_visual_check"
        ref = refs[identifier]
        asset = {
            "id": identifier, "name": ref["name"], "batch": ref["batch"],
            "version": "meshy-r01", "kind": "user_meshy_original",
            "file": "/" + str(target.relative_to(PROJECT / "public")),
            "source_name": source.name, "source_path": str(source),
            "source_aliases": [{"name": p.name, "path": str(p), "bytes": p.stat().st_size,
                                "sha256": hashes[p]} for p in aliases],
            "sha256": sha, "bytes": target.stat().st_size,
            "reference": str(REFERENCE.parent / ref["file"]),
            "reference_file": ref["file"],
            "reference_path": str(REFERENCE.parent / ref["file"]),
            "mapping_confidence": mapping_confidence, "mapping_note": mapping_note,
            "status": "imported_original_pending_review",
            "states": {"inventory": "registered", "source_preservation": "sha256_identical",
                       "resource_parse": "passed", "visual_review": "pending",
                       "user_art": "pending", "optimization": "not_done", "device_test": "not_tested"},
            **metrics,
        }
        assets.append(asset)
    total_bytes = sum(a["bytes"] for a in assets)
    total_triangles = sum(a["triangles"] for a in assets)
    max_dimension = max((max(i.get("width", 0), i.get("height", 0)) for a in assets for i in a["images"]), default=0)
    summary = {
        "expected_reference_count": len(SOURCES), "imported_unique_count": len(assets),
        "matched_download_filename_count": len(relevant),
        "duplicate_download_filename_count": len(relevant) - len(assets),
        "missing_count": len(missing), "total_bytes": total_bytes,
        "total_mb_decimal": round(total_bytes / 1e6, 3), "total_triangles": total_triangles,
        "total_meshes": sum(a["meshes"] for a in assets),
        "total_materials": sum(a["materials"] for a in assets),
        "total_images": sum(a["image_count"] for a in assets),
        "max_texture_dimension": max_dimension,
        "decoded_texture_rgba8_bytes_without_mipmaps_estimate": sum(i.get("width", 0) * i.get("height", 0) * 4 for a in assets for i in a["images"]),
        "texture_memory_estimate_note": "RGBA8 upload estimate only, excludes mipmaps, renderer copies, framebuffers and meshes; not measured device memory",
        "largest_file": max(assets, key=lambda a: a["bytes"])["id"] if assets else None,
        "largest_geometry": max(assets, key=lambda a: a["triangles"])["id"] if assets else None,
        "imported_originals_only": True,
    }
    timestamp = datetime.now(timezone.utc).isoformat()
    result = {"schema_version": 1, "date": "2026-10-18", "updated_at": timestamp,
              "title": "设施与环境 Meshy 原始模型盘点",
              "scope": "User-provided source registration and resource inventory only. No models modified or optimized; no B15-B22 completion or user art acceptance.",
              "reference_manifest": str(REFERENCE), "assets": assets, "missing": missing,
              "existing_reused": ["S05 accepted B02 r04 fence/endcap", "E01 B03 r03 empty tile", "E05 B03 r03 straight shore", "E07 B03 r03 water", "E13 B03 r03 stones"],
              "summary": summary}
    # Preserve explicit user decisions instead of resetting deferred inputs to missing.
    if previous.get("user_decisions"):
        result["user_decisions"] = previous["user_decisions"]
    deferred = {m["id"]: m for m in previous.get("missing", []) if m.get("status") == "user_deferred"}
    for item in result["missing"]:
        if item["id"] in deferred:
            item["status"] = "user_deferred"
            item["note"] = deferred[item["id"]].get("note", "User deferred")
    summary["deferred_count"] = sum(m.get("status") == "user_deferred" for m in result["missing"])
    summary["active_missing_count"] = len(result["missing"]) - summary["deferred_count"]
    summary["active_scope_ready"] = summary["active_missing_count"] == 0
    write_json(PROJECT / "public/models/facilities-meshy/manifest.json", result)
    write_json(REVIEW / "inventory.json", result)
    write_json(REVIEW / "metrics.json", {
        "timestamp": timestamp, "summary": summary,
        "assets": [{k: a[k] for k in ("id", "name", "bytes", "triangles", "scene_triangles", "vertices", "meshes", "primitives", "materials", "textures", "images", "bbox", "node_transforms", "external_uris", "animations", "skins", "warnings", "technical_scope")} for a in assets],
    })
    write_json(REVIEW / "parse-validation.json", {
        "timestamp": timestamp, "files": len(assets),
        "glb_structural_parse": "pass", "embedded_image_full_decodes": sum(a["image_count"] for a in assets),
        "external_uris": sum(len(a["external_uris"]) for a in assets),
        "warning_count": sum(len(a["warnings"]) for a in assets),
        "not_tested": ["topology", "thickness", "collision", "visual art", "world scale compatibility", "tile interfaces", "device performance"],
    })
    preservation = {"timestamp": timestamp, "checked_files": len(relevant),
                    "passed": True, "copied_files": len(assets),
                    "source_before_after": [], "target_matches_source": []}
    for path in relevant:
        after = digest(path)
        if after != hashes[path]:
            raise RuntimeError(f"Source changed during inventory: {path}")
        preservation["source_before_after"].append({"source": str(path), "before": hashes[path], "after": after, "unchanged": True})
    for asset in assets:
        preservation["target_matches_source"].append({"id": asset["id"], "target": asset["file"],
                                                      "sha256": asset["sha256"], "matches": True})
    write_json(REVIEW / "preservation-check.json", preservation)
    write_json(REVIEW / "provenance.json", {
        "timestamp": timestamp, "source": "User-generated Meshy downloads",
        "method": "SHA256 de-duplicate; shutil.copy2; source-after and target SHA256 verify; originals untouched",
        "assets": [{k: a[k] for k in ("id", "name", "batch", "file", "source_name", "source_path", "source_aliases", "sha256", "bytes", "mapping_confidence", "mapping_note")} for a in assets],
    })
    rows = ["| 编号 | 资产 | 三角面 | 文件 MB | 纹理 | 状态 |", "|---|---|---:|---:|---|---|"]
    for a in assets:
        dims = ", ".join(f"{im.get('width','?')}×{im.get('height','?')}" for im in a["images"])
        note = "原始入库，待视觉检查" if a["mapping_confidence"] == "filename_and_reference_id" else "映射待确认"
        rows.append(f"| {a['id']} | {a['name']} | {a['triangles']:,} | {a['bytes']/1e6:.2f} | {dims} | {note} |")
    doc = f"""# 设施与环境 Meshy 入库盘点（2026-10-18）

用户最新下载共 {len(relevant)} 个匹配文件名，按内容去重后 {len(assets)} 份原始 GLB，共 {total_bytes/1e6:.2f} MB、{total_triangles:,} 三角面。仅字节不变复制入库，没有修改、卡通化或优化模型，也没有将 B15–B22 标为完成。

缺项：{'; '.join(m['id']+' '+m['name'] for m in missing) or '无'}。现有 B02 围栏以及 B03 空田格、直岸、水面、石头沿用历史资产，未将本次下载目录里的网页验收导出再次计为新增。

{chr(10).join(rows)}

E04 Farm Ground Base 与 E06 Riverbank Base 的编号映射目前保守保留待实际几何确认；前者已实际查看原始嵌入颜色贴图，为赭黄色，但 UV 图本身不能确认道路形状和拼接。所有其他编号也仅代表来源主题匹配，不构成美术认可。

检查完成：GLB 头、块长度、bufferView 范围、材质/网格/三角面统计、默认场景节点变换与 accessor 包围盒、嵌入图片完整解码、原件及副本 SHA256。包围盒采用 glTF Y-up 原始单位，未做逐件归一化；旋转节点下 accessor AABB 变换可能是保守范围。尚未完成：拓扑、厚度、碰撞、统一世界尺度、拼接、完整固定视图、卡通化、资源优化和目标设备测试。

独立原件在 `public/models/facilities-meshy/meshy-r01/`；manifest 在同级 `manifest.json`。`inventory.json` 保存完整清单；`metrics.json` 保存资源统计；`parse-validation.json` 保存结构与图片解码检查范围；`provenance.json` 保存原名、所有同哈希别名和来源路径；`preservation-check.json` 记录原件前后及副本哈希。
"""
    (REVIEW / "README.md").write_text(doc)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("MISSING:", ", ".join(m["id"] + " " + m["name"] for m in missing))


if __name__ == "__main__":
    main()
