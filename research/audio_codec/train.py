"""训练 VQ-VAE 音频 codec。

用法:
    python -m audio_codec.train --data path/to/audio_dir --epochs 50

产物:
    audio_codec/ckpt/codec.pt        最新 checkpoint（含超参）
    audio_codec/ckpt/sample_*.wav    定期保存的重建样本（对比训练进度）
"""
import argparse
import os
import time

import torch
import torchaudio
from torch.utils.data import DataLoader

from audio_codec.dataset import AudioFolderDataset
from audio_codec.losses import reconstruction_loss
from audio_codec.model import VQVAE
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
    p.add_argument("--data", required=True, help="音频目录")
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--batch", type=int, default=16)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--sr", type=int, default=32000)
    p.add_argument("--segment", type=int, default=32000, help="片段采样点数(需被 hop 整除)")
    p.add_argument("--dim", type=int, default=128)
    p.add_argument("--codes", type=int, default=1024)
    p.add_argument("--quantizers", type=int, default=4)
    p.add_argument("--n-down", type=int, default=5)
    p.add_argument("--outdir", default="audio_codec/ckpt")
    p.add_argument("--save-every", type=int, default=5)
    p.add_argument("--resume", action="store_true", help="从 outdir 下的 checkpoint 续训")
    p.add_argument("--no-amp", action="store_true", help="禁用 CUDA 混合精度")
    return p.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    device = resolve_device(args.device)
    setup_training_env(device)
    print(f"device: {describe_device(device)}")

    ds = AudioFolderDataset(args.data, segment_len=args.segment, sr=args.sr)
    dl = DataLoader(
        ds, batch_size=args.batch, shuffle=True, drop_last=True,
        **dataloader_kwargs(device, 4),
    )
    print(f"数据集: {len(ds)} 个文件")

    model = VQVAE(
        dim=args.dim,
        num_codes=args.codes,
        num_quantizers=args.quantizers,
        n_down=args.n_down,
    ).to(device)
    print(f"下采样倍数 hop={model.hop}, token 帧率≈{args.sr // model.hop} Hz/码本")

    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)
    amp = Amp(device, enabled=not args.no_amp)

    config = {
        "dim": args.dim,
        "num_codes": args.codes,
        "num_quantizers": args.quantizers,
        "n_down": args.n_down,
        "sr": args.sr,
    }
    ckpt_path = os.path.join(args.outdir, "codec.pt")

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
    diverged = False
    try:
        for epoch in range(start_epoch, args.epochs + 1):
            model.train()
            running = {"recon": 0.0, "vq": 0.0, "usage": 0.0}
            t0 = time.time()
            for wav in dl:
                wav = wav.to(device, non_blocking=True)
                opt.zero_grad(set_to_none=True)
                with amp.autocast():
                    recon, indices, vq_loss = model(wav)
                # STFT 不支持 fp16，重建损失在 fp32 下计算
                recon_loss = reconstruction_loss(recon.float(), wav)
                loss = recon_loss + vq_loss.float()
                # NaN 守卫：一旦发散立即停训，绝不用坏权重覆盖已保存的 checkpoint
                if not torch.isfinite(loss):
                    print(f"  ⚠ 检测到非有限 loss，停训（保留上一个 checkpoint）")
                    diverged = True
                    break
                amp.step(loss, opt, model.parameters(), clip=1.0)

                running["recon"] += recon_loss.item()
                running["vq"] += vq_loss.item()
                running["usage"] += indices[:, 0, :].unique().numel() / args.codes

            if diverged:
                break

            n = len(dl)
            dt = time.time() - t0
            print(
                f"epoch {epoch:3d} | recon {running['recon']/n:.4f} "
                f"| vq {running['vq']/n:.4f} "
                f"| 码本利用率(第1层) {running['usage']/n:.2%} "
                f"| {n / dt:.1f} it/s"
            )

            if epoch % args.save_every == 0 or epoch == args.epochs:
                save(epoch)
                # 存一个重建样本
                model.eval()
                with torch.no_grad():
                    sample = next(iter(dl))[:1].to(device)
                    rec, _, _ = model(sample)
                torchaudio.save(
                    os.path.join(args.outdir, f"sample_e{epoch}.wav"),
                    rec[0].float().cpu().clamp(-1, 1),
                    args.sr,
                )
                print(f"  已保存重建样本 (epoch {epoch})")
    except KeyboardInterrupt:
        print("\n训练中断，保存当前进度…")
        if epoch >= start_epoch:
            save(epoch)


if __name__ == "__main__":
    main()
