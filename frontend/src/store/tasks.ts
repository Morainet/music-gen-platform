import { create } from "zustand";
import type { TaskResponse } from "@/types/api";

interface TasksState {
  tasks: TaskResponse[];
  upsert: (task: TaskResponse) => void;
  setAll: (tasks: TaskResponse[]) => void;
}

/** 当前会话的任务列表（最近生成在前） */
export const useTasksStore = create<TasksState>((set) => ({
  tasks: [],
  upsert: (task) =>
    set((state) => {
      const idx = state.tasks.findIndex((t) => t.taskId === task.taskId);
      if (idx === -1) return { tasks: [task, ...state.tasks] };
      const next = [...state.tasks];
      next[idx] = { ...next[idx], ...task };
      return { tasks: next };
    }),
  setAll: (tasks) => set({ tasks }),
}));
