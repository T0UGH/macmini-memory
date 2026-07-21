## GitNexus：开始有人把整仓库理解问题做成 knowledge graph + MCP

这条内容里最值得看的，不是又多了一个 AI 工具，而是 GitNexus 试图正面解决 coding agent 的一个老问题：**怎么让 agent 真正理解整个仓库，而不是只盯当前文件。**

它给出的路径很明确：

- 先把 repo 转成 **knowledge graph**
- 再通过 **MCP** 提供给 Claude Code、Cursor 这类 coding assistant
- 目标是让 agent 在做修改时，不只是看到一个局部片段，而是能拿到更完整的仓库结构信息

这件事的重要性在于，repo-level understanding 一直是 coding agent 很现实的瓶颈。  
很多时候不是模型不会写，而是它对大型代码库的结构、依赖、历史和模块关系理解不够稳。

所以 GitNexus 这条路线，哪怕现在还不能说已经成熟，也很值得持续盯：  
它打的不是边缘需求，而是 coding assistants 真正要走向大仓库生产力时绕不过去的问题。

### 为什么值得看
因为只要 agent 还看不懂整仓库，它在复杂工程里就很难稳定。knowledge graph + MCP 至少给出了一个有方向感的解法。

### 必看指数
**必看指数：★★★★☆**

### 一句话结论
**GitNexus 值得看的地方，不是新奇，而是它正面打在“agent 如何理解整仓库”这个核心难题上。**
