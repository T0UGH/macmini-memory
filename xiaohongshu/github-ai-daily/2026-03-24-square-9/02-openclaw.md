## openclaw/openclaw
**openclaw v2026.3.23**

发布时间：2026-03-24 07:15

这版更像“把系统做结实”的维护版本：修发布链路、补 compaction 校验、收紧 Telegram / SSRF 防护。

**这次具体改了什么**
- Telegram 媒体传输相关的安全策略被修正，属于 SSRF 防护链路的一部分。
- 说明 OpenClaw 在补“平台接入层”的边界安全，不只是堆功能；这对消息渠道型 agent 是硬需求。

**这意味着什么**
- 这类改动对常驻运行和生产使用更关键。

**原始证据**
- Telegram/auto-reply: preserve same-chat inbound debounce order without stranding stale busy-session followups, and keep same-key overflow turns ordered when tracked debounce keys are saturated. Thanks @osolmaz.

**一句判断**
这版更像“把系统做结实”的维护版本：修发布链路、补 compaction 校验、收紧 Telegram / SSRF 防护。
