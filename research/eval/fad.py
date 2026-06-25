"""Fréchet Audio Distance（FAD）。

把真实音频集和生成音频集各自嵌入成向量，分别拟合一个高斯分布
（均值 μ、协方差 Σ），再算两个高斯之间的 Fréchet 距离：

    FAD = ||μr - μg||^2 + Tr(Σr + Σg - 2 (Σr Σg)^{1/2})

值越小，生成分布越接近真实分布。嵌入用 CLAP 音频编码器（也可换 VGGish）。
"""
import numpy as np
from scipy import linalg


def gaussian_stats(emb: np.ndarray):
    """emb [N, D] → (mu [D], sigma [D, D])"""
    mu = emb.mean(axis=0)
    sigma = np.cov(emb, rowvar=False)
    return mu, sigma


def frechet_distance(emb_real: np.ndarray, emb_gen: np.ndarray, eps: float = 1e-6) -> float:
    mu_r, sig_r = gaussian_stats(emb_real)
    mu_g, sig_g = gaussian_stats(emb_gen)

    diff = mu_r - mu_g
    covmean, _ = linalg.sqrtm(sig_r @ sig_g, disp=False)

    # 数值稳定：加微小对角扰动后重算
    if not np.isfinite(covmean).all():
        offset = np.eye(sig_r.shape[0]) * eps
        covmean = linalg.sqrtm((sig_r + offset) @ (sig_g + offset))

    if np.iscomplexobj(covmean):
        covmean = covmean.real

    return float(diff @ diff + np.trace(sig_r + sig_g - 2.0 * covmean))
