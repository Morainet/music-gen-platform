import io

from app.engines.base import MusicEngine, ProgressFn


class MusicGenEngine(MusicEngine):
    """基于 audiocraft 的 MusicGen 引擎（轨道 A 临时引擎）。"""

    def __init__(self, model_name: str):
        super().__init__(model_name)
        self._model = None
        self._sr = 32000

    def load(self) -> None:
        from audiocraft.models import MusicGen
        # model_name 形如 musicgen-medium -> facebook/musicgen-medium
        repo = f"facebook/{self.model_name}"
        self._model = MusicGen.get_pretrained(repo)
        self._sr = self._model.sample_rate

    def generate(self, prompt: str, params: dict, on_progress: ProgressFn) -> bytes:
        import torchaudio

        on_progress(5)
        self._model.set_generation_params(
            duration=params.get("duration", 10),
            temperature=params.get("temperature", 1.0),
            top_k=params.get("top_k", 250),
            top_p=params.get("top_p", 0.0),
            cfg_coef=params.get("cfg_coef", 3.0),
        )

        # audiocraft 提供生成进度回调（generated, total）
        def _cb(generated: int, total: int):
            if total:
                on_progress(5 + int(90 * generated / total))

        self._model.set_custom_progress_callback(_cb)

        wav = self._model.generate([prompt])  # [1, channels, samples]
        on_progress(96)

        buf = io.BytesIO()
        torchaudio.save(buf, wav[0].cpu(), self._sr, format="wav")
        on_progress(99)
        return buf.getvalue()

    @property
    def sample_rate(self) -> int:
        return self._sr
