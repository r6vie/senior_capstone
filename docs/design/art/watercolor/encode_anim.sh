#!/bin/sh
# Encode the painting animations (paint_anim.py) into watercolor set 1 (set-1/anim/):
#   <key>-loop.{mp4,webm}    the front page: paints at full timing, rests, washes back to paper, loops (25 s, 12 fps)
#   <key>-quick.{mp4,webm}   the book reveal, the picks and the design studio: the painting at 0.3 of the time,
#                            ending on the cover (about 4 s, 24 fps). Josef, 2026-11-23: the loop is the only slow one.
#   <key>-poster.webp        the finished cover, for reduced motion and before a video loads
# and, for review only, out/review-chain.{mp4,webm} (every loop in a row: the front page with a new cover each cycle)
# and out/review-quick.{mp4,webm} (every quick paint-in, each held 2 s).
set -e
cd "$(dirname "$0")"
OUT=set-1/anim
mkdir -p "$OUT"
KEYS="mesa hills lake winter city blossom beach autumn lighthouse-day lighthouse-dusk"
X264="-c:v libx264 -pix_fmt yuv420p -crf 24 -preset slow -movflags +faststart -an"
VP9="-c:v libvpx-vp9 -b:v 0 -crf 36 -row-mt 1 -an"
: > out/chain.txt
: > out/quick.txt
for k in $KEYS; do
  d=out/anim-$k
  ffmpeg -y -loglevel error -framerate 12 -i "$d/loop_%04d.png" $X264 "$OUT/$k-loop.mp4"
  ffmpeg -y -loglevel error -framerate 12 -i "$d/loop_%04d.png" $VP9 "$OUT/$k-loop.webm"
  ffmpeg -y -loglevel error -framerate 24 -i "$d/quick_%04d.png" $X264 "$OUT/$k-quick.mp4"
  ffmpeg -y -loglevel error -framerate 24 -i "$d/quick_%04d.png" $VP9 "$OUT/$k-quick.webm"
  cwebp -quiet -q 90 "out/anim-$k-poster.png" -o "$OUT/$k-poster.webp"
  # review: the quick paint-in held 2 s on the finished cover
  ffmpeg -y -loglevel error -framerate 24 -i "$d/quick_%04d.png" -vf "tpad=stop_mode=clone:stop_duration=2" $X264 "out/rq-$k.mp4"
  echo "file 'anim-chain-$k.mp4'" >> out/chain.txt
  cp "$OUT/$k-loop.mp4" "out/anim-chain-$k.mp4"
  echo "file 'rq-$k.mp4'" >> out/quick.txt
  echo "encoded $k"
done
ffmpeg -y -loglevel error -f concat -safe 0 -i out/chain.txt -c copy out/review-chain.mp4
ffmpeg -y -loglevel error -i out/review-chain.mp4 $VP9 out/review-chain.webm
ffmpeg -y -loglevel error -f concat -safe 0 -i out/quick.txt -c copy out/review-quick.mp4
ffmpeg -y -loglevel error -i out/review-quick.mp4 $VP9 out/review-quick.webm
ls -la "$OUT" out/review-*
du -sh "$OUT"
