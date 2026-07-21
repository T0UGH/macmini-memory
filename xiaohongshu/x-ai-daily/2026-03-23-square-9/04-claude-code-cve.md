## Claude Code 的安全边界被现实补课：CVE-2026-33068 说明 agent 工具首先还是软件系统

> Claude Code workspace trust dialog bypass via repository settings loading order [CVE-2026-33068, CVSS 7.7].

### 我的判断
这条特别值得写进日报，因为它提醒大家：agent coding 工具再“智能”，也先是本地高权限软件。真正的高风险点很多时候不是模型推理，而是设置文件、信任边界、仓库内容、工具调用权限这些老派软件工程问题。

### 为什么值得看
对高频使用 Claude Code / OpenClaw / MCP 的用户来说，权限边界和加载顺序失守，风险比一次回答质量下降严重得多。尤其当工具越来越能执行 shell、读文件、调用网络时，这类漏洞会直接触达本机安全。

**建议动作：建议细看**

**必看指数：★★★★★**

### 一句话结论
**建议细看。**
