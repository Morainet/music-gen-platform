package com.mgp.controller;

import com.mgp.dto.ModelResponse;
import com.mgp.repository.ModelRepository;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/models")
public class ModelController {

    private final ModelRepository repo;

    public ModelController(ModelRepository repo) {
        this.repo = repo;
    }

    @GetMapping
    public List<ModelResponse> list() {
        return repo.findByEnabledTrue().stream().map(ModelResponse::from).toList();
    }
}
