# 基于 CUDA 运行时镜像，需 NVIDIA Container Toolkit + 启动时 --gpus all
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y python3 python3-pip ffmpeg git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
# 先装匹配 CUDA 的 torch，再装其余依赖
RUN pip3 install torch torchaudio --index-url https://download.pytorch.org/whl/cu121 \
    && pip3 install -r requirements.txt

COPY app ./app

# 默认跑队列 worker；如需 HTTP 健康检查可另起 uvicorn app.main:app
CMD ["python3", "-m", "app.worker"]
