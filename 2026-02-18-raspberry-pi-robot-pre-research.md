# ZeroClaw 树莓派机器人预研文档

**日期**: 2026-02-18
**作者**: Claude
**主题**: 基于 ZeroClaw 的树莓派语音控制机器人

---

## 一、项目背景

用户希望基于树莓派开发一个小机器人，以 ZeroClaw 作为大脑，实现语音控制功能。

### 1.1 ZeroClaw 项目简介

ZeroClaw 是一个用 100% Rust 编写的轻量级 AI 助手运行时，核心特性：

- **极小内存占用**: < 5MB RAM
- **快速启动**: 冷启动 < 10ms
- **跨平台**: ARM、x86、RISC-V
- **安全优先**: 配对机制、沙箱、工作区隔离

### 1.2 核心架构

ZeroClaw 采用 **Trait + Factory** 架构，核心扩展点：

| 扩展点 | Trait | 现有实现 |
|--------|-------|----------|
| LLM 提供商 | `Provider` | 50+ (OpenAI, Anthropic, Ollama, GLM, Qwen 等) |
| 消息频道 | `Channel` | 10+ (Telegram, Discord, 钉钉, 飞书 等) |
| 工具 | `Tool` | Shell, File, Memory, GPIO 等 |
| 内存后端 | `Memory` | SQLite, PostgreSQL, Markdown 等 |
| 硬件外设 | `Peripheral` | RPi GPIO, Nucleo, Arduino 等 |

---

## 二、需求分析

### 2.1 功能需求

用户期望机器人具备：

1. **语音对话** - 通过语音与机器人交互
2. **GPIO 控制** - 控制 LED、马达、传感器
3. **移动能力** - 轮式/履带移动 (未来扩展)
4. **语音唤醒** - 离线 + 在线结合

### 2.2 技术需求

| 需求 | 描述 |
|------|------|
| 语音唤醒 | 本地检测唤醒词 + 云端识别 |
| 语音输入 | 麦克风 → 语音转文字 (ASR) |
| 语音输出 | 文字转语音 (TTS) → 扬声器 |
| 硬件控制 | GPIO、I2C、SPI |
| 本地智能 | 本地 LLM (Ollama) |
| 云端智能 | OpenAI / Anthropic |

### 2.3 预算

高级预算 (1500+ 元)，可支持：
- 树莓派 5
- 较好的语音模块 (USB 麦克风、扬声器)
- 电机驱动、传感器
- 可选配机械臂或小车底盘

---

## 三、ZeroClaw 现有能力

### 3.1 硬件支持

项目已支持 Raspberry Pi GPIO：

```rust
// src/peripherals/rpi.rs
// 提供 gpio_read 和 gpio_write 工具
// 使用 rppal 库，BCM 编号
```

### 3.2 架构设计参考

参考文档: `docs/hardware-peripherals-design.md`

两种运行模式：

1. **Edge-Native (边缘原生)**: ZeroClaw 直接运行在树莓派上
2. **Host-Mediated (主机中介)**: ZeroClaw 运行在主机，通过 USB 控制树莓派

---

## 四、架构方案

### 4.1 推荐架构: 混合方案

```
┌─────────────────────────────────────────────────────────────┐
│                    树莓派 5 (ZeroClaw 运行)                  │
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐ │
│  │ 语音模块    │───►│ VoiceChannel│───►│ Agent Loop     │ │
│  │ - 麦克风    │    │ (新增)       │    │ (LLM Provider) │ │
│  │ - 扬声器    │    │ - VAD       │    └────────┬────────┘ │
│  │             │    │ - ASR       │             │          │
│  └─────────────┘    └─────────────┘             │          │
│                                                  │          │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Tools                                                   ││
│  │ - gpio_read/write (已有)                                ││
│  │ - shell, file, memory (已有)                           ││
│  │ - tts_play (新增)                                      ││
│  │ - motor_control (新增)                                  ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ 云端 LLM        │
                    │ (OpenAI/本地)   │
                    └─────────────────┘
```

### 4.2 语音数据流

```
1. 唤醒词检测器 (后台运行)
      ↓ 检测到 "小 claw"
2. VoiceChannel 开始收音
      ↓
3. VAD 检测说话结束
      ↓
4. ASR 语音转文字
      ↓
5. 文字作为 UserMessage 发送给 Agent
      ↓
6. Agent 调用 LLM Provider
      ↓
7. Agent 调用 TtsTool 生成语音
      ↓
8. 播放语音回复
```

---

## 五、技术选型建议

### 5.1 语音模块

| 功能 | 技术选型 | 说明 |
|------|----------|------|
| 唤醒词检测 | Porcupine (离线) | 支持自定义唤醒词 |
| 语音活动检测 | WebRTC VAD | 判断说话开始/结束 |
| 语音识别 (ASR) | Whisper.cpp (离线) / OpenAI Whisper API (在线) | 混合使用 |
| 语音合成 (TTS) | Edge TTS (在线) / Coqui TTS (离线) | Edge TTS 效果更好 |

### 5.2 硬件选型

| 组件 | 推荐 | 价格参考 |
|------|------|----------|
| 主控 | 树莓派 5 4GB/8GB | 300-500 元 |
| 存储 | 64GB+ TF 卡 | 50 元 |
| 麦克风 | USB 麦克风 (ReSpeaker 4-Mic) | 100-200 元 |
| 扬声器 | 3.5mm 音箱 或 USB 扬声器 | 50-100 元 |
| 电机驱动 | L298N / DRV8833 | 20-50 元 |
| 电源 | 树莓派官方电源 + 电池组 | 100-200 元 |
| 底盘 | 小车底盘 / 麦克纳姆轮 | 100-300 元 |

### 5.3 软件架构

| 组件 | 实现方式 |
|------|----------|
| ZeroClaw | 边缘原生模式 (直接运行在树莓派) |
| 本地 LLM | Ollama + llama3.2 / qwen2.5 |
| 云端 LLM | OpenAI (GPT-4o) 或 Anthropic (Claude) |
| 语音处理 | Rust crate (绑定 C 库) 或 Python 子进程 |

---

## 六、实施路径

### 6.1 第一阶段: 基础功能

1. 树莓派系统安装 + ZeroClaw 部署
2. GPIO 控制验证 (LED、继电器)
3. 基础对话 (通过 SSH/Telegram 测试)

### 6.2 第二阶段: 语音输入

1. USB 麦克风配置
2. 语音唤醒模块集成
3. ASR 语音转文字
4. VoiceChannel 实现

### 6.3 第三阶段: 语音输出

1. TTS 集成
2. 语音播放
3. 对话流程优化

### 6.4 第四阶段: 移动能力

1. 电机驱动集成
2. 运动控制工具
3. 传感器扩展

---

## 七、关键问题

### 7.1 语音唤醒如何接入 ZeroClaw？

语音唤醒**不是** Provider，而是：

- **唤醒检测**: 独立的后台进程，检测到唤醒词后触发
- **语音输入**: 作为 `Channel` 接入 ZeroClaw
- **语音输出**: 作为 `Tool` 接入 ZeroClaw

### 7.2 离线 vs 在线？

推荐混合模式：

- **简单命令**: 本地识别 ("开灯"、"前进")
- **复杂对话**: 云端 LLM
- **基础回复**: 本地 TTS
- **复杂回复**: 云端 TTS

### 7.3 ZeroClaw 能否直接运行在树莓派上？

可以。ZeroClaw 是纯 Rust，单二进制，支持 ARM。需注意：

- 使用 `aarch64-unknown-linux-gnu` 编译
- 内存考虑: 建议 4GB+ 版本
- 性能: 本地 LLM 建议用量化模型

---

## 八、风险与注意事项

1. **算力限制**: 树莓派运行本地 LLM 较慢，建议主要用云端
2. **音频质量**: USB 麦克风建议选择带降噪的
3. **延迟**: 网络延迟会影响云端响应体验
4. **功耗**: 移动机器人需配电池组

---

## 九、下一步

1. 确认硬件采购清单
2. 购买设备，搭建基础环境
3. 部署 ZeroClaw 到树莓派
4. 验证 GPIO 控制
5. 实现语音 Channel

---

## 十、参考资料

- ZeroClaw 文档: `docs/`
- 硬件外设设计: `docs/hardware-peripherals-design.md`
- RPi GPIO: `src/peripherals/rpi.rs`
- Porcupine: https://picovoice.ai/porcupine/
- Whisper.cpp: https://github.com/ggerganov/whisper.cpp
- Edge TTS: https://github.com/rany2/edge-tts
- Ollama: https://ollama.com/
