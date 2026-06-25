from abc import ABC, abstractmethod
from typing import Callable

# 进度回调：传入 0-100 的整数
ProgressFn = Callable[[int], None]


class MusicEngine(ABC):
    """统一引擎接口。MusicGen 与未来自研模型都实现它，使平台层与模型实现解耦。

    见 docs/05-平台架构详细设计.md 第 8 节。
    """

    def __init__(self, model_name: str):
        self.model_name = model_name

    @abstractmethod
    def load(self) -> None:
        """启动时加载模型，常驻显存。"""

    @abstractmethod
    def generate(self, prompt: str, params: dict, on_progress: ProgressFn) -> bytes:
        """生成音频，返回 wav 字节。过程中调用 on_progress 上报进度。"""

    @property
    @abstractmethod
    def sample_rate(self) -> int:
        ...
