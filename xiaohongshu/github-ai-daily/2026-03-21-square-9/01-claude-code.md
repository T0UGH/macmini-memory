## anthropics/claude-code
**claude-code v2.1.81**

发布时间：2026-03-21 06:24

这版不是 flashy 新能力，而是在补 Claude Code 作为工程工具的执行链路：MCP 交互、hook 节点、会话命名和大仓库 worktree 都更完整了。

- 本次 release 主要围绕 CLI、MCP、hook 和 worktree 的可编排性展开，方向是把 Claude Code 做得更像可控的工程系统。
- Added --bare flag for scripted -p calls — skips hooks, LSP, plugin sync, and skill directory walks; requires ANTHROPIC_API_KEY or an apiKeyHelper via --settings (OAuth and keychain auth disabled); auto-memory fully disabled
- Added --channels permission relay — channel servers that declare the permission capability can forward tool approval prompts to your phone
- Fixed multiple concurrent Claude Code sessions requiring repeated re-authentication when one session refreshes its OAuth token
- Fixed voice mode silently swallowing retry failures and showing a misleading "check your network" message instead of the actual error

**一句话**
本次 release 主要围绕 CLI、MCP、hook 和 worktree 的可编排性展开，方向是把 Claude Code 做得更像可控的工程系统。
