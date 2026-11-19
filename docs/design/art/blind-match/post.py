"""Composite on paper and soften like the reference: python3 post.py in.png out.png"""
import io
import sys

from PIL import Image

src, dst = sys.argv[1:3]
b = Image.open(src).convert("RGBA")
bg = Image.new("RGBA", b.size, (246, 247, 242, 255))
bg.alpha_composite(b)
im = bg.convert("RGB")
W, H = im.size
im = im.resize((int(W * 0.6), int(H * 0.6)), Image.LANCZOS).resize((W, H), Image.BICUBIC)
buf = io.BytesIO()
im.save(buf, "JPEG", quality=82)
buf.seek(0)
Image.open(buf).convert("RGB").save(dst)
