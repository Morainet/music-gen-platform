import io
import math
import struct
import time

from app.engines.base import MusicEngine, ProgressFn


class MockEngine(MusicEngine):
    """无 GPU 时的假引擎：生成一段正弦波 wav，用于先调通整条链路。"""

    def __init__(self, model_name: str):
        super().__init__(model_name)
        self._sr = 32000

    def load(self) -> None:
        pass

    def generate(self, prompt: str, params: dict, on_progress: ProgressFn) -> bytes:
        duration = int(params.get("duration", 5))
        for p in range(0, 100, 20):
            on_progress(p)
            time.sleep(0.2)
        wav = self._sine_wav(duration)
        on_progress(99)
        return wav

    def _sine_wav(self, duration: int, freq: float = 440.0) -> bytes:
        n = self._sr * duration
        buf = io.BytesIO()
        # 最小 WAV 头 + 16bit PCM 单声道
        data = bytearray()
        for i in range(n):
            v = int(32767 * 0.3 * math.sin(2 * math.pi * freq * i / self._sr))
            data += struct.pack("<h", v)
        byte_rate = self._sr * 2
        buf.write(b"RIFF")
        buf.write(struct.pack("<I", 36 + len(data)))
        buf.write(b"WAVEfmt ")
        buf.write(struct.pack("<IHHIIHH", 16, 1, 1, self._sr, byte_rate, 2, 16))
        buf.write(b"data")
        buf.write(struct.pack("<I", len(data)))
        buf.write(data)
        return buf.getvalue()

    @property
    def sample_rate(self) -> int:
        return self._sr
