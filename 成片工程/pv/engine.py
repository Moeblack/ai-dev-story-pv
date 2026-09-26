"""开罗风 PV 渲染引擎：480x270 世界层（4x 最近邻）+ 960x540 UI 层（2x 最近邻）。"""
from __future__ import annotations
import json, math, os, random
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, '资产')
FPS = 30
W, H = 480, 270          # 世界层原生像素
UW, UH = 960, 540        # UI 层
OW, OH = 1920, 1080      # 输出

FONT_PATH = os.path.join(A, '字体', 'fusion-pixel-12px-proportional-zh_hans.ttf')
FONT = ImageFont.truetype(FONT_PATH, 12)

# ---------------- 配色（取自风格指南实测） ----------------
C_BG = (248, 247, 253)
C_BORDER = (140, 146, 158)
C_INNER = (214, 234, 234)
C_BAND = (186, 207, 214)
C_TEXT = (84, 88, 100)
C_SUB = (138, 138, 146)
C_ACC = (98, 118, 214)       # 强调蓝紫（加深以保证可读）
C_RED = (196, 72, 56)
C_GREEN = (64, 168, 88)
C_GOLD = (236, 184, 40)
C_DARK = (73, 79, 89)
C_CYAN = (138, 220, 231)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# ---------------- 节拍 ----------------
_audio = json.load(open(os.path.join(ROOT, '分析', 'audio.json')))
BEATS = np.array(_audio['beats'])

def beat_pulse(t: float, width: float = 0.12) -> float:
    """最近一拍后的衰减脉冲 0..1。"""
    i = np.searchsorted(BEATS, t) - 1
    if i < 0:
        return 0.0
    dt = t - BEATS[i]
    return max(0.0, 1.0 - dt / width) if dt < width else 0.0

def beat_index(t: float) -> int:
    return int(np.searchsorted(BEATS, t))

# ---------------- 缓动 ----------------
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x

def prog(t, t0, dur):
    return clamp((t - t0) / dur) if dur > 0 else (1.0 if t >= t0 else 0.0)

def ease_out(p):
    return 1 - (1 - p) ** 3

def ease_in_out(p):
    return 3 * p * p - 2 * p * p * p

def back_out(p, s=1.8):
    p -= 1
    return p * p * ((s + 1) * p + s) + 1

def lerp(a, b, p):
    return a + (b - a) * p

# ---------------- 资源 ----------------
@lru_cache(None)
def bg(name: str) -> Image.Image:
    return Image.open(os.path.join(A, '底图480', name + '.png')).convert('RGB')

@lru_cache(None)
def _raw(kind: str, name: str) -> Image.Image:
    return Image.open(os.path.join(A, kind, name + '.png')).convert('RGBA')

@lru_cache(None)
def sprite(name: str, h: int, kind: str = '精灵', flip: bool = False) -> Image.Image:
    im = _raw(kind, name)
    w = max(1, round(im.width * h / im.height))
    small = im.resize((w, h), Image.BOX)
    arr = np.array(small)
    arr[:, :, 3] = np.where(arr[:, :, 3] > 120, 255, 0)
    out = Image.fromarray(arr)
    if flip:
        out = out.transpose(Image.FLIP_LEFT_RIGHT)
    return out

def icon(name: str, h: int) -> Image.Image:
    return sprite(name, h, '图标')

def portrait(i: int, h: int) -> Image.Image:
    return sprite(f'p{i}', h, '头像')

# ---------------- 文字 ----------------
@lru_cache(4096)
def text(s: str, color=C_TEXT, scale: int = 1, outline=None, shadow=None) -> Image.Image:
    bb = FONT.getbbox(s)
    w = max(1, bb[2]) + 4
    h = 16
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.fontmode = '1'
    if shadow:
        d.text((3, 2), s, font=FONT, fill=shadow)
    if outline:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx or dy:
                    d.text((2 + dx, 1 + dy), s, font=FONT, fill=outline)
    d.text((2, 1), s, font=FONT, fill=color)
    if scale > 1:
        im = im.resize((w * scale, h * scale), Image.NEAREST)
    return im

def paste(dst: Image.Image, im: Image.Image, x: float, y: float, anchor: str = 'lt', alpha: float = 1.0):
    x, y = int(round(x)), int(round(y))
    if anchor[0] == 'm':
        x -= im.width // 2
    elif anchor[0] == 'r':
        x -= im.width
    if anchor[1] == 'm':
        y -= im.height // 2
    elif anchor[1] == 'b':
        y -= im.height
    if alpha < 1.0:
        im = im.copy()
        a = np.array(im)
        a[:, :, 3] = (a[:, :, 3] * clamp(alpha)).astype(np.uint8)
        im = Image.fromarray(a)
    dst.alpha_composite(im, (x, y)) if 0 <= x and 0 <= y and x + im.width <= dst.width and y + im.height <= dst.height else _paste_clip(dst, im, x, y)

def _paste_clip(dst, im, x, y):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(dst.width, x + im.width), min(dst.height, y + im.height)
    if x1 <= x0 or y1 <= y0:
        return
    crop = im.crop((x0 - x, y0 - y, x1 - x, y1 - y))
    dst.alpha_composite(crop, (x0, y0))

def scaled(im: Image.Image, s: float) -> Image.Image:
    if abs(s - 1) < 1e-3:
        return im
    w, h = max(1, round(im.width * s)), max(1, round(im.height * s))
    return im.resize((w, h), Image.NEAREST)

def pop(dst, im, x, y, t, t0, dur=0.22, anchor='mm', t_out=None, out_dur=0.15):
    """弹出（回弹放大）+ 可选收回。"""
    if t < t0:
        return
    p = prog(t, t0, dur)
    s = back_out(p) if p < 1 else 1.0
    if t_out is not None and t >= t_out:
        q = prog(t, t_out, out_dur)
        if q >= 1:
            return
        s *= (1 - q)
    if s <= 0.02:
        return
    paste(dst, scaled(im, s), x, y, anchor)

def typewriter(s: str, t: float, t0: float, cps: float = 14) -> str:
    n = int(max(0, (t - t0) * cps))
    return s[:n]

# ---------------- 窗口 / 控件 ----------------
def rounded(d: ImageDraw.ImageDraw, box, fill, outline=None, r=3):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline)

def window(dst, x, y, w, h, t, t0, title=None, draw=None, dark=False, t_out=None,
           band=None, border=None, open_dur=0.16):
    """开罗式蓝银窗口：纵向展开/收起动画；draw(d, panel) 在面板坐标内绘制内容。"""
    if t < t0:
        return
    p = ease_out(prog(t, t0, open_dur))
    if t_out is not None and t >= t_out:
        q = prog(t, t_out, 0.12)
        if q >= 1:
            return
        p *= 1 - q
    panel = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(panel)
    d.fontmode = '1'
    bgc = C_DARK if dark else C_BG
    bor = border or ((34, 38, 46) if dark else C_BORDER)
    rounded(d, (0, 0, w - 1, h - 1), fill=bgc, outline=bor, r=5)
    d.rounded_rectangle((2, 2, w - 3, h - 3), radius=4, outline=(96, 104, 116) if dark else C_INNER)
    if title is not None:
        bc = band or (C_CYAN if dark else C_BAND)
        d.rounded_rectangle((4, 4, w - 5, 21), radius=3, fill=bc)
        tc = (30, 40, 52) if dark else (60, 70, 84)
        panel.alpha_composite(text(title, tc), (8, 5))
    if draw is not None:
        draw(d, panel)
    hh = max(2, int(h * p))
    if hh != h:
        panel = panel.resize((w, hh), Image.NEAREST)
    sh = Image.new('RGBA', (w, hh), (20, 20, 40, 70))
    paste(dst, sh, x + 4, y + (h - hh) // 2 + 4)
    paste(dst, panel, x, y + (h - hh) // 2)

def button(panel, x, y, w, h, label, pressed=False, hot=False, color=None):
    d = ImageDraw.Draw(panel)
    base = color or (236, 240, 248)
    if hot:
        base = (255, 236, 150)
    if pressed:
        base = tuple(max(0, c - 40) for c in base)
    d.rounded_rectangle((x, y, x + w, y + h), radius=4, fill=(120, 126, 140))
    oy = 1 if pressed else 0
    d.rounded_rectangle((x, y + oy, x + w, y + h - 2 + oy), radius=4, fill=base, outline=(120, 126, 140))
    tim = text(label, C_TEXT)
    panel.alpha_composite(tim, (x + (w - tim.width) // 2 + 1, y + (h - 14) // 2 + oy))

def bar(panel, x, y, w, h, p, color=C_ACC, back=(222, 226, 236)):
    d = ImageDraw.Draw(panel)
    d.rectangle((x, y, x + w, y + h), fill=back, outline=(150, 156, 170))
    fw = int((w - 2) * clamp(p))
    if fw > 0:
        d.rectangle((x + 1, y + 1, x + fw, y + h - 1), fill=color)
        d.line((x + 1, y + 1, x + fw, y + 1), fill=tuple(min(255, c + 50) for c in color))

# 像素手套光标（开罗风）
_HAND = [
    "....XX......",
    "...XWWX.....",
    "...XWWX.....",
    "...XWWXXX...",
    "...XWWXWWXX.",
    ".XXXWWXWWXWX",
    "XWWXWWWWWWWX",
    "XWWWWWWWWWWX",
    ".XWWWWWWWWWX",
    "..XWWWWWWWX.",
    "...XWWWWWX..",
    "...XXXXXXX..",
]
@lru_cache(None)
def hand_cursor(scale=2):
    im = Image.new('RGBA', (12, 12), (0, 0, 0, 0))
    px = im.load()
    for yy, row in enumerate(_HAND):
        for xx, c in enumerate(row):
            if c == 'X':
                px[xx, yy] = (40, 40, 60, 255)
            elif c == 'W':
                px[xx, yy] = (255, 255, 255, 255)
    return im.resize((12 * scale, 12 * scale), Image.NEAREST)

def cursor(dst, t, path, click_times=()):
    """path: [(t, x, y), ...] 线性插值；click 时按下缩小。"""
    if t < path[0][0]:
        return
    for (ta, xa, ya), (tb, xb, yb) in zip(path, path[1:]):
        if ta <= t <= tb:
            p = ease_in_out(prog(t, ta, tb - ta))
            x, y = lerp(xa, xb, p), lerp(ya, yb, p)
            break
    else:
        _, x, y = path[-1]
    im = hand_cursor(2)
    for ct in click_times:
        if 0 <= t - ct < 0.12:
            im = hand_cursor(2).resize((20, 20), Image.NEAREST)
    paste(dst, im, x - 6, y - 2)

def fmt_num(n: float) -> str:
    return f"{int(round(n)):,}"

def count(t, t0, dur, a, b):
    return lerp(a, b, ease_out(prog(t, t0, dur)))

# ---------------- 粒子（无状态，可并行） ----------------
CONFETTI_COLORS = [(236, 88, 96), (252, 196, 64), (96, 196, 120), (88, 156, 236), (200, 120, 232), (255, 255, 255)]

def confetti(dst_world, t, t0, n=90, seed=1, area=(0, 0, W, H), dur=6.0):
    if t < t0 or t > t0 + dur:
        return
    d = ImageDraw.Draw(dst_world)
    rng = random.Random(seed)
    x0, y0, x1, y1 = area
    lt = t - t0
    for i in range(n):
        sx = rng.uniform(x0, x1)
        delay = rng.uniform(0, 1.5)
        vy = rng.uniform(18, 40)
        sway = rng.uniform(2, 8)
        ph = rng.uniform(0, 6.28)
        col = rng.choice(CONFETTI_COLORS)
        tt = lt - delay
        if tt < 0:
            continue
        y = y0 - 10 + vy * tt
        if y > y1:
            continue
        x = sx + math.sin(tt * 3 + ph) * sway
        w = 2 if int(tt * 8 + i) % 2 else 1
        d.rectangle((int(x), int(y), int(x) + w, int(y) + 1), fill=col)

def falling_icons(dst, t, t0, name, n=18, seed=2, size=16, area=(0, 0, UW, UH), dur=5.0, speed=(60, 120), spin=False):
    if t < t0 or t > t0 + dur:
        return
    rng = random.Random(seed)
    x0, y0, x1, y1 = area
    ic = icon(name, size)
    for i in range(n):
        sx = rng.uniform(x0, x1)
        delay = rng.uniform(0, dur * 0.6)
        vy = rng.uniform(*speed)
        tt = t - t0 - delay
        if tt < 0:
            continue
        y = y0 - size + vy * tt
        if y > y1:
            continue
        paste(dst, ic, sx + math.sin(tt * 4 + i) * 6, y, 'mm')

def rising_icons(dst, t, t0, names, n=16, seed=3, size=14, area=(0, 0, UW, UH), dur=6.0, speed=(30, 60)):
    if t < t0 or t > t0 + dur:
        return
    rng = random.Random(seed)
    x0, y0, x1, y1 = area
    for i in range(n):
        nm = names[i % len(names)]
        sx = rng.uniform(x0, x1)
        delay = rng.uniform(0, dur * 0.8)
        vy = rng.uniform(*speed)
        life = rng.uniform(1.2, 2.2)
        tt = (t - t0 - delay)
        if tt < 0:
            continue
        tt = tt % (life + 0.4)
        if tt > life:
            continue
        y = y1 - vy * tt
        a = 1.0 - (tt / life) ** 2
        paste(dst, icon(nm, size), sx + math.sin(tt * 5 + i) * 5, y, 'mm', alpha=a)

def twinkle(dst_world, t, seed=5, n=40, area=(0, 0, W, 100)):
    d = ImageDraw.Draw(dst_world)
    rng = random.Random(seed)
    x0, y0, x1, y1 = area
    for i in range(n):
        x, y = rng.randint(x0, x1), rng.randint(y0, y1)
        ph = rng.uniform(0, 6.28)
        sp = rng.uniform(2, 5)
        v = (math.sin(t * sp + ph) + 1) / 2
        if v > 0.7:
            d.point((x, y), fill=(255, 255, 230))
            if v > 0.9:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    d.point((x + dx, y + dy), fill=(200, 210, 255))

# ---------------- 相机与合成 ----------------
def camera(world: Image.Image, zoom=1.0, cx=W / 2, cy=H / 2) -> Image.Image:
    cw, ch = W / zoom, H / zoom
    x0 = clamp(cx - cw / 2, 0, W - cw)
    y0 = clamp(cy - ch / 2, 0, H - ch)
    box = (int(round(x0)), int(round(y0)), int(round(x0 + cw)), int(round(y0 + ch)))
    return world.crop(box).resize((OW, OH), Image.NEAREST)

def darken(img: Image.Image, k: float) -> Image.Image:
    if k <= 0:
        return img
    ov = Image.new(img.mode, img.size, (0, 0, 0) if img.mode == 'RGB' else (0, 0, 0, 255))
    return Image.blend(img, ov, clamp(k))

def tint(img: Image.Image, color, k: float) -> Image.Image:
    ov = Image.new('RGB', img.size, color)
    return Image.blend(img, ov, clamp(k))

def shake_offset(t, t0, dur, amp, seed=9):
    if not (t0 <= t < t0 + dur):
        return 0, 0
    k = 1 - (t - t0) / dur
    rng = random.Random(int(t * FPS) * 7 + seed)
    return int(rng.uniform(-amp, amp) * k) * 4, int(rng.uniform(-amp, amp) * k) * 4

def light_beam(dst_world, apex, angle, length, spread, color, alpha):
    """舞台光束（半透明三角形）。"""
    ov = Image.new('RGBA', dst_world.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    ax, ay = apex
    a1, a2 = angle - spread, angle + spread
    p1 = (ax + math.cos(a1) * length, ay + math.sin(a1) * length)
    p2 = (ax + math.cos(a2) * length, ay + math.sin(a2) * length)
    d.polygon([apex, p1, p2], fill=color + (alpha,))
    base = dst_world.convert('RGBA')
    base.alpha_composite(ov)
    return base.convert('RGB')
