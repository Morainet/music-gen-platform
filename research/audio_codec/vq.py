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
    """带 EMA 码本更新与死码重启的 VQ（SoundStream/EnCodec 同款防坍缩）。

    - 码本不走梯度，用聚类分配的指数滑动平均更新（比码本 MSE 损失稳定得多）。
    - 长期无人使用的死码，用当前 batch 的随机编码向量重置，避免码本坍缩。
    编码器仍通过 commitment 损失 + 直通估计获得梯度。
    """

    def __init__(
        self,
        num_codes: int,
        dim: int,
        commitment: float = 0.25,
        decay: float = 0.99,
        eps: float = 1e-5,
        restart_threshold: float = 1.0,
    ):
        super().__init__()
        self.num_codes = num_codes
        self.dim = dim
        self.commitment = commitment
        self.decay = decay
        self.eps = eps
        self.restart_threshold = restart_threshold
        self.codebook = nn.Embedding(num_codes, dim)
        self.codebook.weight.data.uniform_(-1.0 / num_codes, 1.0 / num_codes)
        self.codebook.weight.requires_grad_(False)  # 码本用 EMA 更新，不走梯度
        self.register_buffer("cluster_size", torch.zeros(num_codes))
        self.register_buffer("embed_avg", self.codebook.weight.data.clone())

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

        if self.training:
            self._ema_update(z_e, idx)

        # 只保留 commitment 损失（拉编码靠近码字）；码本由 EMA 负责
        loss = self.commitment * F.mse_loss(z_e, z_q.detach())

        # 直通估计：前向用 z_q，反向梯度走 z_e
        z_q = z_e + (z_q - z_e).detach()

        z_q = z_q.reshape(b, t, d).permute(0, 2, 1)  # [B, D, T]
        return z_q, idx.reshape(b, t), loss

    @torch.no_grad()
    def _ema_update(self, z_e: torch.Tensor, idx: torch.Tensor) -> None:
        onehot = F.one_hot(idx, self.num_codes).type(z_e.dtype)  # [N, K]
        batch_cluster = onehot.sum(0)  # [K]
        batch_embed_sum = onehot.t() @ z_e  # [K, D]

        self.cluster_size.mul_(self.decay).add_(batch_cluster, alpha=1 - self.decay)
        self.embed_avg.mul_(self.decay).add_(batch_embed_sum, alpha=1 - self.decay)

        # Laplace 平滑，避免除零
        n = self.cluster_size.sum()
        normalized = (
            (self.cluster_size + self.eps) / (n + self.num_codes * self.eps) * n
        )
        self.codebook.weight.data.copy_(self.embed_avg / normalized.unsqueeze(1))

        self._restart_dead_codes(z_e)

    @torch.no_grad()
    def _restart_dead_codes(self, z_e: torch.Tensor) -> None:
        dead = self.cluster_size < self.restart_threshold
        n_dead = int(dead.sum())
        if n_dead == 0:
            return
        picks = torch.randint(0, z_e.size(0), (n_dead,), device=z_e.device)
        new = z_e[picks]  # 用当前 batch 的真实编码重置死码
        self.codebook.weight.data[dead] = new
        self.embed_avg[dead] = new
        self.cluster_size[dead] = 1.0

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
