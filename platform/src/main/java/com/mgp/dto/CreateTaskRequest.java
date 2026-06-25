package com.mgp.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.util.Map;

public record CreateTaskRequest(
        @NotBlank(message = "描述不能为空")
        @Size(max = 500, message = "描述最长 500 字")
        String prompt,
        String model,
        Map<String, Object> params
) {}
