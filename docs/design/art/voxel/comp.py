"""Lay a transparent render on cover paper (white)."""
import sys
from PIL import Image
src, out = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGBA")
bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
bg.alpha_composite(im)
bg.convert("RGB").save(out)
