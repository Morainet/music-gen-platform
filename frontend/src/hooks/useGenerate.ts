import { useState } from "react";
import { toast } from "sonner";
import { createTask } from "@/api/tasks";
import { useTasksStore } from "@/store/tasks";
import type { CreateTaskRequest } from "@/types/api";

export function useGenerate() {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const upsert = useTasksStore((s) => s.upsert);

  async function generate(req: CreateTaskRequest): Promise<string | null> {
    setSubmitting(true);
    setError(null);
    try {
      const task = await createTask(req);
      upsert(task);
      return task.taskId;
    } catch (e) {
      const msg = e instanceof Error ? e.message : "提交失败";
      setError(msg);
      toast.error(msg);
      return null;
    } finally {
      setSubmitting(false);
    }
  }

  return { generate, submitting, error };
}
