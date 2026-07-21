# OpenCowork Agent 设计分析

## 架构概览

```
AgentManager (会话管理)
    └── AgentRuntime (每个会话一个实例)
            ├── FileSystemTools (文件系统工具)
            ├── SDKTools (SDK 工具)
            ├── SkillManager (技能管理)
            ├── MCPClientService (MCP 客户端)
            └── AutoMemoryManager (自动记忆)
```

## 核心特性

| 特性 | 实现质量 | 说明 |
|------|---------|------|
| **多会话管理** | ⭐⭐⭐⭐⭐ | 每个会话独立 Agent 实例，支持多窗口广播 |
| **智能历史裁剪** | ⭐⭐⭐⭐⭐ | 基于 token 预算 + 优先级策略，自动保留重要对话 |
| **记忆系统** | ⭐⭐⭐⭐ | 自动保存/检索重要信息到本地文件 |
| **权限管理** | ⭐⭐⭐⭐ | 三级信任模式 (strict/standard/trust) |
| **流式输出** | ⭐⭐⭐⭐⭐ | 实时 token 广播，定期保存防丢失 |
| **后台任务** | ⭐⭐⭐ | 支持后台异步执行任务 |
| **Extended Thinking** | ⭐⭐⭐⭐ | 自动尝试启用，降级兼容 |

## 详细设计

### 1. 会话管理 (AgentManager)

- 每个会话独立 Agent 实例
- 定时清理空闲 Agent（30分钟超时）
- 多窗口广播支持

**核心代码位置**: `electron/agent/AgentManager.ts`

### 2. 消息处理 (AgentRuntime)

**智能历史裁剪策略**:
- 保留最近 20 条消息（确保连贯性）
- 按优先级保留旧消息（工具调用 > 决策 > 偏好 > 普通）
- 自动保存被裁剪的重要信息到记忆

```typescript
// 优先级策略
- 工具调用 (tool_use/tool_result): +10
- 决策关键词 (决定/选择/use/adopt): +15
- 偏好关键词 (我喜欢/i prefer/风格): +12
- 知识关键词 (学到/learned/理解): +10
- 错误/问题 (error/bug/问题): +8
- 助手回复: +5
```

**核心代码位置**: `electron/agent/AgentRuntime.ts`

### 3. 工具系统

**内置工具**:
- `read_file` - 读取文件
- `write_file` - 写入文件
- `list_dir` - 列出目录
- `run_command` - 执行命令
- `edit_file` - 编辑文件
- `glob` - 文件搜索
- `grep` - 内容搜索
- `web_fetch` - 网页抓取
- `web_search` - 网页搜索
- `todo_write` - 任务管理
- `ask_user_question` - 用户问答

**扩展能力**:
- **Skills**: 动态加载，兼容 Claude Code 格式
- **MCP**: 支持外部 MCP 服务

**核心代码位置**: `electron/agent/tools/`

### 4. 权限控制

**三级信任模式**:

| 模式 | 读取 | 安全命令 | 危险命令 | 写入 |
|------|------|---------|---------|------|
| strict | 需授权 | 需确认 | 需确认 | 需确认 |
| standard | 需授权 | 自动批准 | 需确认 | 新文件自动，旧文件确认 |
| trust | 需授权 | 自动批准 | 自动批准 | 自动批准 |

**危险命令模式**:
```typescript
const DANGEROUS_PATTERNS = [
    /rm\s+-rf\s+/i,      // 递归强制删除
    /del\s+\/s\s+\/q/i,  // Windows 强制删除
    /format\s+/i,        // 格式化
    /mkfs/i,             // 创建文件系统
    /dd\s+if=/i,         // 磁盘写入
    /chmod\s+777/i       // 过度授权
];
```

**安全命令白名单**:
```typescript
const SAFE_COMMANDS = [
    'python', 'python3', 'node', 'npm', 'pip', 'git',
    'ls', 'cat', 'head', 'tail', 'grep', 'find', 'echo',
    'curl', 'wget', 'tree', 'wc', 'sort', 'uniq', 'diff'
];
```

**核心代码位置**: `electron/agent/security/PermissionManager.ts`

### 5. 记忆系统

**功能**:
- 自动分析对话，保存重要信息
- 相关记忆自动检索注入上下文
- 支持长期记忆积累

**工作流程**:
1. 用户发送消息 → 检查相关记忆
2. AI 回复后 → 分析并保存重要信息
3. 历史裁剪时 → 自动保存被移除的重要信息

**核心代码位置**: `electron/memory/AutoMemoryManager.ts`

### 6. 流式输出与持久化

**流式广播**:
- 实时 token 推送到前端
- 每 10 个 token 或 1 秒保存一次到 SessionStore

**会话恢复**:
- 切换会话不丢失流式内容
- 支持中断后继续

### 7. Extended Thinking 支持

**自动兼容**:
```typescript
// 默认尝试启用 thinking
requestConfig.thinking = {
    type: 'enabled',
    budget_tokens: 20000
};

// 如果不支持则降级
if (error.includes('unsupported'|'unknown parameter')) {
    retry without thinking
}
```

## Skills 集成

### 格式兼容

OpenCowork 的 Skills 格式与 Claude Code 完全兼容:

```
skill-name/
├── SKILL.md           # 必需：包含 YAML frontmatter + Markdown 指令
├── scripts/           # 可选：可执行脚本
├── references/        # 可选：参考资料
└── assets/           # 可选：资源文件
```

### 加载流程

1. 从 `~/.opencowork/skills` 加载用户 Skills
2. 从 `resources/skills` 加载内置 Skills
3. 解析 SKILL.md 的 frontmatter 获取 name/description
4. 将 Skills 转换为 Anthropic Tool 格式
5. Agent 运行时自动选择使用

## MCP 集成

### 支持情况

- 兼容官方 MCP 协议
- 开箱即用 10 个 MCP 服务
- 支持自定义 MCP 服务器配置

### 工具调用

MCP 工具使用 namespace 前缀: `tool_name__action`

## 可改进点 ⚠️

1. **错误处理** - 部分错误信息可以更友好
2. **并发控制** - 目前单会话单任务，可以考虑支持并发
3. **工具验证** - MCP 工具名称格式验证可以更健壮
4. **监控指标** - 可以增加更多运行时指标

## 总结

OpenCowork 的 Agent 设计**相当专业**:

- ✅ 架构清晰，模块化好
- ✅ 功能完整（记忆/权限/后台任务/SSE）
- ✅ 兼容 Claude Code Skills 和 MCP
- ✅ 考虑了实际使用中的边缘情况（流式丢失、会话恢复等）

**整体评价**: 这是一个生产级的 Agent 运行时设计，接入 Claude Code 格式的 Skills 完全没问题。

## 相关文件

| 文件 | 说明 |
|------|------|
| `electron/agent/AgentManager.ts` | 会话管理 |
| `electron/agent/AgentRuntime.ts` | 核心运行时 (1553 行) |
| `electron/agent/BackgroundTaskManager.ts` | 后台任务 |
| `electron/agent/skills/SkillManager.ts` | 技能管理 |
| `electron/agent/mcp/MCPClientService.ts` | MCP 客户端 |
| `electron/agent/security/PermissionManager.ts` | 权限管理 |
| `electron/agent/tools/FileSystemTools.ts` | 文件系统工具 |
| `electron/agent/tools/SDKTools.ts` | SDK 工具 |
| `electron/memory/AutoMemoryManager.ts` | 自动记忆 |
