# learn-claude-code 深度研究报告

> 日期: 2026-03-11 | GitHub: shareAI-lab/learn-claude-code | 定位: 教育项目

## 项目概述

"Bash is all you need" — 从 0 到 1 构建 nano Claude Code agent 的 12 堂递进式课程。每堂课只加一个机制，核心循环始终不变。支持中/英/日三语，配有 Next.js 交互式学习平台。

- **核心代码**: 12 个 Python 参考实现 + 1 个 capstone (agents/ 目录，4.5k 行)
- **支持模型**: Claude Sonnet, MiniMax M2.5, GLM-5, Kimi K2.5, DeepSeek
- **依赖**: anthropic SDK + python-dotenv (极简)

---

## 12 堂课程设计

| 课程 | 主题 | 行数 | 核心格言 | 关键添加 |
|------|------|------|---------|---------|
| **s01** | Agent 循环 | 106 | *One loop & Bash is all you need* | `while stop_reason=="tool_use"` 基础 ReAct 循环 |
| **s02** | Tool Use | 148 | *加一个工具，只加一个 handler* | Dispatch map + 路径沙箱 (safe_path) |
| **s03** | TodoWrite | 209 | *没有计划的 agent 走哪算哪* | TodoManager + Nag reminder (3轮未更新提醒) |
| **s04** | Subagent | 183 | *大任务拆小，干净的上下文* | run_subagent() 独立 messages[], 只返回摘要 |
| **s05** | Skills | 225 | *用到什么知识，临时加载什么* | SkillLoader + YAML frontmatter + 两层注入 |
| **s06** | Context Compact | 247 | *上下文总会满，要有办法腾地方* | 三层压缩 (micro/auto/manual) |
| **s07** | Task System | 247 | *大目标拆小任务，记在磁盘上* | TaskManager + DAG 依赖图 (blockedBy/blocks) |
| **s08** | Background | 233 | *慢操作丢后台，agent 继续想* | BackgroundManager + 守护线程 + 通知队列 |
| **s09** | Agent Teams | 405 | *任务太大一个人干不完* | TeammateManager + JSONL 邮箱 + 线程 agent loop |
| **s10** | Team Protocols | 486 | *队友之间要有统一沟通规矩* | shutdown/plan 握手协议 (FSM: pending→approved/rejected) |
| **s11** | Autonomous | 578 | *队友自己看看板，有活就认领* | idle 轮询 + 自动 claim 任务 + 身份重注入 |
| **s12** | Worktree | 780 | *各干各的目录，互不干扰* | git worktree 绑定 + 隔离执行 + 事件流 |

### 学习路径

```
第一阶段: 循环 (s01-s02)
  ↓
第二阶段: 规划与知识 (s03-s06) — TodoWrite, Subagent, Skills, Context
  ↓
第三阶段: 持久化 (s07-s08) — Task DAG, Background
  ↓
第四阶段: 团队 (s09-s12) — Teams, Protocols, Autonomous, Worktree
```

---

## 核心机制详解

### 1. ReAct 循环 (s01, 不到 30 行)

```python
while True:
    response = client.messages.create(model, system, messages, tools)
    messages.append(assistant_message)
    if response.stop_reason != "tool_use": return
    results = [execute(tool) for tool in response.tool_uses]
    messages.append(user_tool_results)
```

整个 12 课中，这个循环**始终不变**，所有复杂性通过机制叠加实现。

### 2. 工具系统 (s02)

Dispatch Map 模式，从 1 个工具 (bash) 递增到 24+ 个：
- 文件操作: read_file, write_file, edit_file
- 路径沙箱: `safe_path()` 防止逃逸工作目录
- 每课新增 1-3 个工具

### 3. 上下文压缩 (s06, 三层策略)

```
Layer 1: micro_compact (每轮) — 替换 3 轮前的 tool_result 为占位符
Layer 2: auto_compact (token > 50000) — LLM 摘要 + transcript 保存到磁盘
Layer 3: manual_compact — 模型主动调用 compress 工具
```

### 4. 任务持久化与 DAG (s07)

```
.tasks/task_N.json
{id, subject, status, blockedBy:[], blocks:[]}

状态机: pending → in_progress → completed
完成时自动递归解锁后续任务
```

### 5. 团队协作 (s09-s12)

**JSONL 邮箱架构**:
```
.team/inbox/alice.jsonl  ← append-only, read 时清空
```

**5 种消息类型**: message, broadcast, shutdown_request, shutdown_response, plan_approval_response

**自治模式 (s11)**: idle 轮询 → 检查邮件/未认领任务 → 自动 claim → 工作 → 完成 → 回到 idle

**Worktree 隔离 (s12)**: 每个任务绑定独立 git worktree，互不干扰，事件流审计

---

## 技能系统 (s05)

两层注入模式:
1. **系统提示层** (永久, ~100 tokens/skill): 技能名+描述列表
2. **按需加载层** (tool_result): 模型调用 `load_skill("name")` 时注入完整文档

技能示例: agent-builder, code-review, mcp-builder, pdf

---

## 姊妹项目

| 项目 | 定位 | 区别 |
|------|------|------|
| **Kode Agent CLI** | 开源 coding agent CLI | 支持 Skill + LSP, 跨平台 |
| **Kode Agent SDK** | Agent 能力嵌入 SDK | 无 per-user 进程开销 |
| **OpenClaw (claw0)** | 常驻助手架构 | 心跳+定时+IM+持久记忆 |

---

## 设计哲学

> "The model already knows how to be an agent. Your job is to get out of the way."

1. **最小化核心** — s01 不到 30 行，完整 agent 循环
2. **增量机制** — 每课只加一个机制，循环本身不变
3. **隔离职责** — 子 agent 隔离上下文，后台隔离 I/O，worktree 隔离目录
4. **持久化优先** — 任务、团队、worktree 都存盘，抗压缩/重启
5. **自组织演进** — 单一 agent → 多 agent 团队 → 自治 agent → 隔离执行

---

## 评价

### 亮点
- 教学设计精妙：12 课渐进，每课 diff 清晰
- 代码即文档，注释解释设计决策
- 多模型支持，不绑定 Anthropic
- Web 学习平台 (Next.js) 提供交互体验
- 揭示了 Claude Code 的核心原理：ReAct 循环 + 工具分发 + 上下文管理

### 局限
- 教育项目，非生产可用
- 无错误恢复、权限系统、安全审计等生产级特性
- 团队模式 (s09-s12) 复杂度较高，实际应用有限

---

## 学习记录

- **2026-03-13**: 12 课全部阅读完成（未做实践）
- 每课核心收获:
  - s01-s02: 核心循环极简，while tool_use + dispatch map 就够了
  - s03: nag reminder 制造问责压力，强制顺序聚焦（同时只能一个 in_progress）
  - s04: 子 agent 的价值在于上下文隔离——30 次工具调用浓缩为一段摘要
  - s05: 两层注入是 skill 系统的精髓——system prompt 放目录，tool_result 放内容
  - s06: micro_compact 最巧妙——静默替换旧 tool_result，用户无感
  - s07: 从扁平清单到 DAG，blockedBy 让并行成为可能
  - s08: 主循环单线程不变，只有子进程 I/O 被并行化
  - s09: JSONL 邮箱的 append-only + drain-on-read 设计简洁高效
  - s10: 一个 FSM (pending→approved/rejected) 两种用途（关机+审批）
  - s11: 从中心化分配到去中心化自组织是关键转变
  - s12: 控制面（任务）和执行面（worktree）双向绑定，磁盘状态是持久的
