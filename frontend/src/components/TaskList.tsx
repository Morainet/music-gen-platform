import { TaskCard } from "./TaskCard";
import { EmptyState } from "./EmptyState";
import type { TaskResponse } from "@/types/api";

interface Props {
  tasks: TaskResponse[];
  emptyText?: string;
}

export function TaskList({ tasks, emptyText = "还没有生成记录" }: Props) {
  if (tasks.length === 0) return <EmptyState text={emptyText} />;
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {tasks.map((t) => (
        <TaskCard key={t.taskId} task={t} />
      ))}
    </div>
  );
}
