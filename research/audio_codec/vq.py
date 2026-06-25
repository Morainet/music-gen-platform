"""矢量量化：把连续向量映射到离散码本，这是音频 token 化的核心。

VectorQuantizer  —— 单码本（VQ-VAE 论文）
ResidualVQ       —— 残差多码本（SoundStream/EnCodec），逐级逼近、提升重建

关键技巧：直通估计（straight-through）。argmin 不可导，
前向用量化值、反向把梯度直接拷给编码器输出，使整个网络可端到端训练。
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class VectorQuantizer(nn.Module):
    def __init__(self, num_codes: int, dim: int, commitment: float = 0.25):
        super().__init__()
        self.num_codes = num_codes
        self.dim = dim
        self.commitment = commitment
        self.codebook = nn.Embedding(num_codes, dim)
        self.codebook.weight.data.uniform_(-1.0 / num_codes, 1.0 / num_codes)

    def forward(self, z: torch.Tensor):
        """z: [B, D, T] → (z_q [B, D, T], indices [B, T], loss)"""
        b, d, t = z.shape
        z_e = z.permute(0, 2, 1).reshape(-1, d)  # [B*T, D]

        # 到每个码字的欧氏距离平方，取最近
        dist = (
            z_e.pow(2).sum(1, keepdim=True)
            - 2 * z_e @ self.codebook.weight.t()
            + self.codebook.weight.pow(2).sum(1)
        )
        idx = dist.argmin(1)  # [B*T]
        z_q = self.codebook(idx)  # [B*T, D]

        # 码本损失（拉码字靠近编码）+ commitment 损失（拉编码靠近码字）
        codebook_loss = F.mse_loss(z_q, z_e.detach())
        commit_loss = F.mse_loss(z_e, z_q.detach())
        loss = codebook_loss + self.commitment * commit_loss

        # 直通估计：前向用 z_q，反向梯度走 z_e
        z_q = z_e + (z_q - z_e).detach()

        z_q = z_q.reshape(b, t, d).permute(0, 2, 1)  # [B, D, T]
        return z_q, idx.reshape(b, t), loss

    def codebook_usage(self, idx: torch.Tensor) -> float:
        """被用到的码字占比，用于诊断码本坍缩（死码）。"""
        return idx.unique().numel() / self.num_codes


class ResidualVQ(nn.Module):
    """多层 VQ，每层量化上一层的残差。tokens 形状 [B, num_quantizers, T]。"""

    def __init__(
        self,
        num_quantizers: int,
        num_codes: int,
        dim: int,
        commitment: float = 0.25,
    ):
        super().__init__()
        self.layers = nn.ModuleList(
            [VectorQuantizer(num_codes, dim, commitment) for _ in range(num_quantizers)]
        )

    def forward(self, z: torch.Tensor):
        residual = z
        z_q_total = torch.zeros_like(z)
        indices = []
        loss_total = z.new_zeros(())
        for vq in self.layers:
            z_q, idx, loss = vq(residual)
            residual = residual - z_q
            z_q_total = z_q_total + z_q
            indices.append(idx)
            loss_total = loss_total + loss
        indices = torch.stack(indices, dim=1)  # [B, Nq, T]
        return z_q_total, indices, loss_total / len(self.layers)

    def from_indices(self, indices: torch.Tensor) -> torch.Tensor:
        """tokens [B, Nq, T] → 量化向量 [B, D, T]，供解码用。"""
        z = None
        for i, vq in enumerate(self.layers):
            emb = vq.codebook(indices[:, i, :])  # [B, T, D]
            z = emb if z is None else z + emb
        return z.permute(0, 2, 1)
