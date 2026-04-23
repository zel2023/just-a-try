# Render 部署（GitHub 自动部署）

本项目支持 WebSocket（聊天）+ AI（OpenAI 兼容）。建议用 Render 的 **Web Service + Docker** 部署，开启 Auto Deploy 后，每次 push 到 GitHub 会自动重新部署。

## 1) 推送到 GitHub（公开仓库）

1. 在 GitHub 新建一个 **Public** 仓库（不要勾选创建 README/License，避免冲突）
2. 在本地仓库执行（把 `<YOUR_GITHUB>`、`<REPO>` 替换成你的信息）：

```bash
git remote add origin https://github.com/<YOUR_GITHUB>/<REPO>.git
git push -u origin main
```

## 2) Render 创建 Web Service（Docker）

1. Render Dashboard → New → **Web Service**
2. 连接 GitHub，选择你的仓库
3. Runtime/Environment 选择 **Docker**
4. 确认 Auto Deploy 为 ON（默认通常为 ON）
5. Health Check Path 建议填：`/healthz`

### 环境变量（Render → Environment）

无需设置任何服务端 `OPENAI_API_KEY`（API Key 由用户在网页端输入）。

可选：
- `OPENAI_BASE_URL`：默认 Base URL（显示在网页输入框里）
- `OPENAI_MODEL`：默认模型名（显示在网页输入框里）
- `AI_NAME`：AI 昵称（默认 `AI`）
- `AI_AUTO_REPLY`：是否自动回复（默认 `true`；只有用户填写 API Key 才会触发）

## 3) 验证

1. Render 部署完成后，打开它给你的 URL
2. 输入昵称/房间
3. 在 `API Key` 里粘贴你自己的 Key（可选勾选“在浏览器保存 API Key”）
4. 发送消息观察 AI 回复；或用 `/ai 你好` 强制触发一次

## 4) 注意事项

- 当前为**单进程内存房间**：不要在 Render 上开多实例，否则同一房间的用户会被分散到不同实例里看不到彼此消息。
- Base URL 仅允许 `https://`，并禁止本地/内网 IP（避免 SSRF 风险）。

