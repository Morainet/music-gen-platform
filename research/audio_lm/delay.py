"""Delay pattern（MusicGen 的关键技巧）。

RVQ 每个时间步有 Nq 个 token（多个码本）。直接同时预测它们会丢失码本间依赖。
MusicGen 的做法：把第 k 个码本整体右移 k 步，使一个自回归流配合 Nq 个并行预测头
即可建模多码本，且当前步的高层码本能看到同一帧已生成的低层码本。

延迟后序列长度 = T + Nq - 1，空出来的位置填特殊 token（pad）。
"""
import torch


def apply_delay_pattern(codes: torch.Tensor, pad: int) -> torch.Tensor:
    """codes [B, Nq, T] → delayed [B, Nq, T + Nq - 1]，第 k 个码本右移 k 步。"""
    b, nq, t = codes.shape
    s = t + nq - 1
    out = codes.new_full((b, nq, s), pad)
    for k in range(nq):
        out[:, k, k : k + t] = codes[:, k, :]
    return out


def revert_delay_pattern(delayed: torch.Tensor, nq: int) -> torch.Tensor:
    """delayed [B, Nq, S] → codes [B, Nq, T]，逆操作对齐回每帧。"""
    b, _, s = delayed.shape
    t = s - (nq - 1)
    out = delayed.new_zeros((b, nq, t))
    for k in range(nq):
        out[:, k, :] = delayed[:, k, k : k + t]
    return out
