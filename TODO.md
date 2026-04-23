# 部署上线（GitHub + 一键自动部署）

## 0) 目标
- 代码放到 GitHub，并实现 **push 后自动部署**（PaaS 平台自动 build/run，提供 HTTPS，支持 `wss://`）。
- 尽量“少运维”：不需要自建反代、不需要自己续证书。

## 1) 需要你确认的 3 个信息（决定具体落地平台）
1. 你更倾向的平台：**Render（推荐）** / Railway / Fly.io（任选其一）
2. GitHub 仓库：你希望仓库名是什么？公开还是私有？
3. 域名：是否有自己的域名要绑定？（没有也可以用平台默认域名先上线）

> 你确认这 3 点后，我会把部署配置与 README 指令按对应平台写全。

### 你已确认
- 平台：Render
- GitHub：将创建新仓库，公开
- 域名：暂无（先用 Render 默认域名）
- 额外改动：`OPENAI_API_KEY` / `OPENAI_BASE_URL` 改为**用户在网页端输入**（服务端不内置 Key，避免公网刷 Key 成本）

## 2) 执行计划（你认可后我再逐步执行）

### Step: deploy-github
- [√] 1. 让项目适配 PaaS（端口/环境变量/启动方式 + 网页端输入 key/base_url）
  - 结果：后端新增 WebSocket `config` 消息（用户在线提交 `API Key`/`Base URL`/model，服务端仅内存使用不落盘）；前端增加对应输入框；Dockerfile 支持 `$PORT`，`settings` 支持 `PORT` 回退，适配 Render。
- [ ] 2. 初始化 git 仓库并生成推送指令（不写入任何密钥）
- [√] 2. 初始化 git 仓库并生成推送指令（不写入任何密钥）
  - 结果：已执行 `git init` 并提交到 `main` 分支（commit: `d7498e8`）。待你创建 GitHub 公共仓库后，添加 remote 并 push 即可。
- [√] 3. 增加平台部署说明（按你选的平台：Render）
  - 结果：已新增 `deploy/render.md`（GitHub → Render Web Service(Docker) → Auto Deploy），并补充注意事项（单实例、Base URL 校验等）。
- [√] 4. 更新 `README.md`（一键部署 + 环境变量清单 + WebSocket 注意事项）
  - 结果：README 顶部增加 Render 部署入口与可选环境变量清单，并明确“单进程内存房间”限制。
- [ ] 5. 产物整理：把本 TODO 迁移到 `Done/deploy-github.md` 并删除 `TODO.md`
  - 结果：
