# Planning-with-Files Skill 分析

> Manus 风格的文件持久化规划 skill，用三个 Markdown 文件作为 Agent 的"磁盘工作记忆"

## 基本信息

- **名称**: planning-with-files
- **版本**: 2.10.0
- **作者**: Othman Adi
- **来源**: [playbooks.com](https://playbooks.com/skills/othmanadi/planning-with-files/planning-with-files) | [GitHub](https://github.com/openclaw/skills/blob/main/skills/othmanadi/planning-with-files/SKILL.md)

## 核心理念

```
Context Window = RAM（易失、有限）
Filesystem = Disk（持久、无限）
→ 重要信息必须写入磁盘
```

## 三文件模式

| 文件 | 用途 | 更新时机 |
|------|------|----------|
| `task_plan.md` | 阶段、进度、决策 | 每个阶段完成后 |
| `findings.md` | 调研发现 | 任何发现后 |
| `progress.md` | 会话日志、测试结果 | 贯穿整个会话 |

## Hooks 自动化

- **PreToolUse**: 每次工具调用前自动 `cat task_plan.md | head -30`，保持计划在注意力窗口
- **PostToolUse**: 写文件后提醒更新 plan 状态
- **Stop**: 会话结束时运行 `check-complete.sh` 检查所有阶段是否完成

## 关键规则

1. **Create Plan First** — 复杂任务必须先建 task_plan.md
2. **2-Action Rule** — 每 2 次工具调用后立即保存发现，防止多模态信息丢失
3. **Read Before Decide** — 重大决策前重读 plan 文件
4. **Log ALL Errors** — 所有错误记录到 plan 文件
5. **3-Strike Protocol** — 同一错误 3 次后升级给用户

## Session Recovery (v2.2.0)

新会话开始时运行 `session-catchup.py`，结合 `git diff` 恢复上下文。

## 与 superpowers:writing-plans 的关系

- **planning-with-files**: 侧重运行时持久化记忆（Manus 风格），解决 context window 易失问题
- **superpowers:writing-plans**: 侧重实现前的架构规划和方案设计
- 两者互补，可以组合使用
