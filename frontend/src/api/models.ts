import { http } from "./client";
import type { ModelResponse } from "@/types/api";

export function listModels() {
  return http<ModelResponse[]>("/api/v1/models");
}
