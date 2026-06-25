package com.mgp.dto;

import com.mgp.domain.ModelInfo;

public record ModelResponse(
        String name,
        String displayName,
        String type,
        String meta
) {
    public static ModelResponse from(ModelInfo m) {
        return new ModelResponse(m.getName(), m.getDisplayName(), m.getType(), m.getMeta());
    }
}
