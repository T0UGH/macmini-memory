## openai/codex
**Codex rust-v0.115.0**

发布时间：2026-03-17 03:37

这版 Codex 值得看的不是单点功能，而是底座能力继续往前推进。

- Smart Approvals 能把 review 请求路由给 guardian subagent
- app-server v2 新增 filesystem RPC，并补了 Python SDK
- realtime websocket 会话新增 transcription mode
- `codex` tool 支持 v2 handoff
- subagent 的 sandbox / network 规则继承更稳了
- 还补了 `codex exec --profile`、MCP、TUI 退出卡住等问题

**一句话**
Codex 的方向不是“更像聊天”，而是“更像可编排、可嵌入的编码代理底座”。

---
