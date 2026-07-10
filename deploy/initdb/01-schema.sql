-- 初始化 schema（容器首次启动自动执行）
-- 对应 docs/05-平台架构详细设计.md 第 4 节

CREATE TABLE IF NOT EXISTS users (
    id            BIGSERIAL PRIMARY KEY,
    username      VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT now()
);

-- 默认用户桶：未登录任务归到 id=0（对应 CurrentUser.DEFAULT_USER）
INSERT INTO users (id, username, password_hash)
VALUES (0, 'default', 'x')
ON CONFLICT (id) DO NOTHING;

CREATE TABLE IF NOT EXISTS generation_tasks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     BIGINT REFERENCES users(id),
    prompt      TEXT NOT NULL,
    model_name  VARCHAR(64) NOT NULL,
    params      JSONB NOT NULL,
    status      VARCHAR(16) NOT NULL,
    progress    SMALLINT DEFAULT 0,
    audio_url   TEXT,
    error_msg   TEXT,
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_tasks_user ON generation_tasks(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON generation_tasks(status);

CREATE TABLE IF NOT EXISTS models (
    name         VARCHAR(64) PRIMARY KEY,
    display_name VARCHAR(128),
    type         VARCHAR(32),
    enabled      BOOLEAN DEFAULT true,
    meta         JSONB
);

INSERT INTO models (name, display_name, type, enabled, meta)
VALUES ('musicgen-medium', 'MusicGen Medium', 'builtin', true,
        '{"sample_rate": 32000, "max_duration": 30}')
ON CONFLICT (name) DO NOTHING;
