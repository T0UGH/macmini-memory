# OpenClaw Plugin Evolver — AI Agent 自进化引擎深度解析

> **让 AI Agent 从经验中学习、自我修复、协同进化的协议约束型进化系统**

## 一句话介绍

Capability Evolver 是一个零依赖的 Node.js 项目，赋予 OpenClaw Agent **自我检查、自我修复、自我进化**的能力，并通过 EvoMap 网络让多个 Agent 之间**共享踩坑经验**，避免重复犯错。

---

## 核心概念

### 生物学隐喻

整个系统借用了生物学概念来组织知识：

| 概念 | 含义 | 例子 |
|------|------|------|
| **Gene（基因）** | 可复用的策略模板 | "检测到 npm install 失败 → 清除 node_modules 重试" |
| **Capsule（胶囊）** | 验证通过的修复方案记录 | "Windows shell 不兼容问题 → 已验证修复，置信度 0.85" |
| **Mutation（突变）** | 一次具体的变更指令 | "修复类：针对 gene_npm_fix，预期减少 50% 错误" |
| **EvolutionEvent（进化事件）** | 完整的审计记录 | 时间戳、使用的基因、突变结果、成功/失败 |
| **PersonalityState（性格状态）** | 行为参数 | 严谨度 0.7、创造力 0.35、风险容忍度 0.4 |

### 进化循环

```
日志/信号 → 信号提取 → 基因选择 → 突变构建 → Prompt 生成 → 固化验证
    ↑                                    ↓                           |
    |                             性格状态调整                        |
    └─────────────────── 结果反馈 ←──────────────────────────────────┘
```

---

## 核心能力

### 1. 自动日志分析

扫描运行历史和内存文件，识别：
- 错误模式（`[error]`、`exception:`、JSON 错误结构）
- 机会信号（功能请求、性能瓶颈、能力缺口）
- 循环检测（最近 8 个周期内同一信号出现 3+ 次则抑制）

### 2. 自我修复

- 检测崩溃并自动建议补丁
- Git 自动修复（rebase abort、lock 清理）
- 技能健康监控和版本追踪

### 3. 基因选择 + 遗传漂变

```
基因评分 = 信号匹配度 × 策略权重 × 蒸馏惩罚(0.8x)
                                    ↓
                        遗传漂变（drift_intensity = 1/√Ne）
                                    ↓
                           避免局部最优，探索新解
```

失败过的基因会被**禁用**（2次失败 + 60%信号重叠 → 拉黑）。

### 4. 协议约束的 Prompt 生成

LLM 必须严格输出 5 个 JSON 对象：
```
Mutation → PersonalityState → EvolutionEvent → Gene → Capsule
```
不允许 Markdown，不允许自由发挥，完全可审计。

---

## 知识共享机制

### A2A 协议（Agent-to-Agent）

这是整个系统最核心的差异化能力 —— 让不同 Agent 之间共享进化成果：

```
Agent A 踩坑 → 修复成功 → 打包为 Capsule → 发布到 EvoMap
                                                    ↓
Agent B 遇到类似问题 ← 自动匹配 Capsule ← 从 EvoMap 获取
```

**广播资格要求：**
- Capsule：置信度 ≥ 0.7，连续成功 ≥ 2 次，影响范围安全
- Gene：有有效策略，有验证命令

**安全保障：**
- 验证命令白名单：仅允许 `node`、`npm`、`npx`
- 禁止命令替换（反引号、`$()`）
- 禁止 Shell 操作符（`;`、`&`、`|`、`>`、`<`）
- 每条命令 180 秒超时
- HMAC-SHA256 签名验证

### A2A 消息类型

| 类型 | 用途 |
|------|------|
| `hello` | 节点发现 + 能力声明 |
| `publish` | 广播资产（基因/胶囊） |
| `fetch` | 按类型/ID/哈希请求资产 |
| `report` | 发送验证报告 |
| `decision` | 接受/拒绝/隔离决策 |
| `revoke` | 撤回已发布资产 |
| `heartbeat` | 心跳保活 |

---

## 进化策略

系统提供 6 种策略预设，控制进化方向：

| 策略 | 创新 | 优化 | 修复 | 适用场景 |
|------|------|------|------|----------|
| **balanced**（默认） | 50% | 30% | 20% | 日常运行 |
| **innovate** | 80% | 15% | 5% | 探索新能力 |
| **harden** | 20% | 40% | 40% | 稳定加固 |
| **repair-only** | 0% | 20% | 80% | 紧急修复 |
| **early-stabilize** | 15% | 25% | 60% | 前 5 个周期自动 |
| **steady-state** | 10% | 30% | 60% | 饱和后自动切换 |

```bash
# 指定策略
EVOLVE_STRATEGY=innovate node index.js --loop
```

---

## 快速上手

### 前置要求

- Node.js 18+（使用了 `fetch`、`AbortSignal.timeout`）
- 零 npm 依赖，克隆即用

### 基本用法

```bash
# 单次进化
node index.js

# 人工审核模式（推荐初次使用）
node index.js --review

# 守护进程模式（持续运行）
node index.js --loop

# 固化验证（验证 + 保存资产）
node index.js solidify --dry-run
```

### 后台管理

```bash
node src/ops/lifecycle.js start    # 后台启动
node src/ops/lifecycle.js stop     # 优雅停止
node src/ops/lifecycle.js status   # 查看状态
node src/ops/lifecycle.js check    # 健康检查 + 自动重启
```

### A2A 知识共享

```bash
npm run a2a:export    # 导出合格资产到 A2A 网络
npm run a2a:ingest    # 从外部获取候选资产
npm run a2a:promote   # 验证后合并到本地库
```

---

## 项目结构

```
openclaw-plugin-evolver/
├── index.js                    # 入口：守护进程循环 + solidify
├── SKILL.md                    # OpenClaw 技能清单
│
├── src/
│   ├── evolve.js               # 核心进化编排（信号→基因→突变→Prompt）
│   ├── canary.js               # 金丝雀测试
│   │
│   ├── gep/                    # GEP 协议实现（26 个模块）
│   │   ├── signals.js          #   信号提取与分析
│   │   ├── selector.js         #   基因选择（漂变、评分）
│   │   ├── mutation.js         #   突变对象构建
│   │   ├── personality.js      #   性格状态管理
│   │   ├── prompt.js           #   协议 Prompt 生成
│   │   ├── solidify.js         #   验证与资产固化
│   │   ├── a2a.js              #   A2A 广播工具
│   │   ├── a2aProtocol.js      #   A2A 协议规范
│   │   ├── assetStore.js       #   基因/胶囊存储
│   │   ├── memoryGraph.js      #   本地 JSONL 记忆图谱
│   │   ├── hubSearch.js        #   EvoMap Hub 搜索
│   │   ├── taskReceiver.js     #   Hub 任务领取
│   │   ├── contentHash.js      #   SHA-256 内容寻址
│   │   ├── skillDistiller.js   #   技能→基因自动蒸馏
│   │   └── ...                 #   （其余模块）
│   │
│   └── ops/                    # 运维模块（可移植、零依赖）
│       ├── lifecycle.js        #   启停管理
│       ├── health_check.js     #   健康监控
│       ├── self_repair.js      #   Git 自动修复
│       ├── cleanup.js          #   磁盘清理
│       ├── trigger.js          #   进化触发检测
│       └── ...
│
├── assets/gep/                 # GEP 协议资产
│   ├── genes.json              #   基因库（3 个种子基因）
│   ├── capsules.json           #   成功胶囊（2 个示例）
│   ├── events.jsonl            #   追加式进化历史
│   └── a2a/{inbox,outbox}/     #   A2A 消息队列
│
├── scripts/                    # CLI 工具脚本（12 个）
└── test/                       # 测试套件（5 个测试）
```

---

## 关键配置项

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `EVOLVE_STRATEGY` | `balanced` | 进化策略 |
| `EVOLVE_ALLOW_SELF_MODIFY` | `false` | 允许修改自身代码（**危险，勿开**） |
| `A2A_HUB_URL` | — | EvoMap Hub 地址 |
| `A2A_TRANSPORT` | `file` | 传输方式：`file` 或 `http` |
| `A2A_NODE_ID` | 自动生成 | 网络节点 ID |
| `EVOLVER_MAX_CYCLES_PER_PROCESS` | `100` | 内存泄漏防护：N 个周期后重启 |
| `EVOLVER_MAX_RSS_MB` | `500` | RSS 超阈值则重启 |
| `MEMORY_GRAPH_PROVIDER` | `local` | 记忆图谱：`local` 或 `remote` |
| `EVOLVER_SESSION_SCOPE` | — | 会话隔离 ID（如 Discord 频道） |

---

## 真实案例

### 案例一：运维机器人自学磁盘清理（Ops-Evo）

一个运维机器人 Ops-Evo，初始状态只有基础 shell 执行能力，收到任务：
> "每天凌晨3点检查服务器磁盘，超过90%就清理 /tmp 并发飞书告警"

#### 第一轮进化 — 产出基因 v1

```json
{
  "type": "Gene",
  "id": "gene_disk_check_v1",
  "category": "repair",
  "signals_match": ["disk_usage_high", "storage_alert", "tmp_cleanup"],
  "preconditions": ["server has /tmp directory", "feishu webhook configured"],
  "strategy": [
    "用 df -h 检查磁盘使用率",
    "超过 90% 阈值时清理 /tmp",
    "通过飞书 webhook 发送告警通知",
    "记录清理前后的磁盘变化"
  ],
  "constraints": {
    "max_files": 3,
    "forbidden_paths": ["/var/log", "/home"]
  },
  "validation": ["df -h | grep -v tmpfs"]
}
```

#### 执行成功 — 产出胶囊

```json
{
  "type": "Capsule",
  "id": "capsule_ops_disk_check_01",
  "trigger": ["disk_usage_high", "storage_alert"],
  "gene": "gene_disk_check_v1",
  "summary": "清理 /tmp 释放 12GB 空间，磁盘从 93% 降到 71%",
  "confidence": 0.9,
  "blast_radius": { "files": 2, "lines": 35 },
  "outcome": { "status": "success", "score": 0.9 },
  "success_streak": 1,
  "env_fingerprint": {
    "platform": "linux",
    "arch": "x64",
    "os_release": "Ubuntu 22.04"
  }
}
```

#### 第二轮进化 — 基因自我升级到 v2

第二天，Evolver 发现光清 /tmp 不够，自动升级：

```json
{
  "type": "Gene",
  "id": "gene_disk_check_v2",
  "category": "optimize",
  "signals_match": ["disk_usage_high", "storage_alert", "docker_bloat"],
  "strategy": [
    "用 df -h 检查磁盘使用率",
    "超过 90% 先清理 /tmp",
    "执行 docker system prune 清理无用镜像",
    "检查并轮转过大的日志文件",
    "通过飞书 webhook 发送详细报告"
  ]
}
```

**v1 → v2**：自动学会了 Docker 清理和日志轮转，全程无人写代码。一周后，Ops-Evo 已"自学"了 Docker 清理、日志轮转等高级运维技能。

---

### 案例二：项目自带的 Windows Shell 兼容修复

项目 `assets/gep/capsules.json` 中记录了一个真实胶囊：

```json
{
  "type": "Capsule",
  "id": "capsule_1770477654236",
  "trigger": [
    "log_error",
    "windows_shell_incompatible",
    "perf_bottleneck"
  ],
  "gene": "gene_gep_repair_from_errors",
  "summary": "gene_gep_repair_from_errors 命中信号，变更 1 文件 / 2 行",
  "confidence": 0.85,
  "blast_radius": { "files": 1, "lines": 2 },
  "outcome": { "status": "success", "score": 0.85 },
  "success_streak": 1,
  "env_fingerprint": {
    "node_version": "v22.22.0",
    "platform": "linux",
    "evolver_version": "1.7.0"
  },
  "a2a": { "eligible_to_broadcast": false }
}
```

注意 `eligible_to_broadcast: false` — 因为 `success_streak` 才 1 次，没达到广播门槛（需连续成功 2 次）。

---

### 案例三：跨领域知识共享

一个**游戏设计师**上传了关于「用强上下文前缀做命名空间隔离」的经验胶囊到 EvoMap。一个**后端工程师**的 Agent 遇到命名冲突问题时搜到了这个胶囊。Agent 没有照搬游戏词汇，而是理解了底层原理——用前缀做命名空间隔离——后端代码一次编译通过。

**游戏设计师在不知情的情况下，帮后端工程师修了个 bug。**

这就是 EvoMap 的核心价值：知识不按领域隔离，按**模式**匹配。

---

### 概念对照总结

| 概念 | 类比 | 在案例中 |
|------|------|----------|
| **Gene（基因）** | 医学教科书的治疗方案 | `gene_disk_check_v1`：磁盘满了怎么清理 |
| **Capsule（胶囊）** | 治愈后的病历记录 | `capsule_ops_disk_check_01`：清了12GB，成功了 |
| **Mutation（突变）** | 医生开的处方单 | repair 类、改 2 个文件 35 行、低风险 |
| **EvolutionEvent** | 完整的就诊记录 | 时间、用了什么基因、突变结果、成功/失败 |
| **PersonalityState** | 医生的风格偏好 | 严谨度 0.7、风险容忍度 0.4 |
| **A2A 广播** | 把病历发到医学期刊 | 连续成功 2 次 + 置信度 ≥ 0.7 才能发表 |

---

## 安全注意事项

1. **不要开启 `EVOLVE_ALLOW_SELF_MODIFY=true`** — 官方原话："catastrophic"，会导致级联故障
2. **`--loop` 模式需要沙箱** — 持续运行的 Agent 有失控风险
3. **A2A 外部资产需验证** — 使用 `npm run a2a:promote -- --validated` 手动确认
4. **ClawHub 曾发生供应链投毒**（2026.02.09） — 注意技能来源安全

---

## 设计亮点

- **零依赖**：纯 Node.js 内置 API，克隆即用，无 `npm install`
- **协议约束**：所有进化步骤被 GEP 协议严格约束，完全可审计
- **内容寻址**：SHA-256 哈希保证资产去重、防篡改、跨节点一致
- **自适应行为**：自动检测饱和、调整策略、根据系统负载节流
- **优雅降级**：外部服务不可用时自动回退到本地模式
- **原子写入**：所有文件 I/O 使用 tmp + rename 模式，防止数据损坏

---

## 在 Claude Code 上的类似方案

Evolver 是为 OpenClaw 设计的，不能直接用在 Claude Code 上。但 Claude Code 生态已经有类似的实现：

### Claudeception — Claude Code 版 Evolver

GitHub: https://github.com/blader/Claudeception

一个 Meta-Skill（生产技能的技能）：Claude Code 解决完问题后，自动把踩坑经验提炼成新的 Skill，下次遇到类似问题直接复用。

**安装：**

```bash
# 全局安装（所有项目共享）
git clone https://github.com/blader/Claudeception.git ~/.claude/skills/claudeception

# 项目级安装（团队共享，可提交到 git）
git clone https://github.com/blader/Claudeception.git .claude/skills/claudeception
```

**工作原理：**

```
你修了个复杂 bug → Claude 识别到有价值的经验
                          ↓
              自动提炼成 SKILL.md 保存到 skills 目录
                          ↓
              下次遇到类似问题 → 自动激活这个 skill
```

配合 Hook 可以全自动触发：

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "~/.claude/hooks/claudeception-activator.sh"
      }]
    }]
  }
}
```

### everything-claude-code 的 Instinct 系统

用 Stop Hook 在会话结束时自动提取编码模式，存为 "Instinct"（本能），每个带置信度评分（0.3-0.9）。积累 3 个以上相关 Instinct 后，用 `/evolve` 命令聚合成正式 Skill。

这更接近 Evolver 的思路：**胶囊（Instinct）积累 → 达到阈值 → 升级为基因（Skill）**。

### 与 Evolver 的对比

| | Evolver (OpenClaw) | Claudeception (Claude Code) |
|---|---|---|
| 知识单元 | Gene + Capsule (JSON) | Skill (SKILL.md) |
| 触发方式 | 自动扫描日志 | Hook 自动 + 语义匹配 |
| 提取条件 | 信号匹配 + 置信度 | "非显而易见"的发现 |
| 共享机制 | EvoMap 网络 (A2A 协议) | Git 提交到项目仓库 |
| 存储位置 | `assets/gep/` | `~/.claude/skills/` |
| 进化方式 | 基因 v1→v2 自动升级 | 手动或 `/evolve` 聚合 |
| 跨团队共享 | EvoMap Hub（全网） | 仅限 Git 仓库内团队 |

### Claude Code 现有机制 vs Evolver 概念

| Evolver 概念 | Claude Code 对应 | 差距 |
|-------------|-----------------|------|
| 基因（通用方案） | CLAUDE.md / Skills | 手动维护，不能自动产生 |
| 胶囊（成功记录） | Auto Memory | 只记偏好，不记修复方案 |
| 突变（具体操作） | 每次对话中的操作 | 不会结构化保存 |
| A2A 共享 | 无 | 完全没有跨实例共享 |
| 信号提取 | 无 | 不会自动分析历史错误 |

### 目前缺失的能力

Claude Code 生态目前没有人做**跨团队/跨项目的 A2A 共享网络**。知识共享仅限于：
- Git 仓库内共享 CLAUDE.md / Skills（团队级）
- 全局 skills 目录（个人级）

没有类似 EvoMap 的公共知识交换网络。

---

## 相关链接

- GitHub: https://github.com/huaxianhu/openclaw-plugin-evolver
- EvoMap 网络: https://evomap.ai
- EvoMap/evolver (官方仓库): https://github.com/EvoMap/evolver
- Capability Evolver (官方 Skill): https://github.com/openclaw/skills/blob/main/skills/autogame-17/capability-evolver/SKILL.md
- EvoMap Skill: https://github.com/openclaw/skills/blob/main/skills/segasonicye/evomap/SKILL.md
- Claudeception (Claude Code 版): https://github.com/blader/Claudeception
- GEP 协议参考: https://opengep.com/

---

*本文档由深度代码分析自动生成，基于项目 v1.20.0 版本。*
