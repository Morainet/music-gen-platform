"""Token 数据集：从预编码缓存随机采样固定长度的 token 窗口。"""
import random

import torch
from torch.utils.data import Dataset


class TokenDataset(Dataset):
    def __init__(self, tokens_path: str, frames: int = 300):
        payload = torch.load(tokens_path, map_location="cpu")
        self.meta = {
            "num_codes": payload["num_codes"],
            "num_quantizers": payload["num_quantizers"],
            "sr": payload["sr"],
            "hop": payload["hop"],
        }
        # 只保留长度足够的序列
        self.items = [t for t in payload["tokens"] if t.size(1) >= frames]
        if not self.items:
            raise RuntimeError(
                f"没有长度 >= {frames} 帧的序列，请减小 --frames 或用更长音频"
            )
        self.frames = frames

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, i: int) -> torch.Tensor:
        t = self.items[i]  # [Nq, T]
        start = random.randint(0, t.size(1) - self.frames)
        return t[:, start : start + self.frames].long()  # [Nq, frames]
