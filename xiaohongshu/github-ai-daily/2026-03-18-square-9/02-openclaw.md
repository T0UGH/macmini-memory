## openclaw/openclaw
**openclaw v2026.3.13-1**

发布时间：2026-03-15 02:04

这版更像“把系统做结实”的维护版本：修发布链路、补 compaction 校验、收紧 Telegram / SSRF 防护。

- 这次首先是在修补上一版损坏的 tag / release 路径，属于发布链路补丁，不是大功能更新。
- npm 版本号仍是 2026.3.13，-1 只体现在 Git tag / GitHub Release，等于是在修发布包装层。
- compaction 后置校验被补上：压缩完成后会按完整会话 token 数做 sanity check。
- Telegram 媒体传输相关的安全策略被修正，属于 SSRF 防护链路的一部分。
- This release exists to recover the broken v2026.3.13 tag/release path.

**一句话**
这次首先是在修补上一版损坏的 tag / release 路径，属于发布链路补丁，不是大功能更新。
