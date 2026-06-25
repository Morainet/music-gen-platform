import json

import redis

from app.config import settings

_redis = redis.from_url(settings.redis_url)


def publish(task_id: str, status: str, progress: int = 0,
            audio_url: str | None = None, error: str | None = None) -> None:
    """向 Redis 频道发布进度/结果，平台层订阅后推送到前端。"""
    msg = {"taskId": task_id, "status": status, "progress": progress}
    if audio_url is not None:
        msg["audioUrl"] = audio_url
    if error is not None:
        msg["errorMsg"] = error
    _redis.publish(settings.progress_channel, json.dumps(msg))


def is_cancelled(task_id: str) -> bool:
    """平台层取消任务时会写 cancel:{taskId}，worker 据此中止。"""
    return _redis.get(f"cancel:{task_id}") is not None


def clear_cancel(task_id: str) -> None:
    _redis.delete(f"cancel:{task_id}")
