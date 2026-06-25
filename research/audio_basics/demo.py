"""第 1 层 demo：音频 → 梅尔频谱 → 重建，可视化 + 打印压缩比。

用法:
    python -m audio_basics.demo path/to/audio.wav [--outdir audio_basics/out]
"""
import argparse
import os

from audio_basics.audio_io import load_audio, save_audio
from audio_basics.spectrogram import wav_to_mel, mel_to_wav, compression_ratio
from audio_basics.visualize import plot_waveform, plot_mel


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("audio", help="输入音频路径（wav/mp3/flac）")
    parser.add_argument("--outdir", default="audio_basics/out")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    # 1. 加载并标准化
    wav, sr = load_audio(args.audio)
    print(f"加载: {args.audio}")
    print(f"采样率: {sr} Hz, 时长: {wav.numel() / sr:.2f}s, 采样点数: {wav.numel()}")

    # 2. 波形 → 梅尔频谱
    mel = wav_to_mel(wav, sr)
    print(f"梅尔频谱形状: {tuple(mel.shape)} (n_mels, frames)")
    print(f"压缩比(采样点/频谱元素): {compression_ratio(wav.numel(), mel):.1f}x")

    # 3. 可视化
    plot_waveform(wav, sr, os.path.join(args.outdir, "waveform.png"))
    plot_mel(mel, os.path.join(args.outdir, "mel.png"))

    # 4. 梅尔频谱 → 重建波形（Griffin-Lim）
    print("Griffin-Lim 重建中…")
    recon = mel_to_wav(mel, sr)
    save_audio(os.path.join(args.outdir, "reconstructed.wav"), recon, sr)

    print(f"完成，产物在 {args.outdir}/")
    print("对比 reconstructed.wav 与原音频：梅尔丢了相位，Griffin-Lim 只能近似，"
          "音质有损 —— 这正是引出第 2 层神经 codec 的动机。")


if __name__ == "__main__":
    main()
