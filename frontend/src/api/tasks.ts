import { http } from "./client";
import type {
  CreateTaskRequest,
  PageResponse,
  TaskResponse,
} from "@/types/api";

export function createTask(req: CreateTaskRequest) {
  return http<TaskResponse>("/api/v1/tasks", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export function getTask(id: string) {
  return http<TaskResponse>(`/api/v1/tasks/${id}`);
}

export function listTasks(page = 0, size = 20) {
  return http<PageResponse<TaskResponse>>(
    `/api/v1/tasks?page=${page}&size=${size}`
  );
}

export function cancelTask(id: string) {
  return http<TaskResponse>(`/api/v1/tasks/${id}/cancel`, { method: "POST" });
}
