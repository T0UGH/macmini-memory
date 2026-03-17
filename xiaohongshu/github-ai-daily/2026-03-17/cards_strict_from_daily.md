# GitHub AI Daily 卡片文案｜2026-03-17｜严格按日报文件生成

## anthropics/claude-code
**Claude Code v2.1.77**

发布时间：2026-03-17 08:28

这版不是加花活，核心是在补重度使用时最痛的几条链路。

- 长输出能力继续上调：Opus 4.6 默认 64k，上限到 128k
- `allowRead` 沙箱权限更细，能在 `denyRead` 里局部开白名单
- `/copy N` 能直接复制倒数第 N 条回复
- `--resume` 截断问题修了，大 session 恢复也更快
- tmux / IDE / 剪贴板 / hook 权限边界继续补齐

**一句话**
Claude Code 已经进入“长期稳定工作代理”的打磨阶段。

---

## openclaw/openclaw
**OpenClaw v2026.3.13-1**

发布时间：2026-03-15 02:04

这版名义上是恢复型 release，实际上是发布链路 + 系统稳定性补丁。

- 修复上一版损坏的 tag / release 路径
- npm 版本仍是 `2026.3.13`，`-1` 只体现在 Git tag / GitHub Release
- compaction 改成按完整会话 token 做 sanity check
- Telegram 媒体传输被重新接回 SSRF 防护链路
- 对外功能增量不大，但发布一致性和安全边界更稳了

**一句话**
OpenClaw 真正值得盯的，还是系统底层稳定性和安全收口能力。

---

## sst/opencode
**OpenCode v1.2.27**

发布时间：2026-03-16 10:34

这版重点很清楚：先修基础链路，不急着堆新能力。

- worktree / orphan branch 下的 session 丢失问题被修复
- chunk timeout 从 2 分钟提高到 5 分钟
- compaction message 被明确记为 agent initiated
- legacy permission module 被清理
- QuestionService / PermissionNext 相关底层继续重构
- Desktop 侧补了 multiline web paste

**一句话**
OpenCode 也在往“更稳的长期使用”走，而不是只追求功能列表变长。

---

## openai/codex
**Codex rust-v0.115.0**

发布时间：2026-03-17 03:37

这版 Codex 值得看的不是单点功能，而是底座能力继续往前推进。

- Smart Approvals 能把 review 请求路由给 guardian subagent
- app-server v2 新增 filesystem RPC，并补了 Python SDK
- realtime websocket 会话新增 transcription mode
- `codex` tool 支持 v2 handoff
- subagent 的 sandbox / network 规则继承更稳了
- 还补了 `codex exec --profile`、MCP、TUI 退出卡住等问题

**一句话**
Codex 的方向不是“更像聊天”，而是“更像可编排、可嵌入的编码代理底座”。

---

## phodal/routa
**routa**

Stars：152

这是一个多 Agent 协调平台。

- 把用户意图先转成结构化规格
- 再通过 MCP / ACP / A2A 协议分发给不同工具
- 可接 Claude Code、OpenCode、Gemini 等

**为什么值得看**
它盯的不是单个 agent 强不强，而是多 agent 之间怎么协作、怎么路由。

**一句话**
现在还早，但协议层如果跑通，价值会很大。

---

## RAIT-09/obsidian-agent-client
**obsidian-agent-client**

Stars：1218

它做的是把 Claude Code、Codex、Gemini CLI 等 agent 通过 ACP 接进 Obsidian。

- agent 不再只待在终端
- 开始进入笔记、知识库、个人信息流场景
- 这条线对个人工作流改造很有代表性

**为什么值得看**
如果 ACP 能顺利进入知识管理场景，agent 的使用边界会明显扩大。

**一句话**
这不是小插件，而是在试探“agent + 知识系统”怎么真正接起来。

---

## evalstate/fast-agent
**fast-agent**

Stars：3708

这是一个强调 Model / Skills / MCP / ACP 支持的 agent 构建与评测工具集。

- 不只是做一个 agent 产品
- 更像在做 agent 的组装层和评测层
- 对工作流型系统有很强中间层意味

**为什么值得看**
这类项目一旦成熟，往往比单点工具更容易长成基础设施。

**一句话**
值得长期跟，不只是看功能，而是看它会不会变成生态中间层。

---

## penso/arbor
**arbor**

Stars：361

这是个原生桌面应用，重点围绕 git worktree、terminal 和 diff 来组织 agentic coding workflow。

- 盯的是多任务并行工作流
- 不是单次问答，而是持续执行场景
- 和 Claude Code / Codex / OpenCode 补的方向高度同向

**为什么值得看**
agent 一旦进入持续执行阶段，工作台形态本身就会变成竞争点。

**一句话**
值得继续观察，它代表的是“桌面工作台”这条产品方向。

---

## open-gitagent/gitclaw
**gitclaw**

Stars：146

这是一个 git-native AI agent 框架。

- identity / rules / memory / tools / skills 全都文件化
- agent 能力直接进入仓库版本管理
- 走的是 repo-native memory / rule system 这条路

**为什么值得看**
如果 agent 的记忆、规则、身份都能 repo 化，后面的可移植性和可审计性会非常强。

**一句话**
它还早，但方向非常对，值得放进长期观察名单。
