import { API_BASE } from "./client";

/** 平台层从 MinIO 流式返回音频 */
export function audioUrl(taskId: string) {
  return `${API_BASE}/api/v1/audio/${taskId}`;
}
