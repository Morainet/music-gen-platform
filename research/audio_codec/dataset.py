"""音频文件夹数据集：递归扫描音频，随机裁剪固定长度片段。"""
import glob
import os
import random

import torch
import torch.nn.functional as F
import torchaudio
from torch.utils.data import Dataset

AUDIO_EXTS = (".wav", ".flac", ".mp3", ".ogg")


class AudioFolderDataset(Dataset):
    def __init__(self, root: str, segment_len: int = 32000, sr: int = 32000):
        self.files = [
            p
            for p in glob.glob(os.path.join(root, "**", "*"), recursive=True)
            if p.lower().endswith(AUDIO_EXTS)
        ]
        if not self.files:
            raise RuntimeError(f"{root} 下没有找到音频文件")
        self.segment_len = segment_len
        self.sr = sr

    def __len__(self) -> int:
        return len(self.files)

    def __getitem__(self, i: int) -> torch.Tensor:
        wav, sr = torchaudio.load(self.files[i])
        if wav.size(0) > 1:  # 单声道化
            wav = wav.mean(0, keepdim=True)
        if sr != self.sr:
            wav = torchaudio.transforms.Resample(sr, self.sr)(wav)
        wav = wav.squeeze(0)

        n = wav.numel()
        if n < self.segment_len:  # 补零
            wav = F.pad(wav, (0, self.segment_len - n))
        else:  # 随机裁剪
            start = random.randint(0, n - self.segment_len)
            wav = wav[start : start + self.segment_len]

        return wav.unsqueeze(0)  # [1, L]
