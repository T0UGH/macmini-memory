# OpenCLI 本地接入待办

日期：2026-03-21
目的：把 `opencli` 在家里这台机器上真正接通，至少先让浏览器类命令可用。

## 当前进度（已完成）
- 已 clone 仓库：`/Users/haha/.openclaw/workspace/github/opencli`
- 已执行：`npm install`
- 已执行：`npm run build`
- 公共命令已验证可用：
  - `node dist/main.js hackernews top --limit 5`
- daemon 已自动启动
- 当前卡点：**Chrome 扩展未连接**

当前 `doctor` 状态：
- Daemon: running on port 19825
- Extension: not connected

## 回家后要做的事

### 1. 安装 Browser Bridge 扩展
打开 Chrome：
- 地址：`chrome://extensions`
- 打开右上角 **开发者模式**
- 点击 **加载已解压的扩展程序**
- 选择目录：

`/Users/haha/.openclaw/workspace/github/opencli/extension`

装好后保持 Chrome 开着。

### 2. 先验证连接
在终端进入：

```bash
cd /Users/haha/.openclaw/workspace/github/opencli
node dist/main.js doctor
```

目标结果：
- Daemon: OK
- Extension: OK

### 3. 验证浏览器类命令
先用这些最小命令测试：

```bash
cd /Users/haha/.openclaw/workspace/github/opencli
node dist/main.js bilibili hot --limit 3
node dist/main.js zhihu hot
```

如果要测小红书 / 其他站点，先确认 Chrome 里已经登录对应网站。

### 4. 再看桌面适配器（可选）
后续可以继续试：

```bash
node dist/main.js codex status
node dist/main.js cursor status
node dist/main.js feishu status
```

## 备注
- 这个项目的核心能力是：把网站、Electron 应用、本地 CLI 统一成 agent 可调用的命令行接口。
- 浏览器类命令依赖：
  - Chrome 正在运行
  - 已登录目标网站
  - Browser Bridge 扩展已连接
- 当前不是 opencli 主程序坏了，**只是扩展还没接上**。

## 下一步建议
扩展装好后，回来直接让我继续：
- 验证常用站点是否可用
- 看它和 OpenClaw / agent workflow 怎么结合最值钱
- 选 2~3 个高价值场景做固定用法
