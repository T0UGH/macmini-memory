# Claude Code · v2.1.77

发布时间：2026-03-17 08:28

### 这次更新了什么
- Opus 4.6 默认最大输出提到 64k，上限提到 128k
- 新增 `allowRead`，允许在 `denyRead` 区域里重新放开读权限
- `/copy N` 支持复制倒数第 N 条 assistant 回复
- 修复复合 bash 命令的 Always Allow 规则错误，减少重复权限弹窗
- 修复 `--resume` 截断最近历史
- 修复 PreToolUse hook 绕过 deny
- 修复 tmux / IDE / clipboard / worktree 一批兼容问题
