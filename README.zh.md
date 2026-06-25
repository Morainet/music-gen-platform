# AI 音乐生成平台

<!-- README-I18N:START -->

[English](./README.en.md) | **汉语**

<!-- README-I18N:END -->

一个**自部署模型 + 算法自主研究**的综合音乐生成平台：既是一套可运行的文本到音乐
Web 产品，也是一条从零实现音乐生成算法的研究代码库。

---

## 一、项目背景

### 目标
做一个文本到音乐的生成平台，输入一句描述（如 *"calm piano, relaxing"*），生成对应的音乐音频。

### 两个定位、两条轨道
本项目刻意拆成**双轨并行**，兼顾"尽快有可用产品"和"深入理解算法原理"：

- **轨道 A — 产品线**：工程上用成熟框架（Spring Boot / FastAPI / React）搭一套完整平台，
  先用现成开源模型 **MusicGen** 当引擎，快速产出可演示、可用的产品。
- **轨道 B — 研究线**：在 `research/` 下**从零实现**音乐生成算法（神经 codec + 自回归
  Transformer + 文本条件 + 评估），目标是彻底搞懂原理。成熟后把自研模型接回平台替换
  MusicGen。

两条轨道通过推理层的**引擎抽象**解耦：平台不关心模型实现，换引擎只动一个 Python 文件。

### 技术取舍
- 模型推理用 Python（PyTorch 生态），平台业务用 Java（Spring Boot），前端用 React。
- 生成耗时长 → 全程**异步队列**，削峰、可重试、可反馈进度。
- 训练与在线服务**解耦**：训练离线产出权重，推理服务加载。
- 详细的需求/可行性/架构分析见 `docs/`（按编号阅读）。

---

## 二、整体架构

```
┌─────────── 轨道 A：在线平台 ───────────────────────────────┐
│                                                            │
│  前端 (React)                                              │
│    │ HTTP / WebSocket                                      │
│  Java 平台层 (Spring Boot)   用户·任务·进度推送·不碰模型    │
│    │ RabbitMQ(任务) + Redis(进度)                          │
│  Python 推理层 (FastAPI+worker)  模型常驻显存·音频后处理    │
│    │                                                       │
│  MinIO(音频)   PostgreSQL(元数据)                          │
└────────────────────────────────────────────────────────────┘
              ▲ 自研模型权重接入（engines/custom.py）
┌─────────── 轨道 B：算法研究（research/）──────────────────┐
│  音频信号基础 → 神经codec → 自回归Transformer →            │
│  文本条件 → 评估    （从零实现，独立迭代）                  │
└────────────────────────────────────────────────────────────┘
```

---

## 三、实现介绍

### 目录结构
```
music-gen-platform/
├── docs/         设计文档（需求/可行性、算法路线、数据集、架构、训练、前端规范）
├── deploy/       基础设施 docker-compose（PostgreSQL / Redis / RabbitMQ / MinIO）
├── platform/     Java 平台层（Spring Boot 3 + Maven）
├── inference/    Python 推理层（FastAPI + 队列 worker + 引擎抽象）
├── frontend/     React 前端（Vite + TS + Tailwind，深色创作工具风）
└── research/     轨道 B：从零实现的音乐生成算法
```

### 轨道 A：平台（已实现）
- **平台层 `platform/`**：任务 CRUD、模型列表、音频流式代理、WebSocket 进度推送、
  全局异常、CORS。投递任务到 RabbitMQ，订阅 Redis 进度更新 DB 并推前端。
- **推理层 `inference/`**：消费队列 → 调引擎生成 → 响度归一化 → 写 MinIO → 回报进度。
  - 引擎抽象 `engines/base.py`：`MusicGenEngine`（真实）/ `MockEngine`（无 GPU 调链路）/
    预留 `custom.py`（轨道 B 自研模型）。
  - 失败按 `MAX_RETRIES` 重试。
- **前端 `frontend/`**：创作页（prompt + 参数预设 + 滑块）、波形播放器（wavesurfer）、
  历史页、Toast、深浅主题切换、移动端抽屉导航。

### 轨道 B：算法研究（已实现，`research/`）
从零实现的完整文本到音乐链路，每层都可独立训练/运行：

| 层 | 目录 | 内容 |
|----|------|------|
| 1 音频信号基础 | `audio_basics/` | 波形↔梅尔频谱、Griffin-Lim 重建、可视化 |
| 2 神经编解码 ⭐ | `audio_codec/` | VQ-VAE / RVQ，把音频压成离散 token |
| 3 自回归 Transformer ⭐ | `audio_lm/` | GPT 式逐 token 生成 + MusicGen 的 delay pattern |
| 4 文本条件 | `audio_lm/*_text*` | T5 文本编码 + cross-attention + classifier-free guidance |
| 5 评估 | `eval/` | FAD（分布距离）+ CLAP score（文本匹配度） |

详见 `research/README.md` 与 `docs/02-算法研究路线.md`。

---

## 四、如何使用

### A. 运行平台（轨道 A）

**前置**：Docker、JDK 17、Node 20。（无 GPU 也能跑——用 mock 引擎验证整条链路。）

**步骤 1：起基础设施**
```bash
cd deploy && cp .env.example .env && docker compose up -d
# RabbitMQ 管理台 http://localhost:15672  MinIO 控制台 http://localhost:9001
```

**步骤 2：起推理层**
```bash
cd ../inference
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # 有 GPU：先按 docs/04 装匹配 CUDA 的 torch
cp .env.example .env                      # 无 GPU：把 MOCK_ENGINE 设为 true
python -m app.worker
```

**步骤 3：起平台层**（自带 Maven Wrapper，无需全局装 Maven）
```bash
cd ../platform && ./mvnw spring-boot:run   # Windows: mvnw.cmd spring-boot:run
```

**步骤 4：起前端**
```bash
cd ../frontend && npm install && npm run dev
# 打开 http://localhost:5173，输入描述 → 生成 → 波形播放
```

**或用 curl 直接验证后端**
```bash
curl -X POST localhost:8080/api/v1/tasks \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"calm piano","model":"musicgen-medium","params":{"duration":5}}'
# 返回 taskId → GET /api/v1/tasks/{taskId} 查状态 → GET /api/v1/audio/{taskId} 取音频
```

### B. 跑算法研究（轨道 B）

**前置**：Python + 按 `docs/04` 装匹配 CUDA 的 torch（建议有 GPU，如 4090）。

```bash
cd research
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

**从零跑通文本到音乐（建议先用单码本 + 小数据集 NSynth/MAESTRO）**
```bash
# 第1层：理解音频↔频谱
python -m audio_basics.demo path/to/audio.wav

# 第2层：训练神经 codec（音频→token）
python -m audio_codec.train --data path/to/audio_dir --epochs 50 --quantizers 1
python -m audio_codec.encode_decode --ckpt audio_codec/ckpt/codec.pt --audio in.wav

# 第3层：在 token 上训练自回归 Transformer 并生成
python -m audio_lm.prepare_tokens --codec audio_codec/ckpt/codec.pt \
    --data path/to/audio_dir --out audio_lm/tokens.pt
python -m audio_lm.train --tokens audio_lm/tokens.pt --epochs 100
python -m audio_lm.generate --lm audio_lm/ckpt/lm.pt --codec audio_codec/ckpt/codec.pt

# 第4层：文本条件（需 MusicCaps 等音频-文本配对，见 docs/03）
python -m audio_lm.prepare_tokens_text --codec audio_codec/ckpt/codec.pt \
    --manifest data/musiccaps.jsonl --root data --out audio_lm/tokens_text.pt
python -m audio_lm.train_text --tokens audio_lm/tokens_text.pt --epochs 100
python -m audio_lm.generate_text --lm audio_lm/ckpt/lm_text.pt \
    --codec audio_codec/ckpt/codec.pt --prompt "calm piano, relaxing" --cfg 3.0

# 第5层：评估
python -m eval.evaluate --gen out/generated --ref data/reference --prompts prompts.jsonl
```

### C. 把自研模型接回平台
轨道 B 训练满意后，在 `inference/app/engines/custom.py` 实现统一引擎接口
（`load` / `generate` / `sample_rate`），在 `models` 表注册，前端模型下拉即可选用，
与 MusicGen 并存对比。平台层零改动。

---

## 五、当前状态

- ✅ 轨道 A：基础设施、推理层（mock/MusicGen 引擎、响度归一化、重试）、平台层
  （任务/模型/音频接口、队列、WebSocket、异常、CORS）、React 前端——代码完整，前端已构建验证。
- ✅ 轨道 B：算法第 1–5 层全部实现，语法校验通过。
- ⏳ 待办：在 GPU 上实跑训练与端到端联调；用户体系/鉴权；自研模型接入平台。

> 说明：算法代码与部分后端尚未在 GPU/真实依赖下实跑，需在配齐环境（CUDA torch、Maven、Docker）后验证。

## 六、文档索引（`docs/`）
1. 技术规范与可行性分析　2. 算法研究路线　3. 数据集调研
4. 阶段0实操清单　5. 平台架构详细设计　6. 自研模型训练方案　7. 前端设计规范与架构
