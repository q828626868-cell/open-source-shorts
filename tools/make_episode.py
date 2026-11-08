#!/usr/bin/env python3
"""Build a video from an episode config. Usage: make_episode.py <ep.json> [--test]"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw
import render_short as R

ep = json.load(open(sys.argv[1]))
name = os.path.splitext(os.path.basename(sys.argv[1]))[0]
ACC = tuple(ep["accent"])
out_dir = f"episodes/{name}"
durs = json.load(open(f"{out_dir}/voice/durations.json"))
OFFSET, TAIL = 0.2, 0.5


def chrome(d, out):
    R.text(d, f"開源好物 #{ep['no']:03d}", 280, 44, ACC, out, R.MED)


def hook(d, t, out, v):
    chrome(d, out)
    R.appear(d, t, 0.05, ep["hook"][0], 690, 88, R.INK, out)
    R.appear(d, t, v * 0.32, ep["hook"][1], 880, 112, ACC, out)
    R.appear(d, t, v * 0.62, ep["hook"][2], 1040, 96, R.RED, out)


def intro(d, t, out, v):
    chrome(d, out)
    e = R.ease(t, 0.05, 0.55)
    size = 150 if len(ep["name"]) <= 10 else 128
    R.text(d, ep["name"], 760, size, ACC, e * out, slide=(1 - e) * 60)
    R.appear(d, t, v * 0.4, ep["tag"], 950, 66, R.INK, out)
    R.appear(d, t, v * 0.7, ep["url"], 1085, 44, R.BLUE, out, R.MED)


def features(d, t, out, v):
    chrome(d, out)
    R.appear(d, t, 0.05, ep["feat_title"], 500, 80, R.INK, out)
    for i, (head, sub) in enumerate(ep["features"]):
        st = 0.2 + i * v / 3
        e = R.ease(t, st) * out
        y = 760 + i * 250
        x0 = 120 + (1 - R.ease(t, st)) * 50
        d.rounded_rectangle((x0, y - 100, x0 + 840, y + 100), 30, fill=R.mix(R.PANEL, e))
        d.ellipse((x0 + 40, y - 18, x0 + 76, y + 18), fill=R.mix(ACC, e))
        d.text((x0 + 115, y - 36), head, font=R.font(66), fill=R.mix(R.INK, e), anchor="lm")
        d.text((x0 + 115, y + 44), sub, font=R.font(42, R.MED), fill=R.mix(R.MUTED, e), anchor="lm")


def cta(d, t, out, v):
    chrome(d, out)
    R.appear(d, t, 0.05, ep["tip_label"], 540, 62, ACC, out)
    R.appear(d, t, 0.35, ep["tip"][0], 690, 74, R.INK, out)
    R.appear(d, t, v * 0.22, ep["tip"][1], 820, 58, R.MUTED, out)
    R.appear(d, t, v * ep.get("cta_at", 0.55), "追蹤我", 1090, 104, ACC, out)
    R.appear(d, t, v * ep.get("cta_at", 0.55) + 0.4, "每週更新好用的開源專案", 1220, 70, R.INK, out)


FNS = [hook, intro, features, cta]
SC = [(f, durs[i] + OFFSET + TAIL, durs[i]) for i, f in enumerate(FNS)]


def frame(i, t):
    fn, dur, v = SC[i]
    img = Image.new("RGB", (R.W, R.H), R.BG)
    d = ImageDraw.Draw(img)
    last = i == len(SC) - 1
    o = min(1, (dur - t) / (0.45 if last else 0.2))
    fn(d, t, max(0, o), v)
    return img


if "--test" in sys.argv:
    sheet = Image.new("RGB", (R.W // 3 * 4, R.H // 3), (60, 60, 60))
    for i, (_, dur, _) in enumerate(SC):
        sheet.paste(frame(i, dur - 0.6).resize((R.W // 3 - 4, R.H // 3)), (i * R.W // 3, 0))
    sheet.save(f"{out_dir}/sheet.png")
    sys.exit()

os.makedirs(f"{out_dir}/scenes", exist_ok=True)
for i, (_, dur, _) in enumerate(SC):
    tmp, final = f"{out_dir}/scenes/s{i}.tmp.mp4", f"{out_dir}/scenes/s{i}.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
                          f"{R.W}x{R.H}", "-r", str(R.FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset",
                          "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for f in range(round(dur * R.FPS)):
        p.stdin.write(frame(i, f / R.FPS).tobytes())
    p.stdin.close()
    if p.wait() != 0:
        sys.exit(f"scene {i} failed")
    os.replace(tmp, final)
with open(f"{out_dir}/scenes/list.txt", "w") as fh:
    fh.writelines(f"file 's{i}.mp4'\n" for i in range(len(SC)))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{out_dir}/scenes/list.txt",
                "-c", "copy", f"{out_dir}/video.mp4"], check=True)
print(json.dumps([round(s[1], 3) for s in SC]))
