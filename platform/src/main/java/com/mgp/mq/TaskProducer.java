package com.mgp.mq;

import java.util.Map;
import java.util.UUID;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class TaskProducer {

    private final RabbitTemplate rabbitTemplate;

    @Value("${mgp.queue.tasks}")
    private String tasksQueue;

    public TaskProducer(RabbitTemplate rabbitTemplate) {
        this.rabbitTemplate = rabbitTemplate;
    }

    public void send(UUID taskId, String prompt, String model, Map<String, Object> params) {
        Map<String, Object> msg = Map.of(
                "taskId", taskId.toString(),
                "prompt", prompt,
                "model", model,
                "params", params == null ? Map.of() : params);
        rabbitTemplate.convertAndSend(tasksQueue, msg);
    }
}
