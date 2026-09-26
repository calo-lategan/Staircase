import sys, os, glob
from PIL import Image, ImageDraw
d, out, cols = sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 5
fs = sorted(glob.glob(os.path.join(d, "*.png")))
w, h = 480, 270
rows = (len(fs) + cols - 1) // cols
sheet = Image.new("RGB", (cols * w, rows * h), "white")
for i, p in enumerate(fs):
    im = Image.open(p).convert("RGB").resize((w, h))
    ImageDraw.Draw(im).text((6, 4), os.path.basename(p)[:-4], fill=(255, 0, 0))
    sheet.paste(im, ((i % cols) * w, (i // cols) * h))
sheet.save(out)
