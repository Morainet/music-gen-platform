"""加载训练好的 codec，把一段音频编码成离散 token 并打印，再解码重建。

用法:
    python -m audio_codec.encode_decode --ckpt audio_codec/ckpt/codec.pt --audio in.wav

这一步直观展示「音频 → 离散 token 序列」——正是第 3 层自回归
Transformer 的输入形态。
"""
import argparse

import torch
import torchaudio

from audio_codec.model import VQVAE


def load_model(ckpt_path: str, device: str) -> VQVAE:
    ckpt = torch.load(ckpt_path, map_location=device)
    cfg = ckpt["config"]
    model = VQVAE(
        dim=cfg["dim"],
        num_codes=cfg["num_codes"],
        num_quantizers=cfg["num_quantizers"],
        n_down=cfg["n_down"],
    ).to(device)
    model.load_state_dict(ckpt["model"])
    model.eval()
    return model, cfg


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ckpt", required=True)
    p.add_argument("--audio", required=True)
    p.add_argument("--out", default="audio_codec/recon.wav")
    args = p.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, cfg = load_model(args.ckpt, device)
    sr = cfg["sr"]

    wav, in_sr = torchaudio.load(args.audio)
    if wav.size(0) > 1:
        wav = wav.mean(0, keepdim=True)
    if in_sr != sr:
        wav = torchaudio.transforms.Resample(in_sr, sr)(wav)
    # 对齐到 hop 的整数倍
    hop = model.hop
    L = (wav.size(-1) // hop) * hop
    wav = wav[..., :L].unsqueeze(0).to(device)  # [1,1,L]

    # 编码 → token
    tokens = model.encode(wav)  # [1, Nq, T]
    nq, t = tokens.size(1), tokens.size(2)
    print(f"音频时长: {L / sr:.2f}s")
    print(f"token 形状: [{nq} 码本, {t} 帧]  (帧率≈{sr // hop} Hz)")
    print(f"压缩: {L} 采样点 → {nq * t} 个 token")
    print(f"第 1 个码本前 20 个 token: {tokens[0, 0, :20].tolist()}")

    # 解码 → 重建
    recon = model.decode(tokens)
    torchaudio.save(args.out, recon[0].cpu().clamp(-1, 1), sr)
    print(f"重建音频已保存: {args.out}")


if __name__ == "__main__":
    main()
