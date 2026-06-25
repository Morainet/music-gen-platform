import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

interface Props {
  value: string;
  onChange: (value: string) => void;
  onSubmit?: () => void;
  maxLength?: number;
}

const EXAMPLES = [
  "An upbeat electronic dance track with a catchy synth melody",
  "Calm acoustic guitar, relaxing and warm",
  "Lo-fi hip hop beat with mellow piano",
];

export function PromptInput({
  value,
  onChange,
  onSubmit,
  maxLength = 500,
}: Props) {
  function handleKeyDown(e: React.KeyboardEvent) {
    // Cmd/Ctrl + Enter 提交
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      onSubmit?.();
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <Label>描述你想要的音乐</Label>
        <span className="text-[11px] text-text-muted tabular-nums">
          {value.length}/{maxLength}
        </span>
      </div>
      <Textarea
        rows={3}
        value={value}
        maxLength={maxLength}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="例如：An upbeat electronic dance track with a catchy synth melody"
      />
      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            type="button"
            onClick={() => onChange(ex)}
            className="text-xs text-text-muted hover:text-text-secondary border border-border rounded-full px-2.5 py-1 transition-colors"
          >
            {ex.length > 28 ? ex.slice(0, 28) + "…" : ex}
          </button>
        ))}
        <span className="ml-auto text-[11px] text-text-muted hidden sm:inline">
          ⌘/Ctrl + Enter 生成
        </span>
      </div>
    </div>
  );
}
