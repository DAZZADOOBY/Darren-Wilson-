; =============================================================================
;  DRAGON OF DIGBETH - Amstrad CPC Plus / GX4000 cartridge
;  Bank 0: code (copied to RAM #0000), bank 1: room data, bank 2: sprite
;  frames, banks 3+: ZX0-compressed screens.
; =============================================================================

; ---------------------------------------------------------------- RAM map
sh_mode     equ #8000
sh_rmr2     equ #8001
frames      equ #8002
band        equ #8003
keys        equ #8005
room        equ #8007
next_room   equ #8008
lives       equ #8009
score       equ #800A       ; 3 bytes BCD, big endian
lcount      equ #800D
lgot        equ #800E       ; 4 bytes bitfield
gate_closed equ #8012
hud_dirty   equ #8013
game_state  equ #8014
sfx_ptr     equ #8015
spark_t     equ #8017
spark_x     equ #8018
spark_y     equ #8019
entry_x     equ #801A
entry_y     equ #801B
entry_st    equ #801C
kbuf        equ #8020       ; 10 bytes
tick        equ #802A
inp         equ #802E
inp_old     equ #802F
pal_on      equ #8030
gptr        equ #8031
gidx        equ #8033
hero        equ #8040
en0         equ #8060
en1         equ #8080
tc          equ #8100       ; text colour combos (must be 256-aligned)
line_tab    equ #8200
map_ram     equ #8400
lsave       equ #8600
gsave       equ #8800
sbuf        equ #8A00
grad_ram    equ #8C00
pal_ram     equ #8C40
grad_new    equ #8C80
lant_ram    equ #8D00
spawn_ram   equ #8D20
gopen_ram   equ #8D40
name_ram    equ #8D60
rrec        equ #8D80

; room record offsets
RR_PAGE equ 0
RR_BMP  equ 1
RR_N    equ 3
RR_S    equ 4
RR_E    equ 5
RR_W    equ 6
RR_NAME equ 7
RR_GREQ equ 9
RR_GX   equ 10
RR_GY   equ 11
RR_GW   equ 12
RR_GH   equ 13
RR_GKIND equ 14
RR_NL   equ 15
RR_LB   equ 16
RR_LANT equ 17
RR_ENEM equ 19
RR_MAP  equ 21
RR_PAL  equ 23
RR_GRAD equ 25
RR_GOPEN equ 27

; character struct
C_X     equ 0
C_Y     equ 1
C_ST    equ 2
C_DIR   equ 3
C_TIMER equ 4
C_ANIM  equ 5
C_FRAME equ 6
C_SHOWN equ 7
C_SPR   equ 8
C_VY    equ 9
C_DX    equ 10
C_HP    equ 11
C_TYPE  equ 12
C_FLAGS equ 13
C_INV   equ 14
C_VIS   equ 15
C_SX    equ 16
C_SY    equ 17
C_COOL  equ 18

ST_STAND equ 0
ST_WALK  equ 1
ST_JUMP  equ 2
ST_CLIMB equ 3
ST_PUNCH equ 4
ST_KICK  equ 5
ST_DOWN  equ 6

E_INACTIVE equ 0
E_WALK   equ 1
E_CLIMB  equ 2
E_WINDUP equ 3
E_ATTACK equ 4
E_HURT   equ 5
E_KO     equ 6

T_SOLID  equ 1
T_PLAT   equ 2
T_LADDER equ 3
T_GATE   equ 4
T_WATER  equ 5

I_UP    equ 1
I_DOWN  equ 2
I_LEFT  equ 4
I_RIGHT equ 8
I_FIRE  equ 16

JUMP_APEX equ 10
JUMP_LEN  equ 23
TOP_Y     equ 48

    include "dzx0_standard.asm"
buildcpr
bank 0
org 0
    di
    jp start

; ---------------------------------------------------------------- interrupt
org #38
    push af
    push bc
    push de
    push hl
    ld bc,#7f8c : out (c),c : ld c,#b8 : out (c),c
    ld a,(band) : ld l,a : ld h,0 : add hl,hl : ld de,grad_ram : add hl,de
    ld a,(hl) : ld (#6400),a : inc hl : ld a,(hl) : ld (#6401),a
    ld a,(band) : inc a : cp 25 : jr c,.nb
    ld a,1 : ld (band),a : ld a,7 : ld (#6800),a
    call frame_irq
    jr .rest
.nb ld (band),a : add a,a : add a,a : add a,a : dec a : ld (#6800),a
.rest
    ld bc,(sh_mode)
    ld a,b : ld b,#7f : out (c),a : out (c),c
    pop hl
    pop de
    pop bc
    pop af
    ei
    ret

frame_irq:
    ld hl,frames : inc (hl)
    ld hl,tick : inc (hl)
    ld a,(pal_on) : or a : jr z,.ng
    ld a,(tick) : and #1c : rrca : ld e,a : ld d,0 : ld hl,glow_tab : add hl,de
    ld a,(hl) : ld (#6408),a : inc hl : ld a,(hl) : ld (#6409),a
.ng call read_keys
    jp sfx_tick

glow_tab: dw #bf2,#cf4,#df6,#cf4,#bf2,#9f1,#8e0,#9f1

read_keys:
    ld bc,#f40e : out (c),c
    ld bc,#f6c0 : out (c),c
    ld bc,#f600 : out (c),c
    ld bc,#f792 : out (c),c
    ld hl,kbuf : ld d,#40
.r  ld b,#f6 : out (c),d : ld b,#f4 : in a,(c) : ld (hl),a : inc hl
    inc d : ld a,d : cp #4a : jr nz,.r
    ld bc,#f782 : out (c),c
    ld bc,#f600 : out (c),c
    ld a,(kbuf+9) : cpl : and #1f : ld e,a
    ld hl,key_map
.k  ld a,(hl) : cp #ff : jr z,.kd : inc hl
    push hl : ld l,a : ld h,0 : ld bc,kbuf : add hl,bc : ld a,(hl) : pop hl
    cpl : and (hl) : inc hl : jr z,.kn
    ld a,e : or (hl) : ld e,a
.kn inc hl : jr .k
.kd ld a,e : ld (keys),a
    ret

key_map:
    db 0,#01,I_UP, 0,#04,I_DOWN, 1,#01,I_LEFT, 0,#02,I_RIGHT
    db 5,#80,I_FIRE, 1,#02,I_FIRE
    db 8,#08,I_UP, 8,#20,I_DOWN, 4,#04,I_LEFT, 3,#08,I_RIGHT
    db #ff

; ---------------------------------------------------------------- sound
psg_write:              ; A=reg, C=value
    push bc
    ld b,#f4 : out (c),a
    ld b,#f6 : ld a,#c0 : out (c),a : xor a : out (c),a
    pop bc : push bc
    ld b,#f4 : out (c),c
    ld b,#f6 : ld a,#80 : out (c),a : xor a : out (c),a
    pop bc
    ret

sfx_tick:
    ld hl,(sfx_ptr) : ld a,h : or l : ret z
    ld a,(hl) : cp #ff : jr nz,.go
    ld hl,0 : ld (sfx_ptr),hl
    ld a,10 : ld c,0 : jp psg_write
.go ld a,4 : ld c,(hl) : inc hl : call psg_write
    ld a,5 : ld c,(hl) : inc hl : call psg_write
    ld a,(hl) : inc hl : ld c,#3b : or a : jr z,.nn
    ld c,a : ld a,6 : call psg_write : ld c,#1b
.nn ld a,7 : call psg_write
    ld a,10 : ld c,(hl) : inc hl : call psg_write
    ld (sfx_ptr),hl
    ret

play_sfx:               ; HL=effect
    ld (sfx_ptr),hl
    ret

; tone lo, tone hi, noise (0=off), volume
sfx_jump:   db #2c,1,0,12, #04,1,0,12, #dc,0,0,11, #be,0,0,10, #aa,0,0,8, #96,0,0,5, #ff
sfx_swish:  db 0,0,3,9, 0,0,4,11, 0,0,6,8, 0,0,9,5, #ff
sfx_hit:    db #58,2,15,15, #80,2,18,13, #b0,2,22,10, #e0,2,26,7, #20,3,30,4, #ff
sfx_lamp:   db #78,0,0,13, #64,0,0,13, #50,0,0,13, #3c,0,0,13, #50,0,0,10, #3c,0,0,10, #3c,0,0,6, #ff
sfx_hurt:   db #c8,0,0,14, #2c,1,0,13, #90,1,0,12, #f4,1,0,11, #58,2,0,10, #bc,2,0,8, #20,3,0,6, #ff
sfx_gate:   db 0,4,31,12, 0,4,30,13, 0,4,31,12, 0,4,29,12, 0,4,31,11, 0,4,30,10, 0,4,31,9, 0,4,31,8, 0,4,31,6, 0,4,31,4, #ff
sfx_splash: db 0,0,6,15, 0,0,8,14, 0,0,10,12, 0,0,13,10, 0,0,16,8, 0,0,20,6, 0,0,24,4, #ff
sfx_start:  db #c8,0,0,12, #c8,0,0,12, #96,0,0,12, #96,0,0,12, #64,0,0,13, #64,0,0,13, #64,0,0,10, #64,0,0,6, #ff

; ---------------------------------------------------------------- boot
start:
    ld sp,#c000
    im 1
    ld hl,0 : ld de,0 : ld bc,#4000 : ldir
    ld hl,unlock : ld bc,#bc11
.u  inc b : outi : dec c : jr nz,.u
    ld hl,crtc : ld d,0
.c  ld bc,#bc00 : out (c),d : ld a,(hl) : inc b : out (c),a : inc hl : inc d : ld a,d : cp 14 : jr nz,.c
    ld bc,#f782 : out (c),c
    ld bc,#7f8c : out (c),c : ld c,#b8 : out (c),c
    ld hl,#8000 : ld de,#8001 : ld bc,#3fff : ld (hl),0 : ldir
    ld a,#8c : ld (sh_mode),a : ld a,#b8 : ld (sh_rmr2),a
    ld hl,#c000 : ld de,#c001 : ld bc,#3fff : ld (hl),0 : ldir
    ; line address table
    ld hl,line_tab : ld de,#c000 : ld c,0
.lt ld (hl),e : inc hl : ld (hl),d : inc hl
    ld a,d : add a,8 : ld d,a
    inc c : ld a,c : and 7 : jr nz,.lt2
    ld a,d : sub #40 : ld d,a : ld a,e : add a,80 : ld e,a : jr nc,.lt2 : inc d
.lt2 ld a,c : cp 200 : jr nz,.lt
    ; silence PSG
    ld a,7 : ld c,#3f : call psg_write
    ld a,8 : ld c,0 : call psg_write
    ld a,9 : ld c,0 : call psg_write
    ld a,10 : ld c,0 : call psg_write
    ; ASIC defaults
    xor a : ld (#6801),a : ld (#6804),a : ld (#6c0f),a
    call blackout
    ; sprite palette + spark sprite (from bank 1)
    ld a,1 : call page_in
    ld hl,sprite_pal : ld de,sbuf : ld bc,30 : ldir
    ld hl,spark_gfx : ld de,sbuf+32 : ld bc,256 : ldir
    call asic_on
    ld hl,sbuf : ld de,#6422 : ld bc,30 : ldir
    ld hl,sbuf+32 : ld de,#4000+12*256 : ld bc,256 : ldir
    ld a,1 : ld (band),a : ld a,7 : ld (#6800),a
    im 1
    ei
    jp title

unlock: db #ff,#00,#ff,#77,#b3,#51,#a8,#d4,#62,#39,#9c,#46,#2b,#15,#8a,#cd,#ee
crtc:   db 63,40,46,#8e,38,0,25,30,0,7,0,0,#30,0

; ---------------------------------------------------------------- paging
page_in:                ; A = cartridge page, mapped at #4000
    di
    or #a8 : ld (sh_rmr2),a : ld b,#7f : out (c),a
    ld a,#88 : ld (sh_mode),a : out (c),a
    ei
    ret

asic_on:                ; ASIC registers at #4000, RAM at #0000
    di
    ld a,#8c : ld (sh_mode),a : ld bc,#7f8c : out (c),c
    ld a,#b8 : ld (sh_rmr2),a : out (c),a
    ei
    ret

dzx0:
    dzx0_standard

wait_frame:
.w  ld a,(frames) : cp 2 : jr c,.w
    xor a : ld (frames),a
    ret

blackout:               ; black palette, flat gradient, sprites off
    call asic_on
    xor a : ld (pal_on),a
    ld hl,#6400 : ld b,34
.p  ld (hl),a : inc hl : djnz .p
    ld hl,grad_ram : ld b,50
.g  ld (hl),a : inc hl : djnz .g
hide_all:
    ld hl,#6004 : ld b,16 : xor a
.s  ld (hl),a : ld a,l : add a,8 : ld l,a : xor a : djnz .s
    ret

; ---------------------------------------------------------------- screen helpers
next_line:              ; HL = next scanline address
    ld a,h : add a,8 : ld h,a : ret nc
    ld a,l : add a,#50 : ld l,a : ld a,h : adc a,#c0 : ld h,a
    ret

line_addr:              ; A = line -> HL
    ld l,a : ld h,0 : add hl,hl : push de : ld de,line_tab : add hl,de
    ld a,(hl) : inc hl : ld h,(hl) : ld l,a : pop de
    ret

cell_addr:              ; B=col C=row -> HL screen
    ld a,c : add a,a : add a,a : add a,a : call line_addr
    push de : ld a,b : add a,a : add a,a : ld e,a : ld d,0 : add hl,de : pop de
    ret

; ---------------------------------------------------------------- map
map_ptr:                ; B=col C=row (row clamped 0..24) -> HL
    ld a,c : cp 25 : jr c,.ok
    rla : ld a,0 : jr c,.ok         ; negative -> 0
    ld a,24
.ok push de
    ld l,a : ld h,0 : add hl,hl : add hl,hl : ld d,h : ld e,l : add hl,hl : add hl,hl : add hl,de
    ld e,b : ld d,0 : add hl,de : ld de,map_ram : add hl,de
    pop de
    ret

get_cell:               ; B=col C=row -> A (preserves BC,DE)
    ld a,b : cp 20 : jr nc,.z
    call map_ptr : ld a,(hl)
    ret
.z  xor a
    ret

row_of:                 ; A=y -> C=row
    rrca : rrca : rrca : and 31 : ld c,a
    ret

standable:              ; B=col C=row -> CF if feet can rest on top of this cell
    call get_cell
    cp T_SOLID : jr z,.y
    cp T_PLAT : jr z,.y
    cp T_GATE : jr z,.y
    cp T_LADDER : jr nz,.n
    dec c : call get_cell : inc c
    cp T_LADDER : jr z,.n
.y  scf
    ret
.n  or a
    ret

solid_at:               ; B,C -> CF if wall
    call get_cell
    cp T_SOLID : jr z,.y
    cp T_GATE : jr z,.y
    or a
    ret
.y  scf
    ret

char_cx:                ; IX -> A = centre column
    ld a,(ix+C_X) : add a,8 : rrca : rrca : rrca : and 31
    ret

on_ground:              ; IX -> CF if standing
    ld a,(ix+C_Y) : and 7 : ret nz
    call char_cx : ld b,a : ld a,(ix+C_Y) : call row_of
    jp standable

walk_try:               ; A=newX B=dx -> CF blocked (preserves B,E)
    push bc
    bit 7,b : jr nz,.l
    add a,12 : jr .c
.l  add a,3
.c  rrca : rrca : rrca : and 31 : ld b,a
    ld a,(ix+C_Y) : dec a : call row_of : call solid_at : jr c,.x
    ld a,(ix+C_Y) : sub 16 : call row_of : call solid_at : jr c,.x
    ld a,(ix+C_Y) : sub 28 : call row_of : call solid_at
.x  pop bc
    ret

snap_ladder:            ; IX: centre on ladder column
    call char_cx : add a,a : add a,a : add a,a : sub 4 : jr nc,.ok : xor a
.ok ld (ix+C_X),a
    ld a,(ix+C_Y) : and #fe : ld (ix+C_Y),a
    ret

; ---------------------------------------------------------------- text
pen_l: db #00,#80,#08,#88,#20,#a0,#28,#a8,#02,#82,#0a,#8a,#22,#a2,#2a,#aa

set_colours:            ; A=fg pen, C=bg pen
    push hl
    ld hl,pen_l : ld e,a : ld d,0 : add hl,de : ld d,(hl)      ; d = fgL
    ld hl,pen_l : ld a,c : ld c,0 : ld b,c : ld c,a : add hl,bc : ld e,(hl) ; e = bgL
    ld hl,tc
    ld a,e : srl a : or e : ld (hl),a : inc l              ; 00 bg bg
    ld a,d : srl a : or e : ld (hl),a : inc l              ; 01 bg fg
    ld a,e : srl a : or d : ld (hl),a : inc l              ; 10 fg bg
    ld a,d : srl a : or d : ld (hl),a                      ; 11 fg fg
    pop hl
    ret

print_char:             ; A=char D=col E=line ; bank 1 must be paged ; D++
    push de
    push hl
    sub 32 : jr nc,.a : xor a
.a  cp 59 : jr c,.b : xor a
.b  ld l,a : ld h,0 : add hl,hl : add hl,hl : add hl,hl : ld bc,font_data+1 : add hl,bc
    push hl
    ld a,e : call line_addr
    ld a,d : add a,a : add a,a : ld c,a : ld b,0 : add hl,bc
    pop de
    ld b,7
.row push bc
    push hl
    ld a,(de) : inc de : ld c,a
    ld b,4
.px ld a,c : rlca : rlca : ld c,a : and 3
    push hl : ld l,a : ld h,tc/256 : ld a,(hl) : pop hl
    ld (hl),a : inc hl
    djnz .px
    pop hl
    call next_line
    pop bc
    djnz .row
    pop hl
    pop de
    inc d
    ret

print_str:              ; HL=string D=col E=line
    ld a,(hl) : or a : ret z
    inc hl
    call print_char
    jr print_str

print_bcd:              ; A = 2 BCD digits
    push af
    rrca : rrca : rrca : rrca : and 15 : add a,'0' : call print_char
    pop af
    and 15 : add a,'0'
    jp print_char

print_dec2:             ; A = 0..99
    ld b,'0'-1
.l  inc b : sub 10 : jr nc,.l
    add a,10+'0' : push af
    ld a,b : call print_char
    pop af
    jp print_char

; ---------------------------------------------------------------- HUD
draw_hud_full:          ; bank 1 paged
    ld a,4 : ld c,1 : call set_colours
    ld hl,name_ram : ld de,#0000 : call print_str
draw_stats:
    ld a,2 : ld c,1 : call set_colours
    ld de,#0009
    ld a,(score) : call print_bcd
    ld a,(score+1) : call print_bcd
    ld a,(score+2) : call print_bcd
    ld hl,txt_lamp : ld d,7 : call print_str
    ld a,(lcount) : call print_dec2
    ld hl,txt_life : ld d,15 : call print_str
    ld a,(lives) : add a,'0' : call print_char
    xor a : ld (hud_dirty),a
    ret

hud_refresh:
    ld a,1 : call page_in
    call draw_stats
    jp asic_on

txt_lamp: db "LAMP",0
txt_life: db "LIFE",0

score_add:              ; DE = 4 BCD digits
    ld hl,score+2
    ld a,(hl) : add a,e : daa : ld (hl),a : dec hl
    ld a,(hl) : adc a,d : daa : ld (hl),a : dec hl
    ld a,(hl) : adc a,0 : daa : ld (hl),a
    ld a,1 : ld (hud_dirty),a
    ret

; ---------------------------------------------------------------- lanterns
lamp_bit:               ; A = global id -> HL byte, A mask
    ld e,a : srl a : srl a : srl a : ld l,a : ld h,0
    push de : ld de,lgot : add hl,de : pop de
    ld a,e : and 7 : ld b,a : ld a,1 : ret z
.s  add a,a : djnz .s
    ret

lamp_addr:              ; A = local idx -> HL screen, DE save buffer
    push af
    ld l,a : ld h,0 : add hl,hl : ld de,lant_ram : add hl,de
    ld a,(hl) : add a,a : add a,a : ld e,a : inc hl
    ld a,(hl) : add a,a : add a,a : add a,a
    call line_addr
    ld d,0 : add hl,de
    pop af
    push hl
    ld l,a : ld h,0 : add hl,hl : add hl,hl : add hl,hl : add hl,hl : add hl,hl : add hl,hl
    ld de,lsave : add hl,de : ex de,hl
    pop hl
    ret

lamp_draw:              ; A = local idx ; bank 1 paged
    call lamp_addr
    push ix
    ld ix,lantern_gfx
    ld b,16
.row push bc
    push hl
    ld b,4
.px ld a,(hl) : ld (de),a : inc de
    and (ix+0) : or (ix+1) : ld (hl),a : inc hl
    inc ix : inc ix
    djnz .px
    pop hl
    call next_line
    pop bc
    djnz .row
    pop ix
    ret

lamp_erase:             ; A = local idx
    call lamp_addr
    ex de,hl
    ld b,16
.row push bc
    push de
    ld bc,4 : ldir
    ex (sp),hl
    call next_line
    ex de,hl
    pop hl
    pop bc
    djnz .row
    ret

draw_lanterns:
    ld a,(rrec+RR_NL) : or a : ret z
    ld b,a : ld c,0
.l  push bc
    ld a,(rrec+RR_LB) : add a,c : call lamp_bit : and (hl)
    pop bc : push bc
    jr nz,.sk
    ld a,c : call lamp_draw
.sk pop bc
    inc c
    djnz .l
    ret

lamp_check:             ; hero vs uncollected lanterns
    ld a,(hero+C_ST) : cp ST_DOWN : ret z
    ld a,(rrec+RR_NL) : or a : ret z
    ld b,a : ld c,0
.l  push bc
    ld a,(rrec+RR_LB) : add a,c : call lamp_bit : and (hl)
    pop bc : push bc
    jr nz,.nx
    ld l,c : ld h,0 : add hl,hl : ld de,lant_ram : add hl,de
    ld a,(hl) : add a,a : add a,a : add a,a : ld d,a      ; lx
    inc hl : ld a,(hl) : add a,a : add a,a : add a,a : ld e,a ; ly
    ; hero x0 = X+3 < lx+8  ->  X+3-8 < lx -> X < lx+5
    ld a,d : add a,5 : ld b,a : ld a,(hero+C_X) : cp b : jr nc,.nx
    ; hero x1 = X+13 > lx -> X+13 > lx
    ld a,(hero+C_X) : add a,13 : cp d : jr c,.nx : jr z,.nx
    ; hero y0 = Y-30 < ly+16 -> Y < ly+46
    ld a,e : add a,46 : ld b,a : ld a,(hero+C_Y) : cp b : jr nc,.nx
    ; hero y1 = Y > ly
    ld a,(hero+C_Y) : cp e : jr c,.nx : jr z,.nx
    pop bc : push bc
    call collect
.nx pop bc
    inc c
    djnz .l
    ret

collect:                ; C = local idx
    push bc
    ld a,(rrec+RR_LB) : add a,c : call lamp_bit : or (hl) : ld (hl),a
    pop bc
    ld a,c : call lamp_erase
    ld hl,lcount : inc (hl)
    ld de,#0125 : call score_add
    ld hl,sfx_lamp : call play_sfx
    ld a,(gate_closed) : or a : ret z
    ld a,(rrec+RR_GREQ) : ld b,a : ld a,(lcount) : cp b : ret c
    jp open_gate

; ---------------------------------------------------------------- gates
gate_cells:             ; call IY for each gate cell with B=col C=row
    ld a,(rrec+RR_GY) : ld c,a
    ld a,(rrec+RR_GH) : ld d,a
.r  ld a,(rrec+RR_GX) : ld b,a
    ld a,(rrec+RR_GW) : ld e,a
.c  push bc
    push de
    call .cb
    pop de
    pop bc
    inc b : dec e : jr nz,.c
    inc c : dec d : jr nz,.r
    ret
.cb jp (iy)

gate_draw_cb:
    call cell_addr
    ld de,(gptr)
    push ix
    ld ix,hatch_gfx
    ld a,(rrec+RR_GKIND) : or a : jr z,.h
    ld ix,door_gfx
.h  ld b,8
.r  push bc
    push hl
    ld b,4
.p  ld a,(hl) : ld (de),a : inc de
    ld a,(ix+0) : ld (hl),a : inc hl : inc ix
    djnz .p
    pop hl
    call next_line
    pop bc
    djnz .r
    pop ix
    ld (gptr),de
    ret

gate_restore_cb:
    call cell_addr
    ex de,hl
    ld hl,(gptr)
    ld b,8
.r  push bc
    push de
    ld bc,4 : ldir
    ex (sp),hl
    call next_line
    ex de,hl
    pop hl
    pop bc
    djnz .r
    ld (gptr),hl
    ret

gate_open_cb:
    call map_ptr
    ex de,hl
    ld hl,(gidx) : ld h,0 : ld bc,gopen_ram : add hl,bc
    ld a,(hl) : ld (de),a
    ld hl,gidx : inc (hl)
    ret

setup_gate:             ; bank 1 paged
    xor a : ld (gate_closed),a
    ld a,(rrec+RR_GREQ) : or a : ret z
    ld b,a : ld a,(lcount) : cp b : jr nc,gate_map_open
    ld a,1 : ld (gate_closed),a
    ld hl,gsave : ld (gptr),hl
    ld iy,gate_draw_cb
    jp gate_cells

gate_map_open:
    xor a : ld (gidx),a
    ld iy,gate_open_cb
    jp gate_cells

open_gate:
    xor a : ld (gate_closed),a
    ld hl,gsave : ld (gptr),hl
    ld iy,gate_restore_cb : call gate_cells
    call gate_map_open
    ld hl,sfx_gate
    jp play_sfx

; ---------------------------------------------------------------- rooms
load_room:              ; A = room
    ld (room),a
    call blackout
    ld a,#ff : ld (next_room),a
    xor a : ld (spark_t),a
    ld a,1 : call page_in
    ld a,(room) : add a,a : ld l,a : ld h,0 : ld de,room_table : add hl,de
    ld a,(hl) : inc hl : ld h,(hl) : ld l,a
    ld de,rrec : ld bc,29 : ldir
    ld hl,(rrec+RR_MAP) : ld de,map_ram : ld bc,500 : ldir
    ld hl,(rrec+RR_PAL) : ld de,pal_ram : ld bc,32 : ldir
    ld hl,(rrec+RR_GRAD) : ld de,grad_new : ld bc,50 : ldir
    ld hl,(rrec+RR_LANT) : ld de,lant_ram : ld bc,16 : ldir
    ld hl,(rrec+RR_ENEM) : ld de,spawn_ram : ld bc,10 : ldir
    ld hl,(rrec+RR_GOPEN) : ld de,gopen_ram : ld bc,16 : ldir
    ld hl,(rrec+RR_NAME) : ld de,name_ram : ld bc,20 : ldir
    ld a,(rrec+RR_PAGE) : call page_in
    ld hl,(rrec+RR_BMP) : ld de,#c000 : call dzx0
    ld a,1 : call page_in
    call draw_lanterns
    call setup_gate
    call draw_hud_full
    call asic_on
    call init_enemies
    ld a,#ff : ld (hero+C_SHOWN),a
palette_on:
    ld hl,pal_ram : ld de,#6400 : ld bc,32 : ldir
    ld hl,grad_new : ld de,grad_ram : ld bc,50 : ldir
    ld a,1 : ld (pal_on),a
    ret

set_entry:
    ld a,(hero+C_X) : ld (entry_x),a
    ld a,(hero+C_Y) : ld (entry_y),a
    ld a,(hero+C_ST) : cp ST_CLIMB : jr z,.c
    xor a
.c  ld (entry_st),a
    ret

; ---------------------------------------------------------------- sprites
set_spr:                ; HL=attr DE=x BC=y, mag x2/x1
    ld (hl),e : inc l : ld (hl),d : inc l : ld (hl),c : inc l : ld (hl),b : inc l
    ld (hl),9 : ld a,l : add a,4 : ld l,a
    ret

spr_attr:               ; IX -> HL attr of first sprite
    ld a,(ix+C_SPR) : add a,a : add a,a : add a,a : ld l,a : ld h,#60
    ret

char_hide:
    call spr_attr : inc l : inc l : inc l : inc l
    ld b,4 : xor a
.l  ld (hl),a : ld a,l : add a,8 : ld l,a : xor a : djnz .l
    ret

char_draw:              ; IX
    ld a,(ix+C_VIS) : or a : jr z,char_hide
    ld a,(ix+C_INV) : and 2 : jr nz,char_hide
    ld a,(ix+C_DIR) : rrca : or (ix+C_FRAME) : cp (ix+C_SHOWN) : call nz,upload
    ld l,(ix+C_X) : ld h,0 : add hl,hl : add hl,hl : ex de,hl
    ld a,(ix+C_Y) : sub 32 : ld c,a : ld b,0
    call spr_attr
    call set_spr
    ex de,hl : push bc : ld bc,32 : add hl,bc : pop bc : ex de,hl
    call set_spr
    ex de,hl : push bc : ld bc,-32 : add hl,bc : pop bc : ex de,hl
    ld a,c : add a,16 : ld c,a
    call set_spr
    ex de,hl : push bc : ld bc,32 : add hl,bc : pop bc : ex de,hl
    jp set_spr

upload:                 ; A = frame|dir<<7
    ld (ix+C_SHOWN),a
    ld a,2 : call page_in
    ld a,(ix+C_FRAME) : add a,a : add a,#40 : ld h,a : ld l,0
    ld de,sbuf : ld bc,512 : ldir
    call asic_on
    ld a,(ix+C_SPR) : add a,#40 : ld d,a : ld e,0
    ld a,(ix+C_DIR) : or a : jr nz,.flip
    ld hl,sbuf : ld c,2
.o  ld b,0
.i  ld a,(hl) : inc hl
    rrca : rrca : rrca : rrca : ld (de),a : inc de
    rrca : rrca : rrca : rrca : ld (de),a : inc de
    djnz .i
    dec c : jr nz,.o
    ret
.flip
    ld hl,sbuf+128 : call flip16
    ld hl,sbuf : call flip16
    ld hl,sbuf+384 : call flip16
    ld hl,sbuf+256
flip16:
    ld c,16
.r  ld a,l : add a,7 : ld l,a : ld a,h : adc a,0 : ld h,a
    ld b,8
.p  ld a,(hl) : dec hl : ld (de),a : inc de
    rrca : rrca : rrca : rrca : ld (de),a : inc de
    djnz .p
    ld a,l : add a,9 : ld l,a : ld a,h : adc a,0 : ld h,a
    dec c : jr nz,.r
    ret

spark_update:
    ld a,(spark_t) : or a : jr z,.off
    dec a : ld (spark_t),a
    ld a,(spark_x) : ld l,a : ld h,0 : add hl,hl : add hl,hl : ld (#6000+12*8),hl
    ld a,(spark_y) : ld l,a : ld h,0 : ld (#6002+12*8),hl
    ld a,9 : ld (#6004+12*8),a
    ret
.off ld (#6004+12*8),a
    ret

; ---------------------------------------------------------------- hero
hero_update:
    ld ix,hero
    ld a,(ix+C_INV) : or a : jr z,.ni
    dec (ix+C_INV)
.ni ld a,(ix+C_ST)
    cp ST_DOWN : jp z,h_down
    cp ST_PUNCH : jp z,h_attack
    cp ST_KICK : jp z,h_attack
    cp ST_CLIMB : jp z,h_climb
    cp ST_JUMP : jp z,h_jump
    call on_ground : jr c,h_ground
    ; walked off an edge: fall from jump apex
    ld (ix+C_ST),ST_JUMP : ld (ix+C_VY),JUMP_APEX : ld (ix+C_DX),0
    ld (ix+C_FLAGS),0
    ld (ix+C_FRAME),FR_HERO_JUMP
    ret

h_ground:
    ld a,(inp_old) : cpl : ld c,a : ld a,(inp) : and c : and I_FIRE : jr nz,.attack
    ld a,(inp) : ld c,a
    bit 0,c : jr nz,.up
    bit 1,c : jp nz,.down
    bit 2,c : jp nz,.left
    bit 3,c : jp nz,.right
    ld (ix+C_ST),ST_STAND : ld (ix+C_FRAME),FR_HERO_STAND
    ret
.attack
    ld a,(inp) : ld c,a : and I_LEFT|I_RIGHT : jr z,.punch
    call set_dir
    ld (ix+C_ST),ST_KICK : ld (ix+C_TIMER),8 : ld (ix+C_FRAME),FR_HERO_KICK
    jr .atk
.punch
    ld (ix+C_ST),ST_PUNCH : ld (ix+C_TIMER),6 : ld (ix+C_FRAME),FR_HERO_PUNCH
.atk ld (ix+C_FLAGS),0
    ld hl,sfx_swish : jp play_sfx
.up call char_cx : ld b,a : ld a,(ix+C_Y) : call row_of : dec c : call get_cell
    cp T_LADDER : jr nz,.jump
    call snap_ladder
    ld (ix+C_ST),ST_CLIMB : ld (ix+C_FRAME),FR_HERO_CLIMB0
    ret
.jump
    ld (ix+C_ST),ST_JUMP : ld (ix+C_VY),0 : ld (ix+C_FLAGS),0
    ld a,(inp) : ld c,a : call set_dir
    ld b,0
    bit 2,c : jr z,.j1 : ld b,-2
.j1 bit 3,c : jr z,.j2 : ld b,2
.j2 ld (ix+C_DX),b
    ld (ix+C_FRAME),FR_HERO_JUMP
    ld hl,sfx_jump : jp play_sfx
.down
    call char_cx : ld b,a : ld a,(ix+C_Y) : call row_of : call get_cell
    cp T_LADDER : ret nz
    call snap_ladder
    ld (ix+C_ST),ST_CLIMB : ld (ix+C_FRAME),FR_HERO_CLIMB0
    ret
.left
    ld (ix+C_DIR),1 : ld a,-2 : jr .walk
.right
    ld (ix+C_DIR),0 : ld a,2
.walk
    call hero_move
    ld (ix+C_ST),ST_WALK
    inc (ix+C_ANIM) : ld a,(ix+C_ANIM) : rrca : and 3 : add a,FR_HERO_WALK0 : ld (ix+C_FRAME),a
    ret

set_dir:                ; C = input
    bit 2,c : jr z,.r : ld (ix+C_DIR),1 : ret
.r  bit 3,c : ret z
    ld (ix+C_DIR),0
    ret

hero_move:              ; A = dx (hero, with room exits)
    ld b,a : ld a,(ix+C_X) : add a,b
    bit 7,b : jr z,.r
    jr nc,.exw
    jr .t
.r  cp 145 : jr nc,.exe
.t  ld e,a : call walk_try : ret c
    ld (ix+C_X),e
    ret
.exw call gate_edge : or a : jr z,.cw
    ld a,(rrec+RR_W) : cp #ff : jr z,.cw
    ld (next_room),a : ld (ix+C_X),142
    ret
.cw ld (ix+C_X),0
    ret
.exe call gate_edge : cp 19 : jr z,.ce
    ld a,(rrec+RR_E) : cp #ff : jr z,.ce
    ld (next_room),a : ld (ix+C_X),2
    ret
.ce ld (ix+C_X),144
    ret

gate_edge:              ; -> A = column of a closed vertical gate, else #ff
    ld a,(gate_closed) : or a : jr z,.n
    ld a,(rrec+RR_GKIND) : or a : jr z,.n
    ld a,(rrec+RR_GX)
    ret
.n  ld a,#ff
    ret

h_attack:
    dec (ix+C_TIMER) : jr z,.end
    ld a,(ix+C_TIMER) : cp 4 : ret nz
    ld c,11
    ld a,(ix+C_ST) : cp ST_PUNCH : jp z,hero_hit_check
    ld c,15
    jp hero_hit_check
.end ld (ix+C_ST),ST_STAND : ld (ix+C_FRAME),FR_HERO_STAND
    ret

h_climb:
    ld a,(inp) : ld c,a
    bit 0,c : jr nz,.up
    bit 1,c : jr nz,.dn
    and I_LEFT|I_RIGHT : ret z
    ld a,(ix+C_Y) : and 7 : ret nz
    call char_cx : ld b,a : ld a,(ix+C_Y) : call row_of : call standable : ret nc
    ld a,(inp) : ld c,a : call set_dir
.stand
    ld (ix+C_ST),ST_STAND : ld (ix+C_FRAME),FR_HERO_STAND
    ret
.up ld a,(ix+C_Y) : and 7 : jr nz,.mvu
    call char_cx : ld b,a : ld a,(ix+C_Y) : call row_of : dec c : call get_cell
    cp T_LADDER : jr nz,.stand
.mvu ld a,(ix+C_Y) : sub 2 : ld (ix+C_Y),a
    cp TOP_Y : jr nc,.anim
    ld a,(rrec+RR_N) : cp #ff : jr z,.cn
    ld (next_room),a : ld (ix+C_Y),200
    jr .anim
.cn ld (ix+C_Y),TOP_Y
    jr .anim
.dn ld a,(ix+C_Y) : and 7 : jr nz,.mvd
    call char_cx : ld b,a : ld a,(ix+C_Y) : call row_of : call get_cell
    cp T_LADDER : jr nz,.stand
.mvd ld a,(ix+C_Y) : add a,2 : ld (ix+C_Y),a
    cp 201 : jr c,.anim
    ld a,(rrec+RR_S) : cp #ff : jr z,.cs
    ld (next_room),a : ld (ix+C_Y),TOP_Y
    jr .anim
.cs ld (ix+C_Y),200
.anim
    inc (ix+C_ANIM) : ld a,(ix+C_ANIM) : rrca : and 1 : add a,FR_HERO_CLIMB0 : ld (ix+C_FRAME),a
    ret

h_jump:
    ld a,(inp_old) : cpl : ld c,a : ld a,(inp) : and c : and I_FIRE : jr z,.nf
    bit 1,(ix+C_FLAGS) : jr nz,.nf
    set 1,(ix+C_FLAGS) : res 0,(ix+C_FLAGS)
    ld (ix+C_FRAME),FR_HERO_FLYKICK
    ld hl,sfx_swish : call play_sfx
.nf ; grab a ladder in mid-air
    ld a,(inp) : and I_UP : jr z,.ng
    call char_cx : ld b,a : ld a,(ix+C_Y) : dec a : call row_of : call get_cell
    cp T_LADDER : jr nz,.ng
    call snap_ladder
    ld (ix+C_ST),ST_CLIMB : ld (ix+C_FRAME),FR_HERO_CLIMB0
    ret
.ng ld a,(ix+C_DX) : or a : call nz,hero_move
    ld a,(next_room) : cp #ff : ret nz
    ; vertical
    ld e,(ix+C_VY) : ld d,0 : ld hl,jump_tab : add hl,de : ld b,(hl)
    ld a,e : cp JUMP_LEN-1 : jr nc,.vm
    inc (ix+C_VY)
.vm bit 7,b : jr z,.fall
    ; rising
    ld a,(ix+C_Y) : add a,b : cp TOP_Y : jr c,.bump
    ld e,a : sub 32 : call row_of : call char_cx : ld b,a : call get_cell
    cp T_SOLID : jr z,.bump
    ld (ix+C_Y),e
    jr .fk
.bump ld (ix+C_VY),JUMP_APEX
    jr .fk
.fall
    ld a,(ix+C_Y) : ld e,a : or 7 : inc a : ld d,a
    ld a,e : add a,b : ld (ix+C_Y),a
    cp d : jr c,.nl
    call char_cx : ld b,a : ld a,d : call row_of : call standable : jr nc,.nl
    ld (ix+C_Y),d
    ld (ix+C_ST),ST_STAND : ld (ix+C_FRAME),FR_HERO_STAND
    ret
.nl call char_cx : ld b,a : ld a,(ix+C_Y) : sub 3 : call row_of : call get_cell
    cp T_WATER : jp z,hero_drown
    ld a,(ix+C_Y) : cp 200 : jr c,.fk
    ld a,(rrec+RR_S) : cp #ff : jp z,hero_drown
    ld (next_room),a : ld (ix+C_Y),TOP_Y
    ret
.fk bit 1,(ix+C_FLAGS) : ret z
    bit 0,(ix+C_FLAGS) : ret nz
    ld c,15
    jp hero_hit_check

jump_tab: db -6,-6,-5,-5,-4,-3,-3,-2,-2,-1,0,1,2,2,3,3,4,5,5,6,6,7,8

h_down:
    dec (ix+C_TIMER) : ret nz
    ld a,(lives) : or a : jr nz,.r
    ld a,1 : ld (game_state),a
    ret
.r  ld a,(entry_x) : ld (ix+C_X),a
    ld a,(entry_y) : ld (ix+C_Y),a
    ld a,(entry_st) : ld (ix+C_ST),a
    ld (ix+C_INV),100
    push ix
    ld ix,en0 : call en_retreat
    ld ix,en1 : call en_retreat
    pop ix
    ld (ix+C_FRAME),FR_HERO_STAND
    ld a,(entry_st) : or a : ret z
    ld (ix+C_FRAME),FR_HERO_CLIMB0
    ret

en_retreat:             ; send thugs back to their spawn after hero respawns
    ld a,(ix+C_TYPE) : or a : ret z
    cp 3 : ret z
    ld (ix+C_ST),E_INACTIVE : ld (ix+C_VIS),0 : ld (ix+C_TIMER),75
    ret

hero_drown:
    ld hl,sfx_splash
    jr hero_kill
hero_hurt:              ; enemy blow (any IX)
    ld a,(hero+C_INV) : or a : ret nz
    ld a,(hero+C_ST) : cp ST_DOWN : ret z
    ld hl,sfx_hurt
hero_kill:
    call play_sfx
    ld a,ST_DOWN : ld (hero+C_ST),a
    ld a,40 : ld (hero+C_TIMER),a
    ld a,FR_HERO_DOWN : ld (hero+C_FRAME),a
    ld a,(lives) : or a : jr z,.z
    dec a : ld (lives),a
.z  ld a,1 : ld (hud_dirty),a
    ret

hero_hit_check:         ; C = reach
    ld a,(hero+C_X) : add a,24 : ld e,a
    ld a,(hero+C_DIR) : or a : jr nz,.lf
    ld d,e : ld a,e : add a,c : ld e,a
    jr .go
.lf ld a,e : sub c : ld d,a
.go ld iy,en0 : call .one
    ld iy,en1
.one
    ld a,(iy+C_TYPE) : or a : ret z
    ld a,(iy+C_ST) : or a : ret z
    cp E_HURT : ret nc
    ld a,(iy+C_Y) : ld b,a : ld a,(hero+C_Y) : sub b : jr nc,.p : neg
.p  cp 20 : ret nc
    ld a,(iy+C_X) : add a,28 : cp d : ret c : ret z
    ld a,(iy+C_X) : add a,20 : cp e : ret nc
    ld hl,hero+C_FLAGS : set 0,(hl)
    push de
    call enemy_hit
    pop de
    ret

enemy_hit:              ; IY = enemy
    ld hl,sfx_hit : call play_sfx
    ld a,(iy+C_X) : add a,4 : ld (spark_x),a
    ld a,(hero+C_Y) : sub 26 : ld (spark_y),a
    ld a,4 : ld (spark_t),a
    ld de,#0050 : call score_add
    ld a,2 : ld b,a
    ld a,(hero+C_DIR) : or a : jr z,.k : ld b,-2
.k  ld (iy+C_DX),b
    dec (iy+C_HP) : jr z,.ko
    ld (iy+C_ST),E_HURT : ld (iy+C_TIMER),6
    ret
.ko ld (iy+C_ST),E_KO : ld (iy+C_TIMER),50
    ld a,(iy+C_TYPE) : dec a : add a,a : ld e,a : ld d,0 : ld hl,ko_score : add hl,de
    ld e,(hl) : inc hl : ld d,(hl)
    jp score_add

ko_score: dw #0250,#0500,#5000

; ---------------------------------------------------------------- enemies
; per type tables (index 0 unused)
t_hp:     db 0,2,4,10
t_speed:  db 0,2,1,2
t_windup: db 0,6,8,5
t_cool:   db 0,18,24,10
t_reach:  db 0,19,17,20
t_frame:  db 0,FR_HOODIE_STAND,FR_BOUNCER_STAND,FR_BOSS_STAND

type_val:               ; HL = table -> A = table[type]
    ld e,(ix+C_TYPE) : ld d,0 : add hl,de : ld a,(hl)
    ret

set_eframe:             ; A = offset (0 stand,1/2 walk,3 windup,4 attack,5 down)
    push af : ld hl,t_frame : call type_val : pop bc : add a,b
    ld (ix+C_FRAME),a
    ret

init_enemies:
    ld ix,en0 : ld hl,spawn_ram : ld c,4 : ld b,25 : call .one
    ld ix,en1 : ld hl,spawn_ram+3 : ld c,8 : ld b,70
    ld a,(spawn_ram) : cp #ff : jr nz,.one
    ld (ix+C_TYPE),0
    ret
.one
    push bc : push hl
    push ix : pop hl : ld b,20
.z  ld (hl),0 : inc hl : djnz .z
    pop hl : pop bc
    ld (ix+C_SPR),c : ld (ix+C_TIMER),b : ld (ix+C_SHOWN),#ff
    ld a,(hl) : cp #ff : jr nz,.ok
    xor a
.ok ld (ix+C_TYPE),a
    inc hl : ld a,(hl) : add a,a : add a,a : add a,a : sub 4 : jr nc,.x : xor a
.x  ld (ix+C_SX),a
    inc hl : ld a,(hl) : inc a : add a,a : add a,a : add a,a : ld (ix+C_SY),a
    ret

enemy_update:
    ld a,(ix+C_TYPE) : or a : ret z
    inc (ix+C_ANIM)
    ld a,(ix+C_ST)
    or a : jp z,en_inactive
    cp E_KO : jp z,en_ko
    cp E_HURT : jp z,en_hurt
    cp E_WINDUP : jp z,en_windup
    cp E_ATTACK : jp z,en_attack
    cp E_CLIMB : jp z,en_climb
    ; walking / falling
    call on_ground : jp c,en_ground
    ld a,(ix+C_Y) : ld e,a : or 7 : inc a : ld d,a
    ld a,e : add a,4 : ld (ix+C_Y),a
    cp d : jr c,.fc
    call char_cx : ld b,a : ld a,d : call row_of : call standable : jr nc,.fc
    ld (ix+C_Y),d
.fc ld a,(ix+C_Y) : cp 200 : ret c
en_vanish:
    ld (ix+C_ST),E_INACTIVE : ld (ix+C_VIS),0 : ld (ix+C_TIMER),100
    ret

en_inactive:
    dec (ix+C_TIMER) : ret nz
    ld a,(hero+C_X) : sub (ix+C_SX) : jr nc,.dp
    neg
.dp cp 40 : jr nc,.go
    ld a,(hero+C_Y) : sub (ix+C_SY) : jr nc,.dy
    neg
.dy cp 24 : jr nc,.go
    ld (ix+C_TIMER),25
    ret
.go
    ld a,(ix+C_SX) : ld (ix+C_X),a
    ld a,(ix+C_SY) : ld (ix+C_Y),a
    ld hl,t_hp : call type_val : ld (ix+C_HP),a
    ld (ix+C_ST),E_WALK : ld (ix+C_VIS),1 : ld (ix+C_COOL),12
    xor a : jp set_eframe

en_ground:
    ld a,(ix+C_COOL) : or a : jr z,.c0
    dec (ix+C_COOL)
.c0 ld a,(hero+C_ST) : cp ST_DOWN : jp z,en_idle
    ld a,(hero+C_Y) : sub (ix+C_Y) : ld d,a          ; dy
    jp p,.dpos
    neg
.dpos cp 12 : jr nc,.other
    ; same level
    call face_hero
    ld a,(hero+C_X) : sub (ix+C_X) : jr nc,.ap : neg
.ap cp 14 : jr nc,.chase
    ld a,(ix+C_COOL) : or a : jp nz,en_idle
    ld hl,t_windup : call type_val : ld (ix+C_TIMER),a
    ld (ix+C_ST),E_WINDUP
    ld a,3 : jp set_eframe
.chase
    ld a,(hero+C_X) : ld e,a
    jp en_walk_to_safe
.other
    bit 7,d : jr nz,.above
    ; hero below: ladder down here?
    call char_cx : ld b,a : ld a,(ix+C_Y) : call row_of : call get_cell
    cp T_LADDER : jr z,.cdown
    ld c,0 : call find_ladder : jr c,.walkl
    ld a,(hero+C_X) : ld e,a : jp en_walk_to
.cdown ld (ix+C_DX),2
    jr .climb
.above
    call char_cx : ld b,a : ld a,(ix+C_Y) : call row_of : dec c : call get_cell
    cp T_LADDER : jr z,.cup
    ld c,1 : call find_ladder : jr c,.walkl
    ld a,(hero+C_X) : ld e,a : jp en_walk_to_safe
.cup ld (ix+C_DX),-2
.climb
    call snap_ladder
    ld (ix+C_ST),E_CLIMB
    ret
.walkl                  ; E = target X of ladder
    jp en_walk_to_safe

find_ladder:            ; C=1 up / 0 down -> CF + E = target X of nearest ladder
    ld a,(ix+C_Y) : call row_of
    ld a,c : or a : jr z,.d1
    dec c
.d1 ld d,#ff            ; best distance
    ld b,0
.l  call get_cell : cp T_LADDER : jr nz,.n
    push bc : call char_cx : pop bc
    sub b : jr nc,.p : neg
.p  cp d : jr nc,.n
    ld d,a
    ld a,b : add a,a : add a,a : add a,a : sub 4 : jr nc,.q : xor a
.q  ld e,a
.n  inc b : ld a,b : cp 20 : jr c,.l
    ld a,d : cp #ff
    ret

face_hero:
    ld a,(hero+C_X) : cp (ix+C_X) : ld a,0 : jr nc,.r : inc a
.r  ld (ix+C_DIR),a
    ret

en_walk_to_safe:         ; E = target X ; won't walk off ledges
    ld c,1
    jr en_walk_go
en_walk_to:
    ld c,0
en_walk_go:
    ld a,e : sub (ix+C_X) : jr z,en_idle
    jr nc,.r
    cp -2 : jr nc,en_idle_snap
    ld (ix+C_DIR),1
    ld hl,t_speed : call type_val : neg
    jr .mv
.r  cp 2 : jr c,en_idle_snap
    ld (ix+C_DIR),0
    ld hl,t_speed : call type_val
.mv ld b,a
    ld a,c : or a : jr z,.go
    ; ledge check at new position
    push bc
    ld a,(ix+C_X) : add a,b : add a,8 : bit 7,b : jr nz,.lf
    add a,4 : jr .ck
.lf sub 4
.ck call row_of : ld b,c
    ld a,(ix+C_Y) : call row_of : call standable
    pop bc
    jr nc,en_idle
.go ld a,b : call enemy_move : jr c,en_idle
    ld a,(ix+C_ANIM) : rrca : rrca : and 1 : inc a
    jp set_eframe
en_idle_snap:
en_idle:
    xor a : jp set_eframe

enemy_move:             ; A = dx -> CF blocked
    ld b,a : ld a,(ix+C_X) : add a,b
    bit 7,b : jr z,.r
    jr nc,.blk
    jr .t
.r  cp 145 : jr nc,.blk
.t  ld e,a : call walk_try : ret c
    ld (ix+C_X),e
    or a
    ret
.blk scf
    ret

en_climb:
    ld a,(ix+C_Y) : and 7 : jr nz,.mv
    ; at a cell boundary: stop if level with hero, or ladder ends
    ld a,(hero+C_Y) : sub (ix+C_Y) : jp p,.p : neg
.p  cp 12 : jr nc,.cont
    call on_ground : jr c,.off
.cont
    call char_cx : ld b,a : ld a,(ix+C_Y) : call row_of
    bit 7,(ix+C_DX) : jr z,.dn
    dec c : call get_cell : cp T_LADDER : jr z,.mv
    jr .off
.dn call get_cell : cp T_LADDER : jr z,.mv
.off ld (ix+C_ST),E_WALK : ld (ix+C_COOL),4
    ret
.mv ld a,(ix+C_Y) : add a,(ix+C_DX) : ld (ix+C_Y),a
    cp TOP_Y : jp c,en_vanish
    cp 201 : jp nc,en_vanish
    ld a,(ix+C_ANIM) : rrca : and 1 : inc a
    jp set_eframe

en_windup:
    call face_hero
    dec (ix+C_TIMER) : ret nz
    ld (ix+C_ST),E_ATTACK : ld (ix+C_TIMER),5
    ld a,4 : call set_eframe
    ld hl,sfx_swish : call play_sfx
    ; does the blow land?
    ld a,(hero+C_Y) : sub (ix+C_Y) : jp p,.p : neg
.p  cp 16 : ret nc
    ld hl,t_reach : call type_val : ld c,a
    ld a,(hero+C_X) : sub (ix+C_X) : jr nc,.q : neg
.q  cp c : ret nc
    jp hero_hurt

en_attack:
    dec (ix+C_TIMER) : ret nz
    ld (ix+C_ST),E_WALK
    ld hl,t_cool : call type_val : ld (ix+C_COOL),a
    xor a : jp set_eframe

en_hurt:
    ld a,3 : call set_eframe
    ld a,(ix+C_TIMER) : cp 3 : jr c,.nk
    ld a,(ix+C_DX) : call enemy_move
.nk dec (ix+C_TIMER) : ret nz
    ld (ix+C_ST),E_WALK : ld (ix+C_COOL),8
    ret

en_ko:
    ld a,5 : call set_eframe
    ld a,(ix+C_Y) : and 7 : jr z,.g
    call on_ground : jr c,.g
    ld a,(ix+C_Y) : add a,2 : ld (ix+C_Y),a
.g  ld a,(ix+C_TIMER) : cp 20 : jr nc,.v
    and 2 : ld (ix+C_VIS),a
.v  dec (ix+C_TIMER) : ret nz
    ld a,(ix+C_TYPE) : cp 3 : jr nz,.r
    ld a,2 : ld (game_state),a
    ret
.r  ld (ix+C_ST),E_INACTIVE : ld (ix+C_VIS),0 : ld (ix+C_TIMER),125
    ret

; ---------------------------------------------------------------- screens
wait_fire:
.r  ld a,(keys) : and I_FIRE : jr nz,.r
.p  ld a,(keys) : and I_FIRE : jr z,.p
    ret

show_screen:            ; A=page HL=bitmap ; then bank 1 paged
    push hl : push af
    call blackout
    pop af : call page_in
    pop hl : ld de,#c000 : call dzx0
    ld a,1 : jp page_in

title:
    ld a,bmp_page_title : ld hl,bmp_title : call show_screen
    ld hl,title_pal : ld de,pal_ram : ld bc,32 : ldir
    ld hl,title_grad : ld de,grad_new : ld bc,50 : ldir
    ld a,14 : ld c,1 : call set_colours
    ld hl,txt_t1 : ld de,#0094 : call print_str
    ld a,2 : ld c,1 : call set_colours
    ld hl,txt_t2 : ld de,#00a6 : call print_str
    ld hl,txt_t3 : ld de,#00b0 : call print_str
    ld a,4 : ld c,1 : call set_colours
    ld hl,txt_t4 : ld de,#05bc : call print_str
    call asic_on
    call palette_on
    call wait_fire
    ld hl,sfx_start : call play_sfx

new_game:
    ld a,5 : ld (lives),a
    ld hl,score : ld b,9
.z  ld (hl),0 : inc hl : djnz .z          ; score, lcount, lgot, gate_closed
    xor a : ld (game_state),a : ld (inp),a : ld (inp_old),a
    ld ix,hero : push ix : pop hl : ld b,20
.h  ld (hl),0 : inc hl : djnz .h
    ld (ix+C_X),8 : ld (ix+C_Y),184 : ld (ix+C_VIS),1
    xor a : call load_room
    call set_entry

game_loop:
    call wait_frame
    ld a,(inp) : ld (inp_old),a
    ld a,(keys) : ld (inp),a
    call hero_update
    ld ix,en0 : call enemy_update
    ld ix,en1 : call enemy_update
    call lamp_check
    ld ix,hero : call char_draw
    ld ix,en0 : call char_draw
    ld ix,en1 : call char_draw
    call spark_update
    ld a,(hud_dirty) : or a : call nz,hud_refresh
    ld a,(next_room) : cp #ff : jr z,.nr
    call load_room
    call set_entry
.nr ld a,(game_state) : or a : jr z,game_loop
    cp 1 : jr z,game_over

game_win:
    call hide_all
    ld a,1 : call page_in
    ld a,4 : ld c,1 : call set_colours
    ld hl,txt_win1 : ld de,#0050 : call print_str
    ld a,2 : ld c,1 : call set_colours
    ld hl,txt_win2 : ld de,#0060 : call print_str
    jr end_score
game_over:
    ld b,40
.w  push bc : call wait_frame : pop bc : djnz .w
    call hide_all
    ld a,1 : call page_in
    ld a,3 : ld c,1 : call set_colours
    ld hl,txt_over : ld de,#0558 : call print_str
end_score:
    ld a,2 : ld c,1 : call set_colours
    ld hl,txt_score : ld de,#0370 : call print_str
    ld a,(score) : call print_bcd
    ld a,(score+1) : call print_bcd
    ld a,(score+2) : call print_bcd
    call asic_on
    ld b,50
.w  push bc : call wait_frame : pop bc : djnz .w
    call wait_fire
    jp title

txt_t1:    db "COLLECT THE LANTERNS",0
txt_t2:    db "KEYS QAOP OR CURSORS",0
txt_t3:    db "SPACE OR FIRE  HIT  ",0
txt_t4:    db "PRESS FIRE",0
txt_win1:  db "BRUM IS SAFE AGAIN! ",0
txt_win2:  db "THE GAFFER IS DONE. ",0
txt_over:  db "GAME OVER!",0
txt_score: db "SCORE ",0

code_end:
    assert code_end < #3fff

; ---------------------------------------------------------------- data banks
bank 1
org #4000
    include "../build/data.asm"
data_end:
    assert data_end <= #8000

bank 2
org #4000
    incbin "../build/frames.bin"

    include "../build/bitmaps.asm"
