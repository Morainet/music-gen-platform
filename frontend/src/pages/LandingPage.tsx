import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Sparkles,
  AudioLines,
  Type,
  SlidersHorizontal,
  Layers,
  Cpu,
  ArrowRight,
  Server,
  Gauge,
  Boxes,
  Palette,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const HIGHLIGHTS = [
  { icon: Server, label: "自部署模型", sub: "数据与权重自主可控" },
  { icon: Gauge, label: "异步实时", sub: "队列削峰 + 进度推送" },
  { icon: Boxes, label: "5 层自研算法", sub: "codec→Transformer→评估" },
  { icon: Palette, label: "深浅双主题", sub: "响应式 · 移动端适配" },
];

const FEATURES = [
  {
    icon: Type,
    title: "文本生成音乐",
    desc: "输入一句描述，几十秒得到对应风格的原创音乐。",
    points: ["自然语言 prompt", "风格 / 乐器 / 情绪可控"],
  },
  {
    icon: AudioLines,
    title: "波形可视化",
    desc: "内置波形播放器，所听即所得。",
    points: ["点击波形 seek", "实时进度 · 一键下载"],
  },
  {
    icon: SlidersHorizontal,
    title: "参数与预设",
    desc: "精细调节，也可一键套用风格预设。",
    points: ["时长 / 随机性 / cfg", "电子·舒缓·实验等预设"],
  },
  {
    icon: Layers,
    title: "多模型可切换",
    desc: "引擎抽象设计，模型即插即用。",
    points: ["MusicGen 与自研并存", "前端一键切换对比"],
  },
  {
    icon: Cpu,
    title: "异步生成架构",
    desc: "面向耗时任务的稳健工程设计。",
    points: ["队列削峰 + 失败重试", "WebSocket 实时进度"],
  },
  {
    icon: Sparkles,
    title: "从零自研算法",
    desc: "完整复现文本到音乐的核心链路。",
    points: ["神经 codec + Transformer", "文本条件 + CFG 引导"],
  },
];

const STEPS = [
  { n: "1", title: "描述", desc: "用一句话说出你想要的音乐风格、乐器、情绪。" },
  { n: "2", title: "生成", desc: "提交后异步生成，进度条实时反馈。" },
  { n: "3", title: "播放 / 下载", desc: "波形播放器试听，满意即可下载 wav。" },
];

export function LandingPage() {
  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden">
        {/* 背景光晕 */}
        <div className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute left-1/2 top-0 h-72 w-[42rem] -translate-x-1/2 rounded-full bg-violet/20 blur-[120px]" />
          <div className="absolute left-1/3 top-24 h-56 w-96 rounded-full bg-cyan/10 blur-[120px]" />
        </div>

        <div className="max-w-5xl mx-auto px-4 pt-20 pb-16 text-center">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface px-3 py-1 text-xs text-text-secondary">
              <Sparkles className="h-3.5 w-3.5 text-violet" />
              文本到音乐 · AI 生成平台
            </span>
            <h1 className="mt-6 text-4xl sm:text-5xl font-bold leading-tight">
              用一句话，
              <span className="text-gradient">生成你的音乐</span>
            </h1>
            <p className="mt-4 max-w-xl mx-auto text-text-secondary">
              描述你想要的风格、乐器与情绪，几十秒得到一段原创音乐。
              基于自部署模型，从创作到自研算法的一体化平台。
            </p>
            <div className="mt-8 flex items-center justify-center gap-3">
              <Link to="/create">
                <Button variant="primary" size="lg">
                  <Sparkles className="h-5 w-5" />
                  开始创作
                </Button>
              </Link>
              <Link to="/history">
                <Button variant="secondary" size="lg">
                  查看历史
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-5xl mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold">平台能力</h2>
          <p className="mt-2 text-text-secondary">
            从创作体验到底层算法，一体化的音乐生成平台
          </p>
        </div>

        {/* 核心亮点指标条 */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
          {HIGHLIGHTS.map((h) => (
            <div
              key={h.label}
              className="flex items-center gap-3 rounded-xl border border-border bg-surface px-4 py-3"
            >
              <div className="grid place-items-center h-9 w-9 shrink-0 rounded-lg bg-violet/10">
                <h.icon className="h-4 w-4 text-violet" />
              </div>
              <div className="min-w-0">
                <div className="text-sm font-semibold text-text-primary truncate">
                  {h.label}
                </div>
                <div className="text-xs text-text-muted truncate">{h.sub}</div>
              </div>
            </div>
          ))}
        </div>

        {/* 能力卡片 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {FEATURES.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.3, delay: i * 0.05 }}
              className="group rounded-2xl border border-border bg-surface p-5 transition-all hover:border-violet/50 hover:shadow-glow hover:-translate-y-0.5"
            >
              <div className="grid place-items-center h-11 w-11 rounded-xl bg-accent-gradient shadow-glow mb-4">
                <f.icon className="h-5 w-5 text-white" />
              </div>
              <h3 className="font-semibold text-text-primary">{f.title}</h3>
              <p className="mt-1 text-sm text-text-secondary">{f.desc}</p>
              <ul className="mt-3 space-y-1.5">
                {f.points.map((pt) => (
                  <li
                    key={pt}
                    className="flex items-center gap-2 text-xs text-text-secondary"
                  >
                    <span className="h-1.5 w-1.5 rounded-full bg-accent-gradient shrink-0" />
                    {pt}
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Workflow */}
      <section className="max-w-5xl mx-auto px-4 py-12">
        <h2 className="text-center text-sm font-semibold text-text-secondary mb-6">
          三步开始
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {STEPS.map((s) => (
            <div
              key={s.n}
              className="rounded-2xl border border-border bg-surface p-5"
            >
              <div className="grid place-items-center h-9 w-9 rounded-full bg-accent-gradient text-white font-semibold shadow-glow">
                {s.n}
              </div>
              <h3 className="mt-3 font-semibold text-text-primary">{s.title}</h3>
              <p className="mt-1 text-sm text-text-secondary">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-5xl mx-auto px-4 py-16">
        <div className="rounded-2xl border border-border bg-surface p-10 text-center bg-[radial-gradient(circle_at_top,_rgba(139,92,246,0.12),_transparent_60%)]">
          <h2 className="text-2xl font-bold">准备好创作了吗？</h2>
          <p className="mt-2 text-text-secondary">现在就输入一句描述，生成你的第一段音乐。</p>
          <Link to="/create" className="inline-block mt-6">
            <Button variant="primary" size="lg">
              <Sparkles className="h-5 w-5" />
              立即开始
            </Button>
          </Link>
        </div>
      </section>
    </div>
  );
}
