import { http } from "./client";

export interface AuthResponse {
  token: string;
  username: string;
}

export function register(username: string, password: string) {
  return http<AuthResponse>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function login(username: string, password: string) {
  return http<AuthResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}
