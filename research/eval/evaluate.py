"""评估 CLI：对生成音频算 FAD（对参考集）和 CLAP score（对文本 prompt）。

用法:
    # FAD：生成目录 vs 参考目录
    python -m eval.evaluate --gen out/generated --ref data/reference

    # 同时算 CLAP score：提供 prompts（JSONL: {"audio_path","caption"}）
    python -m eval.evaluate --gen out/generated --ref data/reference \
        --prompts out/generated/prompts.jsonl

建立固定的参考集 + prompt 集，对每个 checkpoint 跑同一套，横向对比。
"""
import argparse
import glob
import json
import os

import torch
import torchaudio

from eval.clap import Clap
from eval.fad import frechet_distance

AUDIO_EXTS = (".wav", ".flac", ".mp3", ".ogg")


def load_wavs(folder: str):
    """读目录下所有音频 → (list of 1D 波形, sr)。统一重采样到 32kHz。"""
    target_sr = 32000
    files = sorted(
        f
        for f in glob.glob(os.path.join(folder, "**", "*"), recursive=True)
        if f.lower().endswith(AUDIO_EXTS)
    )
    wavs = {}
    for f in files:
        w, sr = torchaudio.load(f)
        if w.size(0) > 1:
            w = w.mean(0, keepdim=True)
        if sr != target_sr:
            w = torchaudio.functional.resample(w, sr, target_sr)
        wavs[os.path.basename(f)] = w.squeeze(0)
    return wavs, target_sr


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--gen", required=True, help="生成音频目录")
    p.add_argument("--ref", help="参考音频目录（算 FAD 用）")
    p.add_argument("--prompts", help="JSONL：audio_path + caption（算 CLAP score 用）")
    p.add_argument("--clap", default="laion/clap-htsat-unfused")
    args = p.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    clap = Clap(args.clap, device=device)

    gen_wavs, sr = load_wavs(args.gen)
    print(f"生成音频: {len(gen_wavs)} 条")

    # ---- FAD ----
    if args.ref:
        ref_wavs, _ = load_wavs(args.ref)
        print(f"参考音频: {len(ref_wavs)} 条")
        emb_gen = clap.embed_audio(list(gen_wavs.values()), sr).cpu().numpy()
        emb_ref = clap.embed_audio(list(ref_wavs.values()), sr).cpu().numpy()
        fad = frechet_distance(emb_ref, emb_gen)
        print(f"FAD: {fad:.4f}  (越低越好)")

    # ---- CLAP score ----
    if args.prompts:
        pairs = []
        with open(args.prompts, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                name = os.path.basename(row["audio_path"])
                if name in gen_wavs:
                    pairs.append((gen_wavs[name], row["caption"]))
        if pairs:
            wavs = [w for w, _ in pairs]
            texts = [t for _, t in pairs]
            scores = clap.score(wavs, sr, texts)
            print(
                f"CLAP score: {scores.mean().item():.4f} "
                f"(越高越贴合文本, 基于 {len(pairs)} 对)"
            )
        else:
            print("prompts 中没有与生成音频匹配的文件名，跳过 CLAP score")


if __name__ == "__main__":
    main()
