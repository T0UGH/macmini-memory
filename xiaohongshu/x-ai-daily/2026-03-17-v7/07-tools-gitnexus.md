# 4. GitNexus 这类工具，为什么值得跟？

GitNexus 在做的事情其实很直接：
把整个 repo 转成 knowledge graph，再通过 MCP 喂给 Claude Code / Cursor 这类工具。

它瞄准的问题不是“当前文件怎么补全”，
而是更麻烦、也更真实的那个：

## agent 能不能真正理解整仓库？

这是大项目里最容易卡住的点：
- 代码跨很多目录和模块
- 改一个地方会影响别的地方
- 纯靠聊天上下文很快就会失真

所以 repo understanding 这条线，
我认为会越来越重要。
谁能更好地解决“大仓库上下文问题”，
谁的 coding agent 才更像真实生产力工具。
