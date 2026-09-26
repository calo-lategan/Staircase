import bpy
sc = bpy.context.scene
se = sc.sequence_editor_create()
col = se.strips
print("new_effect doc:", col.new_effect.__doc__)
print("new_image doc:", col.new_image.__doc__)
try:
    s = col.new_effect(name="T", type='TEXT', channel=2, frame_start=1, length=10)
except TypeError as e:
    print("ERR", e); s = col.new_effect(name="T", type='TEXT', channel=2, frame_start=1, frame_end=10)
print("TEXT props:", [p.identifier for p in s.bl_rna.properties if not p.is_readonly])
print("ENGINES", [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items])
print("EEVEE", [p.identifier for p in sc.eevee.bl_rna.properties if not p.is_readonly])
import os
print("STUDIO", os.listdir(os.path.join(bpy.utils.system_resource('DATAFILES'), "studiolights", "world")))
