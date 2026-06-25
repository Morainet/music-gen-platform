import { useEffect, useRef, useState } from "react";
import WaveSurfer from "wavesurfer.js";
import { Download, Play, Pause } from "lucide-react";
import { audioUrl } from "@/api/audio";

function fmt(sec: number) {
  if (!isFinite(sec)) return "0:00";
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function AudioPlayer({ taskId }: { taskId: string }) {
  const url = audioUrl(taskId);
  const containerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WaveSurfer | null>(null);
  const [ready, setReady] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [time, setTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!containerRef.current) return;
    const ws = WaveSurfer.create({
      container: containerRef.current,
      url,
      height: 40,
      waveColor: "#3A3A4A",
      progressColor: "#8B5CF6",
      cursorColor: "#22D3EE",
      barWidth: 2,
      barGap: 2,
      barRadius: 2,
    });
    wsRef.current = ws;

    ws.on("ready", () => {
      setReady(true);
      setDuration(ws.getDuration());
    });
    ws.on("timeupdate", (t: number) => setTime(t));
    ws.on("play", () => setPlaying(true));
    ws.on("pause", () => setPlaying(false));
    ws.on("finish", () => setPlaying(false));
    ws.on("error", () => setFailed(true));

    return () => {
      ws.destroy();
      wsRef.current = null;
    };
  }, [url]);

  // wavesurfer 加载失败时回退到原生 audio
  if (failed) {
    return (
      <div className="flex items-center gap-3">
        <audio controls src={url} className="w-full h-9" />
        <DownloadLink url={url} taskId={taskId} />
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <button
        type="button"
        onClick={() => wsRef.current?.playPause()}
        disabled={!ready}
        className="shrink-0 grid place-items-center h-9 w-9 rounded-lg bg-accent-gradient text-white shadow-glow disabled:opacity-50"
        title={playing ? "暂停" : "播放"}
      >
        {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
      </button>

      <div className="flex-1 min-w-0">
        <div ref={containerRef} className="cursor-pointer" title="点击波形跳转" />
      </div>

      <span className="shrink-0 font-mono text-[11px] text-text-muted tabular-nums">
        {fmt(time)} / {fmt(duration)}
      </span>

      <DownloadLink url={url} taskId={taskId} />
    </div>
  );
}

function DownloadLink({ url, taskId }: { url: string; taskId: string }) {
  return (
    <a
      href={url}
      download={`${taskId}.wav`}
      className="shrink-0 grid place-items-center h-9 w-9 rounded-lg border border-border text-text-secondary hover:text-text-primary hover:border-violet/60 transition-colors"
      title="下载"
    >
      <Download className="h-4 w-4" />
    </a>
  );
}
