package com.mgp.domain;

import jakarta.persistence.*;
import java.time.OffsetDateTime;
import java.util.UUID;
import lombok.Getter;
import lombok.Setter;

@Entity
@Table(name = "generation_tasks")
@Getter
@Setter
public class GenerationTask {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "user_id")
    private Long userId;

    @Column(nullable = false)
    private String prompt;

    @Column(name = "model_name", nullable = false)
    private String modelName;

    // JSON 字符串存储生成参数（duration/temperature/...）
    @Column(nullable = false, columnDefinition = "jsonb")
    private String params;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private TaskStatus status = TaskStatus.PENDING;

    private Short progress = 0;

    @Column(name = "audio_url")
    private String audioUrl;

    @Column(name = "error_msg")
    private String errorMsg;

    @Column(name = "created_at")
    private OffsetDateTime createdAt = OffsetDateTime.now();

    @Column(name = "updated_at")
    private OffsetDateTime updatedAt = OffsetDateTime.now();
}
