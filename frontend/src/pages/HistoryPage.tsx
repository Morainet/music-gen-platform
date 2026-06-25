import { useEffect, useState } from "react";
import { toast } from "sonner";
import { TaskList } from "@/components/TaskList";
import { TaskCardSkeleton } from "@/components/ui/skeleton";
import { listTasks } from "@/api/tasks";
import { useTasksStore } from "@/store/tasks";

export function HistoryPage() {
  const tasks = useTasksStore((s) => s.tasks);
  const setAll = useTasksStore((s) => s.setAll);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listTasks(0, 50)
      .then((res) => setAll(res.items))
      .catch((e) =>
        toast.error(e instanceof Error ? e.message : "加载历史失败")
      )
      .finally(() => setLoading(false));
  }, [setAll]);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">生成历史</h1>
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <TaskCardSkeleton key={i} />
          ))}
        </div>
      ) : (
        <TaskList tasks={tasks} emptyText="暂无历史记录" />
      )}
    </div>
  );
}
