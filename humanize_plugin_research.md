# Humanize Plugin 深度研究报告

> 日期: 2026-03-08 | GitHub: humania-org/humanize | 版本: v1.14.0 | License: MIT

## 项目概述

Humanize 是一个 Claude Code 插件，通过 **Claude（实现）+ Codex（独立审查）** 的双模型迭代循环来保证 AI 生成代码的质量。核心理念："LLM IS AS GOOD AS YOU ARE" — 迭代优于完美。

- **Stars**: 146 | **核心作者**: Sihao Liu (UCLA, 87 commits)
- **技术栈**: Shell 脚本 (~11,250 行) + 60+ 提示模板
- **依赖**: Claude Code + Codex CLI + jq + Git
- **默认审查模型**: gpt-5.4

---

## 核心架构: RLCR 循环 (Ralph-Loop with Codex Review)

### 两阶段 + 终结

```
实现阶段: Claude 实现 → 写总结 → Codex 评审 → 反馈 → Claude 修复 → 循环
审查阶段: codex review --base <branch> → [P0-9] 标记 → Claude 修复
终结阶段: code-simplifier Agent 简化代码
```

### 关键创新: Stop Hook 门控

Claude 试图退出时, `loop-codex-stop-hook.sh` (1681 行) 拦截:
- 读取 Claude 的工作总结
- 调用 Codex 独立评审
- Codex 输出 `COMPLETE` → 允许退出; 有问题 → 阻止退出 (exit 10)
- 检测停滞 (`STOP`) → 电路断路器, 请求人工干预

### 状态管理

```
.humanize/rlcr/<timestamp>/
├── state.md              # YAML frontmatter: round, max, model, branch...
├── goal-tracker.md       # IMMUTABLE: 目标+AC | MUTABLE: 任务进度
├── round-N-prompt.md     # 给 Claude 的提示
├── round-N-summary.md    # Claude 的工作总结
├── round-N-review-*.md   # Codex 的评审提示和结果
└── finalize-*.md         # 终结阶段文件
```

---

## 命令和技能

| 命令 | 功能 | 关键参数 |
|------|------|----------|
| `/humanize:start-rlcr-loop` | 启动迭代开发循环 | `--plan-file`, `--max 42`, `--agent-teams` |
| `/humanize:gen-plan` | 草稿 → 结构化计划 | 6阶段: IO验证→相关性→分析→澄清→生成→复审 |
| `/humanize:start-pr-loop` | GitHub PR 审查循环 | `--claude`, `--codex`, 轮询 Bot 评审 |
| `/humanize:ask-codex` | 单次 Codex 咨询 | 设计评审、专业建议 |
| `/humanize:cancel-*` | 取消循环 | |

---

## Hook 系统 (11 个 Hook, ~4500 行)

### Hook 生命周期

```
[UserPromptSubmit] → 计划文件验证
[PreToolUse] → Write/Edit/Read/Bash 验证 (防止修改 state.md, goal-tracker 等)
[PostToolUse] → Bash 后处理 (未推送提交检查)
[Stop] → loop-codex-stop-hook / pr-loop-stop-hook (超时 7200s)
```

### 验证策略 (防止 Claude "作弊")
- 禁止直接写入 todos 文件
- 禁止修改 prompt 文件和 state.md
- Round 0 后 goal-tracker IMMUTABLE 部分只读
- 检查 git 状态干净、强制推送、大文件

---

## 提示模板系统 (60+ 模板)

```
prompt-template/
├── plan/          # 计划生成模板 (TDD 风格, AC 驱动)
├── claude/        # 实现/审查/终结阶段提示 (11个)
├── codex/         # Codex 评审提示: regular, full-alignment, code-review (4个)
├── pr-loop/       # PR 循环提示 (7个)
└── block/         # 阻止消息 (30+): git-not-clean, work-summary-missing, ...
```

**模板变量**: `{{PLAN_FILE}}`, `{{CURRENT_ROUND}}`, `{{SUMMARY_CONTENT}}` 等
**加载器**: `hooks/lib/template-loader.sh`

---

## 质量保障机制

### 1. 全对齐检查 (Full Alignment Review)
- 每 N 轮一次 (默认 5, 可配置 `--full-review-round`)
- 综合审查所有 AC 进度
- 检测停滞迹象 (多轮同样问题, 无进展, 循环讨论)

### 2. 电路断路器 (Stagnation Detection)
- Codex 在评审结果最后一行输出 `STOP`
- Hook 阻止继续, 报告停滞, 请求人工干预

### 3. 目标追踪不可变性
- Round 0 后 IMMUTABLE SECTION (Ultimate Goal, AC) 不可修改
- 防止目标漂移, 强制显式的计划演变

---

## Agent 系统

### 专用 Agent (2个)
- **draft-relevance-checker** (Haiku): 检查草稿是否与仓库相关
- **plan-compliance-checker** (Sonnet): 验证计划合规性, 检查分支切换

### Agent Teams 模式
- 需要 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- Claude 作为协调者, 不直接写代码
- 多个 Agent 并行处理, 严格文件所有权防止冲突

---

## PR 循环流程

```
初始化 → 检测当前分支 PR → 等待 Bot 自动评审
  ↓
Stop Hook: 获取 PR 评论 → 本地 Codex 验证 → 解析
  ↓
如有问题: Claude 修复 → push → @bot 触发重审 → 轮询 (30s/次, 15min/Bot)
如全部批准: 完成
```

**支持的 Bot**: `claude[bot]`, `chatgpt-codex-connector[bot]`

---

## 关键文件路径速查

| 文件 | 行数 | 用途 |
|------|------|------|
| `scripts/setup-rlcr-loop.sh` | 1190 | RLCR 循环初始化 |
| `hooks/loop-codex-stop-hook.sh` | 1681 | 核心: RLCR 停止门控 |
| `hooks/pr-loop-stop-hook.sh` | 1646 | PR 循环停止门控 |
| `scripts/humanize.sh` | 1590 | 监控仪表板 |
| `scripts/setup-pr-loop.sh` | 945 | PR 循环初始化 |
| `scripts/ask-codex.sh` | 410 | Codex 咨询 |
| `hooks/lib/loop-common.sh` | ~500 | 共用函数库 |
| `hooks/hooks.json` | 80 | Hook 注册配置 |

---

## 计划模板结构 (TDD 风格)

```markdown
# 计划标题
## 目标描述
## 接受标准 (AC-1, AC-2, ...)
  - 正面测试 + 反面测试
## 路径边界 (上界/下界/允许选择)
## 可行性建议
## 依赖和顺序 (里程碑)
## 实现说明
```

**关键规则**: 代码中不能包含计划术语 ("AC-", "Milestone", "Step", "Phase")

---

## 配置

### Codex 默认值
- 模型: `gpt-5.4`
- Effort: `xhigh` (实现), `high` (代码审查), `medium` (PR)
- 超时: 5400s (RLCR), 900s (PR), 3600s (ask-codex)

### 项目规则 (.claude/CLAUDE.md)
- 全英文 (禁止 Emoji/CJK)
- 版本同步: plugin.json + marketplace.json + README.md
- 版本格式: X.Y.Z (仅数字)

---

## 评价

### 亮点
1. **Stop Hook 门控设计** — 强制独立评审, 防止 Claude 自称完成
2. **严密的验证系统** — 多层 Hook 防止绕过
3. **灵活的目标追踪** — 不可变核心 + 可变执行
4. **电路断路器** — 自动检测停滞
5. **详细日志** — 所有循环状态完整保留

### 局限性
1. 依赖 Codex CLI (需要 OpenAI API key)
2. 技术栈以 Shell 为主, 扩展性有限
3. 社区较小 (7 forks, 3 contributors)
4. 相对年轻 (2026年1月创建)

### 可借鉴的设计模式
- **Stop Hook 拦截模式**: 通过 Hook 控制 Agent 退出, 强制质量检查
- **双模型互审**: 实现者和审查者分离, 消除盲点
- **目标不可变性**: 防止 AI 执行过程中目标漂移
- **模板化提示管理**: 60+ 模板文件, 参数化渲染
