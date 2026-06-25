"""训练 VQ-VAE 音频 codec。

用法:
    python -m audio_codec.train --data path/to/audio_dir --epochs 50

产物:
    audio_codec/ckpt/codec.pt        最新 checkpoint（含超参）
    audio_codec/ckpt/sample_*.wav    定期保存的重建样本（对比训练进度）
"""
import argparse
import os

import torch
import torchaudio
from torch.utils.data import DataLoader

from audio_codec.dataset import AudioFolderDataset
from audio_codec.losses import reconstruction_loss
from audio_codec.model import VQVAE


def parse_args():
    p = argparse.ArgumentParser()
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
    return p.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"device: {device}")

    ds = AudioFolderDataset(args.data, segment_len=args.segment, sr=args.sr)
    dl = DataLoader(ds, batch_size=args.batch, shuffle=True, num_workers=4, drop_last=True)
    print(f"数据集: {len(ds)} 个文件")

    model = VQVAE(
        dim=args.dim,
        num_codes=args.codes,
        num_quantizers=args.quantizers,
        n_down=args.n_down,
    ).to(device)
    print(f"下采样倍数 hop={model.hop}, token 帧率≈{args.sr // model.hop} Hz/码本")

    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)

    for epoch in range(1, args.epochs + 1):
        model.train()
        running = {"recon": 0.0, "vq": 0.0, "usage": 0.0}
        for wav in dl:
            wav = wav.to(device)
            recon, indices, vq_loss = model(wav)
            recon_loss = reconstruction_loss(recon, wav)
            loss = recon_loss + vq_loss

            opt.zero_grad()
            loss.backward()
            opt.step()

            running["recon"] += recon_loss.item()
            running["vq"] += vq_loss.item()
            running["usage"] += indices[:, 0, :].unique().numel() / args.codes

        n = len(dl)
        print(
            f"epoch {epoch:3d} | recon {running['recon']/n:.4f} "
            f"| vq {running['vq']/n:.4f} "
            f"| 码本利用率(第1层) {running['usage']/n:.2%}"
        )

        if epoch % args.save_every == 0 or epoch == args.epochs:
            ckpt = {
                "model": model.state_dict(),
                "config": {
                    "dim": args.dim,
                    "num_codes": args.codes,
                    "num_quantizers": args.quantizers,
                    "n_down": args.n_down,
                    "sr": args.sr,
                },
            }
            torch.save(ckpt, os.path.join(args.outdir, "codec.pt"))
            # 存一个重建样本
            model.eval()
            with torch.no_grad():
                sample = next(iter(dl))[:1].to(device)
                rec, _, _ = model(sample)
            torchaudio.save(
                os.path.join(args.outdir, f"sample_e{epoch}.wav"),
                rec[0].cpu().clamp(-1, 1),
                args.sr,
            )
            print(f"  已保存 checkpoint 与重建样本 (epoch {epoch})")


if __name__ == "__main__":
    main()
