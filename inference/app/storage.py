import io

from minio import Minio

from app.config import settings

_client = Minio(
    settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=settings.minio_secure,
)


def ensure_bucket() -> None:
    if not _client.bucket_exists(settings.minio_bucket):
        _client.make_bucket(settings.minio_bucket)


def put_audio(task_id: str, data: bytes) -> str:
    """上传 wav，返回对象路径。"""
    object_name = f"{task_id}.wav"
    _client.put_object(
        settings.minio_bucket,
        object_name,
        io.BytesIO(data),
        length=len(data),
        content_type="audio/wav",
    )
    return f"{settings.minio_bucket}/{object_name}"
