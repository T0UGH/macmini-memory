# 让 Claude Code 获取团队知识：调研报告

> 调研日期：2026-03-08
> 核心问题：团队知识在飞书云文档中，Claude Code 看不到，导致做需求方案设计和排查问题时缺乏上下文。

---

## 1. 核心发现：三层知识架构

学术界和实践社区已经收敛到**三层模型**（来自论文 [Codified Context](https://arxiv.org/html/2602.20478v1)，283 个开发会话验证）：

| 层级 | 加载策略 | 放什么 | 适用场景 |
|------|---------|--------|---------|
| **Tier 1 热知识** | 每次会话自动加载 | 编码规范、架构模式、构建命令、故障排查表 | P0 知识 → `CLAUDE.md` + `.claude/rules/` |
| **Tier 2 领域知识** | 按任务触发加载 | 子系统设计文档、业务规则、领域词汇表 | Skills 或 `docs/` 按需读取 |
| **Tier 3 冷知识** | 按需检索 | 详细规格文档、历史方案、PRD | 飞书 MCP → 实时拉取 |

该论文的知识代码比为 **24.2%**（108,000 行代码对应 26,000 行知识基础设施）。

---

## 2. 方案 A：CLAUDE.md + Rules（P0 知识本地化）

**最简单、最可靠、投入产出比最高。** 把核心知识提炼到本地 markdown，commit 到仓库。

### 2.1 文件结构

```
CLAUDE.md                  # <60 行，指针式索引，全局入口
.claude/rules/
  ├── architecture.md       # 架构决策记录 (ADR)
  ├── business-rules.md     # 核心业务规则
  ├── failure-modes.md      # 已知故障模式表
  ├── domain-glossary.md    # 领域术语表
  └── code-conventions.md   # 编码约定
```

### 2.2 CLAUDE.md 层级体系

| 作用域 | 位置 | 共享范围 |
|-------|------|---------|
| **组织级策略** | `/Library/Application Support/ClaudeCode/CLAUDE.md` (macOS) | 全公司 (通过 MDM 部署) |
| **项目指令** | `./CLAUDE.md` 或 `./.claude/CLAUDE.md` | 团队 (通过 git 共享) |
| **用户指令** | `~/.claude/CLAUDE.md` | 仅个人 (所有项目) |
| **本地指令** | `./CLAUDE.local.md` (gitignored) | 仅个人 (当前项目) |

### 2.3 关键约束

- **`CLAUDE.md` 控制在 60-200 行以内**，超过后指令遵循率显著下降
- Claude 的系统 prompt 已包含约 50 条指令，留给项目的空间约 100-150 条
- 用 `@path/to/file` 语法引用外部文档（最多 5 层嵌套）
- `.claude/rules/*.md` 支持 YAML frontmatter 的 `applyTo` 字段做路径匹配，按需加载
- Monorepo 用 `claudeMdExcludes` 设置排除无关团队的 CLAUDE.md

### 2.4 写作原则

**有效的写法：**
- 具体、可验证的指令（"使用 2 空格缩进" 而非 "格式化代码"）
- 用文件路径引用代码（`src/auth/middleware.ts:42`），不内嵌代码片段
- 表格呈现结构化数据（故障模式、决策矩阵、API 映射）
- 统一术语，建立领域词汇表，避免同义词混用
- 声明式需求优于过程式步骤

**无效的写法：**
- 超过 300 行的 always-loaded 文件
- 内嵌的代码片段（会立即过时）
- 未经整理的自动生成内容
- 没有具体文件路径的抽象指导

> **参考：** [Writing a Good CLAUDE.md (HumanLayer)](https://www.humanlayer.dev/blog/writing-a-good-claude-md) | [Builder.io CLAUDE.md 指南](https://www.builder.io/blog/claude-md-guide) | [10 Tips from Claude Code Team](https://paddo.dev/blog/claude-code-team-tips/)

---

## 3. 方案 B：飞书 MCP Server（云端知识按需拉取）

解决 Tier 3 冷知识的实时获取。

### 3.1 社区已有的文档平台 MCP 方案

| 平台 | MCP Server | 说明 |
|------|-----------|------|
| **Notion** | [官方 Notion MCP](https://github.com/makenotion/notion-mcp-server) | OAuth 认证，自动转 Markdown，token 高效 |
| **Confluence** | [官方 Atlassian MCP](https://github.com/atlassian/atlassian-mcp-server) | OAuth 2.1，覆盖 Jira + Confluence |
| **Google Docs** | [google-docs-mcp](https://github.com/a-bonus/google-docs-mcp) | 读写 Google Docs/Sheets/Drive |
| **多平台** | [Unblocked MCP](https://getunblocked.com/unblocked-mcp/) | 知识图谱，打通 Slack/Confluence/GDocs/Jira/GitHub |
| **本地 RAG** | [knowledge-rag](https://github.com/lyonzin/knowledge-rag) | 100% 本地语义搜索，PDF/MD/代码 |
| **本地 RAG** | [mcp-local-rag](https://github.com/shinpr/mcp-local-rag) | 零配置 `npx` 启动，无需 Docker |
| **Obsidian** | mcp-obsidian | 本地 Markdown 知识库 |

### 3.2 飞书集成路径

飞书目前没有官方 MCP Server，但有开放 API，可以自建：

1. **自建飞书 MCP Server** — 调用飞书开放平台 API，实现文档搜索和内容读取
2. **导出 + 本地 RAG** — 定期导出飞书文档为 Markdown，用 knowledge-rag 或 mcp-local-rag 建索引
3. **混合方案** — P0 文档手动提炼到本地，长尾文档通过 MCP 实时拉取

### 3.3 MCP 配置方式

```json
// .mcp.json — commit 到仓库，团队共享
{
  "mcpServers": {
    "feishu-docs": {
      "command": "node",
      "args": ["path/to/feishu-mcp-server.js"],
      "env": {
        "FEISHU_APP_ID": "...",
        "FEISHU_APP_SECRET": "..."
      }
    }
  }
}
```

企业级部署可通过 `managed-mcp.json` 统一配置到 `/Library/Application Support/ClaudeCode/managed-mcp.json`。

> **参考：** [Claude Code MCP 文档](https://code.claude.com/docs/en/mcp) | [MCP 官方目录](https://github.com/modelcontextprotocol/servers) | [Unblocked 博客](https://blog.getunblocked.com/blog/what-your-coding-agent-cant-see)

---

## 4. 方案 C：Knowledge Skills（领域知识按需触发）

把特定领域知识封装成 Claude Code Skill，只在相关任务时加载，不占用默认 context。

### 4.1 文件结构

```
.claude/skills/
  ├── payment-system/SKILL.md    # 支付系统的设计规范和排查指南
  ├── user-auth/SKILL.md         # 认证系统的架构决策
  └── data-pipeline/SKILL.md     # 数据管道的运维知识
```

### 4.2 Skill 的优势

- Skill 描述的 context 预算仅占 context window 的 **2%**
- 按需加载，不像 CLAUDE.md 每次会话都消耗 token
- 可以打包指令 + 参考资料 + 工具脚本
- 适合"有时需要但不是每次都要"的领域知识

### 4.3 适用场景

- 特定子系统的排查手册
- 特定业务领域的设计规范
- 需要特殊工具或流程的工作流

> **参考：** [Claude Code Skills 文档](https://code.claude.com/docs/en/skills) | [Claude Skills 指南 (Gend.co)](https://www.gend.co/blog/claude-skills-claude-md-guide)

---

## 5. 知识结构化最佳实践

### 5.1 知识文档模板

```markdown
# [子系统/领域名称]

## 概述
[2-3 句话说明是什么、为什么存在]

## 关键文件
- `src/path/to/main.ts` — [用途]
- `src/path/to/types.ts` — [用途]

## 核心模式
[描述规范实现方式，引用具体文件而非内嵌代码]

## 正确性要求
| 要求 | 细节 |
|------|------|
| ...  | ...  |

## 已知故障模式
| 症状 | 原因 | 修复方法 |
|------|------|---------|
| ...  | ...  | ...     |

## 相关决策
- ADR-0042: [标题和简要说明]
```

### 5.2 架构决策记录 (ADR) 格式

```markdown
# ADR-0042: [决策标题]

## 状态
Accepted

## 背景
[决策的上下文和驱动因素]

## 决策
[做出的具体技术选择]

## 后果
[正面和负面影响，包括具体文件路径和代码模式]

## 已知故障模式
| 症状 | 原因 | 修复 |
|------|------|------|
| ...  | ...  | ...  |
```

关键发现：论文指出 **超过一半的 agent 规格由领域知识组成**（设计意图、约束、故障模式），而非行为指令。记录 "why" 比记录 "what" 对 AI 更有用。

### 5.3 P0 vs 参考知识的分类标准

| 分类 | 特征 | 加载策略 |
|------|------|---------|
| **P0 热知识** | 每次开发都要用、出错代价高、变更频率低 | Tier 1: CLAUDE.md + rules |
| **P1 领域知识** | 特定子系统相关、任务触发、中等变更频率 | Tier 2: Skills / 按需读取 |
| **P2 参考知识** | 偶尔查阅、历史沉淀、变更频率高 | Tier 3: MCP 实时检索 |

建议**先迁移使用频率前 20% 的内容**（覆盖 80% 的需求），再逐步扩展。

---

## 6. 知识保鲜策略

这是最容易被忽略、也是最容易导致失败的环节。

### 6.1 维护节奏

| 频率 | 动作 | 耗时 |
|------|------|------|
| **每次 session** | 改代码时顺手更新对应文档 | ~5 分钟 |
| **每两周** | 审查知识文档，标记过期内容 | 30-45 分钟 |
| **每月** | 全量 review，清理和重构 | 1-2 小时 |

总维护成本约 **1-2 小时/周**。

### 6.2 防漂移机制

1. **用指针不用复制** — 引用 `file:line` 而非贴代码片段
2. **Git hook 检测知识漂移** — 代码改了但对应文档没更新时自动告警
3. **PR review 检查清单** — 代码变更是否涉及已文档化的模式/规则
4. **让 Claude 帮忙更新** — 改完代码后说 "更新 .claude/rules/architecture.md 中相关内容"

### 6.3 知识漂移检测脚本思路

```python
# 伪代码：对比最近 git commits 涉及的文件与文档映射
# 如果源码文件变了但对应文档没变，发出告警
subsystem_map = {
    "src/auth/**": ".claude/rules/auth-system.md",
    "src/payment/**": ".claude/rules/payment-rules.md",
}
```

> **参考：** [Codified Context 论文](https://arxiv.org/html/2602.20478v1) | [知识漂移防控 (Datagrid)](https://datagrid.com/blog/automated-knowledge-curation-ai)

---

## 7. 社区实践案例

### 7.1 Anthropic 内部做法

- 新数据科学家入职时，用 Claude Code 读整个代码库快速上手
- CLAUDE.md 标注相关文件、数据管道依赖和上游数据源，替代传统数据目录
- 安全工程团队把散落各处的知识整合成 **Markdown runbooks 和排查指南**
- 研究时间减少 **80%**（从 1 小时降到 10-20 分钟）

### 7.2 社区常见模式

- **自修复循环**：Claude 犯错后，让它更新 CLAUDE.md 防止重犯
- **Claude Code GitHub Action**：PR 评论中 @claude 让它自动更新规则文件
- **Obsidian + GitHub 同步**：本地 Markdown 知识库通过 GitHub 同步，Claude Code 直接读文件
- **每日上下文同步 Skill**：把 7 天内的 Slack、GDrive、Asana、GitHub 变更合并成一个 context 文件

### 7.3 GitHub Issues 中的社区需求

| Issue | 内容 |
|-------|------|
| [#25833](https://github.com/anthropics/claude-code/issues/25833) | 请求 Claude Code 访问 claude.ai Projects 知识库 |
| [#2511](https://github.com/anthropics/claude-code/issues/2511) | 请求复用 claude.ai 上传的文档 |
| [#25983](https://github.com/anthropics/claude-code/issues/25983) | 请求自动同步文件到 Claude web |

> **参考：** [How Anthropic Teams Use Claude Code](https://claude.com/blog/how-anthropic-teams-use-claude-code) | [Anthropic Knowledge Work Plugins](https://github.com/anthropics/knowledge-work-plugins)

---

## 8. 企业级配置

### 8.1 团队共享配置（commit 到 git）

```
.claude/settings.json     # 共享权限和工具规则
.mcp.json                 # 共享 MCP server 配置
CLAUDE.md                 # 共享项目指令
.claude/rules/            # 模块化规则文件
.claude/skills/           # 共享 Skills
.claude/agents/           # 共享子 agent 定义
```

### 8.2 企业管控设置

| 设置 | 用途 |
|------|------|
| `allowManagedMcpServersOnly` | 仅允许管理员配置的 MCP server |
| `allowManagedHooksOnly` | 仅允许管理员配置的 hooks |
| `allowManagedPermissionRulesOnly` | 强制使用管理员权限规则 |
| `disableBypassPermissionsMode` | 禁止跳过权限检查 |
| `companyAnnouncements` | 全公司启动公告 |

通过 MDM (Jamf/Kandji) 部署到 `/Library/Application Support/ClaudeCode/` 目录。

> **参考：** [Claude Code Settings 文档](https://code.claude.com/docs/en/settings) | [Enterprise 部署指南](https://code.claude.com/docs/en/third-party-integrations)

---

## 9. 推荐落地路径

```
Phase 1（1-2 天）
  └─ 方案 A：提炼 P0 知识到 CLAUDE.md + .claude/rules/
     ├─ 从飞书提取 Top 20% 高频知识
     ├─ 用知识文档模板结构化
     └─ Commit 到仓库，团队共享

Phase 2（1 周）
  └─ 方案 C：封装领域 Skills
     ├─ 按子系统建 Skill
     └─ 打包排查指南和设计规范

Phase 3（2-4 周）
  └─ 方案 B：飞书 MCP Server
     ├─ 自建或找社区方案
     ├─ 实现文档搜索和内容读取
     └─ 配置到 .mcp.json 团队共享
```

---

## 10. 参考资料

### 学术论文
- [Codified Context: Infrastructure for AI Agents (arXiv:2602.20478)](https://arxiv.org/html/2602.20478v1)
- [Code Digital Twin (arXiv:2503.07967)](https://arxiv.org/html/2503.07967)
- [Context Engineering for Multi-Agent LLM Code Assistants (arXiv:2508.08322)](https://arxiv.org/abs/2508.08322)

### 官方文档
- [Claude Code Memory 文档](https://code.claude.com/docs/en/memory)
- [Claude Code MCP 文档](https://code.claude.com/docs/en/mcp)
- [Claude Code Skills 文档](https://code.claude.com/docs/en/skills)
- [Claude Code Settings 文档](https://code.claude.com/docs/en/settings)
- [Claude Code Best Practices](https://code.claude.com/docs/en/best-practices)

### 博客和指南
- [How Anthropic Teams Use Claude Code](https://claude.com/blog/how-anthropic-teams-use-claude-code)
- [Writing a Good CLAUDE.md (HumanLayer)](https://www.humanlayer.dev/blog/writing-a-good-claude-md)
- [CLAUDE.md 指南 (Builder.io)](https://www.builder.io/blog/claude-md-guide)
- [10 Tips from Claude Code Team](https://paddo.dev/blog/claude-code-team-tips/)
- [Claude Skills 指南 (Gend.co)](https://www.gend.co/blog/claude-skills-claude-md-guide)
- [What Your Coding Agent Can't See (Unblocked)](https://blog.getunblocked.com/blog/what-your-coding-agent-cant-see)
- [Context Engineering 指南 (LlamaIndex)](https://www.llamaindex.ai/blog/context-engineering-what-it-is-and-techniques-to-consider)

### 开源项目
- [Anthropic Knowledge Work Plugins](https://github.com/anthropics/knowledge-work-plugins)
- [Notion MCP Server](https://github.com/makenotion/notion-mcp-server)
- [Atlassian MCP Server](https://github.com/atlassian/atlassian-mcp-server)
- [knowledge-rag (本地 RAG MCP)](https://github.com/lyonzin/knowledge-rag)
- [mcp-local-rag (零配置)](https://github.com/shinpr/mcp-local-rag)
- [Codified Context 配套代码](https://github.com/arisvas4/codified-context-infrastructure)
