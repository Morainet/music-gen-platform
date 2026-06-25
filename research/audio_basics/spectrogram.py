"""波形 ↔ 梅尔频谱互转。

正向：波形 → 梅尔频谱（手工有损压缩，丢弃相位）。
反向：梅尔频谱 → 线性谱(InverseMelScale) → 波形(Griffin-Lim 估计相位)。

这条反向链路质量有限，正是引出第 2 层「神经 codec」的动机。
"""
import torch
import torchaudio

# STFT / 梅尔参数（音乐常用）
N_FFT = 1024
HOP_LENGTH = 256
N_MELS = 80


def wav_to_mel(wav: torch.Tensor, sr: int) -> torch.Tensor:
    """波形 [samples] → 梅尔频谱 [n_mels, frames]（对数刻度）。"""
    mel_spec = torchaudio.transforms.MelSpectrogram(
        sample_rate=sr,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH,
        n_mels=N_MELS,
        power=2.0,
    )(wav)
    # 转 dB（对数压缩动态范围，更接近听觉、便于可视化）
    return torchaudio.transforms.AmplitudeToDB(stype="power")(mel_spec)


def mel_to_wav(mel_db: torch.Tensor, sr: int, n_iter: int = 64) -> torch.Tensor:
    """梅尔频谱(dB) → 波形 [samples]（近似重建）。"""
    # dB → power
    mel_power = torchaudio.functional.DB_to_amplitude(mel_db, ref=1.0, power=1.0)

    # 梅尔谱 → 线性幅度谱
    inv_mel = torchaudio.transforms.InverseMelScale(
        n_stft=N_FFT // 2 + 1,
        n_mels=N_MELS,
        sample_rate=sr,
    )
    lin_spec = inv_mel(mel_power)

    # Griffin-Lim 迭代估计相位，重建波形
    griffin = torchaudio.transforms.GriffinLim(
        n_fft=N_FFT,
        hop_length=HOP_LENGTH,
        n_iter=n_iter,
    )
    return griffin(lin_spec)


def compression_ratio(num_samples: int, mel: torch.Tensor) -> float:
    """原始采样点数 / 梅尔频谱元素数，直观看压缩比。"""
    mel_elems = mel.numel()
    return num_samples / mel_elems if mel_elems else 0.0
