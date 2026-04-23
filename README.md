# Chat AI Web（多人在线 + AI）

一个简单的多人实时聊天室（WebSocket），支持**多房间**，并接入 **OpenAI 兼容**的 AI（支持自定义 `OPENAI_BASE_URL`）。  
默认行为：在网页侧填写 `API Key` 后，AI 会对你发送的每条消息自动回复；也可用 `/ai ...` 或 `@ai ...` 强制触发一次（未配置 Key 会回声）。

## 快速开始（推荐：Python）

1) 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) 配置（可选：只用于默认 Base URL / 模型名）

```bash
cp .env.example .env
```

编辑 `.env`：按需修改 `OPENAI_BASE_URL`、`OPENAI_MODEL`（会显示在网页输入框里）。  
`API Key` 建议直接在网页端输入（可勾选“在浏览器保存 API Key”）。

3) 后台启动（日志会写入 `logs/月-日/时-分_run_server.log`）

```bash
python scripts/run_server_bg.py
```

浏览器打开：`http://localhost:8000/`  
（公网部署时，用 Nginx/Caddy 等反代到 8000，并启用 HTTPS 以支持 `wss://`）

注意：当前为**单进程内存房间**实现（MVP）。不要用多 worker 启动（例如 `--workers 4`），否则同一房间的用户可能分散在不同进程里看不到彼此消息。

## 环境变量（可选）

- `OPENAI_BASE_URL`：默认 Base URL（显示在网页输入框里）
- `OPENAI_MODEL`：默认模型名（显示在网页输入框里）
- `AI_NAME`：AI 昵称（默认 `AI`）
- `AI_AUTO_REPLY`：是否自动回复（默认 `true`；只有用户填写 API Key 才会触发）

## Docker（可选）

```bash
cp .env.example .env
docker compose up --build -d
docker compose logs -f
```

## 部署到 Render（GitHub 自动部署）

部署说明见：`deploy/render.md`。

---

# Codex 使用指南

本文档基于当前机器在 2026-04-01 可观察到的环境整理，当前安装版本为 `codex-cli 0.115.0`。  
目标是让你在 `/data/zelongzheng` 下可以直接上手使用 Codex，并知道常见命令、配置入口、会话恢复、代码审查、权限控制和安全边界。

## 1. Codex 是什么

Codex CLI 是一个面向开发任务的命令行智能代理。它可以：

- 理解代码库结构
- 读取、修改和新增文件
- 运行测试、构建、格式化、静态检查等命令
- 做代码审查
- 在交互模式和非交互模式下工作
- 通过 MCP 接入外部工具或文档源

如果你直接运行 `codex` 而不带子命令，默认进入交互式会话。

## 2. 当前机器上的相关位置

### 2.1 工作目录

当前操作目录：

```bash
/data/zelongzheng
```

本文档放在：

```bash
/data/zelongzheng/codex/README.md
```

### 2.2 Codex 本地配置目录

当前机器上的 Codex 主目录在：

```bash
~/.codex
```

常见文件和目录：

- `~/.codex/config.toml`
  Codex 主配置文件
- `~/.codex/auth.json`
  登录认证信息
- `~/.codex/history.jsonl`
  历史记录
- `~/.codex/sessions/`
  会话数据
- `~/.codex/log/`
  日志目录
- `~/.codex/skills/`
  已安装技能
- `~/.codex/logs_*.sqlite`、`state_*.sqlite`
  本地状态和日志数据库

注意：

- 不要把 `auth.json`、私有配置、会话日志直接提交到公共仓库。
- 如果你在服务器或共享环境下使用 Codex，先确认 `~/.codex` 的权限和备份策略。

## 3. 当前机器的配置概况

当前机器能读到的 `~/.codex/config.toml` 里，核心配置大致如下：

```toml
model_provider = "IkunCoding"
model = "gpt-5.4"
model_reasoning_effort = "xhigh"
disable_response_storage = true
approval_policy = "on-request"
sandbox_mode = "danger-full-access"
model_supports_reasoning_summaries = true

[projects."/data/zelongzheng"]
trust_level = "trusted"
```

这些字段的含义：

- `model_provider`
  指定模型提供方
- `model`
  默认模型名
- `model_reasoning_effort`
  推理强度，越高通常越慢但更深入
- `disable_response_storage = true`
  禁止保存响应内容
- `approval_policy`
  命令执行时的审批策略
- `sandbox_mode`
  shell 命令的沙箱级别
- `trust_level = "trusted"`
  当前项目目录被标记为可信

如果你切到别的项目路径，Codex 是否自动信任、是否允许写入，会受该目录的项目信任配置影响。

## 4. 最常用的启动方式

### 4.1 交互模式

最简单的启动方式：

```bash
codex
```

带一段初始任务描述启动：

```bash
codex "检查当前仓库里的测试失败原因并直接修复"
```

指定工作目录：

```bash
codex -C /path/to/project "先阅读代码结构，再实现需求"
```

带图片输入：

```bash
codex -i ./ui.png "根据这张界面图实现页面"
```

### 4.2 非交互模式

一次性执行任务：

```bash
codex exec "为当前仓库补一份 README，包含安装和运行说明"
```

从标准输入读取提示词：

```bash
printf '%s\n' "检查 src/ 下的死代码并给出修改" | codex exec -
```

将最终回复写到文件：

```bash
codex exec "总结当前仓库结构" -o last_message.txt
```

输出 JSONL 事件流：

```bash
codex exec --json "运行测试并输出关键失败点"
```

## 5. 登录与认证

查看登录状态：

```bash
codex login status
```

通过环境变量中的 API Key 登录：

```bash
printenv OPENAI_API_KEY | codex login --with-api-key
```

设备登录方式：

```bash
codex login --device-auth
```

退出登录：

```bash
codex logout
```

建议：

- 优先用环境变量或安全密钥管理工具注入 API Key。
- 不要把密钥明文写入脚本、仓库或共享笔记。

## 6. 核心命令总览

运行 `codex --help` 可以看到核心命令。常用子命令如下。

### 6.1 `codex`

交互式主入口。

常见用途：

- 探索代码库
- 逐步修改代码
- 在执行过程中与代理来回协作

### 6.2 `codex exec`

非交互执行任务。

适合：

- 批处理
- CI/CD 辅助
- 一次性文档生成
- 自动审查或自动修改

常见参数：

- `--skip-git-repo-check`
  允许在非 Git 仓库中运行
- `--ephemeral`
  不持久化会话到磁盘
- `--output-schema <FILE>`
  给最终输出指定 JSON Schema
- `--json`
  以 JSONL 输出事件
- `-o, --output-last-message <FILE>`
  把最后一条消息写入文件

### 6.3 `codex review`

非交互式代码审查。

常用方式：

```bash
codex review --uncommitted
codex review --base main
codex review --commit <SHA>
```

适合：

- 审查未提交改动
- 审查某个提交
- 对比某个基线分支的差异

### 6.4 `codex resume`

恢复之前的交互式会话。

```bash
codex resume --last
codex resume <SESSION_ID>
```

适合：

- 接着上次任务继续做
- 恢复上下文，避免重新解释背景

### 6.5 `codex fork`

从已有会话分叉一个新分支式会话。

```bash
codex fork --last
codex fork <SESSION_ID> "基于上次结果尝试另一种实现"
```

适合：

- 试两套不同实现方案
- 保留主线会话，同时探索替代方向

### 6.6 `codex apply`

把某个任务产出的最新 diff 应用到本地工作树。

```bash
codex apply <TASK_ID>
```

适合：

- 从云端任务或其他执行环境回收变更

### 6.7 `codex mcp`

管理外部 MCP 服务。

支持：

- `codex mcp list`
- `codex mcp get <name>`
- `codex mcp add ...`
- `codex mcp remove <name>`
- `codex mcp login <name>`
- `codex mcp logout <name>`

示例：

```bash
codex mcp list
codex mcp add openaiDeveloperDocs --url https://developers.openai.com/mcp
```

### 6.8 `codex completion`

生成 shell 自动补全脚本。

```bash
codex completion bash
codex completion zsh
codex completion fish
```

### 6.9 `codex sandbox`

用 Codex 提供的沙箱运行命令。

```bash
codex sandbox linux <command>
```

当前帮助信息显示支持：

- `linux`
- `macos`
- `windows`

### 6.10 其他命令

- `codex mcp-server`
  以 MCP server 形式启动 Codex
- `codex app-server`
  实验性 app server 或相关工具
- `codex debug`
  调试工具
- `codex cloud`
  浏览 Codex Cloud 任务并可本地应用变更
- `codex features`
  查看功能开关

## 7. 常用全局参数

这些参数在多个命令里都可见。

### 7.1 模型与配置

- `-m, --model <MODEL>`
  指定模型
- `-p, --profile <CONFIG_PROFILE>`
  指定配置 profile
- `-c, --config <key=value>`
  临时覆盖配置项

示例：

```bash
codex -m gpt-5.4 "解释这个项目的架构"
codex -c model_reasoning_effort='"high"' "分析这个并发 bug"
codex -c shell_environment_policy.inherit=all "检查环境变量依赖"
```

注意：

- `-c` 的值按 TOML 解析。
- 复杂值如数组或字符串，最好显式加引号。

### 7.2 沙箱与审批

- `-s, --sandbox <SANDBOX_MODE>`
  可选：`read-only`、`workspace-write`、`danger-full-access`
- `-a, --ask-for-approval <APPROVAL_POLICY>`
  可选：`untrusted`、`on-failure`、`on-request`、`never`
- `--full-auto`
  等价于低摩擦自动执行：`-a on-request` + `--sandbox workspace-write`
- `--dangerously-bypass-approvals-and-sandbox`
  彻底跳过审批和沙箱，风险极高

推荐理解：

- `read-only`
  只能读，适合纯分析
- `workspace-write`
  可修改工作区，适合大多数开发任务
- `danger-full-access`
  几乎不设限制，只适合你能接受全部命令副作用的环境

审批策略建议：

- 日常开发优先 `on-request`
- 批处理脚本可以考虑 `never`
- 不熟悉仓库时不要直接上 `danger-full-access`

### 7.3 目录与搜索

- `-C, --cd <DIR>`
  指定工作根目录
- `--add-dir <DIR>`
  额外允许写入的目录
- `--search`
  启用在线搜索能力

示例：

```bash
codex -C /data/zelongzheng/llm_judge "解释项目入口和主要模块"
codex --search "查一下这个报错对应的官方修复建议"
```

### 7.4 本地开源模型

- `--oss`
  选择本地开源模型提供方
- `--local-provider <lmstudio|ollama>`
  指定本地 provider

示例：

```bash
codex --oss "阅读这个仓库并总结构建方式"
codex --oss --local-provider ollama "帮我审查这个脚本"
```

## 8. 推荐工作流

### 8.1 进入一个代码仓库后

建议从仓库根目录启动：

```bash
cd /path/to/repo
codex
```

第一轮提示词尽量包含：

- 目标
- 限制条件
- 允许改动的范围
- 验证方式

例如：

```text
先阅读仓库结构，只总结，不改代码。然后定位 pytest 失败原因，修复最小必要范围，最后运行相关测试并说明结果。
```

### 8.2 让 Codex 更高效的提示方式

好提示词通常包含：

- 要解决的问题
- 输出形式
- 是否允许改代码
- 是否要运行测试
- 是否只做分析不落盘

示例 1：纯分析

```text
只阅读并总结项目架构，不要修改任何文件。重点说明入口、核心模块、配置来源和测试方式。
```

示例 2：直接修复

```text
修复当前仓库里导致 `pytest tests/api/test_auth.py` 失败的问题，只修改必要文件，完成后运行相关测试。
```

示例 3：文档生成

```text
在 docs/ 下新增一份部署文档，覆盖依赖安装、环境变量、启动命令和常见报错。
```

### 8.3 一次任务的理想闭环

1. 先让 Codex 读代码和定位问题  
2. 再让它实现修改  
3. 然后要求它运行测试或构建  
4. 最后要求它总结修改点、风险和未覆盖项

## 9. 代码审查工作流

### 9.1 审查未提交改动

```bash
codex review --uncommitted
```

适合在提交前做一次问题扫描。

### 9.2 基于分支做审查

```bash
codex review --base main
```

适合当前分支与 `main` 做差异审查。

### 9.3 审查某个提交

```bash
codex review --commit abcdef123456
```

如果你想强调审查重点，也可以加额外提示词：

```bash
codex review --base main "重点检查并发安全、异常处理和回归风险"
```

## 10. 会话管理

### 10.1 恢复最近一次会话

```bash
codex resume --last
```

### 10.2 恢复指定会话

```bash
codex resume <SESSION_ID>
```

### 10.3 分叉最近一次会话

```bash
codex fork --last
```

适合在不破坏原对话链的情况下尝试另一种策略。

## 11. 配置文件写法

主配置文件位置：

```bash
~/.codex/config.toml
```

一个简化示例：

```toml
model_provider = "IkunCoding"
model = "gpt-5.4"
model_reasoning_effort = "high"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
disable_response_storage = true

[projects."/data/zelongzheng/my-project"]
trust_level = "trusted"
```

说明：

- 想要更保守的默认行为，可以把 `sandbox_mode` 改为 `workspace-write` 或 `read-only`
- 不同项目可以有不同信任等级
- 某些命令行参数可以临时覆盖配置，不必每次改 TOML

临时覆盖示例：

```bash
codex -c sandbox_mode='"read-only"' "只做分析"
codex -c approval_policy='"never"' exec "跑一遍自动检查"
```

## 12. 自动补全配置

### 12.1 Bash

```bash
codex completion bash
```

你可以把输出重定向到本地补全目录，例如：

```bash
codex completion bash > ~/.local/share/bash-completion/completions/codex
```

### 12.2 Zsh

```bash
codex completion zsh > ~/.zfunc/_codex
```

### 12.3 Fish

```bash
codex completion fish > ~/.config/fish/completions/codex.fish
```

## 13. MCP 扩展能力

MCP 可以理解为给 Codex 接外部工具、文档源或服务的协议层。

典型用途：

- 接入官方文档
- 接入数据库查询工具
- 接入内部平台
- 接入额外搜索或分析工具

常用命令：

```bash
codex mcp list
codex mcp get openaiDeveloperDocs
codex mcp add openaiDeveloperDocs --url https://developers.openai.com/mcp
codex mcp remove openaiDeveloperDocs
```

如果某个 MCP 服务要求认证，可以再执行：

```bash
codex mcp login <name>
codex mcp logout <name>
```

## 14. 使用建议

### 14.1 让结果更可控

- 先给范围，再给任务
- 明确哪些文件能改，哪些不能改
- 明确是否要运行测试
- 明确最终要什么格式的输出

### 14.2 让改动更安全

- 新仓库先用 `read-only` 或 `workspace-write`
- 大改之前先让它只分析，不落盘
- 改完后让它运行最相关的测试
- 自己再看一遍 diff，不要盲合并

### 14.3 让上下文更稳定

- 在仓库根目录启动
- 描述模块名、文件路径、失败命令
- 长任务用 `resume` 持续推进
- 分支方案用 `fork`，不要把多种实现混在一个会话里

## 15. 常见问题

### 15.1 `codex: command not found`

先确认是否已经安装并在 `PATH` 中：

```bash
which codex
codex --version
```

### 15.2 不在 Git 仓库里无法运行

可以使用：

```bash
codex exec --skip-git-repo-check "在当前目录生成项目说明"
```

### 15.3 命令执行权限太严格或太宽松

检查：

- `approval_policy`
- `sandbox_mode`

推荐先从：

```toml
approval_policy = "on-request"
sandbox_mode = "workspace-write"
```

开始。

### 15.4 想看在线资料但当前会话没有搜索能力

启动时加：

```bash
codex --search
```

### 15.5 想保留记录，但又不想把响应写盘

检查配置中的：

```toml
disable_response_storage = true
```

如果开启了这一项，响应不会持久化保存。

## 16. 一组可以直接复制的常用命令

### 16.1 阅读仓库

```bash
codex "先阅读当前仓库结构，只输出模块关系和启动方式，不修改文件"
```

### 16.2 修复测试

```bash
codex "定位并修复当前仓库导致 pytest 失败的问题，只修改必要文件，最后运行相关测试"
```

### 16.3 生成文档

```bash
codex "在 docs/ 下新增部署文档，覆盖环境变量、安装步骤、启动方式和回滚建议"
```

### 16.4 非交互总结

```bash
codex exec "总结当前项目目录的主要模块和用途" -o summary.txt
```

### 16.5 审查当前改动

```bash
codex review --uncommitted "优先找 bug、回归风险和测试缺口"
```

## 17. 最后建议

把 Codex 当成一个会读代码、会运行命令、会修改文件的工程代理，而不是普通聊天工具。  
你给它的任务边界越清楚，它给出的结果通常越稳。

最实用的三个习惯：

1. 先让它分析，再让它修改  
2. 修改后要求它验证  
3. 自己最终审一次 diff 和测试结果
