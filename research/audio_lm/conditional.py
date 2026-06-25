"""带文本条件的自回归 Transformer。

在第 3 层 `AudioLM` 基础上，每个 block 增加一层 cross-attention，
让音频 token 的生成关注文本嵌入（T5 输出）。配合 classifier-free guidance，
即 MusicGen 的文本到音乐建模方式。
"""
import torch
import torch.nn as nn
import torch.nn.functional as F

from audio_lm.transformer import CausalSelfAttention


class CrossAttention(nn.Module):
    """音频隐状态(query) 关注 文本上下文(key/value)。"""

    def __init__(self, d_model: int, n_head: int, dropout: float):
        super().__init__()
        self.n_head = n_head
        self.q = nn.Linear(d_model, d_model)
        self.kv = nn.Linear(d_model, 2 * d_model)
        self.proj = nn.Linear(d_model, d_model)
        self.dropout = dropout

    def forward(self, x: torch.Tensor, ctx: torch.Tensor, ctx_mask: torch.Tensor):
        b, s, c = x.shape
        _, lc, _ = ctx.shape
        h = self.n_head
        q = self.q(x).reshape(b, s, h, c // h).transpose(1, 2)  # [B,h,S,hd]
        kv = self.kv(ctx).reshape(b, lc, 2, h, c // h).permute(2, 0, 3, 1, 4)
        k, v = kv[0], kv[1]  # [B,h,Lc,hd]

        # 文本 padding mask → 加性 mask [B,1,1,Lc]
        attn_mask = None
        if ctx_mask is not None:
            attn_mask = torch.zeros(b, 1, 1, lc, device=x.device, dtype=q.dtype)
            attn_mask = attn_mask.masked_fill(
                ctx_mask[:, None, None, :] == 0, float("-inf")
            )

        y = F.scaled_dot_product_attention(
            q, k, v, attn_mask=attn_mask,
            dropout_p=self.dropout if self.training else 0.0,
        )
        y = y.transpose(1, 2).reshape(b, s, c)
        return self.proj(y)


class ConditionalBlock(nn.Module):
    def __init__(self, d_model: int, n_head: int, dropout: float):
        super().__init__()
        self.ln1 = nn.LayerNorm(d_model)
        self.self_attn = CausalSelfAttention(d_model, n_head, dropout)
        self.ln_x = nn.LayerNorm(d_model)
        self.cross_attn = CrossAttention(d_model, n_head, dropout)
        self.ln2 = nn.LayerNorm(d_model)
        self.mlp = nn.Sequential(
            nn.Linear(d_model, 4 * d_model),
            nn.GELU(),
            nn.Linear(4 * d_model, d_model),
            nn.Dropout(dropout),
        )

    def forward(self, x, ctx, ctx_mask):
        x = x + self.self_attn(self.ln1(x))
        x = x + self.cross_attn(self.ln_x(x), ctx, ctx_mask)
        x = x + self.mlp(self.ln2(x))
        return x


class ConditionalAudioLM(nn.Module):
    def __init__(
        self,
        num_codes: int,
        num_quantizers: int,
        text_dim: int,
        d_model: int = 512,
        n_head: int = 8,
        n_layer: int = 8,
        max_len: int = 2048,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.nq = num_quantizers
        self.pad = num_codes
        self.vocab = num_codes + 1
        self.max_len = max_len

        self.token_emb = nn.ModuleList(
            [nn.Embedding(self.vocab, d_model) for _ in range(num_quantizers)]
        )
        self.pos_emb = nn.Embedding(max_len, d_model)
        self.ctx_proj = nn.Linear(text_dim, d_model)  # 文本嵌入 → d_model
        self.drop = nn.Dropout(dropout)
        self.blocks = nn.ModuleList(
            [ConditionalBlock(d_model, n_head, dropout) for _ in range(n_layer)]
        )
        self.ln_f = nn.LayerNorm(d_model)
        self.heads = nn.ModuleList(
            [nn.Linear(d_model, self.vocab) for _ in range(num_quantizers)]
        )

    def forward(self, tokens, text_emb, text_mask):
        """tokens [B,Nq,S], text_emb [B,L,text_dim], text_mask [B,L] → logits [B,Nq,S,V]"""
        b, nq, s = tokens.shape
        x = sum(self.token_emb[k](tokens[:, k, :]) for k in range(nq))
        pos = torch.arange(s, device=tokens.device)
        x = self.drop(x + self.pos_emb(pos))

        ctx = self.ctx_proj(text_emb)
        for blk in self.blocks:
            x = blk(x, ctx, text_mask)
        x = self.ln_f(x)
        return torch.stack([head(x) for head in self.heads], dim=1)
