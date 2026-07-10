"""轨道 B 自研模型引擎：VQ-VAE codec + 自回归 Transformer。

复用 research/ 下的模型代码与训练好的 checkpoint。当前 LM 为**无条件**模型
（不吃 prompt），且受 max_len 限制，单次最多约 300 帧（≈0.4s），故按时长
分块生成后拼接。

环境变量（可选）：
    CUSTOM_CODEC  codec checkpoint 路径（默认 research/audio_codec/ckpt/codec.pt）
    CUSTOM_LM     LM checkpoint 路径（默认 research/audio_lm/ckpt/lm.pt）
    CUSTOM_DEVICE auto/cuda/mps/cpu（默认 auto）
"""
import io
import logging
import os
import sys

from app.engines.base import MusicEngine, ProgressFn

log = logging.getLogger("engine.custom")

# 让推理层能 import 轨道 B 的模型代码（audio_lm / audio_codec / device_util）
_RESEARCH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "research")
)
if _RESEARCH not in sys.path:
    sys.path.insert(0, _RESEARCH)


class CustomEngine(MusicEngine):
    def __init__(self, model_name: str):
        super().__init__(model_name)
        self._sr = 22050
        self._hop = 32
        self._max_frames = 300
        self._lm = None
        self._codec = None
        self._device = None

    def load(self) -> None:
        from audio_codec.encode_decode import load_model as load_codec
        from audio_lm.generate import load_lm
        from device_util import describe_device, resolve_device, setup_training_env

        codec_path = os.environ.get(
            "CUSTOM_CODEC", os.path.join(_RESEARCH, "audio_codec/ckpt/codec.pt")
        )
        lm_path = os.environ.get(
            "CUSTOM_LM", os.path.join(_RESEARCH, "audio_lm/ckpt/lm.pt")
        )
        device = resolve_device(os.environ.get("CUSTOM_DEVICE", "auto"))
        setup_training_env(device)
        self._device = device

        self._lm = load_lm(lm_path, str(device))
        self._codec, cfg = load_codec(codec_path, str(device))
        self._sr = cfg["sr"]
        self._hop = 2 ** cfg["n_down"]
        # 单次生成帧数上限：forward 输入长度需 ≤ max_len
        self._max_frames = max(1, self._lm.max_len - self._lm.nq - 1)
        log.info(
            "custom engine loaded on %s | sr=%d hop=%d max_frames=%d",
            describe_device(device), self._sr, self._hop, self._max_frames,
        )

    def generate(self, prompt: str, params: dict, on_progress: ProgressFn) -> bytes:
        import numpy as np
        import soundfile as sf

        from audio_lm.generate import generate_tokens

        duration = float(params.get("duration", 5))
        # 采样偏保守：过高的 temperature/top_k 会明显增加噪声
        temperature = float(params.get("temperature", 0.9))
        top_k = int(params.get("top_k", 80))

        total_frames = max(1, round(duration * self._sr / self._hop))
        chunks = []
        done = 0
        while done < total_frames:
            n = min(self._max_frames, total_frames - done)
            codes = generate_tokens(self._lm, n, str(self._device), temperature, top_k)
            wav = self._codec.decode(codes)  # [1,1,L]
            chunks.append(wav[0].detach().cpu())  # [1, L]
            done += n
            on_progress(min(99, int(done / total_frames * 100)))

        # 分块拼接：相邻块间做短交叉淡化，消除接缝的咔哒声
        fade = int(0.012 * self._sr)  # ≈12ms
        audio = self._concat_crossfade(chunks, fade).clamp(-1, 1)  # [1, L]
        data = audio.squeeze(0).numpy().astype(np.float32)  # [L] 单声道

        buf = io.BytesIO()
        sf.write(buf, data, self._sr, format="WAV", subtype="PCM_16")
        return buf.getvalue()

    @staticmethod
    def _concat_crossfade(chunks: list, fade: int):
        import torch

        if len(chunks) == 1:
            return chunks[0]
        out = chunks[0]
        for nxt in chunks[1:]:
            f = min(fade, out.size(-1), nxt.size(-1))
            if f <= 0:
                out = torch.cat([out, nxt], dim=-1)
                continue
            ramp = torch.linspace(1.0, 0.0, f)
            blended = out[:, -f:] * ramp + nxt[:, :f] * (1.0 - ramp)
            out = torch.cat([out[:, :-f], blended, nxt[:, f:]], dim=-1)
        return out

    @property
    def sample_rate(self) -> int:
        return self._sr
