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


def keycaps(d, keys, y, a):
    fnt = R.font(66)
    ws = [max(120, d.textlength(k, font=fnt) + 70) for k in keys]
    total = sum(ws) + 76 * (len(keys) - 1)
    x = (W - total) / 2
    for i, k in enumerate(keys):
        d.rounded_rectangle((x, y - 62, x + ws[i], y + 62), 20, fill=R.mix((50, 58, 70), a), outline=R.mix(ACC, a), width=5)
        d.text((x + ws[i] / 2, y), k, font=fnt, fill=R.mix(R.INK, a), anchor="mm")
        x += ws[i]
        if i < len(keys) - 1:
            d.text((x + 38, y), "+", font=R.font(58), fill=R.mix(R.MUTED, a), anchor="mm")
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


KINDS = {"windows": k_windows, "pin": k_pin, "ocr": k_ocr, "gif": k_gif, "image": k_image, "cta": k_cta}


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
