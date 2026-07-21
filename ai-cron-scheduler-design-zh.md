# AI Cron Scheduler 设计思路

> 基于对 vesper-schedule 和 murmur 两个开源项目的深度研究，整理出的理想架构方案。
> 日期：2026-03-02

---

## 背景

目标是构建一个 **cron 调度系统**，到时间自动拉起一个 Claude Agent SDK 会话，传入固定 prompt，完成一件事（如每日 AI Coding 新闻摘要）。

类似 happyclaw 的定时任务设计。

---

## 调研的两个项目

### vesper-schedule
- **GitHub**: https://github.com/vulh1209/vesper-schedule
- **核心特点**: 唯一真正使用 Claude Agent SDK 原生 `query()` 调用的开源调度器
- **场景**: GitHub 自动化（issue triage、PR review 等）
- **运行时**: Bun + TypeScript

### murmur
- **GitHub**: https://github.com/t0dorakis/murmur
- **核心特点**: 设计最优雅的 AI cron daemon，自称 "AI cron daemon"
- **场景**: 通用 AI 定时任务，支持多 Agent（Claude Code / Codex / Pi）
- **运行时**: Bun + TypeScript + Effect-TS

---

## 两个项目的核心差异

| 维度 | Vesper | Murmur |
|------|--------|--------|
| Agent 调用 | SDK 原生 `query()` | CLI 桥接 `claude --print` |
| 调度核心 | croner + JobQueue（串行 + 熔断器） | 轮询循环（每 10s tick） |
| Prompt 定义 | Markdown + YAML frontmatter（skill 文件） | Markdown + YAML frontmatter（HEARTBEAT.md） |
| 多 Agent | 仅 Claude Agent SDK | Claude Code / Codex / Pi，Adapter 模式 |
| 会话恢复 | 支持 resume session_id | 不支持 |
| 熔断器 | 有（3次失败 → 冷却5分钟） | 无 |
| 队列持久化 | 有（崩溃恢复） | 无 |
| 热重载 | 不支持 | 支持（每 tick 重读 config） |
| 输出协议 | 结构化 SDK result 对象 | `HEARTBEAT_OK` / `ATTENTION:` 文本协议 |

---

## 理想架构设计

结合两个项目的优点，理想的系统应该是：

```
HEARTBEAT.md（Murmur 风格的文件格式）
      ↓
Scheduler（croner，支持 interval + cron 表达式）
      ↓
JobQueue（Vesper 的熔断器 + 崩溃持久化）
      ↓
Claude Agent SDK query()（Vesper 的原生调用，非 CLI）
      ↓
HEARTBEAT_OK / ATTENTION 分类（Murmur 的简洁输出协议）
```

---

## 从各项目借鉴的具体设计

### 从 Murmur 借鉴

**1. HEARTBEAT.md 文件格式**

```markdown
---
name: Daily AI Coding News
interval: 1d          # 或 cron: "0 9 * * *"
agent: claude-code
model: sonnet
maxTurns: 30
timeout: 10m
---

抓取今日 AI Coding 相关新闻（Cursor、GitHub Copilot、Claude Code、开源工具等），
整理成中文摘要，推送到 Discord #ai-news 频道。
```

- YAML frontmatter 定义调度参数
- 文件正文即 prompt，天然支持版本控制
- 多个 HEARTBEAT.md = 多个独立定时任务

**2. 热重载 config**

每次 tick 重读配置文件，无需重启 daemon 即可新增/修改任务。

**3. 多 Agent Adapter 抽象**

```typescript
interface AgentAdapter {
  name: string
  execute(prompt: string, options: WorkspaceConfig): Promise<AgentResult>
  isAvailable(): Promise<boolean>
}
```

注册多个 adapter，HEARTBEAT.md 里用 `agent: claude-code` 指定。

**4. HEARTBEAT_OK / ATTENTION 输出协议**

Agent 输出约定：
- `HEARTBEAT_OK` → 静默，无需处理
- `ATTENTION: <摘要>` → 需要人工关注，发通知
- 非零退出码 → 执行出错

三行代码完成结果分类，简洁有效。

**5. 登录 Shell 包装**

```bash
/bin/zsh -lc 'claude --print ...'
```

继承用户完整环境（PATH、aliases、环境变量），避免 daemon 里找不到命令。

---

### 从 Vesper 借鉴

**1. Claude Agent SDK 原生调用**

```typescript
import { query } from '@anthropic-ai/claude-code'

const conversation = query({
  prompt: builtPrompt,
  options: {
    cwd: workingDirectory,
    allowedTools: ['Bash', 'Read', 'Write'],  // 白名单
    permissionMode: 'bypassPermissions',       // 无人值守关键
    appendSystemPrompt: '...',
  },
})

for await (const message of conversation) {
  if (message.type === 'result') {
    // 拿到最终结果
  }
}
```

避免 subprocess 开销，直接拿结构化输出。

**2. 熔断器（Circuit Breaker）**

```
连续 3 次失败 → 熔断
熔断后 5 分钟冷却
冷却后自动恢复
```

防止 API 故障时无限重试。

**3. 队列持久化**

daemon 崩溃或重启时，pending jobs 从文件恢复，不丢任务。

**4. allowedTools 白名单**

在 skill/heartbeat 文件里定义 Agent 可以使用的工具，限制权限范围：

```yaml
allowedTools:
  - "Bash(curl *)"   # 只允许 curl
  - "Read"
  - "Write"
```

**5. 会话 Resume**

每次执行保存 `session_id`，下次可以接着上次的上下文继续，适合需要跨次记忆的任务。

---

## 实现路径建议

### 方案 A：Fork Murmur 改造
- Fork murmur，把 CLI 桥接改成 SDK 原生 `query()` 调用
- 加入 Vesper 的熔断器和队列持久化
- 改动量中等，能快速验证

### 方案 B：从头搭建（最小可用版本）
最小可用版本只需要：

```
src/
├── scheduler.ts    # croner 定时触发
├── heartbeat.ts    # 读取 HEARTBEAT.md + 调用 SDK
├── queue.ts        # 简单 Job Queue（可先不加熔断器）
├── config.ts       # 读 ~/.ai-cron/config.json
└── cli.ts          # start / stop / beat / status
```

依赖：
```json
{
  "@anthropic-ai/claude-code": "^1.0.0",
  "croner": "^9.0.0",
  "gray-matter": "^4.0.3"
}
```

### 方案 C：先用 Murmur 跑起来
直接用 murmur，先验证 HEARTBEAT.md + 定时调度的工作流，
再决定是否需要 SDK 原生调用的优化。

---

## 与 daily-ai-news skill 的结合

有了这个 cron 系统后，daily-ai-news 就变成一个 HEARTBEAT.md 文件：

```markdown
---
name: Daily AI Coding News
cron: "0 9 * * *"
agent: claude-code
model: sonnet
maxTurns: 30
allowedTools:
  - "Bash(curl *)"
  - "Read"
  - "Write"
---

抓取今日 AI Coding 相关新闻，重点关注：
- GitHub Copilot、Cursor、Claude Code、Devin 等工具的更新
- 开源 AI Coding 项目（本周新发布或热门趋势）
- AI Coding 相关研究论文或技术博客

整理成中文摘要，格式参考 daily-ai-news skill 的输出模板，
写入 ~/workspace/memory/daily-news-{date}.md。

如果没有值得关注的新内容，回复 HEARTBEAT_OK。
如果有重要更新，回复 ATTENTION: 并附上摘要。
```

---

## 参考资料

- [vesper-schedule 源码](https://github.com/vulh1209/vesper-schedule) — 本地：`/Users/haha/workspace/github/vesper-schedule`
- [murmur 源码](https://github.com/t0dorakis/murmur) — 本地：`/Users/haha/workspace/github/murmur`
- [Claude Agent SDK 文档](https://github.com/anthropics/claude-agent-sdk-python)
- [Anthropic Issue #4785](https://github.com/anthropics/claude-code/issues/4785) — 官方不内置 scheduling，推荐基于 SDK 自建
- [awesome-openclaw-usecases](https://github.com/hesamsheikh/awesome-openclaw-usecases) — 本地：`/Users/haha/workspace/github/awesome-openclaw-usecases`
