import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { PromptInput } from "@/components/PromptInput";
import { ParamPanel } from "@/components/ParamPanel";
import { GenerateButton } from "@/components/GenerateButton";
import { TaskList } from "@/components/TaskList";
import { useGenerate } from "@/hooks/useGenerate";
import { useModels } from "@/hooks/useModels";
import { useTaskProgress } from "@/hooks/useTaskProgress";
import { useTasksStore } from "@/store/tasks";
import type { GenerateParams } from "@/types/api";

export function GeneratePage() {
  const [prompt, setPrompt] = useState("");
  const [model, setModel] = useState("");
  const [params, setParams] = useState<GenerateParams>({
    duration: 10,
    temperature: 1,
    cfg_coef: 3,
  });
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);

  // 默认模型跟随后端返回的可用列表，避免选到已停用的模型
  const { models } = useModels();
  useEffect(() => {
    if (models.length && !models.some((m) => m.name === model)) {
      setModel(models[0].name);
    }
  }, [models, model]);

  const { generate, submitting } = useGenerate();
  const tasks = useTasksStore((s) => s.tasks);

  // 订阅当前提交任务的实时进度
  useTaskProgress(activeTaskId);

  async function handleGenerate() {
    if (!prompt.trim()) return;
    const id = await generate({ prompt: prompt.trim(), model, params });
    if (id) setActiveTaskId(id);
  }

  return (
    <div className="space-y-8">
      <Card className="space-y-5">
        <CardHeader className="mb-0">
          <CardTitle className="text-gradient inline-block">
            创作你的音乐
          </CardTitle>
        </CardHeader>

        <PromptInput
          value={prompt}
          onChange={setPrompt}
          onSubmit={handleGenerate}
        />
        <ParamPanel
          model={model}
          onModelChange={setModel}
          params={params}
          onParamsChange={setParams}
        />

        <div className="flex items-center gap-3">
          <GenerateButton
            onClick={handleGenerate}
            loading={submitting}
            disabled={!prompt.trim()}
          />
        </div>
      </Card>

      <section>
        <h2 className="text-sm font-semibold text-text-secondary mb-3">
          最近生成
        </h2>
        <TaskList tasks={tasks} emptyText="提交一个描述，开始生成第一段音乐" />
      </section>
    </div>
  );
}
