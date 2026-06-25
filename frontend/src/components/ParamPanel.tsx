import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import { ModelSelect } from "./ModelSelect";
import { PresetBar } from "./PresetBar";
import type { GenerateParams } from "@/types/api";

interface Props {
  model: string;
  onModelChange: (m: string) => void;
  params: GenerateParams;
  onParamsChange: (p: GenerateParams) => void;
}

export function ParamPanel({
  model,
  onModelChange,
  params,
  onParamsChange,
}: Props) {
  const set = (patch: Partial<GenerateParams>) =>
    onParamsChange({ ...params, ...patch });

  return (
    <div className="space-y-4">
      <div>
        <Label>参数预设</Label>
        <PresetBar params={params} onApply={onParamsChange} />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <ModelSelect value={model} onChange={onModelChange} />

      <div>
        <Label>
          时长 <span className="text-text-muted">{params.duration ?? 10}s</span>
        </Label>
        <Slider
          min={1}
          max={30}
          value={params.duration ?? 10}
          onChange={(e) => set({ duration: Number(e.target.value) })}
        />
      </div>

      <div>
        <Label>
          随机性 temperature{" "}
          <span className="text-text-muted">
            {(params.temperature ?? 1).toFixed(1)}
          </span>
        </Label>
        <Slider
          min={0}
          max={2}
          step={0.1}
          value={params.temperature ?? 1}
          onChange={(e) => set({ temperature: Number(e.target.value) })}
        />
      </div>

      <div>
        <Label>
          条件强度 cfg{" "}
          <span className="text-text-muted">{params.cfg_coef ?? 3}</span>
        </Label>
          <Slider
            min={1}
            max={10}
            step={0.5}
            value={params.cfg_coef ?? 3}
            onChange={(e) => set({ cfg_coef: Number(e.target.value) })}
          />
        </div>
      </div>
    </div>
  );
}
