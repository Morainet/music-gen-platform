"""CLAP 封装：音频/文本嵌入到同一空间，用于 CLAP score 和 FAD。

CLAP（Contrastive Language-Audio Pretraining）把音频和文本对齐到同一向量空间，
余弦相似度即可衡量"这段音频和这句描述有多匹配"。
模型需要 48kHz 单声道输入，封装内部统一重采样。
"""
import torch
import torch.nn.functional as F
import torchaudio

CLAP_SR = 48000


class Clap:
    def __init__(self, name: str = "laion/clap-htsat-unfused", device: str = "cpu"):
        from transformers import ClapModel, ClapProcessor

        self.model = ClapModel.from_pretrained(name).to(device).eval()
        self.processor = ClapProcessor.from_pretrained(name)
        self.device = device

    @torch.no_grad()
    def embed_audio(self, wavs: list[torch.Tensor], sr: int) -> torch.Tensor:
        """wavs: list of 1D 波形(同一 sr) → 归一化嵌入 [N, D]"""
        arrs = []
        for w in wavs:
            if sr != CLAP_SR:
                w = torchaudio.functional.resample(w, sr, CLAP_SR)
            arrs.append(w.cpu().numpy())
        inputs = self.processor(
            audios=arrs, sampling_rate=CLAP_SR, return_tensors="pt", padding=True
        ).to(self.device)
        emb = self.model.get_audio_features(**inputs)
        return F.normalize(emb, dim=-1)

    @torch.no_grad()
    def embed_text(self, texts: list[str]) -> torch.Tensor:
        inputs = self.processor(text=texts, return_tensors="pt", padding=True).to(
            self.device
        )
        emb = self.model.get_text_features(**inputs)
        return F.normalize(emb, dim=-1)

    @torch.no_grad()
    def score(self, wavs: list[torch.Tensor], sr: int, texts: list[str]) -> torch.Tensor:
        """逐对 (音频, 文本) 的余弦相似度 [N]（已归一化，点积即余弦）。"""
        a = self.embed_audio(wavs, sr)
        t = self.embed_text(texts)
        return (a * t).sum(-1)
