from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    rabbitmq_url: str = "amqp://mgp:mgp@localhost:5672/"
    redis_url: str = "redis://localhost:6379/0"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "mgp"
    minio_secret_key: str = "mgpsecret"
    minio_bucket: str = "audio"
    minio_secure: bool = False

    task_queue: str = "gen.tasks"
    progress_channel: str = "task.progress"

    default_model: str = "musicgen-medium"
    mock_engine: bool = False

    # 响度归一化（EBU R128 LUFS）
    normalize_loudness: bool = True
    target_lufs: float = -14.0

    # 失败重试最大次数（超限标 FAILED）
    max_retries: int = 2


settings = Settings()
