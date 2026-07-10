"""训练自回归 Transformer（audio LM）。

流程：token 窗口 → 加 delay pattern → teacher forcing（输入 = 序列[:-1]，
目标 = 序列[1:]）→ 各码本头交叉熵（忽略 pad 位）。

用法:
    python -m audio_lm.train --tokens audio_lm/tokens.pt --epochs 100
"""
import argparse
import os
import time

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from audio_lm.dataset import TokenDataset
from audio_lm.delay import apply_delay_pattern
from audio_lm.transformer import AudioLM
from device_util import (
    Amp,
    add_device_arg,
    dataloader_kwargs,
    describe_device,
    resolve_device,
    setup_training_env,
)


def parse_args():
    p = argparse.ArgumentParser()
    add_device_arg(p)
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
    p.add_argument("--resume", action="store_true", help="从 outdir 下的 checkpoint 续训")
    p.add_argument("--no-amp", action="store_true", help="禁用 CUDA 混合精度")
    return p.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    device = resolve_device(args.device)
    setup_training_env(device)
    print(f"device: {describe_device(device)}")

    ds = TokenDataset(args.tokens, frames=args.frames)
    dl = DataLoader(
        ds, batch_size=args.batch, shuffle=True, drop_last=True,
        **dataloader_kwargs(device, 2),
    )
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
    amp = Amp(device, enabled=not args.no_amp)

    config = {
        "num_codes": num_codes,
        "num_quantizers": nq,
        "d_model": args.d_model,
        "n_head": args.n_head,
        "n_layer": args.n_layer,
        "max_len": max_len,
    }
    ckpt_path = os.path.join(args.outdir, "lm.pt")

    def save(epoch: int):
        torch.save(
            {"model": model.state_dict(), "optimizer": opt.state_dict(),
             "epoch": epoch, "config": config},
            ckpt_path,
        )
        print(f"  已保存 checkpoint (epoch {epoch})")

    start_epoch = 1
    if args.resume and os.path.exists(ckpt_path):
        ck = torch.load(ckpt_path, map_location=device)
        model.load_state_dict(ck["model"])
        if "optimizer" in ck:
            opt.load_state_dict(ck["optimizer"])
        start_epoch = ck.get("epoch", 0) + 1
        print(f"恢复训练：从 epoch {start_epoch} 继续")

    epoch = start_epoch - 1
    try:
        for epoch in range(start_epoch, args.epochs + 1):
            model.train()
            running = 0.0
            t0 = time.time()
            for codes in dl:  # [B, Nq, frames]
                codes = codes.to(device, non_blocking=True)
                seq = apply_delay_pattern(codes, pad)  # [B, Nq, S]
                inp = seq[:, :, :-1]
                target = seq[:, :, 1:]

                opt.zero_grad(set_to_none=True)
                with amp.autocast():
                    logits = model(inp)  # [B, Nq, S-1, V]
                    loss = F.cross_entropy(
                        logits.reshape(-1, model.vocab),
                        target.reshape(-1),
                        ignore_index=pad,
                    )
                amp.step(loss, opt, model.parameters(), clip=1.0)
                running += loss.item()

            dt = time.time() - t0
            print(f"epoch {epoch:3d} | loss {running / len(dl):.4f} | {len(dl) / dt:.1f} it/s")

            if epoch % args.save_every == 0 or epoch == args.epochs:
                save(epoch)
    except KeyboardInterrupt:
        print("\n训练中断，保存当前进度…")
        if epoch >= start_epoch:
            save(epoch)


if __name__ == "__main__":
    main()
