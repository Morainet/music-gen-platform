package com.mgp.controller;

import com.mgp.dto.CreateTaskRequest;
import com.mgp.dto.PageResponse;
import com.mgp.dto.TaskResponse;
import com.mgp.service.TaskService;
import jakarta.validation.Valid;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/tasks")
public class TaskController {

    private final TaskService service;

    public TaskController(TaskService service) {
        this.service = service;
    }

    @PostMapping
    public TaskResponse create(@Valid @RequestBody CreateTaskRequest req) {
        return TaskResponse.from(service.create(req));
    }

    @GetMapping("/{id}")
    public TaskResponse get(@PathVariable UUID id) {
        return TaskResponse.from(service.get(id));
    }

    @GetMapping
    public PageResponse<TaskResponse> list(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        Page<TaskResponse> p =
                service.list(PageRequest.of(page, size)).map(TaskResponse::from);
        return new PageResponse<>(p.getContent(), p.getTotalElements(), page, size);
    }

    @PostMapping("/{id}/cancel")
    public TaskResponse cancel(@PathVariable UUID id) {
        return TaskResponse.from(service.cancel(id));
    }
}
