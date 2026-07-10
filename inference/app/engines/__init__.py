from app.config import settings
from app.engines.base import MusicEngine


def build_engine(model_name: str) -> MusicEngine:
    """按模型名构造引擎。"""
    # 轨道 B 自研模型：始终用真实引擎，不受 MOCK_ENGINE 影响
    if model_name.startswith("mgp-custom") or model_name.startswith("custom"):
        from app.engines.custom import CustomEngine
        return CustomEngine(model_name)
    if settings.mock_engine:
        from app.engines.mock import MockEngine
        return MockEngine(model_name)
    if model_name.startswith("musicgen"):
        from app.engines.musicgen import MusicGenEngine
        return MusicGenEngine(model_name)
    raise ValueError(f"unknown model: {model_name}")
