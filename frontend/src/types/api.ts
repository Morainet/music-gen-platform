export type TaskStatus =
  | "PENDING"
  | "RUNNING"
  | "SUCCEEDED"
  | "FAILED"
  | "CANCELED";

export interface PageResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export interface TaskResponse {
  taskId: string;
  prompt?: string;
  modelName?: string;
  status: TaskStatus;
  progress: number;
  audioUrl?: string | null;
  errorMsg?: string | null;
}

export interface ModelResponse {
  name: string;
  displayName?: string;
  type?: string;
  meta?: string;
}

export interface GenerateParams {
  duration?: number;
  temperature?: number;
  top_k?: number;
  cfg_coef?: number;
}

export interface CreateTaskRequest {
  prompt: string;
  model?: string;
  params?: GenerateParams;
}

/** WebSocket 进度消息 */
export interface ProgressMessage {
  taskId: string;
  status: TaskStatus;
  progress: number;
  audioUrl?: string;
  errorMsg?: string;
}
