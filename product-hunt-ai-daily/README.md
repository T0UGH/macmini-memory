# Product Hunt AI Daily

每天 08:30（Asia/Shanghai）自动筛选 Product Hunt 上值得关注的 AI 新产品，生成中文简报并推送到飞书。

## 输出

- 每日 markdown 简报：`product-hunt-ai-daily/YYYY-MM-DD.md`
- 飞书直聊推送

## 关注方向

- AI coding / developer tools
- AI agent / multi-agent
- AI workflow / automation
- AI productivity
- AI research / search
- AI 创作者工具

## 降权/排除

- 纯噱头 AI 壁纸/头像/娱乐小工具
- 同质化套壳 chatbot
- 只靠营销文案、缺乏清晰产品信息的条目
- 与 AI 关系很弱的普通 SaaS

## 执行

```bash
python3 scripts/run_product_hunt_ai_daily.py
python3 scripts/validate_product_hunt_ai_daily.py
```

## 数据源

Product Hunt GraphQL API v2（需要 OAuth token）。
配置文件：`scripts/config_product_hunt.json`
