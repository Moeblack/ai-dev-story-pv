"""B 站封面：底图 C_封面.png + 标题文字。输出 16:10(1920x1200) 与 16:9(1920x1080) 两版。"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTD = os.path.join(os.path.dirname(ROOT), '成片')
BLACK_F = '/usr/share/fonts/noto-cjk/NotoSansCJK-Black.ttc'
PIX_F = os.path.join(ROOT, '资产', '字体', 'fusion-pixel-12px-proportional-zh_hans.ttf')

def stroke_text(img, xy, s, font, fill, stroke, sw, shadow=None, anchor='la', angle=0):
    d0 = ImageDraw.Draw(img)
    bb = d0.textbbox((0, 0), s, font=font, stroke_width=sw, anchor='lt')
    w, h = bb[2] - bb[0] + sw * 4 + 30, bb[3] - bb[1] + sw * 4 + 30
    layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ox, oy = sw * 2 + 10 - bb[0], sw * 2 + 10 - bb[1]
    if shadow:
        d.text((ox + 10, oy + 12), s, font=font, fill=shadow, stroke_width=sw, stroke_fill=shadow, anchor='lt')
    d.text((ox, oy), s, font=font, fill=fill, stroke_width=sw, stroke_fill=stroke, anchor='lt')
    if angle:
        layer = layer.rotate(angle, resample=Image.BICUBIC, expand=True)
    x, y = xy
    if anchor[0] == 'm':
        x -= layer.width // 2
    elif anchor[0] == 'r':
        x -= layer.width
    if anchor[1] == 'm':
        y -= layer.height // 2
    elif anchor[1] == 'b':
        y -= layer.height
    img.alpha_composite(layer, (int(x), int(y)))

def pixel_text(s, px, fill, outline, ow=2):
    """像素字：12px 字形按 px 倍放大（最近邻），外加像素描边。"""
    f = ImageFont.truetype(PIX_F, 12)
    bb = f.getbbox(s)
    w, h = bb[2] + 2 * ow + 2, 16 + 2 * ow
    base = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(base)
    d.fontmode = '1'
    for dx in range(-ow, ow + 1):
        for dy in range(-ow, ow + 1):
            if dx or dy:
                d.text((ow + 1 + dx, ow + dy), s, font=f, fill=outline)
    d.text((ow + 1, ow), s, font=f, fill=fill)
    return base.resize((w * px, h * px), Image.NEAREST)

def build(W, H, shift=0):
    src = Image.open(os.path.join(ROOT, '底图', 'C_封面.png')).convert('RGB')
    k = max(W / src.width, H / src.height)
    big = src.resize((round(src.width * k), round(src.height * k)), Image.LANCZOS)
    x0 = min(big.width - W, round(shift * k))
    y0 = (big.height - H) // 2
    img = big.crop((x0, y0, x0 + W, y0 + H)).convert('RGBA')

    # 底部暗条，托住主标题
    grad = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    top = H - 330
    for y in range(top, H):
        a = int(235 * min(1, (y - top) / 170))
        gd.line((0, y, W, y), fill=(8, 10, 30, a))
    img.alpha_composite(grad)

    fb = lambda s: ImageFont.truetype(BLACK_F, s, index=2)   # SC Black
    # 冲击字：震惊！ 瘫坐！
    stroke_text(img, (40, 40), '震惊！', fb(210), (255, 232, 40), (20, 10, 10), 14,
                shadow=(0, 0, 0, 170), angle=6)
    stroke_text(img, (min(860, W - 700), 150), '瘫坐！', fb(190), (255, 255, 255), (200, 30, 30), 14,
                shadow=(0, 0, 0, 170), angle=-5)

    # 主标题：像素字
    t1 = pixel_text('《AI发展国》PV', 11, (255, 255, 255), (30, 40, 110), 1)
    img.alpha_composite(t1, (60, H - t1.height - 40))

    # 右上角徽章：Opus 5.5 制作
    badge_font = fb(64)
    s = 'Claude Opus 5.5 制作'
    d = ImageDraw.Draw(img)
    bb = d.textbbox((0, 0), s, font=badge_font)
    bw, bh = bb[2] - bb[0] + 70, bb[3] - bb[1] + 44
    badge = Image.new('RGBA', (bw, bh), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    bd.rounded_rectangle((0, 0, bw - 1, bh - 1), radius=22, fill=(217, 119, 87, 255), outline=(255, 255, 255), width=6)
    bd.text((35 - bb[0], 22 - bb[1]), s, font=badge_font, fill=(255, 255, 255))
    badge = badge.rotate(-4, resample=Image.BICUBIC, expand=True)
    img.alpha_composite(badge, (W - badge.width - 40, H - 330 - badge.height + 20))
    return img.convert('RGB')

if __name__ == '__main__':
    os.makedirs(OUTD, exist_ok=True)
    for (w, h), sh, nm in (((1920, 1200), 0, 'B站封面_16x10.png'), ((1920, 1080), 0, 'B站封面_16x9.png'),
                           ((1600, 1200), 40, 'B站封面_4x3.png')):
        build(w, h, sh).save(os.path.join(OUTD, nm))
        print(os.path.join(OUTD, nm))
