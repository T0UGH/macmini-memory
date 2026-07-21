## sst/opencode
**opencode v1.2.27**

发布时间：2026-03-16 10:34

- 这版 OpenCode 的重点很明确：修会话、修 worktree、补长任务稳定性，而不是堆新能力。
- 修复 worktree 与孤儿分支场景下的 session 丢失问题，这条对多分支并行工作流最有价值。
- 默认 chunk timeout 从 2 分钟提高到 5 分钟，长步骤执行更不容易被误判超时。
- 明确把 compaction message 记为 agent initiated，说明它在继续补齐会话状态与压缩链路的一致性。
- 清理 legacy permission module，并重构 QuestionService / PermissionNext 相关实现，偏底层治理，方向是把权限与提问流程做得更稳。

**一句话**
这版 OpenCode 的重点很明确：修会话、修 worktree、补长任务稳定性，而不是堆新能力。
