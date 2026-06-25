import { cn } from "@/lib/utils";

interface ProgressProps {
  value: number; // 0-100
  className?: string;
  animated?: boolean;
}

export function Progress({ value, className, animated }: ProgressProps) {
  return (
    <div
      className={cn(
        "h-2 w-full overflow-hidden rounded-full bg-elevated",
        className
      )}
    >
      <div
        className={cn(
          "h-full rounded-full bg-accent-gradient transition-all duration-300",
          animated &&
            "bg-[length:200%_100%] animate-shimmer"
        )}
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  );
}
