"""Build a low-poly tree scene and render it to tree.png.

Run inside Blender via the MCP addon's execute_blender_code.
"""

import math

import bpy
from mathutils import Vector

# --- clean scene --------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for group in (bpy.data.meshes, bpy.data.lights, bpy.data.cameras, bpy.data.materials):
    for block in list(group):
        if block.users == 0:
            group.remove(block)

scene = bpy.context.scene


def try_set(obj, prop, value):
    """Set an RNA property, tolerating names that differ across Blender versions."""
    try:
        setattr(obj, prop, value)
        return True
    except Exception:
        return False


def mat(name, rgb, rough=0.85):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    return m


def shade_flat(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = False


def shade_smooth(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = True
    if hasattr(obj.data, "use_auto_smooth"):
        obj.data.use_auto_smooth = True
        obj.data.auto_smooth_angle = math.radians(40)


BROWN = (0.24, 0.125, 0.055)
GREENS = [
    (0.055, 0.33, 0.085),
    (0.085, 0.42, 0.125),
    (0.045, 0.27, 0.07),
    (0.11, 0.48, 0.16),
]
GRASS = (0.085, 0.34, 0.10)

GROUND_TOP = 0.15

# --- round patch of grass -----------------------------------------------------
bpy.ops.mesh.primitive_cylinder_add(
    vertices=48, radius=2.6, depth=0.3, location=(0, 0, GROUND_TOP - 0.15)
)
grass = bpy.context.active_object
grass.name = "GrassPatch"
grass.data.materials.append(mat("Grass", GRASS, rough=0.95))
shade_smooth(grass)

# --- brown trunk: 7-sided tapered prism, flat shaded --------------------------
TRUNK_H = 2.35
bpy.ops.mesh.primitive_cone_add(
    vertices=7,
    radius1=0.40,
    radius2=0.24,
    depth=TRUNK_H,
    location=(0, 0, GROUND_TOP + TRUNK_H / 2),
)
trunk = bpy.context.active_object
trunk.name = "Trunk"
trunk.rotation_euler[2] = math.radians(12)
trunk.data.materials.append(mat("Bark", BROWN))
shade_flat(trunk)

TRUNK_TOP = GROUND_TOP + TRUNK_H

# --- crown: four blocky green shapes -----------------------------------------
BLOCKS = [
    # name, size xyz, location, euler degrees, colour index
    ("Crown_Main", (1.70, 1.70, 1.55), (0.00, 0.00, TRUNK_TOP + 0.62), (0, 0, 18), 0),
    ("Crown_Right", (1.22, 1.18, 1.12), (0.88, 0.40, TRUNK_TOP + 0.16), (10, 14, 42), 1),
    ("Crown_Left", (1.12, 1.08, 1.02), (-0.80, -0.46, TRUNK_TOP + 0.28), (-12, 8, -27), 2),
    ("Crown_Top", (0.92, 0.88, 0.82), (0.12, 0.62, TRUNK_TOP + 1.42), (16, -10, 58), 3),
]

for i, (name, size, loc, rot_deg, cidx) in enumerate(BLOCKS):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    block = bpy.context.active_object
    block.name = name
    block.scale = size
    block.rotation_euler = tuple(math.radians(a) for a in rot_deg)
    block.data.materials.append(mat(f"Foliage{i}", GREENS[cidx], rough=0.8))
    shade_flat(block)

# --- sun light ----------------------------------------------------------------
sun_data = bpy.data.lights.new("Sun", type="SUN")
sun_data.energy = 4.0
sun_data.color = (1.0, 0.93, 0.80)
sun_data.angle = math.radians(3.0)
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.location = (0, 0, 6)
sun.rotation_euler = (math.radians(48), 0, math.radians(30))

# --- camera -------------------------------------------------------------------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 40
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)

look_at = Vector((0.0, 0.0, 2.10))
cam.location = Vector((6.8, -9.2, 2.60))
cam.rotation_euler = (look_at - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam

# --- world --------------------------------------------------------------------
# Two separate concerns: soft *lighting* from the sky, and a *visible* backdrop.
# A real Nishita sky is far too bright to look at directly - it clips to flat
# white/gray - so camera rays get a controlled gradient while the dim sky still
# provides bluish ambient fill.
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
nt = world.node_tree
nt.nodes.clear()

out = nt.nodes.new("ShaderNodeOutputWorld")
mix = nt.nodes.new("ShaderNodeMixShader")
light_path = nt.nodes.new("ShaderNodeLightPath")
nt.links.new(light_path.outputs["Is Camera Ray"], mix.inputs["Fac"])

# lighting branch: dim physical sky
sky = nt.nodes.new("ShaderNodeTexSky")
try_set(sky, "sky_type", "NISHITA")
try_set(sky, "sun_elevation", math.radians(40))
try_set(sky, "sun_rotation", math.radians(210))
try_set(sky, "sun_intensity", 0.15)
try_set(sky, "dust_density", 3.0)
sky_bg = nt.nodes.new("ShaderNodeBackground")
sky_bg.inputs["Strength"].default_value = 0.05
nt.links.new(sky.outputs["Color"], sky_bg.inputs["Color"])
nt.links.new(sky_bg.outputs["Background"], mix.inputs[1])

# visible branch: vertical gradient, horizon -> zenith
coord = nt.nodes.new("ShaderNodeTexCoord")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.interpolation = "B_SPLINE"
ramp.color_ramp.elements[0].position = -0.05
ramp.color_ramp.elements[0].color = (0.72, 0.82, 0.90, 1.0)  # pale horizon
ramp.color_ramp.elements[1].position = 0.55
ramp.color_ramp.elements[1].color = (0.13, 0.38, 0.75, 1.0)  # blue zenith
view_bg = nt.nodes.new("ShaderNodeBackground")
view_bg.inputs["Strength"].default_value = 1.0
nt.links.new(coord.outputs["Generated"], sep.inputs["Vector"])
nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], view_bg.inputs["Color"])
nt.links.new(view_bg.outputs["Background"], mix.inputs[2])

nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])

# --- render settings ----------------------------------------------------------
try_set(scene.render, "engine", "BLENDER_EEVEE")
for prop in ("use_shadows", "use_shadow"):
    try_set(scene.eevee, prop, True)
try_set(scene.eevee, "use_gtao", True)
try_set(scene.eevee, "taa_render_samples", 32)
try_set(scene.eevee, "shadow_soft_size", 0.35)
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
try_set(scene.view_settings, "view_transform", "Filmic")
try_set(scene.view_settings, "look", "Medium High Contrast")
try_set(scene.view_settings, "exposure", -0.15)
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = r"C:\MRL\tree.png"

# --- report framing in normalised camera space before rendering ---------------
from bpy_extras.object_utils import world_to_camera_view as camview

print("LOOK_AT", tuple(look_at), "CAM", tuple(cam.location))
for o in scene.objects:
    if o.type != "MESH":
        continue
    pts = [camview(scene, cam, o.matrix_world @ Vector(c)) for c in o.bound_box]
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    print(
        "FRAME %-12s x %.2f..%.2f  y %.2f..%.2f"
        % (o.name, min(xs), max(xs), min(ys), max(ys))
    )

bpy.ops.render.render(write_still=False)
bpy.data.images["Render Result"].save_render(
    filepath=scene.render.filepath, scene=scene
)
bpy.ops.wm.save_as_mainfile(filepath=r"C:\MRL\tree.blend")
print("OBJECTS:", ", ".join(sorted(o.name for o in scene.objects)))
print("RENDERED_TO:", scene.render.filepath)
