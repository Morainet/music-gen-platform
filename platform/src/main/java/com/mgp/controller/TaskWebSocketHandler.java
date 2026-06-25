package com.mgp.controller;

import java.io.IOException;
import java.net.URI;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

@Component
public class TaskWebSocketHandler extends TextWebSocketHandler {

    // taskId -> sessions
    private final Map<String, Set<WebSocketSession>> sessions = new ConcurrentHashMap<>();

    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        String taskId = taskIdOf(session);
        sessions.computeIfAbsent(taskId, k -> ConcurrentHashMap.newKeySet()).add(session);
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        String taskId = taskIdOf(session);
        Set<WebSocketSession> set = sessions.get(taskId);
        if (set != null) {
            set.remove(session);
            if (set.isEmpty()) {
                sessions.remove(taskId);
            }
        }
    }

    /** 由进度监听器调用，向订阅该 task 的所有连接推送 JSON。 */
    public void push(String taskId, String json) {
        Set<WebSocketSession> set = sessions.get(taskId);
        if (set == null) {
            return;
        }
        for (WebSocketSession s : set) {
            try {
                if (s.isOpen()) {
                    s.sendMessage(new TextMessage(json));
                }
            } catch (IOException ignored) {
            }
        }
    }

    private String taskIdOf(WebSocketSession session) {
        URI uri = session.getUri();
        String path = uri == null ? "" : uri.getPath();
        int i = path.lastIndexOf('/');
        return i >= 0 ? path.substring(i + 1) : path;
    }
}
