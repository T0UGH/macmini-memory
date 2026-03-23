## OpenAI 给 agent infra 补硬活：Responses API container pool 把冷启动提速约 10 倍

> We added a container pool to the Responses API, so requests can reuse warm infrastructure instead of creating a full container creation each session.

### 我的判断
这条非常工程化，但含金量极高。很多 agent workflow 不是模型不够强，而是每步都像在等 CI。容器冷启动如果真压到原来的十分之一，多步工具调用、拆分执行和技能化编排的体验会直接变一个档次。

### 为什么值得看
对 coding / automation 流程来说，冷启动时间决定了很多事情“值不值得拆成 agent steps”。OpenAI 这次是在动生产可用性的地基。

**建议动作：建议细看**

**必看指数：★★★★★**

### 一句话结论
**建议细看。**
