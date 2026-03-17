## openai/codex
**codex rust-v0.115.0**

发布时间：2026-03-17 03:37

- 这版 Codex 值得看的不是单点功能，而是把多 agent、审批、sandbox、filesystem RPC 和 app-server / realtime 这些基础能力继续往前推了一截。
- Smart Approvals 现在可以把 review 请求路由给 guardian subagent，说明 Codex 正在把审批与审稿链路做成一等能力。
- app-server v2 新增 filesystem RPC，并补了 Python SDK；这条线对外部集成、宿主应用接入和工作流编排都更关键。
- Realtime websocket 会话新增专用 transcription mode，并通过 `codex` tool 支持 v2 handoff，实时交互链路继续增强。
- 修复 spawned subagents 继承 sandbox / network 规则不稳定的问题，也修了 `codex exec --profile`、MCP 工具调用、TUI 退出卡住等真实使用痛点。

**一句话**
这版 Codex 值得看的不是单点功能，而是把多 agent、审批、sandbox、filesystem RPC 和 app-server / realtime 这些基础能力继续往前推了一截。
