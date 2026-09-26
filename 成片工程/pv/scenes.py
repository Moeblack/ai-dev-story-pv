"""《AI发展国》PV 时间轴。BGM：Fly Me to the Moon（小野丽莎），分镜卡在歌词句上。"""
from __future__ import annotations
import math, random
from PIL import Image, ImageDraw
from engine import *

DURATION = 86.5

# 音效事件：(时间, 名称)
SFX: list[tuple[float, str]] = []
def sfx(t, name):
    SFX.append((t, name))

# ================= 通用小部件 =================
def hud(ui, date, money, fans, money_red=False):
    d = ImageDraw.Draw(ui)
    d.rounded_rectangle((6, 4, 953, 27), radius=4, fill=C_BG + (238,), outline=C_BORDER)
    d.rounded_rectangle((8, 6, 951, 25), radius=3, outline=C_INNER)
    paste(ui, text(date, C_TEXT), 14, 8)
    paste(ui, icon('coin', 14), 330, 16, 'mm')
    paste(ui, text('资金', C_SUB), 342, 8)
    paste(ui, text(f'¥{money}', C_RED if money_red else C_ACC), 372, 8)
    paste(ui, icon('heart', 13), 720, 16, 'mm')
    paste(ui, text('粉丝', C_SUB), 732, 8)
    paste(ui, text(fans, C_ACC), 762, 8)

def caption(ui, s, t, t0, t1, y=478, color=WHITE, scale=2):
    if not (t0 <= t < t1):
        return
    im = text(s, color, scale, outline=(24, 24, 40))
    p = ease_out(prog(t, t0, 0.18))
    w, h = im.width + 24, im.height + 8
    box = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle((0, 0, w - 1, h - 1), radius=6, fill=(20, 22, 40, 170))
    box.alpha_composite(im, (12, 4))
    paste(ui, box, UW / 2, y + (1 - p) * 20, 'mm', alpha=p if t < t1 - 0.15 else prog(t1, t, 0.15) * 1.0)

def bubble(ui, x, y, lines, t, t0, t_out=None, tail='down'):
    if t < t0 or (t_out is not None and t >= t_out):
        return
    ims = [text(s, c) for s, c in lines]
    w = max(i.width for i in ims) + 16
    h = 16 * len(ims) + 10
    b = Image.new('RGBA', (w, h + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(b)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=6, fill=WHITE, outline=(60, 60, 80))
    tx = w // 2
    d.polygon([(tx - 5, h - 2), (tx + 5, h - 2), (tx, h + 7)], fill=WHITE, outline=(60, 60, 80))
    d.line((tx - 4, h - 1, tx + 4, h - 1), fill=WHITE)
    for i, im in enumerate(ims):
        b.alpha_composite(im, (8, 5 + 16 * i))
    pop(ui, b, x, y, t, t0, anchor='mb')

def stamp(ui, s, x, y, t, t0, color=C_RED, scale=3, t_out=None):
    if t < t0 or (t_out is not None and t >= t_out):
        return
    im = text(s, color, scale)
    w, h = im.width + 20, im.height + 10
    b = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(b)
    d.rectangle((0, 0, w - 1, h - 1), fill=(255, 250, 240, 235), outline=color, width=3)
    b.alpha_composite(im, (10, 5))
    p = prog(t, t0, 0.14)
    s_ = lerp(2.2, 1.0, ease_out(p))
    paste(ui, scaled(b, s_), x, y, 'mm', alpha=0.4 + 0.6 * p)

def banner(ui, s, x, y, t, t0, t_out, fg=WHITE, ol=(40, 50, 90), ribbon=(214, 76, 76), scale=3):
    if t < t0 or t >= t_out + 0.15:
        return
    im = text(s, fg, scale, outline=ol)
    w, h = im.width + 60, im.height + 14
    b = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(b)
    dark = tuple(max(0, c - 60) for c in ribbon)
    d.polygon([(0, 4), (22, 4), (22, h - 1), (0, h - 1), (10, (h + 4) // 2)], fill=dark)
    d.polygon([(w - 1, 4), (w - 23, 4), (w - 23, h - 1), (w - 1, h - 1), (w - 11, (h + 4) // 2)], fill=dark)
    d.rectangle((12, 0, w - 13, h - 5), fill=ribbon, outline=dark)
    d.line((14, 2, w - 15, 2), fill=tuple(min(255, c + 50) for c in ribbon))
    b.alpha_composite(im, (30, 5))
    pop(ui, b, x, y, t, t0, dur=0.25, t_out=t_out)

def number_pop(ui, s, x, y, t, t0, color=C_GREEN, life=0.9, ic=None):
    lt = t - t0
    if lt < 0 or lt > life:
        return
    a = 1.0 if lt < life * 0.6 else 1 - (lt - life * 0.6) / (life * 0.4)
    yy = y - 26 * ease_out(clamp(lt / life))
    im = text(s, color, 1, outline=WHITE)
    if ic:
        row = Image.new('RGBA', (im.width + 16, 16), (0, 0, 0, 0))
        row.alpha_composite(icon(ic, 14), (0, 1))
        row.alpha_composite(im, (15, 0))
        im = row
    paste(ui, im, x, yy, 'mb', alpha=a)

def w2u(wx, wy, zoom=1.0, cx=W / 2, cy=H / 2):
    cw, ch = W / zoom, H / zoom
    x0 = clamp(cx - cw / 2, 0, W - cw)
    y0 = clamp(cy - ch / 2, 0, H - ch)
    k = 2 * zoom
    return (wx - x0) * k, (wy - y0) * k

def shock_lines(ui, x, y, t, t0, r=26):
    lt = t - t0
    if not (0 <= lt < 0.6):
        return
    d = ImageDraw.Draw(ui)
    rr = r + lt * 30
    for i in range(8):
        a = i * math.pi / 4 + 0.3
        d.line((x + math.cos(a) * rr, y + math.sin(a) * rr, x + math.cos(a) * (rr + 10), y + math.sin(a) * (rr + 10)),
               fill=(40, 40, 60), width=2)

# ================= 分镜 =================
# 音效登记（与画面同一处维护）
for _t, _n in [
    (5.4, 'open'), (8.2, 'confirm'), (8.6, 'fanfare'), (10.2, 'open'),
    (12.44, 'open'), (12.9, 'blip'), (13.4, 'blip'), (13.9, 'blip'), (15.1, 'click'), (15.7, 'alarm'),
    (16.9, 'blip'), (17.4, 'confirm'), (18.0, 'hire'), (18.1, 'coin_down'),
    (20.6, 'alarm'), (21.5, 'open'), (22.6, 'pop'), (23.8, 'pop'),
    (25.2, 'whoosh'), (25.4, 'fanfare_small'), (26.4, 'blip'),
    (29.0, 'open'), (31.9, 'blip'), (32.1, 'error'), (34.0, 'fanfare'),
    (36.0, 'open'), (36.9, 'coin'), (37.9, 'coin'), (38.9, 'coin'), (39.8, 'coin_big'), (38.2, 'pop'),
    (40.7, 'alarm'), (41.8, 'open'), (42.5, 'confirm'), (42.7, 'coin_down'), (43.1, 'stamp'),
    (44.5, 'beep'), (44.97, 'beep'), (45.42, 'beep'), (45.8, 'click'), (45.88, 'launch'), (45.95, 'cheer'),
    (46.1, 'fanfare'),
    (54.24, 'boom'), (54.6, 'thud'), (56.3, 'sad'), (57.0, 'pop'), (57.9, 'pop'), (58.8, 'pop'), (59.7, 'pop'),
    (62.0, 'open'), (63.4, 'whoosh_up'), (64.0, 'fanfare_small'), (65.6, 'open'), (66.6, 'stamp'),
    (69.2, 'fanfare'), (69.25, 'cheer'), (70.4, 'open'),
    (77.1, 'fanfare_big'), (81.2, 'blip'), (82.6, 'thud'), (84.0, 'confirm'),
]:
    sfx(_t, _n)
for _k in range(6):
    sfx(5.9 + _k * 0.31, 'type')
for _k in range(12):
    sfx(29.3 + _k * 0.42, 'pop_small')

HIRE_ROWS = [
    (1, '天才少年 · 小林', 5, '研究 99  代码 99  睡眠 3', '¥1亿'),
    (2, '首席科学家 · 老王', 4, '论文 999 篇  引用 十万+', 'GPU×1万'),
    (3, '调参侠 · 阿强', 3, '调参 88  发际线 危', '¥30万'),
]
BOARD = [('GPT-6.5', 'ClosedAI', 1402), ('浅度求索 R3', '浅度求索', 1402), ('Genimi 4 Ultra', '谷咕', 1402),
         ('Clod Opus 6', '人择', 1399), ('通义万问 4', '阿狸', 1396)]
TICKER = ('【快讯】硅谷迎来 Sputnik 时刻　｜　某大厂连夜拉响 Code Red　｜　分析师：这不可能　｜　'
          '显卡股：我先跌为敬　｜　网友：这周第几个王炸了？　｜　')

def render_frame(t: float) -> Image.Image:
    ui = Image.new('RGBA', (UW, UH), (0, 0, 0, 0))
    zoom, cx, cy = 1.0, W / 2, H / 2
    flash = 0.0
    fade = 0.0
    shake = (0, 0)

    # ---------- S0 月夜开场 0–4.81 ----------
    if t < 4.81:
        world = bg('P0_月夜').copy()
        twinkle(world, t, n=60, area=(0, 0, W, 120))
        zoom, cx = 1.5, W / 2
        cy = lerp(185, 95, ease_in_out(prog(t, 0, 4.8)))
        fade = 1 - prog(t, 0, 1.3)

        def dr(d, p):
            p.alpha_composite(text(typewriter('这是一个 AI 公司多如繁星的时代——', t, 1.0, 16), C_TEXT, 2), (16, 10))
            p.alpha_composite(text(typewriter('而你，决定也开一家。', t, 2.9, 12), C_ACC, 2), (16, 44))
        window(ui, 150, 400, 660, 84, t, 0.8, draw=dr, t_out=4.62)

    # ---------- S1 成立公司 4.81–12.44 ----------
    elif t < 12.44:
        world = bg('P1_空办公室').copy()
        p = ease_in_out(prog(t, 4.81, 1.8))
        zoom = lerp(1.6, 1.0, p)
        cx, cy = lerp(110, 240, p), lerp(130, 135, p)
        confetti(world, t, 8.6, n=110, seed=11)

        def dr(d, pn):
            pn.alpha_composite(text('请为你的公司命名：', C_TEXT), (16, 32))
            d.rectangle((16, 56, 444, 92), fill=WHITE, outline=C_BORDER)
            name = typewriter('月之亮面科技', t, 5.9, 1 / 0.31)
            ti = text(name, C_ACC, 2)
            pn.alpha_composite(ti, (22, 60))
            if int(t * 3) % 2 == 0:
                d.rectangle((22 + ti.width, 62, 24 + ti.width, 88), fill=C_ACC)
            button(pn, 180, 118, 100, 28, '确定', pressed=8.2 <= t < 8.4, hot=t > 7.9)
        window(ui, 250, 160, 460, 162, t, 5.4, title='成立新公司', draw=dr, t_out=8.5)
        cursor(ui, t, [(7.4, 760, 460), (8.1, 480, 292)], click_times=(8.2,))
        if 7.4 <= t < 8.5:
            pass
        banner(ui, '月之亮面科技 成立！', UW / 2, 210, t, 8.6, 10.05)
        if t >= 8.6:
            hud(ui, '第1年 1月 第1周', '500,000', '0')

        def dr2(d, pn):
            pn.alpha_composite(sprite('founder_cheer', 78), (14, 8))
            pn.alpha_composite(text('创始人', C_SUB), (100, 10))
            pn.alpha_composite(text(typewriter('目标：成为世界最强的 AI 公司！', t, 10.35, 16), C_TEXT, 2), (100, 28))
            pn.alpha_composite(text(typewriter('……先把这四张桌子坐满吧。', t, 11.3, 14), C_SUB), (100, 66))
        window(ui, 150, 400, 660, 100, t, 10.2, draw=dr2, t_out=12.3)

    # ---------- S2 招聘 12.44–20.38 ----------
    elif t < 20.38:
        staffed = t >= 18.0
        world = bg('P2_员工办公室' if staffed else 'P1_空办公室').copy()
        if not staffed:
            world = darken(world, 0.35)
        else:
            confetti(world, t, 18.0, n=60, seed=21, dur=3)
        if 17.95 <= t < 18.1:
            flash = 0.6

        def dr(d, pn):
            for i, (pi, nm, st, stats, fee) in enumerate(HIRE_ROWS):
                t_row = 12.9 + i * 0.5
                if t < t_row:
                    continue
                y = 30 + i * 96
                sel = i == 0 and t >= 15.1
                d.rounded_rectangle((10, y, 609, y + 88), radius=4, fill=(255, 246, 204) if sel else (240, 244, 252),
                                    outline=C_GOLD if sel else C_INNER)
                pn.alpha_composite(portrait(pi, 76), (16, y + 6))
                pn.alpha_composite(text(nm, C_ACC, 2), (100, y + 6))
                for k in range(st):
                    pn.alpha_composite(icon('star', 14), (102 + k * 17, y + 40))
                pn.alpha_composite(text(stats, C_SUB), (100, y + 62))
                pn.alpha_composite(text('签字费', C_SUB), (452, y + 10))
                pn.alpha_composite(text(fee, C_RED, 2), (452, y + 34))
        window(ui, 170, 60, 620, 328, t, 12.44, title='招聘 · 明星研究员　1/1', draw=dr, t_out=17.95)
        cursor(ui, t, [(14.3, 860, 500), (15.0, 560, 140), (15.6, 560, 140), (16.9, 700, 400), (17.3, 385, 320)],
               click_times=(15.1, 17.4))

        def dr_w(d, pn):
            pn.alpha_composite(text('Mega 公司 向「小林」开出：', C_TEXT), (16, 30))
            pn.alpha_composite(text('签字费 $100,000,000', C_RED, 2), (16, 50))
            loyal = lerp(0.8, 0.12, ease_out(prog(t, 15.9, 0.8)))
            jit = int(random.Random(int(t * 30)).uniform(-2, 2)) if 15.9 <= t < 16.9 else 0
            pn.alpha_composite(text('忠诚度', C_SUB), (16 + jit, 90))
            bar(pn, 70 + jit, 92, 360, 10, loyal, color=C_RED if loyal < 0.4 else C_GREEN)
            if t >= 16.9:
                button(pn, 60, 128, 150, 30, '加薪留人', pressed=17.4 <= t < 17.6, hot=True)
                button(pn, 250, 128, 150, 30, '放他走')
        window(ui, 250, 170, 460, 172, t, 15.7, title='【警报】猎头来袭！', draw=dr_w, t_out=17.95,
               band=(240, 150, 130))
        caption(ui, '“传教士终将打败雇佣兵。”——先把钱加上。', t, 17.45, 17.95, y=380, scale=1)
        if t >= 17.0:
            rising_icons(ui, t, 17.0, ['star'], n=22, seed=7, size=14, area=(0, 60, UW, UH), dur=3.4)
        banner(ui, '小林 加入了公司！', UW / 2, 120, t, 18.05, 20.2, ribbon=(90, 150, 220), scale=2)
        if 18.3 <= t < 20.3:
            paste(ui, text('研究力 +99　　资金 -¥100,000,000', C_TEXT, 1, outline=WHITE), UW / 2, 160, 'mt')
        money = 500000 if t < 18.1 else count(t, 18.1, 0.8, 500000, -99500000)
        hud(ui, '第1年 2月 第3周', fmt_num(money), '0', money_red=money < 0)

    # ---------- S3 显卡排队 20.38–25.2 ----------
    elif t < 25.2:
        world = bg('P3_显卡排队').copy()
        p = ease_in_out(prog(t, 20.38, 4.8))
        zoom, cx, cy = 1.5, lerp(110, 330, p), lerp(170, 150, p)

        def dr_a(d, pn):
            im = text('显卡全球缺货！', C_RED, 2)
            pn.alpha_composite(im, ((440 - im.width) // 2, 26))
        window(ui, 260, 40, 440, 64, t, 20.6, title='【算力告急】', draw=dr_a, t_out=25.1, band=(240, 150, 130))

        def dr_b(d, pn):
            pn.alpha_composite(text('排队人数', C_SUB), (12, 28))
            n = count(t, 21.6, 3.0, 1024, 99999)
            pn.alpha_composite(text(fmt_num(n) + ('+' if n > 99990 else ''), C_ACC, 2), (12, 44))
            pn.alpha_composite(text('显卡单价', C_SUB), (12, 78))
            price = count(t, 21.9, 2.4, 250000, 350000)
            pn.alpha_composite(text(f'¥{fmt_num(price)}', C_RED), (72, 78))
            if t > 23.0:
                pn.alpha_composite(text('↗+40%', C_RED), (170, 78))
        window(ui, 690, 124, 250, 106, t, 21.5, title='市场行情', draw=dr_b, t_out=25.1)
        pop(ui, sprite('gpu_hug', 116), 150, 420, t, 22.6, t_out=25.05)
        bubble(ui, 150, 350, [('抢到了！！', C_RED), ('（2027 年交货）', C_SUB)], t, 22.8, t_out=25.05)
        if t >= 23.8:
            sp = sprite('sign_hold', 130).copy()
            ti = text('求 8 卡', (60, 50, 50), 1)
            sp.alpha_composite(ti, ((sp.width - ti.width) // 2, int(sp.height * 0.065)))
            pop(ui, sp, 830, 430, t, 23.8, t_out=25.05)
        hud(ui, '第1年 4月 第1周', '-99,500,000', '0', money_red=True)

    # ---------- S3b 火星机房 25.2–28.88 ----------
    elif t < 28.88:
        world = bg('P3b_火星机房').copy()
        twinkle(world, t, seed=8, n=40, area=(0, 0, W, 60))
        zoom = lerp(1.0, 1.15, prog(t, 25.2, 3.7))
        cx, cy = 240, 140
        if t < 25.4:
            flash = 1 - prog(t, 25.2, 0.2)

        def dr(d, pn):
            im = text('火星机房', C_ACC, 3)
            pn.alpha_composite(im, ((460 - im.width) // 2, 28))
            im2 = text('地球的电网，不够用了。', C_SUB)
            pn.alpha_composite(im2, ((460 - im2.width) // 2, 84))
        window(ui, 250, 50, 460, 110, t, 25.4, title='新设施解锁！', draw=dr, t_out=28.8)

        def dr2(d, pn):
            pn.alpha_composite(text('算力 +10,000 PFLOPS', C_GREEN, 2), (12, 10))
            pn.alpha_composite(text('运费：一艘火箭 / 趟', C_SUB), (12, 44))
            pn.alpha_composite(text('木星分部：筹建中……', C_SUB), (12, 62))
        window(ui, 600, 400, 330, 88, t, 26.4, draw=dr2, t_out=28.8)
        rp = prog(t, 25.3, 2.4)
        if 0 < rp < 1:
            paste(ui, icon('rocket', 40), lerp(-20, 980, rp), lerp(520, 120, rp), 'mm')
        hud(ui, '第1年 5月 第2周', '-99,500,000', '0', money_red=True)

    # ---------- S4 深夜训练 28.88–35.9 ----------
    elif t < 35.9:
        world = bg('P4_深夜训练').copy()
        zoom, cx, cy = 1.0, 240, 135
        pts = [(105, 88), (128, 150), (210, 108), (232, 170), (318, 125), (262, 58)]
        labels = [('+12 智力', C_ACC), ('+8 代码', C_GREEN), ('+30 幻觉', C_RED), ('+5 创意', (200, 120, 40)),
                  ('+15 智力', C_ACC), ('+20 幻觉', C_RED)]
        for k in range(12):
            wx, wy = pts[k % 6]
            s, c = labels[k % 6]
            ux, uy = w2u(wx, wy)
            number_pop(ui, s, ux, uy - 20, t, 29.3 + k * 0.42, color=c, ic='bulb')
        # 思考气泡（越想越大）
        if 30.4 <= t < 32.9:
            g = prog(t, 30.4, 2.3)
            ux, uy = w2u(128, 150)
            bub = Image.new('RGBA', (120, 40), (0, 0, 0, 0))
            dd = ImageDraw.Draw(bub)
            dd.ellipse((0, 0, 119, 39), fill=WHITE, outline=(60, 60, 80))
            ti = text('让我想想……', C_TEXT)
            bub.alpha_composite(ti, ((120 - ti.width) // 2, 12))
            paste(ui, scaled(bub, 1 + g * 0.9), ux, uy - 40, 'mb')
            paste(ui, text('（思考按 token 计费）', C_GOLD, 1, outline=(30, 30, 50)), ux, uy - 36, 'mt')

        def dr(d, pn):
            rows = [('智力', 387, C_ACC), ('代码', 412, C_GREEN), ('创意', 256, (210, 130, 40)), ('幻觉', 999, C_RED)]
            for i, (nm, tgt, c) in enumerate(rows):
                v = count(t, 29.2, 4.6, 0, tgt)
                y = 32 + i * 34
                pn.alpha_composite(text(nm, C_TEXT), (14, y))
                num = text(fmt_num(v), c, 2)
                pn.alpha_composite(num, (326 - num.width, y - 6))
                bar(pn, 56, y + 3, 170, 8, v / 1000, color=c)
            pr = 0.61 * ease_out(prog(t, 29.2, 2.4))
            if t >= 31.9:
                pr = 0.99
            if t >= 34.0:
                pr = 1.0
            pn.alpha_composite(text('训练进度', C_SUB), (14, 176))
            bar(pn, 14, 196, 250, 14, pr, color=C_CYAN if pr < 1 else C_GOLD)
            pn.alpha_composite(text(f'{int(pr * 100)}%', C_ACC, 2), (274, 188))
            if 32.1 <= t < 34.0 and int(t * 4) % 2 == 0:
                pn.alpha_composite(text('再加一点算力，就一点……', C_RED), (14, 220))
        window(ui, 600, 60, 340, 246, t, 29.0, title='模型开发 · 望舒-1', draw=dr, t_out=35.8)
        if t >= 34.0:
            confetti(world, t, 34.0, n=70, seed=41, dur=2)
        banner(ui, '训练完成！', 300, 240, t, 34.0, 35.75, ribbon=(230, 170, 40), ol=(90, 60, 10))
        hud(ui, '第1年 8月 第2周', '-99,500,000', '0', money_red=True)

    # ---------- S5 融资 35.9–40.7 ----------
    elif t < 40.7:
        world = bg('P5_投资人排队').copy()
        zoom, cx, cy = lerp(1.0, 1.1, prog(t, 35.9, 4.8)), 240, 135

        def dr(d, pn):
            pn.alpha_composite(text('投资人正在门口排队……', C_SUB), (16, 28))
            steps = [(36.9, '¥10亿'), (37.9, '¥100亿'), (38.9, '¥1,000亿'), (39.8, '¥10,000亿')]
            cur = None
            for ts, v in steps:
                if t >= ts:
                    cur = (ts, v)
            pn.alpha_composite(text('估值', C_TEXT), (16, 56))
            if cur:
                im = text(cur[1], C_RED, 3)
                s_ = back_out(prog(t, cur[0], 0.2))
                im = scaled(im, max(0.2, s_))
                pn.alpha_composite(im, (60, 46 + (36 - im.height) // 2))
                pn.alpha_composite(icon('rocket', 40), (430, 70 - int(12 * prog(t, 36.9, 3.5) * 3) % 60))
        window(ui, 230, 40, 500, 124, t, 36.0, title='融资事件！', draw=dr, t_out=40.6)
        falling_icons(ui, t, 36.3, 'coin', n=40, seed=51, size=18, dur=4.3, speed=(120, 220))
        falling_icons(ui, t, 36.8, 'moneybag', n=10, seed=52, size=26, dur=3.8, speed=(90, 160))
        pop(ui, sprite('investor_bag', 120), 150, 430, t, 38.2, t_out=40.6)
        bubble(ui, 180, 360, [('求你收下我的钱！', C_TEXT)], t, 38.4, t_out=40.6)
        caption(ui, '半年估值翻倍，再融一轮。', t, 39.0, 40.6)
        money = -99500000 if t < 38.9 else count(t, 38.9, 1.0, -99500000, 5000000000)
        hud(ui, '第2年 1月 第1周', fmt_num(money), '1,024', money_red=money < 0)

    # ---------- S6 价格战 40.7–44.5 ----------
    elif t < 44.5:
        world = darken(bg('P2_员工办公室'), 0.3)

        def dr(d, pn):
            pn.alpha_composite(text('浅度求索 宣布：', C_TEXT), (16, 30))
            pn.alpha_composite(text('API 立即降价 50%！', C_RED, 3), (16, 52))
        window(ui, 250, 70, 460, 120, t, 40.7, title='【价格战】', draw=dr, t_out=44.4, band=(240, 150, 130))

        def dr2(d, pn):
            button(pn, 20, 36, 150, 32, '跟着降价')
            button(pn, 190, 36, 150, 32, '开放权重', hot=t >= 42.2, pressed=42.5 <= t < 42.7)
        window(ui, 300, 214, 360, 86, t, 41.8, title='如何应对？', draw=dr2, t_out=44.4)
        cursor(ui, t, [(41.9, 760, 500), (42.4, 565, 268)], click_times=(42.5,))

        def dr3(d, pn):
            a = text('¥1 / 百万 token', C_SUB, 2)
            pn.alpha_composite(a, (16, 10))
            d.line((14, 26, 18 + a.width, 20), fill=C_RED, width=3)
            pn.alpha_composite(text('→ ¥0.1（缓存一折）', C_GREEN, 2), (16, 42))
        window(ui, 300, 318, 360, 80, t, 42.7, draw=dr3, t_out=44.4)
        stamp(ui, '权重给你，配方不给', UW / 2, 460, t, 43.1, t_out=44.4)
        hud(ui, '第2年 3月 第2周', '5,000,000,000', '8,192')

    # ---------- S7 发布倒计时 44.5–45.88 ----------
    elif t < 45.88:
        world = bg('P2_员工办公室').copy()
        zoom = lerp(1.0, 1.25, prog(t, 44.5, 1.38))

        def dr(d, pn):
            for ts, s in ((44.5, '3'), (44.97, '2'), (45.42, '1')):
                if ts <= t < ts + 0.47:
                    im = text(s, C_RED, 6)
                    im = scaled(im, back_out(prog(t, ts, 0.16)))
                    pn.alpha_composite(im, ((300 - im.width) // 2, 30 + (100 - im.height) // 2))
            button(pn, 90, 148, 120, 34, '发布！', hot=True, pressed=t >= 45.8, color=(255, 200, 200))
        window(ui, 330, 140, 300, 200, t, 44.5, title='发布 望舒-1？', draw=dr, open_dur=0.08)
        cursor(ui, t, [(44.6, 760, 480), (45.6, 490, 312)], click_times=(45.8,))
        hud(ui, '第2年 4月 第1周', '5,000,000,000', '8,192')

    # ---------- S8 演唱会 45.88–54.24 ----------
    elif t < 54.24:
        world = bg('P6_演唱会').copy()
        flash = 1 - prog(t, 45.88, 0.35)
        # 相机：先全景，副歌中段推近舞台
        if t < 49.0:
            zoom, cx, cy = 1.0, 240, 135
        elif t < 52.0:
            p = ease_in_out(prog(t, 49.0, 0.8))
            zoom, cx, cy = lerp(1.0, 1.7, p), lerp(240, 262, p), lerp(135, 70, p)
        else:
            p = ease_in_out(prog(t, 52.0, 0.8))
            zoom, cx, cy = lerp(1.7, 1.0, p), lerp(262, 240, p), lerp(70, 135, p)
        # 舞台光束
        bp = beat_pulse(t, 0.3)
        for i, (ax, col) in enumerate(((225, (255, 120, 200)), (262, (120, 230, 255)), (300, (255, 240, 140)))):
            ang = math.pi / 2 + 0.55 * math.sin(t * 1.7 + i * 2.1)
            world = light_beam(world, (ax, 6), ang, 230, 0.12, col, int(40 + 50 * bp))
        # 荧光棒闪烁
        d = ImageDraw.Draw(world)
        rng = random.Random(77)
        for i in range(120):
            x, y = rng.randint(120, 400), rng.randint(95, 235)
            col = rng.choice([(120, 255, 140), (120, 230, 255), (255, 140, 220)])
            up = int(2 * math.sin(t * 8 + i)) + (-2 if bp > 0.5 else 0)
            d.line((x, y + up, x, y + up - 3), fill=col)
        banner(ui, '发布会？不，是演唱会！', UW / 2, 92, t, 46.1, 48.8, ribbon=(150, 90, 210), ol=(50, 20, 80))
        rising_icons(ui, t, 46.2, ['note', 'heart', 'star', 'glowstick'], n=30, seed=81, size=16,
                     area=(40, 120, UW - 40, UH), dur=8.0)

        def dr(d, pn):
            pn.alpha_composite(text('用户数', C_SUB), (12, 28))
            n = count(t, 46.8, 6.2, 0, 50000000)
            pn.alpha_composite(text(fmt_num(n), C_ACC, 2), (12, 44))
            pn.alpha_composite(text('热度', C_SUB), (12, 82))
            bar(pn, 50, 84, 170, 10, 0.85 + 0.15 * beat_pulse(t, 0.4), color=(236, 88, 96))
            pn.alpha_composite(text('MAX', C_RED), (228, 80))
            if int(t * 3) % 2 == 0:
                pn.alpha_composite(text('服务器负载 999%', C_RED), (12, 104))
        if not (49.0 <= t < 52.8):
            window(ui, 660, 360, 280, 132, t, 46.6, title='发布数据', draw=dr)
        caption(ui, '发布模型，顺便出道。', t, 47.4, 48.95, y=478)
        if 49.8 <= t < 52.1:
            jump = int(8 * beat_pulse(t, 0.25))
            pop(ui, sprite('singer', 150), 130, 400 - jump, t, 49.8, t_out=52.0)
            pop(ui, sprite('guitar', 150), 830, 400 - jump, t, 50.1, t_out=52.0)
            caption(ui, '大屏滚动：望舒-1，冲上月球！', t, 50.3, 52.0, y=500)
        if t >= 52.9:
            number_pop(ui, '粉丝 +50,000,000', 480, 330, t, 52.9, color=(236, 88, 96), life=1.3, ic='heart')
        fans = count(t, 46.8, 6.2, 8192, 50000000)
        hud(ui, '第2年 4月 第1周', '5,000,000,000', fmt_num(fans))

    # ---------- S9 核爆 54.24–56.3 ----------
    elif t < 56.3:
        world = bg('P7a_蘑菇云').copy()
        p = ease_out(prog(t, 54.24, 2.0))
        zoom, cx, cy = lerp(1.7, 1.0, p), lerp(308, 240, p), lerp(62, 135, p)
        flash = 1 - prog(t, 54.24, 0.45)
        shake = shake_offset(t, 54.24, 1.5, 4)
        pop(ui, text('业界震动！！', C_RED, 5, outline=WHITE), UW / 2, 430, t, 54.6, dur=0.18)

    # ---------- S9b 同行瘫坐 56.3–61.98 ----------
    elif t < 61.98:
        world = bg('P7b_同行瘫坐').copy()
        shake = shake_offset(t, 56.3, 0.3, 1)

        def dr(d, pn):
            m = lerp(1.0, 0.0, ease_out(prog(t, 56.6, 1.0)))
            pn.alpha_composite(text('士气', C_TEXT), (12, 30))
            bar(pn, 50, 33, 200, 10, m, color=C_RED)
            pn.alpha_composite(text('理智', C_TEXT), (12, 52))
            bar(pn, 50, 55, 200, 10, 0.0)
            pn.alpha_composite(text('0', C_RED), (258, 50))
            if int(t * 4) % 2 == 0:
                pn.alpha_composite(text('Code Red 已拉响', C_RED, 2), (12, 74))
        window(ui, 640, 40, 300, 112, t, 56.5, title='同行的反应', draw=dr, band=(170, 180, 200))
        tags = [(57.0, (195, 97), '瘫坐'), (57.9, (116, 182), '咖啡掉了'), (58.8, (165, 195), '跪了'),
                (59.7, (131, 146), '眼镜裂了')]
        for ts, (wx, wy), s in tags:
            ux, uy = w2u(wx, wy)
            shock_lines(ui, ux, uy, t, ts)
            stamp(ui, s, ux, uy - 46, t, ts, scale=2)
        caption(ui, '“那一刻，就像看到原子弹爆炸。”', t, 58.0, 61.95, y=440)
        if t >= 56.4:
            d = ImageDraw.Draw(ui)
            d.rectangle((0, 508, UW, 536), fill=(16, 16, 24, 235))
            d.rectangle((0, 508, 70, 536), fill=(200, 40, 40, 255))
            tk = text(TICKER * 3, (255, 230, 90), 1)
            off = int((t - 56.4) * 130) % text(TICKER, (255, 230, 90), 1).width
            paste(ui, tk, 76 - off, 515)
            ImageDraw.Draw(ui).rectangle((0, 508, 70, 536), fill=(200, 40, 40, 255))
            paste(ui, text('LIVE', WHITE), 35, 522, 'mm')

    # ---------- S10 排行榜 61.98–69.14 ----------
    elif t < 69.14:
        world = darken(bg('P2_员工办公室'), 0.55)

        def dr(d, pn):
            me_p = ease_in_out(prog(t, 63.4, 0.6))
            rows = []
            for i, (m, c, s) in enumerate(BOARD):
                rows.append((i + me_p, m, c, s, False))
            if t >= 63.4:
                rows.append((lerp(6.2, 0, me_p), '望舒-1', '月之亮面', 1405, True))
            for pos, m, c, s, me in rows:
                y = int(34 + pos * 50)
                if y > 330:
                    continue
                if me:
                    d.rectangle((8, y - 2, 651, y + 44), fill=(96, 88, 40), outline=C_GOLD)
                else:
                    d.rectangle((8, y - 2, 651, y + 44), fill=(84, 90, 102))
                rank = int(round(pos)) + 1
                pn.alpha_composite(text(str(rank), C_CYAN if not me else C_GOLD, 2), (18, y + 8))
                pn.alpha_composite(text(m, WHITE, 2), (60, y + 2))
                pn.alpha_composite(text(c, (180, 186, 200)), (62, y + 28))
                bw = (s - 1380) * 9
                d.rectangle((330, y + 14, 330 + bw, y + 28), fill=C_GOLD if me else C_CYAN)
                pn.alpha_composite(text(str(s), WHITE, 2), (560, y + 8))
                if me and t >= 64.0:
                    pn.alpha_composite(icon('crown', 22), (8, y - 14))
        window(ui, 150, 44, 660, 344, t, 62.0, title='世界大模型排行榜 · 本周', draw=dr, dark=True, t_out=69.0)
        if t >= 64.0:
            number_pop(ui, '+3 分', 760, 110, t, 64.0, color=C_GREEN, life=1.2)
        caption(ui, '三家并列第一？——领先 3 分！', t, 64.2, 65.55)

        def dr2(d, pn):
            base = 220
            d.line((30, base, 330, base), fill=C_TEXT, width=2)
            d.rectangle((70, base - 170, 140, base), fill=C_ACC, outline=(60, 70, 140))
            d.rectangle((210, base - 60, 280, base), fill=(180, 184, 194), outline=(120, 124, 134))
            pn.alpha_composite(text('52.8', C_ACC, 2), (78, base - 196))
            pn.alpha_composite(text('69.1', C_SUB, 2), (218, base - 86))
            pn.alpha_composite(text('望舒-1', C_TEXT), (82, base + 6))
            pn.alpha_composite(text('对手', C_TEXT), (228, base + 6))
        window(ui, 300, 90, 360, 270, t, 65.6, title='发布会 PPT · 第 3 页', draw=dr2, t_out=69.0)
        stamp(ui, '图表犯罪', 600, 170, t, 66.6, t_out=69.0)
        caption(ui, '上擂台的那位，不是你能下载的那位。', t, 67.3, 69.0)
        hud(ui, '第2年 6月 第4周', '12,000,000,000', '50,000,000')

    # ---------- S11 登顶 69.14–76.85 ----------
    elif t < 76.85:
        world = bg('P8_登顶庆功').copy()
        flash = 0.7 * (1 - prog(t, 69.14, 0.3))
        zoom = lerp(1.0, 1.12, prog(t, 69.14, 7.7))
        banner(ui, '终于！世界第一！', UW / 2, 96, t, 69.4, 72.2, ribbon=(230, 170, 40), ol=(100, 60, 10))
        crowd = [('emp_toast', 190, 195), ('girl_confetti', 212, 202), ('fan_green', 236, 206), ('hoodie_thumb', 300, 204),
                 ('scientist', 322, 196), ('fan_pink', 276, 210), ('intern_papers', 170, 210), ('emp_toast', 345, 210),
                 ('robot', 256, 218), ('cat', 360, 224)]
        wl = world.convert('RGBA')
        for i, (nm, wx, wy) in enumerate(crowd):
            jump = 3 if (beat_index(t) + i) % 2 == 0 and beat_pulse(t, 0.2) > 0 else 0
            sp = sprite(nm, {'cat': 20, 'robot': 26}.get(nm, 34), flip=i % 3 == 1)
            paste(wl, sp, wx, wy - jump, 'mb')
        jump = 4 if beat_pulse(t, 0.25) > 0 else 0
        paste(wl, sprite('founder_cheer', 40), 256, 204 - jump, 'mb')
        paste(wl, icon('trophy', 18), 256, 166 - jump, 'mb')
        world = wl.convert('RGB')
        confetti(world, t, 69.2, n=160, seed=91, dur=7.7)

        def dr(d, pn):
            ic = icon('trophy', 84)
            pn.alpha_composite(ic, ((380 - ic.width) // 2, 28))
            im = text('月之亮面科技', C_ACC, 2)
            pn.alpha_composite(im, ((380 - im.width) // 2, 118))
            im = text('奖金 ¥1亿', C_RED, 2)
            pn.alpha_composite(im, ((380 - im.width) // 2, 150))
            im = text('（刚好够付签字费）', C_SUB)
            pn.alpha_composite(im, ((380 - im.width) // 2, 186))
        window(ui, 290, 118, 380, 214, t, 70.4, title='年度最强 AI 公司', draw=dr, t_out=76.7)
        rising_icons(ui, t, 73.4, ['heart'], n=26, seed=93, size=18, area=(0, 100, UW, UH), dur=3.5, speed=(50, 90))
        hud(ui, '第3年 12月 第4周', '9,999,999,999', '99,999,999')

    # ---------- S12 片尾 76.85–86.5 ----------
    else:
        world = bg('P9_片尾群像').copy()
        twinkle(world, t, seed=12, n=70, area=(0, 0, W, 150))
        if t < 77.05:
            flash = 0.5
        fade = prog(t, 85.3, 1.2)
        # 标题下落
        if t >= 77.1:
            ty = lerp(-80, 108, back_out(prog(t, 77.1, 0.5), 1.4))
            paste(ui, text('AI发展国', WHITE, 6, outline=(30, 40, 90), shadow=(20, 20, 50)), UW / 2, ty, 'mm')
        if t >= 77.9:
            pop(ui, text('AI Dev Story', C_CYAN, 2, outline=(20, 30, 60)), UW / 2, 170, t, 77.9)
        if t >= 78.7:
            pop(ui, text('成立公司 · 招募天才 · 训练模型 · 登顶世界', WHITE, 2, outline=(20, 30, 60)), UW / 2, 210, t, 78.7)

        def dr(d, pn):
            pn.alpha_composite(text('【快讯】ClosedAI 宣布：下周发布新模型……', C_TEXT, 2), (14, 12))
        window(ui, 190, 250, 580, 50, t, 81.2, draw=dr)
        if t >= 82.6:
            pop(ui, text('第一名有效期：到下一次发布。', (255, 120, 110), 2, outline=(40, 10, 10)), UW / 2, 322, t, 82.6)
        if t >= 84.0:
            pop(ui, text('敬请期待', C_GOLD, 3, outline=(60, 40, 0)), 860, 496, t, 84.0)
            paste(ui, text('本片纯属虚构 · 如有雷同 · 纯属玩梗', (200, 204, 220)), 10, 530, 'lb')

    # ---------- 合成 ----------
    frame = camera(world, zoom, cx, cy)
    up = ui.resize((OW, OH), Image.NEAREST)
    frame = frame.convert('RGBA')
    frame.alpha_composite(up)
    frame = frame.convert('RGB')
    if shake != (0, 0):
        sh = Image.new('RGB', (OW, OH), BLACK)
        sh.paste(frame, shake)
        frame = sh
    if flash > 0:
        frame = Image.blend(frame, Image.new('RGB', (OW, OH), WHITE), clamp(flash))
    if fade > 0:
        frame = Image.blend(frame, Image.new('RGB', (OW, OH), BLACK), clamp(fade))
    return frame
