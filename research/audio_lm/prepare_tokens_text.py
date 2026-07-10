"""读 manifest（音频 + caption），用 codec 预编码成 (token, caption) 缓存。

manifest 为 JSONL，每行：
    {"audio_path": "clips/0001.wav", "caption": "calm piano, relaxing"}

用法:
    python -m audio_lm.prepare_tokens_text \
        --codec audio_codec/ckpt/codec.pt --manifest data/musiccaps.jsonl \
        --out audio_lm/tokens_text.pt
"""
import argparse
import json
import os

import torch
import torchaudio

from audio_codec.encode_decode import load_model
from device_util import add_device_arg, describe_device, resolve_device, setup_training_env


def main():
    p = argparse.ArgumentParser()
    add_device_arg(p)
    p.add_argument("--codec", required=True)
    p.add_argument("--manifest", required=True, help="JSONL：audio_path + caption")
    p.add_argument("--root", default="", help="audio_path 的相对根目录")
    p.add_argument("--out", default="audio_lm/tokens_text.pt")
    args = p.parse_args()

    device = resolve_device(args.device)
    setup_training_env(device)
    print(f"device: {describe_device(device)}")
    model, cfg = load_model(args.codec, str(device))
    sr, hop = cfg["sr"], 2 ** cfg["n_down"]

    rows = []
    with open(args.manifest, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    print(f"manifest 条目: {len(rows)}")

    items = []
    for i, row in enumerate(rows):
        path = os.path.join(args.root, row["audio_path"])
        caption = row.get("caption", "")
        if not os.path.exists(path):
            continue
        wav, in_sr = torchaudio.load(path)
        if wav.size(0) > 1:
            wav = wav.mean(0, keepdim=True)
        if in_sr != sr:
            wav = torchaudio.transforms.Resample(in_sr, sr)(wav)
        L = (wav.size(-1) // hop) * hop
        if L < hop:
            continue
        wav = wav[..., :L].unsqueeze(0).to(device)
        tokens = model.encode(wav)[0].cpu()  # [Nq, T]
        items.append({"tokens": tokens, "caption": caption})
        if (i + 1) % 50 == 0:
            print(f"  {i + 1}/{len(rows)}")

    payload = {
        "items": items,
        "num_codes": cfg["num_codes"],
        "num_quantizers": cfg["num_quantizers"],
        "sr": sr,
        "hop": hop,
    }
    torch.save(payload, args.out)
    print(f"已保存 {len(items)} 条 (token, caption) → {args.out}")


if __name__ == "__main__":
    main()
