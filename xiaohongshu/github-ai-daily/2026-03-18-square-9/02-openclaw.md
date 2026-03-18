## openclaw/openclaw
**openclaw v2026.3.13-1**

发布时间：2026-03-15 02:04

- 这次发布主要是在修复上一版损坏的 tag / release 路径，属于发布链路补丁。
- npm 版本号仍然是 `2026.3.13`，`-1` 只体现在 Git tag 和 GitHub Release 上。
- 修复 compaction 的后置校验：压缩后会按完整会话 token 数来做 sanity check。
- 修复 Telegram 媒体传输相关的安全策略问题，和 SSRF 防护链路有关。

**一句话**
这次发布主要是在修复上一版损坏的 tag / release 路径，属于发布链路补丁。
