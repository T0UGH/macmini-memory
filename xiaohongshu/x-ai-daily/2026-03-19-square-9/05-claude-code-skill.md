## Claude Code skill 支持 `!` 命令注入动态内容：技能不再只能吃静态说明书

> Claude Code runs it when the skill is invoked and swaps the placeholder inline, the model only sees the result!

### 我的判断
这是很实用但也很容易被低估的工作流升级。它把 skill 从“文档化提示词”推进到“可在调用时动态取数的能力包”。但另一面也很明显：一旦大家开始把 shell 注入到 skill 里，**可预测性、安全边界、幂等性** 会马上变成设计重点。

### 为什么值得看
贵平很在意规则、配置、验证、可复用流程。这个能力正好处在那条线上：skill 终于能少一点死文档，多一点实时上下文，但也更需要工程化约束。

**建议动作：建议细看**

**必看指数：★★★★☆**

### 一句话结论
**建议细看。**
