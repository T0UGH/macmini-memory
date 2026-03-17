## 图 2｜openclaw/openclaw
**OpenClaw v2026.3.13-1**

发布时间：2026-03-15 02:04

这版名义上是恢复型 release，实际上是发布链路 + 系统稳定性补丁。

- 修复上一版损坏的 tag / release 路径
- npm 版本仍是 `2026.3.13`，`-1` 只体现在 Git tag / GitHub Release
- compaction 改成按完整会话 token 做 sanity check
- Telegram 媒体传输被重新接回 SSRF 防护链路
- 对外功能增量不大，但发布一致性和安全边界更稳了

**一句话**
OpenClaw 真正值得盯的，还是系统底层稳定性和安全收口能力。

---
