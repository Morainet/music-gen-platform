package com.mgp.security;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;

/** 取当前登录用户 id；未登录返回默认用户桶。 */
public final class CurrentUser {

    public static final long DEFAULT_USER = 0L;

    private CurrentUser() {}

    public static long id() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth != null && auth.getPrincipal() instanceof AuthUser u) {
            return u.id();
        }
        return DEFAULT_USER;
    }
}
