## skillgrade：agent skills 的评测开始被工具化、沙箱化

Minko Gechev 这条更新里最值得看的，是 **skillgrade** 试图把 agent skills 的评测这件事，做成一个明确工具。  
从原文看，它的入口很轻：用 `skillgrade init` 和 `skillgrade` 两条命令就能建立并运行评测；同时默认在 **sandboxed Docker container** 里执行。

这背后其实有两个很实在的点：

- 一是 agent skills 不再只停留在“写出来就算有了”
- 二是评测过程开始强调安全隔离和可重复执行

这类工具的重要性，恰恰在于它补的是 agent 生态一直偏弱的一块：  
大家都在做 skills、hooks、工作流、命令集合，但真正系统化验证的并不多。

而只要评测不能标准化，后面很多“这个 skill 很强”“这个 agent 很稳”的说法，其实都很难验证。  
skillgrade 这种工具化动作，说明可靠性开始从概念往流程迁移。

### 为什么值得看
因为 agent 生态迟早要进入“谁评测更硬，谁更可信”的阶段。skillgrade 这类工具，正是在提前补这块基础设施。

### 必看指数
**必看指数：★★★★☆**

### 一句话结论
**skillgrade 值得看的地方，是它把 agent skills 的 eval 从口头概念往可执行流程推进了一步。**
