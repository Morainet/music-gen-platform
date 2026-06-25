import { Sparkles, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Props {
  onClick: () => void;
  loading?: boolean;
  disabled?: boolean;
}

export function GenerateButton({ onClick, loading, disabled }: Props) {
  return (
    <Button
      variant="primary"
      size="lg"
      onClick={onClick}
      disabled={disabled || loading}
      className="w-full sm:w-auto"
    >
      {loading ? (
        <>
          <Loader2 className="h-5 w-5 animate-spin" />
          生成中…
        </>
      ) : (
        <>
          <Sparkles className="h-5 w-5" />
          生成音乐
        </>
      )}
    </Button>
  );
}
