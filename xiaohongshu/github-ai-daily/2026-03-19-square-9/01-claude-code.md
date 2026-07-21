## anthropics/claude-code
**claude-code v2.1.79**

发布时间：2026-03-19 06:29

这版不是 flashy 新能力，而是在补 Claude Code 作为工程工具的执行链路：MCP 交互、hook 节点、会话命名和大仓库 worktree 都更完整了。

- 本次 release 主要围绕 CLI、MCP、hook 和 worktree 的可编排性展开，方向是把 Claude Code 做得更像可控的工程系统。
- Added --console flag to claude auth login for Anthropic Console (API billing) authentication
- Added "Show turn duration" toggle to the /config menu
- Fixed claude -p hanging when spawned as a subprocess without explicit stdin (e.g. Python subprocess.run)
- Fixed Ctrl+C not working in -p (print) mode

**一句话**
本次 release 主要围绕 CLI、MCP、hook 和 worktree 的可编排性展开，方向是把 Claude Code 做得更像可控的工程系统。
