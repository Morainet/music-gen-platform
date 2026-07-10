package com.mgp.service;

import com.mgp.domain.GenerationTask;
import com.mgp.domain.TaskStatus;
import com.mgp.dto.CreateTaskRequest;
import com.mgp.mq.TaskProducer;
import com.mgp.repository.ModelRepository;
import com.mgp.repository.TaskRepository;
import com.mgp.security.CurrentUser;
import java.time.Duration;
import java.time.OffsetDateTime;
import java.util.Map;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class TaskService {

    private static final String DEFAULT_MODEL = "musicgen-medium";
    private static final int MAX_DURATION = 30;

    private final TaskRepository repo;
    private final ModelRepository modelRepo;
    private final TaskProducer producer;
    private final StringRedisTemplate redis;

    public TaskService(
            TaskRepository repo,
            ModelRepository modelRepo,
            TaskProducer producer,
            StringRedisTemplate redis) {
        this.repo = repo;
        this.modelRepo = modelRepo;
        this.producer = producer;
        this.redis = redis;
    }

    @Transactional
    public GenerationTask create(CreateTaskRequest req) {
        String model = req.model() == null ? DEFAULT_MODEL : req.model();
        Map<String, Object> params = req.params() == null ? Map.of() : req.params();

        // 边界校验
        if (!modelRepo.existsById(model)) {
            throw new IllegalArgumentException("未知模型: " + model);
        }
        validateDuration(params.get("duration"));

        GenerationTask task = new GenerationTask();
        task.setUserId(CurrentUser.id());
        task.setPrompt(req.prompt());
        task.setModelName(model);
        task.setParams(params);
        task.setStatus(TaskStatus.PENDING);
        task = repo.save(task);

        producer.send(task.getId(), req.prompt(), model, params);
        return task;
    }

    @Transactional(readOnly = true)
    public GenerationTask get(UUID id) {
        return repo.findById(id).orElseThrow();
    }

    @Transactional(readOnly = true)
    public Page<GenerationTask> list(Pageable pageable) {
        return repo.findByUserIdOrderByCreatedAtDesc(CurrentUser.id(), pageable);
    }

    /** 取消 PENDING/RUNNING 任务：写 Redis 标志（worker 据此中止）并标记 CANCELED。 */
    @Transactional
    public GenerationTask cancel(UUID id) {
        GenerationTask task = repo.findById(id).orElseThrow();
        if (task.getStatus() != TaskStatus.PENDING
                && task.getStatus() != TaskStatus.RUNNING) {
            throw new IllegalArgumentException("任务已结束，无法取消");
        }
        redis.opsForValue().set("cancel:" + id, "1", Duration.ofHours(1));
        task.setStatus(TaskStatus.CANCELED);
        task.setUpdatedAt(OffsetDateTime.now());
        return repo.save(task);
    }

    @Transactional
    public void applyProgress(String taskId, String status, int progress,
                              String audioUrl, String errorMsg) {
        repo.findById(UUID.fromString(taskId)).ifPresent(t -> {
            // 已取消的任务不被后续进度覆盖
            if (t.getStatus() == TaskStatus.CANCELED) {
                return;
            }
            t.setStatus(TaskStatus.valueOf(status));
            t.setProgress((short) progress);
            if (audioUrl != null) {
                t.setAudioUrl(audioUrl);
            }
            if (errorMsg != null) {
                t.setErrorMsg(errorMsg);
            }
            t.setUpdatedAt(OffsetDateTime.now());
            repo.save(t);
        });
    }

    private void validateDuration(Object duration) {
        if (duration instanceof Number n) {
            double d = n.doubleValue();
            if (d < 1 || d > MAX_DURATION) {
                throw new IllegalArgumentException("duration 需在 1-" + MAX_DURATION + " 秒");
            }
        }
    }
}
