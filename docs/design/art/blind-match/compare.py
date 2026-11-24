"""Side by side for a blind judge: reference and attempt in random order, labelled A and B.
The answer is written to answers.txt, which the judge never sees."""
import random, sys
from PIL import Image, ImageDraw, ImageFont

attempt, out, rnd = sys.argv[1], sys.argv[2], sys.argv[3]
ref = Image.open("ref.png").convert("RGB")
mine = Image.open(attempt).convert("RGB").resize(ref.size, Image.LANCZOS)
pair = [("reference", ref), ("attempt", mine)]
random.SystemRandom().shuffle(pair)
W, H = ref.size
sheet = Image.new("RGB", (W * 2 + 60, H + 70), (232, 232, 230))
d = ImageDraw.Draw(sheet)
try:
    f = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
except Exception:
    f = None
for i, (_, im) in enumerate(pair):
    x = 20 + i * (W + 20)
    sheet.paste(im, (x, 20))
    d.text((x + W // 2 - 10, H + 28), "AB"[i], fill=(20, 20, 20), font=f)
sheet.save(out)
with open("answers.txt", "a") as fh:
    fh.write(f"round {rnd}: A={pair[0][0]} B={pair[1][0]}\n")
print("saved")
