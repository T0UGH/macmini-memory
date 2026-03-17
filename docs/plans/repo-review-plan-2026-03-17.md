# 仓库浏览计划（起始于 2026-03-17）

目标：控制信息摄入强度，每天只看 2-3 个仓库，但持续覆盖 Claude Code / OpenClaw / agents / coding workflow 生态。

## 执行规则
- 每天最多看 2-3 个仓库，不追求看完，只追求抓重点。
- 每天的组合尽量保持：
  1. **一个核心基础设施仓库**（Claude Code / OpenClaw / OpenCode / GitNexus / Serena 这类）
  2. **一个工作流或方法论仓库**（skills / hooks / commands / orchestrator）
  3. **一个发现型仓库**（awesome list / 新项目 / 候选实验项目，可选）
- 每次只回答 4 个问题：
  - 它解决什么问题？
  - 它的核心机制是什么？
  - 它对贵平当前工作流有没有直接价值？
  - 要不要继续跟踪 / clone / 写进日报候选？
- 看完后，把结论补到 `docs/research-log/YYYY-MM-DD.md`。

---

## 第 1 周安排

### Day 1（2026-03-17，今天）
1. `abhigyanpatwari/GitNexus`
   - 目的：理解 code graph / Graph RAG / MCP 增强的真实价值。
2. `hesreallyhim/awesome-claude-code`
   - 目的：把它当生态入口，看 trends，不当普通收藏夹。
3. `mgechev/skillgrade`
   - 目的：判断“skill 的测试/评分”是不是值得借鉴到 OpenClaw 或技能体系。

### Day 2（2026-03-18）
1. `anthropics/claude-code`
   - 目的：继续盯最高优先级核心产品变化。
2. `openclaw/openclaw`
   - 目的：盯你自己日常使用的 agent runtime / workflow 层变化。
3. `oraios/serena`
   - 目的：看代码理解/符号级导航这条线如何和 Claude Code 形成互补。

### Day 3（2026-03-19）
1. `sst/opencode`
   - 目的：比较 OpenCode 路线和 Claude Code / OpenClaw 的差异。
2. `penso/arbor`
   - 目的：看 agent 工作流/编排工具是否有实操价值。
3. `tintinweb/pi-subagents`
   - 目的：看 subagents 这条线有没有轻量实用做法。

### Day 4（2026-03-20）
1. `zed-industries/zed`
   - 目的：观察 Zed agent 侧的交互与能力更新。
2. `obra/superpowers`
   - 目的：看成熟技能包如何组织工程常见能力。
3. `K-Dense-AI/claude-scientific-skills`
   - 目的：看高质量 skill 仓库的写法和覆盖面。

### Day 5（2026-03-21）
1. `trailofbits/skills`
   - 目的：安全技能仓库，适合提炼“专业技能库”的标准。
2. `vaporif/parry`
   - 目的：关注 hook 层 prompt injection / 安全防护。
3. `ldayton/Dippy`
   - 目的：关注 auto-approve safe commands 这条非常关键的体验/安全平衡线。

### Day 6（2026-03-22）
1. `ryoppippi/ccusage`
   - 目的：看 Claude Code usage 可观测性方案。
2. `tombii/better-ccflare`
   - 目的：看 usage dashboard 的增强路线。
3. `zippoxer/recall`
   - 目的：看 session continuity / 检索这条线，和你的记忆需求有直接关系。

### Day 7（2026-03-23）
1. `sudocode-ai/sudocode`
   - 目的：看 repo 内 orchestrator 的轻量方案。
2. `dtormoen/tsk`
   - 目的：看 sandboxed agent task manager 的工程落地方式。
3. `andyMik90/Auto-Claude`
   - 目的：看多 agent SDLC 编排是不是实用还是过度包装。

---

## 第二梯队候选（后续轮换）
- `affaan-m/everything-claude-code`
- `EveryInc/compound-engineering-plugin`
- `dyoshikawa/rulesync`
- `nulone/claude-rules-doctor`
- `GWUDCAP/cc-sessions`
- `eckardt/cchistory`
- `pchalasani/claude-code-tools`
- `FlineDev/ContextKit`
- `claude-did-this/claude-hub`
- `ruvnet/claude-code-flow`
- `parruda/claude-swarm`
- `slopus/happy`

## 我建议的节奏
- **工作日**：优先“核心基础设施 + 工作流/安全”
- **周末**：优先“发现型仓库 + 方法论仓库”
- **每周日**：回顾本周看过的仓库，挑 3 个进入长期观察名单

## 长期观察名单（当前建议）
- `anthropics/claude-code`
- `openclaw/openclaw`
- `hesreallyhim/awesome-claude-code`
- `abhigyanpatwari/GitNexus`
- `oraios/serena`
- `trailofbits/skills`
- `vaporif/parry`
- `ldayton/Dippy`
