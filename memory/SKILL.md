---
name: persistent-memory
description: Use when user shares preferences, project conventions, or important context that should persist across sessions
---

# Persistent Memory

## Overview

持久化记忆系统，让 AI 能够在跨会话中记住用户的偏好、项目约定和重要上下文。核心原则：**每次有价值的交互都应该被持久化**。

## When to Use

**必须主动记忆的场景：**

- 用户明确说明偏好："我更喜欢 tabs"
- 用户暗示偏好：行为模式、沟通风格
- 项目技术决策：运行时选择、代码规范、测试框架
- 历史上下文：之前修复的 bug、重要的 PR、废弃的模式
- 任何用户说"记住"、"别忘了"、"上次我们"

**立即触发记忆的命令：**
- `/remember` - 记住当前信息
- `/init-memory` - 初始化记忆结构
- `/reflect` - 反思并更新记忆

## Core Pattern

### 1. 记忆存储位置

```
~/.claude/memory/
├── system/                    # 附加到 system prompt
│   ├── persona/
│   │   ├── behavior.md       # 行为准则
│   │   └── constraints.md    # 约束限制
│   ├── human/
│   │   ├── background.md     # 用户背景
│   │   └── preferences/
│   │       ├── coding.md    # 编码偏好
│   │       └── comm.md      # 沟通偏好
│   └── project/
│       ├── overview.md       # 项目概览
│       ├── tooling.md       # 工具配置
│       └── conventions.md   # 约定规范
└── detached/                 # 按需加载
    ├── history/              # 历史上下文
    └── archive/             # 归档
```

### 2. 记忆文件格式

```markdown
---
label: preferences/coding
description: 用户的编码偏好，影响代码生成风格
---

# 编码偏好

## 格式
- 缩进: Tabs (非 spaces)
- 行尾: LF (非 CRLF)

## 风格
- 避免 try-catch 用于控制流
- 使用 early return
- 添加 JSDoc 注释

## 沟通
- 修改代码前先解释思路
```

### 3. 关键原则

| 原则 | 说明 |
|------|------|
| **主动** | 不需要用户说"记住"，看到有价值的信息就存 |
| **层级化** | 使用 `/` 分隔符创建 2-3 层深度 |
| **小而专注** | 每个文件 ~40 行，一个主题 |
| **可检索** | 文件名和路径要有意义 |

## Quick Reference

### 常用命令

| 命令 | 用途 |
|------|------|
| `/remember <信息>` | 快速记住当前信息 |
| `/init-memory` | 初始化层级记忆结构 |
| `/reflect` | 反思并更新记忆 |
| `/memory-check` | 检查当前记忆状态 |

### 文件操作

```bash
# 读取记忆
cat ~/.claude/memory/system/human/preferences/coding.md

# 更新记忆
echo "新偏好内容" >> ~/.claude/memory/system/human/preferences/coding.md

# 创建新记忆块
cat > ~/.claude/memory/system/project/tooling/bun.md << 'EOF'
---
label: project/tooling/bun
description: Bun 运行时相关配置
---

# Bun 配置
EOF
```

## Implementation

### 初始化记忆结构

```bash
mkdir -p ~/.claude/memory/system/{persona,human/preferences,project}
mkdir -p ~/.claude/memory/detached/{history,archive}
```

### 记忆注入到 System Prompt

在会话开始时，将 `system/` 下的所有 .md 文件内容附加到 system prompt：

```
以下是你需要知道的重要信息：

--- USER PREFERENCES ---
[读取 ~/.claude/memory/system/human/**/*.md]

--- PROJECT CONTEXT ---
[读取 ~/.claude/memory/system/project/**/*.md]

--- BEHAVIOR GUIDELINES ---
[读取 ~/.claude/memory/system/persona/**/*.md]
```

### 自动记忆脚本

创建 `~/.claude/remember.sh`:

```bash
#!/bin/bash
# 用法: remember "标签" "内容"

LABEL="$1"
CONTENT="$2"
DATE=$(date +%Y-%m-%d)

mkdir -p ~/.claude/memory/detached

cat >> ~/.claude/memory/detached/"$LABEL".md << EOF
---
label: $LABEL
date: $DATE
---

$CONTENT
EOF
```

## Common Mistakes

| 错误 | 后果 | 修正 |
|------|------|------|
| 只在当前会话记住 | 信息丢失 | 立即写入文件系统 |
| 记忆块太大 | 难以检索 | 拆分成多个小文件 |
| 扁平结构 | 混乱 | 使用 `/` 创建层级 |
| 不更新旧记忆 | 信息过时 | 定期 `/reflect` |
| 不告诉用户 | 用户不知道 | 主动确认"已记住" |

## Red Flags - 立即行动

**以下情况意味着你违反了记忆原则，必须立即修正：**

- ❌ "我会在当前会话中记住这个" → 必须写入文件
- ❌ 用户说"上次我们"而你不知道 → 没有加载历史记忆
- ❌ 用户重复说同一偏好 → 没有正确存储
- ❌ 用户说"我之前告诉过你" → 记忆未持久化
- ❌ 忘记用户的编码偏好 → 没有在会话开始时加载

**所有这些情况都意味着：写入记忆文件，然后继续**。

## Workflow

```dot
digraph memory_flow {
    "用户提供信息" -> "判断是否值得记忆?"
    "判断是否值得记忆?" -> "是" [label="偏好/约定/上下文"]
    "判断是否值得记忆?" -> "否" [label="一次性问题"]
    "是" -> "选择正确位置"
    "选择正确位置" -> "human/preferences" [label="用户偏好"]
    "选择正确位置" -> "project" [label="项目相关"]
    "选择正确位置" -> "persona" [label="行为准则"]
    "选择正确位置" -> "detached" [label="历史上下文"]
    "选择正确位置" -> "写入记忆文件"]
    "写入记忆文件" -> "确认已记住"
}
```

## 启动时自动加载（重要）

**必须执行**：每次会话开始时，必须加载记忆文件到上下文中。

### 自动加载 Hook

在 `~/.claude/settings.json` 中配置 hooks:

```json
{
  "hooks": {
    "MemoryLoad": {
      "match": ".*",
      "command": "cat ~/.claude/memory/system/human/preferences/*.md ~/.claude/memory/system/project/*.md 2>/dev/null"
    }
  }
}
```

### 手动加载命令

如果 hook 未配置，会话开始时执行：

```bash
# 加载所有 system 记忆到上下文
cat ~/.claude/memory/system/human/preferences/*.md
cat ~/.claude/memory/system/project/*.md
cat ~/.claude/memory/system/persona/*.md
```

### 记忆检查提醒

在长会话中，如果用户提供了重要信息但没有明确要求"记住"，应该在以下时机主动检查：

1. **用户说完一段重要上下文后**
2. **会话进行 30 分钟后**
3. **用户表达挫折或提到过去的问题时**

提醒话术：
> "我注意到你提到了一些重要的背景信息，需要我记住这些以便将来参考吗？"

## 与其他工具集成

| 工具 | 集成方式 |
|------|----------|
| conversation_search | 搜索历史对话补充记忆 |
| Read | 读取记忆文件 |
| Write/Edit | 更新记忆文件 |
| Bash | 文件操作 |
