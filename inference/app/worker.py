import json
import logging

import pika

from app.config import settings
from app.engines import build_engine
from app.storage import ensure_bucket, put_audio
from app.progress import publish, is_cancelled, clear_cancel
from app.postprocess.audio import normalize_loudness

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("worker")

# 模型常驻显存：启动时加载一次默认引擎
_engines = {}


class Cancelled(Exception):
    """任务被平台层取消。"""


def _get_engine(model_name: str):
    if model_name not in _engines:
        log.info("loading engine: %s", model_name)
        eng = build_engine(model_name)
        eng.load()
        _engines[model_name] = eng
    return _engines[model_name]


def _handle(task: dict) -> None:
    """处理单个任务，失败时抛出异常交由上层决定重试。"""
    task_id = task["taskId"]
    model_name = task.get("model", settings.default_model)

    # 排队期间可能已被取消
    if is_cancelled(task_id):
        raise Cancelled()

    publish(task_id, "RUNNING", 0)
    engine = _get_engine(model_name)

    def on_progress(p: int) -> None:
        if is_cancelled(task_id):  # 生成途中被取消
            raise Cancelled()
        publish(task_id, "RUNNING", p)

    audio = engine.generate(
        task["prompt"],
        task.get("params", {}),
        on_progress=on_progress,
    )
    if settings.normalize_loudness:
        audio = normalize_loudness(audio, settings.target_lufs)
    url = put_audio(task_id, audio)
    publish(task_id, "SUCCEEDED", 100, audio_url=url)
    log.info("task %s done -> %s", task_id, url)


def main() -> None:
    ensure_bucket()
    # 预热默认引擎
    _get_engine(settings.default_model)

    params = pika.URLParameters(settings.rabbitmq_url)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    ch.queue_declare(queue=settings.task_queue, durable=True)
    ch.basic_qos(prefetch_count=1)

    def _retry_count(properties) -> int:
        headers = properties.headers or {}
        return int(headers.get("x-retry", 0))

    def _republish(channel, body, retry: int) -> None:
        channel.basic_publish(
            exchange="",
            routing_key=settings.task_queue,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=2,  # 持久化
                headers={"x-retry": retry},
            ),
        )

    def on_message(channel, method, properties, body):
        retry = _retry_count(properties)
        task = None
        try:
            task = json.loads(body)
            _handle(task)
        except Cancelled:
            task_id = (task or {}).get("taskId", "?")
            log.info("task %s cancelled", task_id)
            if task_id != "?":
                publish(task_id, "CANCELED", 0)
                clear_cancel(task_id)
        except Exception as e:  # noqa: BLE001
            task_id = (task or {}).get("taskId", "?")
            if retry < settings.max_retries:
                log.warning("task %s failed (retry %d/%d): %s",
                            task_id, retry + 1, settings.max_retries, e)
                _republish(channel, body, retry + 1)
            else:
                log.exception("task %s failed, retries exhausted", task_id)
                if task_id != "?":
                    publish(task_id, "FAILED", 0, error=str(e))
        finally:
            channel.basic_ack(delivery_tag=method.delivery_tag)

    ch.basic_consume(queue=settings.task_queue, on_message_callback=on_message)
    log.info("worker started, waiting for tasks on %s", settings.task_queue)
    ch.start_consuming()


if __name__ == "__main__":
    main()
