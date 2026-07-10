"""自回归生成：从 Transformer 采样 token → codec 解码成音频。

从全 pad（BOS）起步，逐列预测 delay 序列，生成够长后还原 delay pattern
得到 [Nq, T] 的 token，再交给 codec 解码出波形。

用法:
    python -m audio_lm.generate \
        --lm audio_lm/ckpt/lm.pt --codec audio_codec/ckpt/codec.pt \
        --frames 300 --out audio_lm/generated.wav
"""
import argparse

import torch
import torch.nn.functional as F
import torchaudio

from audio_codec.encode_decode import load_model as load_codec
from audio_lm.delay import revert_delay_pattern
from audio_lm.transformer import AudioLM
from device_util import add_device_arg, describe_device, resolve_device, setup_training_env


def load_lm(path: str, device: str) -> AudioLM:
    ckpt = torch.load(path, map_location=device)
    c = ckpt["config"]
    model = AudioLM(
        num_codes=c["num_codes"],
        num_quantizers=c["num_quantizers"],
        d_model=c["d_model"],
        n_head=c["n_head"],
        n_layer=c["n_layer"],
        max_len=c["max_len"],
    ).to(device)
    model.load_state_dict(ckpt["model"])
    model.eval()
    return model


def sample_logits(logits: torch.Tensor, temperature: float, top_k: int) -> torch.Tensor:
    """logits [B, Nq, V] → 采样得到 [B, Nq]"""
    logits = logits / max(temperature, 1e-5)
    if top_k > 0:
        v, _ = torch.topk(logits, top_k, dim=-1)
        logits[logits < v[..., [-1]]] = -float("inf")
    probs = F.softmax(logits, dim=-1)
    b, nq, vocab = probs.shape
    idx = torch.multinomial(probs.reshape(-1, vocab), 1).reshape(b, nq)
    return idx


@torch.no_grad()
def generate_tokens(model: AudioLM, frames: int, device: str,
                    temperature: float, top_k: int) -> torch.Tensor:
    nq = model.nq
    steps = frames + nq - 1  # delay 序列长度
    # BOS：全 pad 列
    seq = torch.full((1, nq, 1), model.pad, dtype=torch.long, device=device)
    for _ in range(steps):
        logits = model(seq)[:, :, -1, :]  # [1, Nq, V]
        nxt = sample_logits(logits, temperature, top_k)  # [1, Nq]
        seq = torch.cat([seq, nxt.unsqueeze(-1)], dim=-1)

    delayed = seq[:, :, 1:]  # 去掉 BOS → [1, Nq, steps]
    codes = revert_delay_pattern(delayed, nq)  # [1, Nq, frames]
    # 把可能采到的 pad 夹回有效范围，避免 codec 查表越界
    codes = codes.clamp(max=model.pad - 1)
    return codes


def main():
    p = argparse.ArgumentParser()
    add_device_arg(p)
    p.add_argument("--lm", required=True)
    p.add_argument("--codec", required=True)
    p.add_argument("--frames", type=int, default=300)
    p.add_argument("--temperature", type=float, default=1.0)
    p.add_argument("--top-k", type=int, default=250)
    p.add_argument("--out", default="audio_lm/generated.wav")
    args = p.parse_args()

    device = resolve_device(args.device)
    setup_training_env(device)
    print(f"device: {describe_device(device)}")
    lm = load_lm(args.lm, str(device))
    codec, cfg = load_codec(args.codec, str(device))
    sr = cfg["sr"]

    print(f"生成 {args.frames} 帧 token (≈{args.frames * (2 ** cfg['n_down']) / sr:.2f}s)…")
    codes = generate_tokens(lm, args.frames, str(device), args.temperature, args.top_k)
    print(f"token 形状: {tuple(codes.shape)}")

    wav = codec.decode(codes)  # [1,1,L]
    torchaudio.save(args.out, wav[0].cpu().clamp(-1, 1), sr)
    print(f"已保存生成音频: {args.out}")


if __name__ == "__main__":
    main()
