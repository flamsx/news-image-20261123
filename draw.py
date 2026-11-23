"""draw.py — fresh rendering engine for news-image-20261123.

Draws the Monday 23 November 2026 front page with PIL + Lexend.
Deterministic: no randomness, no timestamps inside the image.
Canvas is 1024x1024 per the kit rules.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
PAPER = (248, 244, 233)
INK = (20, 20, 20)
RED = (192, 39, 45)
RED_DARK = (150, 25, 30)
MUTED = (107, 100, 85)
RULE = (20, 20, 20)
CARD_BG = (255, 253, 247)
MAP_BG = (214, 228, 232)
LAND = (216, 199, 163)
LAND_LINE = (138, 125, 95)

BASE = os.path.dirname(os.path.abspath(__file__))
FONTS = {
    "regular": os.path.join(BASE, "fonts", "Lexend-Regular.ttf"),
    "medium": os.path.join(BASE, "fonts", "Lexend-Medium.ttf"),
    "semibold": os.path.join(BASE, "fonts", "Lexend-SemiBold.ttf"),
    "bold": os.path.join(BASE, "fonts", "Lexend-Bold.ttf"),
}
_cache = {}


def font(size, weight="regular"):
    key = (size, weight)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(FONTS[weight], int(round(size)))
    return _cache[key]


def text_w(draw, s, fnt):
    return draw.textlength(s, font=fnt)


def wrap(draw, s, fnt, max_w):
    """Greedy word wrap returning a list of lines that fit max_w."""
    words = s.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, x, y, s, fnt, max_w, fill=INK, lh=None, max_lines=None):
    lines = wrap(draw, s, fnt, max_w)
    if max_lines:
        lines = lines[:max_lines]
    if lh is None:
        lh = int(fnt.size * 1.22)
    for ln in lines:
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += lh
    return y


def center(draw, cx, y, s, fnt, fill=INK):
    w = draw.textlength(s, font=fnt)
    draw.text((cx - w / 2, y), s, font=fnt, fill=fill)
    return w


# ---------------------------------------------------------------- scenes
def scene_globe(d, x, y, w, h):
    """COP31: a globe with a red 'no deal' slash."""
    d.rectangle([x, y, x + w, y + h], fill=(31, 78, 110))
    cx, cy, r = x + w * 0.30, y + h * 0.52, min(w, h) * 0.36
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(58, 140, 110))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(248, 244, 233), width=2)
    for k in (-0.5, 0.0, 0.5):
        d.arc([cx - r, cy - r * 0.55 + k * r * 0.5, cx + r, cy + r * 0.55 + k * r * 0.5],
              0, 360, fill=(248, 244, 233), width=1)
    d.line([cx - r, cy, cx + r, cy], fill=(248, 244, 233), width=1)
    # broken pact paper on the right
    px, py = x + w * 0.58, y + h * 0.20
    d.rectangle([px, py, px + w * 0.34, py + h * 0.58], fill=(248, 244, 233))
    d.rectangle([px, py, px + w * 0.34, py + h * 0.58], outline=(150, 25, 30), width=2)
    for i in range(3):
        d.line([px + 6, py + 10 + i * 9, px + w * 0.34 - 6, py + 10 + i * 9],
               fill=(107, 100, 85), width=2)
    d.line([px - 4, py + h * 0.58 + 4, px + w * 0.34 + 4, py - 4],
           fill=(192, 39, 45), width=5)
    d.text((x + 8, y + h - 18), "ANTALYA  •  NO DEAL", font=font(11, "bold"),
           fill=(255, 255, 255))


def scene_drone(d, x, y, w, h):
    """Dymer: night sky, flats, drone path, explosion."""
    d.rectangle([x, y, x + w, y + h], fill=(16, 28, 58))
    for sx, sy in [(0.12, 0.18), (0.35, 0.10), (0.55, 0.22), (0.78, 0.12), (0.92, 0.28), (0.25, 0.30)]:
        d.ellipse([x + w * sx - 1.5, y + h * sy - 1.5, x + w * sx + 1.5, y + h * sy + 1.5],
                  fill=(255, 255, 255))
    d.ellipse([x + w * 0.80, y + h * 0.06, x + w * 0.80 + 26, y + h * 0.06 + 26],
              fill=(240, 235, 210))
    # buildings
    for bx, bw, bh in [(0.05, 0.22, 0.55), (0.30, 0.20, 0.72), (0.53, 0.24, 0.48), (0.80, 0.18, 0.62)]:
        d.rectangle([x + w * bx, y + h - h * bh, x + w * (bx + bw), y + h],
                    fill=(8, 14, 30))
        for wy in range(3):
            for wx in range(2):
                d.rectangle([x + w * (bx + 0.04 + wx * 0.09), y + h - h * bh + 8 + wy * 14,
                             x + w * (bx + 0.04 + wx * 0.09) + 6, y + h - h * bh + 8 + wy * 14 + 7],
                            fill=(255, 196, 66))
    # explosion on the middle block
    ex, ey = x + w * 0.42, y + h * 0.42
    for r, col in [(26, (255, 120, 40)), (18, (255, 170, 60)), (10, (255, 230, 150))]:
        d.ellipse([ex - r, ey - r, ex + r, ey + r], fill=col)
    # dashed drone path
    pts = [(x + w * 0.95, y + h * 0.15), (x + w * 0.75, y + h * 0.28), (x + w * 0.55, y + h * 0.35),
           (x + w * 0.42, y + h * 0.42)]
    for a, b in zip(pts, pts[1:]):
        n = 6
        for i in range(n):
            t0, t1 = i / n, (i + 0.5) / n
            d.line([a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0,
                    a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1],
                   fill=(255, 255, 255), width=2)


def scene_tanker(d, x, y, w, h):
    """Hormuz: sea, tanker, fire, missile streak."""
    d.rectangle([x, y, x + w, y + h * 0.55], fill=(214, 158, 92))
    d.rectangle([x, y + h * 0.55, x + w, y + h], fill=(28, 90, 130))
    for i in range(3):
        d.line([x, y + h * (0.62 + i * 0.12), x + w, y + h * (0.62 + i * 0.12)],
               fill=(120, 180, 210), width=2)
    # tanker
    tx, ty = x + w * 0.10, y + h * 0.48
    d.rectangle([tx, ty, tx + w * 0.62, ty + h * 0.14], fill=(60, 60, 66))
    d.rectangle([tx + w * 0.62, ty - h * 0.10, tx + w * 0.72, ty + h * 0.14], fill=(60, 60, 66))
    d.rectangle([tx + w * 0.05, ty - h * 0.16, tx + w * 0.18, ty], fill=(192, 39, 45))
    # fire on deck
    fx, fy = tx + w * 0.42, ty - h * 0.02
    for r, col in [(20, (255, 110, 30)), (13, (255, 170, 60)), (7, (255, 235, 160))]:
        d.ellipse([fx - r, fy - r, fx + r, fy + r], fill=col)
    # smoke
    for i, r in enumerate([8, 11, 14]):
        d.ellipse([fx - r + i * 4, fy - 26 - i * 10, fx + r + i * 4, fy - 26 - i * 10 + 2 * r],
                  fill=(90, 90, 90))
    # missile streak
    d.line([x + w * 0.98, y + h * 0.10, x + w * 0.72, y + h * 0.30], fill=(255, 255, 255), width=3)


def scene_plane(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(126, 166, 200))
    d.ellipse([x + w * 0.08, y + h * 0.30, x + w * 0.92, y + h * 0.62], fill=(248, 244, 233))
    d.polygon([(x + w * 0.86, y + h * 0.38), (x + w * 0.98, y + h * 0.46), (x + w * 0.86, y + h * 0.52)],
              fill=(248, 244, 233))
    d.rectangle([x + w * 0.30, y + h * 0.62, x + w * 0.42, y + h * 0.86], fill=(192, 39, 45))
    d.rectangle([x + w * 0.55, y + h * 0.62, x + w * 0.67, y + h * 0.86], fill=(192, 39, 45))
    for wx in range(5):
        d.ellipse([x + w * (0.16 + wx * 0.13), y + h * 0.40, x + w * (0.16 + wx * 0.13) + 5,
                   y + h * 0.40 + 5], fill=(31, 78, 110))


def scene_fire(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(52, 52, 58))
    d.rectangle([x + w * 0.15, y + h * 0.45, x + w * 0.85, y + h], fill=(30, 30, 34))
    for i in range(4):
        d.rectangle([x + w * (0.22 + i * 0.17), y + h * 0.55, x + w * (0.22 + i * 0.17) + 8,
                     y + h * 0.72], fill=(255, 196, 66))
    fx, fy = x + w * 0.5, y + h * 0.42
    for r, col in [(24, (255, 110, 30)), (16, (255, 170, 60)), (9, (255, 235, 160))]:
        d.ellipse([fx - r, fy - r, fx + r, fy + r], fill=col)


def scene_baseball(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(38, 110, 62))
    d.ellipse([x + w * 0.30, y + h * 0.14, x + w * 0.70, y + h * 0.86], fill=(248, 244, 233),
              outline=(192, 39, 45), width=2)
    d.arc([x + w * 0.34, y + h * 0.20, x + w * 0.58, y + h * 0.80], 90, 270, fill=(192, 39, 45), width=2)
    d.arc([x + w * 0.42, y + h * 0.20, x + w * 0.66, y + h * 0.80], 270, 90, fill=(192, 39, 45), width=2)
    d.text((x + w * 0.72, y + h * 0.62), "$450m", font=font(13, "bold"), fill=(255, 255, 255))


def scene_bike(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(140, 30, 36))
    cx1, cx2, cy = x + w * 0.28, x + w * 0.72, y + h * 0.62
    for cx in (cx1, cx2):
        d.ellipse([cx - 15, cy - 15, cx + 15, cy + 15], outline=(248, 244, 233), width=3)
    d.line([cx1, cy, x + w * 0.45, cy - 18], fill=(248, 244, 233), width=3)
    d.line([x + w * 0.45, cy - 18, cx2, cy], fill=(248, 244, 233), width=3)
    d.line([cx1, cy, x + w * 0.55, cy], fill=(248, 244, 233), width=3)
    d.line([x + w * 0.45, cy - 18, x + w * 0.52, cy - 30], fill=(248, 244, 233), width=3)


def scene_handshake(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(232, 196, 120))
    d.rectangle([x, y + h * 0.55, x + w * 0.5, y + h], fill=(255, 153, 51))
    d.rectangle([x + w * 0.5, y + h * 0.55, x + w, y + h], fill=(220, 20, 60))
    d.ellipse([x + w * 0.32, y + h * 0.30, x + w * 0.68, y + h * 0.78], fill=(248, 244, 233),
              outline=(20, 20, 20), width=2)
    d.text((x + w * 0.44, y + h * 0.44), "DELHI", font=font(11, "bold"), fill=(20, 20, 20))


def scene_capitol(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(31, 58, 110))
    d.rectangle([x + w * 0.15, y + h * 0.55, x + w * 0.85, y + h * 0.62], fill=(248, 244, 233))
    d.rectangle([x + w * 0.42, y + h * 0.38, x + w * 0.58, y + h * 0.55], fill=(248, 244, 233))
    d.ellipse([x + w * 0.40, y + h * 0.18, x + w * 0.60, y + h * 0.44], fill=(248, 244, 233))
    d.rectangle([x + w * 0.22, y + h * 0.62, x + w * 0.78, y + h * 0.92], fill=(248, 244, 233))
    for i in range(4):
        d.line([x + w * (0.28 + i * 0.15), y + h * 0.62, x + w * (0.28 + i * 0.15), y + h * 0.92],
               fill=(31, 58, 110), width=2)


def scene_virus(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(240, 214, 170))
    for cx, cy, r in [(0.30, 0.45, 16), (0.62, 0.35, 12), (0.70, 0.68, 10), (0.38, 0.72, 8)]:
        d.ellipse([x + w * cx - r, y + h * cy - r, x + w * cx + r, y + h * cy + r],
                  fill=(192, 39, 45))
        for a in range(0, 360, 45):
            ex = x + w * cx + math.cos(math.radians(a)) * (r + 5)
            ey = y + h * cy + math.sin(math.radians(a)) * (r + 5)
            d.line([x + w * cx, y + h * cy, ex, ey], fill=(192, 39, 45), width=2)


def scene_planet(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(12, 12, 28))
    for sx, sy in [(0.15, 0.2), (0.8, 0.15), (0.6, 0.8), (0.9, 0.6), (0.3, 0.85)]:
        d.ellipse([x + w * sx - 1, y + h * sy - 1, x + w * sx + 1, y + h * sy + 1],
                  fill=(255, 255, 255))
    d.ellipse([x + w * 0.28, y + h * 0.22, x + w * 0.72, y + h * 0.78], fill=(180, 150, 130))
    for cx, cy, r in [(0.42, 0.40, 5), (0.55, 0.58, 7), (0.62, 0.38, 4)]:
        d.ellipse([x + w * cx - r, y + h * cy - r, x + w * cx + r, y + h * cy + r],
                  fill=(140, 110, 95))
    d.ellipse([x + w * 0.74, y + h * 0.62, x + w * 0.74 + 16, y + h * 0.62 + 16],
              fill=(120, 170, 210))


def scene_euro(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(20, 60, 120))
    for sx in range(6):
        for sy in range(4):
            d.ellipse([x + w * (0.12 + sx * 0.14), y + h * (0.14 + sy * 0.20),
                       x + w * (0.12 + sx * 0.14) + 4, y + h * (0.14 + sy * 0.20) + 4],
                      fill=(255, 210, 60))
    d.text((x + w * 0.36, y + h * 0.30), "€", font=font(30, "bold"), fill=(255, 255, 255))


def scene_cricket(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(46, 125, 60))
    d.rectangle([x + w * 0.08, y + h * 0.62, x + w * 0.92, y + h * 0.70], fill=(232, 210, 170))
    d.line([x + w * 0.30, y + h * 0.62, x + w * 0.55, y + h * 0.12], fill=(200, 160, 110), width=7)
    d.ellipse([x + w * 0.68, y + h * 0.30, x + w * 0.68 + 14, y + h * 0.30 + 14], fill=(192, 39, 45))


SCENES = {
    "globe": scene_globe, "drone": scene_drone, "tanker": scene_tanker,
    "plane": scene_plane, "fire": scene_fire, "baseball": scene_baseball,
    "bike": scene_bike, "handshake": scene_handshake, "capitol": scene_capitol,
    "virus": scene_virus, "planet": scene_planet, "euro": scene_euro,
    "cricket": scene_cricket,
}

REGION_COLORS = {
    "Europe": (31, 78, 121), "Asia": (176, 42, 48), "Middle East": (138, 109, 27),
    "Africa": (46, 125, 50), "Americas": (106, 63, 160), "Oceania": (15, 118, 110),
    "Global": (85, 85, 85),
}

# Rough continent outlines in (lon, lat), drawn equirectangular.
CONTINENTS = [
    [(-168, 66), (-140, 70), (-125, 71), (-110, 68), (-95, 69), (-85, 66), (-80, 73),
     (-70, 62), (-65, 60), (-55, 47), (-60, 45), (-70, 42), (-75, 35), (-80, 32),
     (-81, 26), (-90, 21), (-97, 16), (-94, 12), (-86, 12), (-83, 9), (-79, 8),
     (-95, 15), (-105, 20), (-110, 24), (-117, 32), (-125, 40), (-124, 48),
     (-140, 60), (-155, 58), (-165, 60)],
    [(-79, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12), (-70, -18), (-70, -25),
     (-65, -35), (-68, -45), (-66, -55), (-65, -50), (-62, -40), (-57, -30),
     (-52, -25), (-48, -15), (-41, -8), (-35, -6), (-40, -3), (-44, -2), (-50, 0),
     (-53, 4), (-58, 6), (-62, 9), (-72, 11)],
    [(-10, 36), (-9, 43), (-2, 48), (0, 50), (3, 52), (8, 55), (8, 58), (12, 56),
     (18, 56), (21, 55), (24, 58), (28, 60), (30, 62), (25, 65), (20, 68), (15, 70),
     (10, 64), (5, 60), (-2, 57), (-5, 50), (-9, 43), (-9, 37), (-6, 36), (0, 38),
     (3, 42), (7, 44), (10, 44), (12, 42), (16, 40), (19, 40), (23, 36), (26, 38),
     (28, 41), (23, 40), (19, 42), (15, 44), (12, 45), (8, 44), (3, 43), (-2, 37)],
    [(-6, 35), (0, 36), (10, 37), (11, 34), (20, 32), (30, 31), (34, 28), (35, 23),
     (37, 18), (39, 15), (43, 11), (48, 11), (51, 10), (46, 5), (41, 0), (40, -5),
     (40, -12), (36, -18), (33, -26), (28, -33), (20, -35), (17, -32), (15, -27),
     (12, -18), (13, -12), (12, -6), (9, 4), (4, 6), (-8, 5), (-13, 8), (-17, 12),
     (-17, 15), (-16, 20), (-15, 25), (-13, 28), (-10, 31)],
    [(30, 36), (35, 36), (42, 41), (48, 42), (55, 44), (60, 46), (65, 50), (70, 55),
     (75, 60), (80, 66), (85, 68), (90, 70), (100, 72), (110, 73), (120, 72),
     (130, 72), (140, 72), (150, 70), (160, 66), (170, 67), (178, 65), (170, 60),
     (162, 56), (158, 52), (150, 45), (142, 40), (135, 35), (130, 31), (127, 35),
     (122, 38), (120, 32), (115, 25), (110, 20), (108, 12), (105, 9), (100, 7),
     (98, 10), (94, 16), (92, 21), (89, 22), (86, 20), (80, 15), (77, 8),
     (75, 12), (72, 20), (68, 23), (66, 25), (62, 25), (58, 26), (56, 27),
     (52, 26), (50, 29), (48, 30), (44, 29), (40, 31), (36, 36)],
    [(113, -22), (114, -30), (115, -35), (120, -34), (125, -32), (129, -32),
     (132, -32), (135, -35), (138, -35), (140, -38), (145, -38), (150, -37),
     (153, -32), (153, -27), (150, -23), (146, -19), (142, -15), (142, -11),
     (137, -12), (135, -15), (132, -12), (130, -13), (126, -14), (122, -17),
     (118, -20), (114, -21)],
]


def project(lon, lat, x, y, w, h):
    px = x + (lon + 180.0) / 360.0 * w
    py = y + (75.0 - lat) / 150.0 * h
    return (px, py)


def draw_map(d, x, y, w, h, pins):
    d.rectangle([x, y, x + w, y + h], fill=MAP_BG)
    for poly in CONTINENTS:
        pts = [project(lon, lat, x, y, w, h) for lon, lat in poly]
        d.polygon(pts, fill=LAND, outline=LAND_LINE)
    # Indonesia islands as small blobs
    for lon, lat, r in [(100, -2, 4), (110, -6, 5), (120, -3, 4), (130, -3, 4), (140, -4, 3)]:
        px, py = project(lon, lat, x, y, w, h)
        d.ellipse([px - r, py - r / 2, px + r, py + r / 2], fill=LAND, outline=LAND_LINE)
    for num, (lon, lat) in pins:
        px, py = project(lon, lat, x, y, w, h)
        if num <= 13:
            r = 9
            d.ellipse([px - r, py - r, px + r, py + r], fill=RED, outline=(255, 255, 255), width=1)
            t = str(num)
            tw = d.textlength(t, font=font(9, "bold"))
            d.text((px - tw / 2, py - 5), t, font=font(9, "bold"), fill=(255, 255, 255))
        else:
            r = 6
            d.ellipse([px - r, py - r, px + r, py + r], fill=(31, 58, 110),
                      outline=(255, 255, 255), width=1)
            t = str(num)
            tw = d.textlength(t, font=font(7, "bold"))
            d.text((px - tw / 2, py - 4), t, font=font(7, "bold"), fill=(255, 255, 255))


def label_banner(d, x, y, text, fnt):
    tw = d.textlength(text, font=fnt) + 12
    d.rectangle([x, y, x + tw, y + 18], fill=RED)
    d.text((x + 6, y + 3), text, font=fnt, fill=(255, 255, 255))
    return tw


def render(leads, mediums, briefs, stats, regions, date_check, footer_note):
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    M = 14
    CW = W - 2 * M

    # --- masthead
    d.text((M, 8), "THE WORLD IN ONE DAY", font=font(15, "bold"), fill=RED)
    right = "35 STORIES  ·  7 REGIONS  ·  EVERY ONE DATED MONDAY 23 NOVEMBER 2026"
    rw = d.textlength(right, font=font(12, "semibold"))
    d.text((W - M - rw, 10), right, font=font(12, "semibold"), fill=INK)
    d.line([M, 34, W - M, 34], fill=RULE, width=2)

    # --- giant date
    center(d, W / 2, 38, "Monday 23 November 2026", font(58, "bold"))
    center(d, W / 2, 106,
           "COP31 collapses with no deal  ·  Drone flattens flats near Kyiv  ·  Three tankers hit in Hormuz",
           font(16, "medium"), fill=RED)
    d.line([M, 132, W - M, 132], fill=RULE, width=1)

    # --- stat strip: 6 numbers
    sy, sh = 138, 52
    cell = CW / 6
    for i, (num, label) in enumerate(stats):
        cx = M + i * cell
        if i:
            d.line([cx, sy + 4, cx, sy + sh - 4], fill=(200, 190, 170), width=1)
        center(d, cx + cell / 2, sy, num, font(27, "bold"))
        draw_wrapped(d, cx + 8, sy + 32, label, font(10.5, "regular"), cell - 16,
                     fill=MUTED, lh=12, max_lines=2)
    d.line([M, 196, W - M, 196], fill=RULE, width=1)

    # --- region strip
    ry = 202
    total_w = sum(d.textlength(f"{name} {n}", font=font(12, "bold")) + 18 for name, n in regions)
    gap = (CW - total_w) / (len(regions) - 1)
    rx = M
    for name, n in regions:
        tw = d.textlength(f"{name} {n}", font=font(12, "bold")) + 18
        d.rectangle([rx, ry, rx + tw, ry + 20], fill=REGION_COLORS[name])
        d.text((rx + 9, ry + 4), f"{name} {n}", font=font(12, "bold"), fill=(255, 255, 255))
        rx += tw + gap

    # --- 3 lead cards
    ly, lh = 230, 216
    lw = (CW - 20) / 3
    for i, s in enumerate(leads):
        x = M + i * (lw + 10)
        d.rectangle([x, ly, x + lw, ly + lh], fill=CARD_BG, outline=(210, 200, 180), width=1)
        SCENES[s["scene"]](d, x + 1, ly + 1, lw - 2, 112)
        label_banner(d, x + 1, ly + 1, s["banner"], font(12, "bold"))
        ty = ly + 120
        d.text((x + 8, ty), f"{s['num']}  {s['tag']}", font=font(11, "bold"), fill=RED)
        ty += 15
        ty = draw_wrapped(d, x + 8, ty, s["headline"], font(18, "bold"), lw - 16, lh=21, max_lines=2)
        ty += 2
        ty = draw_wrapped(d, x + 8, ty, s["deck"], font(12, "regular"), lw - 16, lh=15, max_lines=2)
        d.text((x + 8, ly + lh - 16), f"({s['source']})", font=font(10, "regular"), fill=MUTED)

    # --- 10 medium cards: 5 x 2
    my, mh = 456, 128
    mw = (CW - 4 * 8) / 5
    for i, s in enumerate(mediums):
        col, row = i % 5, i // 5
        x = M + col * (mw + 8)
        yy = my + row * (mh + 8)
        d.rectangle([x, yy, x + mw, yy + mh], fill=CARD_BG, outline=(210, 200, 180), width=1)
        SCENES[s["scene"]](d, x + 1, yy + 1, mw - 2, 44)
        label_banner(d, x + 1, yy + 1, s["banner"], font(9, "bold"))
        ty = yy + 50
        d.text((x + 6, ty), f"{s['num']}  {s['tag']}", font=font(9, "bold"), fill=RED)
        ty += 12
        ty = draw_wrapped(d, x + 6, ty, s["headline"], font(13.5, "bold"), mw - 12, lh=15, max_lines=2)
        ty = draw_wrapped(d, x + 6, ty, s["deck"], font(10.5, "regular"), mw - 12, lh=12, max_lines=2)
        d.text((x + 6, yy + mh - 13), f"({s['source']})", font=font(9, "regular"), fill=MUTED)

    # --- bottom band: map + also-on list
    by = 730
    d.text((M, by), "WHERE IT HAPPENED", font=font(13, "bold"), fill=INK)
    d.text((M + 300, by), "ALSO ON MONDAY 23 NOVEMBER  —  22 MORE STORIES",
           font=font(13, "bold"), fill=INK)
    map_x, map_y, map_w, map_h = M, by + 20, 284, 138
    pins = [(s["num"], s["pin"]) for s in leads + mediums if s.get("pin")]
    pins += [(b["num"], b["pin"]) for b in briefs if b.get("pin")]
    draw_map(d, map_x, map_y, map_w, map_h, pins)
    d.text((M, map_y + map_h + 4),
           "Each number is that story on this page.",
           font=font(9.5, "regular"), fill=MUTED)
    # brief list, two columns of 11
    bx = M + 300
    col_w = (W - M - bx - 10) / 2
    for i, b in enumerate(briefs):
        col = i // 11
        row = i % 11
        x = bx + col * (col_w + 10)
        yy = by + 20 + row * 14
        line = f"{b['num']}  {b['headline']}  ({b['source']})"
        fnt = font(11.5, "regular")
        if d.textlength(line, font=fnt) > col_w:
            fnt = font(10.5, "regular")
        d.text((x, yy), line, font=fnt, fill=INK)

    # --- date check
    dy = 906
    d.rectangle([M, dy, W - M, dy + 58], outline=RED, width=2)
    d.text((M + 8, dy + 6), "DATE CHECK", font=font(12, "bold"), fill=RED)
    draw_wrapped(d, M + 96, dy + 6, date_check, font(11.5, "regular"), W - M - 104, lh=14)

    # --- footer
    fy = 976
    d.line([M, fy - 6, W - M, fy - 6], fill=RULE, width=1)
    d.text((M, fy), footer_note, font=font(11, "regular"), fill=INK)
    rt = "Sources named beside each story  ·  original drawings"
    rw = d.textlength(rt, font=font(10, "regular"))
    d.text((W - M - rw, fy + 1), rt, font=font(10, "regular"), fill=MUTED)
    return img
