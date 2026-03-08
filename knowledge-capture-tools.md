# 知识沉淀工具对比：Claude Diary vs Claude-Mem vs /retro

## 三个工具对比

| 维度 | Claude Diary | Claude-Mem | /retro (自定义) |
|------|-------------|-----------|----------------|
| **作者** | Lance Martin (LangChain) | thedotmack | 自建 |
| **复杂度** | 极简（2 个 md + 1 个 hook） | 重量级（TS + SQLite + Chroma + HTTP） | 中等（1 个 md 命令） |
| **存储** | Markdown 文件 | SQLite + 向量数据库 | `.claude/rules/` + 文档 |
| **压缩** | 无，结构化记录 | 90% token 压缩 | 人工触发，Claude 辅助提炼 |
| **搜索** | 靠 `/reflect` 分析模式 | 混合搜索（关键词 + 向量） | 无 |
| **运行开销** | 零 | HTTP 服务常驻 (localhost:37777) | 零 |
| **粒度** | Session 级 | Session 级（工具调用级） | 需求/功能级 |
| **触发方式** | 手动 `/diary` + PreCompact hook | 全自动（5 个 hooks） | 手动触发 |

## Claude Diary

- 仓库：https://github.com/rlancemartin/claude-diary（已 clone 到 workspace）
- 两个命令：`/diary`（记录 session）+ `/reflect`（分析模式 → 更新 CLAUDE.md）
- PreCompact hook 自动触发 diary
- 灵感来自 Generative Agents 论文（Park et al.）
- 存储位置：`~/.claude/memory/diary/` 和 `~/.claude/memory/reflections/`
- 安装：复制 `commands/diary.md` 和 `commands/reflect.md` 到 `~/.claude/commands/`

## Claude-Mem

- 仓库：https://github.com/thedotmack/claude-mem（已 clone 到 workspace）
- 4 层架构：Hooks → Worker Service (HTTP) → Business Logic → SQLite + Chroma
- 6 种观察类型：bugfix, feature, refactor, change, discovery, decision
- 7 种概念标签：how-it-works, why-it-exists, what-changed, problem-solution, gotcha, pattern, trade-off
- 3 层渐进式注入：index (~100 tokens) → timeline (~200) → detail (~500)
- 安装：插件市场安装，需要 Bun 运行时

## /retro 命令（计划自建）

- 需求完成后手动触发
- 分析 git diff + 会话上下文
- 双输出：精华 → `.claude/rules/`，详细版 → 文档仓库
- 借鉴 Claude-Mem 的分类体系

## 选型结论

**推荐组合：Claude Diary + 自定义 /retro**
- Diary 负责 session 级日常积累 → 自动更新 CLAUDE.md
- /retro 负责需求级知识沉淀 → 精华进 rules，详细版存文档
- 两者互补，覆盖不同粒度

## 完整调研报告
- 知识沉淀流程调研：`/Users/haha/workspace/memory/knowledge-capture-after-feature-research.md`
- 团队知识集成调研：`/Users/haha/workspace/memory/claude-code-team-knowledge-research.md`
