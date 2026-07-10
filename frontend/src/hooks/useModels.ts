import { useEffect, useState } from "react";
import { listModels } from "@/api/models";
import type { ModelResponse } from "@/types/api";

export function useModels() {
  const [models, setModels] = useState<ModelResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    listModels()
      .then((data) => active && setModels(data))
      .catch(() => {
        // 后端不可用时给个兜底，便于本地先看 UI
        if (active)
          setModels([
            {
              name: "mgp-custom",
              displayName: "自研模型 (VQ-VAE + AR Transformer)",
            },
          ]);
      })
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, []);

  return { models, loading };
}
