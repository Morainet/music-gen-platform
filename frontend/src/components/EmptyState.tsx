import { Music2 } from "lucide-react";

export function EmptyState({ text }: { text: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="grid place-items-center h-12 w-12 rounded-2xl bg-elevated mb-3">
        <Music2 className="h-6 w-6 text-text-muted" />
      </div>
      <p className="text-sm text-text-muted">{text}</p>
    </div>
  );
}
