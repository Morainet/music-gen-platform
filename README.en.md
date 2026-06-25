# AI Music Generation Platform

<!-- README-I18N:START -->

**English** | [汉语](./README.zh.md)

<!-- README-I18N:END -->

A comprehensive music generation platform with **self-deployed models + independent algorithm research**: 
it is both a runnable text-to-music web product and a research codebase for implementing music 
generation algorithms from scratch.

---

## 1. Project Background

### Goal
Build a text-to-music generation platform: input a description (e.g., *"calm piano, relaxing"*) 
and generate the corresponding music audio.

### Two Positions, Two Tracks
This project is deliberately structured as **dual tracks** running in parallel, balancing 
"a usable product ASAP" with "deep understanding of algorithm principles":

- **Track A — Product Line**: Use mature frameworks (Spring Boot / FastAPI / React) to build a 
  complete platform. Start with the open-source **MusicGen** model as the engine for a quick, 
  demonstrable product.
- **Track B — Research Line**: Under `research/`, **implement music generation algorithms from scratch** 
  (neural codec + autoregressive Transformer + text conditioning + evaluation), with the goal of 
  thoroughly understanding the principles. Once mature, plug the custom model back into the platform 
  to replace MusicGen.

The two tracks are decoupled through the inference layer's **engine abstraction**: the platform 
doesn't care about model implementation — swapping engines only requires changing one Python file.

### Technical Decisions
- Model inference uses Python (PyTorch ecosystem), platform business logic uses Java (Spring Boot), 
  frontend uses React.
- Generation is time-consuming → fully **async queue**, with peak shaving, retries, and progress feedback.
- Training and online serving are **decoupled**: training produces weights offline, inference service loads them.
- For detailed requirements/feasibility/architecture analysis, see `docs/` (read by number).

---

## 2. Overall Architecture

```
┌─────────── Track A: Online Platform ──────────────────────┐
│                                                            │
│  Frontend (React)                                          │
│    │ HTTP / WebSocket                                      │
│  Java Platform (Spring Boot)  Users · Tasks · Progress    │
│    │ RabbitMQ (tasks) + Redis (progress)                  │
│  Python Inference (FastAPI + worker)  GPU-resident model   │
│    │                                                       │
│  MinIO (audio)   PostgreSQL (metadata)                    │
└────────────────────────────────────────────────────────────┘
              ▲ Custom model weights via engines/custom.py
┌─────────── Track B: Algorithm Research (research/) ───────┐
│  Audio basics → Neural codec → Autoregressive Transformer  │
│  → Text conditioning → Evaluation   (from scratch)        │
└────────────────────────────────────────────────────────────┘
```

---

## 3. Implementation Overview

### Directory Structure
```
music-gen-platform/
├── docs/         Design docs (requirements, algorithm roadmap, datasets, architecture, training, frontend specs)
├── deploy/       Infrastructure docker-compose (PostgreSQL / Redis / RabbitMQ / MinIO)
├── platform/     Java platform layer (Spring Boot 3 + Maven)
├── inference/    Python inference layer (FastAPI + queue worker + engine abstraction)
├── frontend/     React frontend (Vite + TS + Tailwind, dark creative-tool style)
└── research/     Track B: music generation algorithms implemented from scratch
```

### Track A: Platform (Implemented)
- **Platform layer `platform/`**: Task CRUD, model listing, audio streaming proxy, WebSocket 
  progress push, global exception handling, CORS. Enqueues tasks to RabbitMQ, subscribes to 
  Redis progress updates to DB and pushes to frontend.
- **Inference layer `inference/`**: Consumes queue → invokes engine → loudness normalization → 
  writes to MinIO → reports progress.
  - Engine abstraction `engines/base.py`: `MusicGenEngine` (real) / `MockEngine` (no GPU, test pipeline) /
    reserved `custom.py` (Track B custom model).
  - Failed tasks retry up to `MAX_RETRIES`.
- **Frontend `frontend/`**: Creation page (prompt + parameter presets + sliders), waveform player 
  (wavesurfer), history page, Toast notifications, light/dark theme toggle, mobile drawer navigation.

### Track B: Algorithm Research (Implemented, `research/`)
A complete text-to-music pipeline implemented from scratch, with each layer independently trainable/runnable:

| Layer | Directory | Contents |
|----|------|------|
| 1 Audio Signal Basics | `audio_basics/` | Waveform ↔ Mel spectrogram, Griffin-Lim reconstruction, visualization |
| 2 Neural Codec ⭐ | `audio_codec/` | VQ-VAE / RVQ, compressing audio into discrete tokens |
| 3 Autoregressive Transformer ⭐ | `audio_lm/` | GPT-style token-by-token generation + MusicGen's delay pattern |
| 4 Text Conditioning | `audio_lm/*_text*` | T5 text encoding + cross-attention + classifier-free guidance |
| 5 Evaluation | `eval/` | FAD (distribution distance) + CLAP score (text-audio alignment) |

See `research/README.md` and `docs/02-算法研究路线.md` for details.

---

## 4. How to Use

### A. Run the Platform (Track A)

**Prerequisites**: Docker, JDK 17, Node 20. (No GPU needed — use mock engine to verify the full pipeline.)

**Step 1: Start Infrastructure**
```bash
cd deploy && cp .env.example .env && docker compose up -d
# RabbitMQ console http://localhost:15672  MinIO console http://localhost:9001
```

**Step 2: Start Inference Layer**
```bash
cd ../inference
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # With GPU: install CUDA-compatible torch first (see docs/04)
cp .env.example .env                      # No GPU: set MOCK_ENGINE to true
python -m app.worker
```

**Step 3: Start Platform Layer** (includes Maven Wrapper, no global Maven needed)
```bash
cd ../platform && ./mvnw spring-boot:run   # Windows: mvnw.cmd spring-boot:run
```

**Step 4: Start Frontend**
```bash
cd ../frontend && npm install && npm run dev
# Open http://localhost:5173, enter description → generate → waveform playback
```

**Or verify backend directly with curl**
```bash
curl -X POST localhost:8080/api/v1/tasks \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"calm piano","model":"musicgen-medium","params":{"duration":5}}'
# Returns taskId → GET /api/v1/tasks/{taskId} to check status → GET /api/v1/audio/{taskId} for audio
```

### B. Run Algorithm Research (Track B)

**Prerequisites**: Python + install CUDA-compatible torch per `docs/04` (GPU recommended, e.g., RTX 4090).

```bash
cd research
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

**Run the full text-to-music pipeline from scratch (start with single codebook + small datasets like NSynth/MAESTRO)**
```bash
# Layer 1: Understand audio ↔ spectrogram
python -m audio_basics.demo path/to/audio.wav

# Layer 2: Train neural codec (audio → tokens)
python -m audio_codec.train --data path/to/audio_dir --epochs 50 --quantizers 1
python -m audio_codec.encode_decode --ckpt audio_codec/ckpt/codec.pt --audio in.wav

# Layer 3: Train autoregressive Transformer on tokens and generate
python -m audio_lm.prepare_tokens --codec audio_codec/ckpt/codec.pt \
    --data path/to/audio_dir --out audio_lm/tokens.pt
python -m audio_lm.train --tokens audio_lm/tokens.pt --epochs 100
python -m audio_lm.generate --lm audio_lm/ckpt/lm.pt --codec audio_codec/ckpt/codec.pt

# Layer 4: Text conditioning (requires audio-text pairs like MusicCaps, see docs/03)
python -m audio_lm.prepare_tokens_text --codec audio_codec/ckpt/codec.pt \
    --manifest data/musiccaps.jsonl --root data --out audio_lm/tokens_text.pt
python -m audio_lm.train_text --tokens audio_lm/tokens_text.pt --epochs 100
python -m audio_lm.generate_text --lm audio_lm/ckpt/lm_text.pt \
    --codec audio_codec/ckpt/codec.pt --prompt "calm piano, relaxing" --cfg 3.0

# Layer 5: Evaluation
python -m eval.evaluate --gen out/generated --ref data/reference --prompts prompts.jsonl
```

### C. Integrate Custom Model Back into Platform
Once Track B training is satisfactory, implement the unified engine interface in 
`inference/app/engines/custom.py` (`load` / `generate` / `sample_rate`), register it in the 
`models` table, and it becomes selectable in the frontend model dropdown — coexisting and 
comparing with MusicGen. Zero changes needed on the platform layer.

---

## 5. Current Status

- ✅ Track A: Infrastructure, inference layer (mock/MusicGen engine, loudness normalization, retry), 
  platform layer (task/model/audio APIs, queue, WebSocket, exception handling, CORS), React frontend — 
  code complete, frontend build verified.
- ✅ Track B: Algorithm layers 1–5 all implemented, syntax checks passed.
- ⏳ TODO: Run training and end-to-end integration on GPU; user system / authentication; 
  custom model integration into platform.

> Note: Algorithm code and some backend components have not yet been run on actual GPU/real dependencies. 
> Verification requires setting up the environment (CUDA torch, Maven, Docker).

## 6. Document Index (`docs/`)
1. Technical Specifications & Feasibility Analysis　2. Algorithm Research Roadmap　3. Dataset Survey
4. Phase 0 Practical Checklist　5. Platform Architecture Detailed Design　6. Custom Model Training Plan　7. Frontend Design Specs & Architecture
