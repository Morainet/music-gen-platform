package com.mgp.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;

@Entity
@Table(name = "models")
@Getter
@Setter
public class ModelInfo {

    @Id
    private String name;

    @Column(name = "display_name")
    private String displayName;

    private String type;

    private Boolean enabled = true;

    // JSON 字符串：采样率、最大时长等
    @Column(columnDefinition = "jsonb")
    private String meta;
}
