from app.config import settings
from app.engines.base import MusicEngine


def build_engine(model_name: str) -> MusicEngine:
    """按模型名构造引擎。自研模型成熟后在此分支接入 CustomEngine。"""
    if settings.mock_engine:
        from app.engines.mock import MockEngine
        return MockEngine(model_name)
    if model_name.startswith("musicgen"):
        from app.engines.musicgen import MusicGenEngine
        return MusicGenEngine(model_name)
    raise ValueError(f"unknown model: {model_name}")
