"""用训练好的 codec 把音频目录预编码成 token 缓存。

训练 Transformer 时直接读 token，无需每步重新编码音频，大幅加速。

用法:
    python -m audio_lm.prepare_tokens \
        --codec audio_codec/ckpt/codec.pt --data path/to/audio_dir \
        --out audio_lm/tokens.pt
"""
import argparse
import glob
import os

import torch
import torchaudio

from audio_codec.encode_decode import load_model
from audio_codec.dataset import AUDIO_EXTS


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--codec", required=True, help="codec checkpoint")
    p.add_argument("--data", required=True, help="音频目录")
    p.add_argument("--out", default="audio_lm/tokens.pt")
    args = p.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, cfg = load_model(args.codec, device)
    sr, hop = cfg["sr"], 2 ** cfg["n_down"]

    files = [
        f
        for f in glob.glob(os.path.join(args.data, "**", "*"), recursive=True)
        if f.lower().endswith(AUDIO_EXTS)
    ]
    print(f"待编码: {len(files)} 个文件")

    items = []
    for i, f in enumerate(files):
        wav, in_sr = torchaudio.load(f)
        if wav.size(0) > 1:
            wav = wav.mean(0, keepdim=True)
        if in_sr != sr:
            wav = torchaudio.transforms.Resample(in_sr, sr)(wav)
        L = (wav.size(-1) // hop) * hop
        if L < hop:
            continue
        wav = wav[..., :L].unsqueeze(0).to(device)  # [1,1,L]
        tokens = model.encode(wav)[0].cpu()  # [Nq, T]
        items.append(tokens)
        if (i + 1) % 50 == 0:
            print(f"  {i + 1}/{len(files)}")

    payload = {
        "tokens": items,
        "num_codes": cfg["num_codes"],
        "num_quantizers": cfg["num_quantizers"],
        "sr": sr,
        "hop": hop,
    }
    torch.save(payload, args.out)
    print(f"已保存 {len(items)} 条 token 序列 → {args.out}")


if __name__ == "__main__":
    main()
