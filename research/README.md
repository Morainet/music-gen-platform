# 算法研究工作区（轨道 B）

从零研究音乐生成算法。与平台（轨道 A）解耦，独立迭代。路线见 `../docs/02-算法研究路线.md`。

## 环境

```bash
cd research
python -m venv .venv && source .venv/bin/activate
# NVIDIA：按 docs/04 装匹配 CUDA 的 torch/torchaudio
# Apple Silicon：pip install torch torchaudio（官方 wheel 已含 MPS）
pip install -r requirements.txt
```

### 计算设备

所有训练/生成/评估脚本支持 `--device`：

| 值 | 说明 |
|----|------|
| `auto` | 默认，优先级 cuda → mps → cpu |
| `cuda` | NVIDIA GPU |
| `mps` | Apple Silicon GPU |
| `cpu` | 纯 CPU（调试用，训练很慢） |

查看当前可用设备：

```bash
python -m device_util
```

示例（Mac 上用 MPS 训练 codec）：

```bash
python -m audio_codec.train --data path/to/audio --epochs 50 --device mps
```

### 训练加速与健壮性

三个训练脚本（`audio_codec.train` / `audio_lm.train` / `audio_lm.train_text`）共享以下能力：

- **混合精度**：CUDA 上自动启用 float16 autocast + GradScaler；MPS/CPU 自动跳过（透明直通）。如遇数值问题加 `--no-amp` 关闭。
- **续训**：`--resume` 从 `outdir` 下的 checkpoint 恢复模型、优化器与 epoch。
- **中断保存**：Ctrl-C 会先保存当前 epoch 的 checkpoint 再退出。
- **吞吐**：每个 epoch 打印 `it/s`；CUDA 自动开启 TF32 与 cudnn.benchmark，DataLoader 在 CUDA 上启用 pin_memory，多 worker 时复用进程。

```bash
# 续训示例
python -m audio_lm.train --tokens audio_lm/tokens.pt --epochs 200 --resume
```

## 进度

- [x] **第 1 层 音频信号基础** → `audio_basics/`
- [x] **第 2 层 神经编解码（VQ-VAE / RVQ）** → `audio_codec/` ⭐
- [x] **第 3 层 自回归 Transformer（含 delay pattern）** → `audio_lm/` ⭐
- [x] **第 4 层 文本条件（T5 + cross-attention + CFG）** → `audio_lm/*_text*`
- [x] **第 5 层 评估（FAD + CLAP score）** → `eval/`

## 第 1 层：音频信号基础

理解音频如何数字化、为什么不能直接生成原始波形。

```bash
# 准备一个音频文件（wav/mp3/flac 均可），然后：
python -m audio_basics.demo path/to/audio.wav
```

产出（默认写到 `audio_basics/out/`）：
- `waveform.png` / `mel.png` —— 波形与梅尔频谱可视化
- `reconstructed.wav` —— 梅尔频谱经 Griffin-Lim 重建的音频（对比原音频，理解有损压缩）
- 控制台打印：原始采样点数 vs 梅尔频谱帧数，直观看到压缩比

### 这一层要带走的认知
- 48kHz × 30s ≈ 144 万采样点 → 序列太长，无法直接自回归生成
- 必须先把音频压成更短的表示（频谱是手工压缩；第 2 层的神经 codec 是学习式压缩）
- 梅尔频谱丢了相位信息，Griffin-Lim 只能近似还原 → 引出更好的神经 codec

## 第 2 层：神经音频编解码（VQ-VAE / RVQ）⭐

把连续音频用神经网络压成**离散 token**、再还原。这是整条路线的地基——
搞懂"音频如何变成 token"，第 3 层的自回归生成就水到渠成。

`audio_codec/` 结构：
- `vq.py` —— `VectorQuantizer`（单码本，直通估计）+ `ResidualVQ`（残差多码本）
- `model.py` —— 1D 卷积 `Encoder`/`Decoder` + `VQVAE`（参考 SoundStream/EnCodec 极简版）
- `losses.py` —— 波形 L1 + 多分辨率 STFT 幅度损失
- `dataset.py` —— 音频文件夹数据集（随机裁剪固定片段）
- `train.py` —— 训练循环（打印 recon/vq 损失、码本利用率）
- `encode_decode.py` —— 编码成 token 并打印、再解码重建

### 训练与验证

```bash
# 训练（推荐先用 NSynth/MAESTRO 子集，4090 上够用）
python -m audio_codec.train --data path/to/audio_dir --epochs 50

# 用训练好的 codec 编码→打印 token→解码重建
python -m audio_codec.encode_decode --ckpt audio_codec/ckpt/codec.pt --audio in.wav
```

### 验收标准
- [ ] 训练 loss 下降，重建样本 `ckpt/sample_*.wav` 能听出原貌
- [ ] 码本利用率合理（不要大量死码 → 否则调 commitment / 重置码本）
- [ ] `encode_decode` 能打印出一段音频的 token 序列（第 3 层的输入形态）

### 这一层要带走的认知
- **VQ 直通估计**：argmin 不可导，前向用量化值、反向把梯度拷给编码器，使端到端可训
- **RVQ**：多码本逐级量化残差，用更多 token 换更高保真
- token 帧率 = 采样率 / hop（hop = 2^下采样层数）——决定序列长度与压缩比
- 这里产出的 token，就是第 3 层 Transformer 要逐个预测的"音频词"

## 第 3 层：自回归 Transformer（含 delay pattern）⭐

在第 2 层的 token 上训练一个 GPT 式模型，像语言模型一样逐 token 生成音乐。

`audio_lm/` 结构：
- `transformer.py` —— `AudioLM`：decoder-only Transformer，多码本各一张词嵌入表 +
  Nq 个并行预测头（单码本时退化为标准 GPT）
- `delay.py` —— **delay pattern**：第 k 个码本右移 k 步的交错/还原（MusicGen 关键）
- `prepare_tokens.py` —— 用 codec 把音频预编码成 token 缓存（加速训练）
- `dataset.py` —— 从缓存随机采样固定长度 token 窗口
- `train.py` —— teacher forcing + 各码本头交叉熵（忽略 pad）
- `generate.py` —— 自回归采样（temperature/top-k）→ codec 解码出音频

### 训练与生成（需先完成第 2 层 codec）

```bash
# 1. 用 codec 预编码音频为 token 缓存
python -m audio_lm.prepare_tokens --codec audio_codec/ckpt/codec.pt \
    --data path/to/audio_dir --out audio_lm/tokens.pt

# 2. 训练 Transformer
python -m audio_lm.train --tokens audio_lm/tokens.pt --epochs 100

# 3. 自回归生成音频
python -m audio_lm.generate --lm audio_lm/ckpt/lm.pt \
    --codec audio_codec/ckpt/codec.pt --frames 300 --out audio_lm/generated.wav
```

### 验收标准
- [ ] 训练 loss 正常下降
- [ ] `generate` 能产出有音乐性（哪怕粗糙）、非纯噪声的音频
- [ ] 理解 delay pattern：为什么右移能让单一自回归流建模多码本

### 这一层要带走的认知
- **自回归生成**：给定前文 token 预测下一个，像 GPT 写文字一样"写"音频 token
- **delay pattern**：把第 k 个码本右移 k 步，使当前帧的高层码本能看到同帧已生成的低层码本，
  Nq 个并行头一次预测一帧的所有码本——这是 MusicGen 的核心创新
- **里程碑** 🎯：走到这里，你已能用全自研的 codec + Transformer 从零生成音频

### 建议入门设置
- 先用 `--quantizers 1` 训练 codec（单码本），第 3 层退化为标准 GPT，跑通整条链路最简单
- 再上多码本（如 4），体会 delay pattern 的作用

## 第 4 层：文本条件（T5 + cross-attention + CFG）

让文本 prompt 控制生成什么音乐。需要**音频-文本配对数据**（如 MusicCaps，见 `../docs/03`）。

相关文件：
- `text_encoder.py` —— 冻结的 T5 文本编码器，输出文本嵌入 + mask
- `conditional.py` —— `ConditionalAudioLM`：在第 3 层基础上每个 block 加 cross-attention 关注文本
- `prepare_tokens_text.py` —— 读 manifest（音频 + caption）预编码成 (token, caption) 缓存
- `dataset_text.py` —— 带 caption 的数据集 + collate
- `train_text.py` —— 训练，含 **CFG dropout**（随机丢弃文本条件）
- `generate_text.py` —— 文本生成，含 **classifier-free guidance**

### 数据：manifest 格式（JSONL）
```json
{"audio_path": "clips/0001.wav", "caption": "calm piano, relaxing"}
```

### 训练与生成

```bash
# 1. 预编码音频+文本（需先有 codec）
python -m audio_lm.prepare_tokens_text --codec audio_codec/ckpt/codec.pt \
    --manifest data/musiccaps.jsonl --root data --out audio_lm/tokens_text.pt

# 2. 训练条件模型（首次会下载 t5-base）
python -m audio_lm.train_text --tokens audio_lm/tokens_text.pt --epochs 100

# 3. 文本到音乐
python -m audio_lm.generate_text --lm audio_lm/ckpt/lm_text.pt \
    --codec audio_codec/ckpt/codec.pt --prompt "calm piano, relaxing" --cfg 3.0
```

### 验收标准
- [ ] 不同 prompt 能产出可区分的风格
- [ ] 调大 `--cfg` 更贴合文本（但多样性下降），理解 guidance 权衡

### 这一层要带走的认知
- **cross-attention 注入条件**：音频 token 生成时"看"文本嵌入
- **classifier-free guidance**：训练时随机丢条件让模型兼学有/无条件；生成时用
  `uncond + cfg*(cond-uncond)` 放大文本影响——无需额外分类器
- 至此具备完整的**文本 → 音乐**能力，可接回平台轨道 A 替换 MusicGen

## 第 5 层：评估（FAD + CLAP score）

生成质量没有简单的 accuracy，用两个指标量化：

`eval/` 结构：
- `clap.py` —— CLAP 封装：音频/文本嵌入到同一空间，余弦相似度打分
- `fad.py` —— **Fréchet Audio Distance** 的数学实现（μ/Σ + 矩阵平方根）
- `evaluate.py` —— CLI：对生成集算 FAD（需参考集）、对 prompt 算 CLAP score

### 两个指标
- **FAD**：生成分布 vs 真实分布的距离（越低越好）。用 CLAP 音频嵌入拟合高斯，算
  `||μr-μg||² + Tr(Σr+Σg-2(ΣrΣg)^½)`
- **CLAP score**：生成音频与文本 prompt 的余弦相似度（越高越贴合文本）

### 用法

```bash
# FAD：生成目录 vs 参考目录
python -m eval.evaluate --gen out/generated --ref data/reference

# 同时算 CLAP score（prompts 为 JSONL: {"audio_path","caption"}）
python -m eval.evaluate --gen out/generated --ref data/reference \
    --prompts out/generated/prompts.jsonl
```

### 这一层要带走的认知
- 音频生成评估靠**分布距离(FAD)** 和 **跨模态匹配(CLAP)**，而非逐样本对错
- 建立固定参考集 + prompt 集，每个 checkpoint 跑同一套横向对比，指导迭代

---

## 路线完成 🎉

第 1–5 层全部实现：从音频信号基础 → 神经 codec → 自回归 Transformer →
文本条件 → 评估，构成完整的**从零文本到音乐**研究链路。
下一步是在真实数据上训练调优，并把满意的模型接回平台（轨道 A 的 `engines/custom.py`）。
