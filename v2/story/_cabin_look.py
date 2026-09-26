import bpy, math
from mathutils import Vector
sc = bpy.context.scene
cab = [o for o in bpy.data.collections["Unsorted"].objects if o.type=='MESH' and (o.matrix_world @ Vector(o.bound_box[0])).x < -90]
keep = set(cab)
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = o not in keep
lo = Vector((1e9,)*3); hi = Vector((-1e9,)*3)
for o in cab:
    for v in o.data.vertices:
        w = o.matrix_world @ v.co
        lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
print("CABIN n", len(cab), "lo", lo, "hi", hi)
# objects near door side
door = sorted([(o.name, [round(x,2) for x in (o.matrix_world @ Vector(o.bound_box[0]))], [round(x,2) for x in o.dimensions]) for o in cab if (o.matrix_world @ Vector(o.bound_box[6])).x > -93.3], key=lambda r: r[1][1])
for d in door: print("DOORSIDE", d)
cam = bpy.data.objects.get("StateCam")
sc.camera = cam
cam.data.type = 'PERSP'; cam.data.lens = 28; cam.data.clip_end = 300
c = (lo + hi) / 2
R = sc.render; R.engine = 'BLENDER_WORKBENCH'; R.resolution_x, R.resolution_y = 1280, 720
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
for i, d in enumerate([Vector((1, -0.35, 0.3)), Vector((1, 0.2, 0.15)), Vector((-0.4, -1, 0.6))]):
    d.normalize()
    cam.location = c + d * 16
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    R.filepath = f"C:/Users/USER/Desktop/Staircases/idea one/v2/story/_cabin_{i}.png"
    bpy.ops.render.render(write_still=True)
