"""跨设备训练/推理的设备选择与 CLI 辅助。

支持 auto / cuda / mps / cpu。auto 优先级：cuda > mps > cpu。

用法:
    python -m device_util              # 列出当前可用设备
    python -m device_util --device mps # 验证指定设备可用
"""
from __future__ import annotations

import argparse
import contextlib
import os

import torch

VALID_CHOICES = ("auto", "cuda", "mps", "cpu")


def cuda_available() -> bool:
    return torch.cuda.is_available()


def mps_available() -> bool:
    mps = getattr(torch.backends, "mps", None)
    return mps is not None and mps.is_available()


def auto_device() -> torch.device:
    if cuda_available():
        return torch.device("cuda")
    if mps_available():
        return torch.device("mps")
    return torch.device("cpu")


def resolve_device(preference: str = "auto") -> torch.device:
    pref = preference.strip().lower()
    if pref == "auto":
        return auto_device()
    if pref == "cuda":
        if not cuda_available():
            raise RuntimeError("请求 cuda 但 torch.cuda.is_available() 为 False")
        return torch.device("cuda")
    if pref == "mps":
        if not mps_available():
            raise RuntimeError(
                "请求 mps 但 MPS 不可用（需 Apple Silicon Mac + 支持 MPS 的 PyTorch）"
            )
        return torch.device("mps")
    if pref == "cpu":
        return torch.device("cpu")
    raise ValueError(f"未知设备: {preference!r}，可选: {', '.join(VALID_CHOICES)}")


def describe_device(device: torch.device | str) -> str:
    dev = torch.device(device)
    if dev.type == "cuda":
        idx = dev.index if dev.index is not None else torch.cuda.current_device()
        return f"cuda:{idx} ({torch.cuda.get_device_name(idx)})"
    if dev.type == "mps":
        return "mps (Apple Silicon GPU)"
    return "cpu"


def add_device_arg(parser: argparse.ArgumentParser, *, default: str = "auto") -> None:
    parser.add_argument(
        "--device",
        default=default,
        choices=VALID_CHOICES,
        help="计算设备：auto=自动(cuda>mps>cpu)，或显式指定",
    )


def dataloader_workers(device: torch.device | str, requested: int) -> int:
    """MPS 上 DataLoader 多进程易与 Metal 后端冲突，自动降为 0。"""
    dev = torch.device(device)
    if dev.type == "mps" and requested > 0:
        return 0
    return requested


def dataloader_kwargs(device: torch.device | str, requested_workers: int) -> dict:
    """按设备生成 DataLoader 性能参数。

    - pin_memory 仅对 CUDA 有意义（加速 host→device 拷贝），其余设备关闭。
    - persistent_workers 仅在有 worker 时开启，省去每个 epoch 重建进程的开销。
    """
    dev = torch.device(device)
    workers = dataloader_workers(dev, requested_workers)
    kw: dict = {"num_workers": workers, "pin_memory": dev.type == "cuda"}
    if workers > 0:
        kw["persistent_workers"] = True
    return kw


def setup_training_env(device: torch.device) -> None:
    """训练前环境设置（MPS 算子回退、CUDA matmul 加速等）。"""
    if device.type == "mps":
        os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    if device.type == "cuda":
        # Ampere+ 上用 TF32 加速 matmul/卷积，对训练精度影响可忽略。
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        torch.backends.cudnn.benchmark = True


class Amp:
    """设备感知的混合精度封装。

    CUDA 上启用 float16 autocast + GradScaler；MPS/CPU 上 GradScaler(enabled=False)
    为透明直通，因此训练循环可共用同一套写法，无需按设备分支。

    用法:
        amp = Amp(device)
        for batch in dl:
            opt.zero_grad(set_to_none=True)
            with amp.autocast():
                loss = compute_loss(...)
            amp.step(loss, opt, model.parameters(), clip=1.0)
    """

    def __init__(self, device: torch.device, enabled: bool = True):
        self.device_type = device.type
        self.enabled = bool(enabled) and device.type == "cuda"
        self.scaler = torch.amp.GradScaler("cuda", enabled=self.enabled)

    def autocast(self):
        if self.enabled:
            return torch.autocast(device_type="cuda", dtype=torch.float16)
        return contextlib.nullcontext()

    def step(self, loss, optimizer, params=None, clip: float | None = None) -> None:
        """scale→backward→(可选梯度裁剪)→step→update。enabled=False 时为普通流程。"""
        self.scaler.scale(loss).backward()
        if clip is not None:
            self.scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(params, clip)
        self.scaler.step(optimizer)
        self.scaler.update()


def list_devices() -> None:
    print(f"PyTorch {torch.__version__}")
    print(f"  cuda : {'可用' if cuda_available() else '不可用'}", end="")
    if cuda_available():
        print(f" — {torch.cuda.get_device_name(0)}")
    else:
        print()
    print(f"  mps  : {'可用' if mps_available() else '不可用'}")
    print(f"  cpu  : 可用")
    print(f"  auto → {describe_device(auto_device())}")


def _cli() -> None:
    p = argparse.ArgumentParser(description="查看或验证训练设备")
    p.add_argument("--device", default="auto", choices=VALID_CHOICES)
    args = p.parse_args()
    list_devices()
    dev = resolve_device(args.device)
    print(f"  选定 → {describe_device(dev)}")


if __name__ == "__main__":
    _cli()
