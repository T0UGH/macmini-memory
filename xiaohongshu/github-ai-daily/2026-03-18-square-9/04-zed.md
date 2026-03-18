## zed-industries/zed
**zed v0.227.1**

发布时间：2026-03-11 23:41

Zed 这版的重点是 agent workflow 成熟化：子代理、提供商接入、diff 跳转和线程持久化都在补。

- Zed Agent 新增 spawn_agent，开始显式支持并行子代理调度。
- OpenAI provider 补上 GPT-5.3-Codex 自带 Key 模式支持，Codex 接入门槛继续下降。
- 新增 Vercel AI Gateway 作为 LLM provider，意味着模型接入层继续扩张。
- agent 对话里可以直接从 diff 跳回文件，减少“看改动—回源码”之间的切换成本。
- 线程体验继续补：草稿提示词、思考模式和线程状态持久化更完整。

**一句话**
Zed Agent 新增 spawn_agent，开始显式支持并行子代理调度。
