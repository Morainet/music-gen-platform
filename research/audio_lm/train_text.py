"""训练文本条件 Transformer。

关键：classifier-free guidance 的训练侧——以一定概率把 caption 换成 ""（null 条件），
让模型同时学会"有条件"和"无条件"生成，生成时才能做引导。

用法:
    python -m audio_lm.train_text --tokens audio_lm/tokens_text.pt --epochs 100
"""
import argparse
import os
import random

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from audio_lm.dataset_text import TextTokenDataset, collate
from audio_lm.delay import apply_delay_pattern
from audio_lm.conditional import ConditionalAudioLM
from audio_lm.text_encoder import T5TextEncoder


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--tokens", required=True)
    p.add_argument("--epochs", type=int, default=100)
    p.add_argument("--batch", type=int, default=8)
    p.add_argument("--frames", type=int, default=300)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--d-model", type=int, default=512)
    p.add_argument("--n-head", type=int, default=8)
    p.add_argument("--n-layer", type=int, default=8)
    p.add_argument("--t5", default="t5-base")
    p.add_argument("--cfg-dropout", type=float, default=0.1, help="丢弃文本条件的概率")
    p.add_argument("--outdir", default="audio_lm/ckpt")
    p.add_argument("--save-every", type=int, default=10)
    return p.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"device: {device}")

    ds = TextTokenDataset(args.tokens, frames=args.frames)
    dl = DataLoader(
        ds, batch_size=args.batch, shuffle=True, num_workers=2,
        drop_last=True, collate_fn=collate,
    )
    nq = ds.meta["num_quantizers"]
    num_codes = ds.meta["num_codes"]

    text_encoder = T5TextEncoder(args.t5, device=device)
    max_len = args.frames + nq + 8
    model = ConditionalAudioLM(
        num_codes=num_codes,
        num_quantizers=nq,
        text_dim=text_encoder.dim,
        d_model=args.d_model,
        n_head=args.n_head,
        n_layer=args.n_layer,
        max_len=max_len,
    ).to(device)
    pad = model.pad
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)
    print(f"数据: {len(ds)} 条 | Nq={nq} | t5_dim={text_encoder.dim}")

    for epoch in range(1, args.epochs + 1):
        model.train()
        running = 0.0
        for codes, captions in dl:
            codes = codes.to(device)
            # CFG dropout：随机把部分 caption 置空
            captions = [
                "" if random.random() < args.cfg_dropout else c for c in captions
            ]
            text_emb, text_mask = text_encoder.encode(captions)

            seq = apply_delay_pattern(codes, pad)
            inp, target = seq[:, :, :-1], seq[:, :, 1:]
            logits = model(inp, text_emb, text_mask)
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
                        "text_dim": text_encoder.dim,
                        "d_model": args.d_model,
                        "n_head": args.n_head,
                        "n_layer": args.n_layer,
                        "max_len": max_len,
                        "t5": args.t5,
                    },
                },
                os.path.join(args.outdir, "lm_text.pt"),
            )
            print(f"  已保存 checkpoint (epoch {epoch})")


if __name__ == "__main__":
    main()
