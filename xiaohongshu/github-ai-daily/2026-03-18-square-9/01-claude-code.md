## anthropics/claude-code
**claude-code v2.1.78**

发布时间：2026-03-18 07:42

这版不是 flashy 新能力，而是在补 Claude Code 作为工程工具的执行链路：MCP 交互、hook 节点、会话命名和大仓库 worktree 都更完整了。

- 本次 release 主要围绕 CLI、MCP、hook 和 worktree 的可编排性展开，方向是把 Claude Code 做得更像可控的工程系统。
- Added StopFailure hook event that fires when the turn ends due to an API error (rate limit, auth failure, etc.)
- Added ${CLAUDE_PLUGIN_DATA} variable for plugin persistent state that survives plugin updates; /plugin uninstall prompts before deleting it
- Added effort, maxTurns, and disallowedTools frontmatter support for plugin-shipped agents
- Terminal notifications (iTerm2/Kitty/Ghostty popups, progress bar) now reach the outer terminal when running inside tmux with set -g allow-passthrough on

**一句话**
本次 release 主要围绕 CLI、MCP、hook 和 worktree 的可编排性展开，方向是把 Claude Code 做得更像可控的工程系统。
