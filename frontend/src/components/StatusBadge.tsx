import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { TaskStatus } from "@/types/api";
import { Clock, Loader2, CheckCircle2, XCircle, Ban } from "lucide-react";

const MAP: Record<
  TaskStatus,
  { label: string; className: string; icon: React.ReactNode }
> = {
  PENDING: {
    label: "排队中",
    className: "bg-text-muted/15 text-text-secondary",
    icon: <Clock className="h-3 w-3" />,
  },
  RUNNING: {
    label: "生成中",
    className: "bg-info/15 text-info",
    icon: <Loader2 className="h-3 w-3 animate-spin" />,
  },
  SUCCEEDED: {
    label: "完成",
    className: "bg-success/15 text-success",
    icon: <CheckCircle2 className="h-3 w-3" />,
  },
  FAILED: {
    label: "失败",
    className: "bg-error/15 text-error",
    icon: <XCircle className="h-3 w-3" />,
  },
  CANCELED: {
    label: "已取消",
    className: "bg-text-muted/15 text-text-muted",
    icon: <Ban className="h-3 w-3" />,
  },
};

export function StatusBadge({ status }: { status: TaskStatus }) {
  const s = MAP[status];
  return (
    <Badge className={cn(s.className)}>
      {s.icon}
      {s.label}
    </Badge>
  );
}
