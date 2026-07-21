## OpenAI 给 agent 基础设施补硬活：Responses API 容器池把 skills/shell/code interpreter 启动提速约 10 倍

> We added a container pool to the Responses API, so requests can reuse warm infrastructure instead of creating a full container each session.

### 我的判断
这条比任何模型 headline 都更接近生产价值。大量 agent workflow 真正卡住的不是“模型不够聪明”，而是每个子任务都要起冷容器，导致交互像在等 CI。OpenAI 这次是在补 agent 落地最痛的基础设施延迟。

### 为什么值得看
对多步 coding / automation 流程来说，10 倍冷启动改进会改变很多工作流是否“值得拆成子任务”。以前嫌慢的技能化、子代理化、工具化调用，现在会更接近实时体验。

**建议动作：建议细看**

**必看指数：★★★★★**

### 一句话结论
**建议细看。**
