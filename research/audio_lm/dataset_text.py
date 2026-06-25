"""带文本的 token 数据集：返回 (token 窗口, caption)。"""
import random

import torch
from torch.utils.data import Dataset


class TextTokenDataset(Dataset):
    def __init__(self, tokens_path: str, frames: int = 300):
        payload = torch.load(tokens_path, map_location="cpu")
        self.meta = {
            "num_codes": payload["num_codes"],
            "num_quantizers": payload["num_quantizers"],
            "sr": payload["sr"],
            "hop": payload["hop"],
        }
        self.items = [it for it in payload["items"] if it["tokens"].size(1) >= frames]
        if not self.items:
            raise RuntimeError(f"没有长度 >= {frames} 帧的序列")
        self.frames = frames

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, i: int):
        it = self.items[i]
        t = it["tokens"]
        start = random.randint(0, t.size(1) - self.frames)
        codes = t[:, start : start + self.frames].long()  # [Nq, frames]
        return codes, it["caption"]


def collate(batch):
    """把 (codes, caption) 列表整理成 (codes [B,Nq,frames], captions list[str])。"""
    codes = torch.stack([b[0] for b in batch], dim=0)
    captions = [b[1] for b in batch]
    return codes, captions
