"""Cut the rendered storyline frames into MP4s with captions (Blender VSE, no external ffmpeg needed).
blender -b --factory-startup --python assemble_v4.py -- <frames_dir> <story_json> <out_mp4> [WxH] [kbps]
kbps = 0 -> constant-quality (high) master; kbps > 0 -> fixed bitrate web copy.
"""
import bpy, sys, os, json, glob
argv = sys.argv[sys.argv.index("--") + 1:]
frames_dir, story_json, out_mp4 = argv[0], argv[1], argv[2]
W, H = map(int, (argv[3] if len(argv) > 3 else "1600x900").split("x"))
kbps = int(argv[4]) if len(argv) > 4 else 0
story = json.load(open(story_json))
files = sorted(glob.glob(os.path.join(frames_dir, "*.jpg")))
assert files, "no frames"
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
sc.render.fps = 24
sc.frame_start, sc.frame_end = 1, len(files)
se = sc.sequence_editor_create()
img = se.strips.new_image("frames", files[0], 1, 1, fit_method='FIT')
for f in files[1:]:
    img.elements.append(os.path.basename(f))
S = H / 900.0


def text(t, f0, f1, ch, size, loc, ax, ay, box=True, bold=False):
    s = se.strips.new_effect(name=t[:40], type='TEXT', channel=ch, frame_start=f0, length=max(1, f1 - f0))
    s.text = t
    s.font_size = size * S
    s.color = (1, 1, 1, 1)
    s.location = loc
    s.anchor_x, s.anchor_y = ax, ay
    s.alignment_x = ax if ax in ('LEFT', 'CENTER', 'RIGHT') else 'CENTER'
    s.wrap_width = 0.86
    s.use_bold = bold
    s.use_box = box
    s.box_color = (0.06, 0.09, 0.12, 0.72)
    s.box_margin = 0.012
    s.use_shadow = False
    s.blend_type = 'ALPHA_OVER'
    return s


n = 0
for c in story["captions"]:
    f0, f1 = c["f0"], min(c["f1"], len(files))
    if f1 <= f0:
        continue
    if c["slot"] == "title":
        text(c["text"], f0, f1, 4, 44, (0.5, 0.16), 'CENTER', 'BOTTOM', bold=True)
    elif c["slot"] == "top":
        text(c["text"], f0, f1, 3, 26, (0.025, 0.955), 'LEFT', 'TOP')
    else:
        text(c["text"], f0, f1, 2 + (n % 2) * 3, 27, (0.5, 0.05), 'CENTER', 'BOTTOM')   # alternate channels: overlaps
    n += 1
R = sc.render
R.use_sequencer = True
R.use_compositing = False
try:
    R.image_settings.media_type = 'IMAGE'
except Exception:
    pass
R.image_settings.file_format = 'PNG'
R.ffmpeg.format = 'MPEG4'
R.ffmpeg.codec = 'H264'
R.ffmpeg.gopsize = 24
if kbps:
    R.ffmpeg.constant_rate_factor = 'NONE'
    R.ffmpeg.video_bitrate = kbps
    R.ffmpeg.minrate = 0
    R.ffmpeg.maxrate = int(kbps * 1.6)
    R.ffmpeg.buffersize = kbps * 2
else:
    R.ffmpeg.constant_rate_factor = 'HIGH'
R.ffmpeg.ffmpeg_preset = 'GOOD'
R.filepath = out_mp4
sc.frame_set(1240); bpy.ops.render.render(write_still=True)
print("ASSEMBLED", len(files), "frames", n, "captions ->", out_mp4)
