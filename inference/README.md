# 推理层（Python / FastAPI + Worker）

消费 RabbitMQ 任务队列，调用模型生成音频，写 MinIO，经 Redis 上报进度。

## 本地运行

```bash
cd inference
python -m venv .venv && source .venv/bin/activate
# 先按 docs/04 装匹配 CUDA 的 torch，再装依赖
pip install -r requirements.txt
cp .env.example .env
```

先起基础设施（见 deploy/）。无 GPU 时设 `MOCK_ENGINE=true` 先调通链路。

```bash
# 启动队列 worker（核心）
python -m app.worker

# 可选：健康检查 HTTP 服务
uvicorn app.main:app --port 8001
```

## 结构
- `app/worker.py` —— 队列消费主循环，模型常驻显存
- `app/engines/` —— 引擎抽象：`base` 接口 / `musicgen` 实现 / `mock` 假引擎
- `app/storage.py` —— MinIO 上传
- `app/progress.py` —— Redis 进度发布
- `app/main.py` —— FastAPI 健康检查
