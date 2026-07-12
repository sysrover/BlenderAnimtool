import math

import bpy
from mathutils import Vector


COLLECTION_NAME = "Codex_P220_Visual"


def get_collection(name):
    existing = bpy.data.collections.get(name)
    if existing:
        for obj in list(existing.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        return existing
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def link_to_collection(obj, collection):
    for coll in list(obj.users_collection):
        coll.objects.unlink(obj)
    collection.objects.link(obj)


def make_mat(name, color, roughness=0.55, metallic=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def bevel_object(obj, amount=0.04, segments=3):
    bevel = obj.modifiers.new("soft bevel", "BEVEL")
    bevel.width = amount
    bevel.segments = segments
    bevel.affect = "EDGES"
    obj.modifiers.new("weighted normals", "WEIGHTED_NORMAL")
    return obj


def cube_obj(name, loc, scale, mat, collection, bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    link_to_collection(obj, collection)
    if bevel:
        bevel_object(obj, bevel, 3)
    return obj


def cube_rot_obj(name, loc, scale, rot_xyz, mat, collection, bevel=0.02):
    obj = cube_obj(name, loc, scale, mat, collection, bevel)
    obj.rotation_euler = rot_xyz
    return obj


def cyl_obj(name, loc, radius, depth, mat, collection, axis="X", vertices=48, bevel=True):
    rotation = (0.0, math.radians(90), 0.0) if axis == "X" else (0.0, 0.0, 0.0)
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    link_to_collection(obj, collection)
    if bevel:
        bevel_object(obj, 0.01, 2)
    return obj


def prism_from_xz(name, points, thickness, mat, collection, bevel=0.025):
    verts = []
    for x, z in points:
        verts.append((x, -thickness / 2.0, z))
    for x, z in points:
        verts.append((x, thickness / 2.0, z))

    n = len(points)
    faces = []
    for i in range(1, n - 1):
        faces.append((0, i, i + 1))
        faces.append((n, n + i + 1, n + i))
    for i in range(n):
        faces.append((i, (i + 1) % n, ((i + 1) % n) + n, i + n))

    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(mat)
    collection.objects.link(obj)
    if bevel:
        bevel_object(obj, bevel, 3)
    return obj


def curve_line(name, points, mat, collection, bevel_depth=0.015):
    curve = bpy.data.curves.new(name + "Curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = bevel_depth
    curve.bevel_resolution = 2
    poly = curve.splines.new("POLY")
    poly.points.add(len(points) - 1)
    for p, co in zip(poly.points, points):
        p.co = (co[0], co[1], co[2], 1.0)
    obj = bpy.data.objects.new(name, curve)
    obj.data.materials.append(mat)
    collection.objects.link(obj)
    return obj


def add_label(text, name, loc, size, mat, collection):
    bpy.ops.object.text_add(location=loc, rotation=(math.radians(90), 0.0, 0.0))
    obj = bpy.context.object
    obj.name = name
    obj.data.body = text
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    obj.data.size = size
    obj.data.extrude = 0.004
    obj.data.materials.append(mat)
    link_to_collection(obj, collection)
    return obj


def build_scene():
    collection = get_collection(COLLECTION_NAME)

    gunmetal = make_mat("P220 dark parkerized metal", (0.18, 0.18, 0.165, 1.0), 0.38, 0.8)
    black = make_mat("P220 satin black", (0.018, 0.018, 0.017, 1.0), 0.48, 0.55)
    rubber = make_mat("P220 textured grip", (0.045, 0.045, 0.04, 1.0), 0.75, 0.1)
    edge = make_mat("P220 bright edge wear", (0.55, 0.55, 0.50, 1.0), 0.35, 0.7)
    brass = make_mat("P220 brass cartridge hint", (0.95, 0.64, 0.25, 1.0), 0.32, 0.85)
    engraved = make_mat("P220 dark engraving", (0.01, 0.01, 0.01, 1.0), 0.7, 0.0)

    # Main non-functional visual silhouette inspired by the P220 side reference.
    slide_points = [
        (-2.06, 0.88), (2.43, 0.88), (2.58, 1.00), (2.58, 1.38),
        (2.44, 1.54), (-1.70, 1.58), (-1.94, 1.48), (-2.08, 1.16),
    ]
    prism_from_xz("continuous beveled slide silhouette", slide_points, 0.48, gunmetal, collection, 0.055)
    cube_obj("flat side slide face", (0.18, -0.255, 1.18), (4.28, 0.035, 0.44), gunmetal, collection, 0.018)
    cube_obj("long lower slide shadow line", (0.22, -0.285, 0.88), (4.18, 0.022, 0.035), black, collection, 0.004)
    cube_obj("front rounded slide nose", (2.42, -0.015, 1.12), (0.34, 0.50, 0.68), gunmetal, collection, 0.09)

    frame_points = [
        (-1.92, 0.18), (1.98, 0.18), (2.34, 0.42), (2.36, 0.82),
        (-1.95, 0.85), (-2.10, 0.56),
    ]
    prism_from_xz("one piece frame side plate", frame_points, 0.42, gunmetal, collection, 0.045)
    cube_obj("front dust cover block", (1.62, -0.015, 0.50), (1.54, 0.43, 0.54), gunmetal, collection, 0.05)
    cube_obj("dust cover bevel shadow", (1.62, -0.270, 0.20), (1.34, 0.030, 0.08), black, collection, 0.006)

    grip_points = [
        (-1.92, 0.68), (-0.80, 0.56), (-0.37, -1.52),
        (-0.54, -1.70), (-1.58, -1.74), (-1.96, -1.48), (-2.12, -0.10),
    ]
    prism_from_xz("curved backstrap angled grip", grip_points, 0.52, rubber, collection, 0.09)
    cube_rot_obj("front grip strap highlight", (-0.56, -0.285, -0.58), (0.18, 0.06, 1.96), (0.0, math.radians(-12), 0.0), black, collection, 0.06)
    panel_points = [
        (-1.72, 0.39), (-0.92, 0.30), (-0.62, -1.26),
        (-0.78, -1.40), (-1.46, -1.42), (-1.77, -0.18),
    ]
    prism_from_xz("inset diamond grip panel", panel_points, 0.56, rubber, collection, 0.035)
    prism_from_xz("rear beavertail and tang", [(-2.02, 0.78), (-2.26, 0.61), (-2.16, 0.50), (-1.88, 0.60)], 0.42, gunmetal, collection, 0.035)

    # Barrel and muzzle hints.
    cyl_obj("barrel outer muzzle", (2.68, 0.0, 1.18), 0.215, 0.62, black, collection, "X", 64, True)
    cyl_obj("barrel bright muzzle ring", (2.99, 0.0, 1.18), 0.150, 0.025, edge, collection, "X", 64, False)
    cyl_obj("barrel inner bore", (3.02, 0.0, 1.18), 0.095, 0.035, engraved, collection, "X", 48, False)
    cyl_obj("recoil spring guide hint", (2.57, 0.0, 0.70), 0.095, 0.44, black, collection, "X", 48, True)
    cube_obj("black front lower opening", (2.35, -0.277, 0.70), (0.30, 0.035, 0.24), black, collection, 0.014)

    # Ejection port and chamber are visible notches on top/side.
    cube_obj("ejection port dark pocket", (0.42, -0.284, 1.42), (0.82, 0.045, 0.25), black, collection, 0.035)
    cube_obj("brushed chamber block", (0.25, -0.315, 1.33), (0.54, 0.032, 0.12), edge, collection, 0.018)
    cyl_obj("small brass cartridge glimpse", (0.23, -0.325, 1.36), 0.045, 0.22, brass, collection, "X", 32, True)

    # Trigger guard and trigger: solid outer loop with black internal opening.
    guard_outer = [(-0.72, 0.28), (-0.54, -0.12), (-0.12, -0.28), (0.58, -0.24), (0.82, 0.18), (0.68, 0.50), (-0.55, 0.52)]
    prism_from_xz("solid trigger guard outer", guard_outer, 0.40, black, collection, 0.045)
    guard_inner = [(-0.46, 0.25), (-0.32, -0.02), (0.00, -0.12), (0.43, -0.10), (0.58, 0.18), (0.49, 0.34), (-0.42, 0.35)]
    prism_from_xz("trigger guard hollow black insert", guard_inner, 0.43, make_mat("P220 void black", (0.0, 0.0, 0.0, 1), 0.7, 0), collection, 0.02)
    curve_line("curved trigger", [(-0.04, -0.295, 0.34), (-0.16, -0.300, 0.08), (-0.02, -0.300, -0.12)], black, collection, 0.045)

    # Rear serrations.
    for i in range(14):
        x = -1.46 + i * 0.11
        serr = cube_obj(f"rear slide serration {i+1:02d}", (x, -0.302, 1.18), (0.035, 0.060, 0.62), edge, collection, 0.010)
        serr.rotation_euler[1] = math.radians(-12)

    # Controls, pins, screws.
    for name, x, z, r in [
        ("large frame takedown pin", 0.18, 0.55, 0.105),
        ("small frame pin", -0.58, 0.47, 0.075),
        ("slide screw detail", -0.88, 1.18, 0.060),
        ("grip upper screw", -1.28, -0.42, 0.145),
        ("grip lower screw", -1.22, -1.34, 0.145),
    ]:
        cyl_obj(name, (x, -0.275, z), r, 0.035, black, collection, "Y", 40, True)
        if "screw" in name:
            cube_obj(name + " slot", (x, -0.300, z), (r * 1.55, 0.012, 0.025), edge, collection, 0.004)

    cube_obj("slide stop lever", (-0.26, -0.310, 0.48), (0.55, 0.055, 0.13), gunmetal, collection, 0.025)
    cube_obj("decocker lever", (-0.78, -0.310, 0.66), (0.38, 0.055, 0.12), gunmetal, collection, 0.025)
    cube_obj("mag release button", (-0.95, -0.310, 0.30), (0.18, 0.055, 0.12), gunmetal, collection, 0.025)

    # Sights and hammer.
    prism_from_xz("rear sight with notch", [(-1.62, 1.54), (-1.30, 1.54), (-1.35, 1.80), (-1.56, 1.80)], 0.30, black, collection, 0.025)
    cube_obj("rear sight notch", (-1.46, -0.180, 1.74), (0.08, 0.06, 0.11), engraved, collection, 0.004)
    prism_from_xz("front sight blade", [(2.04, 1.50), (2.28, 1.50), (2.24, 1.68), (2.08, 1.68)], 0.22, black, collection, 0.025)
    prism_from_xz("curved hammer silhouette", [(-2.00, 1.14), (-2.24, 1.05), (-2.16, 0.96), (-1.92, 1.00)], 0.28, black, collection, 0.025)

    # Grip diamond checkering as crossed raised strokes on the grip panel.
    for i in range(12):
        x0 = -1.48 + i * 0.048
        curve_line(f"grip checkering rising {i:02d}", [(x0, -0.323, -1.14), (x0 + 0.32, -0.323, 0.10)], edge, collection, 0.004)
        curve_line(f"grip checkering falling {i:02d}", [(x0, -0.330, 0.10), (x0 + 0.32, -0.330, -1.14)], edge, collection, 0.004)

    # Subtle horizontal body seams and slide/frame split.
    cube_obj("slide lower shadow groove", (0.38, -0.325, 0.84), (4.10, 0.025, 0.035), black, collection, 0.005)
    cube_obj("frame lower accent groove", (0.80, -0.325, 0.34), (1.75, 0.025, 0.030), black, collection, 0.005)

    # Engravings and labels are shallow raised/dark text, not functional markings.
    add_label("P220", "slide model marking", (1.36, -0.315, 1.26), 0.18, engraved, collection)
    add_label("9mm Luger", "caliber marking", (0.28, -0.315, 1.14), 0.105, engraved, collection)
    add_label("G 130 198", "serial style marking", (0.88, -0.315, 1.12), 0.105, engraved, collection)
    add_label("VISUAL MODEL", "non functional label", (1.47, -0.315, 1.02), 0.065, engraved, collection)

    # Add a separate magazine as a visual prop, matching the reference board feel.
    mag_points = [(-2.05, -1.95), (-0.70, -1.72), (-0.58, -2.42), (-1.95, -2.68)]
    prism_from_xz("separate magazine body", mag_points, 0.32, gunmetal, collection, 0.06)
    for i in range(7):
        cyl_obj(f"magazine witness hole {i+1}", (-1.82 + i * 0.17, -0.19, -2.18 + i * 0.03), 0.045, 0.035, black, collection, "Y", 24, False)
    cyl_obj("brass cartridge hint", (-1.98, -0.03, -1.83), 0.085, 0.26, brass, collection, "X", 32, True)

    # Lighting, camera, and scene setup.
    bpy.ops.object.light_add(type="AREA", location=(0.2, -4.0, 4.2))
    key = bpy.context.object
    key.name = "large softbox key light"
    key.data.energy = 650
    key.data.size = 5.0
    link_to_collection(key, collection)

    bpy.ops.object.camera_add(location=(0.15, -7.5, 0.15), rotation=(math.radians(90), 0.0, 0.0))
    cam = bpy.context.object
    cam.name = "P220 visual camera"
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 6.6
    bpy.context.scene.camera = cam
    link_to_collection(cam, collection)

    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.cycles.samples = 64
    bpy.context.scene.view_settings.view_transform = "Filmic"
    bpy.context.scene.view_settings.look = "Medium High Contrast"

    # Aim camera at the model center.
    target = Vector((0.15, 0.0, 0.15))
    direction = target - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    return {
        "collection": COLLECTION_NAME,
        "objects": len(collection.objects),
        "note": "Created a non-functional visual P220-style Blender model with slide, frame, grip texture, controls, barrel, markings, and magazine prop.",
    }


RESULT = build_scene()
