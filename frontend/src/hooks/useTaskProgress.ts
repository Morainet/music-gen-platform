import { useEffect } from "react";
import { toast } from "sonner";
import { WS_BASE } from "@/api/client";
import { useTasksStore } from "@/store/tasks";
import type { ProgressMessage } from "@/types/api";

/**
 * 订阅某个任务的 WebSocket 进度，自动更新 store。
 * 任务结束（SUCCEEDED/FAILED）后关闭连接。
 */
export function useTaskProgress(taskId: string | null) {
  const upsert = useTasksStore((s) => s.upsert);

  useEffect(() => {
    if (!taskId) return;
    const ws = new WebSocket(`${WS_BASE}/ws/tasks/${taskId}`);

    ws.onmessage = (ev) => {
      try {
        const msg: ProgressMessage = JSON.parse(ev.data);
        upsert({
          taskId: msg.taskId,
          status: msg.status,
          progress: msg.progress,
          audioUrl: msg.audioUrl,
          errorMsg: msg.errorMsg,
        });
        if (msg.status === "SUCCEEDED") {
          toast.success("音乐生成完成");
          ws.close();
        } else if (msg.status === "FAILED") {
          toast.error(msg.errorMsg || "生成失败");
          ws.close();
        }
      } catch {
        /* ignore malformed */
      }
    };

    return () => ws.close();
  }, [taskId, upsert]);
}
