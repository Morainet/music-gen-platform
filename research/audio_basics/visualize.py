"""波形与梅尔频谱可视化。"""
import matplotlib

matplotlib.use("Agg")  # 无显示环境下也能存图
import matplotlib.pyplot as plt
import torch


def plot_waveform(wav: torch.Tensor, sr: int, path: str) -> None:
    t = torch.arange(wav.numel()) / sr
    plt.figure(figsize=(10, 3))
    plt.plot(t.numpy(), wav.numpy(), linewidth=0.5)
    plt.xlabel("time (s)")
    plt.ylabel("amplitude")
    plt.title("waveform")
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()


def plot_mel(mel_db: torch.Tensor, path: str) -> None:
    plt.figure(figsize=(10, 3))
    plt.imshow(mel_db.numpy(), origin="lower", aspect="auto", cmap="magma")
    plt.xlabel("frame")
    plt.ylabel("mel bin")
    plt.title("mel-spectrogram (dB)")
    plt.colorbar(format="%+2.0f dB")
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()
