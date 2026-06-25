"""音频加载与标准化：重采样、单声道化。"""
import torch
import torchaudio

TARGET_SR = 32000  # 对齐后续 codec / MusicGen


def load_audio(path: str, target_sr: int = TARGET_SR) -> tuple[torch.Tensor, int]:
    """加载音频并标准化为单声道、目标采样率。

    返回 (wav, sr)，wav 形状 [samples]，取值约 [-1, 1]。
    """
    wav, sr = torchaudio.load(path)  # [channels, samples]

    # 单声道化：多声道取均值
    if wav.size(0) > 1:
        wav = wav.mean(dim=0, keepdim=True)

    # 重采样到目标采样率
    if sr != target_sr:
        wav = torchaudio.transforms.Resample(sr, target_sr)(wav)
        sr = target_sr

    return wav.squeeze(0), sr


def save_audio(path: str, wav: torch.Tensor, sr: int) -> None:
    """保存音频。wav 形状 [samples] 或 [channels, samples]。"""
    if wav.dim() == 1:
        wav = wav.unsqueeze(0)
    torchaudio.save(path, wav.cpu(), sr)
