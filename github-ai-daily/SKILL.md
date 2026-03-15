---
name: github-daily
description: 生成面向 coding agent 生态的 GitHub 中文日报。用户想看固定 5 个核心仓库（anthropics/claude-code、openclaw/openclaw、sst/opencode、zed-industries/zed、anthropics/claude-plugins-official）的更新，或想看 10 个新仓候选时使用。
---

在此目录运行 `scripts/run_github_daily.py`。

硬规则：
- 输出必须以中文为主，不要生成纯英文成品。
- 英文只能作为仓库名、链接或极少量原文引用出现。

行为：
- 抓取 4 个 release 驱动核心仓库的最新 release。
- 通过 `.claude-plugin/marketplace.json` 对比 `anthropics/claude-plugins-official`。
- 通过 GitHub 搜索生成 10 个 coding-agent 生态新仓候选。
- 结果写入 `runs/<timestamp>.md` 和 `runs/<timestamp>.json`。

输出约束：
- `anthropics/claude-code` 是最高优先级。
- Zed 只保留在核心观察里，不拿它做外扩新仓来源。
- discovery 保持在 coding-agent 生态范围内，不局限于 Claude Code。
- 优先短、密、中文化的高信号摘要。
