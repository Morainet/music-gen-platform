import { cn } from "@/lib/utils";
import type { GenerateParams } from "@/types/api";

interface Preset {
  name: string;
  params: GenerateParams;
}

const PRESETS: Preset[] = [
  { name: "默认", params: { duration: 10, temperature: 1, cfg_coef: 3 } },
  { name: "电子舞曲", params: { duration: 15, temperature: 1.1, cfg_coef: 4 } },
  { name: "舒缓氛围", params: { duration: 20, temperature: 0.8, cfg_coef: 3 } },
  { name: "实验先锋", params: { duration: 10, temperature: 1.4, cfg_coef: 2 } },
];

function matches(a: GenerateParams, b: GenerateParams) {
  return (
    a.duration === b.duration &&
    a.temperature === b.temperature &&
    a.cfg_coef === b.cfg_coef
  );
}

interface Props {
  params: GenerateParams;
  onApply: (params: GenerateParams) => void;
}

export function PresetBar({ params, onApply }: Props) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {PRESETS.map((p) => {
        const active = matches(params, p.params);
        return (
          <button
            key={p.name}
            type="button"
            onClick={() => onApply(p.params)}
            className={cn(
              "text-xs rounded-full px-3 py-1 border transition-colors",
              active
                ? "border-violet/70 text-violet bg-violet/10"
                : "border-border text-text-secondary hover:text-text-primary hover:border-violet/50"
            )}
          >
            {p.name}
          </button>
        );
      })}
    </div>
  );
}
