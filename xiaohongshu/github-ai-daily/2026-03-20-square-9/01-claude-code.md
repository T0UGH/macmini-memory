## anthropics/claude-code
**claude-code v2.1.80**

发布时间：2026-03-20 06:08

这版不是 flashy 新能力，而是在补 Claude Code 作为工程工具的执行链路：MCP 交互、hook 节点、会话命名和大仓库 worktree 都更完整了。

- 本次 release 主要围绕 CLI、MCP、hook 和 worktree 的可编排性展开，方向是把 Claude Code 做得更像可控的工程系统。
- Added rate_limits field to statusline scripts for displaying Claude.ai rate limit usage (5-hour and 7-day windows with used_percentage and resets_at)
- Added source: 'settings' plugin marketplace source — declare plugin entries inline in settings.json
- Added CLI tool usage detection to plugin tips, in addition to file pattern matching
- Added effort frontmatter support for skills and slash commands to override the model effort level when invoked

**一句话**
本次 release 主要围绕 CLI、MCP、hook 和 worktree 的可编排性展开，方向是把 Claude Code 做得更像可控的工程系统。
