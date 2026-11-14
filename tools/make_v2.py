#!/usr/bin/env python3
"""Second-generation Reel renderer driven by a scene list. Usage: make_v2.py <ep.json> [--test]"""
import glob, json, math, os, subprocess, sys
from PIL import Image, ImageDraw
import render_short as R

ep = json.load(open(sys.argv[1]))
name = os.path.splitext(os.path.basename(sys.argv[1]))[0]
root = os.path.dirname(os.path.abspath(sys.argv[1]))
out_dir = f"{root}/{name}"
ACC = tuple(ep["accent"])
scenes = ep["scenes"]
durs = json.load(open(f"{out_dir}/voice/durations.json"))
OFFSET, TAIL = 0.15, 0.4
W, H = R.W, R.H
_cache = {}


def asset(path):
    p = os.path.join(root, path) if not os.path.isabs(path) else path
    if p not in _cache:
        _cache[p] = Image.open(p).convert("RGB")
    return _cache[p]


def fit(img, bw, bh):
    s = min(bw / img.width, bh / img.height)
    return img.resize((int(img.width * s), int(img.height * s)), Image.BILINEAR)


def bg(img, t):
    d = ImageDraw.Draw(img)
    for i in range(3):
        k = 0.12 - i * 0.035
        cx, cy = W * 0.5 + math.sin(t * 0.6 + i) * 180, 300 + i * 620 + math.cos(t * 0.5 + i) * 60
        r = 520 - i * 90
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=tuple(int(R.BG[c] + (ACC[c] - R.BG[c]) * k * 0.45) for c in range(3)))


def win(d, x, y, w, h, title, col, a=1.0, border=None, lines=4):
    d.rounded_rectangle((x, y, x + w, y + h), 22, fill=R.mix((36, 42, 52), a), outline=R.mix(border or (70, 78, 90), a), width=8 if border else 3)
    d.rounded_rectangle((x + 3, y + 3, x + w - 3, y + 66), 20, fill=R.mix(col, a))
    d.text((x + 30, y + 34), title, font=R.font(36), fill=R.mix(R.INK, a), anchor="lm")
    for i in range(lines):
        lw = (w - 90) * (1 - 0.14 * (i % 3))
        ly = y + 110 + i * 54
        if ly + 20 < y + h:
            d.rounded_rectangle((x + 40, ly, x + 40 + lw, ly + 20), 10, fill=R.mix((92, 100, 114), a))


def keycaps(d, keys, y, a, sep="+"):
    fnt = R.font(66)
    ws = [max(120, d.textlength(k, font=fnt) + 70) for k in keys]
    total = sum(ws) + 76 * (len(keys) - 1)
    x = (W - total) / 2
    for i, k in enumerate(keys):
        d.rounded_rectangle((x, y - 62, x + ws[i], y + 62), 20, fill=R.mix((50, 58, 70), a), outline=R.mix(ACC, a), width=5)
        d.text((x + ws[i] / 2, y), k, font=fnt, fill=R.mix(R.INK, a), anchor="mm")
        x += ws[i]
        if i < len(keys) - 1:
            d.text((x + 38, y), sep, font=R.font(58 if sep == "+" else 44), fill=R.mix(R.MUTED, a), anchor="mm")
            x += 76


def title(d, s, a=1.0, y=430, size=92, col=None):
    d.text((W / 2, y), s, font=R.font(size), fill=R.mix(col or R.INK, a), anchor="mm")


def k_windows(img, d, t, v, sc):
    title(d, sc["title"], col=R.RED)
    win(d, 150, 620, 640, 470, "我的筆記", (45, 110, 70))
    pops = [(330, 690, "網頁", (60, 90, 160), -0.5), (210, 800, "試算表", (120, 80, 150), 0.18), (420, 900, "聊天", (160, 95, 60), 0.42)]
    for x, y, n, c, st in pops:
        e = R.ease(t, st * v, 0.25)
        if e > 0:
            win(d, x, y + (1 - e) * 80, 560, 400, n, c, e)


def k_pin(img, d, t, v, sc):
    title(d, sc["title"], y=400, size=118, col=ACC)
    d.text((W / 2, 520), sc["subtitle"], font=R.font(54, R.MED), fill=R.INK, anchor="mm")
    for x, y, n, c in [(330, 690, "網頁", (60, 90, 160)), (210, 800, "試算表", (120, 80, 150)), (420, 900, "聊天", (160, 95, 60))]:
        win(d, x, y, 560, 400, n, c, 0.42)
    e = R.ease(t, v * 0.55, 0.35)
    if e < 1:
        win(d, 150, 620, 640, 470, "我的筆記", (45, 110, 70), 0.42)
    if e > 0:
        win(d, 240, 680 - e * 30, 640, 470, "我的筆記", (45, 110, 70), e, border=ACC)
    keycaps(d, sc["keys"], 1275, R.ease(t, v * 0.3))


def k_ocr(img, d, t, v, sc):
    title(d, sc["title"], y=420)
    x, y, w, h = 130, 560, 820, 460
    d.rounded_rectangle((x, y, x + w, y + h), 24, fill=(232, 228, 214))
    for i, line in enumerate(sc["lines"]):
        d.text((x + 70, y + 110 + i * 120), line, font=R.font(68), fill=(40, 40, 46), anchor="lm")
    e = R.ease(t, v * 0.42, 0.7)
    if e > 0:
        x1, y1 = x + 40 + e * (w - 80), y + 40 + e * (h - 80)
        d.rectangle((x + 40, y + 40, x1, y1), outline=ACC, width=8)
    keycaps(d, sc["keys"], 1150, R.ease(t, v * 0.2))
    a = R.ease(t, v * 0.82)
    if a > 0:
        d.rounded_rectangle((270, 1240, 810, 1336), 48, fill=R.mix(ACC, a))
        d.text((W / 2, 1288), "已複製到剪貼簿", font=R.font(52), fill=R.mix((10, 14, 20), a), anchor="mm")


def k_gif(img, d, t, v, sc):
    title(d, sc["title"], y=400)
    frames = sorted(glob.glob(os.path.join(root, sc["frames"], "*.png")))
    fr = asset(frames[int(t * sc.get("fps", 12)) % len(frames)])
    im = fit(fr, 960, 760)
    x, y = (W - im.width) // 2, 520 + (760 - im.height) // 2
    d.rounded_rectangle((x - 10, y - 10, x + im.width + 10, y + im.height + 10), 22, outline=ACC, width=6)
    img.paste(im, (x, y))
    d.text((W / 2, 1320), sc["credit"], font=R.font(34, R.MED), fill=R.MUTED, anchor="mm")


def k_image(img, d, t, v, sc):
    title(d, sc["title"], y=400)
    base = fit(asset(sc["image"]), 980, 760)
    z = 1 + 0.05 * (t / max(v, 1))
    im = base.resize((int(base.width * z), int(base.height * z)), Image.BILINEAR)
    img.paste(im, ((W - im.width) // 2, 900 - im.height // 2))
    d.text((W / 2, 1320), sc["credit"], font=R.font(34, R.MED), fill=R.MUTED, anchor="mm")


def k_cta(img, d, t, v, sc):
    title(d, sc["title"], y=410, size=88)
    if sc.get("image"):
        im = fit(asset(sc["image"]), 960, 340)
        img.paste(im, ((W - im.width) // 2, 500))
    d.text((W / 2, 900), sc["url"], font=R.font(46, R.MED), fill=R.BLUE, anchor="mm")
    a = R.ease(t, v * sc.get("cta_at", 0.5))
    d.text((W / 2, 1090), "追蹤我", font=R.font(116), fill=R.mix(ACC, a), anchor="mm")
    d.text((W / 2, 1225), "每週挖一個好用的開源專案", font=R.font(62), fill=R.mix(R.INK, a), anchor="mm")
    if sc.get("credit"):
        d.text((W / 2, 1320), sc["credit"], font=R.font(32, R.MED), fill=R.MUTED, anchor="mm")



INK_D = (30, 30, 36)


def wline(d, a, b, prog, col, seed, w=7):
    n = 16
    pts = []
    for i in range(int(n * max(0, min(1, prog))) + 1):
        f = i / n
        off = math.sin(f * 7 + seed) * 4 + math.sin(f * 17 + seed * 2) * 2
        pts.append((a[0] + (b[0] - a[0]) * f + off, a[1] + (b[1] - a[1]) * f - off))
    if len(pts) > 1:
        d.line(pts, fill=col, width=w, joint="curve")


def wbox(d, x, y, w, h, prog, col, label, seed):
    c = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
    for i in range(4):
        wline(d, c[i], c[i + 1], prog * 4 - i, col, seed + i)
    if prog >= 1:
        d.text((x + w / 2, y + h / 2), label, font=R.font(54, R.MED), fill=INK_D, anchor="mm")


def arrow(d, a, b, prog, seed):
    wline(d, a, b, prog, INK_D, seed)
    if prog >= 1:
        wline(d, b, (b[0] - 22, b[1] - 28), 1, INK_D, seed + 1)
        wline(d, b, (b[0] + 22, b[1] - 28), 1, INK_D, seed + 2)


def paper(d, note=True):
    d.rounded_rectangle((90, 540, 990, 1300), 26, fill=(250, 249, 245))
    if note:
        d.text((W / 2, 1345), "示意畫面", font=R.font(32, R.MED), fill=R.MUTED, anchor="mm")


def flow(d, f, cols=None):
    cols = cols or ((105, 80, 210), (20, 140, 110), (210, 95, 50))
    labels = [(330, 600, "有個想法"), (330, 835, "畫成流程圖"), (330, 1070, "分享給大家")]
    for i, (x, y, l) in enumerate(labels):
        wbox(d, x, y, 420, 150, (f - i * 0.36) / 0.26, cols[i], l, i * 3 + 1)
    arrow(d, (540, 752), (540, 830), (f - 0.26) / 0.1, 11)
    arrow(d, (540, 987), (540, 1065), (f - 0.62) / 0.1, 13)


def k_install(img, d, t, v, sc):
    title(d, sc["title"], col=R.RED, size=84)
    win(d, 150, 640, 780, 480, "安裝程式", (70, 80, 100), lines=0)
    d.text((W / 2, 830), "正在安裝…", font=R.font(66), fill=R.INK, anchor="mm")
    d.rounded_rectangle((230, 930, 850, 975), 22, fill=(60, 66, 78))
    d.rounded_rectangle((230, 930, 230 + 620 * (0.08 + 0.05 * min(1, t / max(v, 1))), 975), 22, fill=R.RED)
    d.text((W / 2, 1040), "剩餘時間：計算中", font=R.font(46, R.MED), fill=R.MUTED, anchor="mm")


def k_sketch(img, d, t, v, sc):
    title(d, sc["title"], y=385, size=118, col=ACC)
    d.text((W / 2, 495), sc["subtitle"], font=R.font(52, R.MED), fill=R.INK, anchor="mm")
    paper(d)
    flow(d, min(1, t / (v * 0.92)))


def cursor(d, x, y, col, name):
    d.polygon([(x, y), (x, y + 54), (x + 15, y + 41), (x + 38, y + 44)], fill=col)
    tw = d.textlength(name, font=R.font(36, R.MED))
    d.rounded_rectangle((x + 34, y + 44, x + 34 + tw + 32, y + 100), 14, fill=col)
    d.text((x + 50 + tw / 2, y + 72), name, font=R.font(36, R.MED), fill=(255, 255, 255), anchor="mm")


def k_collab(img, d, t, v, sc):
    title(d, sc["title"], y=420)
    paper(d)
    flow(d, 1)
    q = min(1, t / (v * 0.85))
    wbox(d, 790, 600, 165, 150, q * 1.1, (40, 120, 220), "A", 21)
    wline(d, (170, 880), (300, 880), q * 1.4, (200, 60, 120), 25)
    wline(d, (170, 930), (300, 930), q * 1.4 - 0.4, (200, 60, 120), 27)
    cursor(d, 610 + q * 190, 760 + math.sin(t * 2) * 25, (40, 120, 220), "同事 A")
    cursor(d, 300 - q * 40 + math.sin(t * 2.4) * 30, 945 + q * 30, (200, 60, 120), "同事 B")


def k_export(img, d, t, v, sc):
    title(d, sc["title"], y=420)
    paper(d, note=False)
    flow(d, 1)
    d.rounded_rectangle((90, 540, 990, 1300), 26, outline=ACC, width=6)
    for i, l in enumerate(sc["chips"]):
        e = R.ease(t, v * (0.2 + i * 0.2))
        if e > 0:
            x = 775
            y = 650 + i * 150 + (1 - e) * 40
            d.rounded_rectangle((x, y, x + 195, y + 110), 22, fill=tuple(int(250 + (ACC[c] - 250) * e) for c in range(3)))
            d.text((x + 97, y + 55), l, font=R.font(50), fill=(255, 255, 255), anchor="mm")
    d.text((W / 2, 1345), "示意畫面", font=R.font(32, R.MED), fill=R.MUTED, anchor="mm")


# ---------- v3: fast-hook scenes (big result text first, label only on the last scene) ----------
WHITE, PAPER = (255, 255, 255), (246, 247, 250)
DARK_INK = (28, 32, 40)
TOP = 640  # top of the illustration area


def fit_font(d, s, size, maxw, path=None):
    path = path or R.BOLD
    while size > 40 and d.textlength(s, font=R.font(size, path)) > maxw:
        size -= 4
    return R.font(size, path)


def big_lines(d, lines, y0=360, gap=150, size=124):
    for i, s in enumerate(lines):
        col = R.INK if (i == 0 and len(lines) > 1) else ACC
        d.text((W / 2, y0 + i * gap), s, font=fit_font(d, s, size if i else int(size * 0.8), 980), fill=col, anchor="mm")


def note(d, s="示意畫面"):
    d.text((W / 2, 1335), s, font=R.font(30, R.MED), fill=R.MUTED, anchor="mm")


def phone_box(d, cx, cy, w=250, h=470, edge=None):
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), 40, fill=(22, 26, 33), outline=edge or (110, 118, 130), width=7)
    return (cx - w / 2 + 16, cy - h / 2 + 40, cx + w / 2 - 16, cy + h / 2 - 34)


def laptop_box(d, cx, cy, w=470, h=300, edge=None):
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), 20, fill=(22, 26, 33), outline=edge or (110, 118, 130), width=7)
    d.rounded_rectangle((cx - w / 2 - 40, cy + h / 2 + 6, cx + w / 2 + 40, cy + h / 2 + 34), 14, fill=(110, 118, 130))
    return (cx - w / 2 + 16, cy - h / 2 + 16, cx + w / 2 - 16, cy + h / 2 - 16)


CODES = [("Email", "382 914"), ("雲端硬碟", "507 226"), ("社群帳號", "641 083")]


def screen_codes(d, box, t, scale=1.0):
    x0, y0, x1, y1 = box
    rh = (y1 - y0) / 3
    for i, (n, c) in enumerate(CODES):
        y = y0 + i * rh
        d.rounded_rectangle((x0 + 6, y + 8, x1 - 6, y + rh - 8), 14, fill=(40, 46, 58))
        d.text((x0 + 22, y + rh * 0.3), n, font=R.font(int(24 * scale), R.MED), fill=R.MUTED, anchor="lm")
        d.text((x0 + 22, y + rh * 0.64), c, font=R.font(int(40 * scale)), fill=ACC, anchor="lm")
        a = (t * 0.25 + i * 0.2) % 1
        cx, cy, r = x1 - 34, y + rh / 2, 15
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(80, 88, 100), width=5)
        d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * (1 - a), fill=ACC, width=5)


def screen_note(d, box, t, scale=1.0):
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, 12, fill=PAPER)
    d.text((x0 + 20, y0 + 36 * scale), "週末清單", font=R.font(int(36 * scale)), fill=DARK_INK, anchor="lm")
    for i, s in enumerate(["買牛奶", "繳電話費", "訂餐廳"]):
        y = y0 + (95 + i * 62) * scale
        if y + 20 > y1:
            break
        d.rounded_rectangle((x0 + 20, y - 15 * scale, x0 + 20 + 30 * scale, y + 15 * scale), 6, outline=ACC, width=4)
        if i == 0:
            d.line((x0 + 26, y, x0 + 33 * scale, y + 9 * scale, x0 + 46 * scale, y - 10 * scale), fill=ACC, width=5)
        d.text((x0 + 66 * scale, y), s, font=R.font(int(30 * scale), R.MED), fill=DARK_INK, anchor="lm")


def screen_browser(d, box, t, label, url, other):
    x0, y0, x1, y1 = box
    d.rounded_rectangle((x0, y0, x1, y0 + 44), 10, fill=(48, 54, 66))
    d.text(((x0 + x1) / 2, y0 + 22), url, font=fit_font(d, url, 26, x1 - x0 - 20, R.MED), fill=R.INK, anchor="mm")
    cx, cy = (x0 + x1) / 2, (y0 + 44 + y1) / 2 - 14
    r = 46 + 6 * math.sin(t * 4)
    for k in (1.9, 1.45):
        d.ellipse((cx - r * k, cy - r * k, cx + r * k, cy + r * k), outline=R.mix(ACC, 0.35), width=3)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ACC)
    d.text((cx, cy), other[:2], font=R.font(30), fill=(10, 14, 20), anchor="mm")
    d.text((cx, min(cy + r * 1.9 + 24, y1 - 18)), other, font=R.font(26, R.MED), fill=R.INK, anchor="mm")


def file_chip(d, x, y, label, a=1.0):
    w = d.textlength(label, font=R.font(36)) + 90
    d.rounded_rectangle((x - w / 2, y - 40, x + w / 2, y + 40), 18, fill=R.mix(ACC, a))
    d.rectangle((x - w / 2 + 22, y - 18, x - w / 2 + 50, y + 18), fill=R.mix((10, 14, 20), a))
    d.text((x + 22, y), label, font=R.font(36), fill=R.mix((10, 14, 20), a), anchor="mm")


def v_devices(img, d, t, v, sc, hook=False):
    mode = sc.get("screen", "send")
    pc, lc = (290, TOP + 330), (760, TOP + 300)
    pb = phone_box(d, *pc)
    lb = laptop_box(d, *lc)
    d.text((pc[0], TOP + 615), "手機", font=R.font(40, R.MED), fill=R.MUTED, anchor="mm")
    d.text((lc[0], TOP + 615), "電腦", font=R.font(40, R.MED), fill=R.MUTED, anchor="mm")
    if mode == "send":
        url = sc.get("url_bar", "")
        screen_browser(d, pb, t, "手機", url, "電腦")
        screen_browser(d, lb, t, "電腦", url, "手機")
        p = ((t + (0.55 if hook else 0)) / 1.5) % 1
        e = 1 - (1 - min(1, p / 0.7)) ** 3
        x = pc[0] + (lc[0] - pc[0]) * e
        y = TOP + 120 - math.sin(e * math.pi) * 110
        file_chip(d, x, y, sc.get("item", "照片.jpg"), 1 if p < 0.85 else max(0, 1 - (p - 0.85) / 0.15))
    else:
        fn = screen_codes if mode == "codes" else screen_note
        fn(d, pb, t, 0.82 if mode == "codes" else 0.95)
        fn(d, lb, t, 1.0)
        p = (t / 1.2) % 1
        for k in range(3):
            q = (p + k / 3) % 1
            x = pc[0] + 150 + (lc[0] - 250 - pc[0] - 150) * q
            d.ellipse((x - 9, TOP + 300 - 9, x + 9, TOP + 300 + 9), fill=R.mix(ACC, math.sin(q * math.pi)))
    note(d, sc.get("note", "示意畫面"))


def v_typing(img, d, t, v, sc, hook=False):
    typed, result = sc["typed"], sc["result"]
    period = max(2.4, v * 0.95)
    p = ((t + (period * 0.55 if hook else 0)) / period) % 1
    x0, y0, x1, y1 = 90, TOP + 60, 990, TOP + 330
    d.rounded_rectangle((x0, y0, x1, y1), 26, fill=PAPER)
    d.text((x0 + 40, y0 + 46), sc.get("app", "任何可以打字的地方"), font=R.font(32, R.MED), fill=(120, 126, 138), anchor="lm")
    if p < 0.45:
        s = typed[:max(1, int(len(typed) * min(1, p / 0.35)) + 0)]
        f = R.font(84)
        d.text((x0 + 40, y0 + 175), s, font=f, fill=DARK_INK, anchor="lm")
        cx = x0 + 44 + d.textlength(s, font=f)
        if int(t * 3) % 2 == 0:
            d.rectangle((cx, y0 + 130, cx + 6, y0 + 220), fill=DARK_INK)
    else:
        f = fit_font(d, result, 84, x1 - x0 - 80)
        tw = d.textlength(result, font=f)
        d.rounded_rectangle((x0 + 30, y0 + 125, x0 + 50 + tw, y0 + 225), 14, fill=R.mix(ACC, 0.35 + 0.65 * min(1, (p - 0.45) / 0.1)))
        d.text((x0 + 40, y0 + 175), result, font=f, fill=DARK_INK, anchor="lm")
    # trigger -> result legend
    fy = TOP + 470
    tf = R.font(64)
    tw = d.textlength(typed, font=tf)
    d.rounded_rectangle((W / 2 - 330 - tw / 2 - 30, fy - 55, W / 2 - 330 + tw / 2 + 30, fy + 55), 20, outline=ACC, width=5)
    d.text((W / 2 - 330, fy), typed, font=tf, fill=R.INK, anchor="mm")
    d.text((W / 2 - 120, fy), "→", font=R.font(80), fill=ACC, anchor="mm")
    d.text((W / 2 + 230, fy), sc.get("result_tag", "自動展開"), font=fit_font(d, sc.get("result_tag", "自動展開"), 60, 420), fill=R.INK, anchor="mm")
    note(d, sc.get("note", "示意畫面"))


def scenery(w, h):
    im = Image.new("RGB", (w, h))
    dd = ImageDraw.Draw(im)
    for y in range(h):
        k = y / h
        dd.line((0, y, w, y), fill=(int(90 + 120 * k), int(150 + 70 * k), int(230 - 20 * k)))
    dd.ellipse((w * 0.68, h * 0.12, w * 0.68 + h * 0.22, h * 0.34), fill=(255, 214, 102))
    dd.polygon([(0, h * 0.72), (w * 0.25, h * 0.35), (w * 0.5, h * 0.72)], fill=(70, 110, 130))
    dd.polygon([(w * 0.3, h * 0.72), (w * 0.6, h * 0.28), (w * 0.95, h * 0.72)], fill=(52, 88, 112))
    dd.polygon([(w * 0.53, h * 0.38), (w * 0.6, h * 0.28), (w * 0.67, h * 0.38)], fill=(245, 248, 252))
    dd.rectangle((0, h * 0.72, w, h), fill=(64, 150, 96))
    dd.rectangle((w * 0.12, h * 0.6, w * 0.26, h * 0.8), fill=(214, 90, 70))
    dd.polygon([(w * 0.1, h * 0.6), (w * 0.19, h * 0.5), (w * 0.28, h * 0.6)], fill=(120, 60, 50))
    for i in range(7):
        x = w * (0.35 + i * 0.09)
        dd.ellipse((x, h * 0.78, x + w * 0.05, h * 0.86), fill=(250, 250, 250) if i % 2 else (255, 200, 80))
    return im


def v_upscale(img, d, t, v, sc, hook=False):
    w, h = 900, 600
    key = ("scenery", w, h)
    if key not in _cache:
        sharp = scenery(w, h)
        low = sharp.resize((w // 14, h // 14), Image.BILINEAR).resize((w, h), Image.NEAREST)
        _cache[key] = (sharp, low)
    sharp, low = _cache[key]
    x0, y0 = 90, TOP + 10
    if sc.get("view", "wipe") == "wipe":
        div = int(w * (0.5 + 0.32 * math.sin(t * 1.6 + (1.2 if hook else 0))))
        img.paste(low.crop((0, 0, div, h)), (x0, y0))
        img.paste(sharp.crop((div, 0, w, h)), (x0 + div, y0))
        d.line((x0 + div, y0, x0 + div, y0 + h), fill=WHITE, width=8)
        d.ellipse((x0 + div - 30, y0 + h / 2 - 30, x0 + div + 30, y0 + h / 2 + 30), fill=WHITE)
        d.text((x0 + div, y0 + h / 2), "⇆", font=R.font(36), fill=DARK_INK, anchor="mm")
        for lx, s, c in [(x0 + 20, "原圖", (60, 60, 66)), (x0 + w - 20, "AI 放大", ACC)]:
            tw = d.textlength(s, font=R.font(40))
            bx = lx if lx < W / 2 else lx - tw - 40
            d.rounded_rectangle((bx, y0 + 20, bx + tw + 40, y0 + 86), 16, fill=c)
            d.text((bx + 20 + tw / 2, y0 + 53), s, font=R.font(40), fill=WHITE if c != ACC else (10, 14, 20), anchor="mm")
    else:
        e = R.ease(t, v * 0.25, 0.8)
        sw = int(150 + (w - 150) * e)
        sh = int(sw * h / w)
        src = low if e < 0.6 else sharp
        im = src.resize((sw, sh), Image.BILINEAR)
        img.paste(im, (x0 + (w - sw) // 2, y0 + (h - sh) // 2))
        d.rounded_rectangle((W / 2 - 90, y0 + h + 10, W / 2 + 90, y0 + h + 90), 24, fill=ACC)
        d.text((W / 2, y0 + h + 50), "× 4", font=R.font(56), fill=(10, 14, 20), anchor="mm")
    d.rectangle((x0, y0, x0 + w, y0 + h), outline=ACC, width=5)
    note(d, sc.get("note", "示意畫面"))


FILES = [("旅行.jpg", (64, 150, 96)), ("報告.pdf", (214, 70, 60)), ("簡報.pptx", (220, 120, 50)), ("影片.mp4", (90, 110, 220))]


def v_explorer(img, d, t, v, sc, hook=False):
    x0, y0, x1, y1 = 90, TOP, 990, TOP + 620
    win(d, x0, y0, x1 - x0, y1 - y0, "檔案總管", (60, 70, 90), lines=0)
    period = max(2.0, v * 0.9)
    p = ((t + (period * 0.5 if hook else 0)) / period) % 1
    sel = int((t / 1.1)) % len(FILES) if sc.get("arrows") else 0
    for i, (n, c) in enumerate(FILES):
        y = y0 + 110 + i * 120
        if i == sel:
            d.rounded_rectangle((x0 + 24, y - 10, x1 - 24, y + 90), 14, fill=R.mix(ACC, 0.35))
        d.rounded_rectangle((x0 + 50, y + 5, x0 + 120, y + 75), 10, fill=c)
        d.text((x0 + 150, y + 40), n, font=R.font(46, R.MED), fill=R.INK, anchor="lm")
    show = sc.get("arrows") or p > 0.4
    if show:
        a = 1 if sc.get("arrows") else min(1, (p - 0.4) / 0.1)
        px0, py0, px1, py1 = 330, TOP + 150, 1020, TOP + 600
        d.rounded_rectangle((px0, py0, px1, py1), 22, fill=R.mix((245, 246, 248), a), outline=R.mix(ACC, a), width=6)
        name, col = FILES[sel]
        if a > 0.6:
            key = ("scenery", px1 - px0 - 40, py1 - py0 - 100)
            if sel == 0:
                if key not in _cache:
                    _cache[key] = scenery(key[1], key[2])
                img.paste(_cache[key], (px0 + 20, py0 + 80))
            else:
                d.rectangle((px0 + 20, py0 + 80, px1 - 20, py1 - 20), fill=(255, 255, 255))
                d.rectangle((px0 + 20, py0 + 80, px1 - 20, py0 + 150), fill=col)
                for k in range(5):
                    d.rounded_rectangle((px0 + 60, py0 + 190 + k * 50, px1 - 60 - (k % 3) * 80, py0 + 210 + k * 50), 8, fill=(200, 204, 212))
            d.text((px0 + 30, py0 + 40), name, font=R.font(36), fill=DARK_INK, anchor="lm")
    note(d, sc.get("note", "示意畫面"))


def v_cliplist(img, d, t, v, sc, hook=False):
    items = sc["items"]
    q = sc.get("query", "")
    x0, y0, x1 = 140, TOP, 940
    rows = len(items)
    d.rounded_rectangle((x0, y0, x1, y0 + 130 + rows * 104), 26, fill=(242, 242, 245), outline=(200, 200, 208), width=3)
    p = min(1, t / max(0.1, v * 0.6)) if not hook else 1
    typed = q[:int(len(q) * p)] if q else ""
    d.rounded_rectangle((x0 + 24, y0 + 24, x1 - 24, y0 + 100), 16, fill=WHITE)
    d.text((x0 + 50, y0 + 62), "🔍" if False else "搜尋：", font=R.font(38, R.MED), fill=(130, 134, 144), anchor="lm")
    d.text((x0 + 170, y0 + 62), typed, font=R.font(40), fill=DARK_INK, anchor="lm")
    hit = next((i for i, s in enumerate(items) if q and q in s), 0) if typed == q and q else (int(t / 0.8) % rows if hook else 0)
    for i, s in enumerate(items):
        y = y0 + 130 + i * 104
        dim = bool(q) and typed == q and q not in s
        if i == hit:
            d.rounded_rectangle((x0 + 16, y, x1 - 16, y + 90), 14, fill=ACC)
        f = fit_font(d, s, 42, x1 - x0 - 200, R.MED)
        d.text((x0 + 50, y + 45), s, font=f, fill=(170, 172, 180) if dim else DARK_INK, anchor="lm")
        d.text((x1 - 50, y + 45), f"⌘{i + 1}", font=R.font(34, R.MED), fill=(110, 114, 124), anchor="rm")
    note(d, sc.get("note", "示意畫面"))


VISUALS = {"devices": v_devices, "typing": v_typing, "upscale": v_upscale, "explorer": v_explorer, "cliplist": v_cliplist}


def k_hook(img, d, t, v, sc):
    big_lines(d, sc["big"])
    VISUALS[sc["visual"]](img, d, t, v, sc, hook=True)


def k_demo(img, d, t, v, sc):
    d.text((W / 2, 330), sc["title"], font=fit_font(d, sc["title"], 84, 980), fill=R.INK, anchor="mm")
    if sc.get("keys"):
        keycaps(d, sc["keys"], 495, 1.0, sc.get("keys_sep", "+"))
    elif sc.get("chips"):
        fnt = R.font(46)
        ws = [d.textlength(c, font=fnt) + 56 for c in sc["chips"]]
        x = (W - sum(ws) - 24 * (len(ws) - 1)) / 2
        for i, c in enumerate(sc["chips"]):
            e = R.ease(t, v * 0.12 * i, 0.3)
            d.rounded_rectangle((x, 450 + (1 - e) * 30, x + ws[i], 540 + (1 - e) * 30), 45, fill=R.mix(ACC, e))
            d.text((x + ws[i] / 2, 495 + (1 - e) * 30), c, font=fnt, fill=R.mix((10, 14, 20), e), anchor="mm")
            x += ws[i] + 24
    VISUALS[sc["visual"]](img, d, t, v, sc)


def k_cta2(img, d, t, v, sc):
    d.text((W / 2, 440), sc["name"], font=fit_font(d, sc["name"], 130, 980), fill=ACC, anchor="mm")
    d.text((W / 2, 570), sc["subtitle"], font=fit_font(d, sc["subtitle"], 56, 980, R.MED), fill=R.INK, anchor="mm")
    y = 720
    for u in sc["urls"]:
        d.text((W / 2, y), u, font=fit_font(d, u, 50, 980, R.MED), fill=R.BLUE, anchor="mm")
        y += 80
    a = R.ease(t, v * sc.get("cta_at", 0.45))
    d.text((W / 2, 1060), "追蹤我", font=R.font(116), fill=R.mix(ACC, a), anchor="mm")
    d.text((W / 2, 1195), "每天一個好用的開源工具", font=R.font(60), fill=R.mix(R.INK, a), anchor="mm")
    if sc.get("credit"):
        d.text((W / 2, 1320), sc["credit"], font=R.font(30, R.MED), fill=R.MUTED, anchor="mm")


KINDS = {"hook": k_hook, "demo": k_demo, "cta2": k_cta2, "install": k_install, "sketch": k_sketch, "collab": k_collab, "export": k_export, "windows": k_windows, "pin": k_pin, "ocr": k_ocr, "gif": k_gif, "image": k_image, "cta": k_cta}


def caption(img, d, t, v, subs):
    total = sum(len(s) for s in subs)
    pos, cur = 0.0, subs[-1]
    for s in subs:
        pos += len(s) / total * v
        if t - OFFSET <= pos:
            cur = s
            break
    fnt = R.font(60)
    tw = d.textlength(cur, font=fnt)
    d.rounded_rectangle((W / 2 - tw / 2 - 34, 1415, W / 2 + tw / 2 + 34, 1525), 20, fill=(0, 0, 0))
    d.text((W / 2, 1470), cur, font=fnt, fill=(255, 226, 90), anchor="mm")


def frame(i, t):
    sc, v = scenes[i], durs[i]
    dur = v + OFFSET + TAIL
    img = Image.new("RGB", (W, H), R.BG)
    bg(img, t + i)
    d = ImageDraw.Draw(img)
    last = i == len(scenes) - 1
    if (last if ep.get("label_last") else i > 0 or not ep.get("no_first_label")):
        d.text((W / 2, 280), f"開源好物 #{ep['no']:03d}", font=R.font(44, R.MED), fill=ACC, anchor="mm")
    KINDS[sc["kind"]](img, d, t, v, sc)
    caption(img, d, t, v, sc["subs"])
    if i == len(scenes) - 1:
        o = max(0, min(1, (dur - t) / 0.4))
        if o < 1:
            img = Image.blend(Image.new("RGB", (W, H), R.BG), img, o)
    return img


if "--test" in sys.argv:
    sheet = Image.new("RGB", (W // 3 * len(scenes), H // 3), (60, 60, 60))
    for i in range(len(scenes)):
        sheet.paste(frame(i, durs[i] * 0.9 + OFFSET).resize((W // 3 - 4, H // 3)), (i * W // 3, 0))
    sheet.save(f"{out_dir}/sheet.png")
    frame(0, 0).save(f"{out_dir}/first.png")
    sys.exit()

os.makedirs(f"{out_dir}/scenes", exist_ok=True)
lens = []
for i in range(len(scenes)):
    dur = durs[i] + OFFSET + TAIL
    lens.append(round(dur, 3))
    tmp, final = f"{out_dir}/scenes/s{i}.tmp.mp4", f"{out_dir}/scenes/s{i}.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(R.FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                          "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for f in range(round(dur * R.FPS)):
        p.stdin.write(frame(i, f / R.FPS).tobytes())
    p.stdin.close()
    if p.wait() != 0:
        sys.exit(f"scene {i} failed")
    os.replace(tmp, final)
with open(f"{out_dir}/scenes/list.txt", "w") as fh:
    fh.writelines(f"file 's{i}.mp4'\n" for i in range(len(scenes)))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{out_dir}/scenes/list.txt",
                "-c", "copy", f"{out_dir}/video.mp4"], check=True)
print(json.dumps(lens))
