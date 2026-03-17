# 信号 4：真正值得跟的，是这些配套层

这两天还有两个工具很典型：

## GitNexus
它在做的是：
把整个 repo 转成 knowledge graph，再通过 MCP 喂给 Claude Code / Cursor。

这说明什么？
说明大家已经意识到，agent 真正难的不是“会写几行代码”，
而是：
**能不能理解整个仓库。**

## skillgrade
它做的是：
给 agent skills 跑 eval，而且默认在沙箱里执行。

这又说明什么？
说明 agent 生态开始把“技能评测”“可靠性验证”单独工具化。

## 所以今天最值得跟的不是单个炫技产品
而是三类配套能力：
1. repo understanding
2. skill / workflow eval
3. MCP / context infrastructure
