#!/usr/bin/env python3
"""LocalSend 30-second vertical short. Usage: render_short.py [--test]"""
import math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
BG = (13, 17, 23)
INK = (240, 246, 252)
MUTED = (139, 148, 158)
GREEN = (63, 185, 80)
BLUE = (88, 166, 255)
RED = (248, 81, 73)
PANEL = (33, 38, 45)
BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
MED = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"
_fonts = {}


def font(size, path=BOLD):
    key = (size, path)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(path, size, index=3)
    return _fonts[key]


def mix(c, a):
    a = max(0, min(1, a))
    return tuple(int(BG[i] + (c[i] - BG[i]) * a) for i in range(3))


def ease(t, start, dur=0.45):
    x = max(0, min(1, (t - start) / dur))
    return 1 - (1 - x) ** 3


def text(d, s, y, size, color=INK, a=1, path=BOLD, slide=0, x=W / 2):
    d.text((x, y + slide), s, font=font(size, path), fill=mix(color, a), anchor="mm")


def appear(d, t, start, s, y, size, color=INK, out=1, path=BOLD):
    e = ease(t, start)
    text(d, s, y, size, color, e * out, path, slide=(1 - e) * 50)


def chrome(d, out):
    text(d, "開源好物 #001", 280, 44, GREEN, out, MED)


def phone(d, cx, cy, a, label="手機"):
    d.rounded_rectangle((cx - 85, cy - 165, cx + 85, cy + 165), 28,
                        fill=mix(PANEL, a), outline=mix(BLUE, a), width=6)
    d.rounded_rectangle((cx - 32, cy + 135, cx + 32, cy + 143), 4, fill=mix(MUTED, a))
    text(d, label, cy + 220, 46, MUTED, a, MED, x=cx)


def laptop(d, cx, cy, a, label="電腦"):
    d.rounded_rectangle((cx - 155, cy - 120, cx + 155, cy + 80), 18,
                        fill=mix(PANEL, a), outline=mix(GREEN, a), width=6)
    d.rounded_rectangle((cx - 195, cy + 88, cx + 195, cy + 112), 12, fill=mix(GREEN, a))
    text(d, label, cy + 220, 46, MUTED, a, MED, x=cx)


def s1(d, t, out):
    chrome(d, out)
    appear(d, t, 0.05, "手機傳檔案到電腦", 690, 92, INK, out)
    appear(d, t, 0.75, "你還在", 900, 76, MUTED, out)
    appear(d, t, 1.15, "傳給自己嗎？", 1040, 124, RED, out)


def s2(d, t, out):
    chrome(d, out)
    e = ease(t, 0.05, 0.55)
    text(d, "LocalSend", 760, 150, GREEN, e * out, slide=(1 - e) * 60)
    appear(d, t, 0.8, "免費　開源　跨平台", 950, 72, INK, out)
    appear(d, t, 1.5, "github.com/localsend/localsend", 1090, 46, BLUE, out, MED)


def s3(d, t, out):
    chrome(d, out)
    appear(d, t, 0.05, "只要在同一個區域網路", 470, 76, INK, out)
    y0 = 880
    a = ease(t, 0.3) * out
    phone(d, 250, y0, a)
    laptop(d, 800, y0, a)
    if t > 0.9:
        for i in range(5):
            p = ((t - 0.9) * 0.55 + i / 5) % 1
            x = 345 + p * 280
            y = y0 - math.sin(p * math.pi) * 90
            r = 15
            d.ellipse((x - r, y - r, x + r, y + r), fill=mix(GREEN, out * min(1, (t - 0.9) * 2)))
    appear(d, t, 1.7, "不需要網際網路", 1270, 76, GREEN, out)
    appear(d, t, 3.1, "不經過第三方伺服器", 1390, 76, GREEN, out)


def s4(d, t, out):
    chrome(d, out)
    appear(d, t, 0.05, "這些裝置都能互傳", 500, 84, INK, out)
    names = ["Windows", "macOS", "Linux", "Android", "iOS"]
    for i, n in enumerate(names):
        st = 0.45 + i * 0.42
        e = ease(t, st) * out
        y = 680 + i * 150
        x0 = 240 + (1 - ease(t, st)) * 50
        d.rounded_rectangle((x0, y - 58, x0 + 600, y + 58), 26, fill=mix(PANEL, e))
        d.ellipse((x0 + 40, y - 14, x0 + 68, y + 14), fill=mix(GREEN, e))
        d.text((x0 + 105, y), n, font=font(66), fill=mix(INK, e), anchor="lm")


def s5(d, t, out):
    chrome(d, out)
    cx, cy = W // 2, 760
    e = ease(t, 0.05, 0.5) * out
    d.arc((cx - 80, cy - 190, cx + 80, cy - 30), 180, 360, fill=mix(GREEN, e), width=26)
    d.rectangle((cx - 80, cy - 112, cx - 54, cy - 50), fill=mix(GREEN, e))
    d.rectangle((cx + 54, cy - 112, cx + 80, cy - 50), fill=mix(GREEN, e))
    d.rounded_rectangle((cx - 135, cy - 55, cx + 135, cy + 145), 28, fill=mix(GREEN, e))
    d.ellipse((cx - 26, cy + 18, cx + 26, cy + 70), fill=mix(BG, e))
    appear(d, t, 0.7, "HTTPS 加密傳輸", 1050, 96, INK, out)
    appear(d, t, 1.5, "檔案只在你的裝置之間移動", 1190, 62, MUTED, out)


def s6(d, t, out):
    chrome(d, out)
    appear(d, t, 0.05, "小提醒", 540, 62, GREEN, out)
    appear(d, t, 0.4, "它沒有自動更新", 680, 92, INK, out)
    appear(d, t, 2.0, "建議從 App Store", 830, 68, MUTED, out)
    appear(d, t, 2.5, "或套件管理器安裝", 930, 68, MUTED, out)
    appear(d, t, 4.7, "追蹤我", 1170, 104, GREEN, out)
    appear(d, t, 5.2, "每週更新好用的開源專案", 1300, 70, INK, out)


SCENES = [(s1, 3.5), (s2, 4.95), (s3, 5.5), (s4, 5.7), (s5, 4.8), (s6, 8.2)]


def frame(fn, t, dur, last):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    out = 1 if last else min(1, (dur - t) / 0.2)
    if last:
        out = min(1, (dur - t) / 0.45)
    fn(d, t, max(0, out))
    return img


def test():
    os.makedirs("test", exist_ok=True)
    picks = [(0, 3.0), (1, 3.0), (2, 4.8), (3, 4.5), (4, 3.2), (5, 4.5)]
    sheet = Image.new("RGB", (W // 3 * 6, H // 3), (60, 60, 60))
    for n, (i, t) in enumerate(picks):
        fn, dur = SCENES[i]
        im = frame(fn, t, dur, i == len(SCENES) - 1)
        sheet.paste(im.resize((W // 3 - 4, H // 3)), (n * W // 3, 0))
    sheet.save("test/sheet.png")


def render():
    os.makedirs("scenes", exist_ok=True)
    files = []
    for i, (fn, dur) in enumerate(SCENES):
        out, tmp = f"scenes/s{i}.mp4", f"scenes/s{i}.tmp.mp4"
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                              "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                              "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
        for f in range(round(dur * FPS)):
            p.stdin.write(frame(fn, f / FPS, dur, i == len(SCENES) - 1).tobytes())
        p.stdin.close()
        if p.wait() != 0:
            sys.exit(f"scene {i} failed")
        os.replace(tmp, out)
        files.append(out)
    with open("scenes/list.txt", "w") as fh:
        fh.writelines(f"file 's{i}.mp4'\n" for i in range(len(files)))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "scenes/list.txt",
                    "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest", "-c:v", "copy", "-c:a", "aac",
                    "-movflags", "+faststart", "localsend_short.mp4"], check=True)


if __name__ == "__main__":
    test() if "--test" in sys.argv else render()
