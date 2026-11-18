"""Boho illustrations, drawn in SVG.

Patches of flat colour (suns, arches, pebbles, hills, waves, pots), cut paper leaves,
and loose hand lines on top. Paper grain runs through the colour and the lines wobble a
little, so it reads as made by hand.

Every drawing on the site is its own composition, made for what it shows; none is
repeated. Each one is grounded: it stands on a base, sits inside a window, or rests on
a hill, so none floats unfinished. Three sizes:
  heads    520 x 460, in page heads without a photo
  cards    520 x 460, small, on cards
  accents  300 x 240, a light touch beside a photo
"""
import math

CLAY, CLAY_SOFT, CLAY_PALE, ROSE, ROSE_SOFT, ROSE_PALE = "#B06F4F", "#E3B79D", "#F0DCCD", "#D98C93", "#F0C2BF", "#F6DEDA"
SAGE, SAGE_DEEP, SAGE_PALE, OCHRE, INK, CREAM = "#A9B79B", "#7F8F71", "#E3E9DA", "#D9A85B", "#4B3027", "#F6EEE5"


# ---------- shapes ----------

def _smooth(pts):
    d, k = "", len(pts)
    for i in range(k):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % k], pts[(i + 2) % k]
        if i == 0:
            d += f"M{p1[0]:.1f} {p1[1]:.1f}"
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d + "Z"


def pebble(cx, cy, rx, ry=None, shape=(1, .92, 1.05, .9, 1.06, .95), turn=0.0):
    ry = ry or rx
    k = len(shape)
    pts = [(cx + rx * f * math.cos(turn + 2 * math.pi * i / k), cy + ry * f * math.sin(turn + 2 * math.pi * i / k))
           for i, f in enumerate(shape)]
    return _smooth(pts)


def disc(cx, cy, r):
    return f"M{cx - r} {cy} a{r} {r} 0 1 0 {2 * r} 0 a{r} {r} 0 1 0 {-2 * r} 0Z"


def arch(x0, x1, base, top):
    r = (x1 - x0) / 2
    return f"M{x0} {base} V{top + r} A{r} {r} 0 0 1 {x1} {top + r} V{base} Z"


def arch_open(x0, x1, base, top):
    r = (x1 - x0) / 2
    return f"M{x0} {base} V{top + r} A{r} {r} 0 0 1 {x1} {top + r} V{base}"


def half(cx, base, r):
    return f"M{cx - r} {base} A{r} {r} 0 0 1 {cx + r} {base} Z"


def hill(cx, base, rx, ry):
    return f"M{cx - rx} {base} Q{cx} {base - 2 * ry} {cx + rx} {base} Z"


def ground(x0, x1, y, h=26):
    """A low, soft base for a scene to stand on."""
    return f"M{x0} {y} Q{(x0 + x1) / 2} {y - h * .55} {x1} {y} Q{(x0 + x1) / 2} {y + h * .9} {x0} {y} Z"


def waves(y, amp, length, x0, x1, bottom):
    d, x, up = f"M{x0} {y}", x0, True
    while x < x1:
        d += f" q{length / 2} {-amp if up else amp} {length} 0"
        x += length
        up = not up
    return d + f" V{bottom} H{x0} Z"


def leaf(x, y, ang, L, W):
    dx, dy = math.cos(ang), math.sin(ang)
    nx, ny = -dy, dx
    p = lambda a, b: (x + dx * a + nx * b, y + dy * a + ny * b)
    q = [p(0, 0), p(.3 * L, W), p(.8 * L, W * .8), p(L, 0), p(.8 * L, -W * .7), p(.3 * L, -W)]
    f = lambda t: f"{t[0]:.1f} {t[1]:.1f}"
    return f"M{f(q[0])}C{f(q[1])} {f(q[2])} {f(q[3])}C{f(q[4])} {f(q[5])} {f(q[0])}Z"


def frond(x, y, a0, a1, n, L, W, color, op=1):
    """A fan of narrow leaves from one point, like a cut paper plant."""
    out = ""
    for i in range(n):
        a = a0 + (a1 - a0) * i / max(1, n - 1)
        ln = L * (1 - .35 * abs(i - (n - 1) / 2) / ((n - 1) / 2 or 1))
        out += fill(leaf(x, y, a, ln, W), color, op)
    return out


def pot(cx, base, w, h):
    """A round bellied pot."""
    t = base - h
    return (f"M{cx - w * .32} {t} H{cx + w * .32} C{cx + w * .34} {t + h * .18} {cx + w * .62} {t + h * .3} {cx + w * .6} {t + h * .62}"
            f" C{cx + w * .58} {t + h * .9} {cx + w * .3} {base} {cx} {base} C{cx - w * .3} {base} {cx - w * .58} {t + h * .9} {cx - w * .6} {t + h * .62}"
            f" C{cx - w * .62} {t + h * .3} {cx - w * .34} {t + h * .18} {cx - w * .32} {t} Z")


def crescent(cx, cy, r, turn=0.0):
    a = math.radians(turn)
    x1, y1 = cx + r * math.cos(a - 1.25), cy + r * math.sin(a - 1.25)
    x2, y2 = cx + r * math.cos(a + 1.25), cy + r * math.sin(a + 1.25)
    return f"M{x1:.1f} {y1:.1f} A{r} {r} 0 1 0 {x2:.1f} {y2:.1f} A{r * .78:.1f} {r * .78:.1f} 0 1 1 {x1:.1f} {y1:.1f} Z"


def rect(x, y, w, h, r=6):
    return f"M{x + r} {y} H{x + w - r} Q{x + w} {y} {x + w} {y + r} V{y + h - r} Q{x + w} {y + h} {x + w - r} {y + h} H{x + r} Q{x} {y + h} {x} {y + h - r} V{y + r} Q{x} {y} {x + r} {y} Z"


# ---------- paint and ink ----------

def fill(d, color, op=1):
    o = f' opacity="{op}"' if op != 1 else ""
    return f'<path d="{d}" fill="{color}"{o}/>'


def line(d, w=2.6, dash="", color=INK):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"{da}/>'


def squiggle(x, y, n=3, w=30, h=16):
    d = f"M{x} {y}"
    for i in range(n):
        d += f" q{w / 2} {-h if i % 2 == 0 else h} {w} 0"
    return line(d)


def dots(points, r=3):
    return "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{INK}"/>' for x, y in points)


def rays(cx, cy, r0, r1, degrees, w=2.6):
    return "".join(line(f"M{cx + r0 * math.cos(math.radians(a)):.1f} {cy - r0 * math.sin(math.radians(a)):.1f}"
                        f"L{cx + r1 * math.cos(math.radians(a)):.1f} {cy - r1 * math.sin(math.radians(a)):.1f}", w) for a in degrees)


def sprig(x, y, ang, L, n=4):
    """A hand drawn stem with small leaves, in ink."""
    dx, dy = math.cos(ang), math.sin(ang)
    out = line(f"M{x} {y} l{dx * L:.1f} {dy * L:.1f}", 2.4)
    for i in range(1, n + 1):
        t = i / (n + 1)
        bx, by = x + dx * L * t, y + dy * L * t
        for s in (1, -1):
            a = ang + s * .7
            out += line(f"M{bx:.1f} {by:.1f} q{math.cos(a) * 9:.1f} {math.sin(a) * 9:.1f} {math.cos(a) * 18:.1f} {math.sin(a) * 18:.1f}", 2.2)
    return out


def _svg(name, colour, ink, box="0 0 520 460", clip="", cls="boho"):
    clip_def = f'<clipPath id="c-{name}"><path d="{clip}"/></clipPath>' if clip else ""
    if clip:
        colour = f'<g clip-path="url(#c-{name})">{colour}</g>'
    return (f'<svg class="{cls}" viewBox="{box}" aria-hidden="true" focusable="false"><defs>{clip_def}'
            f'<filter id="g-{name}" x="-10%" y="-10%" width="120%" height="120%">'
            '<feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="4" result="g"/>'
            '<feColorMatrix in="g" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.1 1.15" result="m"/>'
            '<feComposite in="SourceGraphic" in2="m" operator="in"/></filter>'
            f'<filter id="r-{name}" x="-10%" y="-10%" width="120%" height="120%">'
            '<feTurbulence type="fractalNoise" baseFrequency=".04" numOctaves="2" seed="7" result="w"/>'
            '<feDisplacementMap in="SourceGraphic" in2="w" scale="5" xChannelSelector="R" yChannelSelector="G"/></filter>'
            f'</defs><g filter="url(#g-{name})">{colour}</g><g filter="url(#r-{name})">{ink}</g></svg>')


# ---------- page heads ----------

def articles():
    """Reading: an open book whose pages are two soft curves, thoughts rising from it as pebbles and dots."""
    colour = (fill(ground(60, 470, 410, 26), CLAY_PALE)
              + fill("M262 392 C230 372 170 366 106 382 L100 250 C160 232 226 238 262 262 Z", CLAY_SOFT)
              + fill("M262 392 C294 372 354 366 418 382 L424 250 C364 232 298 238 262 262 Z", ROSE_SOFT)
              + fill(disc(190, 150, 28), OCHRE, .9) + fill(pebble(300, 118, 36, 30), SAGE) + fill(disc(372, 168, 16), ROSE)
              + fill(leaf(430, 405, -1.45, 110, 20), SAGE_DEEP, .85))
    ink = (line("M262 262 V392", 2.4) + line("M128 290 c40 -10 80 -12 116 -2 M128 318 c40 -10 80 -12 116 -2 M128 346 c36 -8 72 -10 112 -2", 2, "2 9")
           + line("M282 290 c36 -10 76 -8 116 2 M282 318 c36 -10 76 -8 116 2 M286 346 c34 -8 70 -6 108 2", 2, "2 9")
           + line("M262 238 C250 200 230 180 210 170", 2.2, "2 10") + dots([(250, 200), (330, 200), (96, 150)]) + squiggle(410, 90, 2, 36, 22))
    return _svg("articles", colour, ink)

def lectures():
    """Ideas rising: a half sun with its rays, a pebble, an arch and a cut leaf, on the ground."""
    colour = (fill(pebble(250, 240, 105), CLAY_SOFT, .9) + fill(half(260, 400, 150), OCHRE, .92)
              + fill(arch(400, 480, 410, 230), SAGE) + fill(pebble(95, 220, 52, shape=(1, .88, 1.08, .92, 1.02)), ROSE)
              + fill(leaf(40, 425, -1.1, 170, 34), SAGE_DEEP, .9) + fill(ground(30, 500, 410, 22), CLAY_PALE))
    ink = rays(260, 400, 168, 192, (50, 72, 94, 116, 138)) + squiggle(340, 60, 2, 44, 26) + dots([(70, 120), (92, 104), (58, 146)])
    return _svg("lectures", colour, ink)


def tashlich():
    """The sea inside an arched window: a sun, waves, a paper boat and pebbles on the shore."""
    colour = (fill(arch(70, 450, 440, 40), ROSE_PALE) + fill(disc(300, 175, 72), ROSE) + fill(waves(300, 14, 80, 0, 520, 460), SAGE, .95)
              + fill(waves(345, 12, 70, -30, 520, 460), SAGE_DEEP, .75) + fill(waves(392, 10, 90, 0, 520, 460), CLAY_SOFT)
              + fill(pebble(110, 420, 28, shape=(1, .8, 1.1, .9, 1)), OCHRE) + fill(pebble(160, 432, 20, shape=(1, .9, 1.1, .85)), CLAY, .85)
              + fill(pebble(400, 425, 24, shape=(1, .85, 1.05, .9, 1.1)), ROSE_SOFT))
    boat = line("M150 296 L220 296 L206 314 L164 314 Z") + line("M186 296 L186 252 L214 290", 2.4)
    ink = boat + line(arch_open(50, 470, 450, 20), 2.2, "2 10") + line("M10 120 q20 -24 40 0") + dots([(492, 150), (504, 172), (486, 190)])
    return _svg("tashlich", colour, ink, clip=arch(70, 450, 440, 40))


def nervous_system():
    """Layers that settle: a rainbow of arches standing on pebbles, a small sun."""
    colour = (fill(arch(70, 450, 400, 120), CLAY_SOFT) + fill(arch(125, 395, 400, 175), ROSE_SOFT)
              + fill(arch(180, 340, 400, 230), SAGE) + fill(arch(232, 288, 400, 282), OCHRE, .9)
              + fill(disc(440, 95, 34), ROSE) + fill(ground(40, 480, 402, 24), CLAY_PALE)
              + fill(pebble(60, 405, 30, 22), SAGE_DEEP, .85) + fill(pebble(460, 400, 26, 18), CLAY, .8))
    ink = line(arch_open(50, 470, 404, 100), 2.2, "2 10") + squiggle(40, 120, 2, 48, 28) + dots([(470, 200), (488, 222), (466, 240)])
    return _svg("nervous", colour, ink)


def education():
    """A team: three pebbles sitting together on one base, under an arch, with a sun and leaves."""
    colour = (fill(ground(60, 470, 380, 34), CLAY_PALE) + fill(pebble(150, 318, 70, 62), CLAY_SOFT) + fill(pebble(265, 300, 82, 76), SAGE)
              + fill(pebble(375, 322, 62, 56, shape=(1, .88, 1.08, .92, 1.02)), ROSE) + fill(disc(420, 110, 40), OCHRE, .9)
              + fill(leaf(60, 200, -.35, 120, 26), SAGE_DEEP, .85) + fill(leaf(70, 230, .25, 90, 20), SAGE, .9))
    ink = line(arch_open(90, 450, 300, 110), 2.4) + squiggle(200, 425, 2, 50, 24) + dots([(470, 220), (486, 242), (462, 258)])
    return _svg("education", colour, ink)


def gift_tashlich():
    """A sun touching the sea, inside a smaller window."""
    colour = (fill(arch(130, 390, 440, 90), ROSE_PALE) + fill(disc(260, 200, 80), ROSE) + fill(waves(270, 16, 90, 0, 520, 460), SAGE, .95)
              + fill(waves(340, 12, 76, -20, 520, 460), CLAY_SOFT) + fill(pebble(330, 405, 26, shape=(1, .86, 1.08, .92, 1)), OCHRE))
    ink = squiggle(60, 120, 2, 40, 24) + dots([(450, 110), (470, 126)]) + line(arch_open(110, 410, 440, 70), 2.2, "2 10")
    return _svg("gift-tashlich", colour, ink, clip=arch(130, 390, 440, 90))


def gift_kit():
    """Two pebbles leaning on each other inside a round window, a heart between them."""
    colour = (fill(disc(260, 230, 190), ROSE_PALE) + fill(ground(70, 450, 360, 28), CLAY_SOFT)
              + fill(pebble(205, 270, 95, 88), ROSE_SOFT) + fill(pebble(325, 280, 82, 76, shape=(1, .94, 1.04, .9, 1.06)), SAGE)
              + fill(disc(360, 140, 30), OCHRE, .9) + fill(leaf(120, 360, -1.9, 110, 22), SAGE_DEEP, .85))
    heart = line("M268 236 c-10 -18 -36 -12 -30 8 c4 14 30 28 30 28 c0 0 26 -14 30 -28 c6 -20 -20 -26 -30 -8 Z")
    ink = heart + line("M260 230 m-205 0 a205 205 0 0 1 410 0", 2.2, "2 10") + dots([(470, 300), (486, 322), (464, 338)])
    return _svg("gift-kit", colour, ink, clip=disc(260, 230, 190))


def lost():
    """A path that wanders to a small arched door."""
    colour = (fill(ground(40, 480, 380, 30), CLAY_PALE) + fill(arch(330, 430, 380, 190), SAGE) + fill(arch(358, 402, 380, 250), CREAM, .9)
              + fill(disc(150, 140, 46), ROSE) + fill(pebble(120, 360, 40, 28), CLAY_SOFT) + fill(leaf(450, 380, -1.4, 120, 22), SAGE_DEEP, .85))
    ink = line("M60 400 c60 -40 120 30 180 0 s70 -30 110 -10", 2.4, "2 10") + squiggle(230, 90, 2, 40, 24) + dots([(470, 160), (486, 180)])
    return _svg("lost", colour, ink)


# ---------- cards ----------

def card_pressure():
    """Balance: stones stacked on each other, a sun behind them."""
    colour = (fill(disc(330, 170, 80), OCHRE, .85) + fill(ground(90, 430, 400, 26), CLAY_PALE)
              + fill(pebble(260, 368, 110, 40), CLAY) + fill(pebble(258, 300, 84, 34, shape=(1, .9, 1.06, .94, 1.02, .96)), SAGE)
              + fill(pebble(264, 242, 60, 28), ROSE_SOFT) + fill(pebble(258, 196, 38, 22), CLAY_SOFT))
    ink = squiggle(70, 110, 2, 40, 24) + dots([(440, 300), (456, 320), (436, 338)]) + line("M150 420 h220", 2.2, "2 10")
    return _svg("c-pressure", colour, ink)


def card_education():
    """Three arched windows side by side, like a class."""
    colour = (fill(ground(50, 470, 400, 24), CLAY_PALE) + fill(arch(90, 190, 400, 210), CLAY_SOFT) + fill(arch(210, 310, 400, 170), SAGE)
              + fill(arch(330, 430, 400, 210), ROSE_SOFT) + fill(disc(260, 245, 26), OCHRE, .9))
    ink = (line(arch_open(108, 172, 400, 236), 2.2) + line(arch_open(348, 412, 400, 236), 2.2)
           + squiggle(380, 110, 2, 40, 24) + dots([(80, 140), (98, 124), (70, 166)]))
    return _svg("c-education", colour, ink)


def card_calm():
    """The eye of the storm: a calm sun in the middle of a spiral."""
    pts = [(260 + (8 + 1.95 * t) * math.cos(t * .3), 230 + (8 + 1.95 * t) * math.sin(t * .3)) for t in range(0, 66)]
    spiral = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    colour = (fill(disc(260, 230, 150), SAGE_PALE) + fill(disc(260, 230, 54), OCHRE, .9) + fill(ground(70, 450, 410, 26), CLAY_SOFT)
              + fill(pebble(400, 120, 34, 30), ROSE))
    ink = line(spiral, 2.4) + line("M70 90 l-10 24 M92 82 l-10 24 M114 90 l-10 24", 2.4) + dots([(450, 300), (466, 318)])
    return _svg("c-calm", colour, ink)


def card_nervous():
    """Waves that grow quieter inside a round window."""
    colour = (fill(disc(260, 230, 180), CLAY_PALE) + fill(waves(170, 26, 70, 60, 470, 460), ROSE_SOFT) + fill(waves(240, 18, 80, 40, 480, 460), SAGE)
              + fill(waves(310, 10, 90, 40, 480, 460), CLAY_SOFT) + fill(waves(370, 4, 100, 40, 480, 460), SAGE_DEEP, .7)
              + fill(disc(350, 105, 28), OCHRE, .9))
    ink = line("M260 230 m-195 0 a195 195 0 0 1 390 0", 2.2, "2 10") + dots([(90, 420), (106, 436)])
    return _svg("c-nervous", colour, ink, clip=disc(260, 230, 180))


def card_birth():
    """An embrace: a large curved shape holding a small round one, with the breath around them."""
    colour = (fill(ground(80, 440, 404, 26), CLAY_PALE)
              + fill("M300 160 C200 140 140 220 150 300 C158 368 220 404 292 398 C238 380 206 340 208 290 C210 236 248 196 300 160 Z", ROSE)
              + fill(disc(268, 300, 52), OCHRE, .92) + fill(pebble(372, 360, 36, 30), SAGE)
              + fill(leaf(392, 330, -1.3, 76, 16), SAGE_DEEP, .9))
    ink = (line("M262 290 m-118 0 a118 118 0 1 0 236 0", 2.2, "2 10") + line("M252 296 q16 14 32 0", 2.2)
           + dots([(120, 130), (140, 112), (110, 156)]) + squiggle(330, 120, 2, 40, 22))
    return _svg("c-birth", colour, ink)

def card_kit():
    """Two leaves leaning on each other, on a pebble."""
    colour = (fill(ground(90, 430, 400, 26), CLAY_PALE) + fill(pebble(260, 370, 120, 38), CLAY_SOFT)
              + fill(leaf(240, 360, -2.0, 220, 46), SAGE) + fill(leaf(280, 360, -1.15, 200, 42), ROSE_SOFT) + fill(disc(400, 110, 30), OCHRE, .9))
    ink = line("M262 150 c-6 -11 -22 -7 -18 5 c3 9 18 17 18 17 c0 0 15 -8 18 -17 c4 -12 -12 -16 -18 -5 Z", 2.4) + dots([(110, 160), (126, 180)])
    return _svg("c-kit", colour, ink)


def card_workbooks():
    """A stack of workbooks and a cup of tea on top, steam rising."""
    colour = (fill(ground(90, 430, 400, 24), CLAY_PALE) + fill(rect(140, 340, 240, 44), CLAY) + fill(rect(160, 296, 210, 44), SAGE)
              + fill(rect(150, 252, 220, 44), ROSE_SOFT) + fill("M226 196 H298 V236 C298 248 290 252 280 252 H244 C234 252 226 248 226 236 Z", OCHRE)
              + fill(disc(400, 130, 26), ROSE, .9))
    ink = (line("M180 318 h150 M172 274 h170", 2, "2 9") + line("M298 206 c22 0 22 30 0 30", 2.4)
           + line("M246 182 c-8 -12 8 -18 0 -30 M266 182 c-8 -12 8 -18 0 -30 M286 182 c-8 -12 8 -18 0 -30", 2.2) + dots([(110, 180), (128, 200)]))
    return _svg("c-workbooks", colour, ink)

def card_tashlich():
    """A paper boat on one wave, a sun going down behind it."""
    colour = (fill(half(260, 300, 110), ROSE) + fill(waves(300, 12, 70, 40, 480, 400), SAGE) + fill(ground(40, 480, 400, 24), CLAY_SOFT))
    ink = line("M200 290 L300 290 L282 314 L218 314 Z") + line("M250 290 L250 226 L208 282", 2.4) + squiggle(90, 120, 2, 40, 24) + dots([(420, 130), (438, 150)])
    return _svg("c-tashlich", colour, ink)


def card_meditation():
    """Breath: rings around a small sun, over a calm hill."""
    colour = (fill(hill(260, 400, 210, 80), SAGE) + fill(disc(260, 210, 44), ROSE) + fill(ground(40, 480, 402, 22), CLAY_PALE)
              + fill(leaf(70, 400, -1.3, 110, 22), SAGE_DEEP, .85))
    ink = (line("M260 210 m-80 0 a80 80 0 1 0 160 0 a80 80 0 1 0 -160 0", 2.2) + line("M260 210 m-118 0 a118 118 0 1 0 236 0 a118 118 0 1 0 -236 0", 2.2, "2 10")
           + dots([(440, 110), (458, 130)]))
    return _svg("c-meditation", colour, ink)


# ---------- accents beside photos ----------

def _accent(name, colour, ink):
    return _svg(name, colour, ink, box="0 0 300 240", cls="boho accent-art")


def accent_home():
    """Under the portrait: a small garden the circle rests on, a sun, two leaves and two stones."""
    colour = (fill(ground(30, 370, 236, 28), CLAY_PALE) + fill(disc(88, 156, 34), OCHRE, .9)
              + fill(leaf(150, 232, -1.95, 150, 28), SAGE) + fill(leaf(166, 234, -1.3, 120, 23), SAGE_DEEP, .85)
              + fill(pebble(256, 222, 38, 22), ROSE_SOFT) + fill(pebble(312, 228, 22, 14), CLAY_SOFT))
    ink = dots([(296, 140), (312, 158)])
    return _svg("a-home", colour, ink, box="0 0 400 270", cls="boho accent-art")

def accent_about():
    return _accent("a-about", frond(150, 220, -2.6, -.55, 7, 150, 18, SAGE) + fill(disc(240, 70, 30), ROSE),
                   dots([(60, 80), (76, 100), (52, 118)]))


def accent_therapy():
    return _accent("a-therapy", fill(arch(150, 250, 220, 60), CLAY_SOFT) + fill(disc(110, 80, 34), OCHRE, .9) + fill(pebble(90, 205, 40, 22), SAGE),
                   line(arch_open(170, 230, 220, 100), 2.2, color=CREAM) + dots([(40, 150), (56, 168)]))


def accent_breathwork():
    """Breath in waves: a sun, three hand drawn waves and a pebble on a small base."""
    colour = (fill(ground(30, 270, 214, 22), CLAY_PALE) + fill(disc(200, 84, 38), ROSE) + fill(pebble(96, 196, 46, 24), SAGE)
              + fill(pebble(168, 204, 24, 14), OCHRE, .9))
    ink = (line("M30 70 q30 -30 60 0 t60 0", 2.4) + line("M40 112 q25 -22 50 0 t50 0", 2.2, "2 9")
           + line("M60 150 q20 -18 40 0 t40 0", 2.2) + dots([(262, 150), (276, 168)]))
    return _accent("a-breath", colour, ink)

def accent_birth():
    return _accent("a-birth", fill(crescent(200, 90, 50, 210), OCHRE, .9) + fill(pebble(110, 190, 54, 36), ROSE_SOFT),
                   dots([(60, 70), (78, 54), (52, 96)]) + squiggle(170, 210, 2, 34, 18))


def accent_kotzim():
    """For the lecture on thorns: a spiky plant."""
    return _accent("a-kotzim", frond(150, 225, -2.8, -.35, 9, 150, 12, SAGE_DEEP) + fill(pebble(150, 228, 80, 18), CLAY_SOFT) + fill(disc(250, 60, 26), ROSE),
                   dots([(40, 90), (56, 70), (34, 118)]))


def accent_pressure():
    return _accent("a-pressure", fill(half(150, 210, 90), OCHRE, .88) + fill(pebble(60, 205, 40, 24), CLAY_SOFT),
                   rays(150, 210, 104, 124, (40, 65, 90, 115, 140), 2.4) + dots([(260, 120), (276, 140)]))


def accent_workshops():
    return _accent("a-workshops", fill(hill(110, 230, 110, 70), SAGE) + fill(hill(210, 230, 90, 52), CLAY_SOFT) + fill(disc(230, 70, 30), ROSE),
                   squiggle(30, 70, 2, 36, 20) + dots([(150, 50), (166, 66)]))


def accent_calm():
    return _accent("a-calm", fill(pebble(150, 190, 90, 40), SAGE_PALE) + fill(disc(150, 175, 34), OCHRE, .9),
                   line("M70 60 l-10 24 M95 52 l-10 24 M120 60 l-10 24 M200 52 l-10 24 M225 60 l-10 24", 2.4) + dots([(260, 160), (276, 176)]))


def accent_free():
    return _accent("a-free", fill(pebble(150, 200, 100, 30), CLAY_PALE) + fill(pot(150, 210, 80, 66), CLAY_SOFT),
                   sprig(150, 146, -1.57, 110, 4) + dots([(250, 70), (266, 90)]))


def accent_contact():
    return _accent("a-contact", fill(arch(170, 260, 220, 70), SAGE) + fill(arch(196, 234, 220, 130), CREAM, .9) + fill(disc(80, 70, 30), ROSE),
                   line("M20 225 c40 -26 80 10 130 -6", 2.4, "2 10") + dots([(120, 120), (136, 138)]))


# ---------- the four ways to work with Anna, for the circles on the home page ----------

def _figure(cx, base, w, h, color, head=None):
    """A person, half abstract: an arched body and a round head."""
    head = head or color
    r = w * .32
    return fill(arch(cx - w / 2, cx + w / 2, base, base - h), color) + fill(disc(cx, base - h - r - 4, r), head)


def way_therapy():
    """Two people side by side, a heart between them."""
    colour = fill(ground(30, 290, 222, 18), CLAY_PALE) + _figure(110, 222, 64, 80, CLAY) + _figure(210, 222, 58, 70, SAGE_DEEP)
    ink = line("M160 120 c-6 -11 -22 -7 -18 5 c3 9 18 17 18 17 c0 0 15 -8 18 -17 c4 -12 -12 -16 -18 -5 Z", 2.4) + dots([(270, 70), (282, 86)])
    return _svg("w-therapy", colour, ink, box="0 0 320 250", cls="boho way-art")


def way_breath():
    """Someone sitting still, the breath around them."""
    colour = (fill(ground(40, 280, 222, 18), CLAY_PALE) + fill("M86 222 C86 186 234 186 234 222 Z", SAGE)
              + fill(arch(132, 188, 200, 120), ROSE) + fill(disc(160, 102, 20), ROSE))
    ink = line("M160 102 m-44 0 a44 44 0 1 0 88 0 a44 44 0 1 0 -88 0", 2.2, "2 9") + line("M160 102 m-66 0 a66 66 0 0 1 132 0", 2, "2 11")
    return _svg("w-breath", colour, ink, box="0 0 320 250", cls="boho way-art")


def way_group():
    """A group: three people under one arch."""
    colour = (fill(ground(20, 300, 222, 18), CLAY_PALE) + _figure(92, 222, 50, 64, ROSE) + _figure(160, 222, 58, 78, CLAY)
              + _figure(228, 222, 50, 62, SAGE_DEEP))
    ink = line(arch_open(50, 270, 224, 40), 2.2, "2 10")
    return _svg("w-group", colour, ink, box="0 0 320 250", cls="boho way-art")


def way_lecture():
    """Someone speaking, the words going out as lines and dots, a small sun."""
    colour = fill(ground(40, 290, 222, 18), CLAY_PALE) + _figure(118, 222, 58, 84, SAGE_DEEP) + fill(disc(250, 80, 26), OCHRE, .92)
    ink = line("M170 120 q14 10 0 20 M186 112 q22 18 0 36 M202 104 q30 26 0 52", 2.4) + dots([(230, 150), (246, 164)])
    return _svg("w-lecture", colour, ink, box="0 0 320 250", cls="boho way-art")




# ---------- the lecture "on thorns": a sabra whose thorns turn into flowers ----------

KOTZIM_LABEL = "צבר עם קוצים, בכוננות. נשימה מגיעה, הקוצים מתרככים, ועל הצבר פורחים פרחים ושמש עולה."


def _paddle(cx, cy, rx, ry, rot, color):
    return (f'<path d="{pebble(cx, cy, rx, ry, shape=(1, .97, 1.02, .98, 1.01, .97, 1.02, .99))}" '
            f'transform="rotate({rot} {cx} {cy})" fill="{color}"/>')


def _areoles(cx, cy, rx, ry, rot, n_rings=((.42, 4), (.74, 7))):
    """The small tufts a sabra's paddle is dotted with, in loose rings."""
    out = ""
    a0 = math.radians(rot)
    for f, n in n_rings:
        for i in range(n):
            t = 2 * math.pi * i / n + f * 2
            x, y = rx * f * math.cos(t), ry * f * math.sin(t)
            X = cx + x * math.cos(a0) - y * math.sin(a0)
            Y = cy + x * math.sin(a0) + y * math.cos(a0)
            out += f'<circle class="k-mark" cx="{X:.1f}" cy="{Y:.1f}" r="2.6"/>'
    return out


def _spikes(cx, cy, rx, ry, rot, degrees):
    """Thorns standing out of a paddle's edge."""
    out = ""
    a0 = math.radians(rot)
    for d in degrees:
        t = math.radians(d)
        x0, y0 = rx * .98 * math.cos(t), ry * .98 * math.sin(t)
        x1, y1 = rx * 1.22 * math.cos(t), ry * 1.22 * math.sin(t)
        P = lambda x, y: (cx + x * math.cos(a0) - y * math.sin(a0), cy + x * math.sin(a0) + y * math.cos(a0))
        (X0, Y0), (X1, Y1) = P(x0, y0), P(x1, y1)
        out += f'<path class="k-spike" pathLength="1" d="M{X0:.1f} {Y0:.1f} L{X1:.1f} {Y1:.1f}"/>'
    return out


def _bloom(cx, cy, r, color, centre, delay):
    petals = "".join(
        f'<ellipse cx="{cx + r * .55 * math.cos(math.radians(a)):.1f}" cy="{cy + r * .55 * math.sin(math.radians(a)):.1f}" '
        f'rx="{r * .46:.1f}" ry="{r * .3:.1f}" transform="rotate({a} {cx + r * .55 * math.cos(math.radians(a)):.1f} {cy + r * .55 * math.sin(math.radians(a)):.1f})" fill="{color}"/>'
        for a in range(-90, 270, 60))
    return (f'<g class="k-bloom" style="transform-origin:{cx}px {cy}px;animation-delay:{delay}s">{petals}'
            f'<circle cx="{cx}" cy="{cy}" r="{r * .2:.1f}" fill="{centre}"/></g>')


def kotzim_animation(cls="kotzim-anim", uid="main"):
    """A sabra on alert: its thorns stand out and tremble. The breath arrives in a ring,
    the thorns draw back, flowers open on the paddles and a sun comes up. Then the thorns
    return gently and the cycle starts again: alert is not the enemy, it can be met."""
    paddles = [(232, 318, 74, 92, -8, SAGE_DEEP), (322, 250, 50, 66, 28, SAGE), (152, 232, 46, 62, -32, SAGE), (246, 178, 40, 54, 6, SAGE)]
    body = "".join(_paddle(*p) for p in paddles)
    marks = "".join(_areoles(cx, cy, rx, ry, rot) for cx, cy, rx, ry, rot, _ in paddles)
    spikes = (_spikes(232, 318, 74, 92, -8, (150, 172, 194, 12, 34)) + _spikes(322, 250, 50, 66, 28, (296, 330, 0, 30))
              + _spikes(152, 232, 46, 62, -32, (160, 196, 232, 268)) + _spikes(246, 178, 40, 54, 6, (216, 248, 284, 318)))
    blooms = (_bloom(250, 126, 30, OCHRE, CLAY, 0) + _bloom(352, 196, 24, ROSE, CLAY, .15) + _bloom(124, 182, 22, CLAY_SOFT, CLAY, .3)
              + _bloom(296, 214, 15, ROSE_SOFT, CLAY, .45))
    alarm = ('<g class="k-alarm">'
             '<path d="M430 236 l22 -10 M436 264 l24 0 M430 292 l22 10"/><path d="M66 236 l-22 -10 M60 264 l-24 0 M66 292 l-22 10"/></g>')
    g = f'url(#k-grain-{uid})'
    return (f'<svg class="{cls}" viewBox="0 0 500 460" role="img" aria-label="{KOTZIM_LABEL}">'
            f'<defs><filter id="k-grain-{uid}" filterUnits="userSpaceOnUse" x="0" y="0" width="500" height="460">'
            '<feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="4" result="g"/>'
            '<feColorMatrix in="g" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -.75 1.3" result="m"/>'
            '<feComposite in="SourceGraphic" in2="m" operator="in"/></filter></defs>'
            f'<g filter="{g}"><circle class="k-sun" cx="400" cy="110" r="42" fill="{OCHRE}"/></g>'
            f'<g filter="{g}"><path class="k-ground" d="{ground(50, 450, 412, 30)}" fill="{CLAY_PALE}"/>'
            f'<path class="k-base" d="{pebble(232, 408, 96, 20)}" fill="{CLAY_SOFT}"/></g>'
            f'<g class="k-cactus"><g class="k-plant" filter="{g}">{body}</g>'
            f'<g class="k-marks" fill="{CREAM}" opacity=".8">{marks}</g>'
            f'<g class="k-spikes" stroke="{INK}" stroke-width="2.6" stroke-linecap="round" stroke-dasharray="1 1">{spikes}</g>'
            f'<g class="k-blooms" filter="{g}">{blooms}</g></g>'
            f'<g stroke="{INK}" stroke-width="2.6" stroke-linecap="round">{alarm}</g>'
            f'<circle class="k-ring" cx="240" cy="270" r="190" fill="none" stroke="{INK}" stroke-width="2.4" stroke-dasharray="2 11" stroke-linecap="round"/>'
            '</svg>')


# ---------- grounds that a photo stands on ----------
# A band of earth half again as wide as the photo. The photo stands in its middle
# (x 70 to 350 of 420) with its lower edge in the earth, so only the two ends show:
# something growing at each side, and a sun or a moon half hidden behind the photo,
# so the drawing and the photo read as one scene.

EARTH = "M16 110 C90 102 150 106 210 104 C280 102 340 104 404 110 C420 116 420 134 404 138 C330 146 90 146 16 138 C0 134 0 116 16 110 Z"


def _ground_scene(name, left, right):
    """The earth is a band with soft round ends, as thick at its ends as in its middle, so it shows."""
    colour = fill(EARTH, CLAY, .3) + left[0] + right[0]
    ink = left[1] + right[1]
    return _svg(name, colour, ink, box="0 0 420 150", cls="boho ground-art")


def ground_therapy():
    """The clinic's garden: tall leaves on one side, a sun behind the photo and stones on the other."""
    return _ground_scene("gr-therapy",
                         (fill(leaf(40, 124, -2.3, 66, 13), SAGE, .85) + fill(leaf(54, 124, -1.72, 112, 22), SAGE)
                          + fill(leaf(68, 126, -1.2, 82, 16), SAGE_DEEP, .9), ""),
                         (fill(disc(356, 52, 28), OCHRE, .9) + fill(pebble(388, 117, 24, 12), ROSE_SOFT) + fill(pebble(368, 124, 13, 8), CLAY), ""))


def ground_about():
    return _ground_scene("gr-about",
                         (frond(44, 126, -2.4, -1.05, 6, 88, 12, SAGE), ""),
                         (fill(disc(360, 58, 26), ROSE) + fill(pebble(390, 118, 24, 12), ROSE_SOFT) + fill(pebble(370, 125, 11, 7), SAGE_DEEP), ""))


def ground_birth():
    return _ground_scene("gr-birth",
                         (fill(crescent(44, 52, 22, 210), OCHRE, .9) + fill(pebble(44, 119, 30, 13), SAGE) + fill(pebble(18, 125, 11, 7), ROSE), ""),
                         (fill(leaf(380, 126, -1.48, 100, 19), SAGE_DEEP, .9) + fill(leaf(392, 126, -1.0, 66, 13), SAGE), ""))


def ground_contact():
    return _ground_scene("gr-contact",
                         (fill(arch(12, 74, 126, 46), SAGE) + fill(arch(28, 58, 126, 78), CREAM, .9), ""),
                         (fill(disc(362, 62, 24), ROSE) + fill(pebble(392, 118, 24, 12), CLAY_SOFT) + fill(pebble(372, 125, 10, 7), OCHRE, .9), ""))


def ground_breathwork():
    return _ground_scene("gr-breath",
                         (fill(disc(60, 56, 24), ROSE) + fill(pebble(38, 119, 30, 13), SAGE), line("M6 90 q12 -10 24 0 t24 0", 2.2)),
                         (fill(pebble(388, 119, 26, 12), OCHRE, .9) + fill(pebble(368, 125, 10, 7), CLAY),
                          line("M362 64 q12 -10 24 0 t24 0", 2.2) + line("M368 88 q10 -8 20 0 t20 0", 2, "2 7")))


def ground_workshops():
    """A circle of people, as pebbles of different colours side by side, and hills."""
    return _ground_scene("gr-workshops",
                         (fill(hill(36, 124, 38, 40), SAGE) + fill(hill(72, 124, 26, 24), CLAY_SOFT), ""),
                         (fill(disc(358, 54, 22), OCHRE, .9) + fill(pebble(372, 118, 14, 11), ROSE) + fill(pebble(396, 120, 13, 10), SAGE_DEEP)
                          + fill(pebble(384, 102, 11, 8), ROSE_SOFT), ""))


def ground_pressure():
    return _ground_scene("gr-pressure",
                         (fill(pebble(40, 119, 30, 11), CLAY) + fill(pebble(40, 101, 22, 9), SAGE) + fill(pebble(40, 86, 13, 7), ROSE_SOFT), ""),
                         (fill(half(382, 123, 32), OCHRE, .9), rays(382, 123, 38, 50, (40, 70, 110, 140), 2)))


def ground_calm():
    return _ground_scene("gr-calm",
                         (fill(pebble(40, 118, 30, 13), SAGE_PALE) + fill(disc(40, 108, 11), OCHRE, .9), line("M20 56 l-5 12 M34 50 l-5 12 M48 56 l-5 12", 2)),
                         (fill(leaf(380, 126, -1.6, 100, 18), SAGE) + fill(leaf(392, 126, -1.1, 60, 12), SAGE_DEEP, .85), ""))


def ground_kotzim():
    """Two small sabra paddles on one side, a flower opening on the other."""
    return _ground_scene("gr-kotzim",
                         (fill(pebble(40, 98, 19, 25), SAGE_DEEP) + fill(pebble(62, 72, 12, 16), SAGE),
                          line("M22 88 l-7 -3 M58 92 l7 -3 M64 54 l1 -7 M46 76 l-6 -4", 1.8)),
                         (fill(pebble(388, 119, 26, 12), CLAY_SOFT)
                          + "".join(fill(pebble(388 + 10 * math.cos(math.radians(a)), 78 + 10 * math.sin(math.radians(a)), 8, 5.5, turn=math.radians(a)), ROSE)
                                    for a in range(-90, 270, 72))
                          + fill(disc(388, 78, 4.5), CLAY), line("M388 90 q2 14 0 26", 2)))


def free_head():
    """Small tools for calm, as a still life: a bowl of smooth stones in front of a hill and a
    low sun, a sprig growing beside it, the breath drawn above."""
    colour = (fill(half(290, 336, 150), OCHRE, .85) + fill(hill(140, 342, 132, 112), SAGE)
              + fill("M30 336 C140 324 380 324 490 336 C506 342 506 368 490 374 C380 388 140 388 30 374 C14 368 14 342 30 336 Z", CLAY_SOFT, .7)
              + fill(leaf(414, 352, -1.78, 190, 34), SAGE_DEEP, .92) + fill(leaf(430, 354, -1.12, 128, 24), SAGE)
              + fill(pebble(190, 292, 42, 32), ROSE) + fill(pebble(256, 284, 38, 30), SAGE_PALE) + fill(pebble(318, 296, 34, 27), CLAY_SOFT)
              + fill("M104 300 H396 C396 370 332 392 250 392 C168 392 104 370 104 300 Z", CLAY))
    ink = (line("M128 326 H372", 2.2, "2 9") + line("M290 336 m-186 0 a186 186 0 0 1 372 0", 2.2, "2 11")
           + line("M290 336 m-222 0 a222 222 0 0 1 444 0", 2, "2 13"))
    return _svg("free-head", colour, ink)


# ---------- the lecture "on thorns", as one line ----------
# One line, sharp and jagged like thorns, softens into a long wave of breath, and five small
# flowers open along it, from the middle outwards. Drawn in currentColor, so it reads on deep
# berry and on paper alike. Everything moves in one SVG clock (SMIL), so the line, the flowers
# and the three words stay together.

KOTZIM_LINE_LABEL = "קו חד ומשונן, כמו קוצים, שמתרכך לאט לגל רך של נשימה, ועליו נפתחים פרחים."
KOTZIM_DUR = 9  # seconds for one cycle


def _jag_and_wave(n=14, x0=24, x1=456, y=96, periods=2.5, amp=22):
    """The same 28 curve pieces twice: sharp straight teeth, and a long soft wave."""
    step = (x1 - x0) / n
    heights = [34, 52, 26, 60, 40, 22, 56, 30, 48, 24, 58, 36, 44, 28]
    xs = [x0 + j * step / 2 for j in range(2 * n + 1)]
    jy = [y if j % 2 == 0 else y - heights[j // 2] for j in range(2 * n + 1)]
    wy = [y + amp * math.sin(2 * math.pi * periods * (x - x0) / (x1 - x0)) for x in xs]

    def path(ys, soft):
        d = f"M{xs[0]:.1f} {ys[0]:.1f}"
        for j in range(2 * n):
            if soft:
                p0, p1 = (xs[max(j - 1, 0)], ys[max(j - 1, 0)]), (xs[j], ys[j])
                p2, p3 = (xs[j + 1], ys[j + 1]), (xs[min(j + 2, 2 * n)], ys[min(j + 2, 2 * n)])
                c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
                c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
            else:
                c1, c2 = (xs[j], ys[j]), (xs[j + 1], ys[j + 1])
            d += f" C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {xs[j + 1]:.1f} {ys[j + 1]:.1f}"
        return d
    return path(jy, False), path(wy, True)


def _flower(r=1.0):
    """A small, even flower: six slender petals around a centre."""
    petals = "".join(f'<ellipse cx="0" cy="{-6.2 * r:.1f}" rx="{2.3 * r:.1f}" ry="{5.6 * r:.1f}" transform="rotate({a})"/>' for a in range(0, 360, 60))
    return f'{petals}<circle r="{2 * r:.1f}" fill="#B8873E"/>'


def kotzim_line(words=True, cls="kotzim-line"):
    jag, wave = _jag_and_wave()
    ease = ".45 0 .55 1"
    line = (f'<path d="{wave}" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round">'
            f'<animate attributeName="d" dur="{KOTZIM_DUR}s" repeatCount="indefinite" values="{jag};{jag};{wave};{wave};{jag}" '
            f'keyTimes="0;.16;.4;.9;1" calcMode="spline" keySplines="{ease};{ease};{ease};{ease}"/></path>')
    # five flowers, evenly spaced, alternately on the troughs and the crests of the wave;
    # the middle one opens first, then the two beside it, then the two at the ends
    flowers = ""
    for t, start in ((.1, .48), (.3, .44), (.5, .4), (.7, .44), (.9, .48)):
        x = 24 + 432 * t
        y = 96 + 22 * math.sin(2 * math.pi * 2.5 * t)
        flowers += (f'<g transform="translate({x:.1f} {y:.1f})"><g>{_flower()}'
                    f'<animateTransform attributeName="transform" type="scale" dur="{KOTZIM_DUR}s" repeatCount="indefinite" '
                    f'values="0;0;1;1;0;0" keyTimes="0;{start};{start + .07:.2f};.86;.9;1" calcMode="spline" '
                    f'keySplines="{ease};{ease};{ease};{ease};{ease}"/></g></g>')
    text = ""
    h = 160
    if words:
        h = 214
        steps = (("כוננות", "1;1;.35;.35;1", "0;.16;.2;.94;1", 336),
                 ("נשימה", ".35;.35;1;1;.35;.35", "0;.16;.2;.4;.44;1", 240),
                 ("ויסות", ".35;.35;1;1;.35;.35", "0;.4;.44;.88;.92;1", 144))
        for word, vals, keys, x in steps:
            base = "1" if word == "ויסות" else ".35"
            text += (f'<text x="{x}" y="198" text-anchor="middle" font-size="18" opacity="{base}">{word}'
                     f'<animate attributeName="opacity" dur="{KOTZIM_DUR}s" repeatCount="indefinite" values="{vals}" keyTimes="{keys}"/></text>')
    return (f'<svg class="{cls}" viewBox="0 0 480 {h}" role="img" aria-label="{KOTZIM_LINE_LABEL}">'
            f'{line}<g fill="#D9A85B">{flowers}</g><g class="k-text" fill="currentColor">{text}</g></svg>')
