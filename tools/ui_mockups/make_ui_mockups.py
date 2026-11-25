#!/usr/bin/env python3
"""Draws e-paper UI concept screens at the display's native resolution (400 x 300, 1-bit).

Usage:
    python3 make_ui_mockups.py ../../docs/images

Writes ui/<name>.png (native 400 x 300, black/white) and ui-concepts.png (all screens,
scaled 2x with e-paper colors, for the README). Needs Pillow. The numbers on the
screens are example data.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
W, H = 400, 300
BLACK, WHITE = 0, 1

FONT_DIRS = [
    "/usr/share/fonts/truetype/liberation",
    "/Library/Fonts",
    "/System/Library/Fonts/Supplemental",
    "C:/Windows/Fonts",
]
FONT_FILES = {
    "sans": ["LiberationSans-Regular.ttf", "Arial.ttf", "arial.ttf"],
    "sansb": ["LiberationSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf"],
    "mono": ["LiberationMono-Regular.ttf", "Courier New.ttf", "cour.ttf"],
    "monob": ["LiberationMono-Bold.ttf", "Courier New Bold.ttf", "courbd.ttf"],
}
_cache = {}


def font(kind, size):
    key = (kind, size)
    if key not in _cache:
        for d in FONT_DIRS:
            for name in FONT_FILES[kind]:
                path = os.path.join(d, name)
                if os.path.exists(path):
                    _cache[key] = ImageFont.truetype(path, size)
                    break
            if key in _cache:
                break
        else:
            raise SystemExit(f"No font found for {kind}; install Liberation fonts or Arial/Courier New")
    return _cache[key]


def new_screen():
    im = Image.new("1", (W, H), WHITE)
    return im, ImageDraw.Draw(im)


def tri_up(d, x, y, s, fill=BLACK):
    """Triangle pointing up; (x, y) is its bottom-left corner."""
    d.polygon([(x, y), (x + s, y), (x + s / 2, y - s)], fill=fill)


def tri_down(d, x, y, s, fill=BLACK):
    """Triangle pointing down; (x, y) is its top-left corner."""
    d.polygon([(x, y), (x + s, y), (x + s / 2, y + s)], fill=fill)


def dotted_hline(d, x0, x1, y, step=3):
    for x in range(x0, x1 + 1, step):
        d.point((x, y), fill=BLACK)


def chip(d, right_x, top_y, label):
    """Small inverted label aligned to the right edge."""
    f = font("sansb", 12)
    w = d.textlength(label, font=f)
    d.rectangle((right_x - w - 12, top_y, right_x, top_y + 18), fill=BLACK)
    d.text((right_x - w / 2 - 6, top_y + 14), label, font=f, fill=WHITE, anchor="ms")


def touch_bar(d, labels, active=None):
    """Bottom bar with the three touch-pad actions (pads sit under the screen)."""
    d.rectangle((0, 268, W - 1, H - 1), fill=BLACK)
    f = font("sansb", 14)
    for i, label in enumerate(labels):
        cx = 67 + i * 133
        if i == active:
            w = d.textlength(label, font=f)
            d.rounded_rectangle((cx - w / 2 - 9, 274, cx + w / 2 + 9, 294), radius=4, fill=WHITE)
            d.text((cx, 289), label, font=f, fill=BLACK, anchor="ms")
        else:
            d.text((cx, 289), label, font=f, fill=WHITE, anchor="ms")
    for x in (133, 266):
        d.line((x, 275, x, 293), fill=WHITE, width=1)


# ------------------------------------------------------------------ screens
def portfolio():
    im, d = new_screen()
    d.text((10, 20), "PORTFOLIO", font=font("sansb", 15), fill=BLACK, anchor="ls")
    d.text((390, 20), "Wed 25 Nov  09:42", font=font("sans", 13), fill=BLACK, anchor="rs")
    d.line((8, 27, 391, 27), fill=BLACK, width=2)

    d.text((10, 68), "$12,480.55", font=font("sansb", 34), fill=BLACK, anchor="ls")
    tri_up(d, 11, 91, 11)
    d.text((28, 92), "+$153.20  (+1.24%) today", font=font("sans", 14), fill=BLACK, anchor="ls")

    # 7-day sparkline
    d.text((266, 45), "7 DAYS", font=font("sansb", 10), fill=BLACK, anchor="ls")
    vals = [12210, 12262, 12188, 12305, 12290, 12327, 12480]
    x0, x1, y0, y1 = 266, 386, 52, 98
    lo, hi = min(vals), max(vals)
    pts = [(x0 + i * (x1 - x0) / (len(vals) - 1), y1 - (v - lo) / (hi - lo) * (y1 - y0)) for i, v in enumerate(vals)]
    d.line(pts, fill=BLACK, width=2, joint="curve")
    lx, ly = pts[-1]
    d.ellipse((lx - 3, ly - 3, lx + 3, ly + 3), fill=BLACK)

    d.line((8, 110, 391, 110), fill=BLACK, width=1)
    d.text((12, 128), "ASSET", font=font("sansb", 11), fill=BLACK, anchor="ls")
    d.text((250, 128), "PRICE", font=font("sansb", 11), fill=BLACK, anchor="rs")
    d.text((390, 128), "TODAY", font=font("sansb", 11), fill=BLACK, anchor="rs")
    dotted_hline(d, 10, 390, 134)

    rows = [("VOO", "512.30", 0.82), ("QQQ", "448.10", 1.46), ("VT", "118.74", -0.21), ("BND", "72.15", 0.05)]
    y = 156
    for ticker, price, change in rows:
        d.text((12, y), ticker, font=font("monob", 17), fill=BLACK, anchor="ls")
        d.text((250, y), price, font=font("mono", 16), fill=BLACK, anchor="rs")
        s = f"{abs(change):.2f}%"
        d.text((390, y), s, font=font("mono", 16), fill=BLACK, anchor="rs")
        tx = 390 - d.textlength(s, font=font("mono", 16)) - 16
        if change >= 0:
            tri_up(d, tx, y - 1, 10)
        else:
            tri_down(d, tx, y - 11, 10)
        y += 27

    touch_bar(d, ["‹ PREV", "VIEW", "NEXT ›"])
    return im


def stock_week():
    im, d = new_screen()
    d.text((10, 24), "VOO", font=font("sansb", 20), fill=BLACK, anchor="ls")
    d.text((64, 24), "S&P 500 ETF", font=font("sans", 13), fill=BLACK, anchor="ls")
    chip(d, 390, 8, "1 WEEK")
    d.line((8, 33, 391, 33), fill=BLACK, width=2)

    d.text((10, 68), "512.30", font=font("sansb", 30), fill=BLACK, anchor="ls")
    px = 10 + d.textlength("512.30", font=font("sansb", 30)) + 14
    tri_up(d, px, 66, 11)
    d.text((px + 17, 67), "+4.18  (+0.82%)", font=font("sans", 14), fill=BLACK, anchor="ls")

    # chart
    left, right, top, bottom = 50, 390, 86, 240
    lo, hi = 504.0, 514.0

    def ymap(v):
        return bottom - (v - lo) / (hi - lo) * (bottom - top)

    for t in (506, 509, 512):
        y = ymap(t)
        dotted_hline(d, left, right, int(round(y)), step=4)
        d.text((44, y + 4), str(t), font=font("mono", 11), fill=BLACK, anchor="rs")

    # five trading days, 8 points each (example data)
    day_paths = [
        [508.1, 508.6, 507.9, 507.2, 507.6, 508.3, 508.0, 508.4],
        [508.4, 509.1, 509.6, 509.2, 508.8, 509.4, 509.9, 509.7],
        [509.7, 509.2, 508.5, 507.9, 508.3, 508.9, 509.3, 509.1],
        [509.1, 509.8, 510.6, 510.2, 510.9, 511.4, 511.1, 511.6],
        [511.6, 511.2, 511.9, 512.6, 512.1, 512.8, 512.5, 512.3],
    ]
    series = [v for day in day_paths for v in day]
    n = len(series)
    pts = [(left + i * (right - left) / (n - 1), ymap(v)) for i, v in enumerate(series)]

    # light dither under the line, so the area reads as gray on a 1-bit screen
    px_ = im.load()
    for i in range(len(pts) - 1):
        (xa, ya), (xb, yb) = pts[i], pts[i + 1]
        for x in range(int(xa), int(xb) + 1):
            t = 0 if xb == xa else (x - xa) / (xb - xa)
            yl = ya + t * (yb - ya)
            for y in range(int(yl) + 3, bottom + 1):
                if (x + y) % 4 == 0 and (y % 2 == 0):
                    px_[x, y] = BLACK
    d.line(pts, fill=BLACK, width=2, joint="curve")
    lx, ly = pts[-1]
    d.ellipse((lx - 3, ly - 3, lx + 3, ly + 3), fill=BLACK)
    d.line((left, bottom, right, bottom), fill=BLACK, width=1)

    days = ["MON", "TUE", "WED", "THU", "FRI"]
    seg = (right - left) / 5
    for i, name in enumerate(days):
        d.text((left + seg * (i + 0.5), 256), name, font=font("sans", 11), fill=BLACK, anchor="ms")

    touch_bar(d, ["‹ DAY", "WEEK", "MONTH ›"], active=1)
    return im


def lyrics():
    im, d = new_screen()
    # microphone icon
    d.rounded_rectangle((12, 6, 20, 18), radius=4, outline=BLACK, width=2)
    d.arc((8, 10, 24, 24), start=0, end=180, fill=BLACK, width=2)
    d.line((16, 24, 16, 28), fill=BLACK, width=2)
    d.text((32, 22), "NOW PLAYING", font=font("sansb", 15), fill=BLACK, anchor="ls")
    chip(d, 390, 8, "SYNCED")
    d.line((8, 33, 391, 33), fill=BLACK, width=2)

    d.text((10, 64), "Sample Track", font=font("sansb", 22), fill=BLACK, anchor="ls")
    d.text((10, 84), "Demo Artist", font=font("sans", 14), fill=BLACK, anchor="ls")
    d.rectangle((10, 94, 390, 100), outline=BLACK, width=1)
    d.rectangle((10, 94, 10 + int(0.49 * 380), 100), fill=BLACK)
    d.text((10, 116), "1:42", font=font("mono", 12), fill=BLACK, anchor="ls")
    d.text((390, 116), "3:28", font=font("mono", 12), fill=BLACK, anchor="rs")
    dotted_hline(d, 10, 390, 125)

    d.text((200, 151), "the morning paper on the stair", font=font("sans", 15), fill=BLACK, anchor="ms")
    d.rectangle((8, 161, 391, 197), fill=BLACK)
    d.text((200, 186), "every word is waiting there", font=font("sansb", 19), fill=WHITE, anchor="ms")
    d.text((200, 223), "turn the page and start again", font=font("sans", 15), fill=BLACK, anchor="ms")
    d.text((200, 247), "and read it like it's new", font=font("sans", 13), fill=BLACK, anchor="ms")

    touch_bar(d, ["‹ -5 s", "RE-SYNC", "+5 s ›"])
    return im


def three_counters():
    """Approximation of what firmware/03_three_counters draws (FreeMonoBold fonts)."""
    im, d = new_screen()
    d.rectangle((0, 0, W - 1, H - 1), outline=BLACK)
    d.rectangle((2, 2, W - 3, H - 3), outline=BLACK)
    d.text((200, 28), "Three counters", font=font("monob", 23), fill=BLACK, anchor="mm")
    d.line((10, 52, 389, 52), fill=BLACK, width=1)
    for i, (x, val) in enumerate(zip((16, 144, 272), (7, 12, 3))):
        d.rectangle((x, 72, x + 119, 221), outline=BLACK)
        d.rectangle((x + 1, 73, x + 118, 220), outline=BLACK)
        d.text((x + 60, 91), f"B{i + 1}", font=font("monob", 23), fill=BLACK, anchor="mm")
        d.line((x + 8, 110, x + 111, 110), fill=BLACK, width=1)
        d.text((x + 60, 166), str(val), font=font("monob", 46), fill=BLACK, anchor="mm")
    d.text((200, 260), "Tap a button to add 1", font=font("monob", 17), fill=BLACK, anchor="mm")
    return im


# ------------------------------------------------------------------ output
SCREENS = [
    ("portfolio", portfolio, "Portfolio overview (concept, example data)"),
    ("stock-week", stock_week, "One stock over a week (concept, example data)"),
    ("lyrics", lyrics, "Song recognition with synced lyrics (concept)"),
    ("three-counters", three_counters, "Three counters (what 03_three_counters shows)"),
]

PAPER, INK = (236, 235, 228), (30, 30, 32)


def to_paper(im1, scale=2):
    lum = im1.convert("L")
    rgb = Image.merge("RGB", [lum.point(lambda v, c=c: INK[c] if v < 128 else PAPER[c]) for c in range(3)])
    return rgb.resize((W * scale, H * scale), Image.NEAREST)


def main():
    ui_dir = os.path.join(OUT, "ui")
    os.makedirs(ui_dir, exist_ok=True)
    rendered = []
    for name, fn, caption in SCREENS:
        im = fn()
        im.save(os.path.join(ui_dir, f"{name}.png"), optimize=True)
        rendered.append((to_paper(im), caption))

    bezel_pad, gap, margin, top, cap_h = 24, 64, 40, 110, 64
    bw, bh = W * 2 + 2 * bezel_pad, H * 2 + 2 * bezel_pad
    cw = 2 * margin + 2 * bw + gap
    ch = top + 2 * (bh + cap_h) + 40 + margin
    canvas = Image.new("RGB", (cw, ch), (243, 244, 242))
    d = ImageDraw.Draw(canvas)
    d.text((margin, 72), "E-paper UI concepts", font=font("sansb", 38), fill=(30, 33, 36), anchor="ls")
    d.text((margin + d.textlength("E-paper UI concepts", font=font("sansb", 38)) + 20, 72),
           "400 × 300 px, black and white, shown 2× with the touch-pad actions at the bottom",
           font=font("sans", 22), fill=(90, 96, 102), anchor="ls")
    for i, (img, caption) in enumerate(rendered):
        col, row = i % 2, i // 2
        x = margin + col * (bw + gap)
        y = top + row * (bh + cap_h + 40)
        d.rounded_rectangle((x, y, x + bw, y + bh), radius=18, fill=(48, 51, 54))
        canvas.paste(img, (x + bezel_pad, y + bezel_pad))
        d.text((x + 4, y + bh + 40), caption, font=font("sans", 26), fill=(60, 64, 68), anchor="ls")
    canvas.save(os.path.join(OUT, "ui-concepts.png"), optimize=True)
    print("wrote", ui_dir, "and", os.path.join(OUT, "ui-concepts.png"), canvas.size)


if __name__ == "__main__":
    main()
