package com.mgp.repository;

import com.mgp.domain.ModelInfo;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ModelRepository extends JpaRepository<ModelInfo, String> {
    List<ModelInfo> findByEnabledTrue();
}
