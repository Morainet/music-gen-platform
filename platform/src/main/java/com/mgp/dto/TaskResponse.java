package com.mgp.dto;

import com.mgp.domain.GenerationTask;
import java.util.UUID;

public record TaskResponse(
        UUID taskId,
        String prompt,
        String modelName,
        String status,
        Short progress,
        String audioUrl,
        String errorMsg
) {
    public static TaskResponse from(GenerationTask t) {
        return new TaskResponse(
                t.getId(),
                t.getPrompt(),
                t.getModelName(),
                t.getStatus().name(),
                t.getProgress(),
                t.getAudioUrl(),
                t.getErrorMsg());
    }
}
