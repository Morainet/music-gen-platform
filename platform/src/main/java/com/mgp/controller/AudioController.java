package com.mgp.controller;

import io.minio.GetObjectArgs;
import io.minio.MinioClient;
import io.minio.StatObjectArgs;
import java.io.InputStream;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.InputStreamResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 从 MinIO 流式读取生成的音频。支持 HTTP Range，便于大文件拖动 seek。
 */
@RestController
@RequestMapping("/api/v1/audio")
public class AudioController {

    private static final MediaType WAV = MediaType.parseMediaType("audio/wav");

    private final MinioClient minio;

    @Value("${mgp.minio.bucket}")
    private String bucket;

    public AudioController(MinioClient minio) {
        this.minio = minio;
    }

    @GetMapping("/{taskId}")
    public ResponseEntity<InputStreamResource> get(
            @PathVariable String taskId,
            @RequestHeader(value = HttpHeaders.RANGE, required = false) String range)
            throws Exception {
        String object = taskId + ".wav";
        long size = minio.statObject(
                StatObjectArgs.builder().bucket(bucket).object(object).build()).size();

        if (range == null || !range.startsWith("bytes=")) {
            InputStream in = minio.getObject(
                    GetObjectArgs.builder().bucket(bucket).object(object).build());
            return ResponseEntity.ok()
                    .header(HttpHeaders.ACCEPT_RANGES, "bytes")
                    .contentType(WAV)
                    .contentLength(size)
                    .body(new InputStreamResource(in));
        }

        // 解析 "bytes=start-end"（end 可省略）
        long[] r = parseRange(range, size);
        long start = r[0], end = r[1], len = end - start + 1;

        InputStream in = minio.getObject(
                GetObjectArgs.builder().bucket(bucket).object(object)
                        .offset(start).length(len).build());
        return ResponseEntity.status(HttpStatus.PARTIAL_CONTENT)
                .header(HttpHeaders.ACCEPT_RANGES, "bytes")
                .header(HttpHeaders.CONTENT_RANGE, "bytes " + start + "-" + end + "/" + size)
                .contentType(WAV)
                .contentLength(len)
                .body(new InputStreamResource(in));
    }

    private long[] parseRange(String range, long size) {
        String spec = range.substring("bytes=".length());
        String[] parts = spec.split("-", 2);
        long start = parts[0].isEmpty() ? 0 : Long.parseLong(parts[0].trim());
        long end = (parts.length > 1 && !parts[1].isEmpty())
                ? Long.parseLong(parts[1].trim())
                : size - 1;
        if (end >= size) {
            end = size - 1;
        }
        if (start > end) {
            start = 0;
        }
        return new long[] {start, end};
    }
}
