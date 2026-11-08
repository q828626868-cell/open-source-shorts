#!/usr/bin/env python3
"""Synthesize original background music, duck it under narration, write mix.wav."""
import json, sys
import numpy as np
import soundfile as sf

SR = 44100
OFFSET = 0.2
scene = json.loads(sys.argv[1])
total = sum(scene)
n = int(total * SR)
rng = np.random.default_rng(7)

BPM = int(sys.argv[2]) if len(sys.argv) > 2 else 92
KEY = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
beat = 60 / BPM
CHORDS = [[261.63, 329.63, 392.00, 493.88], [220.00, 261.63, 329.63, 392.00],
          [174.61, 261.63, 349.23, 440.00], [196.00, 246.94, 293.66, 392.00]]
music = np.zeros(n)


def add(sig, start):
    i = int(start * SR)
    if i >= n:
        return
    m = min(len(sig), n - i)
    music[i:i + m] += sig[:m]


def tone(f, dur, level, decay):
    t = np.arange(int(dur * SR)) / SR
    wave = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)
    env = np.minimum(1, t / 0.015) * np.exp(-t * decay)
    return level * wave * env


bar = 0
while bar * 4 * beat < total:
    start = bar * 4 * beat
    chord = [f * KEY for f in CHORDS[bar % 4]]
    for f in chord:
        add(tone(f, 4 * beat, 0.09, 0.45), start)
    add(tone(chord[0] / 2, 4 * beat, 0.26, 0.7), start)
    for s, idx in enumerate([0, 2, 1, 3, 2, 1, 3, 2]):
        add(tone(chord[idx] * 2, beat, 0.07, 4.5), start + s * beat / 2)
    for b in range(4):
        tb = start + b * beat
        if b % 2 == 0:
            t = np.arange(int(0.22 * SR)) / SR
            add(0.32 * np.sin(2 * np.pi * (46 + 70 * np.exp(-t * 30)) * t) * np.exp(-t * 16), tb)
        hat = rng.normal(0, 1, int(0.05 * SR))
        hat = np.diff(hat, prepend=0) * np.exp(-np.arange(len(hat)) / SR * 90)
        add(0.03 * hat, tb + beat / 2)
    bar += 1

music /= np.max(np.abs(music))
voice = np.zeros(n)
at = 0.0
for i, dur in enumerate(scene):
    v, sr = sf.read(f"voice/v{i}.wav")
    assert sr == SR
    v = v / np.max(np.abs(v)) * 0.85
    s = int((at + OFFSET) * SR)
    m = min(len(v), n - s)
    voice[s:s + m] += v[:m]
    at += dur

win = int(0.25 * SR)
active = np.convolve((np.abs(voice) > 0.01).astype(float), np.ones(win) / win, mode="same")
active = np.clip(active * 4, 0, 1)
gain = 0.34 - 0.21 * active
fade = np.minimum(1, np.minimum(np.arange(n) / (0.4 * SR), (n - np.arange(n)) / (0.9 * SR)))
mix = voice + music * gain * fade
mix = mix / max(1, np.max(np.abs(mix)) / 0.95)
sf.write("mix.wav", mix, SR)
print("seconds", round(total, 2), "peak", round(float(np.max(np.abs(mix))), 3))
