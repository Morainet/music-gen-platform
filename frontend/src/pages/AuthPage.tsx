import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { login, register } from "@/api/auth";
import { useAuthStore } from "@/store/auth";

export function AuthPage() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit() {
    if (!username.trim() || !password) return;
    setLoading(true);
    try {
      const fn = mode === "login" ? login : register;
      const res = await fn(username.trim(), password);
      setAuth(res.token, res.username);
      toast.success(mode === "login" ? "已登录" : "注册成功");
      navigate("/create");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "操作失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-sm mx-auto px-4 py-16">
      <Card className="space-y-5">
        <CardHeader className="mb-0">
          <CardTitle>{mode === "login" ? "登录" : "注册"}</CardTitle>
        </CardHeader>

        <div>
          <Label>用户名</Label>
          <Input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="3-64 字符"
            onKeyDown={(e) => e.key === "Enter" && submit()}
          />
        </div>
        <div>
          <Label>密码</Label>
          <Input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="至少 6 位"
            onKeyDown={(e) => e.key === "Enter" && submit()}
          />
        </div>

        <Button
          variant="primary"
          size="lg"
          className="w-full"
          onClick={submit}
          disabled={loading || !username.trim() || !password}
        >
          {mode === "login" ? "登录" : "注册"}
        </Button>

        <p className="text-center text-xs text-text-muted">
          {mode === "login" ? "还没有账号？" : "已有账号？"}
          <button
            type="button"
            className="ml-1 text-violet hover:underline"
            onClick={() => setMode(mode === "login" ? "register" : "login")}
          >
            {mode === "login" ? "去注册" : "去登录"}
          </button>
        </p>
      </Card>
    </div>
  );
}
