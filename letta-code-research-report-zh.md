# Letta Code 项目深度调研报告

## 项目概述

### 什么是 Letta Code

Letta Code 是一个运行在终端中的有状态（Stateful）AI 编程助手 CLI 工具，由 Letta 公司开发。与传统的会话式 AI 编程工具（如 Claude Code、OpenAI Codex、Google Gemini CLI）不同，Letta Code 的核心差异化在于**持久化智能体**和**长期学习能力**。

**核心理念**：
- 智能体跨会话持久存在，不会每次对话都重新开始
- 持久的记忆系统，让 AI 能够从历史交互中学习和成长
- 支持多种主流 LLM 提供商（Anthropic、OpenAI、Google、MiniMax 等）

### 版本与发布

当前版本：**0.15.6**（2025年发布）

---

## 技术架构

### 技术栈

| 类别 | 技术 |
|------|------|
| **运行时** | Bun（首选）、Node.js（兼容） |
| **语言** | TypeScript |
| **TUI 框架** | Ink（React 18.2.0 for CLI） |
| **API 客户端** | @letta-ai/letta-client |
| **构建工具** | Bun Build |
| **代码质量** | Biome、TypeScript |

### 目录结构

```
letta-code/
├── src/
│   ├── index.ts              # 主入口文件（约80KB）
│   ├── headless.ts           # 无头模式入口
│   ├── agent/                # 智能体核心逻辑
│   │   ├── App.tsx           # 主应用组件（约450KB）
│   │   ├── prompts/          # 系统提示词模板
│   │   ├── subagents/        # 子智能体定义
│   │   ├── memory.ts         # 记忆系统
│   │   ├── skills.ts         # 技能系统
│   │   └── create.ts         # 智能体创建逻辑
│   ├── cli/                  # CLI 相关
│   │   ├── components/       # React 组件（76个）
│   │   ├── subcommands/      # 子命令（agents、blocks、memfs、messages）
│   │   └── profile-selection.tsx
│   ├── tools/                # 工具实现
│   │   ├── impl/             # 工具实现（40+ 个）
│   │   ├── manager.ts        # 工具管理器
│   │   └── toolDefinitions.ts
│   ├── providers/            # LLM 提供商
│   │   ├── byok-providers.ts
│   │   ├── openai-codex-provider.ts
│   │   ├── minimax-provider.ts
│   │   └── ...
│   ├── skills/               # 内置技能
│   │   └── builtin/          # 14+ 个内置技能
│   ├── permissions/          # 权限系统（9个模块）
│   ├── hooks/                # 生命周期钩子
│   └── utils/                # 工具函数
├── bin/                      # 入口脚本
├── scripts/                  # 构建脚本
├── package.json
└── CLAUDE.md                 # 项目规范
```

### 入口与启动

- **`src/index.ts`**：主入口，处理 CLI 参数解析和主应用启动
- **`bin/letta.js`**：npm 包入口，跨平台二进制分发器
- **`build.js`**：使用 Bun 构建，将 TypeScript 打包为单个 JS 文件

---

## 核心系统详解

### 1. 记忆系统（Memory System）

Letta Code 最核心的差异化特性是它的记忆系统。

#### 记忆块（Memory Blocks）

记忆系统的基础单位是**记忆块（Memory Blocks）**，每个记忆块包含：
- **Label（标签）**：标题/名称
- **Description（描述）**：解释该记忆块如何影响 AI 的行为
- **Value（值）**：实际内容

记忆块有以下类型：

| 类型 | 说明 |
|------|------|
| `persona` | AI 角色定义 |
| `human` | 用户偏好和背景 |
| `project` | 项目上下文 |
| `skills` | 技能定义 |
| `notes` | 笔记 |

#### 记忆文件系统（MemFS）

可选功能，允许将记忆块同步到本地文件系统：
- 路径：`~/.letta/agents/<agent-id>/memory/`
- 支持分层组织记忆块（使用 `/` 命名，如 `project/architecture`、`user/preferences`）
- 用户可以直接编辑文件系统中的 `.md` 文件来更新 AI 记忆

#### 睡眠时间记忆管理

内置的睡眠时间（Sleep-time）子智能体负责：
- 实时更新记忆块
- 保持记忆块简洁和有用
- 重组过大的记忆块为层级结构
- 强制执行大小限制

#### 记忆初始化

新智能体创建时会自动初始化默认记忆块，用户可以通过 `/init` 命令重新组织记忆结构。

### 2. 技能系统（Skills System）

Letta Code 内置 14+ 个技能（Skills），每个技能是一个可重用的能力模块。

#### 内置技能列表

| 技能 | 功能 |
|------|------|
| `/skill-create` | 创建新技能 |
| `/skill-get` | 获取技能详情 |
| `/skill-list` | 列出所有可用技能 |
| `/skill-learn` | 学习新技能 |
| `/init` | 初始化/重组记忆 |
| `/remember` | 记住重要信息 |
| `/reflect` | 反思和总结 |
| `memory-check` | 检查记忆状态 |
| `history-analyzer` | 分析对话历史 |

#### 技能学习

- AI 可以从外部文档学习新技能
- 支持 MCP（Model Context Protocol）转换为技能
- 技能可以被其他智能体共享和使用

### 3. 权限系统（Permissions）

Letta Code 实现了细粒度的权限控制。

#### 权限模式

| 模式 | 说明 |
|------|------|
| `ask` | 询问用户授权 |
| `auto-approve` | 自动批准 |
| `readonly` | 只读模式 |

#### 权限检查流程

```
permissions/
├── analyzer.ts    # 分析权限需求
├── checker.ts     # 检查权限
├── loader.ts      # 加载权限配置
├── matcher.ts     # 匹配权限规则
├── mode.ts        # 权限模式管理
├── session.ts     # 会话权限
└── types.ts       # 类型定义
```

### 4. 工具系统（Tools）

Letta Code 提供了 40+ 个工具供 AI 智能体使用。

#### 工具分类

| 类别 | 工具示例 |
|------|---------|
| **文件系统** | read、write、edit、glob、grep |
| **Shell** | bash、run |
| **Git** | git_status、git_commit |
| **编辑** | str_replace_editor |
| **搜索** | ripgrep_search |
| **网络** | http_request |

#### 工具管理

- 工具定义在 `tools/toolDefinitions.ts`
- 工具实现在 `tools/impl/`
- 工具管理器：`tools/manager.ts`

---

## LLM 提供商集成

Letta Code 支持多种 LLM 提供商，采用 BYOK（Bring Your Own Key，自带密钥）模式。

### 支持的提供商

| 提供商 | 模型 |
|--------|------|
| **Anthropic** | Claude Sonnet 4.6、Opus 4.6、Haiku |
| **OpenAI** | GPT-5、GPT-4.1、o4-mini |
| **Google** | Gemini 2.5 Pro/Flash、Gemini 3 Pro |
| **ChatGPT+** | GPT-5.3 Codex、GPT-5.2 Codex |
| **MiniMax** | M2.5、M2.1 |
| **ZAI** | GLM-5、GLM-4.7 |
| **OpenRouter** | Kimi K2、DeepSeek V3.1 等 |

### OAuth 集成

支持通过 OAuth 认证接入：
- ChatGPT Plus 计划
- OpenAI Codex

### 提供商文件

| 文件 | 用途 |
|------|------|
| `byok-providers.ts` | 自带密钥提供商配置 |
| `openai-codex-provider.ts` | OpenAI Codex 集成 |
| `minimax-provider.ts` | MiniMax 集成 |
| `openrouter-provider.ts` | OpenRouter 集成 |
| `zai-provider.ts` | ZAI 集成 |

---

## CLI 功能

### 主命令

```bash
letta              # 启动交互式 TUI
letta -p "prompt"  # 无头模式（一次性提示）
```

### 子命令

| 命令 | 功能 |
|------|------|
| `letta memfs` | 管理记忆文件系统 |
| `letta agents` | 管理智能体 |
| `letta messages` | 查看消息历史 |
| `letta blocks` | 管理记忆块 |

### 命令行参数

- `-p, --prompt`：无头模式
- `-m, --model`：指定模型
- `--no-color`：禁用颜色输出

---

## 测试与质量

### 测试覆盖

- **80+ 测试文件**：单元测试、集成测试
- 测试框架：`bun test`
- 持续集成：GitHub Actions

### 代码质量

- **Biome**：代码检查和格式化
- **TypeScript**：静态类型检查
- **Husky + lint-staged**：Git 钩子

---

## 项目特点总结

### 优势

1. **记忆持久化**：区别于其他 CLI 工具的核心优势，AI 能记住跨会话的上下文
2. **层级记忆**：支持分层组织记忆块，易于管理和检索
3. **多提供商支持**：灵活切换不同 LLM
4. **细粒度权限**：安全的操作控制
5. **技能系统**：可扩展的能力模块

### 与竞品对比

| 特性 | Letta Code | Claude Code | Codex |
|------|-----------|-------------|-------|
| 记忆持久化 | ✅ | ❌ | ❌ |
| 层级记忆 | ✅ | ❌ | ❌ |
| 技能系统 | ✅ | ✅ | ✅ |
| 多模型支持 | ✅ | 仅 Anthropic | 仅 OpenAI |

---

## 总结

Letta Code 是一个功能完善的 AI 编程助手 CLI 工具，其核心价值在于**记忆持久化**和**长期学习能力**。通过 Bun + TypeScript + React (Ink) 构建，提供完整的终端交互界面。

该工具特别适合：
- 需要长期维护项目的开发者
- 希望 AI 记住个人偏好的用户
- 需要多模型切换的团队
