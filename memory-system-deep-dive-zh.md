# Letta Code 记忆系统深度分析报告

## 概述

Letta Code 的记忆系统是其核心差异化特性，区别于其他 AI 编程 CLI 工具（如 Claude Code、OpenAI Codex）的关键所在。与传统工具每次会话重新开始不同，Letta Code 的智能体具有**持久化记忆**，能够跨会话学习和成长。

本报告深入分析 Letta Code 记忆系统的架构设计、实现细节和核心机制。

---

## 1. 记忆系统架构

### 1.1 核心组件

记忆系统由以下核心模块组成：

| 模块 | 文件路径 | 职责 |
|------|----------|------|
| **memory.ts** | `src/agent/memory.ts` | 记忆块加载、解析、缓存 |
| **memoryConstants.ts** | `src/agent/memoryConstants.ts` | 记忆块常量定义 |
| **memoryFilesystem.ts** | `src/agent/memoryFilesystem.ts` | 记忆文件系统（MemFS）管理 |
| **memoryGit.ts** | `src/agent/memoryGit.ts` | Git 版本控制集成 |
| **memoryPrompt.ts** | `src/agent/memoryPrompt.ts` | 记忆提示词处理 |

### 1.2 记忆块类型

Letta Code 定义了两种记忆块存储级别：

```typescript
// src/agent/memory.ts:13-19
// 全局记忆块：跨项目共享
export const GLOBAL_BLOCK_LABELS = ["persona", "human"] as const;

// 项目级记忆块：本地存储（当前版本已移除，技能通过系统提醒注入）
export const PROJECT_BLOCK_LABELS = [] as const;
```

| 记忆块 | 类型 | 说明 |
|--------|------|------|
| `persona` | 全局 | AI 角色定义和行为准则 |
| `human` | 全局 | 用户偏好和背景信息 |
| `project` | 全局 | 项目上下文和约定 |
| `skills` | 全局 | 技能定义（通过系统提醒注入） |

---

## 2. 记忆块格式与加载

### 2.1 MDX 格式

记忆块使用 MDX 格式存储，支持 Frontmatter 元数据：

```yaml
---
label: human
description: What I've learned about the person I'm working with. Understanding them helps me be genuinely helpful rather than generically helpful.
---

I haven't gotten to know this person yet.
```

**Frontmatter 字段说明：**

| 字段 | 必填 | 说明 |
|------|------|------|
| `label` | 是 | 记忆块标识符 |
| `description` | 是 | 记忆块描述，定义如何影响 AI 行为 |
| `limit` | 否 | 记忆块大小限制（字符数） |
| `read_only` | 是（系统） | 只读标记，Agent 无法修改 |

### 2.2 记忆块解析

```typescript
// src/agent/memory.ts:55-81
export function parseMdxFrontmatter(content: string): {
  frontmatter: Record<string, string>;
  body: string;
} {
  const frontmatterRegex = /^---\n([\s\S]*?)\n---\n([\s\S]*)$/;
  const match = content.match(frontmatterRegex);

  // 解析 Frontmatter
  // ...

  return { frontmatter, body: body.trim() };
}
```

### 2.3 默认记忆块模板

Letta Code 提供以下默认记忆块模板（位于 `src/agent/prompts/`）：

| 模板文件 | 用途 |
|----------|------|
| `human.mdx` | 用户信息和学习 |
| `persona.mdx` | AI 角色定义 |
| `persona_claude.mdx` | Claude 风格角色 |
| `persona_kawaii.mdx` | Kawaii 风格角色 |
| `persona_memo.mdx` | Memo 风格角色 |
| `project.mdx` | 项目上下文 |
| `style.mdx` | 编码风格偏好 |
| `memory_filesystem.mdx` | 记忆文件系统配置 |

---

## 3. 记忆文件系统（MemFS）

MemFS 是 Letta Code 记忆系统的核心创新，允许将记忆块同步到本地文件系统。

### 3.1 目录结构

```
~/.letta/agents/<agent-id>/
└── memory/                    # 记忆存储目录（Git 仓库）
    ├── system/                # 附加到系统提示词的块
    │   ├── persona/
    │   │   └── behavior.md
    │   ├── human.md
    │   └── project/
    │       ├── overview.md
    │       └── tooling/
    │           └── bun.md
    ├── notes.md               # 根级（未附加）块
    └── archive/              # 归档块
```

### 3.2 层级命名规范

使用 `/` 分隔符创建层级结构：

- `system/persona/behavior.md` → 标签 `persona/behavior`
- `project/tooling/bun.md` → 标签 `tooling/bun`
- `human/prefs/coding_style.md` → 标签 `prefs/coding_style`

**目标结构**：
- 总文件数：15-25 个
- 每文件最大行数：约 40 行
- 层级深度：2-3 层

### 3.3 核心 API

```typescript
// src/agent/memoryFilesystem.ts:21-54

// 获取记忆文件系统根目录
export function getMemoryFilesystemRoot(agentId: string): string;

// 确保目录存在
export function ensureMemoryFilesystemDirs(agentId: string): void;

// 渲染记忆目录树
export function renderMemoryFilesystemTree(
  systemLabels: string[],
  detachedLabels: string[]
): string;

// 应用 MemFS 标志
export async function applyMemfsFlags(
  agentId: string,
  memfsFlag: boolean | undefined,
  noMemfsFlag: boolean | undefined
): Promise<ApplyMemfsFlagsResult>;
```

---

## 4. Git 版本控制集成

MemFS 的核心是基于 Git 的版本控制，提供以下能力：

### 4.1 仓库结构

每个 Agent 的记忆存储在一个 Git 仓库中：

```
远程：$LETTA_BASE_URL/v1/git/$AGENT_ID/state.git
本地：~/.letta/agents/<agent-id>/memory/
```

### 4.2 Git 操作

```typescript
// src/agent/memoryGit.ts

// 克隆记忆仓库
export async function cloneMemoryRepo(agentId: string): Promise<void>;

// 拉取最新更改
export async function pullMemory(agentId: string): Promise<{ updated: boolean; summary: string }>;

// 检查 Git 状态
export async function getMemoryGitStatus(agentId: string): Promise<MemoryGitStatus>;

// 添加 Git 标签（触发后端创建仓库）
export async function addGitMemoryTag(agentId: string): Promise<void>;
```

### 4.3 Pre-commit 钩子

系统安装了一个 pre-commit 钩子来验证记忆文件的 Frontmatter：

```bash
# src/agent/memoryGit.ts:151-283
# 验证规则：
# - Frontmatter 必须存在
# - 必须包含 description（非空）
# - 必须包含 limit（正整数）
# - read_only 是受保护字段，Agent 无法修改
```

### 4.4 认证机制

使用 Basic Auth 进行 Git 操作：

```typescript
// src/agent/memoryGit.ts:87-93
const authArgs = token
  ? [
      "-c",
      `http.extraHeader=Authorization: Basic ${Buffer.from(`letta:${token}`).toString("base64")}`,
    ]
  : [];
```

---

## 5. 记忆与系统提示词

### 5.1 两种模式

Letta Code 支持两种记忆模式：

| 模式 | 说明 |
|------|------|
| `standard` | 标准模式，记忆块通过 Letta API 管理 |
| `memfs` | 文件系统模式，记忆块存储在本地 Git 仓库 |

### 5.2 提示词注入

```typescript
// src/agent/memoryPrompt.ts

// 记忆提示词模式
export type MemoryPromptMode = "standard" | "memfs";

// 协调系统提示词与记忆模式
export function reconcileMemoryPrompt(
  systemPrompt: string,
  mode: MemoryPromptMode
): string;

// 检测提示词漂移
export function detectMemoryPromptDrift(
  systemPrompt: string,
  expectedMode: MemoryPromptMode
): MemoryPromptDrift[];
```

### 5.3 提示词附加内容

**标准模式（SYSTEM_PROMPT_MEMORY_ADDON）：**
- 记忆块说明
- 记忆工具使用指南

**MemFS 模式（SYSTEM_PROMPT_MEMFS_ADDON）：**
- Git 仓库说明
- 文件同步指南
- 提交和推送命令

---

## 6. 记忆初始化与重组

### 6.1 初始化流程

当用户运行 `/init` 命令时，AI 会执行以下操作：

1. **检查现有记忆块**：使用 `memory` 工具查看当前状态
2. **询问用户**：了解用户偏好、项目背景、工作方式
3. **爆炸式重组**：将大块记忆拆分为 15-25 个层级化小文件
4. **创建目录结构**：使用 `/` 命名创建 2-3 层深度

### 6.2 目标结构示例

```
system/
├── human.md                      # 索引：指向子文件
├── human/
│   ├── background.md             # 用户背景
│   ├── prefs.md                  # 偏好索引
│   └── prefs/
│       ├── communication.md      # 沟通偏好
│       ├── coding_style.md       # 编码风格
│       └── review_style.md       # 审查偏好
├── project.md                    # 项目索引
├── project/
│   ├── overview.md               # 项目概览
│   ├── architecture.md          # 架构
│   └── tooling/
│       ├── bun.md                # Bun 配置
│       └── testing.md           # 测试配置
└── persona.md                    # 角色索引
    └── persona/
        ├── role.md              # 角色定义
        └── behavior.md          # 行为准则
```

### 6.3 只读记忆块

某些记忆块被标记为只读，Agent 无法修改：

```typescript
// src/agent/memoryConstants.ts
export const READ_ONLY_BLOCK_LABELS = ["memory_filesystem"] as const;
```

---

## 7. 睡眠时间记忆管理

Letta Code 包含一个专门的睡眠时间（Sleep-time）子智能体，负责在会话间隙维护记忆：

### 7.1 职责

- 实时更新记忆块（不等待会话结束）
- 保持记忆块简洁和有用
- 重组过大的记忆块为层级结构
- 强制执行大小限制
- 更新 persona 块以反映学到的经验

### 7.2 行为准则

```markdown
# src/agent/prompts/sleeptime.ts

- Update memory blocks in real-time
- Reorganize when structure becomes unclear
- Keep memory blocks under size limits through aggressive consolidation
- Never let memory blocks grow stale or bloated
- Assume the primary agent relies entirely on memory blocks for context
```

---

## 8. 记忆工具

### 8.1 工具列表

当 MemFS 禁用时，Agent 可使用以下记忆工具：

```typescript
// src/tools/toolset.ts:20-27
export const MEMORY_TOOL_NAMES = new Set([
  "memory",
  // ... 其他工具
]);
```

### 8.2 MemFS 分离

当启用 MemFS 时，旧的基于 API 的记忆工具会被分离：

```typescript
// src/agent/memoryFilesystem.ts:205-208
if (isEnabled && memfsFlag) {
  const { detachMemoryTools } = await import("../tools/toolset");
  await detachMemoryTools(agentId);
}
```

Agent 现在通过文件系统（`mkdir`、`mv`、`edit`）直接操作记忆文件。

---

## 9. 记忆检查提醒

Letta Code 会定期提醒 Agent 检查记忆：

```markdown
# src/agent/prompts/memory_check_reminder.txt

MEMORY CHECK: Review this conversation for information worth storing in your memory blocks.

Ask yourself: "If I started a new session tomorrow, what from this conversation would I want to remember?"
```

---

## 10. 数据流总结

```
┌─────────────────────────────────────────────────────────────┐
│                     用户交互层                               │
│  /init  /remember  /reflect  常规对话                        │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Agent 智能体                              │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              系统提示词 (System Prompt)               │  │
│  │  - 基础指令                                          │  │
│  │  - 记忆块内容 (附加)                                  │  │
│  │  - 记忆提示词附加                                     │  │
│  └─────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
    ┌────▼────┐                    ┌─────▼─────┐
    │ Standard │                    │   MemFS   │
    │  模式    │                    │   模式    │
    └────┬────┘                    └─────┬─────┘
         │                               │
    ┌────▼──────────────────────────┐    │
    │    Letta Cloud API            │    │
    │    - 记忆块 CRUD              │    │
    │    - 记忆搜索                 │    │
    └───────────────────────────────┘    │
                                         │
                              ┌──────────▼──────────┐
                              │  本地文件系统       │
                              │  ~/.letta/agents/  │
                              │  └── memory/       │
                              │      └── (Git 仓库) │
                              └───────────────────┘
```

---

## 11. 核心设计原则

### 11.1 持久化优先

记忆是 Letta Code 的核心价值。Agent 期望与用户长期合作，记忆不是便利性功能，而是持续改进的基础。

### 11.2 层级组织

通过 `/` 分隔符创建层级结构，使记忆：
- 更易扫描
- 更易维护
- 更易与其他 Agent 共享

### 11.3 爆炸式拆分

目标是将大型记忆块拆分为 15-25 个小型专注文件：
- 每个文件约 40 行
- 2-3 层深度
- 强制执行大小限制

### 11.4 版本控制

Git 集成提供：
- 变更历史
- 冲突解决
- 备份和恢复
- 多设备同步

### 11.5 实时更新

不等待会话结束，实时更新记忆：
- 立即存储重要信息
- 持续保持记忆准确

---

## 12. 总结

Letta Code 的记忆系统是一个精心设计的复杂系统，核心特点：

1. **持久化**：跨会话保留记忆，Agent 能够学习和成长
2. **层级化**：通过文件系统层级组织记忆，提高可维护性
3. **版本化**：Git 集成提供变更历史和同步能力
4. **自动化**：睡眠时间管理自动维护记忆质量
5. **工具化**：通过记忆工具和技能系统提供灵活的内存管理能力

这套系统使 Letta Code 区别于传统的一次性会话 AI 工具，成为真正的长期编程伙伴。
