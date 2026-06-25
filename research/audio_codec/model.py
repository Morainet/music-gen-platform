"""波形域 VQ-VAE：1D 卷积编码器 + RVQ 瓶颈 + 1D 卷积解码器。

结构参考 SoundStream/EnCodec 的极简版：
- 编码器用 stride=2 卷积逐级下采样，把波形压成 [B, D, T]
- RVQ 把每帧向量量化成离散 token
- 解码器用 ConvTranspose 逐级上采样还原波形

下采样总倍数 hop = 2 ** len(strides)。输入长度需能被 hop 整除。
"""
import torch
import torch.nn as nn

from audio_codec.vq import ResidualVQ


class ResBlock(nn.Module):
    def __init__(self, ch: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.ELU(),
            nn.Conv1d(ch, ch, 3, padding=1),
            nn.ELU(),
            nn.Conv1d(ch, ch, 1),
        )

    def forward(self, x):
        return x + self.net(x)


class Encoder(nn.Module):
    def __init__(self, dim: int, base_ch: int = 32, n_down: int = 5, max_ch: int = 512):
        super().__init__()
        layers: list[nn.Module] = [nn.Conv1d(1, base_ch, 7, padding=3)]
        ch = base_ch
        for _ in range(n_down):
            out = min(ch * 2, max_ch)
            layers += [
                ResBlock(ch),
                nn.ELU(),
                nn.Conv1d(ch, out, kernel_size=4, stride=2, padding=1),  # 长度减半
            ]
            ch = out
        layers += [nn.ELU(), nn.Conv1d(ch, dim, 3, padding=1)]
        self.net = nn.Sequential(*layers)

    def forward(self, x):  # [B,1,L] → [B,dim,T]
        return self.net(x)


class Decoder(nn.Module):
    def __init__(self, dim: int, base_ch: int = 32, n_down: int = 5, max_ch: int = 512):
        super().__init__()
        # 镜像编码器的通道序列
        chs = [base_ch]
        ch = base_ch
        for _ in range(n_down):
            ch = min(ch * 2, max_ch)
            chs.append(ch)
        chs = chs[::-1]  # 从最深通道往回

        layers: list[nn.Module] = [nn.Conv1d(dim, chs[0], 3, padding=1)]
        for i in range(n_down):
            in_ch, out_ch = chs[i], chs[i + 1]
            layers += [
                ResBlock(in_ch),
                nn.ELU(),
                nn.ConvTranspose1d(in_ch, out_ch, kernel_size=4, stride=2, padding=1),  # 长度翻倍
            ]
        layers += [nn.ELU(), nn.Conv1d(chs[-1], 1, 7, padding=3), nn.Tanh()]
        self.net = nn.Sequential(*layers)

    def forward(self, z):  # [B,dim,T] → [B,1,L]
        return self.net(z)


class VQVAE(nn.Module):
    def __init__(
        self,
        dim: int = 128,
        num_codes: int = 1024,
        num_quantizers: int = 4,
        base_ch: int = 32,
        n_down: int = 5,
        commitment: float = 0.25,
    ):
        super().__init__()
        self.hop = 2 ** n_down
        self.encoder = Encoder(dim, base_ch, n_down)
        self.rvq = ResidualVQ(num_quantizers, num_codes, dim, commitment)
        self.decoder = Decoder(dim, base_ch, n_down)

    def forward(self, wav: torch.Tensor):
        """wav [B,1,L] → (recon [B,1,L], indices [B,Nq,T], vq_loss)"""
        z = self.encoder(wav)
        z_q, indices, vq_loss = self.rvq(z)
        recon = self.decoder(z_q)
        return recon, indices, vq_loss

    @torch.no_grad()
    def encode(self, wav: torch.Tensor) -> torch.Tensor:
        """wav [B,1,L] → tokens [B,Nq,T]"""
        z = self.encoder(wav)
        _, indices, _ = self.rvq(z)
        return indices

    @torch.no_grad()
    def decode(self, indices: torch.Tensor) -> torch.Tensor:
        """tokens [B,Nq,T] → wav [B,1,L]"""
        z_q = self.rvq.from_indices(indices)
        return self.decoder(z_q)
