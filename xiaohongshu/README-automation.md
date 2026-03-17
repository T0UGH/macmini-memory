# 小红书自动发布链路

## GitHub AI Daily 发布脚本

脚本：
- `scripts/publish_xiaohongshu_github_daily.py`

作用：
- 按日期自动读取 `xiaohongshu/github-ai-daily/<date>-square-9/` 下的 PNG 图片
- 调用 `mcporter` → `xiaohongshu.publish_content(...)`
- 将发布结果记录到 `xiaohongshu/published/github-ai-daily/`

## 使用方式

```bash
python3 scripts/publish_xiaohongshu_github_daily.py \
  --date 2026-03-17 \
  --title 'github-ai日报 260317版' \
  --content 'GitHub AI 日报 260317 版。这次重点看 9 个仓库。图片按一仓一图整理，便于直接翻看。'
```

## 前置条件

- 本机已安装并启动 `xiaohongshu-mcp`
- `mcporter` 已配置：`xiaohongshu -> http://localhost:18060/mcp`
- 小红书已登录成功

## 默认约定

- 图片目录默认：`<date>-square-9`
- 默认标签：`GitHub AI日报 ClaudeCode Codex OpenClaw`
- 默认可见性：`公开可见`
