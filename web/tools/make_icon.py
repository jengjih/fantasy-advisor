"""LeSunshine 顧問 App 圖示：太陽＋籃球。純 Python 產生 PNG（不需要 PIL），超取樣抗鋸齒。

用法（在 web/ 底下）：python3 tools/make_icon.py
輸出到 web/icons/：apple-touch-icon.png(180)、icon-192.png、icon-512.png、
icon-maskable-512.png、favicon-32.png；另外在 tools/ 產生 icon-preview.png（模擬 iPhone 圓角，只供檢查）。
"""
import math
import os
import struct
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "icons")


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


BG_TOP, BG_BOT = hexrgb("#1A2A5E"), hexrgb("#0A1230")
GLOW = hexrgb("#FF8A2A")
RAY = hexrgb("#FFC23D")
BALL_HI, BALL_LO = hexrgb("#FFA247"), hexrgb("#EE5A17")
SEAM = hexrgb("#0F1A3F")

BALL_R = 0.50
RAY_IN, RAY_OUT, RAY_W = 0.64, 0.80, 0.085
SEAM_W = 0.040
N_RAYS = 12


def mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


RAYS = []
for i in range(N_RAYS):
    a = 2 * math.pi * i / N_RAYS + math.pi / N_RAYS
    c, s = math.cos(a), math.sin(a)
    RAYS.append((RAY_IN * c, RAY_IN * s, RAY_OUT * c, RAY_OUT * s))


def color_at(x, y, scale, glow=True):
    """x, y in [-1, 1]（y 向下）。scale 用來縮小圖案（maskable 要留安全區）。"""
    t = (y + 1) / 2
    col = mix(BG_TOP, BG_BOT, t)
    u, v = x / scale, y / scale
    r = math.hypot(u, v)
    if glow:  # 太陽背後的柔光
        g = max(0.0, 1 - r / 1.05) ** 2 * 0.35
        col = mix(col, GLOW, g)
    # 光芒（圓頭膠囊）
    if RAY_IN - RAY_W < r < RAY_OUT + RAY_W:
        for ax, ay, bx, by in RAYS:
            if seg_dist(u, v, ax, ay, bx, by) <= RAY_W / 2:
                return RAY
    if r <= BALL_R:
        # 球體：左上亮、右下暗
        k = max(0.0, min(1.0, (u + v) / (2 * BALL_R) * 0.5 + 0.5))
        col = mix(BALL_HI, BALL_LO, k)
        # 球縫：十字＋左右兩道弧
        h = SEAM_W / 2
        if abs(u) < h or abs(v) < h:
            return SEAM
        cx, rr = 0.86, 0.62
        if abs(math.hypot(u - cx, v) - rr) < h or abs(math.hypot(u + cx, v) - rr) < h:
            return SEAM
        # 外緣細線，讓球和光暈分開
        if r > BALL_R - SEAM_W * 0.55:
            return SEAM
    return col


def render(size, scale=1.0, ss=4, rounded=False, glow=True):
    rows = []
    step = 2.0 / size
    offs = [(i + 0.5) / ss for i in range(ss)]
    rad = size * 0.2237
    for py in range(size):
        row = bytearray([0])
        for px in range(size):
            acc = [0.0, 0.0, 0.0]
            for oy in offs:
                y = -1 + (py + oy) * step
                for ox in offs:
                    x = -1 + (px + ox) * step
                    c = color_at(x, y, scale, glow)
                    acc[0] += c[0]; acc[1] += c[1]; acc[2] += c[2]
            n = ss * ss
            c = [acc[0] / n, acc[1] / n, acc[2] / n]
            if rounded:  # 只供預覽：模擬 iPhone 圓角遮罩（白底）
                cx = min(px + 0.5, size - px - 0.5); cy = min(py + 0.5, size - py - 0.5)
                if cx < rad and cy < rad:
                    d = math.hypot(rad - cx, rad - cy) - rad
                    a = max(0.0, min(1.0, 0.5 - d))
                    c = [c[i] * a + 255 * (1 - a) for i in range(3)]
            row += bytes(int(round(max(0, min(255, v)))) for v in c)
        rows.append(bytes(row))
    return b"".join(rows)


def write_png(path, size, raw):
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    print("wrote", os.path.relpath(path, os.path.join(HERE, "..")))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    jobs = [
        ("apple-touch-icon.png", 180, 1.0, 4, False),
        ("icon-192.png", 192, 1.0, 4, False),
        ("icon-512.png", 512, 1.0, 3, False),
        ("icon-maskable-512.png", 512, 0.78, 3, False),
        ("favicon-32.png", 32, 1.12, 6, False),
        ("preview.png", 240, 1.0, 3, True),
    ]
    for name, size, scale, ss, rounded in jobs:
        folder = HERE if rounded else OUT
        name = "icon-preview.png" if rounded else name
        write_png(os.path.join(folder, name), size, render(size, scale, ss, rounded))
