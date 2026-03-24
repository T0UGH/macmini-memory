## anthropics/claude-code
**claude-code v2.1.81**

发布时间：2026-03-21 06:24

这版不是 flashy 新能力，而是在补 Claude Code 作为工程工具的执行链路：MCP 交互、hook 节点、会话命名和大仓库 worktree 都更完整了。

**这次具体改了什么**
- 本次 release 主要围绕 CLI、MCP、hook 和 worktree 的可编排性展开，方向是把 Claude Code 做得更像可控的工程系统。

**这意味着什么**
- 如果你在用 Claude Code 跑多轮任务或大仓库，这版比“模型更聪明”更值得关注，因为它改的是工作流可用性。
- 更偏工程执行链路补强，不是表面功能加法。

**原始证据**
- Added --bare flag for scripted -p calls — skips hooks, LSP, plugin sync, and skill directory walks; requires ANTHROPIC_API_KEY or an apiKeyHelper via --settings (OAuth and keychain auth disabled); auto-memory fully disabled

**一句判断**
这版不是 flashy 新能力，而是在补 Claude Code 作为工程工具的执行链路：MCP 交互、hook 节点、会话命名和大仓库 worktree 都更完整了。
