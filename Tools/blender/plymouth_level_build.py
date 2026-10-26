# plymouth_level_build.py — The Commander Boomer Shooter, Plymouth map build
# Run: blender -b -P plymouth_level_build.py -- --data <dir> --out <dir>
# Builds the Plymouth (MA) level from real OSM GPS data at 1 unit = 1 meter.
import bpy, bmesh, json, math, os, sys, argparse

def parse_args():
    argv = list(sys.argv)
    i = argv.index("--") if "--" in argv else -1
    a = argv[i+1:] if i >= 0 else []
    p = argparse.ArgumentParser()
    p.add_argument("--data", default="/home/gillsystems-htpc/plymouth_data")
    p.add_argument("--out", default="/home/gillsystems-htpc/plymouth_out")
    try:
        return p.parse_args(a)
    except SystemExit:
        return p.parse_args([])

A = parse_args()
DATA, OUT = os.path.abspath(A.data), os.path.abspath(A.out)
os.makedirs(OUT, exist_ok=True)
level = json.load(open(os.path.join(DATA, "plymouth_level.json")))
corr = json.load(open(os.path.join(DATA, "corridor.json")))

u1, v1, u2, v2 = corr["u1"], corr["v1"], corr["u2"], corr["v2"]
CW_m, CH_m = corr["m"]  # corridor meters (X = east, Y = north)
HU, HV = corr["house"]
TU, TV = corr["hut"]

def uv2xy(u, v):
    """local mosaic (u,v): u->east, v: 0=north 1=south. World: X=east, Y=north."""
    x = (u - u1) / (u2 - u1) * CW_m
    y = (v2 - v) / (v2 - v1) * CH_m
    return x, y

def uv2uv(u, v):
    """image UV for ground plane (0,0)=bottom-left of image = (u1, v2)."""
    px = (u - u1) / (u2 - u1)
    py = 1.0 - (v - v1) / (v2 - v1)
    return px, py

# ---------- clear scene ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.textures, bpy.data.images):
    for b in list(block):
        if b.users == 0:
            block.remove(b)

# ---------- materials ----------
def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes.get("Principled BSDF")

# ground with real map texture
ground_mat, gb = new_mat("M_PlymouthGround")
gb.inputs["Roughness"].default_value = 0.95
img = bpy.data.images.load(os.path.join(DATA, "plymouth_corridor.png"), check_existing=True)
nt = ground_mat.node_tree
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = img
bright = nt.nodes.new("ShaderNodeBrightContrast")
bright.inputs["Bright"].default_value = 0.25
bright.inputs["Contrast"].default_value = 1.05
nt.links.new(tex.outputs["Color"], bright.inputs["Color"])
nt.links.new(bright.outputs["Color"], gb.inputs["Base Color"])
# flip v: image top = north = +Y. Ground plane made by primitive_plane is in XZ-ish; we build manually with bmesh.

road_mat, rb = new_mat("M_Road")
rb.inputs["Base Color"].default_value = (0.08, 0.08, 0.09, 1.0)
rb.inputs["Roughness"].default_value = 0.9
water_mat, wb = new_mat("M_Water")
wb.inputs["Base Color"].default_value = (0.02, 0.08, 0.22, 1.0)
wb.inputs["Roughness"].default_value = 0.15
wb.inputs["Metallic"].default_value = 0.3
bld_mat, _ = new_mat("M_Building")
bld_mat.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.35, 0.33, 0.32, 1.0)
bld_mat.node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value = 0.8
beacon_mat, bb2 = new_mat("M_Beacon")
bb2.inputs["Base Color"].default_value = (1, 1, 1, 1)
bb2.inputs["Emission Color"].default_value = (1.0, 0.85, 0.1, 1.0)
bb2.inputs["Emission Strength"].default_value = 80.0
beacon_red_mat, br = new_mat("M_BeaconRed")
br.inputs["Emission Color"].default_value = (1.0, 0.08, 0.05, 1.0)
br.inputs["Emission Strength"].default_value = 100.0
route_mat, rt = new_mat("M_Route")
rt.inputs["Emission Color"].default_value = (1.0, 0.9, 0.1, 1.0)
rt.inputs["Emission Strength"].default_value = 30.0

# ---------- ground plane (bmesh, UV mapped) ----------
bm = bmesh.new()
x0, y0 = 0.0, 0.0
x1, y1 = CW_m, CH_m
va = bm.verts.new((x0, y0, 0.0)); vb = bm.verts.new((x1, y0, 0.0))
vc = bm.verts.new((x1, y1, 0.0)); vd = bm.verts.new((x0, y1, 0.0))
f = bm.faces.new((va, vb, vc, vd))
me = bpy.data.meshes.new("Ground")
bm.to_mesh(me); bm.free()
uv_layer = me.uv_layers.new(name="UVMap")
uvs = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
for li, uvv in enumerate(uvs):
    uv_layer.data[li].uv = uvv
ground = bpy.data.objects.new("PLY_Ground", me)
bpy.context.collection.objects.link(ground)
ground.data.materials.append(ground_mat)

# ---------- roads (single mesh, bmesh) ----------
road_w = {"motorway": 14, "motorway_link": 8, "trunk": 12, "primary": 9,
          "secondary": 6, "tertiary": 5, "residential": 4, "unclassified": 3.5}
bm = bmesh.new()
n = 0
for r in level["roads"]:
    if r["type"] != "road":
        continue
    pts = [uv2xy(u, v) for u, v in r["ul"]]
    if len(pts) < 2:
        continue
    w = road_w.get(r["kind"], 4) / 2.0
    prev = None
    for i in range(len(pts) - 1):
        ax, ay = pts[i]; bx, by = pts[i+1]
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy)
        if L < 1e-4:
            continue
        nx, ny = -dy / L * w, dx / L * w
        a1 = bm.verts.new((ax + nx, ay + ny, 0.06))
        a2 = bm.verts.new((ax - nx, ay - ny, 0.06))
        if prev is None:
            b1 = bm.verts.new((bx + nx, by + ny, 0.06))
            b2 = bm.verts.new((bx - nx, by - ny, 0.06))
        else:
            b1, b2 = prev
        bm.faces.new((a1, a2, b2, b1))
        prev = (b1, b2)
        n += 1
if n:
    me = bpy.data.meshes.new("Roads")
    bm.to_mesh(me); bm.free()
    roads_obj = bpy.data.objects.new("PLY_Roads", me)
    bpy.context.collection.objects.link(roads_obj)
    roads_obj.data.materials.append(road_mat)
print("road quads:", n)

# ---------- water plane (big, at north edge + bay) ----------
bm = bmesh.new()
# bay: everything north of hut line, full width
hy = uv2xy(TU, TV)[1]
wa = bm.verts.new((0, hy + 60, -0.2)); wb2 = bm.verts.new((CW_m, hy + 60, -0.2))
wc = bm.verts.new((CW_m, CH_m + 2000, -0.2)); wd = bm.verts.new((0, CH_m + 2000, -0.2))
bm.faces.new((wa, wb2, wc, wd))
me = bpy.data.meshes.new("Water")
bm.to_mesh(me); bm.free()
water_obj = bpy.data.objects.new("PLY_Water", me)
bpy.context.collection.objects.link(water_obj)
water_obj.data.materials.append(water_mat)

# ---------- buildings (boxes) ----------
bm = bmesh.new()
nb = 0
for b in level["buildings"]:
    ul = b["ul"]
    if len(ul) < 3:
        continue
    xs = [uv2xy(u, v) for u, v in ul]
    minx = min(p[0] for p in xs); maxx = max(p[0] for p in xs)
    miny = min(p[1] for p in xs); maxy = max(p[1] for p in xs)
    dw = maxx - minx; dh = maxy - miny
    if dw < 3 or dh < 3:
        continue
    if dw > 400 or dh > 400:
        continue  # park/greenery footprint, skip
    h = min(14.0, 4.5 + (dw + dh) * 0.06)
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    res = bmesh.ops.create_cube(bm, size=1.0)
    verts = res["verts"]
    bmesh.ops.scale(bm, vec=(dw, dh, h), verts=verts)
    bmesh.ops.translate(bm, vec=(cx, cy, h / 2 - 0.05), verts=verts)
    nb += 1
me = bpy.data.meshes.new("Buildings")
bm.to_mesh(me); bm.free()
bld_obj = bpy.data.objects.new("PLY_Buildings", me)
bpy.context.collection.objects.link(bld_obj)
bld_obj.data.materials.append(bld_mat)
print("buildings:", nb)

# ---------- landmarks ----------
hx, hy2 = uv2xy(HU, HV)
tx, ty = uv2xy(TU, TV)

def beacon(x, y, mat, h=18.0, r=1.6):
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=r, radius2=0.35, depth=h, location=(x, y, h / 2 + 0.1))
    o = bpy.context.active_object
    o.name = "PLY_Beacon"
    o.data.materials.append(mat)
    return o

beacon(hx, hy2, beacon_mat)
beacon(tx, ty, beacon_red_mat)
# house block
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx - 8, hy2 - 8, 6.5))
hb = bpy.context.active_object
hb.name = "PLY_Home"
_hbm = bmesh.new(); _hbm.from_mesh(hb.data)
bmesh.ops.scale(_hbm, vec=(14, 12, 13))
_hbm.to_mesh(hb.data); _hbm.free()
hb.data.materials.append(bld_mat)
# hut block (waterfront restaurant)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(tx - 10, ty - 18, 8.0))
hutb = bpy.context.active_object
hutb.name = "PLY_Hut"
_hbm = bmesh.new(); _hbm.from_mesh(hutb.data)
bmesh.ops.scale(_hbm, vec=(18, 14, 16))
_hbm.to_mesh(hutb.data); _hbm.free()
hutb.data.materials.append(bld_mat)

# route line house -> hut (elevated strip)
bm = bmesh.new()
ax, ay = hx, hy2; bx, by = tx, ty
dx, dy = bx - ax, by - ay
L = math.hypot(dx, dy)
nx, ny = -dy / L * 1.2, dx / L * 1.2
v1 = bm.verts.new((ax + nx, ay + ny, 2.5)); v2 = bm.verts.new((ax - nx, ay - ny, 2.5))
v3 = bm.verts.new((bx - nx, by - ny, 2.5)); v4 = bm.verts.new((bx + nx, by + ny, 2.5))
bm.faces.new((v1, v2, v3, v4))
me = bpy.data.meshes.new("Route")
bm.to_mesh(me); bm.free()
route_obj = bpy.data.objects.new("PLY_Route", me)
bpy.context.collection.objects.link(route_obj)
route_obj.data.materials.append(route_mat)
print("landmarks: house", hx, hy2, "hut", tx, ty)

# ---------- world / lighting (night game) ----------
world = bpy.data.worlds["World"] if "World" in bpy.data.worlds else bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.02, 0.03, 0.08, 1.0)
bg.inputs["Strength"].default_value = 2.0
bpy.ops.object.light_add(type='SUN', location=(2000, 4000, 3000))
sun = bpy.context.active_object
sun.name = "PLY_Moon"
sun.data.energy = 6.0
sun.rotation_euler = (math.radians(55), 0, math.radians(-35))
bpy.ops.object.light_add(type='SUN', location=(-3000, 2000, 1500))
fill = bpy.context.active_object
fill.name = "PLY_Fill"
fill.data.energy = 2.0

# ---------- cameras ----------
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 32
scene.view_settings.view_transform = 'Standard'
scene.render.resolution_x = 1600
scene.render.resolution_y = 1200
scene.render.image_settings.file_format = 'PNG'

def ortho_cam(name, target, height, scale, rotz=0.0):
    bpy.ops.object.camera_add(location=(target[0], target[1], height))
    cam = bpy.context.active_object
    cam.name = name
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = scale
    cam.data.clip_start = 1.0
    cam.data.clip_end = max(height * 3, 50000)
    cam.rotation_euler = (0.0, 0.0, rotz)
    tgt = bpy.data.objects.new(name + "_Tgt", None)
    bpy.context.collection.objects.link(tgt)
    tgt.location = target
    con = cam.constraints.new('TRACK_TO')
    con.target = tgt
    con.track_axis = 'TRACK_NEGATIVE_Z'
    con.up_axis = 'UP_Y'
    return cam

ortho_cam("CAM_Overview", (CW_m/2, CH_m/2, 0), 4200, max(CW_m, CH_m) * 1.15)
ortho_cam("CAM_Home", (hx, hy2, 0), 1400, 1400)
ortho_cam("CAM_Hut", (tx, ty, 0), 1400, 1400)

# Hero perspective: offshore looking north up the harbor at the town
hero_cam = bpy.data.cameras.new("HERO")
hero_cam.type = 'PERSP'; hero_cam.lens = 30
hero_cam.clip_start = 1.0; hero_cam.clip_end = 60000
hc = bpy.data.objects.new("CAM_Hero", hero_cam)
bpy.context.collection.objects.link(hc)
hc.location = (CW_m*0.5, hy2 - 900, 350)   # closer offshore, look north up the bay
hc.rotation_euler = (math.radians(84), 0, 0)

views = [("CAM_Overview", "plymouth_overview.png"), ("CAM_Home", "plymouth_home.png"), ("CAM_Hut", "plymouth_hut.png"), ("CAM_Hero", "plymouth_hero.png")]
for cam_name, fname in views:
    cam = bpy.data.objects[cam_name]
    scene.camera = cam
    scene.render.filepath = os.path.join(OUT, fname)
    bpy.ops.render.render(write_still=True)
    print("rendered:", fname)

# ---------- FBX export (whole level, UE-ready) ----------
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
    if o.name.startswith("PLY_"):
        o.select_set(True)
fbx = os.path.join(OUT, "PLY_PlymouthLevel.fbx")
bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True,
    apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y',
    add_leaf_bones=False, use_mesh_modifiers=True, object_types={'MESH'},
    path_mode='COPY', embed_textures=True)
print("fbx:", fbx, os.path.getsize(fbx), "bytes")
print("DONE")
