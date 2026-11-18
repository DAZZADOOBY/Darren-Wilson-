"""Room definitions: collision maps, palettes, raster gradients, scene art."""
import math, random
from PIL import Image, ImageDraw

W, H = 320, 200  # drawing canvas in square pixels; sampled to 160x200 mode 0

# Fixed pens shared by every room
FIXED = {0: None, 1: (0, 0, 1), 2: (15, 15, 15), 3: (13, 1, 1), 4: (15, 11, 2), 5: (8, 8, 9), 6: (4, 4, 5)}

MAPS = {}
ROOMS = []


def grad(stops, n=25):
    """stops: list of (band, (r,g,b)); linear interpolation per 8-line band."""
    out = []
    for i in range(n):
        for (b0, c0), (b1, c1) in zip(stops, stops[1:]):
            if b0 <= i <= b1:
                t = 0 if b1 == b0 else (i - b0) / (b1 - b0)
                out.append(tuple(int(round(c0[k] + (c1[k] - c0[k]) * t)) for k in range(3)))
                break
        else:
            out.append(stops[-1][1])
    return out


class Scene:
    def __init__(self, pal):
        self.img = Image.new('P', (W, H), 0)
        self.d = ImageDraw.Draw(self.img)
        self.pal = pal

    def rect(self, x0, y0, x1, y1, pen):
        self.d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=pen)

    def dither(self, x0, y0, x1, y1, a, b, level=2):
        """level 0..4 : proportion of pen b (2x2 ordered dither at mode 0 resolution)."""
        bay = [[0, 2], [3, 1]]
        px = self.img.load()
        for y in range(max(0, y0), min(H, y1)):
            for x in range(max(0, x0), min(W, x1)):
                px[x, y] = b if bay[y & 1][(x >> 1) & 1] < level else a

    def ellipse(self, x0, y0, x1, y1, pen):
        self.d.ellipse([x0, y0, x1, y1], fill=pen)

    def poly(self, pts, pen):
        self.d.polygon(pts, fill=pen)

    def line(self, pts, pen, w=1):
        self.d.line(pts, fill=pen, width=w)

    def windows(self, x0, y0, x1, y1, wx, wy, gx, gy, pen, lit=None, litpen=None, seed=1):
        r = random.Random(seed)
        y = y0
        while y + wy <= y1:
            x = x0
            while x + wx <= x1:
                p = litpen if (lit and r.random() < lit) else pen
                self.rect(x, y, x + wx, y + wy, p)
                x += wx + gx
            y += wy + gy

    def stars(self, y1, n, seed=5, pen=2):
        r = random.Random(seed)
        px = self.img.load()
        for _ in range(n):
            x, y = r.randrange(0, W, 2), r.randrange(17, y1)
            if px[x, y] == 0:
                px[x, y] = pen
                px[x + 1, y] = pen

    def to_mode0(self):
        px = self.img.load()
        return [[px[x * 2, y] for x in range(160)] for y in range(200)]


# ---------------- generic structure drawing from the collision map ----------------

def cell_rect(c, r):
    return c * 16, r * 8, c * 16 + 16, r * 8 + 8


def draw_structures(sc, m, style):
    top, body, shade = style['top'], style['body'], style['shade']
    for r in range(25):
        for c in range(20):
            ch = m[r][c]
            x0, y0, x1, y1 = cell_rect(c, r)
            if ch == '=' or (ch in 'HG' and False):
                sc.rect(x0, y0, x1, y0 + 2, top)
                sc.rect(x0, y0 + 2, x1, y0 + 6, body)
                sc.rect(x0, y0 + 6, x1, y0 + 7, shade)
                if style.get('rivets'):
                    sc.rect(x0 + 6, y0 + 3, x0 + 8, y0 + 4, top)
                if style.get('girder'):
                    sc.line([(x0, y0 + 6), (x0 + 8, y0 + 2), (x1, y0 + 6)], shade)
            elif ch == '#':
                gtop = style.get('gtop', top)
                gb = style.get('gbody', body)
                if r > 0 and m[r - 1][c] not in '#G':
                    sc.rect(x0, y0, x1, y0 + 2, gtop)
                    sc.rect(x0, y0 + 2, x1, y1, gb)
                    sc.rect(x0 + (c * 7) % 16, y0 + 2, x0 + (c * 7) % 16 + 1, y1, shade)
                else:
                    sc.dither(x0, y0, x1, y1, gb, shade, 1)
            elif ch == 'W':
                if r > 0 and m[r - 1][c] != 'W':
                    sc.rect(x0, y0, x1, y0 + 1, 2)
                    sc.rect(x0, y0 + 1, x1, y1, 0)
                    sc.rect(x0 + (c * 5) % 12, y0 + 4, x0 + (c * 5) % 12 + 4, y0 + 5, 2)
                else:
                    sc.rect(x0, y0, x1, y1, 0)
    # ladders
    for r in range(25):
        for c in range(20):
            if m[r][c] == 'H' or (m[r][c] == 'G' and ladder_under_gate(m, c, r)):
                x0, y0, x1, y1 = cell_rect(c, r)
                sc.rect(x0 + 2, y0, x0 + 4, y1, style.get('lrail', 5))
                sc.rect(x0 + 12, y0, x0 + 14, y1, style.get('lrail', 5))
                sc.rect(x0 + 4, y0 + 3, x0 + 12, y0 + 4, style.get('lrung', 2))
                sc.rect(x0 + 4, y0 + 7, x0 + 12, y0 + 8, style.get('lrung', 2))
                sc.rect(x0 + 4, y0 + 4, x0 + 12, y0 + 5, 1)


def ladder_under_gate(m, c, r):
    return (r > 0 and m[r - 1][c] == 'H') or (r < 24 and m[r + 1][c] == 'H')


def hud_panel(sc):
    sc.rect(0, 0, W, 16, 1)
    sc.rect(0, 15, W, 16, 6)


# ---------------- landmarks ----------------

def skyline(sc, base, pen, seed, hmin=20, hmax=60, wmin=16, wmax=40, winpen=None, lit=0.25):
    r = random.Random(seed)
    x = 0
    while x < W:
        w = r.randrange(wmin, wmax) // 2 * 2
        h = r.randrange(hmin, hmax)
        sc.rect(x, base - h, x + w, base, pen)
        if winpen is not None:
            sc.windows(x + 2, base - h + 4, x + w - 2, base, 2, 3, 4, 4, pen, lit, winpen, seed + x)
        x += w


def rotunda(sc, cx, base, top, body, glass, lit):
    sc.rect(cx - 18, top, cx + 18, base, body)
    for y in range(top + 4, base - 2, 6):
        sc.rect(cx - 16, y, cx + 16, y + 3, glass)
        for x in range(cx - 16, cx + 16, 6):
            sc.rect(x, y, x + 2, y + 3, lit if (x * 3 + y) % 7 == 0 else glass)
    sc.rect(cx - 18, top - 3, cx + 18, top, 5)
    sc.dither(cx + 8, top, cx + 18, base, body, 1, 1)


def blob(sc, x0, y0, x1, y1, body, disc, shade):
    sc.ellipse(x0, y0, x1, y1 + (y1 - y0), body)
    sc.rect(x0, y1, x1 + 1, y1 + (y1 - y0), body)
    for yy in range(y0 + 4, y1 + (y1 - y0), 7):
        for xx in range(x0 + 4, x1, 9):
            ox = 4 if (yy // 7) % 2 else 0
            px, py = xx + ox, yy
            if sc.img.getpixel((min(px, W - 1), min(py, H - 1))) == body:
                sc.ellipse(px - 2, py - 2, px + 2, py + 2, disc)
                sc.rect(px - 1, py + 1, px + 2, py + 2, shade)


def spire(sc, cx, base, h, body, shade):
    sc.rect(cx - 10, base - h // 2, cx + 10, base, body)
    sc.poly([(cx - 6, base - h // 2), (cx, base - h), (cx + 6, base - h // 2)], body)
    sc.poly([(cx, base - h), (cx + 6, base - h // 2), (cx + 2, base - h // 2)], shade)
    sc.rect(cx - 3, base - h // 2 + 6, cx + 3, base - h // 2 + 14, 1)


def pagoda(sc, cx, base, roof, wall, trim):
    y = base
    w = 34
    for i in range(5):
        sc.rect(cx - w // 2 + 4, y - 14, cx + w // 2 - 4, y, wall)
        sc.rect(cx - 3, y - 11, cx + 3, y - 3, 1)
        y -= 14
        sc.poly([(cx - w // 2 - 6, y + 2), (cx - w // 2 + 2, y - 4), (cx + w // 2 - 2, y - 4), (cx + w // 2 + 6, y + 2)], roof)
        sc.rect(cx - w // 2 - 6, y + 1, cx + w // 2 + 6, y + 3, trim)
        w -= 5
    sc.rect(cx - 1, y - 14, cx + 1, y - 4, trim)
    sc.ellipse(cx - 2, y - 17, cx + 2, y - 13, 4)


def bt_tower(sc, cx, base, top, body, dish, shade):
    sc.rect(cx - 9, top + 30, cx + 9, base, body)
    sc.dither(cx + 3, top + 30, cx + 9, base, body, shade, 2)
    for y in range(top, top + 30, 7):
        sc.rect(cx - 13, y, cx + 13, y + 4, dish)
        sc.rect(cx - 13, y + 4, cx + 13, y + 5, shade)
    for (dx, dy) in ((-16, 6), (14, 13), (-17, 20)):
        sc.ellipse(cx + dx - 4, top + dy - 3, cx + dx + 4, top + dy + 3, 2)
    sc.rect(cx - 1, top - 20, cx + 1, top, shade)
    sc.rect(cx - 1, top - 22, cx + 1, top - 20, 3)


def viaduct(sc, y, h, body, dark, shade):
    sc.rect(0, y, W, y + h, body)
    for x in range(-10, W, 48):
        sc.ellipse(x + 6, y + 10, x + 42, y + h + 24, dark)
    for yy in range(y, y + h, 4):
        for xx in range((yy // 4 % 2) * 6, W, 12):
            sc.rect(xx, yy, xx + 1, yy + 1, shade)


def narrowboat(sc, x0, x1, ytop, hull, roof, trim):
    sc.rect(x0, ytop, x1, ytop + 3, roof)
    sc.rect(x0 + 4, ytop + 3, x1 - 4, ytop + 9, trim)
    for x in range(x0 + 10, x1 - 10, 14):
        sc.rect(x, ytop + 4, x + 6, ytop + 8, 1)
    sc.poly([(x0 - 8, ytop + 9), (x1 + 10, ytop + 9), (x1, ytop + 16), (x0, ytop + 16)], hull)
    sc.rect(x0, ytop + 11, x1, ytop + 12, 4)


def pillar(sc, x, y0, y1, body, shade):
    sc.rect(x, y0, x + 14, y1, body)
    sc.rect(x + 10, y0, x + 14, y1, shade)


# ---------------- room definitions ----------------

def room(name, mapstr, pal, gradient, art, style, nb, gate_req=0):
    m = [row for row in mapstr.strip().split('\n')]
    m = [r.strip() for r in m]
    assert len(m) == 25, (name, len(m))
    for r in m:
        assert len(r) == 20, (name, r, len(r))
    ROOMS.append(dict(name=name, map=m, pal=pal, grad=gradient, art=art, style=style, nb=nb, gate_req=gate_req))


def pal_with(free):
    p = dict(FIXED)
    for i, c in enumerate(free):
        p[7 + i] = c
    return p


# 0 THE BULLRING ------------------------------------------------------------
def art_bullring(sc, m):
    skyline(sc, 140, 7, 11, 30, 70, 20, 44, 15, 0.15)
    rotunda(sc, 160, 150, 52, 15, 8, 4)
    spire(sc, 40, 150, 100, 10, 11)
    blob(sc, 210, 70, 320, 110, 8, 9, 10)
    sc.rect(0, 150, W, 184, 11)
    sc.dither(0, 150, W, 184, 11, 7, 1)
    # market awnings
    for i, x in enumerate(range(8, 300, 52)):
        p = 13 if i % 2 else 14
        sc.rect(x, 160, x + 40, 166, p)
        for k in range(x, x + 40, 8):
            sc.rect(k, 160, k + 4, 166, 2)
        sc.rect(x + 2, 166, x + 38, 184, 12)
        sc.rect(x + 4, 170, x + 36, 172, 7)
    # bronze bull-ish sculpture plinth (abstract)
    sc.rect(130, 176, 160, 184, 12)


room('THE BULLRING', '''
....................
....................
....................
....................
....................
....................
...........L........
.........===H====...
..L.........H.......
=====H......H.......
.....H......H.......
.....H......H.......
.....H......H.......
.....H......H....L..
.....H...=====H=====
.....H........H.....
.....H........H.....
.....H........H.....
.....H........H.....
.....H........H.....
.....H........H.....
...L.H........H.....
.....H........H...1.
####################
####################
''', pal_with([(3, 2, 6), (2, 5, 11), (9, 11, 14), (10, 6, 3), (6, 4, 3), (13, 9, 4), (3, 8, 4), (12, 3, 2), (7, 7, 9)]),
     grad([(0, (1, 0, 4)), (3, (3, 1, 7)), (9, (10, 3, 8)), (14, (15, 7, 4)), (19, (15, 12, 6)), (24, (15, 14, 9))]),
     art_bullring, dict(top=13, body=12, shade=11, gtop=15, gbody=7, rivets=True), dict(E=1))


# 1 NEW STREET --------------------------------------------------------------
def art_newstreet(sc, m):
    # mirrored steel facade with curved panels
    sc.rect(0, 30, W, 150, 7)
    for x in range(0, W, 24):
        for y in range(30, 150, 10):
            sc.poly([(x, y), (x + 24, y + 3), (x + 24, y + 10), (x, y + 7)], 8 if (x // 24 + y // 10) % 2 else 9)
    sc.dither(0, 30, W, 60, 7, 0, 2)
    # big glass "eye" screens
    for cx in (60, 250):
        sc.ellipse(cx - 34, 70, cx + 34, 120, 10)
        sc.ellipse(cx - 28, 75, cx + 28, 115, 11)
        sc.dither(cx - 20, 80, cx + 20, 110, 11, 15, 1)
    # departure board
    sc.rect(110, 150, 210, 178, 1)
    sc.rect(112, 152, 208, 176, 6)
    for i, y in enumerate(range(154, 176, 5)):
        sc.rect(114, y, 114 + 40 + (i * 13) % 50, y + 3, 4)
    sc.rect(0, 150, 108, 184, 12)
    sc.rect(212, 150, W, 184, 12)
    sc.windows(4, 154, 104, 180, 6, 6, 4, 4, 13, 0.3, 4, 3)
    sc.windows(216, 154, W, 180, 6, 6, 4, 4, 13, 0.3, 4, 4)


room('NEW STREET', '''
....................
....................
....................
....................
....................
....................
......L.............
....=======H........
...........H....L...
...........H.=====H=
...........H......H.
..L........H......H.
======H....H......H.
......H....H......H.
......H....H......H.
......H....H..L...H.
......H....H=====.H.
......H....H......H.
......H....H......H.
......H....H......H.
......H....H......H.
...L..H....H......H.
..1...H....H.....2H.
########GGG#########
#########H##########
''', pal_with([(4, 5, 7), (9, 10, 12), (12, 13, 14), (2, 3, 6), (5, 9, 12), (3, 3, 4), (2, 2, 3), (10, 10, 11), (6, 12, 15)]),
     grad([(0, (2, 4, 9)), (6, (5, 9, 13)), (12, (9, 12, 15)), (24, (12, 14, 15))]),
     art_newstreet, dict(top=9, body=13, shade=12, gtop=15, gbody=13, girder=True), dict(W=0, E=2, S=4), gate_req=6)


# 2 CHINESE QUARTER ---------------------------------------------------------
def art_chinese(sc, m):
    sc.ellipse(230, 30, 270, 70, 15)   # big moon
    sc.ellipse(238, 36, 262, 60, 4)
    sc.stars(90, 40, 9)
    skyline(sc, 150, 7, 21, 30, 80, 24, 50, 14, 0.2)
    pagoda(sc, 90, 150, 9, 10, 11)
    # theatre with marquee
    sc.rect(190, 90, 300, 150, 12)
    sc.rect(186, 86, 304, 92, 11)
    sc.rect(196, 100, 294, 112, 1)
    for x in range(198, 292, 6):
        sc.rect(x, 103, x + 3, 109, 4 if (x // 6) % 2 else 14)
    sc.windows(196, 118, 294, 148, 8, 10, 6, 6, 13, 0.4, 14, 7)
    # strings of lanterns across the street
    for y0 in (40, 64):
        pts = [(x, y0 + int(8 * math.sin(x / 50.0))) for x in range(0, W, 4)]
        sc.line(pts, 6)
        for x in range(10, W, 26):
            y = y0 + int(8 * math.sin(x / 50.0))
            sc.ellipse(x - 3, y + 1, x + 3, y + 7, 3)
            sc.rect(x - 1, y + 2, x + 1, y + 6, 4)
    # street level
    sc.rect(0, 150, W, 184, 8)
    sc.dither(0, 150, W, 160, 8, 7, 2)
    # paifang style arch (generic)
    sc.rect(120, 120, 126, 184, 9)
    sc.rect(194, 120, 200, 184, 9)
    sc.rect(112, 112, 208, 120, 9)
    sc.poly([(104, 112), (216, 112), (206, 104), (114, 104)], 10)
    sc.rect(150, 122, 170, 132, 11)


room('CHINESE QUARTER', '''
....................
....................
....................
....................
.........L..........
.......=====H.......
............H.......
............H.......
.L..........H.......
=====H......H...L...
.....H....=====H====
.....H.........H....
.....H.........H....
.....H.........H....
.....H.........H....
.....H.L.......H....
===H=====......H....
...H...........H....
...H...........H...G
...H...........H...G
...H...........H...G
...H...........H...G
...H....L..1...H...G
####################
####################
''', pal_with([(2, 1, 4), (5, 2, 4), (12, 1, 2), (6, 2, 1), (14, 9, 1), (5, 3, 3), (3, 2, 3), (15, 6, 9), (15, 14, 10)]),
     grad([(0, (0, 0, 2)), (8, (2, 1, 6)), (16, (6, 2, 8)), (20, (9, 3, 6)), (24, (12, 5, 5))]),
     art_chinese, dict(top=11, body=9, shade=10, gtop=11, gbody=12, rivets=True), dict(W=1, E=3), gate_req=18)


# 3 GAS STREET BASIN ------------------------------------------------------------
def art_gasstreet(sc, m):
    skyline(sc, 120, 8, 31, 40, 90, 24, 60, 14, 0.3)
    # warehouse brick buildings along the canal
    sc.rect(0, 90, 120, 176, 9)
    sc.rect(220, 80, W, 176, 9)
    for y in range(90, 176, 3):
        for x in range((y // 3 % 2) * 4, W, 8):
            if not (120 <= x < 220):
                sc.rect(x, y, x + 1, y + 1, 10)
    sc.windows(10, 100, 110, 170, 8, 12, 8, 10, 1, 0.5, 14, 2)
    sc.windows(230, 92, W, 170, 8, 12, 8, 10, 1, 0.5, 14, 3)
    # brick bridge arch over canal
    sc.rect(120, 110, 220, 130, 11)
    sc.ellipse(128, 118, 212, 190, 0)
    for x in range(120, 220, 6):
        sc.rect(x, 110, x + 3, 112, 12)
    # water reflection uses pen 0 gradient
    sc.rect(0, 176, W, 184, 7)
    # narrowboat (platform at row 21)
    narrowboat(sc, 82, 238, 168, 7, 13, 15)


room('GAS STREET BASIN', '''
....................
....................
................H...
...............GGG..
................H...
................H...
...L............H...
==========H.....H...
..........H.....H...
..........H.....H...
..........H.....H...
..........H.....H...
..........H.....H...
..........H...L.H...
..........H..=====H=
..........H.......H.
..........H.......H.
..........H.......H.
..L.......H.......H.
..........H.......H.
..........H..L....H.
.....==========...H.
................2.H.
######WWWWWWWW######
######WWWWWWWW######
''', pal_with([(1, 4, 3), (3, 4, 6), (8, 3, 2), (5, 2, 1), (7, 4, 3), (10, 5, 3), (2, 7, 5), (15, 13, 7), (12, 2, 2)]),
     grad([(0, (6, 2, 7)), (8, (12, 5, 6)), (15, (15, 10, 5)), (21, (15, 12, 7)), (22, (2, 5, 6)), (24, (1, 3, 5))]),
     art_gasstreet, dict(top=13, body=11, shade=10, gtop=13, gbody=11, rivets=False), dict(W=2, N=6), gate_req=26)


# 4 DIGBETH ---------------------------------------------------------------------
def art_digbeth(sc, m):
    skyline(sc, 100, 7, 41, 20, 50, 20, 40, None)
    viaduct(sc, 100, 34, 9, 1, 10)
    # custard-yellow factory with big chimney
    sc.rect(20, 30, 32, 100, 10)
    sc.rect(18, 26, 34, 30, 6)
    sc.rect(180, 60, 300, 100, 11)
    sc.windows(186, 66, 296, 98, 10, 10, 6, 6, 12, 0.0, None, 4)
    # graffiti wall
    sc.rect(0, 134, W, 184, 13)
    r = random.Random(77)
    for i in range(14):
        x = r.randrange(0, W - 40)
        y = r.randrange(140, 176)
        p = r.choice([14, 15, 3, 4, 8])
        sc.ellipse(x, y, x + r.randrange(20, 50), y + r.randrange(6, 12), p)
        sc.line([(x + 4, y + 4), (x + 30, y + 2)], 1, 2)
    sc.dither(0, 134, W, 138, 13, 1, 2)


room('DIGBETH', '''
....................
....................
.........H..........
.........H..........
.........H..........
.........H.....L....
...L.....H...===H===
=========H......H...
.........H......H...
.........H......H...
.........H......H...
.........H......H...
..L......H......H...
======H..H......H...
......H..H......H...
......H..H...L..H...
......H..H..====H===
......H..H......H...
......H..H......H...
......H..H......H...
......H..H......H...
......H..H......H.L.
..2...H..H..1...H...
####################
####################
''', pal_with([(4, 2, 5), (8, 4, 3), (5, 3, 3), (15, 12, 4), (12, 9, 3), (7, 3, 2), (6, 6, 6), (2, 12, 11), (14, 3, 10)]),
     grad([(0, (2, 1, 3)), (6, (6, 3, 6)), (12, (12, 6, 4)), (16, (15, 9, 4)), (24, (15, 12, 6))]),
     art_digbeth, dict(top=10, body=8, shade=12, gtop=12, gbody=8, rivets=True), dict(N=1, E=5))


# 5 SPAGHETTI JUNCTION -------------------------------------------------------
def art_spaghetti(sc, m):
    sc.stars(60, 30, 13)
    skyline(sc, 110, 7, 51, 10, 40, 30, 60, 15, 0.1)
    # sweeping road decks
    for k, (yc, amp) in enumerate(((60, 18), (88, 14), (120, 10))):
        for x in range(0, W, 2):
            y = int(yc + amp * math.sin((x + k * 60) / 60.0))
            sc.rect(x, y, x + 2, y + 6, 9)
            sc.rect(x, y + 6, x + 2, y + 9, 10)
            if x % 24 == 0:
                sc.rect(x, y - 2, x + 2, y, 5)
    for x in range(14, W, 56):
        pillar(sc, x, 70, 184, 11, 10)
    # car lights
    r = random.Random(8)
    for i in range(20):
        x = r.randrange(0, W, 2)
        k = r.randrange(3)
        yc, amp = ((60, 18), (88, 14), (120, 10))[k]
        y = int(yc + amp * math.sin((x + k * 60) / 60.0))
        sc.rect(x, y + 2, x + 2, y + 3, 4 if i % 2 else 3)
    sc.rect(0, 176, W, 184, 12)


room('SPAGHETTI JUNCTION', '''
....................
....................
....................
....................
....................
....L..........L....
..========H..====H=.
..........H......H..
..........H......H..
..........H......H..
..........H......H..
..........H......H..
..........H......H..
..L.......H.L...2H..
=====H...=====H====.
.....H........H.....
.....H........H.....
.....H........H.....
.....H........H.....
.....H........H.....
.....H........H.....
.....H........H..L..
.....H........H..1..
#######WWWWWW#######
#######WWWWWW#######
''', pal_with([(1, 2, 4), (4, 4, 6), (9, 9, 10), (5, 5, 7), (7, 7, 8), (3, 3, 3), (8, 8, 9), (2, 3, 4), (13, 12, 6)]),
     grad([(0, (0, 0, 2)), (8, (1, 1, 5)), (14, (4, 2, 7)), (19, (8, 4, 6)), (22, (1, 3, 5)), (24, (0, 2, 4))]),
     art_spaghetti, dict(top=9, body=11, shade=10, gtop=9, gbody=11, rivets=False), dict(W=4))


# 6 BT TOWER ------------------------------------------------------------------
def art_bttower(sc, m):
    sc.stars(140, 70, 21)
    skyline(sc, 184, 7, 61, 20, 60, 16, 30, 15, 0.35)
    bt_tower(sc, 250, 184, 40, 9, 10, 11)
    # steel lattice behind platforms
    for x in range(0, W, 40):
        sc.line([(x, 184), (x + 40, 40)], 8)
        sc.line([(x + 40, 184), (x, 40)], 8)
    sc.rect(0, 180, W, 184, 8)


room('BT TOWER', '''
....................
....................
....................
....................
.......L............
.....=====H.........
..........H.........
..........H.........
..L.......H....L....
=====H....H...H=====
.....H....H...H.....
.....H....H...H.....
.....H....H...H.....
.....H....H...H.....
.....H....H...H.....
.....H....H...H.L...
==H===....H..=====H=
..H.......H.......H.
..H.......H.......HG
..H.......H.......HG
..H.......H.......HG
..H.......H.......HG
..H....1..H.......HG
################H###
################H###
''', pal_with([(1, 1, 3), (3, 3, 6), (9, 10, 12), (12, 12, 13), (5, 6, 8), (6, 4, 8), (2, 2, 5), (4, 7, 11), (14, 13, 6)]),
     grad([(0, (0, 0, 1)), (10, (1, 1, 4)), (18, (3, 2, 7)), (22, (8, 3, 8)), (24, (12, 5, 6))]),
     art_bttower, dict(top=10, body=11, shade=12, gtop=10, gbody=11, girder=True), dict(S=3, E=7), gate_req=32)


# 7 THE GAFFER'S PENTHOUSE ----------------------------------------------------
def art_penthouse(sc, m):
    sc.stars(120, 80, 31)
    sc.ellipse(40, 26, 64, 50, 4)
    sc.ellipse(46, 28, 66, 48, 0)
    skyline(sc, 184, 7, 71, 40, 110, 20, 40, 15, 0.4)
    skyline(sc, 184, 8, 72, 20, 60, 30, 50, 4, 0.2)
    # rooftop helipad + neon sign
    sc.rect(0, 150, W, 184, 9)
    sc.ellipse(110, 156, 210, 182, 10)
    sc.rect(150, 162, 154, 176, 2)
    sc.rect(166, 162, 170, 176, 2)
    sc.rect(150, 168, 170, 170, 2)
    sc.rect(60, 70, 260, 96, 1)
    sc.rect(62, 72, 258, 94, 11)
    sc.rect(70, 78, 250, 88, 12)
    for x in range(74, 246, 10):
        sc.rect(x, 80, x + 6, 86, 13)


room("GAFFER'S PENTHOUSE", '''
....................
....................
....................
....................
....................
....................
....................
....................
....................
....................
....................
....................
....................
....................
......1.............
...H====....====H...
...H............H...
...H............H...
...H............H...
...H............H...
...H............H...
...H............H...
...H...........BH...
####################
####################
''', pal_with([(1, 1, 3), (2, 2, 6), (6, 6, 8), (3, 3, 4), (8, 1, 6), (15, 3, 11), (4, 13, 14), (15, 13, 8), (6, 6, 7)]),
     grad([(0, (0, 0, 1)), (12, (2, 0, 4)), (20, (6, 1, 6)), (24, (10, 3, 6))]),
     art_penthouse, dict(top=9, body=15, shade=10, gtop=15, gbody=9, rivets=True), dict(W=6))
