"""自回归 Transformer（decoder-only，nanoGPT 风格）建模音频 token。

多码本处理：每个码本一张词嵌入表，逐帧把 Nq 个嵌入相加得到每步表示；
输出端 Nq 个并行预测头，各自预测对应码本的下一 token。
配合 delay pattern（见 delay.py），即 MusicGen 的建模方式。

单码本（Nq=1）时退化为标准 GPT。
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class CausalSelfAttention(nn.Module):
    def __init__(self, d_model: int, n_head: int, dropout: float):
        super().__init__()
        assert d_model % n_head == 0
        self.n_head = n_head
        self.qkv = nn.Linear(d_model, 3 * d_model)
        self.proj = nn.Linear(d_model, d_model)
        self.dropout = dropout

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, s, c = x.shape
        qkv = self.qkv(x).reshape(b, s, 3, self.n_head, c // self.n_head)
        q, k, v = qkv.permute(2, 0, 3, 1, 4).unbind(0)  # 各 [B, nh, S, hd]
        y = F.scaled_dot_product_attention(
            q, k, v, is_causal=True, dropout_p=self.dropout if self.training else 0.0
        )
        y = y.transpose(1, 2).reshape(b, s, c)
        return self.proj(y)


class Block(nn.Module):
    def __init__(self, d_model: int, n_head: int, dropout: float):
        super().__init__()
        self.ln1 = nn.LayerNorm(d_model)
        self.attn = CausalSelfAttention(d_model, n_head, dropout)
        self.ln2 = nn.LayerNorm(d_model)
        self.mlp = nn.Sequential(
            nn.Linear(d_model, 4 * d_model),
            nn.GELU(),
            nn.Linear(4 * d_model, d_model),
            nn.Dropout(dropout),
        )

    def forward(self, x):
        x = x + self.attn(self.ln1(x))
        x = x + self.mlp(self.ln2(x))
        return x


class AudioLM(nn.Module):
    def __init__(
        self,
        num_codes: int,
        num_quantizers: int,
        d_model: int = 512,
        n_head: int = 8,
        n_layer: int = 8,
        max_len: int = 2048,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.nq = num_quantizers
        self.pad = num_codes  # 额外 token：delay 填充 / BOS
        self.vocab = num_codes + 1
        self.max_len = max_len

        self.token_emb = nn.ModuleList(
            [nn.Embedding(self.vocab, d_model) for _ in range(num_quantizers)]
        )
        self.pos_emb = nn.Embedding(max_len, d_model)
        self.drop = nn.Dropout(dropout)
        self.blocks = nn.ModuleList(
            [Block(d_model, n_head, dropout) for _ in range(n_layer)]
        )
        self.ln_f = nn.LayerNorm(d_model)
        self.heads = nn.ModuleList(
            [nn.Linear(d_model, self.vocab) for _ in range(num_quantizers)]
        )

    def forward(self, tokens: torch.Tensor) -> torch.Tensor:
        """tokens [B, Nq, S] → logits [B, Nq, S, vocab]"""
        b, nq, s = tokens.shape
        assert s <= self.max_len, f"序列长度 {s} 超过 max_len {self.max_len}"

        x = sum(self.token_emb[k](tokens[:, k, :]) for k in range(nq))  # [B,S,d]
        pos = torch.arange(s, device=tokens.device)
        x = self.drop(x + self.pos_emb(pos))
        for blk in self.blocks:
            x = blk(x)
        x = self.ln_f(x)
        logits = torch.stack([head(x) for head in self.heads], dim=1)  # [B,Nq,S,V]
        return logits
