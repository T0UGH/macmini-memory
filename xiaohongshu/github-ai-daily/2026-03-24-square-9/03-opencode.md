## sst/opencode
**opencode v1.3.0**

发布时间：2026-03-23 07:32

OpenCode 这版重点不在宣传点，而在底层结构、历史性能和输入形态这些会影响长期使用体验的细节。

**这次具体改了什么**
- Bun 安装链路的配置序列化问题被处理，减少环境差异造成的安装异常。
- 会话历史改成分页加载，目标是把服务端性能和长会话稳定性拉上来。
- 这不是表面功能，但说明 OpenCode 也在补“越用越重”后的历史负担问题。

**这意味着什么**
- 长期使用时的稳定性和可维护性会比短期演示更受益。

**原始证据**
- **Node.js Support** : opencode can now run on Node.js in addition to Bun, with a dedicated Node.js entry point and build script that bundles the server with database migrations.

**一句判断**
OpenCode 这版重点不在宣传点，而在底层结构、历史性能和输入形态这些会影响长期使用体验的细节。
