"""The title adjusts by itself (Josef, 2026-11-21): the cover's ink is chosen from the paint behind the type. Measure
the mean luminance of the title area (world x 18-200, y 20-175 of 236 x 344); on a dark top the title and name are
cream, on a light top they take the book's own dark ink.

python3 ink.py out/<name>-xl.png [dark ink] -> prints the ink and the measured luminance"""
import sys
import numpy as np
from PIL import Image

CREAM = "#f6efe0"


def top_luminance(path):
    a = np.asarray(Image.open(path).convert("RGB"), float) / 255
    h, w = a.shape[:2]
    r = a[int(h * 20 / 344):int(h * 175 / 344), int(w * 18 / 236):int(w * 200 / 236)]
    lin = np.where(r <= 0.04045, r / 12.92, ((r + 0.055) / 1.055) ** 2.4)
    return float((0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]).mean())


def ink_for(path, dark_ink):
    """Cream on a dark top, the dark ink on a light one: whichever reads with more contrast."""
    L = top_luminance(path)

    def lum(hexc):
        c = np.array([int(hexc[i:i + 2], 16) for i in (1, 3, 5)], float) / 255
        c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

    def contrast(a, b):
        hi, lo = max(a, b), min(a, b)
        return (hi + 0.05) / (lo + 0.05)

    c_cream, c_dark = contrast(L, lum(CREAM)), contrast(L, lum(dark_ink))
    return (CREAM if c_cream > c_dark else dark_ink), L, max(c_cream, c_dark)


if __name__ == "__main__":
    ink, L, c = ink_for(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "#2a2a2a")
    print(ink, round(L, 3), round(c, 2))
