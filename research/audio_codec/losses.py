"""重建损失：波形 L1 + 多分辨率 STFT 幅度损失。

只用波形 L1 重建音质差（听感模糊）；加上 STFT 幅度损失能显著改善，
这也是 SoundStream/EnCodec 等用频域损失的原因。
"""
import torch
import torch.nn.functional as F


def multi_res_stft_loss(
    recon: torch.Tensor,
    target: torch.Tensor,
    ffts=(512, 1024, 2048),
) -> torch.Tensor:
    """recon/target: [B,1,L]"""
    r = recon.squeeze(1)
    t = target.squeeze(1)
    loss = r.new_zeros(())
    for n in ffts:
        window = torch.hann_window(n, device=r.device)
        hop = n // 4
        sr = torch.stft(r, n, hop_length=hop, window=window, return_complex=True).abs()
        st = torch.stft(t, n, hop_length=hop, window=window, return_complex=True).abs()
        loss = loss + F.l1_loss(sr, st)
    return loss / len(ffts)


def reconstruction_loss(
    recon: torch.Tensor, target: torch.Tensor, stft_weight: float = 1.0
) -> torch.Tensor:
    # 对齐长度（卷积可能有微小长度差）
    n = min(recon.size(-1), target.size(-1))
    recon, target = recon[..., :n], target[..., :n]
    wav_l1 = F.l1_loss(recon, target)
    return wav_l1 + stft_weight * multi_res_stft_loss(recon, target)
