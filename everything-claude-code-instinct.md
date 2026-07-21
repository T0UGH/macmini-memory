# Everything Claude Code — Instinct 系统深度解读

> **让 Claude Code 从你的使用习惯中自动学习，把踩坑经验变成可复用的"本能"**

GitHub: https://github.com/affaan-m/everything-claude-code

---

## 一句话理解

你用 Claude Code 干活 → 系统在后台悄悄观察你的行为 → 提炼成"本能"（Instinct） → 积累够了自动进化成 Skill → 下次遇到类似场景直接触发。

---

## 核心流程

```
1. 观察  →  Hooks 捕获每次工具调用（Edit/Bash/Read...）
                    ↓
2. 记录  →  写入 observations.jsonl（一行一条，流式追加）
                    ↓
3. 分析  →  后台 Observer（Haiku 模型）每 5 分钟分析一次
                    ↓
4. 提炼  →  检测模式，生成带置信度的 Instinct（0.3-0.9）
                    ↓
5. 进化  →  /evolve 命令：聚合相关 Instinct → 生成 Skill/Command/Agent
                    ↓
6. 晋升  →  同一个 Instinct 在 2+ 项目出现 → 自动晋升为全局本能
```

---

## 数据格式详解

### Observation（观察记录）

每次你在 Claude Code 里用一个工具，Hook 就记一条：

```jsonl
{
  "timestamp": "2025-01-22T10:30:00Z",
  "event": "tool_complete",
  "tool": "Edit",
  "session": "abc123",
  "project_id": "a1b2c3d4e5f6",
  "project_name": "my-react-app",
  "input": "修改了 src/App.tsx 的第 42 行...",
  "output": "文件已更新"
}
```

- JSONL 格式，一行一条，方便流式处理
- 自动脱敏：API key、token、password 等会被替换为 `[REDACTED]`
- 超过 10MB 自动归档到 `observations.archive/`
- 输入输出各限制 5000 字符

### Instinct（本能）

从观察中提炼出的原子级知识，用 YAML + Markdown 格式：

```yaml
---
id: prefer-functional-style
trigger: "when writing new functions"
confidence: 0.75
domain: "code-style"
source: "session-observation"
scope: "project"
project_id: "a1b2c3d4e5f6"
project_name: "my-react-app"
---

# Prefer Functional Style

## Action
Use functional patterns over classes when appropriate.

## Evidence
- Observed 5 instances of functional pattern preference
- User corrected class-based approach to functional on 2025-01-15
- Last observed: 2025-01-22
```

**字段说明：**

| 字段 | 含义 | 示例 |
|------|------|------|
| `id` | 唯一标识（kebab-case） | `prefer-functional-style` |
| `trigger` | 什么时候触发 | `"when writing new functions"` |
| `confidence` | 置信度（0.3-0.9） | `0.75` |
| `domain` | 领域分类 | code-style / testing / git / debugging / workflow / security |
| `source` | 来源 | session-observation / inherited / promoted / auto-promoted / repo-analysis |
| `scope` | 作用域 | project（仅当前项目） / global（所有项目） |

---

## 置信度评分系统

### 初始置信度（基于观察频率）

| 观察次数 | 初始置信度 | 含义 |
|----------|-----------|------|
| 1-2 次 | 0.3 | 试探性的，仅建议 |
| 3-5 次 | 0.5 | 中等确信，相关时应用 |
| 6-10 次 | 0.7 | 强确信，自动应用 |
| 11+ 次 | 0.85 | 核心行为，高优先级 |

### 动态调整

- **确认**：每次观察到符合的行为 → +0.05
- **矛盾**：观察到相反的行为 → -0.10
- **衰减**：每周没有观察到 → -0.02

> 类比 Evolver：Instinct 的置信度 ≈ Capsule 的 confidence + success_streak 的简化版

---

## 项目隔离机制

系统按项目隔离，不同项目有不同的本能库。

### 项目 ID 怎么来的

```
git remote URL → SHA256 哈希 → 取前 12 位
例：https://github.com/me/my-app.git → sha256 → a1b2c3d4e5f6
```

优先级：
1. `CLAUDE_PROJECT_DIR` 环境变量（最高）
2. `git remote get-url origin` → 哈希（跨机器稳定）
3. `git rev-parse --show-toplevel` → 回退方案
4. 无项目 → 全局作用域

### 项目注册表

`~/.claude/homunculus/projects.json`：

```json
{
  "a1b2c3d4e5f6": {
    "name": "my-react-app",
    "root": "/Users/me/projects/my-react-app",
    "remote": "https://github.com/me/my-react-app.git",
    "last_seen": "2025-01-22T10:30:00Z"
  }
}
```

### Scope 决策指南

| 类型 | 归属 | 例子 |
|------|------|------|
| **项目级**（默认） | 仅当前项目 | React hooks 偏好、项目文件结构、框架特定模式 |
| **全局级** | 所有项目 | 安全实践、Git 规范、通用工具使用习惯 |

原则：**默认 project，宁窄勿宽，后续可晋升。**

---

## Observer 观察者代理

后台运行的 AI 分析进程，使用 Haiku 模型（快且便宜）。

### 检测的模式类型

| 模式类型 | 怎么检测的 | 例子 |
|----------|-----------|------|
| 用户纠正 | "不对，用 X 不要用 Y" | 用户纠正了 class → function |
| 错误修复 | 工具报错 → 下一步修复 | Edit 失败 → 换个方式 Edit |
| 重复工作流 | 同一个工具序列多次出现 | 总是先 Grep 再 Read 再 Edit |
| 工具偏好 | 一直用某个工具 | 总是用 Grep 而不是 Bash grep |
| 代码风格 | 代码中的一致模式 | 总是用 arrow function |

### 触发条件

- 积累 ≥ 20 条观察记录后才会分析
- 每 5 分钟检查一次（可配置）
- Hook 通过 SIGUSR1 信号通知 Observer 有新数据

---

## 进化管线（/evolve）

当 Instinct 积累到一定量，可以聚合成更高级的形态：

### 三种进化产物

| 产物 | 条件 | 用途 | 生成位置 |
|------|------|------|----------|
| **Skill** | 2+ 个 Instinct 触发条件相似 | 自动触发的行为规则 | `evolved/skills/<name>/SKILL.md` |
| **Command** | 高置信度(≥0.7)的工作流 Instinct | 用户主动调用的命令 | `evolved/commands/<name>.md` |
| **Agent** | 3+ 个 Instinct，平均置信度 ≥0.75 | 复杂多步骤流程 | `evolved/agents/<name>.md` |

### 聚类算法

```
1. 标准化触发条件（小写、去掉 "when"/"creating" 等停用词）
2. 按标准化后的 trigger 分组
3. 过滤：只保留 2+ 个 Instinct 的组
4. 排序：按组大小和平均置信度
5. 生成建议：告诉你哪些可以合并成 Skill/Command/Agent
```

### 示例

```
Instinct 1: "when writing React components" → 用 functional component（0.8）
Instinct 2: "when writing React components" → 用 hooks 而不是 class state（0.7）
Instinct 3: "when writing React components" → 加 TypeScript props 接口（0.75）
                    ↓
/evolve 检测到这三个触发条件相似
                    ↓
建议生成 Skill: "react-patterns"（合并三条规则）
                    ↓
/evolve --generate → 生成 evolved/skills/react-patterns/SKILL.md
```

---

## 晋升机制（Promote）

项目级 Instinct 可以晋升为全局：

### 自动晋升条件
- 同一个 Instinct ID 在 **2+ 个项目**中出现
- 跨项目**平均置信度 ≥ 0.8**
- 尚未是全局的

### 晋升流程

```bash
# 查看可晋升的候选
python3 instinct-cli.py evolve

# 预览（不实际操作）
python3 instinct-cli.py promote --dry-run

# 晋升指定 Instinct
python3 instinct-cli.py promote prefer-functional-style

# 自动晋升所有符合条件的
python3 instinct-cli.py promote
```

晋升后标记为 `source: auto-promoted`，带上 `promoted_from` 和 `seen_in_projects` 字段。

---

## 导入/导出（知识共享）

### 导出你的本能

```bash
# 导出所有
python3 instinct-cli.py export --output my-instincts.yaml

# 只导出高置信度的
python3 instinct-cli.py export --min-confidence 0.7

# 只导出某个领域的
python3 instinct-cli.py export --domain testing
```

### 导入别人的本能

```bash
# 从文件导入
python3 instinct-cli.py import teammate-instincts.yaml

# 从 URL 导入
python3 instinct-cli.py import https://example.com/instincts.yaml

# 预览不实际导入
python3 instinct-cli.py import file.yaml --dry-run

# 只导入高置信度的
python3 instinct-cli.py import file.yaml --min-confidence 0.7
```

### 合并策略

| 情况 | 操作 |
|------|------|
| 新 Instinct | 添加 |
| 已有 + 导入置信度更高 | 更新 |
| 已有 + 导入置信度更低 | 跳过（保留本地） |
| 低于 `--min-confidence` | 跳过 |

---

## 完整目录结构

```
~/.claude/homunculus/
├── identity.json                    # 用户身份
├── projects.json                    # 项目注册表
├── disabled                         # 存在则禁用观察
│
├── instincts/                       # 全局本能
│   ├── personal/                    #   自己积累的
│   │   ├── validate-user-input.yaml
│   │   └── prefer-explicit-errors.yaml
│   └── inherited/                   #   从别人导入的
│
├── evolved/                         # 全局进化产物
│   ├── skills/
│   ├── commands/
│   └── agents/
│
└── projects/
    └── a1b2c3d4e5f6/               # 项目级存储
        ├── observations.jsonl       #   观察记录
        ├── observations.archive/    #   归档
        ├── observer.log             #   Observer 日志
        ├── .observer.pid            #   后台进程 PID
        ├── instincts/
        │   ├── personal/            #   项目级本能
        │   └── inherited/           #   导入的本能
        └── evolved/                 #   项目级进化产物
            ├── skills/
            ├── commands/
            └── agents/
```

---

## 所有命令速查

| 命令 | 作用 |
|------|------|
| `/instinct-status` | 查看所有本能，按领域分组，带置信度进度条 |
| `/instinct-import <file\|url>` | 导入别人的本能 |
| `/instinct-export` | 导出自己的本能 |
| `/evolve` | 分析本能，建议聚合成 Skill/Command/Agent |
| `/evolve --generate` | 实际生成进化产物文件 |
| `/learn` | 中途手动触发模式提取 |
| `/learn-eval` | 评估并持久化学习到的模式 |
| `promote [id]` | 把项目级本能晋升为全局 |
| `projects` | 列出所有已知项目和本能数量 |

---

## 安全机制

| 保护 | 实现方式 |
|------|----------|
| **ID 注入防护** | 只允许 `^[A-Za-z0-9][A-Za-z0-9._-]*$`，最长 128 字符 |
| **路径穿越防护** | 禁止 `..`、`/`、`\`、前导 `.` |
| **系统目录保护** | 禁止写入 /etc、/usr、/bin、/proc 等 |
| **秘密脱敏** | 自动检测并替换 API key、token、password |
| **输入截断** | 观察记录中 input/output 各限 5000 字符 |

---

## 与 Evolver 的深度对比

| 维度 | Evolver (OpenClaw) | Instinct (Claude Code) |
|------|-------------------|----------------------|
| **知识粒度** | Gene（策略模板）+ Capsule（成功记录） | Instinct（原子行为）→ 进化为 Skill |
| **数据格式** | 严格 JSON Schema（5 个对象） | YAML + Markdown（灵活） |
| **分析引擎** | 自带信号提取 + 基因选择算法 | 外部 Haiku 模型分析 |
| **置信度机制** | Capsule confidence + success_streak | 0.3-0.9 连续评分 + 衰减 |
| **进化方式** | LLM 输出新 Gene（协议约束） | /evolve 聚类 → 生成 Skill |
| **项目隔离** | Session Scope（可选） | 默认按项目哈希隔离 |
| **跨项目晋升** | 无（全局 or 本地） | 2+ 项目出现 + 置信度 ≥0.8 自动晋升 |
| **共享范围** | EvoMap 全球网络 | export/import 文件或 Git |
| **安全保护** | Gene 验证命令白名单 + HMAC 签名 | ID/路径验证 + 秘密脱敏 |
| **依赖** | 零依赖 Node.js | Python3 + Claude Haiku |
| **成熟度** | 协议严格，生产级 | 灵活实用，社区驱动 |

### 各有所长

- **Evolver 胜在**：协议约束严格、完全可审计、零依赖、全球共享网络
- **Instinct 胜在**：项目隔离更自然、晋升机制更优雅、上手更简单、与 Claude Code 原生集成

---

## 配置文件

`skills/continuous-learning-v2/config.json`：

```json
{
  "version": "2.1",
  "observer": {
    "enabled": false,
    "run_interval_minutes": 5,
    "min_observations_to_analyze": 20
  }
}
```

注意：`observer.enabled` 默认是 `false`，需要手动开启。

---

## 安装方式

```bash
# 克隆项目
git clone https://github.com/affaan-m/everything-claude-code.git ~/.claude/plugins/everything-claude-code

# 或只安装 continuous-learning-v2 skill
# 复制 skills/continuous-learning-v2/ 到 ~/.claude/skills/
```

---

*基于 everything-claude-code 项目 continuous-learning-v2 (v2.1) 版本源码分析。*
