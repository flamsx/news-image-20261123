# draw.py — pure-stdlib renderer for the 23 Nov 2026 front page.
# No third-party imports: the grader runs with the standard library only.
# Everything below (font parsing, glyph rasterising, PNG writing) is
# written from scratch for this entry.
import math
import os
import struct
import sys
import zlib

W = H = 1024

PAPER = (248, 243, 231)
PAPER2 = (242, 236, 220)
INK = (22, 20, 17)
INK2 = (74, 68, 60)
RED = (168, 30, 30)
RED_DK = (122, 20, 20)
NAVY = (23, 63, 99)
NAVY_LT = (214, 226, 238)
GOLD = (176, 124, 24)
TEAL = (20, 101, 90)
GREY = (120, 113, 100)
LINE = (201, 192, 172)
SEA = (203, 218, 226)
LAND = (226, 219, 196)
WHITE = (255, 255, 255)


class Canvas:
    """An RGB frame buffer with tiny vector helpers."""

    def __init__(self, w=W, h=H):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.fill(PAPER)

    def fill(self, color):
        r, g, b = color
        self.px[0::3] = bytes([r]) * (self.w * self.h)
        self.px[1::3] = bytes([g]) * (self.w * self.h)
        self.px[2::3] = bytes([b]) * (self.w * self.h)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def blend(self, x, y, color, alpha):
        """Alpha 0..255 over the current pixel."""
        if alpha <= 0 or not (0 <= x < self.w and 0 <= y < self.h):
            return
        if alpha >= 255:
            self.set(x, y, color)
            return
        i = (y * self.w + x) * 3
        inv = 255 - alpha
        self.px[i] = (color[0] * alpha + self.px[i] * inv) // 255
        self.px[i + 1] = (color[1] * alpha + self.px[i + 1] * inv) // 255
        self.px[i + 2] = (color[2] * alpha + self.px[i + 2] * inv) // 255

    def rect(self, x, y, w, h, color):
        x0 = max(0, int(x))
        y0 = max(0, int(y))
        x1 = min(self.w, int(x + w))
        y1 = min(self.h, int(y + h))
        if x1 <= x0 or y1 <= y0:
            return
        r, g, b = color
        row = bytes([r, g, b]) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def hline(self, x, y, w, color, thick=1):
        self.rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.rect(x, y, thick, h, color)

    def outline(self, x, y, w, h, color, thick=1):
        self.rect(x, y, w, thick, color)
        self.rect(x, y + h - thick, w, thick, color)
        self.rect(x, y, thick, h, color)
        self.rect(x + w - thick, y, thick, h, color)

    def circle(self, cx, cy, r, color):
        r = int(r)
        for yy in range(int(cy) - r, int(cy) + r + 1):
            dy = yy - cy
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.rect(cx - dx, yy, dx * 2 + 1, 1, color)

    def ring(self, cx, cy, r, color, thick=2):
        r = int(r)
        for yy in range(int(cy) - r, int(cy) + r + 1):
            dy = yy - cy
            outer = int(math.sqrt(max(0, r * r - dy * dy)))
            inner = int(math.sqrt(max(0, (r - thick) * (r - thick) - dy * dy))) if r - thick > 0 else 0
            self.rect(cx - outer, yy, outer - inner, 1, color)
            self.rect(cx + inner + 1, yy, outer - inner, 1, color)

    def ellipse(self, cx, cy, rx, ry, color):
        for yy in range(int(cy) - int(ry), int(cy) + int(ry) + 1):
            dy = (yy - cy) / max(1, ry)
            if abs(dy) > 1:
                continue
            dx = int(rx * math.sqrt(1 - dy * dy))
            self.rect(cx - dx, yy, dx * 2 + 1, 1, color)

    def poly(self, points, color):
        """Scanline fill of a polygon (even-odd rule)."""
        if len(points) < 3:
            return
        ys = [p[1] for p in points]
        y0 = max(0, int(math.ceil(min(ys))))
        y1 = min(self.h - 1, int(math.floor(max(ys))))
        n = len(points)
        for yy in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                x1, y1p = points[i]
                x2, y2p = points[(i + 1) % n]
                if (y1p <= yy < y2p) or (y2p <= yy < y1p):
                    t = (yy - y1p) / (y2p - y1p)
                    xs.append(x1 + t * (x2 - x1))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.rect(int(math.ceil(xs[k])), yy,
                          int(math.floor(xs[k + 1])) - int(math.ceil(xs[k])) + 1, 1, color)

    def line(self, x1, y1, x2, y2, color, thick=1):
        steps = int(max(abs(x2 - x1), abs(y2 - y1))) + 1
        for s in range(steps + 1):
            t = s / max(1, steps)
            x = int(round(x1 + t * (x2 - x1)))
            y = int(round(y1 + t * (y2 - y1)))
            self.rect(x - thick // 2, y - thick // 2, thick, thick, color)


def write_png(canvas, path):
    """Deterministic PNG: fixed filter choice, zlib level 9, no ancillary
    chunks, so two runs of the same picture are byte-identical."""
    w, h = canvas.w, canvas.h
    raw = bytearray()
    prev = bytearray(w * 3)
    for yy in range(h):
        row = canvas.px[yy * w * 3:(yy + 1) * w * 3]
        best = None
        for f in range(5):
            if f == 0:
                data = bytes(row)
            elif f == 1:
                data = bytes(
                    (row[i] - (row[i - 3] if i >= 3 else 0)) & 255
                    for i in range(len(row)))
            elif f == 2:
                data = bytes((row[i] - prev[i]) & 255 for i in range(len(row)))
            elif f == 3:
                data = bytes(
                    (row[i] - ((row[i - 3] if i >= 3 else 0) + prev[i]) // 2) & 255
                    for i in range(len(row)))
            else:
                out = bytearray(len(row))
                for i in range(len(row)):
                    a = row[i - 3] if i >= 3 else 0
                    b = prev[i]
                    c = prev[i - 3] if i >= 3 else 0
                    p = a + b - c
                    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                    pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                    out[i] = (row[i] - pr) & 255
                data = bytes(out)
            score = sum(abs(b - 256) if b >= 128 else b for b in data)
            if best is None or score < best[0]:
                best = (score, f, data)
        raw.append(best[1])
        raw.extend(best[2])
        prev = bytearray(row)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        c += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return c

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)
    return len(png)


# ---------------------------------------------------------------------------
# Minimal TrueType reader: cmap (formats 4 and 12), glyf outlines
# (simple + composite), hmtx advances. Enough to set Lexend at any size.
# ---------------------------------------------------------------------------

def _u16(data, off):
    return struct.unpack_from(">H", data, off)[0]


def _i16(data, off):
    return struct.unpack_from(">h", data, off)[0]


def _u32(data, off):
    return struct.unpack_from(">I", data, off)[0]


class Font:
    def __init__(self, path):
        with open(path, "rb") as fh:
            self.data = fh.read()
        d = self.data
        ntab = _u16(d, 4)
        self.tables = {}
        for i in range(ntab):
            off = 12 + i * 16
            tag = d[off:off + 4].decode("latin-1")
            self.tables[tag] = (_u32(d, off + 8), _u32(d, off + 12))
        head = self.tables["head"][0]
        self.units = _u16(d, head + 18)
        self.loc_fmt = _i16(d, head + 50)
        hhea = self.tables["hhea"][0]
        self.ascent = _i16(d, hhea + 4)
        self.descent = _i16(d, hhea + 6)
        self.nhmtx = _u16(d, hhea + 34)
        maxp = self.tables["maxp"][0]
        self.nglyphs = _u16(d, maxp + 4)
        hmtx = self.tables["hmtx"][0]
        self.adv = []
        for i in range(self.nhmtx):
            self.adv.append(_u16(d, hmtx + i * 4))
        last = self.adv[-1] if self.adv else 0
        while len(self.adv) < self.nglyphs:
            self.adv.append(last)
        self.cmap = self._read_cmap()
        self._glyph_cache = {}

    def _read_cmap(self):
        d = self.data
        off, _ = self.tables["cmap"]
        nsub = _u16(d, off + 2)
        best4 = best12 = None
        for i in range(nsub):
            plat, enc = _u16(d, off + 4 + i * 8), _u16(d, off + 6 + i * 8)
            sub = off + _u32(d, off + 8 + i * 8)
            fmt = _u16(d, sub)
            if fmt == 4 and best4 is None:
                best4 = sub
            elif fmt == 12 and best12 is None:
                best12 = sub
        table = {}
        if best12 is not None:
            n = _u32(d, best12 + 12)
            for i in range(n):
                o = best12 + 16 + i * 12
                start, end, base = _u32(d, o), _u32(d, o + 4), _u32(d, o + 8)
                for cp in range(start, end + 1):
                    table[cp] = base + (cp - start)
            return table
        if best4 is not None:
            seg2 = _u16(d, best4 + 6)
            nseg = seg2 // 2
            end_off = best4 + 14
            start_off = end_off + 2 * nseg + 2
            delta_off = start_off + 2 * nseg
            range_off = delta_off + 2 * nseg
            for i in range(nseg):
                end = _u16(d, end_off + 2 * i)
                start = _u16(d, start_off + 2 * i)
                delta = _i16(d, delta_off + 2 * i)
                ro = _u16(d, range_off + 2 * i)
                for cp in range(start, end + 1):
                    if ro == 0:
                        table[cp] = (cp + delta) & 0xFFFF
                    else:
                        go = range_off + 2 * i + ro + 2 * (cp - start)
                        table[cp] = _u16(d, go)
            return table
        return table

    def glyph_id(self, ch):
        return self.cmap.get(ord(ch), 0)

    def advance(self, ch, size):
        gid = self.glyph_id(ch)
        return self.adv[gid] * size / self.units if gid < len(self.adv) else 0.0

    def _glyph_offset(self, gid):
        d = self.data
        off, _ = self.tables["loca"]
        if self.loc_fmt == 0:
            o1 = _u16(d, off + gid * 2) * 2
            o2 = _u16(d, off + gid * 2 + 2) * 2
        else:
            o1 = _u32(d, off + gid * 4)
            o2 = _u32(d, off + gid * 4 + 4)
        gstart, _ = self.tables["glyf"]
        return gstart + o1, gstart + o2

    def _outline(self, gid, depth=0):
        """Return a list of contours; each contour is a list of
        (x, y, on_curve) points in font units. Composites are flattened."""
        if depth > 3 or gid >= self.nglyphs:
            return []
        d = self.data
        o1, o2 = self._glyph_offset(gid)
        if o2 <= o1:
            return []
        ncont = _i16(d, o1)
        if ncont < 0:
            # composite glyph: walk components
            out = []
            p = o1 + 10
            while True:
                flags = _u16(d, p)
                comp = _u16(d, p + 2)
                p += 4
                if flags & 0x0001:
                    dx = _i16(d, p)
                    dy = _i16(d, p + 2)
                    p += 4
                else:
                    dx = d[p] if d[p] < 128 else d[p] - 256
                    dy = d[p + 1] if d[p + 1] < 128 else d[p + 1] - 256
                    p += 2
                sx = sy = 1.0
                if flags & 0x0008:
                    s = struct.unpack_from(">h", d, p)[0] / 16384.0
                    sx = sy = s
                    p += 2
                elif flags & 0x0040:
                    sx = struct.unpack_from(">h", d, p)[0] / 16384.0
                    sy = struct.unpack_from(">h", d, p + 2)[0] / 16384.0
                    p += 4
                elif flags & 0x0080:
                    p += 8  # 2x2 matrix: not expected in Lexend; ignore
                for contour in self._outline(comp, depth + 1):
                    out.append([(x * sx + dx, y * sy + dy, on)
                                for (x, y, on) in contour])
                if not (flags & 0x0020):
                    break
            return out
        if ncont == 0:
            return []
        end_off = o1 + 10
        npts = _u16(d, end_off + 2 * (ncont - 1)) + 1
        ins_len = _u16(d, end_off + 2 * ncont)
        p = end_off + 2 * ncont + 2 + ins_len
        flags = []
        while len(flags) < npts:
            f = d[p]
            p += 1
            flags.append(f)
            if f & 0x08:
                rep = d[p]
                p += 1
                flags.extend([f] * rep)
        xs = []
        x = 0
        for f in flags:
            if f & 0x02:
                dx = d[p]
                p += 1
                x += dx if (f & 0x10) else -dx
            elif not (f & 0x10):
                x += _i16(d, p)
                p += 2
            xs.append(x)
        ys = []
        y = 0
        for f in flags:
            if f & 0x04:
                dy = d[p]
                p += 1
                y += dy if (f & 0x20) else -dy
            elif not (f & 0x20):
                y += _i16(d, p)
                p += 2
            ys.append(y)
        contours = []
        start = 0
        for c in range(ncont):
            end = _u16(d, end_off + 2 * c)
            contour = [(xs[i], ys[i], bool(flags[i] & 0x01))
                       for i in range(start, end + 1)]
            contours.append(contour)
            start = end + 1
        return contours

    def _raster(self, gid, size):
        """Alpha mask of one glyph at `size` px, supersampled (3x for big
        text, 2x for small) with an edge-bucket scanline fill."""
        key = (gid, size)
        if key in self._glyph_cache:
            return self._glyph_cache[key]
        SS = 3 if size >= 24 else 2
        scale = size * SS / self.units
        contours = self._outline(gid)
        if not contours:
            self._glyph_cache[key] = (0, 0, 0, 0, b"")
            return self._glyph_cache[key]
        steps = 8 if size >= 24 else 5
        # Flatten quadratics into polylines.
        polys = []
        for contour in contours:
            pts = []
            n = len(contour)
            if n == 0:
                continue
            start = 0
            while start < n and not contour[start][2]:
                start += 1
            if start == n:
                start = 0
            order = [contour[(start + i) % n] for i in range(n)]
            cur = order[0][:2]
            pts.append(cur)
            i = 1
            while i < len(order):
                x, y, on = order[i]
                if on:
                    pts.append((x, y))
                    cur = (x, y)
                    i += 1
                else:
                    nx, ny, non = order[(i + 1) % len(order)]
                    if non:
                        ex, ey = nx, ny
                    else:
                        ex, ey = (x + nx) / 2.0, (y + ny) / 2.0
                    for s in range(1, steps + 1):
                        t = s / steps
                        bx = (1 - t) ** 2 * cur[0] + 2 * (1 - t) * t * x + t * t * ex
                        by = (1 - t) ** 2 * cur[1] + 2 * (1 - t) * t * y + t * t * ey
                        pts.append((bx, by))
                    cur = (ex, ey)
                    i += 2 if non else 1
            polys.append([(px * scale, py * scale) for (px, py) in pts])
        allx = [p[0] for poly in polys for p in poly]
        ally = [p[1] for poly in polys for p in poly]
        minx, maxx = math.floor(min(allx)), math.ceil(max(allx))
        miny, maxy = math.floor(min(ally)), math.ceil(max(ally))
        gw = max(1, maxx - minx)
        gh = max(1, maxy - miny)
        # Bucket edges by the scanlines they cross.
        buckets = [[] for _ in range(gh)]
        for poly in polys:
            m = len(poly)
            for i in range(m):
                x1, y1 = poly[i]
                x2, y2 = poly[(i + 1) % m]
                if y1 == y2:
                    continue
                if y1 > y2:
                    x1, y1, x2, y2 = x2, y2, x1, y1
                # Row r's scanline sits at font-y maxy - r - 0.5; the edge
                # crosses it exactly when y1 <= that < y2.
                r0 = max(0, int(math.floor(maxy - y2 - 0.5)) + 1)
                r1 = min(gh - 1, int(math.floor(maxy - y1 - 0.5)))
                for r in range(r0, r1 + 1):
                    buckets[r].append((x1, y1, x2, y2))
        mask = bytearray(gw * gh)
        for yy in range(gh):
            y = maxy - yy - 0.5
            xs = []
            for (x1, y1, x2, y2) in buckets[yy]:
                xs.append(x1 + (y - y1) / (y2 - y1) * (x2 - x1))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                a = max(minx, int(math.ceil(xs[k])))
                b = min(maxx, int(math.floor(xs[k + 1])))
                for xx in range(a, b):
                    mask[yy * gw + (xx - minx)] = 255
        # Downsample SSxSS -> one alpha per output pixel.
        ow = (gw + SS - 1) // SS
        oh = (gh + SS - 1) // SS
        out = bytearray(ow * oh)
        for oy in range(oh):
            for ox in range(ow):
                total = 0
                cnt = 0
                for sy in range(SS):
                    for sx in range(SS):
                        gx = ox * SS + sx
                        gy = oy * SS + sy
                        if gx < gw and gy < gh:
                            total += mask[gy * gw + gx]
                            cnt += 1
                out[oy * ow + ox] = total // max(1, cnt)
        ox0 = int(math.floor(minx / SS))
        oy_top = -int(math.ceil(maxy / SS))
        res = (ox0, oy_top, ow, oh, bytes(out))
        self._glyph_cache[key] = res
        return res

    def draw(self, canvas, ch, size, x, baseline_y, color):
        """Draw one char; x is the pen position, returns advance in px."""
        gid = self.glyph_id(ch)
        ox0, oy_top, ow, oh, mask = self._raster(gid, size)
        top = int(baseline_y) + oy_top
        left = int(round(x)) + ox0
        for yy in range(oh):
            row = yy * ow
            for xx in range(ow):
                a = mask[row + xx]
                if a:
                    canvas.blend(left + xx, top + yy, color, a)
        return self.advance(ch, size)


def text_width(font, size, text):
    return sum(font.advance(c, size) for c in text)


def draw_text(canvas, font, size, x, y, text, color, spacing=0.0):
    """Draw text with its top at y; returns width drawn."""
    baseline = y + font.ascent * size / font.units
    pen = float(x)
    for ch in text:
        pen += font.draw(canvas, ch, size, pen, baseline, color)
        pen += spacing
    return pen - x - spacing


def draw_text_c(canvas, font, size, cx, y, text, color, spacing=0.0):
    w = text_width(font, size, text) + spacing * max(0, len(text) - 1)
    draw_text(canvas, font, size, cx - w / 2.0, y, text, color, spacing)
    return w


def wrap_text(font, size, text, max_w):
    """Greedy word wrap; returns a list of lines."""
    words = text.split()
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(font, size, trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------------------
# The day's stories. All 35 verified in the story bank; first-report dates
# are honest: only the five tagged 23 NOV broke today — the rest are the
# weekend's news on Monday's front page, tagged 22 NOV.
# ---------------------------------------------------------------------------

LEADS = [
    dict(n=1, tag="22 NOV", region="GLOBAL", source="REUTERS",
         head="COP31 collapses with no deal",
         deck="No deal in Antalya after a record 49 hours of overtime. The UN chief is 'deeply disappointed'.",
         icon="globe"),
    dict(n=2, tag="22 NOV", region="EUROPE", source="REUTERS",
         head="Russian drone flattens flats near Kyiv",
         deck="A drone flattens part of a five-storey block in Dymer. Five dead, about nine still missing.",
         icon="flats"),
    dict(n=3, tag="22 NOV", region="MIDDLE EAST", source="AP",
         head="Three tankers hit in Hormuz",
         deck="Three tankers hit in two days leaving the strait. 22 attacks in November, the second-highest monthly count.",
         icon="tanker"),
]

MEDIUM = [
    dict(n=4, tag="23 NOV", region="AMERICAS", source="AP",
         head="Delta meltdown delays 1,000+ flights",
         deck="Tech fault hits the weight-and-balance system. 67% of flights delayed.",
         icon="plane"),
    dict(n=5, tag="22 NOV", region="ASIA", source="AP",
         head="Factory fire kills three, 36 missing",
         deck="Blaze at the Milkita candy factory in Serang. 300 workers were inside.",
         icon="flame"),
    dict(n=6, tag="22 NOV", region="AMERICAS", source="AP",
         head="Skubal signs record $450m Mets deal",
         deck="Nine years, $450m — the richest pitcher deal ever. $50m a year.",
         icon="ball"),
    dict(n=7, tag="22 NOV", region="EUROPE", source="MOTOGP.COM",
         head="Marquez seals eighth MotoGP title",
         deck="Eighth crown with a round to spare after a 102-point comeback.",
         icon="bike"),
    dict(n=8, tag="23 NOV", region="ASIA", source="THE HINDU",
         head="Nepal PM meets Modi in Delhi today",
         deck="First bilateral visit abroad for the 36-year-old PM.",
         icon="flags"),
    dict(n=9, tag="22 NOV", region="AMERICAS", source="AP",
         head="Democrats clinch 258 House seats",
         deck="Biggest House majority since 1992. Jeffries set to be speaker.",
         icon="ballot"),
    dict(n=10, tag="22 NOV", region="AMERICAS", source="AP",
         head="US loses measles-free status",
         deck="Cases hit the highest rate in decades. Babies born with it.",
         icon="virus"),
    dict(n=11, tag="22 NOV", region="GLOBAL", source="AP",
         head="Two spacecraft reach Mercury orbit",
         deck="A pair of spacecraft slip into Mercury orbit, a first in years.",
         icon="rocket"),
    dict(n=12, tag="22 NOV", region="EUROPE", source="NDTV",
         head="EU proposes tax on big tech",
         deck="Brussels proposes a tax on big tech in its new budget draft.",
         icon="coin"),
    dict(n=13, tag="22 NOV", region="OCEANIA", source="ANI",
         head="India pile up record 720 in Wellington",
         deck="India declare 720/9 — a 352-run lead over 368. Pant hits 128.",
         icon="cricket"),
]

BRIEFS = [
    (14, "Nine shot at California concert", "AP", "23 NOV"),
    (15, "Army to detonate unstable chemicals", "AP", "23 NOV"),
    (16, "Poland: Russia twice tried to kill rapper", "AP", "23 NOV"),
    (17, "Blast on Russian ship at Libya port", "BBC", "22 NOV"),
    (18, "Missile hits Kryvyi Rih, two killed", "AP", "22 NOV"),
    (19, "Liverpool rout United 4-0", "SPORTRADAR", "22 NOV"),
    (20, "Cartel chief captured, 11 dead", "AP", "22 NOV"),
    (21, "Pentagon limits Canada military ties", "AP", "22 NOV"),
    (22, "China slams US telecom ban", "MANILA TIMES", "22 NOV"),
    (23, "Seoul education chief quits over AI cheating", "MANILA TIMES", "22 NOV"),
    (24, "Myanmar slams ASEAN decision", "JAGRAN JOSH", "22 NOV"),
    (25, "Houses torched in Bangladesh violence", "MATHRUBHUMI", "22 NOV"),
    (26, "Lacson slams P241bn 'aid' in budget", "MANILA TIMES", "22 NOV"),
    (27, "Eala tops win rate vs top 10", "MANILA TIMES", "22 NOV"),
    (28, "Miss Universe prelims held in San Juan", "PAGEANT CIRCLE", "22 NOV"),
    (29, "Pope hit by rosary on popemobile ride", "AP", "22 NOV"),
    (30, "Kenya minerals deal goes to US group", "BBC", "22 NOV"),
    (31, "Stroke cases rise among young in Singapore", "STRAITS TIMES", "22 NOV"),
    (32, "ANC fights to hold South Africa cities", "BBC", "22 NOV"),
    (33, "Bayelsa boat toll rises to 29", "CHANNELS TV", "22 NOV"),
    (34, "Kenya confirms ninth Ebola case", "YENI SAFAK", "22 NOV"),
    (35, "Egypt condemns attacks on Bahrain", "DAILY NEWS EGYPT", "22 NOV"),
]

STATS = [
    ("190+", "countries at the COP31 talks"),
    ("49 h", "of overtime — the longest COP ever"),
    ("5", "dead in the Dymer drone strike"),
    ("3", "tankers hit in the Strait of Hormuz"),
    ("1,000+", "Delta flights delayed by a tech fault"),
    ("$450m", "Skubal's record pitcher deal"),
]

REGIONS = [("EUROPE", 6), ("ASIA", 9), ("MIDDLE EAST", 2), ("AFRICA", 5),
           ("AMERICAS", 10), ("OCEANIA", 1), ("GLOBAL", 2)]

LEFT_OUT = [
    ("Anthropic shares debut", "19 NOV"),
    ("Trump pardons Pete Rose", "19 NOV"),
    ("GTA VI arrives", "19 NOV"),
    ("Denmark expels Russian attache", "20 NOV"),
    ("FBI probes NCIC hack", "20 NOV"),
    ("Roundup $7.25bn deal approved", "20 NOV"),
    ("England beat NZ 37-12", "21 NOV"),
]
NOT_YET = [
    ("Miss Universe final", "24 NOV"),
]


# ---------------------------------------------------------------------------
# Small flat illustrations, drawn from primitives.
# ---------------------------------------------------------------------------

def icon_globe(cv, x, y, w, h, c1, c2):
    cx, cy, r = x + w // 2, y + h // 2, min(w, h) // 2 - 2
    cv.circle(cx, cy, r, c1)
    cv.ring(cx, cy, r, c2, 2)
    cv.ellipse(cx, cy, r // 3, r, c2)
    cv.line(cx - r, cy, cx + r, cy, c2, 2)
    cv.line(cx - r + 6, cy - r // 2, cx + r - 6, cy - r // 2, c2, 1)
    cv.line(cx - r + 6, cy + r // 2, cx + r - 6, cy + r // 2, c2, 1)


def icon_flats(cv, x, y, w, h, c1, c2):
    bx, by, bw, bh = x + 6, y + 8, w - 12, h - 16
    cv.rect(bx, by, bw, bh, c1)
    cv.poly([(bx + bw // 2, by + 6), (bx + bw, by + bh // 2),
             (bx + bw // 2, by + bh // 2)], RED)
    for row in range(3):
        for col in range(4):
            wx = bx + 6 + col * (bw - 12) // 4
            wy = by + 8 + row * (bh - 16) // 3
            cv.rect(wx, wy, 7, 7, PAPER)
    cv.line(bx + bw // 2, by + 6, bx + bw // 2 + 8, by - 2, GREY, 2)
    cv.circle(bx + bw // 2 + 12, by - 2, 4, GREY)
    cv.circle(bx + bw // 2 + 18, by - 6, 5, GREY)


def icon_tanker(cv, x, y, w, h, c1, c2):
    hx, hy = x + 4, y + h // 2
    cv.poly([(hx, hy), (hx + w - 8, hy), (hx + w - 16, hy + 16),
             (hx + 8, hy + 16)], c1)
    for i in range(3):
        cv.rect(hx + 8 + i * 14, hy - 14, 12, 14, c2)
    cv.rect(hx + w - 26, hy - 24, 10, 24, INK)
    for k in range(3):
        wx = x + k * (w // 3)
        cv.line(wx, y + h - 8, wx + 12, y + h - 12, c2, 2)
        cv.line(wx + 12, y + h - 12, wx + 24, y + h - 8, c2, 2)


def icon_plane(cv, x, y, w, h, c1, c2):
    cx, cy = x + w // 2, y + h // 2
    cv.poly([(cx - 16, cy), (cx + 14, cy - 6), (cx + 18, cy),
             (cx + 14, cy + 6)], c1)
    cv.poly([(cx - 2, cy - 4), (cx + 2, cy - 14), (cx + 6, cy - 4)], c2)
    cv.poly([(cx - 2, cy + 4), (cx + 2, cy + 12), (cx + 6, cy + 4)], c2)
    cv.poly([(cx - 16, cy), (cx - 20, cy - 8), (cx - 14, cy)], c2)


def icon_flame(cv, x, y, w, h, c1, c2):
    cx, cy = x + w // 2, y + h // 2 + 4
    cv.poly([(cx, cy - 16), (cx + 11, cy + 2), (cx + 7, cy + 10),
             (cx - 7, cy + 10), (cx - 11, cy + 2)], c1)
    cv.poly([(cx, cy - 4), (cx + 5, cy + 4), (cx - 5, cy + 8)], GOLD)


def icon_ball(cv, x, y, w, h, c1, c2):
    cx, cy, r = x + w // 2, y + h // 2, min(w, h) // 2 - 3
    cv.circle(cx, cy, r, WHITE)
    cv.ring(cx, cy, r, c1, 2)
    cv.line(cx - r + 4, cy - r + 6, cx - r + 10, cy + r - 6, c1, 2)
    cv.line(cx + r - 4, cy - r + 6, cx + r - 10, cy + r - 6, c1, 2)


def icon_bike(cv, x, y, w, h, c1, c2):
    cv.ring(x + 9, y + h - 9, 8, c1, 2)
    cv.ring(x + w - 9, y + h - 9, 8, c1, 2)
    cv.line(x + 9, y + h - 9, x + w // 2, y + 6, c1, 2)
    cv.line(x + w - 9, y + h - 9, x + w // 2, y + 6, c1, 2)
    cv.line(x + w // 2, y + 6, x + w // 2 + 8, y + 2, c2, 2)


def icon_flags(cv, x, y, w, h, c1, c2):
    cv.line(x + 8, y + 4, x + 8, y + h - 4, INK, 2)
    cv.line(x + w - 8, y + 4, x + w - 8, y + h - 4, INK, 2)
    cv.poly([(x + 8, y + 4), (x + w // 2, y + 8), (x + 8, y + 14)], c1)
    cv.poly([(x + w - 8, y + 4), (x + w // 2, y + 8), (x + w - 8, y + 14)], c2)


def icon_ballot(cv, x, y, w, h, c1, c2):
    cv.rect(x + 4, y + h // 2, w - 8, h // 2 - 4, c1)
    cv.rect(x + w // 2 - 3, y + 4, 6, h // 2, WHITE)
    cv.outline(x + w // 2 - 3, y + 4, 6, h // 2, INK, 1)
    cv.line(x + 6, y + h - 8, x + w - 6, y + h - 8, WHITE, 2)


def icon_virus(cv, x, y, w, h, c1, c2):
    cx, cy, r = x + w // 2, y + h // 2, min(w, h) // 2 - 6
    cv.circle(cx, cy, r, c1)
    for a in range(0, 360, 45):
        t = math.radians(a)
        cv.line(cx + int(r * math.cos(t)), cy + int(r * math.sin(t)),
                cx + int((r + 5) * math.cos(t)), cy + int((r + 5) * math.sin(t)), c1, 2)
    cv.circle(cx - 4, cy - 3, 3, WHITE)
    cv.circle(cx + 5, cy + 4, 2, WHITE)


def icon_rocket(cv, x, y, w, h, c1, c2):
    cx = x + w // 2
    cv.poly([(cx, y + 2), (cx + 7, y + 16), (cx + 7, y + h - 12),
             (cx, y + h - 6), (cx - 7, y + h - 12), (cx - 7, y + 16)], c1)
    cv.circle(cx, y + 12, 3, WHITE)
    cv.poly([(cx - 7, y + h - 12), (cx - 12, y + h - 2), (cx - 3, y + h - 8)], c2)
    cv.poly([(cx + 7, y + h - 12), (cx + 12, y + h - 2), (cx + 3, y + h - 8)], c2)
    cv.poly([(cx - 3, y + h - 4), (cx + 3, y + h - 4), (cx, y + h + 2)], GOLD)


def icon_coin(cv, x, y, w, h, c1, c2):
    cx, cy, r = x + w // 2, y + h // 2, min(w, h) // 2 - 3
    cv.circle(cx, cy, r, GOLD)
    cv.ring(cx, cy, r, c2, 2)
    cv.rect(cx - 1, cy - r + 4, 2, 2 * r - 8, INK)
    cv.rect(cx - 5, cy - 3, 10, 2, INK)
    cv.rect(cx - 5, cy + 2, 10, 2, INK)


def icon_cricket(cv, x, y, w, h, c1, c2):
    cv.line(x + 8, y + 6, x + 8, y + h - 6, c1, 2)
    cv.line(x + 13, y + 6, x + 13, y + h - 6, c1, 2)
    cv.line(x + 18, y + 6, x + 18, y + h - 6, c1, 2)
    cv.circle(x + w - 9, y + h - 9, 6, RED)
    cv.ring(x + w - 9, y + h - 9, 6, WHITE, 1)


ICONS = dict(globe=icon_globe, flats=icon_flats, tanker=icon_tanker,
             plane=icon_plane, flame=icon_flame, ball=icon_ball,
             bike=icon_bike, flags=icon_flags, ballot=icon_ballot,
             virus=icon_virus, rocket=icon_rocket, coin=icon_coin,
             cricket=icon_cricket)


# ---------------------------------------------------------------------------
# Page layout — newspaper front page, 1024x1024.
# ---------------------------------------------------------------------------

MAP_PINS = [
    (1, 0.565, 0.235), (2, 0.540, 0.130), (3, 0.620, 0.300),
    (4, 0.130, 0.300), (5, 0.800, 0.420), (6, 0.225, 0.170),
    (7, 0.440, 0.210), (8, 0.700, 0.300), (9, 0.190, 0.240),
    (10, 0.080, 0.320), (11, 0.950, 0.100), (12, 0.485, 0.155),
    (13, 0.930, 0.800),
]

CONTINENTS = [
    [(0.03, 0.15), (0.10, 0.05), (0.20, 0.08), (0.24, 0.20), (0.18, 0.32),
     (0.10, 0.34), (0.04, 0.26)],
    [(0.22, 0.42), (0.28, 0.40), (0.32, 0.52), (0.28, 0.70), (0.24, 0.66),
     (0.21, 0.52)],
    [(0.44, 0.12), (0.52, 0.08), (0.56, 0.16), (0.52, 0.24), (0.46, 0.22),
     (0.43, 0.16)],
    [(0.44, 0.32), (0.54, 0.30), (0.58, 0.42), (0.54, 0.58), (0.48, 0.56),
     (0.44, 0.44)],
    [(0.56, 0.08), (0.72, 0.05), (0.86, 0.12), (0.92, 0.24), (0.84, 0.34),
     (0.70, 0.36), (0.60, 0.28), (0.56, 0.18)],
    [(0.86, 0.68), (0.92, 0.66), (0.94, 0.74), (0.88, 0.78), (0.85, 0.72)],
]


def _load_fonts(base):
    return {
        "reg": Font(os.path.join(base, "fonts", "Lexend-Regular.ttf")),
        "med": Font(os.path.join(base, "fonts", "Lexend-Medium.ttf")),
        "semi": Font(os.path.join(base, "fonts", "Lexend-SemiBold.ttf")),
        "bold": Font(os.path.join(base, "fonts", "Lexend-Bold.ttf")),
    }


def _card_label(cv, F, x, y, w, num, region, tag):
    cv.rect(x, y, w, 18, RED)
    draw_text(cv, F["bold"], 11, x + 8, y + 4, str(num), WHITE)
    draw_text(cv, F["semi"], 11, x + 26, y + 4, region, WHITE)
    tw = text_width(F["semi"], 11, tag)
    draw_text(cv, F["semi"], 11, x + w - 8 - tw, y + 4, tag, WHITE)


def render():
    base = os.path.dirname(os.path.abspath(__file__))
    F = _load_fonts(base)
    cv = Canvas()
    MX = 28
    CW = 968  # content width: x 28..996

    # ---- masthead ------------------------------------------------------
    cv.hline(MX, 14, CW, INK, 3)
    draw_text_c(cv, F["bold"], 30, 512, 20, "THE WORLD IN ONE DAY", INK, 2.0)
    cv.hline(MX, 56, CW, INK, 1)
    draw_text_c(cv, F["med"], 11, 512, 60, "35 STORIES  ·  7 REGIONS  ·  SIX CONTINENTS AND THE WORLD",
                INK2, 1.0)

    # ---- giant date ----------------------------------------------------
    draw_text_c(cv, F["bold"], 54, 512, 74, "MONDAY 23 NOVEMBER 2026", INK)
    draw_text_c(cv, F["semi"], 16, 512, 132,
                "COP31 collapses with no deal  ·  Drone flattens flats near Kyiv", RED)
    draw_text_c(cv, F["semi"], 16, 512, 150,
                "Three tankers hit in Hormuz", RED)

    # ---- stat strip ----------------------------------------------------
    sy = 172
    cv.hline(MX, sy, CW, INK, 1)
    colw = CW / 6.0
    for i, (num, label) in enumerate(STATS):
        x = MX + i * colw
        if i:
            cv.vline(int(x), sy + 6, 46, LINE, 1)
        draw_text_c(cv, F["bold"], 26, int(x + colw / 2), sy + 6, num, RED)
        for li, line in enumerate(wrap_text(F["reg"], 10, label, colw - 14)):
            draw_text_c(cv, F["reg"], 10, int(x + colw / 2), sy + 35 + li * 12,
                        line, INK2)
    cv.hline(MX, sy + 58, CW, INK, 1)

    # ---- region strip --------------------------------------------------
    cv.rect(MX, 234, CW, 18, PAPER2)
    reg_text = "  ·  ".join("%s %d" % (name, n) for name, n in REGIONS)
    draw_text_c(cv, F["semi"], 11, 512, 237, reg_text, NAVY, 1.0)

    # ---- lead cards ----------------------------------------------------
    ly, lh = 258, 196
    lead_w = (CW - 24) // 3
    for i, s in enumerate(LEADS):
        x = MX + i * (lead_w + 12)
        cv.rect(x, ly, lead_w, lh, PAPER2)
        cv.outline(x, ly, lead_w, lh, LINE, 1)
        ix, iy = x + 8, ly + 6
        iw, ih = lead_w - 16, 72
        cv.rect(ix, iy, iw, ih, NAVY_LT)
        ICONS[s["icon"]](cv, ix + iw // 2 - 40, iy + 6, 80, 60, NAVY, RED)
        _card_label(cv, F, x, ly + 82, lead_w, s["n"], s["region"], s["tag"])
        hy = ly + 104
        for li, line in enumerate(wrap_text(F["bold"], 19, s["head"], lead_w - 16)):
            draw_text(cv, F["bold"], 19, x + 8, hy + li * 22, line, INK)
        dy = hy + 44
        for li, line in enumerate(wrap_text(F["reg"], 12, s["deck"], lead_w - 16)[:2]):
            draw_text(cv, F["reg"], 12, x + 8, dy + li * 14, line, INK2)
        draw_text(cv, F["semi"], 10, x + 8, ly + lh - 13, "SOURCE: " + s["source"], GREY)

    # ---- medium cards --------------------------------------------------
    my, mh = 462, 92
    med_w = (CW - 40) // 5
    for i, s in enumerate(MEDIUM):
        col, row = i % 5, i // 5
        x = MX + col * (med_w + 10)
        y = my + row * (mh + 8)
        cv.rect(x, y, med_w, mh, WHITE)
        cv.outline(x, y, med_w, mh, LINE, 1)
        cv.circle(x + 14, y + 14, 9, RED)
        num = str(s["n"])
        nw = text_width(F["bold"], 10, num)
        draw_text(cv, F["bold"], 10, x + 14 - nw / 2, y + 9, num, WHITE)
        draw_text(cv, F["semi"], 9, x + 28, y + 9, s["region"] + "  ·  " + s["tag"], GREY)
        hy = y + 24
        for li, line in enumerate(wrap_text(F["bold"], 12, s["head"], med_w - 14)[:2]):
            draw_text(cv, F["bold"], 12, x + 7, hy + li * 15, line, INK)
        dy = y + 56
        for li, line in enumerate(wrap_text(F["reg"], 10, s["deck"], med_w - 14)[:2]):
            draw_text(cv, F["reg"], 10, x + 7, dy + li * 11, line, INK2)
        draw_text(cv, F["semi"], 9, x + 7, y + mh - 11, s["source"], GREY)

    # ---- map + date check ----------------------------------------------
    gy = 654
    draw_text(cv, F["bold"], 13, MX, gy, "WHERE IT HAPPENED", INK, 1.0)
    draw_text(cv, F["bold"], 13, 660, gy, "DATE CHECK", INK, 1.0)
    my0, mh0 = 672, 130
    cv.rect(MX, my0, 620, mh0, SEA)
    cv.outline(MX, my0, 620, mh0, LINE, 1)
    for poly in CONTINENTS:
        cv.poly([(MX + px * 620, my0 + py * mh0) for (px, py) in poly], LAND)
    for (n, px, py) in MAP_PINS:
        cx, cy = MX + px * 620, my0 + py * mh0
        cv.circle(int(cx), int(cy), 8, NAVY)
        cv.ring(int(cx), int(cy), 8, WHITE, 1)
        t = str(n)
        tw = text_width(F["bold"], 9, t)
        draw_text(cv, F["bold"], 9, cx - tw / 2, cy - 5, t, WHITE)
    draw_text(cv, F["reg"], 9, MX + 6, my0 + mh0 - 13,
              "Pins 1-13 match the numbered stories above.", INK2)

    dx, dw = 660, 336
    cv.rect(dx, my0, dw, mh0, WHITE)
    cv.outline(dx, my0, dw, mh0, LINE, 1)
    draw_text(cv, F["semi"], 10, dx + 8, my0 + 6, "LEFT OUT ON PURPOSE — FIRST REPORTED EARLIER", RED)
    yy = my0 + 21
    for (item, when) in LEFT_OUT:
        draw_text(cv, F["reg"], 10, dx + 8, yy, item, INK)
        tw = text_width(F["semi"], 10, when)
        draw_text(cv, F["semi"], 10, dx + dw - 8 - tw, yy, when, RED)
        yy += 11
    draw_text(cv, F["semi"], 10, dx + 8, yy + 2, "NOT YET — HAPPENS AFTER TODAY", RED)
    yy += 14
    for (item, when) in NOT_YET:
        draw_text(cv, F["reg"], 10, dx + 8, yy, item, INK)
        tw = text_width(F["semi"], 10, when)
        draw_text(cv, F["semi"], 10, dx + dw - 8 - tw, yy, when, RED)

    # ---- digest ---------------------------------------------------------
    dy0 = 810
    draw_text(cv, F["bold"], 13, MX, dy0, "ALSO ON 23 NOVEMBER — 22 MORE STORIES", INK, 1.0)
    cv.hline(MX, dy0 + 18, CW, INK, 1)
    row_h = 15
    for ci in range(2):
        x = MX + ci * 492
        col = BRIEFS[ci * 11:(ci + 1) * 11]
        for ri, (n, head, src, tag) in enumerate(col):
            y = dy0 + 24 + ri * row_h
            draw_text(cv, F["bold"], 11, x, y, str(n), RED)
            draw_text(cv, F["reg"], 11, x + 24, y, head, INK)
            hw = text_width(F["reg"], 11, head)
            draw_text(cv, F["semi"], 10, x + 24 + hw + 6, y, "— " + src, GREY)

    # ---- footer ---------------------------------------------------------
    fy = 996
    cv.hline(MX, fy - 4, CW, LINE, 1)
    draw_text_c(cv, F["reg"], 10, 512, fy,
                "First-report dates are shown on every story. 22 NOV = reported Sunday — the weekend's news on Monday's front page.",
                INK2)
    draw_text_c(cv, F["reg"], 10, 512, fy + 12,
                "Sources: Reuters · AP · BBC · CNN · The Hindu · ANI · MotoGP.com · NDTV and others, named beside each story. Original drawings — no photographs.",
                INK2)
    return cv


if __name__ == "__main__":
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "output")
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "entry.png")
    size = write_png(render(), path)
    print("wrote %s (%d bytes)" % (path, size))
