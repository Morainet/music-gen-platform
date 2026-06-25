import { useState } from "react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { X } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { StatusBadge } from "./StatusBadge";
import { AudioPlayer } from "./AudioPlayer";
import { cancelTask } from "@/api/tasks";
import { useTasksStore } from "@/store/tasks";
import { cn } from "@/lib/utils";
import type { TaskResponse } from "@/types/api";

export function TaskCard({ task }: { task: TaskResponse }) {
  const running = task.status === "RUNNING" || task.status === "PENDING";
  const upsert = useTasksStore((s) => s.upsert);
  const [canceling, setCanceling] = useState(false);

  async function handleCancel() {
    setCanceling(true);
    try {
      const updated = await cancelTask(task.taskId);
      upsert(updated);
      toast.success("已取消任务");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "取消失败");
    } finally {
      setCanceling(false);
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
    >
      <Card
        className={cn(
          "flex flex-col gap-3",
          running && "animate-pulse-glow border-violet/40"
        )}
      >
        <div className="flex items-start justify-between gap-3">
          <p className="text-sm text-text-primary line-clamp-2">
            {task.prompt ?? "(无描述)"}
          </p>
          <div className="flex items-center gap-1.5 shrink-0">
            <StatusBadge status={task.status} />
            {running && (
              <button
                type="button"
                onClick={handleCancel}
                disabled={canceling}
                title="取消"
                className="grid place-items-center h-6 w-6 rounded-md text-text-muted hover:text-error hover:bg-error/10 transition-colors disabled:opacity-50"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        </div>

        {running && <Progress value={task.progress} animated />}

        {task.status === "SUCCEEDED" && <AudioPlayer taskId={task.taskId} />}

        {task.status === "FAILED" && (
          <p className="text-xs text-error">{task.errorMsg ?? "生成失败"}</p>
        )}

        <p className="font-mono text-[10px] text-text-muted truncate">
          {task.taskId}
        </p>
      </Card>
    </motion.div>
  );
}
