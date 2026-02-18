# OpenCowork 项目研究报告

## 1. 项目概述

**OpenCowork** 是一个开源的桌面端 AI 助手应用程序（数字同事），由 [Safphere](https://github.com/Safphere) 开发。

- **当前版本**: 1.1.8
- **许可证**: Apache-2.0
- **GitHub 仓库**: https://github.com/Safphere/opencowork
- **技术栈**: Electron + React + TypeScript + Vite
- **定位**: 开源版 Cowork，将电脑变成 AI 驱动的工作助手

![OpenCowork Demo](https://i.meee.com.tw/uA5H9yG.png)

---

## 2. 项目定位与目标

OpenCowork 是商业产品 "Cowork" 的开源版本，旨在将用户的电脑变成一个 AI 驱动的工作助手。

### 核心特点
- **模型无关性** - 支持任何具备 Agent 能力的模型（MiniMax、Claude、GPT 等），无供应商锁定
- **本地运行** - 在桌面端运行，可直接操作本地文件系统
- **可扩展性** - 通过 Skills 和 MCP 协议进行功能扩展

---

## 3. 主要功能特性

### 3.1 核心能力

| 功能 | 描述 |
|------|------|
| **模型 Agnostic** | 支持多种 Agent 模型，包括 Claude 兼容接口、MiniMax、智谱等 |
| **文件操作** | 读取、写入、创建、修改本地文件 |
| **终端控制** | 执行命令行操作 |
| **多会话管理** | 同时管理多个对话上下文 |
| **跨平台** | 支持 Windows、macOS、Linux |

### 3.2 Skills 系统

内置 **11 个 Skills** 和 **10 个 MCP 服务**（包含 MiniMax、智谱等的 Coding Plan 服务），开箱即用支持：
- Web Search（网页搜索）
- Web Reader（网页读取）
- Image Understanding（图像理解）

> 注意：使用 ClaudeCode 兼容接口（非标准 OpenAI SDK）

#### 内置 Skills 列表

项目在 `resources/skills/` 目录下提供了丰富的 Skills：
- `algorithmic-art` - 算法艺术
- `brand-guidelines` - 品牌指南
- `canvas-design` - Canvas 设计
- `doc-coauthoring` - 文档协作
- `internal-comms` - 内部沟通
- `mcp-builder` - MCP 服务构建
- `mcp_manager` - MCP 管理
- `skill-creator` - 技能创建
- `slack-gif-creator` - Slack GIF 创建
- `theme-factory` - 主题工厂
- `web-artifacts-builder` - Web 产物构建

#### MCP 服务

支持通过 MCP（Model Context Protocol）协议扩展功能，开箱即用提供 10 个 MCP 服务。

### 3.3 悬浮球（Floating Ball）

- 通过 `Alt+Space` 快捷键快速调用（可在设置中自定义）
- 增强的 UI 动画和优化的性能

### 3.4 合作伙伴

- **MiniMax** (国内/国际版)
- **智谱 AI** (Zhipu AI)
- **ZAI** (国际版)

---

## 4. 技术架构

### 4.1 前端
- **React 18** - UI 框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Tailwind CSS** - 样式框架
- **lucide-react** - 图标库
- **react-markdown** - Markdown 渲染
- **mermaid** - 流程图支持

### 4.2 后端（Electron）
- **Electron 30** - 桌面应用框架
- **@anthropic-ai/sdk** - Anthropic API 调用
- **@modelcontextprotocol/sdk** - MCP 协议支持
- **electron-store** - 本地配置存储

### 4.3 目录结构

```
opencowork/
├── electron/                    # Electron 主进程
│   ├── agent/                  # AI Agent 核心
│   │   ├── AgentManager.ts     # Agent 管理器
│   │   ├── AgentRuntime.ts     # 运行时
│   │   ├── BackgroundTaskManager.ts
│   │   ├── mcp/                # MCP 客户端
│   │   ├── security/           # 权限管理
│   │   ├── skills/             # Skills 管理
│   │   └── tools/              # 文件系统工具
│   ├── config/                 # 配置存储
│   ├── memory/                 # 记忆管理
│   └── services/               # 文件监控、日志
├── src/                        # React 前端
│   ├── components/             # UI 组件
│   ├── hooks/                  # React Hooks
│   ├── i18n/                   # 国际化
│   ├── services/               # 服务
│   └── theme/                  # 主题管理
├── resources/
│   ├── skills/                 # 内置 Skills
│   └── mcp/                    # 内置 MCP 配置
└── docs/                       # 文档
```

---

## 5. 安全考虑

⚠️ **风险提示**

项目 README 中明确指出：
- AI 可能会意外删除文件或执行错误命令
- 存在提示注入风险
- AI 可以读取授权目录内的所有文件

**建议**：
- 仅授权必要的目录
- 定期备份数据
- 审查操作请求

**免责声明**：本软件按"原样"提供，仅供学习和开发目的使用。开发者不对使用本软件造成的任何损失负责。

---

## 5.1 macOS 特定注意事项

由于该应用未使用 Apple 官方开发者证书签名，首次运行时会显示为"已损坏"。

**解决方案（任选其一）**：
1. **右键打开（推荐）**：右键点击 OpenCowork.app → 选择"打开" → 点击"打开"
2. **系统设置**：系统设置 → 隐私与安全 → 点击"仍要打开"
3. **命令行**：`sudo xattr -rd com.apple.quarantine /Applications/OpenCowork.app`

**安全保证**：该应用完全安全且开源：
- 查看源码：[github.com/Safphere/opencowork](https://github.com/Safphere/opencowork)
- 自行构建：`bun install && npm run build`

---

## 6. 构建与运行

### 开发模式
```bash
bun install
bun run dev
```

### 构建
```bash
bun run build
```

### macOS 注意事项
由于没有 Apple 开发者证书，应用可能显示为"已损坏"。解决方案：
1. 右键打开 → 选择"打开" → 点击"打开"
2. 系统设置 → 隐私与安全 → 点击"仍要打开"
3. 命令行：`sudo xattr -rd com.apple.quarantine /Applications/OpenCowork.app`

---

## 7. 配置选项

### 默认配置
- **API URL**: `https://api.minimaxi.com/anthropic`
- **Model**: `MiniMax-M2.1`

### 自定义配置
通过设置界面修改：
- API Key
- API URL
- Model 名称

或通过 `.env` 文件（开发环境）：
```bash
VITE_MODEL_NAME=your-model-name
```

---

## 8. 总结

OpenCowork 是一个功能完整的开源桌面 AI 助手，具有以下亮点：

✅ **开源免费** - Apache-2.0 许可证
✅ **多模型支持** - 不依赖单一供应商
✅ **本地运行** - 保护隐私
✅ **可扩展** - MCP 协议和 Skills
✅ **跨平台** - 支持主流操作系统

适合希望拥有本地 AI 工作助手、注重数据隐私、且需要灵活定制能力的开发者和技术用户使用。
