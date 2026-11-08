#!/usr/bin/env python3
"""Generate one narration wav per scene and record the durations."""
import json, os, sys
import sherpa_onnx
import soundfile as sf

MODEL = os.path.expanduser(sys.argv[1])
LINES = json.loads(sys.argv[2])
OUT = sys.argv[3]
cfg = sherpa_onnx.OfflineTtsConfig(
    model=sherpa_onnx.OfflineTtsModelConfig(
        vits=sherpa_onnx.OfflineTtsVitsModelConfig(
            model=f"{MODEL}/model.onnx", lexicon=f"{MODEL}/lexicon.txt",
            tokens=f"{MODEL}/tokens.txt", dict_dir=f"{MODEL}/dict"),
        num_threads=4),
    rule_fsts=f"{MODEL}/date.fst,{MODEL}/phone.fst,{MODEL}/number.fst,{MODEL}/new_heteronym.fst",
)
tts = sherpa_onnx.OfflineTts(cfg)
print("speakers", tts.num_speakers, "rate", tts.sample_rate)
os.makedirs(OUT, exist_ok=True)
out = []
for i, line in enumerate(LINES):
    a = tts.generate(line, sid=0, speed=1.08)
    path = f"{OUT}/v{i}.wav"
    sf.write(path, a.samples, a.sample_rate)
    out.append(len(a.samples) / a.sample_rate)
    print(i, round(out[-1], 2), line)
json.dump(out, open(f"{OUT}/durations.json", "w"))
