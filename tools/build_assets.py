"""Generate all game assets for Dragon of Digbeth (CPC Plus).

Outputs into build/: room bitmaps (CPC screen layout), sprite frames, data.asm, bitmaps.asm, previews.
"""
import os, sys, subprocess, collections
sys.path.insert(0, os.path.dirname(__file__))
import chars, rooms
from rooms import ROOMS, Scene, draw_structures, hud_panel, grad, pal_with, skyline, rotunda, pagoda, spire, bt_tower
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'build')
os.makedirs(OUT, exist_ok=True)
RASM = os.environ.get('RASM', 'rasm')

CT = {'.': 0, 'L': 0, '1': 0, '2': 0, 'B': 0, '#': 1, '=': 2, 'H': 3, 'G': 4, 'W': 5}


def m0(p0, p1):
    b = 0
    for bit, (pix, shift) in ((7, (p0, 0)), (6, (p1, 0)), (5, (p0, 2)), (4, (p1, 2)),
                              (3, (p0, 1)), (2, (p1, 1)), (1, (p0, 3)), (0, (p1, 3))):
        if (pix >> shift) & 1:
            b |= 1 << bit
    return b


def to_screen(px):
    scr = bytearray(16384)
    for y in range(200):
        base = (y // 8) * 80 + (y % 8) * 2048
        for xb in range(80):
            scr[base + xb] = m0(px[y][xb * 2], px[y][xb * 2 + 1])
    return bytes(scr)


def rgb12(c):
    r, g, b = c
    return (r << 4 | b) | (g << 8)


# ---------------------------------------------------------------- font (original 5x7)
FONT = {
    ' ': ['     '] * 7,
    'A': [' ### ', '#   #', '#   #', '#####', '#   #', '#   #', '#   #'],
    'B': ['#### ', '#   #', '#   #', '#### ', '#   #', '#   #', '#### '],
    'C': [' ####', '#    ', '#    ', '#    ', '#    ', '#    ', ' ####'],
    'D': ['#### ', '#   #', '#   #', '#   #', '#   #', '#   #', '#### '],
    'E': ['#####', '#    ', '#    ', '#### ', '#    ', '#    ', '#####'],
    'F': ['#####', '#    ', '#    ', '#### ', '#    ', '#    ', '#    '],
    'G': [' ####', '#    ', '#    ', '#  ##', '#   #', '#   #', ' ####'],
    'H': ['#   #', '#   #', '#   #', '#####', '#   #', '#   #', '#   #'],
    'I': ['#####', '  #  ', '  #  ', '  #  ', '  #  ', '  #  ', '#####'],
    'J': ['  ###', '    #', '    #', '    #', '    #', '#   #', ' ### '],
    'K': ['#   #', '#  # ', '# #  ', '##   ', '# #  ', '#  # ', '#   #'],
    'L': ['#    ', '#    ', '#    ', '#    ', '#    ', '#    ', '#####'],
    'M': ['#   #', '## ##', '# # #', '# # #', '#   #', '#   #', '#   #'],
    'N': ['#   #', '##  #', '# # #', '#  ##', '#   #', '#   #', '#   #'],
    'O': [' ### ', '#   #', '#   #', '#   #', '#   #', '#   #', ' ### '],
    'P': ['#### ', '#   #', '#   #', '#### ', '#    ', '#    ', '#    '],
    'Q': [' ### ', '#   #', '#   #', '#   #', '# # #', '#  # ', ' ## #'],
    'R': ['#### ', '#   #', '#   #', '#### ', '# #  ', '#  # ', '#   #'],
    'S': [' ####', '#    ', '#    ', ' ### ', '    #', '    #', '#### '],
    'T': ['#####', '  #  ', '  #  ', '  #  ', '  #  ', '  #  ', '  #  '],
    'U': ['#   #', '#   #', '#   #', '#   #', '#   #', '#   #', ' ### '],
    'V': ['#   #', '#   #', '#   #', '#   #', '#   #', ' # # ', '  #  '],
    'W': ['#   #', '#   #', '#   #', '# # #', '# # #', '## ##', '#   #'],
    'X': ['#   #', '#   #', ' # # ', '  #  ', ' # # ', '#   #', '#   #'],
    'Y': ['#   #', '#   #', ' # # ', '  #  ', '  #  ', '  #  ', '  #  '],
    'Z': ['#####', '    #', '   # ', '  #  ', ' #   ', '#    ', '#####'],
    '0': [' ### ', '#   #', '#  ##', '# # #', '##  #', '#   #', ' ### '],
    '1': ['  #  ', ' ##  ', '  #  ', '  #  ', '  #  ', '  #  ', ' ### '],
    '2': [' ### ', '#   #', '    #', '   # ', '  #  ', ' #   ', '#####'],
    '3': ['#### ', '    #', '    #', ' ### ', '    #', '    #', '#### '],
    '4': ['   # ', '  ## ', ' # # ', '#  # ', '#####', '   # ', '   # '],
    '5': ['#####', '#    ', '#### ', '    #', '    #', '#   #', ' ### '],
    '6': [' ### ', '#    ', '#    ', '#### ', '#   #', '#   #', ' ### '],
    '7': ['#####', '    #', '   # ', '  #  ', ' #   ', ' #   ', ' #   '],
    '8': [' ### ', '#   #', '#   #', ' ### ', '#   #', '#   #', ' ### '],
    '9': [' ### ', '#   #', '#   #', ' ####', '    #', '    #', ' ### '],
    '.': ['     ', '     ', '     ', '     ', '     ', ' ##  ', ' ##  '],
    ',': ['     ', '     ', '     ', '     ', ' ##  ', '  #  ', ' #   '],
    '!': ['  #  ', '  #  ', '  #  ', '  #  ', '  #  ', '     ', '  #  '],
    '?': [' ### ', '#   #', '    #', '   # ', '  #  ', '     ', '  #  '],
    '-': ['     ', '     ', '     ', ' ### ', '     ', '     ', '     '],
    '/': ['    #', '    #', '   # ', '  #  ', ' #   ', '#    ', '#    '],
    ':': ['     ', ' ##  ', ' ##  ', '     ', ' ##  ', ' ##  ', '     '],
    "'": ['  #  ', '  #  ', ' #   ', '     ', '     ', '     ', '     '],
    '(': ['   # ', '  #  ', ' #   ', ' #   ', ' #   ', '  #  ', '   # '],
    ')': [' #   ', '  #  ', '   # ', '   # ', '   # ', '  #  ', ' #   '],
    '*': ['     ', ' # # ', '  #  ', '#####', '  #  ', ' # # ', '     '],
}
FONT_FIRST, FONT_LAST = 32, 90


def font_bytes():
    out = bytearray()
    for code in range(FONT_FIRST, FONT_LAST + 1):
        g = FONT.get(chr(code), FONT[' '])
        rows = [0]  # top padding row
        for r in g:
            v = 0
            for i, ch in enumerate(r):
                if ch == '#':
                    v |= 0x40 >> i   # 1px left pad, 5px glyph, 2px right pad
            rows.append(v)
        out += bytes(rows)
    return out


# ---------------------------------------------------------------- overlay graphics
LANTERN = [
    '..6666..',
    '...55...',
    '.333333.',
    '33344333',
    '33444433',
    '34444443',
    '34444443',
    '34444443',
    '34444443',
    '33444433',
    '33344333',
    '.333333.',
    '...55...',
    '..6666..',
    '...44...',
    '....4...',
]


def lantern_bytes():
    out = bytearray()
    for row in LANTERN:
        for xb in range(4):
            a, b = row[xb * 2], row[xb * 2 + 1]
            mask = (0xAA if a == '.' else 0) | (0x55 if b == '.' else 0)
            data = m0(0 if a == '.' else int(a), 0 if b == '.' else int(b))
            out += bytes([mask, data])
    return out


HATCH = ['55555555', '66666666', '55655565', '55655565', '66666666', '55555555', '56555655', '11111111']
DOOR = ['56665666', '55555555', '66666666', '55555555', '56565656', '55555555', '66666666', '11111111']


def tile_bytes(t):
    out = bytearray()
    for row in t:
        for xb in range(4):
            out.append(m0(int(row[xb * 2]), int(row[xb * 2 + 1])))
    return out


# ---------------------------------------------------------------- map validation
SOLIDF = set('#=G')


def validate(ri, rm):
    m = rm['map']
    def cell(c, r):
        if r < 0 or r > 24 or c < 0 or c > 19:
            return '.'
        return m[r][c]
    def passable(c, r):
        return cell(c, r) not in '#G'
    def standable(c, r):
        if not passable(c, r):
            return False
        below = cell(c, r + 1)
        return below in SOLIDF or (below == 'H' and cell(c, r) != 'H')
    # start: any standable cell on row 22 (or any)
    start = [(c, 22) for c in range(20) if standable(c, 22)]
    if not start:
        start = [(c, r) for r in range(25) for c in range(20) if cell(c, r) == 'H'][:1]
    seen = set(start)
    q = collections.deque(start)
    while q:
        c, r = q.popleft()
        nxt = []
        if cell(c, r) == 'H' or cell(c, r + 1) == 'H':
            for dr in (-1, 1):
                if cell(c, r + dr) == 'H' or (dr == -1 and cell(c, r) == 'H'):
                    nxt.append((c, r + dr))
            for dc in (-1, 1):
                if standable(c + dc, r):
                    nxt.append((c + dc, r))
        if standable(c, r) or cell(c, r) == 'H':
            for dc in (-1, 1):
                if passable(c + dc, r):
                    nxt.append((c + dc, r))
            for up in range(1, 5):
                for dc in range(-2, 3):
                    if standable(c + dc, r - up) and cell(c + dc, r - up + 1) == '=':
                        nxt.append((c + dc, r - up))
        else:
            rr = r
            while rr < 24 and not standable(c, rr) and cell(c, rr) != 'W':
                rr += 1
            if cell(c, rr) != 'W':
                nxt.append((c, rr))
        for n in nxt:
            if 0 <= n[0] < 20 and 0 <= n[1] < 25 and n not in seen and cell(*n) != 'W':
                seen.add(n)
                q.append(n)
    ok = True
    for r in range(25):
        for c in range(20):
            if m[r][c] == 'L':
                reach = any((cc, rr) in seen for cc in range(c - 1, c + 2) for rr in range(r, r + 8))
                if not reach:
                    print('WARNING room %d lantern (%d,%d) unreachable' % (ri, c, r))
                    ok = False
    return ok


# ---------------------------------------------------------------- scenes
def render_room(rm):
    sc = Scene(rm['pal'])
    rm['art'](sc, rm['map'])
    draw_structures(sc, rm['map'], rm['style'])
    hud_panel(sc)
    return sc.to_mode0()


def title_screen():
    pal = pal_with([(2, 1, 5), (6, 2, 8), (14, 3, 2), (15, 8, 1), (15, 13, 3), (5, 3, 9), (3, 2, 6), (15, 15, 9), (9, 5, 12)])
    gr = grad([(0, (0, 0, 2)), (6, (3, 1, 7)), (13, (10, 2, 7)), (18, (15, 6, 3)), (24, (15, 12, 5))])
    sc = Scene(pal)
    sc.ellipse(120, 90, 200, 170, 11)
    sc.dither(120, 130, 200, 170, 11, 10, 2)
    skyline(sc, 200, 7, 99, 20, 60, 16, 40, 11, 0.2)
    rotunda(sc, 70, 200, 110, 13, 8, 11)
    pagoda(sc, 250, 200, 9, 13, 10)
    spire(sc, 170, 200, 70, 13, 8)
    bt_tower(sc, 120, 200, 120, 13, 8, 7)
    px = sc.img.load()

    def big(text, y, sx, sy, pens):
        w = len(text) * 6 * sx
        x0 = (320 - w) // 2
        for i, ch in enumerate(text):
            g = FONT.get(ch, FONT[' '])
            for r, row in enumerate(g):
                for c, v in enumerate(row):
                    if v == '#':
                        for yy in range(sy):
                            pen = pens[min(len(pens) - 1, (r * sy + yy) * len(pens) // (7 * sy))]
                            for xx in range(sx):
                                X, Y = x0 + (i * 6 + c) * sx + xx, y + r * sy + yy
                                px[X, Y] = pen
                                # shadow
                                if X + 4 < 320 and Y + 2 < 200 and px[X + 4, Y + 2] not in pens:
                                    px[X + 4, Y + 2] = 1
    big('DRAGON', 24, 8, 5, [12, 12, 11, 10, 9, 9])
    big('OF DIGBETH', 66, 5, 4, [14, 14, 2, 2, 15])
    return to_screen(sc.to_mode0()), pal, gr, sc.to_mode0()


def preview_png(px, pal, gr, path):
    img = Image.new('RGB', (320, 200))
    p = img.load()
    for y in range(200):
        for x in range(160):
            pen = px[y][x]
            c = gr[y // 8] if pen == 0 else pal[pen]
            col = (c[0] * 17, c[1] * 17, c[2] * 17)
            p[x * 2, y] = col
            p[x * 2 + 1, y] = col
    img = img.resize((640, 400), Image.NEAREST)
    img.save(path)


# ---------------------------------------------------------------- main
def zx0_size(binpath):
    asm = binpath + '.z.asm'
    out = binpath + '.zx0'
    with open(asm, 'w') as f:
        f.write("org 0\ninczx0 '%s'\n" % os.path.basename(binpath))
    subprocess.run([RASM, os.path.basename(asm), '-ob', os.path.basename(out)], cwd=OUT, check=True,
                   stdout=subprocess.DEVNULL)
    return os.path.getsize(out)


def main():
    ok = True
    data = []  # lines of asm for bank 1
    bitmaps = []  # (label, file)
    lantern_id = 0
    ens = {'1': 1, '2': 2, 'B': 3}
    room_lines = []
    for ri, rm in enumerate(ROOMS):
        ok &= validate(ri, rm)
        px = render_room(rm)
        scr = to_screen(px)
        fn = 'room%d.scr' % ri
        open(os.path.join(OUT, fn), 'wb').write(scr)
        preview_png(px, rm['pal'], rm['grad'], os.path.join(OUT, 'room%d.png' % ri))
        bitmaps.append(('bmp_room%d' % ri, fn))
        m = rm['map']
        lants = [(c, r) for r in range(25) for c in range(20) if m[r][c] == 'L']
        enem = [(ens[m[r][c]], c, r) for r in range(25) for c in range(20) if m[r][c] in ens]
        gcells = [(c, r) for r in range(25) for c in range(20) if m[r][c] == 'G']
        nb = rm['nb']
        L = 'room%d' % ri
        room_lines.append('%s:' % L)
        room_lines.append(' db bmp_page_%d : dw bmp_room%d' % (ri, ri))
        room_lines.append(' db %s' % ','.join(str(nb.get(k, 255)) for k in 'NSEW'))
        room_lines.append(' dw %s_name' % L)
        if gcells:
            gx = min(c for c, _ in gcells); gy = min(r for _, r in gcells)
            gw = max(c for c, _ in gcells) - gx + 1; gh = max(r for _, r in gcells) - gy + 1
            kind = 0 if gh == 1 else 1
            room_lines.append(' db %d,%d,%d,%d,%d,%d' % (rm['gate_req'], gx, gy, gw, gh, kind))
        else:
            room_lines.append(' db 0,0,0,0,0,0')
        room_lines.append(' db %d,%d' % (len(lants), lantern_id))
        lantern_id += len(lants)
        room_lines.append(' dw %s_lant,%s_enem,%s_map,%s_pal,%s_grad,%s_gopen' % ((L,) * 6))
        room_lines.append('%s_name: db "%s",0' % (L, rm['name']))
        room_lines.append('%s_lant: db %s' % (L, ','.join('%d,%d' % lc for lc in lants) or '0'))
        room_lines.append('%s_enem: db %s255' % (L, ''.join('%d,%d,%d,' % e for e in enem)))
        mb = bytes(CT[ch] for row in m for ch in row)
        room_lines.append('%s_map: db %s' % (L, ','.join(str(b) for b in mb)))
        pal = rm['pal']
        room_lines.append('%s_pal: dw %s' % (L, ','.join('#%03x' % rgb12(pal[i] if pal[i] else rm['grad'][0]) for i in range(16))))
        room_lines.append('%s_grad: dw %s' % (L, ','.join('#%03x' % rgb12(c) for c in rm['grad'])))
        gopen = []
        for (c, r) in gcells:
            if rooms.ladder_under_gate(m, c, r):
                gopen.append(3)
            elif len(set(rr for _, rr in gcells)) == 1:
                gopen.append(2)
            else:
                gopen.append(0)
        room_lines.append('%s_gopen: db %s' % (L, ','.join(str(v) for v in gopen) or '0'))
    total_lanterns = lantern_id
    # title
    tscr, tpal, tgr, tpx = title_screen()
    open(os.path.join(OUT, 'title.scr'), 'wb').write(tscr)
    preview_png(tpx, tpal, tgr, os.path.join(OUT, 'title.png'))
    bitmaps.append(('bmp_title', 'title.scr'))

    # sprites
    frames = chars.all_frames()
    fb = b''.join(chars.pack_frame(f) for f in frames)
    open(os.path.join(OUT, 'frames.bin'), 'wb').write(fb)
    chars.preview(os.path.join(OUT, 'chars.png'))
    spark = chars.spark_sprite()
    sb = bytes(spark[y][x] for y in range(16) for x in range(16))

    # pack bitmaps into banks 3..7
    sizes = [(lab, fn, zx0_size(os.path.join(OUT, fn))) for lab, fn in bitmaps]
    banks = []
    cur, used = [], 0
    for lab, fn, sz in sizes:
        if used + sz > 16384:
            banks.append(cur); cur, used = [], 0
        cur.append((lab, fn, sz)); used += sz
    banks.append(cur)
    assert len(banks) <= 5, 'too many bitmap banks'
    bl = []
    for bi, bk in enumerate(banks):
        bl.append('bank %d' % (3 + bi))
        bl.append('org #4000')
        for lab, fn, sz in bk:
            bl.append('%s: incbin "%s"' % (lab, fn + '.zx0'))
            idx = lab.replace('bmp_room', '').replace('bmp_', '')
            bl.append('bmp_page_%s equ %d' % (idx, 3 + bi))
    open(os.path.join(OUT, 'bitmaps.asm'), 'w').write('\n'.join(bl) + '\n')
    for lab, fn, sz in sizes:
        print('%-12s %6d bytes' % (lab, sz))

    d = []
    d.append('NUM_ROOMS equ %d' % len(ROOMS))
    d.append('TOTAL_LANTERNS equ %d' % total_lanterns)
    d.append('FONT_FIRST equ %d' % FONT_FIRST)
    for n, i in chars.FRAME_INDEX.items():
        d.append('FR_%s equ %d' % (n.upper(), i))
    d.append('room_table: dw %s' % ','.join('room%d' % i for i in range(len(ROOMS))))
    d += room_lines
    d.append('font_data: db %s' % ','.join(str(b) for b in font_bytes()))
    d.append('lantern_gfx: db %s' % ','.join(str(b) for b in lantern_bytes()))
    d.append('hatch_gfx: db %s' % ','.join(str(b) for b in tile_bytes(HATCH)))
    d.append('door_gfx: db %s' % ','.join(str(b) for b in tile_bytes(DOOR)))
    d.append('spark_gfx: db %s' % ','.join(str(b) for b in sb))
    d.append('sprite_pal: dw %s' % ','.join('#%03x' % rgb12(c) for c in chars.SPRITE_PAL[1:]))
    d.append('title_pal: dw %s' % ','.join('#%03x' % rgb12(tpal[i] if tpal[i] else tgr[0]) for i in range(16)))
    d.append('title_grad: dw %s' % ','.join('#%03x' % rgb12(c) for c in tgr))
    # wrap long db lines
    lines = []
    for ln in d:
        if len(ln) > 400 and (' db ' in ln or ' dw ' in ln):
            head, _, vals = ln.partition(' db ') if ' db ' in ln else ln.partition(' dw ')
            kw = 'db' if ' db ' in ln else 'dw'
            items = vals.split(',')
            lines.append(head)
            for i in range(0, len(items), 32):
                lines.append(' %s %s' % (kw, ','.join(items[i:i + 32])))
        else:
            lines.append(ln)
    open(os.path.join(OUT, 'data.asm'), 'w').write('\n'.join(lines) + '\n')
    print('lanterns:', total_lanterns, 'frames:', len(frames), 'maps ok' if ok else 'MAP WARNINGS')


if __name__ == '__main__':
    main()
