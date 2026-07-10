"""基于 HuggingFace transformers 的 MusicGen 引擎。

用 facebook/musicgen-* 预训练模型做真实的文本条件音乐生成，替代原先依赖
audiocraft 的实现（audiocraft 在新 Python 上不易安装）。
"""
import io
import logging
import os

from app.engines.base import MusicEngine, ProgressFn

log = logging.getLogger("engine.musicgen")


class MusicGenEngine(MusicEngine):
    def __init__(self, model_name: str):
        super().__init__(model_name)
        self._model = None
        self._processor = None
        self._device = "cpu"
        self._sr = 32000

    def load(self) -> None:
        import torch
        from transformers import AutoProcessor, MusicgenForConditionalGeneration

        # 部分算子在 MPS 上没实现，允许回退到 CPU
        os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

        repo = (
            self.model_name
            if self.model_name.startswith("facebook/")
            else f"facebook/{self.model_name}"
        )
        self._processor = AutoProcessor.from_pretrained(repo)
        self._model = MusicgenForConditionalGeneration.from_pretrained(repo)

        if torch.backends.mps.is_available():
            self._device = "mps"
        elif torch.cuda.is_available():
            self._device = "cuda"
        else:
            self._device = "cpu"
        self._model.to(self._device).eval()
        self._sr = self._model.config.audio_encoder.sampling_rate
        log.info("MusicGen(%s) loaded on %s, sr=%d", repo, self._device, self._sr)

    def generate(self, prompt: str, params: dict, on_progress: ProgressFn) -> bytes:
        import numpy as np
        import soundfile as sf
        import torch

        on_progress(5)
        inputs = self._processor(
            text=[prompt], padding=True, return_tensors="pt"
        ).to(self._device)

        duration = float(params.get("duration", 8))
        max_new_tokens = int(duration * 50)  # MusicGen ≈ 50 token/s
        on_progress(10)

        with torch.no_grad():
            audio = self._model.generate(
                **inputs,
                do_sample=True,
                guidance_scale=float(params.get("cfg_coef", 3.0)),
                temperature=float(params.get("temperature", 1.0)),
                max_new_tokens=max_new_tokens,
            )
        on_progress(95)

        wav = audio[0, 0].cpu().numpy().astype(np.float32)  # [samples]
        buf = io.BytesIO()
        sf.write(buf, wav, self._sr, format="WAV", subtype="PCM_16")
        on_progress(99)
        return buf.getvalue()

    @property
    def sample_rate(self) -> int:
        return self._sr
