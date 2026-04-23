# 从 Claude Code 迁移到 Codex：快速入门

本文面向“已经用过 Claude Code，但第一次用 Codex”的开发者。  
目标不是完整手册，而是帮你快速建立映射关系：你在 Claude Code 里常用的概念，在 Codex 里分别对应什么、有什么差别、第一天最该掌握什么。

本文结合两类信息：

- 当前机器本地可见的 `codex-cli 0.115.0`
- OpenAI 官方 Codex 文档与产品说明

---

## 1. 先说结论

如果你之前主要关注的是：

- `CLAUDE.md`
- `MCP`
- `skills`
- `resume`

那么在 Codex 里基本都能找到对应物，而且大多数能力不只是“有”，而是更工程化：

| Claude Code 习惯 | Codex 对应功能 | 是否有一一对应 | 你最该知道的区别 |
| --- | --- | --- | --- |
| `CLAUDE.md` | `AGENTS.md` | 基本对应 | Codex 的指令文件有层级、覆盖和回退文件名机制，比单文件更强 |
| `MCP` | `MCP` | 完全对应 | Codex 原生支持 CLI/IDE 共用配置，支持 `stdio` 和 HTTP MCP |
| `skills` | `skills` | 完全对应 | Codex 的 skill 更像“可打包工作流”，支持脚本、资源、依赖、插件化分发 |
| `resume` | `resume` | 完全对应 | Codex 还多了 `fork`，很适合从同一上下文分叉不同方案 |

如果只让我给你三个最值得优先上手的点：

1. 学会 `AGENTS.md`
2. 学会 `resume` + `fork`
3. 学会 `review` + `exec`

---

## 2. `CLAUDE.md` 在 Codex 里对应什么

### 2.1 对应物：`AGENTS.md`

在 Codex 里，最接近 `CLAUDE.md` 的不是别的，就是 `AGENTS.md`。

官方文档明确说明：

- Codex 会在开始工作前读取 `AGENTS.md`
- 它会把这些文件作为项目附加指令
- 你可以用它告诉 Codex 如何理解仓库、如何运行测试、以及遵守哪些工程规范

核心区别不在“有没有”，而在“更分层”。

### 2.2 Codex 的 `AGENTS.md` 比 `CLAUDE.md` 更强的地方

Codex 对指令文件的发现顺序是分层的：

1. 全局层：`~/.codex/AGENTS.md` 或 `~/.codex/AGENTS.override.md`
2. 项目层：从仓库根目录一直走到你当前工作目录
3. 每一层都按 `AGENTS.override.md` -> `AGENTS.md` -> fallback 文件名的顺序寻找

更重要的是：

- 离你当前目录越近的文件，优先级越高
- `AGENTS.override.md` 可以临时覆盖同目录下的 `AGENTS.md`
- 可以配置备用文件名，让 Codex 直接把别的文件也当指令文件读

这点对你很关键，因为它意味着：

- 你可以保留一份全局个人偏好
- 仓库根目录放团队规范
- 某个子模块再放局部 override

这比把所有内容堆进一个 `CLAUDE.md` 更适合大型仓库。

### 2.3 迁移建议：你甚至可以先不改名

如果你仓库里已经有 `CLAUDE.md`，最省事的办法不是立刻批量重命名，而是先在 `~/.codex/config.toml` 里加 fallback 文件名：

```toml
project_doc_fallback_filenames = ["CLAUDE.md", ".agents.md"]
project_doc_max_bytes = 65536
```

这样 Codex 就可以把 `CLAUDE.md` 当成项目指令文件来发现。

如果你想长期统一，建议还是逐步迁移到：

- 全局：`~/.codex/AGENTS.md`
- 仓库根：`<repo>/AGENTS.md`
- 子目录 override：`<repo>/subdir/AGENTS.override.md`

### 2.4 你该怎么写 `AGENTS.md`

建议只写这些高价值信息：

- 仓库的测试命令
- 构建命令
- 哪些目录能改，哪些不能改
- 提交或 PR 习惯
- 代码风格和验证要求
- 敏感操作约束

一个很实用的根目录示例：

```md
# AGENTS.md

## Working Rules

- 修改 Python 代码后先运行 `pytest -q`
- 修改前端代码后运行 `pnpm test` 和 `pnpm lint`
- 不要改 `infra/` 下的部署脚本，除非用户明确要求
- 新增依赖前先说明理由
- 输出时先给 findings，再给 change summary
```

### 2.5 与 Claude Code 的心智差异

你可以把它理解成：

- `CLAUDE.md` 更像“项目说明书”
- Codex 的 `AGENTS.md` 更像“分层可继承的代理操作规约”

换句话说，Codex 在这块不是少了，而是更系统。

---

## 3. `MCP` 在 Codex 里怎么样

### 3.1 对应物：还是 `MCP`

这块几乎不用迁移心智模型。Codex 原生支持 MCP。

你会继续用它来给代理增加：

- 文档源
- 数据库/内部系统访问
- 浏览器自动化
- 设计工具
- 团队内部工具

### 3.2 Codex 里的 MCP 特点

根据官方文档和本机 CLI，Codex 的 MCP 有这些特点：

- 配置存在 `config.toml`
- CLI 和 IDE extension 共用 MCP 配置
- 可以用 `codex mcp add/get/list/remove/login/logout`
- 支持 `stdio` 启动的本地 MCP server
- 也支持 HTTP MCP server
- 可以在 TUI 里用 `/mcp` 看当前激活的服务器

你可以把它理解为：

- 协议层没变
- Codex 把 CLI、IDE、技能依赖和配置管理打通得更完整

### 3.3 最常用命令

查看已配置的 MCP：

```bash
codex mcp list
```

添加一个 `stdio` MCP：

```bash
codex mcp add context7 -- npx -y @upstash/context7-mcp
```

查看单个 MCP 详情：

```bash
codex mcp get context7
```

### 3.4 与 Claude Code 的差异

Codex 的优势主要在这几个方向：

- 配置和产品形态更统一：CLI、IDE、App 可以共用
- skill 可以声明 MCP 依赖
- 插件也可以连带 MCP 配置一起打包

所以在 Codex 里，MCP 不只是“工具接入”，还更容易进入团队级复用。

---

## 4. `skills` 在 Codex 里是什么

### 4.1 对应物：也是 `skills`

这一点可以直接平移，但要升级理解：

在 Codex 里，skill 不是一句“附加提示词”，而是一整个可复用的能力包。

官方文档定义里，一个 skill 至少包含：

- `SKILL.md`

还可以带：

- `scripts/`
- `references/`
- `assets/`
- `agents/openai.yaml`

### 4.2 Skill 在 Codex 里的结构

典型结构：

```text
my-skill/
├── SKILL.md
├── scripts/
├── references/
├── assets/
└── agents/
    └── openai.yaml
```

这意味着一个 skill 可以同时封装：

- 何时触发
- 工作流程
- 参考文档
- 执行脚本
- UI 元数据
- 工具依赖

所以它比很多人理解里的“技能提示词”更接近“可安装的工作流模块”。

### 4.3 Codex 怎么触发 skill

Codex 有两种触发方式：

1. 显式触发
2. 隐式触发

显式触发：

- 在提示词里直接提 skill
- 在 CLI/IDE 里用 `/skills`
- 或输入 `$skill-name`

隐式触发：

- 当你的任务和 skill 的 `description` 匹配时，Codex 自动启用

所以 skill 的 `description` 写得准不准，直接决定自动触发效果。

### 4.4 Skill 应该放在哪里

官方文档给出的主要位置是：

- 仓库级：`.agents/skills`
- 用户级：`$HOME/.agents/skills`
- 管理级：`/etc/codex/skills`
- 系统级：Codex 自带

对你最实用的做法：

- 团队共享技能放 `<repo>/.agents/skills/`
- 个人常用技能放 `~/.agents/skills/`

说明：

当前这个代理环境里你也能看到 `~/.codex/skills` 这样的系统技能目录，但面向普通 Codex 使用者的官方文档，用户级技能位置是 `~/.agents/skills`。  
也就是说，文档里讲的是“你平时自己配置和分发 skill 的入口”，而当前运行环境里还存在一套系统内置技能目录。

### 4.5 与 Claude Code 的差异

如果你之前已经在 Claude Code 里用 skill/workflow 类能力，到了 Codex 最需要记住这几点：

- Codex skill 更强调目录化和可分发
- skill 可带脚本和参考资料，不只是指令文本
- 可以被隐式自动触发
- 可以进一步打包成 plugin 分发

一句话总结：

Claude Code 的“技能”更像操作经验；Codex 的 skill 更像工程化能力包。

### 4.6 两个非常实用的内置入口

创建 skill：

```text
$skill-creator
```

安装 curated skills：

```text
$skill-installer
```

如果你后面想把自己的工作流沉淀下来，优先学这个，而不是只堆 prompt。

---

## 5. `resume` 在 Codex 里怎么用

### 5.1 对应物：`resume`

Codex 有明确的会话恢复能力，而且本机 CLI 已经内置：

```bash
codex resume --last
codex resume <SESSION_ID>
```

这点你几乎可以无缝迁移。

### 5.2 最值得你注意的不是 `resume`，而是 `fork`

Codex 在恢复会话之外，还有一个非常实用的能力：

```bash
codex fork --last
codex fork <SESSION_ID>
```

这相当于：

- 保留原会话上下文
- 从当前状态分叉一个新方向
- 试另一套实现而不污染主线

如果你以前在 Claude Code 里经常遇到“同一段上下文里开始讨论两套方案，后来混了”的情况，Codex 的 `fork` 很适合你。

### 5.3 `resume` 的实际使用建议

推荐这样用：

- 当任务中断时用 `resume --last`
- 当你想尝试另一种实现时用 `fork --last`
- 当你切换仓库或目录时，最好从对应目录再启动会话

本机 CLI 帮助还显示：

- `resume` 默认会按 cwd 过滤会话
- 用 `--all` 可以看全部会话

这对多仓库开发很有用。

### 5.4 一个你会马上用上的套路

```bash
codex "先定位问题，不改代码"
codex resume --last "现在开始修复，只改最小范围"
codex fork --last "再给我尝试一个更激进的重构版本"
```

这套操作在 Codex 里非常自然。

---

## 6. 除了你提到的 4 个功能，Codex 里最实用的还有什么

下面这些是我更建议你尽快上手的。

### 6.1 `review`

如果你平时会做代码审查，这个命令很值得优先掌握：

```bash
codex review --uncommitted
codex review --base main
codex review --commit <SHA>
```

适用场景：

- 提交前扫风险
- 分支对比分支
- 审查某个提交的行为回归

为什么很实用：

- 它是 Codex 的一等功能，不是让你自己拼 prompt 的替代品
- 很适合本地改完后做一次“AI reviewer 预审”

### 6.2 `exec`

`exec` 是 Codex 很强的地方，尤其适合脚本化和自动化：

```bash
codex exec "总结当前仓库结构"
codex exec --json "输出模块信息"
codex exec --output-schema schema.json -o result.json "抽取项目元数据"
```

实用价值：

- 可用于脚本、CI、批处理
- 支持 JSONL 事件流
- 支持结构化最终输出

如果你想把 Codex 真正接进工程流，而不是只当聊天工具，`exec` 很关键。

### 6.3 `cloud`

Codex 很强调异步委托和并行任务，这一点是它非常鲜明的产品方向。

本机 CLI 已经有：

```bash
codex cloud exec
codex cloud status
codex cloud list
codex cloud diff
codex cloud apply
```

这类能力适合：

- 让任务在云端后台跑
- 你本地继续做别的事
- 等结果出来后再拉 diff 或应用改动

如果你之前主要把 AI 当成本地 pairing partner，Codex 会更强地把你往“异步协作 + 多代理”工作流上带。

### 6.4 沙箱和审批策略

这也是 Codex 非常值得熟悉的部分。

关键参数：

```bash
--sandbox read-only|workspace-write|danger-full-access
--ask-for-approval untrusted|on-request|never
```

对第一次用 Codex 的人，我的建议很直接：

- 不要默认长期使用 `danger-full-access`
- 日常建议优先 `workspace-write`
- 审批策略优先 `on-request`

你这台机器当前配置里已经是：

```toml
approval_policy = "on-request"
sandbox_mode = "danger-full-access"
```

如果你只是想安全上手，建议未来把默认沙箱改成：

```toml
sandbox_mode = "workspace-write"
```

然后按需提升权限。

### 6.5 `apply`

这个命令在“云端任务 -> 本地落地”链路里很有用：

```bash
codex apply <TASK_ID>
```

如果你以后开始频繁使用云端任务或异步代理，这个会变得很常用。

### 6.6 worktrees

Codex 官方产品还很强调 worktrees，尤其在 App 里：

- 多个 agent 可以并行处理同一个仓库
- 各自用隔离副本工作
- 降低互相污染 Git 状态的风险

如果你已经习惯手动开多个分支/工作目录，Codex 在这条路上会走得更远。

---

## 7. 给 Claude Code 老用户的最短迁移路线

如果你不想看太多文档，按下面 6 步就够你快速进入状态。

### 第 1 步：先让 Codex 兼容你现有的 `CLAUDE.md`

在 `~/.codex/config.toml` 里加：

```toml
project_doc_fallback_filenames = ["CLAUDE.md", ".agents.md"]
```

这样你可以先不重构仓库说明文件。

### 第 2 步：再补一个个人全局规则

创建：

```bash
~/.codex/AGENTS.md
```

写你个人固定偏好，例如：

- 修改代码后总要跑测试
- 不要擅自新增依赖
- 输出要先给结论再给细节

### 第 3 步：开始把团队规范迁到仓库根 `AGENTS.md`

把真正项目相关的东西写到仓库里，而不是全堆在个人配置里。

### 第 4 步：把可复用工作流做成 skill

例如：

- 部署某个服务
- 读取内部规范并生成文档
- 拉设计稿并转成页面
- 固定格式的数据分析与报告

### 第 5 步：把 `resume` 和 `fork` 当成标配

不要每次重新解释上下文。

### 第 6 步：尽早用 `review` 和 `exec`

这两个功能最容易把 Codex 变成真正的工程工具，而不是对话工具。

---

## 8. 一套你现在就可以直接用的命令

### 8.1 像 Claude Code 一样先读仓库，不改代码

```bash
codex "先阅读当前仓库结构，只总结模块关系、入口、测试方式，不修改文件"
```

### 8.2 继续上次任务

```bash
codex resume --last
```

### 8.3 从上次任务分叉一个新方案

```bash
codex fork --last "保留原方案，再尝试一个更激进的重构版本"
```

### 8.4 审查当前未提交改动

```bash
codex review --uncommitted "优先检查 bug、回归风险和缺失测试"
```

### 8.5 非交互批量跑

```bash
codex exec --json "总结当前仓库的语言、框架和主要入口"
```

### 8.6 查看 MCP

```bash
codex mcp list
```

---

## 9. 如果只保留一句迁移建议

不要把 Codex 当成“另一个 Claude Code CLI”。  
更准确的理解是：

- 它有 Claude Code 里你熟悉的核心能力
- 但它更强调分层指令、工程化技能、异步云端任务、并行代理和结构化自动化

如果你用得好，Codex 的最佳使用方式通常不是“反复重开新对话”，而是：

1. 用 `AGENTS.md` 固化规则  
2. 用 `resume/fork` 管理上下文  
3. 用 `skills` 固化工作流  
4. 用 `review/exec/cloud` 把它接进真实工程链路

---

## 10. 官方参考链接

- Codex 介绍：https://openai.com/index/introducing-codex/
- Codex 文档总览：https://developers.openai.com/codex/cloud
- `AGENTS.md` 指南：https://developers.openai.com/codex/guides/agents-md
- `MCP` 指南：https://developers.openai.com/codex/mcp
- `Skills` 指南：https://developers.openai.com/codex/skills
- 非交互模式：https://developers.openai.com/codex/noninteractive
- Codex App 介绍：https://openai.com/index/introducing-the-codex-app/

