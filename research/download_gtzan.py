"""通过 torchaudio 下载 GTZAN 数据集（torchaudio 内置支持）。
如果直连失败，尝试 Kaggle 镜像。
"""
import os
import sys
import subprocess

DATASET_DIR = os.path.join(os.path.dirname(__file__), "data", "gtzan")
os.makedirs(DATASET_DIR, exist_ok=True)

# 方法1：torchaudio 内置
try:
    print("方法1: 尝试 torchaudio 内置下载...")
    import torchaudio
    dataset = torchaudio.datasets.GTZAN(
        root=DATASET_DIR,
        download=True,
    )
    print(f"成功！数据集路径: {DATASET_DIR}")
    sys.exit(0)
except Exception as e:
    print(f"torchaudio 下载失败: {e}")

# 方法2: 用 huggingface hub + 镜像
try:
    print("\n方法2: 尝试 huggingface hub (镜像)...")
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    from huggingface_hub import snapshot_download
    snapshot_download(
        repo_id="marsyas/gtzan",
        repo_type="dataset",
        local_dir=DATASET_DIR,
    )
    print(f"成功！数据集路径: {DATASET_DIR}")
    sys.exit(0)
except Exception as e:
    print(f"huggingface hub 下载失败: {e}")

# 方法3: 用 kagglehub
try:
    print("\n方法3: 尝试 kagglehub...")
    import kagglehub
    path = kagglehub.dataset_download("andradaolteanu/gtzan-dataset-music-genre-classification")
    print(f"成功！数据集路径: {path}")
    sys.exit(0)
except Exception as e:
    print(f"kagglehub 下载失败: {e}")

print("\n所有方法均失败。请手动下载 GTZAN 数据集。")
print("下载地址: https://www.kaggle.com/datasets/andradaolteanu/gtzan-dataset-music-genre-classification")
print(f"解压到: {DATASET_DIR}/Data/genres_original/")
