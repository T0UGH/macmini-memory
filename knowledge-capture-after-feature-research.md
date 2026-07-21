# 需求完成后的知识沉淀调研报告

> 调研日期：2026-03-08
> 核心问题：每做完一个需求，如何系统化地沉淀知识到 `.claude/rules/`（精华）和文档仓库（详细版）

---

## 1. 五种实践模式对比

| 模式 | 工具/方法 | 自动化程度 | 说明 |
|------|----------|-----------|------|
| **A. `/retro` 命令** | 自定义 slash command | 手动触发，Claude 辅助生成 | 最推荐，简单直接 |
| **B. Claude Diary** | [插件](https://rlancemartin.github.io/2025/12/01/claude_diary/) | 半自动 `/diary` + `/reflect` | 灵感来自 Generative Agents 论文 |
| **C. claude-mem** | [插件](https://github.com/thedotmack/claude-mem) | 全自动 session 级捕获 | 5 个 hooks 自动压缩 session 记忆 |
| **D. PR 驱动知识循环** | Claude Code GitHub Action | 嵌入 code review | 团队推广时用 |
| **E. SessionEnd Hook** | Claude Code hooks | 自动触发 | 作为补充方案 |

---

## 2. 推荐方案：自定义 `/retro` 命令

### 2.1 实现方式

在项目中创建 `.claude/commands/retro.md`，需求完成后手动执行 `/retro`。

### 2.2 工作流

```
需求开发完成
    ↓
执行 /retro
    ↓
Claude 分析 git diff + 会话上下文
    ↓
├─ 精华知识 → 更新 .claude/rules/ 对应文件
└─ 详细文档 → 生成 docs/retros/YYYY-MM-DD-feature-xxx.md
    ↓
开发者 review 生成内容
    ↓
commit 到仓库，团队共享
```

### 2.3 双输出策略

- **精华 → `.claude/rules/`**：架构决策、故障模式表、核心业务规则，给未来的 Claude 直接用
- **详细版 → 文档仓库**：完整的技术方案、排查过程、设计权衡，给人阅读

---

## 3. Claude Diary 方案

来源：[Claude Diary](https://rlancemartin.github.io/2025/12/01/claude_diary/)（灵感来自 Park et al. Generative Agents 论文）

两阶段知识捕获：
- **`/diary`**：Claude 反思当前 session，记录成就、设计决策、障碍、用户偏好
- **`/reflect`**：分析累积的 diary 条目，识别模式和规则违反，建议更新 CLAUDE.md

转化链：session 对话 → diary 条目 → 规则提案 → CLAUDE.md 更新

---

## 4. claude-mem 方案

来源：[claude-mem](https://github.com/thedotmack/claude-mem)

全自动 session 记忆压缩系统：
- 5 个生命周期 hooks：`SessionStart` → `UserPromptSubmit` → `PostToolUse` → `Summary` → `SessionEnd`
- 工具输出（1,000-10,000 tokens）压缩为 ~500 token 语义观察
- 观察分类：`decision`, `bugfix`, `feature`, `refactor`, `discovery`, `change`
- 新 session 自动接收过去 10 个 session 的相关上下文
- 存储在 SQLite 中，支持全文搜索

---

## 5. PR 驱动知识循环

### Anthropic 内部做法（Boris Cherny，Claude Code 创建者）
- Claude 犯错时，修代码 **同时** 更新 CLAUDE.md
- Code review 是知识捕获的关键时刻
- 用 `@claude` 在同事的 PR 中直接添加学习到 CLAUDE.md

### Claude Code GitHub Action
- `instructions` 参数可以指示 Claude 在 review PR 时提取知识
- 可配置为 PR 合并后触发知识提取
- 需要 `contents: write` 权限来推送文档更新

### CodeRabbit Learnings
- [CodeRabbit](https://docs.coderabbit.ai/integrations/knowledge-base) 实现了跨 PR 持久化的学习系统
- 跨仓库学习，组织级一致性
- 向量数据库存储 review 学习

---

## 6. Claude Code Hooks 能力

### 知识捕获相关的 hook 事件

| 事件 | 触发时机 | 用途 |
|------|---------|------|
| `SessionEnd` | session 结束 | 主要捕获点 |
| `Stop` | Claude 完成回复 | 回合级摘要 |
| `PreCompact` | context 压缩前 | 压缩前保存状态 |
| `PostToolUse` | 工具执行后 | 匹配 `Bash(git commit)` 做提交级捕获 |
| `TaskCompleted` | 任务完成 | 任务完成时捕获 |

注意：目前没有原生 `PostCommit` hook 事件（[Issue #4834](https://github.com/anthropics/claude-code/issues/4834) 请求中）。

### 补充方案：PreCompact Hook
- [precompact-hook](https://github.com/mvara-ai/precompact-hook)：compact 前读取最近 50 轮对话，生成恢复简报

---

## 7. 相关工具和社区项目

| 工具 | 说明 |
|------|------|
| [Claude Command Suite](https://github.com/qdhenry/Claude-Command-Suite) | 216+ 命令，含 `/team:retrospective-analyzer`、`/team:session-learning-capture` |
| [Ars Contexta](https://github.com/agenticnotetaking/arscontexta) | 从对话生成个人知识系统，wiki links 知识图谱 |
| [Notion Skills](https://github.com/tommy-ca/notion-skills) | 含 Knowledge Capture skill，写入 Notion |
| [GitNarrative](https://gitnarrative.io/) | git commits 转叙事文档 |
| [Gitmore](https://gitmore.io/) | LLM 分析 commit/PR 生成知识摘要 |

---

## 8. 落地建议

### Phase 1：立即可做
- 创建 `/retro` slash command，需求完成后手动触发
- 输出精华到 `.claude/rules/`，详细版到 `docs/retros/`

### Phase 2：增强
- 安装 Claude Diary 或类似插件，session 级自动捕获
- 配置 `PreCompact` hook 防止 compact 丢失知识

### Phase 3：团队推广
- 配置 Claude Code GitHub Action，PR 合并时自动提取知识
- 建立 code review 中更新 CLAUDE.md 的团队习惯

---

## 参考资料

- [How Anthropic teams use Claude Code (PDF)](https://www-cdn.anthropic.com/58284b19e702b49db9302d5b6f135ad8871e7658.pdf)
- [Claude Code 创建者工作流 (InfoQ)](https://www.infoq.com/news/2026/01/claude-code-creator-workflow/)
- [Claude Diary](https://rlancemartin.github.io/2025/12/01/claude_diary/)
- [claude-mem](https://github.com/thedotmack/claude-mem)
- [Claude Code Hooks 文档](https://code.claude.com/docs/en/hooks)
- [Claude Code GitHub Action](https://github.com/anthropics/claude-code-action)
- [Claude Command Suite](https://github.com/qdhenry/Claude-Command-Suite)
- [Ars Contexta](https://github.com/agenticnotetaking/arscontexta)
- [CodeRabbit Knowledge Base](https://docs.coderabbit.ai/integrations/knowledge-base)
- [precompact-hook](https://github.com/mvara-ai/precompact-hook)
