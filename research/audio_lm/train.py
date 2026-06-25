"""训练自回归 Transformer（audio LM）。

流程：token 窗口 → 加 delay pattern → teacher forcing（输入 = 序列[:-1]，
目标 = 序列[1:]）→ 各码本头交叉熵（忽略 pad 位）。

用法:
    python -m audio_lm.train --tokens audio_lm/tokens.pt --epochs 100
"""
import argparse
import os

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from audio_lm.dataset import TokenDataset
from audio_lm.delay import apply_delay_pattern
from audio_lm.transformer import AudioLM


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--tokens", required=True, help="prepare_tokens 产出的缓存")
    p.add_argument("--epochs", type=int, default=100)
    p.add_argument("--batch", type=int, default=16)
    p.add_argument("--frames", type=int, default=300, help="每个样本的 token 帧数")
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--d-model", type=int, default=512)
    p.add_argument("--n-head", type=int, default=8)
    p.add_argument("--n-layer", type=int, default=8)
    p.add_argument("--outdir", default="audio_lm/ckpt")
    p.add_argument("--save-every", type=int, default=10)
    return p.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"device: {device}")

    ds = TokenDataset(args.tokens, frames=args.frames)
    dl = DataLoader(ds, batch_size=args.batch, shuffle=True, num_workers=2, drop_last=True)
    nq = ds.meta["num_quantizers"]
    num_codes = ds.meta["num_codes"]
    print(f"数据: {len(ds)} 条 | Nq={nq} | num_codes={num_codes}")

    # delay 后序列长度 = frames + nq - 1
    max_len = args.frames + nq + 8
    model = AudioLM(
        num_codes=num_codes,
        num_quantizers=nq,
        d_model=args.d_model,
        n_head=args.n_head,
        n_layer=args.n_layer,
        max_len=max_len,
    ).to(device)
    pad = model.pad
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)

    for epoch in range(1, args.epochs + 1):
        model.train()
        running = 0.0
        for codes in dl:  # [B, Nq, frames]
            codes = codes.to(device)
            seq = apply_delay_pattern(codes, pad)  # [B, Nq, S]
            inp = seq[:, :, :-1]
            target = seq[:, :, 1:]

            logits = model(inp)  # [B, Nq, S-1, V]
            loss = F.cross_entropy(
                logits.reshape(-1, model.vocab),
                target.reshape(-1),
                ignore_index=pad,
            )

            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            running += loss.item()

        print(f"epoch {epoch:3d} | loss {running / len(dl):.4f}")

        if epoch % args.save_every == 0 or epoch == args.epochs:
            torch.save(
                {
                    "model": model.state_dict(),
                    "config": {
                        "num_codes": num_codes,
                        "num_quantizers": nq,
                        "d_model": args.d_model,
                        "n_head": args.n_head,
                        "n_layer": args.n_layer,
                        "max_len": max_len,
                    },
                },
                os.path.join(args.outdir, "lm.pt"),
            )
            print(f"  已保存 checkpoint (epoch {epoch})")


if __name__ == "__main__":
    main()
