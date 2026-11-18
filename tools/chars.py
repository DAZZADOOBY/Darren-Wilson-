"""Procedural character sprite generator (original characters).

Each frame is 32x32 square pixels (CPC Plus hardware sprites at X-mag 2),
split into 4 hardware sprites (TL, TR, BL, BR) of 16x16.
"""
import math
from PIL import Image, ImageDraw

# Shared hardware sprite palette (index 1..15), 12-bit RGB (0..15 per channel)
SPRITE_PAL = [
    None,
    (0, 0, 1),     # 1 outline
    (15, 11, 8),   # 2 skin
    (11, 7, 5),    # 3 skin shadow
    (15, 15, 15),  # 4 white
    (10, 10, 11),  # 5 light grey
    (5, 5, 6),     # 6 dark grey
    (14, 2, 2),    # 7 red
    (8, 1, 3),     # 8 claret
    (3, 6, 14),    # 9 blue
    (1, 2, 7),     # 10 dark blue
    (15, 12, 2),   # 11 gold
    (8, 5, 2),     # 12 brown
    (3, 2, 1),     # 13 hair
    (6, 11, 15),   # 14 sky blue
    (15, 7, 1),    # 15 orange
]

S = 4  # supersampling

STYLES = {
    'hero': dict(skin=2, skin_back=3, torso=4, torso_back=5, arm=2, arm_back=3,
                 leg=10, leg_back=10, shoe=4, head='hero', torso_w=6, leg_w=3.4, arm_w=2.6, scale=1.0),
    'hoodie': dict(skin=3, skin_back=3, torso=5, torso_back=6, arm=5, arm_back=6,
                   leg=6, leg_back=6, shoe=4, head='hood', torso_w=6, leg_w=3, arm_w=2.6, scale=1.0, bat=True),
    'bouncer': dict(skin=3, skin_back=3, torso=13, torso_back=1, arm=13, arm_back=6,
                    leg=6, leg_back=13, shoe=1, head='bald', torso_w=8.5, leg_w=4, arm_w=3.4, scale=1.0),
    'boss': dict(skin=2, skin_back=3, torso=8, torso_back=8, arm=8, arm_back=8,
                 leg=10, leg_back=10, shoe=12, head='cap', torso_w=7, leg_w=3.4, arm_w=3, scale=1.0, chain=True),
}

# Bone lengths (pixels)
HEAD_R = 3.6
TORSO = 9.0
UARM, LARM = 5.5, 5.5
THIGH, SHIN = 7.0, 7.5


def rot(angle_deg, length):
    """angle 0 = straight down, positive swings forward (towards +x)."""
    a = math.radians(angle_deg)
    return (math.sin(a) * length, math.cos(a) * length)


def render(style_name, pose):
    st = STYLES[style_name]
    img = Image.new('P', (32 * S, 32 * S), 0)
    d = ImageDraw.Draw(img)
    hip = pose.get('hip', (15.5, 17.0))
    root = pose.get('root', 0)  # whole-body rotation (for lying down)
    hx, hy = hip

    def P(pt):
        return (pt[0] * S, pt[1] * S)

    def chain(start, angs, lens):
        pts = [start]
        acc = root
        x, y = start
        for a, l in zip(angs, lens):
            acc += a
            dx, dy = rot(acc, l)
            x, y = x + dx, y + dy
            pts.append((x, y))
        return pts

    def limb(pts, col, w):
        for a, b in zip(pts, pts[1:]):
            d.line([P(a), P(b)], fill=col, width=int(w * S))
            r = w * S / 2
            d.ellipse([b[0] * S - r, b[1] * S - r, b[0] * S + r, b[1] * S + r], fill=col)
        r = w * S / 2
        a = pts[0]
        d.ellipse([a[0] * S - r, a[1] * S - r, a[0] * S + r, a[1] * S + r], fill=col)

    # torso goes up from hip: angle 180 = up
    lean = pose.get('lean', 0)
    sh = chain(hip, [180 - lean], [TORSO])[1]
    neck = chain(sh, [180 - lean], [1.2])[1]
    head_c = chain(neck, [180 - lean], [HEAD_R])[1]

    bl = chain(hip, pose['bleg'], [THIGH, SHIN])
    fl = chain(hip, pose['fleg'], [THIGH, SHIN])
    ba = chain(sh, pose['barm'], [UARM, LARM])
    fa = chain(sh, pose['farm'], [UARM, LARM])

    def foot(pts, col):
        x, y = pts[-1]
        fwd = 1 if pose.get('facing', 1) > 0 else -1
        a = math.radians(root)
        # small shoe extending forward
        ex, ey = x + math.cos(a) * 2.2, y - math.sin(a) * 2.2
        d.line([P((x, y)), P((ex, ey))], fill=col, width=int(2.2 * S))

    # back arm & leg
    limb(ba, st['arm_back'], st['arm_w'] * 0.9)
    limb(bl, st['leg_back'], st['leg_w'])
    foot(bl, st['shoe'])
    # torso
    limb([hip, sh], st['torso'], st['torso_w'])
    if st.get('chain'):
        mid = ((hip[0] + sh[0]) / 2 + 0.5, (hip[1] + sh[1]) / 2 - 1)
        d.ellipse([P((mid[0] - 1, mid[1] - 1)), P((mid[0] + 1, mid[1] + 1))], fill=11)
    # front leg
    limb(fl, st['leg'], st['leg_w'])
    foot(fl, st['shoe'])
    if style_name == 'hero':
        # white side stripe on trousers
        limb(fl, st['leg'], st['leg_w'])
        d.line([P(fl[0]), P(fl[1])], fill=9, width=int(0.9 * S))
    # head
    cx, cy = head_c
    r = HEAD_R * S
    kind = st['head']
    if kind == 'hood':
        d.ellipse([cx * S - r - 0.6 * S, cy * S - r - 0.6 * S, cx * S + r + 0.6 * S, cy * S + r + 0.4 * S], fill=5)
        d.ellipse([cx * S - r * 0.2, cy * S - r * 0.55, cx * S + r * 0.9, cy * S + r * 0.7], fill=6)
        d.rectangle([cx * S + r * 0.25, cy * S - r * 0.1, cx * S + r * 0.55, cy * S + r * 0.1], fill=4)
    else:
        d.ellipse([cx * S - r, cy * S - r, cx * S + r, cy * S + r], fill=st['skin'])
        # eye
        d.rectangle([cx * S + r * 0.35, cy * S - r * 0.25, cx * S + r * 0.75, cy * S + r * 0.05], fill=1)
        if kind == 'hero':
            # spiky black hair
            d.pieslice([cx * S - r, cy * S - r - 0.8 * S, cx * S + r, cy * S + r * 0.6], 180, 360, fill=13)
            d.polygon([P((cx - 3.8, cy - 1.0)), P((cx - 1.0, cy - 2.5)), P((cx - 4.5, cy - 3.6))], fill=13)
            # red headband with flowing tails
            d.rectangle([cx * S - r, cy * S - r * 0.55, cx * S + r, cy * S - r * 0.2], fill=7)
            d.line([P((cx - 3.2, cy - 1.4)), P((cx - 6.0, cy - 0.2))], fill=7, width=int(1.2 * S))
            d.line([P((cx - 3.2, cy - 1.0)), P((cx - 5.5, cy + 1.4))], fill=7, width=int(1.0 * S))
        elif kind == 'bald':
            d.rectangle([cx * S - r * 0.1, cy * S - r * 0.35, cx * S + r * 0.95, cy * S + r * 0.1], fill=1)  # shades
        elif kind == 'cap':
            d.pieslice([cx * S - r - 0.3 * S, cy * S - r - 0.6 * S, cx * S + r + 0.3 * S, cy * S + r * 0.5], 180, 360, fill=12)
            d.rectangle([cx * S, cy * S - r * 0.45, cx * S + r * 1.5, cy * S - r * 0.15], fill=12)
            d.rectangle([cx * S - r * 0.3, cy * S + r * 0.5, cx * S + r * 0.6, cy * S + r * 0.9], fill=13)  # moustache
    # front arm (+ bat)
    limb(fa, st['arm'], st['arm_w'])
    hx2, hy2 = fa[-1]
    d.ellipse([P((hx2 - 1.3, hy2 - 1.3)), P((hx2 + 1.3, hy2 + 1.3))], fill=st['skin'])
    if st.get('bat') and 'bat' in pose:
        acc = root + sum(pose['farm']) + pose['bat']
        bx, by = rot(acc, 9)
        d.line([P((hx2, hy2)), P((hx2 + bx, hy2 + by))], fill=12, width=int(1.8 * S))
        bx2, by2 = rot(acc, 5)
        d.line([P((hx2 + bx2, hy2 + by2)), P((hx2 + bx, hy2 + by))], fill=11, width=int(2.4 * S))

    # downsample
    px = img.load()
    out = [[0] * 32 for _ in range(32)]
    for y in range(32):
        for x in range(32):
            out[y][x] = px[x * S + S // 2, y * S + S // 2]
    # outline
    res = [row[:] for row in out]
    for y in range(32):
        for x in range(32):
            if out[y][x] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < 32 and 0 <= ny < 32 and out[ny][nx] not in (0, 1):
                        res[y][x] = 1
                        break
    return res


# ---- Poses (facing right) ----
STAND = dict(bleg=[-8, 4], fleg=[10, -4], barm=[-15, 40], farm=[20, 60])
WALK = [
    dict(bleg=[-30, 22], fleg=[28, -4], barm=[28, 30], farm=[-28, 40]),
    dict(bleg=[-8, 40], fleg=[6, 0], barm=[8, 30], farm=[-8, 40]),
    dict(bleg=[28, -4], fleg=[-30, 22], barm=[-28, 40], farm=[28, 30]),
    dict(bleg=[6, 0], fleg=[-8, 40], barm=[-8, 40], farm=[8, 30]),
]
PUNCH = dict(bleg=[-18, 6], fleg=[18, -6], barm=[-30, 100], farm=[88, 4], lean=-8)
KICK = dict(hip=(13.5, 17.5), bleg=[-12, 8], fleg=[92, -4], barm=[-40, 70], farm=[150, 60], lean=-22)
JUMP = dict(hip=(15.5, 14.5), bleg=[40, -95], fleg=[70, -100], barm=[-30, 120], farm=[140, 40])
FLYKICK = dict(hip=(13.0, 15.0), bleg=[40, -110], fleg=[100, -6], barm=[-50, 80], farm=[160, 40], lean=-28)
CLIMB = [
    dict(bleg=[-35, 70], fleg=[0, 0], barm=[-140, -20], farm=[120, 30], facing=0),
    dict(bleg=[0, 0], fleg=[35, -70], barm=[-120, -30], farm=[140, 20], facing=0),
]
DOWN = dict(hip=(14.0, 29.0), root=-90, bleg=[-6, 6], fleg=[8, 4], barm=[-30, 30], farm=[30, 40])
# enemy attacks
WINDUP = dict(bleg=[-14, 6], fleg=[14, -4], barm=[-30, 40], farm=[-150, 30], bat=20, lean=8)
SWING = dict(bleg=[-18, 6], fleg=[18, -6], barm=[-30, 60], farm=[80, 10], bat=0, lean=-10)
HEAVY_WIND = dict(bleg=[-14, 6], fleg=[14, -4], barm=[-30, 40], farm=[-60, 120], lean=6)
HEAVY_HIT = dict(bleg=[-20, 6], fleg=[20, -6], barm=[-30, 90], farm=[85, 5], lean=-12)

FRAME_LIST = []  # (name, style, pose)


def _add(name, style, pose):
    FRAME_LIST.append((name, style, pose))


for st in ('hero',):
    _add('hero_stand', st, STAND)
    for i, w in enumerate(WALK):
        _add('hero_walk%d' % i, st, w)
    _add('hero_punch', st, PUNCH)
    _add('hero_kick', st, KICK)
    _add('hero_jump', st, JUMP)
    _add('hero_flykick', st, FLYKICK)
    _add('hero_climb0', st, CLIMB[0])
    _add('hero_climb1', st, CLIMB[1])
    _add('hero_down', st, DOWN)

for st in ('hoodie', 'bouncer', 'boss'):
    stand = dict(STAND)
    if st == 'hoodie':
        stand = dict(STAND, farm=[20, 60], bat=-60)
    _add(st + '_stand', st, stand)
    w0 = dict(WALK[0]); w2 = dict(WALK[2])
    if st == 'hoodie':
        w0['bat'] = -60; w2['bat'] = -60
    _add(st + '_walk0', st, w0)
    _add(st + '_walk1', st, w2)
    if st == 'hoodie':
        _add(st + '_windup', st, WINDUP)
        _add(st + '_attack', st, SWING)
    else:
        _add(st + '_windup', st, HEAVY_WIND)
        _add(st + '_attack', st, HEAVY_HIT)
    _add(st + '_down', st, DOWN)

FRAME_INDEX = {n: i for i, (n, _, _) in enumerate(FRAME_LIST)}


def all_frames():
    return [render(st, pose) for (_, st, pose) in FRAME_LIST]


def pack_frame(px):
    """-> 512 bytes: 4 sprites (TL,TR,BL,BR), each 16 rows x 8 bytes, hi nibble = left pixel."""
    out = bytearray()
    for sy, sx in ((0, 0), (0, 16), (16, 0), (16, 16)):
        for y in range(16):
            for x in range(0, 16, 2):
                out.append((px[sy + y][sx + x] << 4) | px[sy + y][sx + x + 1])
    return bytes(out)


def spark_sprite():
    px = [[0] * 16 for _ in range(16)]
    import random
    rnd = random.Random(3)
    for i in range(12):
        a = i * math.pi / 6
        l = 7 if i % 2 == 0 else 4.5
        for t in range(int(l * 2)):
            r = t / 2
            x = int(round(7.5 + math.cos(a) * r))
            y = int(round(7.5 + math.sin(a) * r))
            if 0 <= x < 16 and 0 <= y < 16:
                px[y][x] = 4 if r < 2 else (11 if r < 4 else 15)
    return px


def preview(path, scale=6):
    frames = all_frames()
    n = len(frames)
    cols = 12
    rows = (n + cols - 1) // cols
    img = Image.new('RGB', (cols * 34 * scale, rows * 34 * scale), (60, 90, 120))
    p = img.load()
    for i, f in enumerate(frames):
        ox, oy = (i % cols) * 34 * scale, (i // cols) * 34 * scale
        for y in range(32):
            for x in range(32):
                c = f[y][x]
                if c:
                    r, g, b = SPRITE_PAL[c]
                    for yy in range(scale):
                        for xx in range(scale):
                            p[ox + x * scale + xx, oy + y * scale + yy] = (r * 17, g * 17, b * 17)
    img.save(path)


if __name__ == '__main__':
    preview('/tmp/chars.png')
    print(len(FRAME_LIST), 'frames')
