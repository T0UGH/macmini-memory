## Codex 支持 subagents：这次具体补了什么

这次 Codex 更新里，最值得注意的是对 **subagents** 的支持开始变得更明确了。  
如果只看表面，会觉得它只是多了一个“子代理”能力；但从原始更新内容看，它其实是在补一整套和多 agent 协作相关的基础链路。

这次更新里比较具体的点包括：

- **Smart Approvals** 现在可以把 review 请求路由给 **guardian subagent**
- app-server v2 新增了 **filesystem RPC**
- 同时补上了 **Python SDK**
- realtime websocket 会话里新增了专门的 **transcription mode**
- `codex` tool 开始支持 **v2 handoff**
- 还修了 spawned subagents 在 **sandbox / network 规则继承**上的稳定性问题

如果把这些点放在一起看，会发现它不是只补了一个“能不能开 subagent”的能力，  
而是在补“多 agent 真的跑起来之后，外围链路是否能接住”：

- review 怎么分发
- agent 之间怎么交接
- 外部应用怎么接
- 文件系统怎么暴露给上层
- sandbox 权限怎么跟着走
- 实时会话怎么承接新的交互模式

这才是这次更新真正值得看的地方。

### 为什么值得看
因为这说明 Codex 现在补的不是表面功能，而是**多 agent 工作方式真正落地所需要的基础设施**。  
也就是说，它开始往“可编排的编码代理底座”走，而不只是一个会聊天、会改代码的 agent。

### 必看指数
**必看指数：★★★★★**

### 一句话结论
**这次 Codex 真正推进的，不是一个孤立新功能，而是多 agent 协作背后的整条基础链路。**
