"""音频后处理：响度归一化。

用 pyloudnorm 按 EBU R128 (LUFS) 归一化，统一不同生成结果的响度。
依赖缺失时安全降级（原样返回），不阻塞主链路。
"""
import io
import logging

log = logging.getLogger("postprocess")


def normalize_loudness(wav_bytes: bytes, target_lufs: float = -14.0) -> bytes:
    try:
        import numpy as np
        import soundfile as sf
        import pyloudnorm as pyln
    except ImportError:
        log.warning("pyloudnorm/soundfile 未安装，跳过响度归一化")
        return wav_bytes

    try:
        data, sr = sf.read(io.BytesIO(wav_bytes))
        meter = pyln.Meter(sr)
        loudness = meter.integrated_loudness(data)
        normalized = pyln.normalize.loudness(data, loudness, target_lufs)
        # 防削波
        peak = np.max(np.abs(normalized))
        if peak > 1.0:
            normalized = normalized / peak
        out = io.BytesIO()
        sf.write(out, normalized, sr, format="WAV")
        return out.getvalue()
    except Exception:  # noqa: BLE001
        log.exception("响度归一化失败，返回原音频")
        return wav_bytes
