"""Save separate Meshy import/review .blend projects; never write a GLB.

Run with Blender --background --python tools/save_crop_meshy_import_sources.py.
The imported mesh/material data remains unchanged. Only an extra inspection
root changes the displayed scale and position, matching the crop preview.
"""
from pathlib import Path
import hashlib
import json
import math
import os

import bpy
from mathutils import Matrix, Vector


PROJECT = Path(__file__).resolve().parents[1]
REVIEW = PROJECT / "review/crop-meshy-progress-20261018"
MANIFEST = REVIEW / "import-manifest.json"
VALIDATION = REVIEW / "import-source-validation.json"
SCALE = 0.47
ROOT_NAME = "Meshy_Import_Review_Root"
SCOPE = (
    "用户 Meshy GLB 的独立导入检查工程；不是手工建模源。"
    "原始网格、材质、UV 与贴图保留；仅额外根对象应用共同 0.47 检查缩放、"
    "XY 居中和最低点着地。不包含几何优化，不代表美术或设备性能验收。"
)


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_validation(records):
    data = {
        "scope": SCOPE,
        "common_inspection_scale": SCALE,
        "manifest": str(MANIFEST),
        "completed_count": len(records),
        "expected_count": 11,
        "all_completed": len(records) == 11,
        "models_exported": False,
        "meshes_optimized": False,
        "items": records,
    }
    temp = VALIDATION.with_suffix(".json.tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    os.replace(temp, VALIDATION)


def model_bounds(meshes):
    points = [obj.matrix_world @ Vector(p) for obj in meshes for p in obj.bound_box]
    low = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    high = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    return low, high


def add_inspection_camera_and_lights(low, high):
    scene = bpy.context.scene
    center = (low + high) * 0.5
    distance = max((high - low).length, 0.1)
    direction = Vector((1.35, -4.0, 2.25)).normalized()
    camera_data = bpy.data.cameras.new("Inspection camera only")
    camera = bpy.data.objects.new(camera_data.name, camera_data)
    scene.collection.objects.link(camera)
    camera.location = center + direction * distance * 3
    camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = max(high.z - low.z, high.x - low.x, high.y - low.y) * 1.35
    scene.camera = camera
    for label, relative, energy in [
        ("Review key", (-3, -4, 6), 280),
        ("Review fill", (4, -1, 3), 140),
        ("Review rim", (0, 4, 5), 230),
    ]:
        light_data = bpy.data.lights.new(label, "AREA")
        light = bpy.data.objects.new(label, light_data)
        scene.collection.objects.link(light)
        light.location = center + Vector(relative) * distance
        light.rotation_euler = (center - light.location).to_track_quat("-Z", "Y").to_euler()
        light_data.energy = energy * distance * distance
        light_data.shape = "DISK"
        light_data.size = distance * 3
    scene.world = bpy.data.worlds.new("Neutral inspection world")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.78, 0.80, 0.75, 1)
    scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.32
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.render.resolution_x = scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                space = area.spaces.active
                space.clip_start = 0.001
                space.clip_end = max(100, distance * 100)
                space.region_3d.view_location = center
                space.region_3d.view_distance = distance * 1.7
                space.region_3d.view_rotation = camera.rotation_euler.to_quaternion()
                space.region_3d.view_perspective = "ORTHO"
                space.shading.type = "MATERIAL"


def create_source(item, glb, target):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.import_scene.gltf(filepath=str(glb))
    scene = bpy.context.scene
    imported_objects = list(scene.objects)
    meshes = [obj for obj in imported_objects if obj.type == "MESH"]
    assert meshes, "No imported mesh"
    low, high = model_bounds(meshes)
    root = bpy.data.objects.new(ROOT_NAME, None)
    scene.collection.objects.link(root)
    root.empty_display_type = "PLAIN_AXES"
    for obj in imported_objects:
        if obj.parent is None:
            original_world = obj.matrix_world.copy()
            obj.parent = root
            obj.matrix_parent_inverse = Matrix.Identity(4)
            obj.matrix_world = original_world
    root.scale = (SCALE,) * 3
    root.location = (
        -(low.x + high.x) * 0.5 * SCALE,
        -(low.y + high.y) * 0.5 * SCALE,
        -low.z * SCALE,
    )
    root["scope"] = SCOPE
    root["original_glb_sha256"] = item["sha256"]
    root["original_name"] = item["original_name"]
    root["geometry_edited"] = False
    scene["source_kind"] = "user_meshy_glb_import_for_review"
    scene["original_glb_sha256"] = item["sha256"]
    scene["imported_glb_path"] = str(glb)
    scene["original_download_path"] = item["original_download"]
    scene["catalog_id"] = item["code"]
    scene["scope"] = SCOPE
    bpy.context.view_layer.update()
    normalized_low, normalized_high = model_bounds(meshes)
    add_inspection_camera_and_lights(normalized_low, normalized_high)
    text = bpy.data.texts.new("README - Meshy import review.txt")
    text.write(SCOPE + "\n\n" + json.dumps(item, ensure_ascii=False, indent=2) + "\n")
    bpy.ops.file.pack_all()
    for obj in scene.objects:
        obj.select_set(False)
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    target.parent.mkdir(parents=True, exist_ok=True)
    assert not target.exists(), f"Refuse to overwrite existing source: {target}"
    bpy.ops.wm.save_as_mainfile(filepath=str(target), check_existing=False, compress=True)


def validate_source(item, glb, target, reused):
    # Reopen each saved source rather than relying on in-memory save success.
    bpy.ops.wm.open_mainfile(filepath=str(target))
    scene = bpy.context.scene
    assert scene.get("source_kind") == "user_meshy_glb_import_for_review", "Different source kind"
    assert scene.get("original_glb_sha256") == item["sha256"], "Different existing source"
    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    assert meshes
    root = bpy.data.objects.get(ROOT_NAME)
    assert root is not None
    assert all(math.isclose(v, SCALE, abs_tol=1e-6) for v in root.scale)
    # Packed images are lazily decoded on reopen; has_data can be False even
    # when the packed JPEG and its dimensions are valid. Read one pixel to
    # verify decoding instead of confusing this with a missing texture.
    images = [image for image in bpy.data.images if image.source == "FILE" and image.users > 0]
    packed = [image for image in images if image.packed_file or len(image.packed_files)]
    assert len(images) >= 3 and len(images) == len(packed), "Missing packed texture"
    for image in images:
        assert image.size[0] > 0 and image.size[1] > 0
        assert len(image.pixels) > 0
        assert math.isfinite(image.pixels[0])
    materials = [mat for mat in bpy.data.materials if mat.users > 0]
    assert materials
    low, high = model_bounds(meshes)
    assert abs(low.z) < 1e-5, f"Model not grounded: {low.z}"
    assert abs(low.x + high.x) < 1e-5 and abs(low.y + high.y) < 1e-5, "Model not centered"
    original_hash = sha256(item["original_download"])
    project_hash = sha256(glb)
    assert original_hash == project_hash == item["sha256"], "GLB bytes changed"
    return {
        "id": item["id"], "code": item["code"], "batch": item["batch"],
        "source": str(target), "source_sha256": sha256(target), "source_bytes": target.stat().st_size,
        "source_kind": scene["source_kind"], "reused_existing_matching_source": reused,
        "reopened_successfully": True, "mesh_object_count": len(meshes),
        "vertices": sum(len(obj.data.vertices) for obj in meshes),
        "triangles": sum(sum(len(face.vertices) - 2 for face in obj.data.polygons) for obj in meshes),
        "material_count": len(materials), "image_count": len(images), "packed_image_count": len(packed),
        "images": [{"name": image.name, "size": list(image.size),
                    "packed_bytes": image.packed_file.size, "pixel_decode_verified": True}
                   for image in images],
        "all_images_packed": True, "inspection_root_scale": list(root.scale),
        "inspection_root_location": list(root.location), "bounds_z_up": [list(low), list(high)],
        "xy_centered": True, "grounded": True, "geometry_edited": False,
        "project_glb": str(glb), "project_glb_sha256": project_hash,
        "original_download": item["original_download"], "original_glb_sha256": original_hash,
        "glbs_unchanged": True, "glb_exported": False,
    }


def main():
    imports = json.loads(MANIFEST.read_text())["imports"]
    assert len(imports) == 11
    records = []
    for item in imports:
        glb = PROJECT / item["file"]
        target = PROJECT / item["source"]
        assert glb.resolve().is_relative_to(PROJECT)
        assert target.resolve().is_relative_to(PROJECT)
        assert sha256(glb) == sha256(item["original_download"]) == item["sha256"]
        reused = target.exists()
        if not reused:
            create_source(item, glb, target)
        record = validate_source(item, glb, target, reused)
        records.append(record)
        write_validation(records)
        print("IMPORT SOURCE VALIDATED", item["id"], str(target), flush=True)
    print("ALL ELEVEN IMPORT SOURCES VALIDATED", flush=True)


if __name__ == "__main__":
    main()
