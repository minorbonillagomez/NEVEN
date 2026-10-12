"""
Generate logo_neven-32.png and logo_neven-16.png for the NEVEN Ribbon
from the NEvƎИ SVG logo.

Ribbon requirements:
- 32x32 PNG (large button)
- 16x16 PNG (small button)
- RGBA, transparent background allowed
- No rounded corners — Office clips/renders them itself
"""
from PIL import Image, ImageDraw
import os

SVG_SIZE = 1024
SIZES    = [32, 16]
WHITE    = (255, 255, 255, 255)
RED      = (229,   9,  20, 255)
BG       = (  0,   0,   0, 255)   # black background
CORNER_R = 160

OUT_DIR  = os.path.dirname(os.path.abspath(__file__))


def s(val, size):
    return val * size / SVG_SIZE


def thick_line(draw, x0, y0, x1, y1, w, color):
    draw.line([(x0, y0), (x1, y1)], fill=color, width=max(1, w))


def draw_rounded_rect(draw, size, radius, fill):
    r = max(1, radius)
    x0, y0, x1, y1 = 0, 0, size - 1, size - 1
    draw.rectangle([x0 + r, y0, x1 - r, y1], fill=fill)
    draw.rectangle([x0, y0 + r, x1, y1 - r], fill=fill)
    for cx, cy in [(x0, y0), (x1 - 2*r, y0), (x0, y1 - 2*r), (x1 - 2*r, y1 - 2*r)]:
        draw.ellipse([cx, cy, cx + 2*r, cy + 2*r], fill=fill)


def render(size):
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    def sc(v):   return s(v, size)
    def sw(v):   return max(1, round(s(v, size)))

    r  = round(sc(CORNER_R))
    lw = sw(38)   # standard stroke
    vw = sw(42)   # v stroke (slightly thicker)

    # Rounded black background
    draw_rounded_rect(draw, size, r, BG)

    # N
    thick_line(draw, sc(120), sc(620), sc(120), sc(404), lw, WHITE)
    thick_line(draw, sc(120), sc(404), sc(216), sc(620), lw, WHITE)
    thick_line(draw, sc(216), sc(620), sc(216), sc(404), lw, WHITE)

    # E
    thick_line(draw, sc(336), sc(404), sc(256), sc(404), lw, WHITE)
    thick_line(draw, sc(256), sc(404), sc(256), sc(620), lw, WHITE)
    thick_line(draw, sc(256), sc(620), sc(336), sc(620), lw, WHITE)
    thick_line(draw, sc(256), sc(512), sc(320), sc(512), lw, WHITE)

    # v  (red)
    thick_line(draw, sc(390), sc(470), sc(440), sc(620), vw, RED)
    thick_line(draw, sc(440), sc(620), sc(490), sc(470), vw, RED)

    # Ǝ
    thick_line(draw, sc(544), sc(404), sc(624), sc(404), lw, WHITE)
    thick_line(draw, sc(624), sc(404), sc(624), sc(620), lw, WHITE)
    thick_line(draw, sc(624), sc(620), sc(544), sc(620), lw, WHITE)
    thick_line(draw, sc(624), sc(512), sc(560), sc(512), lw, WHITE)

    # И
    thick_line(draw, sc(704), sc(620), sc(704), sc(404), lw, WHITE)
    thick_line(draw, sc(704), sc(620), sc(800), sc(404), lw, WHITE)
    thick_line(draw, sc(800), sc(620), sc(800), sc(404), lw, WHITE)

    return img


if __name__ == "__main__":
    targets = [
        (32, "logo_neven-32.png"),
        (16, "logo_neven-16.png"),
        (32, "logo-32.png"),
        (16, "logo-16.png"),
    ]
    for sz, name in targets:
        img  = render(sz)
        path = os.path.join(OUT_DIR, name)
        img.save(path, "PNG")
        print(f"Saved {name}  ({sz}x{sz})")
    print("Done — rebuild NEVENRibbon.dll to apply.")
