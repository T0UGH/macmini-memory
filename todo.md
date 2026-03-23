# TODO

- [ ] 本周研究一下这个 Obsidian 相关思路/用法：
  - 链接：`https://x.com/boniusex/status/2035630916668907740?s=46`
  - 备注：来自 boniusex 的 X 帖子，先作为待研究线索收录；后续重点看它适不适合纳入个人知识管理 / 记忆工作流。

- [ ] 完成 OpenCLI Browser Bridge 初始化：
  - 在 Chrome 打开 `chrome://extensions`
  - 打开 Developer mode
  - Load unpacked
  - 选择目录：`/Users/haha/.local/node-v22.19.0-darwin-arm64/lib/node_modules/@jackwener/opencli/extension`
  - 完成后运行：`opencli doctor --live`

- [ ] 继续研究 OpenCLI 原理，下一步优先看 Browser Bridge / daemon / CDP 这层是怎么接起来的。

- [ ] 注册 Product Hunt 开发者应用，获取 API 凭据：
  - 打开 https://www.producthunt.com/v2/oauth/applications
  - 创建一个新应用（免费）
  - 拿到 `client_id` 和 `client_secret`
  - 填入 `/Users/haha/workspace/memory/scripts/config_product_hunt.json` 的对应字段
  - 有了这个，Product Hunt AI Daily 就能从月度数据升级到每日精确数据
