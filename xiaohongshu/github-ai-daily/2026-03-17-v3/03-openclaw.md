# OpenClaw · v2026.3.13-1

发布时间：2026-03-15 02:04

### 这次更新了什么
- 恢复损坏的 tag / release 路径
- compaction 改用完整会话 token 做校验
- Telegram 媒体链路接入 SSRF 防护
- 修复 session reset 后 account/thread 丢失
- 修复 Feishu 非 ASCII 文件名与重复回复问题
- 修复 cron deadlock、gateway 未应答请求、browser session 校验
- 增加 Docker 时区支持
