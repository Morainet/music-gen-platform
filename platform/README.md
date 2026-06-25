# 平台层（Java / Spring Boot 3）

业务编排：任务 CRUD、投递队列、订阅进度、WebSocket 推送。不直接调用模型。

## 运行前提
- JDK 17（已含 Maven Wrapper，无需全局装 Maven）
- 基础设施已起（见 deploy/），且 PG 已建表（initdb 自动执行）

## 运行
```bash
cd platform
./mvnw spring-boot:run        # 首次运行自动下载 Maven 3.9.9 到 ~/.m2/wrapper
# 打包: ./mvnw clean package -> java -jar target/music-gen-platform-0.1.0.jar
# Windows: mvnw.cmd spring-boot:run
```
> 全局装了 Maven 也可直接用 `mvn`。Wrapper 的作用是锁定 Maven 版本、免去本机安装。

## 主要端点
- `POST /api/v1/tasks` 创建生成任务 → 投递队列
- `GET  /api/v1/tasks/{id}` 查询任务
- `GET  /api/v1/tasks` 历史列表
- `GET  /api/v1/models` 可用模型列表
- `GET  /api/v1/audio/{taskId}` 从 MinIO 流式读取音频（前端播放/下载）
- `WS   /ws/tasks/{taskId}` 实时进度

## 数据流
```
POST 创建任务 → 存 PG(PENDING) → 投 RabbitMQ
推理层消费 → 经 Redis 上报进度 → ProgressListener 更新 PG + WebSocket 推前端
```

## 结构
- `controller/` REST + WebSocket
- `service/TaskService` 业务逻辑
- `domain/` JPA 实体、状态枚举
- `mq/` 队列投递（TaskProducer）、进度订阅（ProgressListener）
- `config/` WebSocket、Redis 订阅容器
