# GitHub AI Daily 卡片文案｜2026-03-17

## 卡片 1｜Claude Code
**Claude Code 这一版，补的是重度使用痛点。**
- 长会话输出上限继续提高
- `--resume` 截断问题修了
- tmux / IDE / 剪贴板兼容继续补
- 权限与 hook 边界更严了

**一句话判断**
已经不是拼“能不能写代码”，而是在拼“能不能长期稳定跑”。

---

## 卡片 2｜OpenClaw
**OpenClaw 这版更像系统补丁包。**
- 发布链路错误被修正
- compaction 校验更稳
- Telegram / SSRF 安全链路补强
- 多端、多 channel、多 session 细节继续修

**一句话判断**
重点不在新功能，而在把底层稳定性和安全边界补齐。

---

## 卡片 3｜Codex
**Codex 这一版，重点在底座能力继续加厚。**
- Smart Approvals 接入 guardian subagent
- app-server v2 新增 filesystem RPC
- Python SDK 补上了
- realtime / handoff / subagent 继续推进

**一句话判断**
方向很明确：不是更像聊天，而是更像可嵌入、可编排的编码代理底座。

---

## 卡片 4｜OpenCode
**OpenCode 这版优先修基础链路。**
- worktree / orphan branch 的 session 丢失被修
- chunk timeout 从 2 分钟提到 5 分钟
- compaction message 归因更一致
- permission / question service 底层继续重构

**一句话判断**
多任务工程流已经从功能竞争，走向稳定性竞争。

---

## 卡片 5｜routa
**这是个值得盯的协议层项目。**
- 做的是多 agent 协调
- 把 MCP / ACP / A2A 串起来
- 能把 Claude Code、OpenCode、Gemini 接到一起

**一句话判断**
现在还是早期，但如果协议层真跑通，价值会很大。

---

## 卡片 6｜obsidian-agent-client
**ACP 正在往知识管理场景外扩。**
- 把 Claude Code / Codex / Gemini CLI 接进 Obsidian
- 不只是 coding，开始碰笔记和知识流

**一句话判断**
如果 agent 能自然进入笔记系统，个人工作流会被重做一遍。

---

## 卡片 7｜fast-agent
**它更像 agent 中间层框架。**
- 同时强调 model / skills / MCP / ACP
- 不只是“调用工具”，而是想把构建和评测一起收进去

**一句话判断**
这类项目更值得长期跟，因为容易长成基础设施。

---

## 卡片 8｜arbor
**arbor 盯的是工作台形态。**
- 核心是 git worktree + terminal + diff
- 服务的是多任务并行 coding workflow

**一句话判断**
agent 进入持续执行阶段后，工作界面本身也会变成竞争点。

---

## 卡片 9｜gitclaw
**gitclaw 值得看的是 repo-native 这条线。**
- identity / memory / rules / skills 全部文件化
- agent 能力直接进仓库版本管理

**一句话判断**
如果这条路成立，后面的 agent 可移植性和可审计性会很强。
