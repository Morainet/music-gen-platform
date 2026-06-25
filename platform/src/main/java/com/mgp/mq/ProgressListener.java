package com.mgp.mq;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.mgp.controller.TaskWebSocketHandler;
import com.mgp.service.TaskService;
import org.springframework.stereotype.Component;

/**
 * 订阅 Redis 进度频道，收到推理层上报后：更新 PG，并通过 WebSocket 推给前端。
 */
@Component
public class ProgressListener {

    private final ObjectMapper mapper = new ObjectMapper();
    private final TaskService taskService;
    private final TaskWebSocketHandler wsHandler;

    public ProgressListener(TaskService taskService, TaskWebSocketHandler wsHandler) {
        this.taskService = taskService;
        this.wsHandler = wsHandler;
    }

    public void onMessage(String message) {
        try {
            JsonNode n = mapper.readTree(message);
            String taskId = n.get("taskId").asText();
            String status = n.get("status").asText();
            int progress = n.path("progress").asInt(0);
            String audioUrl = n.path("audioUrl").asText(null);
            String errorMsg = n.path("errorMsg").asText(null);

            taskService.applyProgress(taskId, status, progress, audioUrl, errorMsg);
            wsHandler.push(taskId, message);
        } catch (Exception ignored) {
        }
    }
}
