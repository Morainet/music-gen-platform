"""文本编码器：用预训练 T5 把文本 prompt 编码成序列嵌入。

输出 [B, L, d_text] + padding mask，供条件模型 cross-attention 使用。
空字符串 "" 的编码即 classifier-free guidance 的 null 条件。
"""
import torch


class T5TextEncoder:
    def __init__(self, name: str = "t5-base", device: str = "cpu"):
        from transformers import AutoTokenizer, T5EncoderModel

        self.tokenizer = AutoTokenizer.from_pretrained(name)
        self.model = T5EncoderModel.from_pretrained(name).to(device).eval()
        for p in self.model.parameters():  # 冻结，不训练文本编码器
            p.requires_grad_(False)
        self.device = device
        self.dim = self.model.config.d_model

    @torch.no_grad()
    def encode(self, texts: list[str], max_length: int = 64):
        """texts → (emb [B, L, d_text], mask [B, L] 1=有效)"""
        batch = self.tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=max_length,
        ).to(self.device)
        emb = self.model(**batch).last_hidden_state
        return emb, batch["attention_mask"]
