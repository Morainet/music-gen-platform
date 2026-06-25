import { Select } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { useModels } from "@/hooks/useModels";

interface Props {
  value: string;
  onChange: (value: string) => void;
}

export function ModelSelect({ value, onChange }: Props) {
  const { models, loading } = useModels();

  return (
    <div>
      <Label>模型</Label>
      <Select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={loading}
      >
        {models.map((m) => (
          <option key={m.name} value={m.name}>
            {m.displayName ?? m.name}
          </option>
        ))}
      </Select>
    </div>
  );
}
