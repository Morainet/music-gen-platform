"""文本到音乐生成，带 classifier-free guidance。

每步同时算"有文本条件"和"无条件(空文本)"的 logits，按
    guided = uncond + cfg * (cond - uncond)
组合后采样。cfg 越大越贴合文本、但多样性下降。

用法:
    python -m audio_lm.generate_text \
        --lm audio_lm/ckpt/lm_text.pt --codec audio_codec/ckpt/codec.pt \
        --prompt "calm piano, relaxing" --frames 300 --cfg 3.0
"""
import argparse

import torch
import torch.nn.functional as F
import torchaudio

from audio_codec.encode_decode import load_model as load_codec
from audio_lm.conditional import ConditionalAudioLM
from audio_lm.delay import revert_delay_pattern
from audio_lm.text_encoder import T5TextEncoder


def load_lm(path: str, device: str):
    ckpt = torch.load(path, map_location=device)
    c = ckpt["config"]
    model = ConditionalAudioLM(
        num_codes=c["num_codes"],
        num_quantizers=c["num_quantizers"],
        text_dim=c["text_dim"],
        d_model=c["d_model"],
        n_head=c["n_head"],
        n_layer=c["n_layer"],
        max_len=c["max_len"],
    ).to(device)
    model.load_state_dict(ckpt["model"])
    model.eval()
    return model, c["t5"]


def sample(logits: torch.Tensor, temperature: float, top_k: int) -> torch.Tensor:
    logits = logits / max(temperature, 1e-5)
    if top_k > 0:
        v, _ = torch.topk(logits, top_k, dim=-1)
        logits[logits < v[..., [-1]]] = -float("inf")
    probs = F.softmax(logits, dim=-1)
    b, nq, vocab = probs.shape
    return torch.multinomial(probs.reshape(-1, vocab), 1).reshape(b, nq)


@torch.no_grad()
def generate(model, text_enc, prompt, frames, cfg, temperature, top_k, device):
    nq = model.nq
    steps = frames + nq - 1

    cond_emb, cond_mask = text_enc.encode([prompt])
    uncond_emb, uncond_mask = text_enc.encode([""])

    seq = torch.full((1, nq, 1), model.pad, dtype=torch.long, device=device)
    for _ in range(steps):
        logits_c = model(seq, cond_emb, cond_mask)[:, :, -1, :]
        logits_u = model(seq, uncond_emb, uncond_mask)[:, :, -1, :]
        guided = logits_u + cfg * (logits_c - logits_u)
        nxt = sample(guided, temperature, top_k)
        seq = torch.cat([seq, nxt.unsqueeze(-1)], dim=-1)

    codes = revert_delay_pattern(seq[:, :, 1:], nq)
    return codes.clamp(max=model.pad - 1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lm", required=True)
    p.add_argument("--codec", required=True)
    p.add_argument("--prompt", required=True)
    p.add_argument("--frames", type=int, default=300)
    p.add_argument("--cfg", type=float, default=3.0)
    p.add_argument("--temperature", type=float, default=1.0)
    p.add_argument("--top-k", type=int, default=250)
    p.add_argument("--out", default="audio_lm/generated_text.wav")
    args = p.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, t5_name = load_lm(args.lm, device)
    text_enc = T5TextEncoder(t5_name, device=device)
    codec, cfg = load_codec(args.codec, device)
    sr = cfg["sr"]

    print(f'prompt: "{args.prompt}" | cfg={args.cfg}')
    codes = generate(
        model, text_enc, args.prompt, args.frames, args.cfg,
        args.temperature, args.top_k, device,
    )
    wav = codec.decode(codes)
    torchaudio.save(args.out, wav[0].cpu().clamp(-1, 1), sr)
    print(f"已保存: {args.out}")


if __name__ == "__main__":
    main()
