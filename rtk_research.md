# RTK (Rust Token Killer) 研究报告

> 日期: 2026-03-10 | GitHub: rtk-ai/rtk | 版本: v0.27.2 | License: MIT

## 项目概述

RTK 是一个 Rust 编写的高性能 CLI 代理工具，通过智能过滤和压缩命令输出，为 AI 编程助手（尤其是 Claude Code）降低 **60-90% 的 token 消耗**。单个二进制，零依赖，代理开销 <10ms。

- **Stars**: 5,300+ (1.5 个月) | **Forks**: 279 | **Open Issues**: 175
- **核心贡献者**: pszymkowiak (117), FlorianBruniaux (110), aeppling (35)
- **技术栈**: Rust (~1.07M 行), Shell (~89K 行)
- **安装**: `brew install rtk` 或 `cargo install`

---

## 核心工作机制

### 六阶段命令生命周期

```
用户输入: rtk git log -5
  ↓ PARSE → ROUTE → EXECUTE → FILTER → PRINT → TRACK
```

### 四大过滤策略

| 策略 | 操作 | 节省 |
|------|------|------|
| Smart Filtering | 移除注释、空白、样板代码 | -70% |
| Grouping | 按目录/类型聚合文件和错误 | -80% |
| Truncation | 保留关键上下文删除冗余 | -75% |
| Deduplication | 合并重复行并计数 | -90% |

### 三级过滤等级

```rust
pub enum FilterLevel {
    None,          // 无过滤
    Minimal,       // 删除注释、空白、样板
    Aggressive,    // 仅保留签名和关键结构
}
```

语言感知：支持 Rust, Python, JS/TS, Go, C/C++, Java, Ruby, Shell

---

## 支持的命令 (50+)

| 类别 | 命令 |
|------|------|
| 文件操作 | ls, tree, read, find, grep, diff, smart |
| Git | status, diff, log, add, commit, push, blame, show, branch |
| 构建 | cargo build, npm build, pnpm, go build |
| 测试 | cargo test, pytest, vitest, playwright, go test |
| 代码质量 | eslint, biome, tsc, ruff, clippy, mypy, golangci, prettier |
| GitHub CLI | gh pr/issue/run list/view |
| 容器 | docker ps/images/logs, kubectl pods/logs |
| 数据 | json, deps, env, curl, log |

---

## Claude Code 集成

### 自动重写模式（推荐）

```bash
rtk init --global  # 安装 PreToolUse Hook 到 ~/.claude/settings.json
```

工作流：
```
Claude 执行 Bash: git status
  ↓ PreToolUse Hook (rtk-rewrite.sh)
  ↓ 自动重写为: rtk git status
  ↓ 执行并过滤
  ↓ 压缩输出返回 Claude
```

- 100% 自动采用，Claude 无感知
- 零上下文开销
- Hook 文件: `~/.claude/hooks/rtk-rewrite.sh` (~50 行)

### 建议模式（非侵入）

```bash
rtk init --global --suggest
```

- Hook 发出系统消息提示，Claude 自主决定是否使用
- ~70-85% 采用率

---

## Token 节省分析

### 30 分钟 Claude Code 会话示例

| 操作 | 频率 | 标准 tokens | RTK tokens | 节省 |
|------|------|------------|-----------|------|
| ls/tree | 10x | 2,000 | 400 | -80% |
| cat/read | 20x | 40,000 | 12,000 | -70% |
| grep/rg | 8x | 16,000 | 3,200 | -80% |
| git status | 10x | 3,000 | 600 | -80% |
| git diff | 5x | 10,000 | 2,500 | -75% |
| cargo/npm test | 5x | 25,000 | 2,500 | -90% |
| **总计** | | **~118,000** | **~23,900** | **-80%** |

成本：标准 ~$0.71/session → RTK ~$0.14/session

---

## 模块架构

| 模块 | 行数 | 功能 |
|------|------|------|
| main.rs | 2,180 | Clap CLI 解析、命令路由 |
| git.rs | 1,813 | Git 命令过滤 |
| cargo_cmd.rs | 1,727 | Cargo 构建/测试过滤 |
| gh_cmd.rs | 1,601 | GitHub CLI 过滤 |
| init.rs | 1,575 | Hook 初始化与安装 |
| tracking.rs | 1,395 | SQLite token 统计 |
| cc_economics.rs | 1,157 | 成本分析 |
| filter.rs | - | 语言感知代码过滤引擎 |

### Token 追踪系统

- **存储**: SQLite (`~/.local/share/rtk/tracking.db`)
- **保留**: 90 天自动清理
- **查询**: `rtk gain`, `rtk gain --graph`, `rtk discover`

---

## 容错设计

- **Tee 模式**: 命令失败时保存完整输出到 `~/.local/share/rtk/tee/`
- **降级机制**: 过滤失败 → 输出原始结果
- **Exit Code 保留**: CI/CD 兼容
- **RTK_DISABLED=1**: 临时禁用过滤

---

## 构建优化

```toml
[profile.release]
opt-level = 3        # 最大优化
lto = true           # 链接时优化
codegen-units = 1    # 单代码生成单元
panic = "abort"      # 最小二进制
strip = true         # 移除调试符号
```

---

## 评价

### 亮点
1. **极致性能** — Rust 单二进制，<10ms 开销，零依赖
2. **覆盖面广** — 50+ 命令专项优化
3. **Claude Code 原生集成** — PreToolUse Hook 自动重写
4. **可观测性** — SQLite 追踪 + gain/discover 分析工具
5. **增长迅猛** — 1.5 个月 5,300+ stars

### 局限性
1. **Pre-1.0** — v0.27.x，API 可能有破坏性变更
2. **175 open issues** — Bug 和功能请求积压
3. **核心维护者少** — 2-3 人主力
4. **某些命令不兼容** — tail, xargs 等有已知问题
5. **Hook 依赖 Claude Code 版本** — 版本兼容性风险

### 适用场景
- 个人开发者使用 Claude Code（成本敏感）
- 长时间编码会话（token 节省累积显著）
- 中大型代码库（输出压缩收益更大）

### 不适用场景
- 需要完整输出调试的特殊情况
- 企业严格控制自动化工具
- 某些特殊 CLI 工具（需配置 exclude_commands）

---

## 相关资源

- 官网: https://www.rtk-ai.app
- Discord: https://discord.gg/gFwRPEKq4p
- 架构文档: ARCHITECTURE.md
- 故障排除: docs/TROUBLESHOOTING.md
