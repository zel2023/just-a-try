# 聊天AI Web 项目（至少5人同时在线）

## 0) 目标与范围（方案设计）

### 核心目标
- 在网页上实现**多人实时聊天**（至少 5 人同时在线、同房间可见消息）。
- 提供一个**AI 角色**参与聊天：用户可通过指令触发 AI 回复（避免每条消息都自动触发导致刷屏/成本不可控）。
- 支持部署：一条命令启动（本地或服务器），并具备清晰的配置方式。

### 建议的最小可行方案（MVP）
- **后端：Python FastAPI + WebSocket**
  - 维护在线连接列表、用户列表、广播消息。
  - 负责调用 AI（默认 OpenAI API；若未配置 Key 则使用“回声/占位 AI”保证可跑通）。
- **前端：单页 HTML/JS**
  - 输入昵称加入房间；实时显示消息、在线人数、系统提示。
  - 支持 `/ai 你的问题` 或 `@ai 你的问题` 触发 AI 回复。
- **部署：Docker（推荐）或直接 uvicorn**
  - 用 `.env` 管理配置（端口、模型名、API Key 等）。

### 交互与数据流（概念）
1. 浏览器打开页面 → 选择昵称 → 通过 WebSocket 连接到后端。
2. 用户发消息 → 后端广播给所有在线客户端。
3. 若消息为 AI 指令 → 后端取最近 N 条上下文 → 调用 AI → 将 AI 回复广播回房间。

### 并发与容量（至少5人）
- WebSocket + async I/O 可轻松支撑 5～50+ 并发连接（取决于机器与 AI 调用延迟）。
- AI 调用采用异步任务/队列（简单实现：后台 `asyncio.create_task`），避免阻塞广播。

### 安全与可控项（MVP 级别）
- 昵称唯一性/冲突处理（自动加后缀）。
- 基础限流（同一用户短时间内触发 AI 次数限制，防止刷接口）。
- 不做复杂登录；如需要可后续加入 token/房间密码。

## 1) 需要你确认的问题（影响实现细节）
1. **聊天形态**：是「所有人一个公共房间 + 1 个 AI」还是需要「多个房间」？
回答：多个房间
2. **AI 提供方**：你希望接 OpenAI API（提供 `OPENAI_API_KEY`）还是本地模型（如 Ollama/LM Studio）？
openai api（OpenAI 兼容），`OPENAI_API_KEY` 写入 `.env`（不要提交到仓库），base url：https://api.agicto.cn/v1
3. **AI 触发方式**：只在 `/ai ...` 时回复（推荐），还是每条消息都自动回复？
每条消息都自动回复
4. **历史记录**：需要落盘保存（SQLite）吗？还是只做内存（重启丢失）？
暂时哪个简单按哪个
5. **部署目标**：只需本机访问，还是要公网访问（需要域名/HTTPS/反代）？
公网访问

> 你回复以上问题后，我会按你的偏好微调计划；若你不想纠结，我会按“推荐”默认值推进。

## 2) 执行计划（你认可后我再逐步执行）

### Step: chat-ai-web
- [√] 1. 明确需求与默认值（根据你回复定稿）
  - 结果：支持多房间（前端输入 room）；AI 使用 OpenAI 兼容接口（支持自定义 base_url）；AI 默认每条用户消息自动回复（且不会对自己的消息触发，按房间串行生成避免爆并发）；历史先做内存；部署按公网可用（Docker + 0.0.0.0 监听，HTTPS 交给反代）。
- [√] 2. 初始化工程结构（`app/`、`static/`、`process/`、`logs/`、`.env.example`）
  - 结果：已创建目录与基础文件：`app/`、`static/`、`process/`、`logs/`、`.env.example`、`process/2026-04-23.md`。
- [√] 3. 实现 WebSocket 聊天后端（连接管理、广播、在线列表、系统消息）
  - 结果：已实现 FastAPI WebSocket `/ws`（按 room 隔离）；支持聊天广播、系统加入/离开提示、在线列表广播（presence）、新连接下发历史（history）。
- [√] 4. 接入 AI 模块（可配置模型/Key，缺省可回声；支持 `/ai` 指令）
  - 结果：新增 OpenAI 兼容 AI 模块（支持 `OPENAI_BASE_URL`/`OPENAI_API_KEY`/model 配置），按房间串行队列生成；默认配置好 Key 后每条消息自动回复；同时支持 `/ai ...`、`@ai ...` 强制触发（未配置 Key 时走回声）。
- [√] 5. 实现前端页面（昵称、消息列表、输入框、基础样式、指令提示）
  - 结果：已实现 `static/index.html` + `static/app.js` + `static/styles.css`：支持输入昵称/房间连接 WebSocket，渲染 chat/system/presence/history 事件，展示在线用户与基础样式。
- [√] 6. 增加部署与运行方式（`requirements.txt`、Dockerfile、可选 docker-compose）
  - 结果：已新增 `requirements.txt`、`Dockerfile`、`docker-compose.yml`（支持读取 `.env` 并映射端口）。
- [√] 7. 补充最小验证脚本/说明（后台运行示例 + 日志落到 `logs/月-日/`）
  - 结果：已新增后台启动脚本 `scripts/run_server_bg.py`：按规范把日志写入 `logs/月-日/时-分_run_server.log`，并输出 PID 与日志路径。
- [√] 8. 更新 `README.md`（启动/配置/常见问题，尽量简洁）
  - 结果：已在 `README.md` 顶部补充 Chat AI Web 的快速开始（含后台运行与日志规范）、Docker 启动与公网反代提示；同时新增 `.gitignore`（忽略 `.env`、`logs/` 等）。
- [√] 9. 产物整理：把本 TODO 迁移到 `Done/chat-ai-web.md` 并删除 `TODO.md`
  - 结果：已同步到 `Done/chat-ai-web.md`，并已获得允许删除 `TODO.md`（将立即执行删除以完成归档）。
