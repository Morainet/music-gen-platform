import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { Music4, Menu, X, Sun, Moon, LogIn, LogOut, User } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTheme } from "@/hooks/useTheme";
import { useAuthStore } from "@/store/auth";

const NAV = [
  { to: "/", label: "首页" },
  { to: "/create", label: "创作" },
  { to: "/history", label: "历史" },
];

export function AppHeader() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { theme, toggle } = useTheme();
  const { username, logout } = useAuthStore();
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-20 border-b border-border bg-base/80 backdrop-blur">
      <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <span className="grid place-items-center h-8 w-8 rounded-lg bg-accent-gradient shadow-glow">
            <Music4 className="h-4 w-4 text-white" />
          </span>
          <span className="font-semibold text-text-primary">AI 音乐生成</span>
        </Link>

        <div className="flex items-center gap-1">
          {/* 桌面导航 */}
          <nav className="hidden sm:flex items-center gap-1">
            {NAV.map((n) => (
              <Link
                key={n.to}
                to={n.to}
                className={cn(
                  "px-3 py-1.5 rounded-lg text-sm transition-colors",
                  pathname === n.to
                    ? "text-text-primary bg-elevated"
                    : "text-text-secondary hover:text-text-primary"
                )}
              >
                {n.label}
              </Link>
            ))}
          </nav>

          {/* 主题切换 */}
          <button
            type="button"
            onClick={toggle}
            className="grid place-items-center h-9 w-9 rounded-lg text-text-secondary hover:text-text-primary hover:bg-elevated transition-colors"
            title={theme === "dark" ? "切换浅色" : "切换深色"}
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
          </button>

          {/* 登录 / 用户 */}
          {username ? (
            <div className="hidden sm:flex items-center gap-1">
              <span className="flex items-center gap-1.5 px-2 text-sm text-text-secondary">
                <User className="h-4 w-4" />
                {username}
              </span>
              <button
                type="button"
                onClick={logout}
                title="退出登录"
                className="grid place-items-center h-9 w-9 rounded-lg text-text-secondary hover:text-error hover:bg-error/10 transition-colors"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => navigate("/login")}
              className="hidden sm:flex items-center gap-1.5 h-9 px-3 rounded-lg text-sm text-text-secondary hover:text-text-primary hover:bg-elevated transition-colors"
            >
              <LogIn className="h-4 w-4" />
              登录
            </button>
          )}

          {/* 移动端汉堡 */}
          <button
            type="button"
            onClick={() => setOpen(true)}
            className="sm:hidden grid place-items-center h-9 w-9 rounded-lg text-text-secondary hover:text-text-primary hover:bg-elevated transition-colors"
            title="菜单"
          >
            <Menu className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* 移动端抽屉 */}
      <AnimatePresence>
        {open && (
          <>
            <motion.div
              className="fixed inset-0 z-30 bg-black/50 sm:hidden"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setOpen(false)}
            />
            <motion.aside
              className="fixed top-0 right-0 z-40 h-full w-64 bg-surface border-l border-border p-4 sm:hidden"
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "tween", duration: 0.25 }}
            >
              <div className="flex items-center justify-between mb-6">
                <span className="font-semibold text-text-primary">菜单</span>
                <button
                  type="button"
                  onClick={() => setOpen(false)}
                  className="grid place-items-center h-9 w-9 rounded-lg text-text-secondary hover:text-text-primary hover:bg-elevated"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              <nav className="flex flex-col gap-1">
                {NAV.map((n) => (
                  <Link
                    key={n.to}
                    to={n.to}
                    onClick={() => setOpen(false)}
                    className={cn(
                      "px-3 py-2.5 rounded-lg text-sm transition-colors",
                      pathname === n.to
                        ? "text-text-primary bg-elevated"
                        : "text-text-secondary hover:text-text-primary hover:bg-elevated"
                    )}
                  >
                    {n.label}
                  </Link>
                ))}

                <div className="my-2 h-px bg-border" />

                {username ? (
                  <>
                    <span className="flex items-center gap-1.5 px-3 py-2 text-sm text-text-secondary">
                      <User className="h-4 w-4" />
                      {username}
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        logout();
                        setOpen(false);
                      }}
                      className="flex items-center gap-1.5 px-3 py-2.5 rounded-lg text-sm text-text-secondary hover:text-error hover:bg-error/10 transition-colors"
                    >
                      <LogOut className="h-4 w-4" />
                      退出登录
                    </button>
                  </>
                ) : (
                  <Link
                    to="/login"
                    onClick={() => setOpen(false)}
                    className="flex items-center gap-1.5 px-3 py-2.5 rounded-lg text-sm text-text-secondary hover:text-text-primary hover:bg-elevated transition-colors"
                  >
                    <LogIn className="h-4 w-4" />
                    登录
                  </Link>
                )}
              </nav>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </header>
  );
}
