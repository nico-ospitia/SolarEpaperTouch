#!/usr/bin/env python3
"""Draws the SolarEpaperTouch system schematic as an SVG (A3 landscape sheet).

Usage:
    python3 generate_schematic.py ../../hardware/schematic/SolarEpaperTouch_schematic_revA.svg

Needs Pillow (pip install pillow) to measure text. It looks for Arial or
Liberation Sans (same metrics) and falls back to an estimate if neither is found.
Render the SVG to PDF/PNG with render_schematic.py.
"""
import html
import math
import os
import sys

from PIL import ImageFont

OUT_SVG = sys.argv[1] if len(sys.argv) > 1 else "schematic.svg"

W, H = 1800, 1273  # A3 proportions
FONT = "Arial, 'Liberation Sans', Helvetica, sans-serif"

FONT_CANDIDATES = {
    (False, False): [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ],
    (True, False): [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ],
    (False, True): [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf",
        "/Library/Fonts/Arial Italic.ttf",
        "/System/Library/Fonts/Supplemental/Arial Italic.ttf",
        "C:/Windows/Fonts/ariali.ttf",
    ],
    (True, True): [
        "/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf",
        "/Library/Fonts/Arial Bold Italic.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf",
        "C:/Windows/Fonts/arialbi.ttf",
    ],
}

C = {
    "wire": "#12753C",
    "comp": "#8A1C1C",
    "fill": "#FFF8DA",
    "pinname": "#0C5866",
    "ref": "#0C5866",
    "label": "#9A3B00",
    "labelfill": "#FFF3E2",
    "pwr": "#8A1C1C",
    "nc": "#1F4FD8",
    "frame": "#7A1E1E",
    "text": "#1F2328",
    "muted": "#5B6470",
    "block": "#A3ABB6",
    "rowalt": "#F7F5F0",
    "head": "#EFEAE0",
}

_fonts = {}


def _font(bold, italic, size):
    key = (bold, italic, size)
    if key not in _fonts:
        _fonts[key] = None
        for path in FONT_CANDIDATES[(bold, italic)]:
            if os.path.exists(path):
                _fonts[key] = ImageFont.truetype(path, int(round(size * 8)))
                break
    return _fonts[key]


def tw(s, size, bold=False, italic=False):
    """Text width in SVG units."""
    f = _font(bold, italic, size)
    if f is None:
        return len(s) * size * (0.62 if bold else 0.57)
    return f.getlength(s) / 8.0


S = []
TEXT_BOXES = []  # (x0, y0, x1, y1, text) used to report overlapping labels


def f(v):
    return ("%.2f" % v).rstrip("0").rstrip(".")


def text(x, y, s, size=13, color=None, anchor="start", bold=False, italic=False, ls=None, check=True):
    color = color or C["text"]
    attrs = [f'x="{f(x)}"', f'y="{f(y)}"', f'font-size="{f(size)}"', f'fill="{color}"']
    if anchor != "start":
        attrs.append(f'text-anchor="{anchor}"')
    if bold:
        attrs.append('font-weight="700"')
    if italic:
        attrs.append('font-style="italic"')
    if ls:
        attrs.append(f'letter-spacing="{ls}"')
    S.append(f'<text {" ".join(attrs)}>{html.escape(s)}</text>')
    if check:
        w = tw(s, size, bold, italic) + (ls or 0) * len(s)
        x0 = {"start": x, "middle": x - w / 2, "end": x - w}[anchor]
        TEXT_BOXES.append((x0, y - 0.74 * size, x0 + w, y + 0.22 * size, s))


def line(x1, y1, x2, y2, color, w=2.0, dash=None, cap="round"):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    S.append(
        f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" stroke="{color}" '
        f'stroke-width="{f(w)}" stroke-linecap="{cap}"{d}/>'
    )


def wire(*pts):
    p = " ".join(f"{f(x)},{f(y)}" for x, y in pts)
    S.append(
        f'<polyline points="{p}" fill="none" stroke="{C["wire"]}" stroke-width="2" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
    )


def junction(x, y):
    S.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="4.3" fill="{C["wire"]}"/>')


def nc(x, y, s=6):
    line(x - s, y - s, x + s, y + s, C["nc"], 2.2)
    line(x - s, y + s, x + s, y - s, C["nc"], 2.2)


def rect(x, y, w, h, fill="none", stroke=None, sw=1.0, rx=0, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    st = f' stroke="{stroke}" stroke-width="{f(sw)}"' if stroke else ""
    S.append(f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" rx="{f(rx)}" fill="{fill}"{st}{d}/>')


def module(ref, value, x, y, w, h, pins, ref_xy=None, value_xy=None):
    """Module body with pins. pins: (side, position, name[, {"key", "nc", "len"}])."""
    rect(x, y, w, h, fill=C["fill"], stroke=C["comp"], sw=2.2)
    ends = {}
    for p in pins:
        side, pos, name = p[0], p[1], p[2]
        opts = p[3] if len(p) > 3 else {}
        L = opts.get("len", 30)
        if side == "L":
            line(x, pos, x - L, pos, C["comp"])
            text(x + 8, pos + 4.4, name, 12.5, C["pinname"])
            end = (x - L, pos)
        elif side == "R":
            line(x + w, pos, x + w + L, pos, C["comp"])
            text(x + w - 8, pos + 4.4, name, 12.5, C["pinname"], anchor="end")
            end = (x + w + L, pos)
        elif side == "T":
            line(pos, y, pos, y - L, C["comp"])
            text(pos, y + 18, name, 12.5, C["pinname"], anchor="middle")
            end = (pos, y - L)
        else:  # B
            line(pos, y + h, pos, y + h + L, C["comp"])
            text(pos, y + h - 8, name, 12.5, C["pinname"], anchor="middle")
            end = (pos, y + h + L)
        if opts.get("nc"):
            nc(*end)
        ends[opts.get("key", name)] = end
    rx_, ry_ = ref_xy or (x, y - 9)
    text(rx_, ry_, ref, 15, C["ref"], bold=True)
    vx, vy = value_xy or (x, y + h + 21)
    text(vx, vy, value, 13, C["ref"])
    return ends


def netlabel(x, y, name, direction="left", size=12.5):
    w_ = tw(name, size, bold=True)
    h, pad, pt = 20, 7, 9
    total = w_ + 2 * pad + pt
    if direction == "left":
        xr, xl = x, x - total
        pts = [(xr, y - h / 2), (xl + pt, y - h / 2), (xl, y), (xl + pt, y + h / 2), (xr, y + h / 2)]
        tx = xl + pt + pad + w_ / 2
    else:
        xl, xr = x, x + total
        pts = [(xl, y - h / 2), (xr - pt, y - h / 2), (xr, y), (xr - pt, y + h / 2), (xl, y + h / 2)]
        tx = xl + pad + w_ / 2
    p = " ".join(f"{f(a)},{f(b)}" for a, b in pts)
    S.append(f'<polygon points="{p}" fill="{C["labelfill"]}" stroke="{C["label"]}" stroke-width="1.4" stroke-linejoin="round"/>')
    text(tx, y + 4.4, name, size, C["label"], anchor="middle", bold=True)
    return total


def p3v3(x, y, d="up", label="+3V3"):
    col = C["pwr"]
    if d == "up":
        line(x, y, x, y - 14, col)
        line(x - 11, y - 14, x + 11, y - 14, col, 2.6)
        text(x, y - 21, label, 12.5, col, "middle", bold=True)
    elif d == "left":
        line(x, y, x - 14, y, col)
        line(x - 14, y - 11, x - 14, y + 11, col, 2.6)
        text(x - 20, y + 4.4, label, 12.5, col, "end", bold=True)
    else:
        line(x, y, x + 14, y, col)
        line(x + 14, y - 11, x + 14, y + 11, col, 2.6)
        text(x + 20, y + 4.4, label, 12.5, col, "start", bold=True)


def gnd(x, y, d="down"):
    col = C["pwr"]
    if d == "down":
        line(x, y, x, y + 12, col)
        line(x - 12, y + 12, x + 12, y + 12, col, 2.4)
        line(x - 7.5, y + 17, x + 7.5, y + 17, col, 2.4)
        line(x - 3, y + 22, x + 3, y + 22, col, 2.4)
    elif d == "left":
        line(x, y, x - 12, y, col)
        line(x - 12, y - 12, x - 12, y + 12, col, 2.4)
        line(x - 17, y - 7.5, x - 17, y + 7.5, col, 2.4)
        line(x - 22, y - 3, x - 22, y + 3, col, 2.4)
    else:
        line(x, y, x + 12, y, col)
        line(x + 12, y - 12, x + 12, y + 12, col, 2.4)
        line(x + 17, y - 7.5, x + 17, y + 7.5, col, 2.4)
        line(x + 22, y - 3, x + 22, y + 3, col, 2.4)


def arrow(x1, y1, x2, y2, color, w=1.8, head=8.5):
    ang = math.atan2(y2 - y1, x2 - x1)
    bx, by = x2 - head * 0.8 * math.cos(ang), y2 - head * 0.8 * math.sin(ang)
    line(x1, y1, bx, by, color, w)
    p1 = (x2 - head * math.cos(ang - 0.42), y2 - head * math.sin(ang - 0.42))
    p2 = (x2 - head * math.cos(ang + 0.42), y2 - head * math.sin(ang + 0.42))
    S.append(f'<polygon points="{f(x2)},{f(y2)} {f(p1[0])},{f(p1[1])} {f(p2[0])},{f(p2[1])}" fill="{color}"/>')


def block(x, y, w, h, num, title):
    rect(x, y, w, h, stroke=C["block"], sw=1.3, rx=10, dash="8 5")
    rect(x + 12, y + 12, 22, 20, fill=C["comp"], rx=4)
    text(x + 23, y + 26.6, str(num), 12.5, "#FFFFFF", "middle", bold=True, check=False)
    text(x + 42, y + 27, title, 13.5, C["text"], bold=True, ls=0.6)


def wrap(s, size, maxw, bold=False):
    words, lines, cur = s.split(" "), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if tw(t, size, bold) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- sheet frame with zones
rect(8, 8, W - 16, H - 16, stroke=C["frame"], sw=1.4)
rect(28, 28, W - 56, H - 56, stroke=C["frame"], sw=2)
cw, rh = (W - 56) / 8, (H - 56) / 6
for i in range(1, 8):
    x = 28 + i * cw
    line(x, 8, x, 28, C["frame"], 1.2, cap="butt")
    line(x, H - 28, x, H - 8, C["frame"], 1.2, cap="butt")
for i in range(8):
    x = 28 + (i + 0.5) * cw
    text(x, 22.5, str(i + 1), 11.5, C["frame"], "middle", bold=True, check=False)
    text(x, H - 13.5, str(i + 1), 11.5, C["frame"], "middle", bold=True, check=False)
for j in range(1, 6):
    y = 28 + j * rh
    line(8, y, 28, y, C["frame"], 1.2, cap="butt")
    line(W - 28, y, W - 8, y, C["frame"], 1.2, cap="butt")
for j in range(6):
    y = 28 + (j + 0.5) * rh + 4.2
    text(18, y, "ABCDEF"[j], 11.5, C["frame"], "middle", bold=True, check=False)
    text(W - 18, y, "ABCDEF"[j], 11.5, C["frame"], "middle", bold=True, check=False)

# ---------------------------------------------------------------- 1 · power
block(40, 40, 1200, 400, 1, "POWER · SOLAR + BATTERY")

# PV1: solar panel (two cells in series)
px = 130
line(px - 22, 204, px + 22, 204, C["comp"], 2.4)
line(px - 11, 215, px + 11, 215, C["comp"], 5, cap="butt")
line(px, 218.5, px, 229.5, C["comp"], 1.6, dash="2.5 3")
line(px - 22, 233, px + 22, 233, C["comp"], 2.4)
line(px - 11, 244, px + 11, 244, C["comp"], 5, cap="butt")
arrow(72, 176, 101, 199, C["comp"])
arrow(72, 206, 101, 229, C["comp"])
text(160, 201, "+", 16, C["comp"], "middle", bold=True)
text(160, 252, "−", 16, C["comp"], "middle", bold=True)
wire((px, 204), (px, 170), (230, 170))
wire((px, 244), (px, 290), (230, 290))
text(px, 322, "PV1", 15, C["ref"], "middle", bold=True)
text(px, 339, "Solar panel 5 V", 13, C["ref"], "middle")
text(px, 355, "Voc ≤ 6 V", 12, C["muted"], "middle")

# U2: CN3065 solar charger
u2 = module(
    "U2", "Solar charger CN3065 (module)", 260, 130, 200, 250,
    [
        ("L", 170, "SOLAR +", {"key": "S+"}),
        ("L", 290, "SOLAR −", {"key": "S-"}),
        ("R", 170, "BATT IN +", {"key": "B+"}),
        ("R", 290, "BATT IN −", {"key": "B-"}),
        ("R", 335, "SYS OUT +", {"key": "O+", "nc": True}),
        ("R", 358, "SYS OUT −", {"key": "O-", "nc": True}),
    ],
    value_xy=(260, 401),
)
text(360, 222, "CN3065", 16, C["text"], "middle", bold=True)
text(360, 241, "Solar charger", 12, C["text"], "middle")
text(360, 258, "4.4–6.0 V · 500 mA", 11.5, C["muted"], "middle")
text(270, 349, "micro-USB:", 11, C["muted"])
text(270, 364, "backup charging", 11, C["muted"])

# U3: TP4056 + DW01A module, used only as battery protection
u3 = module(
    "U3", "Charger/protection TP4056 + DW01A (USB-C)", 640, 130, 200, 250,
    [
        ("L", 170, "OUT+", {"key": "OUT+"}),
        ("L", 290, "OUT−", {"key": "OUT-"}),
        ("T", 700, "IN+", {"key": "IN+", "nc": True}),
        ("T", 780, "IN−", {"key": "IN-", "nc": True}),
        ("R", 170, "B+", {"key": "B+"}),
        ("R", 290, "B−", {"key": "B-"}),
    ],
    value_xy=(640, 401),
)
text(740, 218, "TP4056 + DW01A", 14, C["text"], "middle", bold=True)
text(740, 237, "1S protection", 12, C["text"], "middle")
text(740, 254, "FS8205A", 11.5, C["muted"], "middle")
text(740, 362, "USB-C: not used", 11, C["muted"], "middle")
text(796, 104.5, "not connected (note 3)", 11, C["muted"], italic=True)

# Charger -> protection (VBAT and GND nets)
wire((490, 170), (610, 170))
wire((490, 290), (610, 290))
junction(550, 170)
junction(550, 290)
text(560, 163, "VBAT", 12.5, C["text"], bold=True)
wire((550, 290), (550, 318))
gnd(550, 318, "down")

# BT1: LiPo cell
bx = 960
wire((870, 170), (bx, 170), (bx, 220))
line(bx - 22, 220, bx + 22, 220, C["comp"], 2.4)
line(bx - 11, 232, bx + 11, 232, C["comp"], 5, cap="butt")
wire((bx, 232), (bx, 290), (870, 290))
text(990, 216, "+", 16, C["comp"], "middle", bold=True)
text(1000, 238, "BT1", 15, C["ref"], bold=True)
text(1000, 256, "LiPo 1S 3.7 V", 13, C["ref"])
text(1000, 272, "500–1000 mAh", 12, C["muted"])

# SW1 -> VSYS
wire((550, 170), (550, 80), (1042.4, 80))
S.append(f'<circle cx="1046" cy="80" r="3.6" fill="#FFFFFF" stroke="{C["comp"]}" stroke-width="2"/>')
S.append(f'<circle cx="1096" cy="80" r="3.6" fill="#FFFFFF" stroke="{C["comp"]}" stroke-width="2"/>')
line(1049, 78, 1092, 61, C["comp"], 2.2)
wire((1099.6, 80), (1130, 80))
netlabel(1130, 80, "VSYS", "right")
text(1071, 106, "SW1", 15, C["ref"], "middle", bold=True)
text(1071, 123, "ON/OFF switch", 12, C["muted"], "middle")

# ---------------------------------------------------------------- 2 · microcontroller
block(40, 455, 650, 480, 2, "MICROCONTROLLER")
pin_y = [545 + 34 * i for i in range(8)]
left = ["IO5", "IO6", "IO7", "IO8", "IO9", "IO10", "IO20", "IO21"]
right = ["5V", "GND", "3V3", "IO4", "IO3", "IO2", "IO1", "IO0"]
pins = [("L", y, n, {"nc": n == "IO9"}) for y, n in zip(pin_y, left)]
pins += [("R", y, n) for y, n in zip(pin_y, right)]
u1 = module("U1", "ESP32-C3 SuperMini (module)", 230, 520, 210, 296, pins, ref_xy=(230, 509), value_xy=(230, 837))
rect(310, 513, 40, 14, fill="#FFFFFF", stroke=C["comp"], sw=1.6, rx=5)
text(335, 549, "USB-C", 10.5, C["muted"], "middle")
text(335, 640, "ESP32-C3", 17, C["text"], "middle", bold=True)
text(335, 660, "SuperMini", 13, C["text"], "middle")
text(335, 690, "top view", 11, C["muted"], "middle")
text(335, 705, "USB-C up", 11, C["muted"], "middle")

left_nets = {"IO5": "EPD_RES", "IO6": "EPD_SCL", "IO7": "EPD_SDA", "IO8": "MIC_SCK",
             "IO10": "EPD_CS", "IO20": "EPD_BUSY", "IO21": "MIC_SD"}
for n, net in left_nets.items():
    x, y = u1[n]
    wire((x, y), (x - 15, y))
    netlabel(x - 15, y, net, "left")
text(188, 685, "BOOT: leave open", 11, C["muted"], "end", italic=True)

x, y = u1["5V"]
wire((x, y), (x + 15, y))
netlabel(x + 15, y, "VSYS", "right")
x, y = u1["GND"]
gnd(x, y, "right")
x, y = u1["3V3"]
p3v3(x, y, "right")
right_nets = {"IO4": "EPD_DC", "IO3": "TOUCH3", "IO2": "MIC_WS", "IO1": "TOUCH2", "IO0": "TOUCH1"}
for n, net in right_nets.items():
    x, y = u1[n]
    wire((x, y), (x + 15, y))
    netlabel(x + 15, y, net, "right")

# R1: boot pull-up on IO2
ry = 884
p3v3(128, ry, "left")
wire((128, ry), (150, ry))
rect(150, ry - 8, 56, 16, fill="#FFFFFF", stroke=C["comp"], sw=2)
wire((206, ry), (232, ry))
netlabel(232, ry, "MIC_WS", "right")
text(178, ry - 15, "R1", 12.5, C["ref"], "middle", bold=True)
text(178, ry + 25, "10 kΩ", 12, C["ref"], "middle")
text(332, ry + 4, "IO2 must be high at boot", 11.5, C["muted"], italic=True)

# ---------------------------------------------------------------- 3 · display
block(705, 455, 535, 480, 3, "E-PAPER DISPLAY")
u4 = module(
    "U4", "WeAct Studio 4.2\" e-paper", 1010, 520, 180, 296,
    [("L", y, n) for y, n in zip(pin_y, ["VCC", "GND", "SDA", "SCL", "CS", "D/C", "RES", "BUSY"])],
    ref_xy=(1010, 509), value_xy=(1010, 837),
)
x, y = u4["VCC"]
wire((x, y), (x - 12, y))
p3v3(x - 12, y, "left")
x, y = u4["GND"]
gnd(x, y, "left")
for n, net in {"SDA": "EPD_SDA", "SCL": "EPD_SCL", "CS": "EPD_CS", "D/C": "EPD_DC",
               "RES": "EPD_RES", "BUSY": "EPD_BUSY"}.items():
    x, y = u4[n]
    wire((x, y), (x - 15, y))
    netlabel(x - 15, y, net, "left")
text(1120, 625, "e-Paper 4.2\"", 15, C["text"], "middle", bold=True)
text(1120, 645, "400 × 300 px", 12, C["text"], "middle")
text(1120, 662, "SSD1683 · B/W", 11.5, C["muted"], "middle")
text(1120, 678, "SPI · 3.3 V", 11.5, C["muted"], "middle")
text(719, 902, "SDA = MOSI and SCL = SCK: this is an SPI bus, not I²C.", 11.5, C["muted"], italic=True)

# ---------------------------------------------------------------- 4 · touch buttons
block(40, 950, 770, 285, 4, "TOUCH BUTTONS (TTP223)")
for k, bxm in enumerate([170, 430, 690], start=1):
    ends = module(
        f"U{5 + k}", f"Touch B{k} (TTP223)", bxm, 1010, 100, 110,
        [("L", 1037, "VCC"), ("L", 1065, "I/O"), ("L", 1093, "GND")],
        ref_xy=(bxm, 1001), value_xy=(bxm, 1140),
    )
    x, y = ends["VCC"]
    wire((x, y), (x - 12, y))
    p3v3(x - 12, y, "left")
    x, y = ends["I/O"]
    wire((x, y), (x - 12, y))
    netlabel(x - 12, y, f"TOUCH{k}", "left")
    x, y = ends["GND"]
    gnd(x, y, "left")
    S.append(f'<circle cx="{bxm + 70}" cy="1060" r="16" fill="none" stroke="{C["comp"]}" stroke-width="1.8"/>')
    S.append(f'<circle cx="{bxm + 70}" cy="1060" r="8" fill="{C["comp"]}" fill-opacity="0.18" stroke="{C["comp"]}" stroke-width="1.2"/>')
    text(bxm + 70, 1103, "pad", 10.5, C["muted"], "middle")
text(54, 1188, "Jumpers A and B open: active-high, momentary output (note 7).", 11.5, C["muted"], italic=True)
text(54, 1206, "IO0, IO1 and IO3 can wake the ESP32-C3 from deep sleep.", 11.5, C["muted"], italic=True)

# ---------------------------------------------------------------- 5 · microphone
block(825, 950, 415, 285, 5, "I2S MICROPHONE (INMP441)")
u5 = module(
    "U5", "INMP441 microphone (module)", 990, 1010, 150, 140,
    [("L", 1045, "SCK"), ("L", 1080, "WS"), ("L", 1115, "SD"),
     ("R", 1045, "VDD"), ("R", 1080, "GND"), ("R", 1115, "L/R")],
    ref_xy=(990, 1001), value_xy=(990, 1170),
)
for n, net in {"SCK": "MIC_SCK", "WS": "MIC_WS", "SD": "MIC_SD"}.items():
    x, y = u5[n]
    wire((x, y), (x - 13, y))
    netlabel(x - 13, y, net, "left")
x, y = u5["VDD"]
p3v3(x, y, "right")
x, y = u5["GND"]
wire((x, y), (x + 16, y))
gnd(x + 16, y, "right")
x, y = u5["L/R"]
wire((x, y), (x + 8, y), (x + 8, 1080))
junction(x + 8, 1080)
text(1065, 1074, "INMP441", 13.5, C["text"], "middle", bold=True)
text(1065, 1092, "MEMS · I²S", 11, C["muted"], "middle")
S.append(f'<circle cx="1065" cy="1122" r="7" fill="none" stroke="{C["comp"]}" stroke-width="1.6"/>')
S.append(f'<circle cx="1065" cy="1122" r="2.2" fill="{C["comp"]}"/>')
text(839, 1196, "L/R to GND: left channel.", 11.5, C["muted"], italic=True)
text(839, 1214, "Still draws 0.8 mA when idle (note 8).", 11.5, C["muted"], italic=True)

# ---------------------------------------------------------------- U1 pin table
rect(1252, 40, 508, 430, stroke=C["block"], sw=1.3, rx=10)
text(1266, 67, "U1 CONNECTIONS (ESP32-C3)", 13.5, C["text"], bold=True, ls=0.6)
cols = [("Pin", 62), ("Net", 104), ("Goes to", 122), ("Note", 196)]
tx0, ty0, rowh = 1264, 80, 22
rows = [
    ("IO0", "TOUCH1", "U6 · I/O", "Wakes from deep sleep"),
    ("IO1", "TOUCH2", "U7 · I/O", "Wakes from deep sleep"),
    ("IO2", "MIC_WS", "U5 · WS, R1", "Strapping: must be high"),
    ("IO3", "TOUCH3", "U8 · I/O", "Wakes from deep sleep"),
    ("IO4", "EPD_DC", "U4 · D/C", "—"),
    ("IO5", "EPD_RES", "U4 · RES", "—"),
    ("IO6", "EPD_SCL", "U4 · SCL", "SPI SCK"),
    ("IO7", "EPD_SDA", "U4 · SDA", "SPI MOSI"),
    ("IO8", "MIC_SCK", "U5 · SCK", "Strapping · on-board LED"),
    ("IO9", "—", "—", "BOOT: leave unconnected"),
    ("IO10", "EPD_CS", "U4 · CS", "—"),
    ("IO20", "EPD_BUSY", "U4 · BUSY", "Input (U0RXD)"),
    ("IO21", "MIC_SD", "U5 · SD", "Input (U0TXD)"),
    ("5V", "VSYS", "SW1", "Battery 3.0–4.2 V"),
    ("3V3", "+3V3", "U4–U8, R1", "U1 regulator output"),
    ("GND", "GND", "All", "Common ground"),
]
tw_total = sum(c[1] for c in cols)
rect(tx0, ty0, tw_total, rowh, fill=C["head"])
cx = tx0
for name, wcol in cols:
    text(cx + 7, ty0 + 15.5, name, 12, C["text"], bold=True)
    cx += wcol
for i, r in enumerate(rows):
    y = ty0 + rowh * (i + 1)
    if i % 2 == 1:
        rect(tx0, y, tw_total, rowh, fill=C["rowalt"])
    cx = tx0
    for j, (val, (_, wcol)) in enumerate(zip(r, cols)):
        if j == 0:
            text(cx + 7, y + 15.5, val, 12.5, C["text"], bold=True)
        elif j == 1:
            text(cx + 7, y + 15.5, val, 12.5, C["label"] if val != "—" else C["muted"], bold=val != "—")
        elif j == 2:
            text(cx + 7, y + 15.5, val, 12.5, C["text"])
        else:
            text(cx + 7, y + 15.5, val, 12, C["muted"])
        cx += wcol
tbl_bottom = ty0 + rowh * (len(rows) + 1)
line(tx0, ty0, tx0 + tw_total, ty0, C["block"], 1, cap="butt")
line(tx0, ty0 + rowh, tx0 + tw_total, ty0 + rowh, C["block"], 1, cap="butt")
line(tx0, tbl_bottom, tx0 + tw_total, tbl_bottom, C["block"], 1, cap="butt")

# ---------------------------------------------------------------- notes
rect(1252, 485, 508, 585, stroke=C["block"], sw=1.3, rx=10)
text(1266, 512, "NOTES", 13.5, C["text"], bold=True, ls=0.6)
notes = [
    "All parts are breakout modules: pin names follow each board's silkscreen. U1 is drawn from the top, USB-C up, with its pins in physical order.",
    "BT1 (−) goes only to B− on U3. B− is not GND: the system ground is OUT−, after the protection.",
    "The solar charger output (U2, BATT IN ±) goes to OUT+ / OUT− on U3. U3's IN+ / IN− and USB-C stay unconnected.",
    "No external diode on PV1: the CN3065 blocks reverse current in the dark (< 3 µA) and the module already has SS14 diodes. Use a panel with Voc ≤ 6 V.",
    "Turn SW1 off before plugging USB-C into U1: on most SuperMini boards the 5V pin is tied to USB VBUS.",
    "IO2, IO8 and IO9 are strapping pins. IO2 must be high at boot (R1 makes sure of it). IO2 and IO8 only carry signals driven by the ESP32. Leave IO9 (BOOT) unconnected.",
    "TTP223 (U6–U8): jumpers A and B open, so the output is active-high and momentary. Don't touch the pads at power-up: they calibrate at power-on.",
    "INMP441 (U5): with its clock stopped it still draws 0.8 mA, about 20 times U1 in deep sleep. Switching it off completely needs a free GPIO.",
    "For low power, remove the power LED on U1 (deep sleep ≈ 43 µA).",
]
ny = 538
for i, n in enumerate(notes, start=1):
    lines = wrap(n, 12.5, 446)
    text(1268, ny, f"{i}.", 12.5, C["comp"], bold=True)
    for k, ln in enumerate(lines):
        text(1292, ny + 17 * k, ln, 12.5, C["text"])
    ny += 17 * len(lines) + 8
notes_end = ny

# legend
ly = max(notes_end + 12, 958)
line(1266, ly - 14, 1746, ly - 14, C["block"], 1, cap="butt")
text(1266, ly + 6, "LEGEND", 12, C["text"], bold=True, ls=0.6)
r1y, r2y = ly + 34, ly + 66
netlabel(1270, r1y, "NET", "right")
text(1325, r1y + 4.4, "Same label = same wire", 12, C["text"])
junction(1278, r2y)
line(1266, r2y, 1290, r2y, C["wire"], 2)
line(1278, r2y - 10, 1278, r2y, C["wire"], 2)
text(1325, r2y + 4.4, "Wire junction", 12, C["text"])
nc(1528, r1y)
text(1548, r1y + 4.4, "Not connected", 12, C["text"])
p3v3(1520, r2y + 8, "up", "")
gnd(1540, r2y - 6, "down")
text(1560, r2y + 4.4, "3.3 V / ground (GND)", 12, C["text"])
legend_bottom = r2y + 22
assert legend_bottom <= 1062, f"legend does not fit in the notes panel: {legend_bottom}"

# ---------------------------------------------------------------- title block
tbx, tby, tbw = 1252, 1085, 520
rect(tbx, tby, tbw, 160, fill="#FFFFFF", stroke=C["frame"], sw=2)
for yy in (1121, 1167, 1206):
    line(tbx, yy, tbx + tbw, yy, C["frame"], 1, cap="butt")
line(1452, 1167, 1452, 1245, C["frame"], 1, cap="butt")
line(1612, 1167, 1612, 1206, C["frame"], 1, cap="butt")
line(1352, 1206, 1352, 1245, C["frame"], 1, cap="butt")


def cell(x, ycap, cap, val, size=14, bold=False, gap=19):
    text(x + 8, ycap, cap, 9.5, C["muted"], bold=True, ls=0.8)
    text(x + 8, ycap + gap, val, size, C["text"], bold=bold)


cell(tbx, 1097, "PROJECT", "SolarEpaperTouch · github.com/nico-ospitia/SolarEpaperTouch", 13, gap=17)
text(tbx + 8, 1133, "TITLE", 9.5, C["muted"], bold=True, ls=0.8)
text(tbx + 8, 1159, "System schematic", 21, C["text"], bold=True)
cell(tbx, 1179, "AUTHOR", "nico-ospitia")
cell(1452, 1179, "DATE", "2026-11-25")
cell(1612, 1179, "REVISION", "A", bold=True)
cell(tbx, 1218, "SIZE", "A3")
cell(1352, 1218, "SHEET", "1 of 1")
cell(1452, 1218, "STATUS", "Perfboard prototype")

# ---------------------------------------------------------------- output
svg = (
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
    f'font-family="{FONT}" role="img" aria-labelledby="sch-title">'
    f'<title id="sch-title">SolarEpaperTouch system schematic, revision A</title>'
    f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>' + "".join(S) + "</svg>\n"
)
os.makedirs(os.path.dirname(os.path.abspath(OUT_SVG)), exist_ok=True)
with open(OUT_SVG, "w", encoding="utf-8") as fh:
    fh.write(svg)

overlaps = []
for i in range(len(TEXT_BOXES)):
    a = TEXT_BOXES[i]
    for j in range(i + 1, len(TEXT_BOXES)):
        b = TEXT_BOXES[j]
        if a[0] < b[2] - 0.5 and b[0] < a[2] - 0.5 and a[1] < b[3] - 0.5 and b[1] < a[3] - 0.5:
            overlaps.append((a[4], b[4]))
print("SVG:", OUT_SVG, "| notes end at y =", round(notes_end), "| legend ends at", round(legend_bottom))
print("Overlapping text:", overlaps if overlaps else "none")
