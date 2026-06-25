import { create } from "zustand";

const TOKEN_KEY = "token";
const USER_KEY = "username";

interface AuthState {
  token: string | null;
  username: string | null;
  setAuth: (token: string, username: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem(TOKEN_KEY),
  username: localStorage.getItem(USER_KEY),
  setAuth: (token, username) => {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, username);
    set({ token, username });
  },
  logout: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    set({ token: null, username: null });
  },
}));

/** 供非 React 代码（http 封装）读取当前 token。 */
export function currentToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
