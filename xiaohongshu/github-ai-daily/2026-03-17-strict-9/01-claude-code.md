## anthropics/claude-code
**Claude Code v2.1.77**

发布时间：2026-03-17 08:28

这版不是加花活，核心是在补重度使用时最痛的几条链路。

- 长输出能力继续上调：Opus 4.6 默认 64k，上限到 128k
- `allowRead` 沙箱权限更细，能在 `denyRead` 里局部开白名单
- `/copy N` 能直接复制倒数第 N 条回复
- `--resume` 截断问题修了，大 session 恢复也更快
- tmux / IDE / 剪贴板 / hook 权限边界继续补齐

**一句话**
Claude Code 已经进入“长期稳定工作代理”的打磨阶段。

---
