# 前端（React + TypeScript）

Vite + React 18 + TypeScript + Tailwind CSS。深色创作工具风。
设计规范见 `../docs/07-前端设计规范与架构.md`。

## 开发

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

需要平台层（:8080）已启动。API/WS 地址在 `.env`（`VITE_API_BASE` / `VITE_WS_BASE`）。

## 构建

```bash
npm run build      # 产物在 dist/
npm run preview
```

## 结构

```
src/
├── api/         后端调用封装（纯函数）
├── hooks/       useGenerate / useTaskProgress(WS) / useModels
├── store/       Zustand 任务状态
├── types/       与后端 DTO 对齐的 TS 类型
├── components/  ui/(基础) + 业务组件
└── pages/       GeneratePage / HistoryPage
```

## 数据流
```
PromptInput → useGenerate → POST /api/v1/tasks
  → useTaskProgress 连 WS /ws/tasks/{id} → 更新 store → TaskCard 进度
  → SUCCEEDED → AudioPlayer 播放 GET /api/v1/audio/{id}
```
