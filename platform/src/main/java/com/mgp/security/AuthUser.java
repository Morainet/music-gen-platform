package com.mgp.security;

/** 鉴权后放入 SecurityContext 的主体。 */
public record AuthUser(Long id, String username) {}
