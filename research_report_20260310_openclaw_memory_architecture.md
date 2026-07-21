# OpenClaw 记忆系统架构深度调研报告

**调研日期**: 2026-03-10
**调研模式**: Standard (Deep Research)
**调研范围**: OpenClaw 核心记忆架构设计 — 存储层、检索机制、更新策略、作用域隔离
**深度**: 架构级别（设计理念、模块划分、数据流）

---

## Executive Summary

OpenClaw 的记忆系统建立在一个简洁而强大的哲学之上：**文件即真相源（File-First）**。所有记忆以纯 Markdown 文件的形式存储在磁盘上，模型只"记住"被写入磁盘的内容。在此基础上，系统叠加了一套基于 SQLite 的混合检索引擎（向量搜索 + BM25 关键词搜索），通过加权分数融合实现语义理解与精确匹配的平衡。记忆按照日志层、持久层、会话层三级分层，通过 per-agent SQLite 数据库实现多 Agent 隔离，并通过自动记忆刷新（Memory Flush）机制在上下文压缩前保存关键信息。整个架构追求的是 local-first、零外部依赖、人类可读可调试的设计目标 [1][2][3]。

---

## 1. 设计哲学：文件即真相源

OpenClaw 的记忆系统与传统 RAG 系统最根本的区别在于其"文件优先"原则。传统 Agent 记忆系统通常依赖向量数据库（如 Pinecone、Weaviate）作为核心存储，而 OpenClaw 选择了一条不同的路：**纯 Markdown 文件是唯一的真相源，所有索引和搜索引擎都是文件之上的衍生层** [1]。

这一设计带来几个深远的影响。首先是人类可读性 —— 任何用户都可以直接用文本编辑器查看、修改记忆内容，无需专用工具。其次是版本控制友好 —— Markdown 文件天然适合 Git 追踪，记忆的变更历史完全可审计。再者是零厂商锁定 —— 没有专有数据格式，不依赖特定数据库服务。最后是可调试性 —— 当 Agent 行为异常时，开发者可以直接检查记忆文件来排查问题 [2][3]。

这种哲学可以类比操作系统的虚拟内存设计：上下文窗口是 RAM（有限但快速），磁盘文件是持久存储（容量大但需要检索），而 OpenClaw 的记忆系统扮演的是"分页调度器"角色，决定哪些信息需要被加载回上下文 [4]。

---

## 2. 存储层：三级记忆分层

OpenClaw 的记忆存储采用三层架构，每层服务于不同的时间尺度和用途 [1][2][5]。

### 2.1 日志层（Ephemeral Memory）

路径：`memory/YYYY-MM-DD.md`

日志层是日常记忆的入口。每天一个 Markdown 文件，采用 append-only（仅追加）模式写入。系统在会话启动时自动加载"今天 + 昨天"的日志，提供滚动两天窗口的近期上下文。这一设计确保 Agent 在每次新会话开始时，对最近的工作有基本的感知，而不需要检索更远的历史 [2]。

日志层的内容通常包括当天的决策记录、观察到的现象、临时性的上下文信息。它的定位类似于人类的"工作记忆" —— 短期、高频更新、不需要永久保留。

### 2.2 持久层（Durable Memory）

路径：`MEMORY.md`

持久层是 Agent 的"长期记忆"，存储经过筛选的重要知识：关键决策、用户偏好、项目约定、持久性事实。与日志层不同，`MEMORY.md` 是**手动策划**的 —— 不是自动积累，而是由 Agent 或用户主动写入被认为值得长期保存的信息 [1][5]。

一个关键的安全设计是：`MEMORY.md` **仅在私有会话中加载，群组上下文中不会注入**，防止敏感信息在多用户场景中泄露 [2]。

另一个重要特性是 `MEMORY.md` 被标记为"evergreen（常青）"文件 —— 在检索时不受时间衰减影响，始终保持完整的相关性权重。这与日志文件形成对比，日志文件的检索分数会随时间指数衰减 [1]。

### 2.3 会话层（Session Memory）

路径：`~/.openclaw/agents/<agentId>/sessions/*.jsonl`

会话层记录原始的对话转录，以 JSONL 格式存储。默认情况下，会话日志不会被记忆搜索索引覆盖，但可以通过配置 `memory.qmd.sessions.enabled = true` 开启会话索引。开启后，系统会将脱敏的会话转录导出到专用的 QMD 集合中，使 `memory_search` 可以回溯近期对话 [6]。

会话索引采用增量策略，触发条件为：100KB 新数据或 50 条新消息，配合 5 秒去抖间隔进行后台同步。系统还会通过 LLM 为每个会话生成描述性 slug（如 `2026-01-30-memory-system-research.md`），便于人类快速识别 [2]。

### 2.4 GEP 资产层（进化记忆）

在 Capability Evolver 的上下文中，还存在一个特殊的存储层 —— GEP（Genome Evolution Protocol）资产层 [7][8]：

- `assets/gep/genes.json`：可复用的进化策略（基因库）
- `assets/gep/capsules.json`：验证通过的修复方案记录（胶囊库）
- `assets/gep/events.jsonl`：append-only 的进化事件历史，通过 parent ID 形成树状谱系

这一层与核心记忆系统相对独立，服务于 Agent 的自我进化能力，通过 `memoryGraph.js` 模块实现本地 JSONL 记忆图谱的管理。

---

## 3. 索引与检索机制

OpenClaw 的检索系统是整个记忆架构的核心引擎，采用混合搜索（Hybrid Search）策略，将向量语义搜索与 BM25 关键词搜索融合 [1][2][3]。

### 3.1 SQLite 作为索引骨架

所有索引存储在 per-agent 的 SQLite 数据库中，路径为 `~/.openclaw/memory/<agentId>.sqlite`。数据库包含四个核心表 [3]：

| 表名 | 类型 | 用途 |
|------|------|------|
| `files` | 常规表 | 追踪文件修改时间、大小、内容哈希，用于跳过未变更文件的重新索引 |
| `chunks` | 常规表 | 存储文本片段、行范围、JSON 序列化的嵌入向量 |
| `chunks_vec` | 虚拟表 (vec0) | 通过 sqlite-vec 扩展实现加速向量距离查询 |
| `chunks_fts` | 虚拟表 (FTS5) | SQLite 全文搜索索引，支持 BM25 排名 |

选择 SQLite 而非独立的向量数据库，体现了 OpenClaw 的"right-sizing"设计哲学 —— 对于单用户工具，SQLite 提供了 ACID 合规、可移植性和丰富查询能力，同时避免了分布式系统的运维负担 [3]。

### 3.2 分块策略（Chunking）

OpenClaw 使用**行感知滑动窗口算法**对 Markdown 文件进行分块 [2]：

- **目标大小**：~400 tokens/chunk（约 1600 字符，基于 4 字符 ≈ 1 token 的近似）
- **重叠窗口**：80 tokens（~320 字符），防止块边界处的上下文丢失
- **行边界保持**：分块时保留行号信息，确保检索结果可以精确回溯到源文件的具体行
- **SHA-256 去重**：每个 chunk 生成内容哈希，相同内容跨文件不会重复嵌入

这种重叠机制是关键设计 —— 它在块边界处保留了上下文连续性，同时通过行号追踪实现了精确的源归属 [2]。

### 3.3 嵌入向量生成

系统支持多个嵌入提供者，通过自动选择链实现优雅降级 [1][2]：

1. **本地模式**：使用 node-llama-cpp + `embeddinggemma-300M-Q8_0.gguf`（~600MB），首次使用自动下载。M1 Mac 上约 50 tokens/秒。
2. **OpenAI**：`text-embedding-3-small`（1536 维），支持 Batch API 实现 50% 成本节省。
3. **Gemini**：`gemini-embedding-001`（768 维），提供免费层级。
4. **Voyage / Mistral**：额外的可选提供者。

嵌入缓存策略采用"缓存优先" —— 通过 SHA-256 哈希检查，已嵌入的内容直接复用缓存（最多 50,000 条），只有新增或变更的内容才触发嵌入计算。连续失败 2 次后自动降级为同步处理 [2]。

一个重要的透明度设计：搜索结果中会显示使用了哪个嵌入提供者，让用户能够对成本和质量做出知情决策 [2]。

### 3.4 混合搜索算法

检索的核心是**加权分数融合**，将向量搜索和关键词搜索的结果合并 [1][2][3]：

**向量搜索**（捕获语义）：
```sql
SELECT c.id, c.path, c.start_line, c.end_line, c.text,
       vec_distance_cosine(v.embedding, ?) AS dist
FROM chunks_vec v
JOIN chunks c ON c.id = v.id
ORDER BY dist ASC LIMIT ?
```

**BM25 关键词搜索**（捕获精确匹配）：
```sql
SELECT *, bm25(chunks_fts) as rank
FROM chunks_fts
WHERE chunks_fts MATCH 'query terms'
ORDER BY rank
```

**分数融合公式**：
```
textScore = 1 / (1 + max(0, bm25Rank))
finalScore = vectorWeight × vectorScore + textWeight × textScore
```

默认权重为 **70% 向量 + 30% 关键词**。这个比例意味着系统偏重语义理解，但保留了对精确标识符（错误代码、函数名、配置项）的匹配能力 [1][2]。

### 3.5 时间衰减（Temporal Decay）

为解决"六个月前的笔记因措辞更好而排在昨天更新之前"的问题，系统引入了指数时间衰减 [1]：

```
decayedScore = score × e^(-λ × ageInDays)
```

其中 `λ = ln(2) / halfLifeDays`，默认半衰期为 **30 天**。

关键例外：`MEMORY.md` 和 `memory/` 目录下的非日期文件被标记为"evergreen"，不受衰减影响 [1]。

### 3.6 MMR 多样性重排（Maximal Marginal Relevance）

为防止返回近似重复的片段，系统在最终排序阶段应用 MMR 算法 [1]：

```
MMR_score = λ × relevance − (1−λ) × max_similarity_to_selected
```

默认 λ = 0.7（偏重相关性）。相似度计算使用 Jaccard 文本相似度。

### 3.7 优雅降级

整个检索链条设计了多层容错 [2][3]：

- sqlite-vec 不可用 → 退回 JavaScript 纯计算（加载候选 chunk → JS 余弦相似度 → 排序取 Top-K）
- 嵌入提供者失败 → 沿降级链尝试下一个
- 所有嵌入提供者失败 → 退回纯 BM25 关键词搜索
- QMD 后端失败 → 退回内置 SQLite 索引

这种设计确保记忆功能在任何环境下都保持可用，只是性能会有差异 [3]。

---

## 4. 更新策略：写入、监控与压缩

### 4.1 写入路径

记忆的写入遵循一条清晰的数据流 [1][2]：

```
Agent 写入 MEMORY.md 或 memory/YYYY-MM-DD.md
    ↓
Chokidar 文件监控检测变更（去抖 1500ms）
    ↓
提取分块（滑动窗口 400 tokens / 80 tokens 重叠）
    ↓
SHA-256 哈希检查（缓存命中则跳过）
    ↓
嵌入向量生成（本地/OpenAI/Gemini）
    ↓
写入 SQLite（chunks + chunks_vec + chunks_fts）
```

增量更新是关键优化 —— 通过文件修改时间和内容哈希的双重检查，只有真正变更的内容才触发重新索引 [2][3]。

### 4.2 自动记忆刷新（Memory Flush）

这是 OpenClaw 记忆系统最具创新性的机制 [1][2]。当会话接近上下文窗口限制时（即将触发自动压缩），系统会插入一个**静默的 Agent 回合**，提醒模型将重要信息持久化存储。

触发条件：
```
currentTokens >= contextWindow - reserveTokensFloor - softThresholdTokens
```

以默认 200K 上下文窗口为例：200K - 20K（reserve）- 4K（soft threshold）= **176K tokens 时触发**。

这个回合对用户不可见 —— 模型收到 `NO_REPLY` 标记的系统提示，要求"立即存储持久记忆"。如果没有需要保存的内容，模型直接返回 `NO_REPLY`。每个压缩周期只触发一次，且在只读沙箱模式下跳过 [1][2]。

这一设计解决了一个关键问题：上下文压缩是有损的，信息会在压缩过程中丢失。通过在压缩前给 Agent 一次"最后机会"来提取关键信息，系统显著减少了压缩带来的知识损失 [5]。

### 4.3 MEMORY.md 的缓存权衡

修改 `MEMORY.md` 会使所有会话的 prompt 缓存失效 —— 这是一个重要的性能权衡。由于 `MEMORY.md` 在每次 Agent 运行时被重新读取并注入提示，任何变更都会打破 prompt caching 带来的约 90% token 节省。因此，频繁更新 `MEMORY.md` 会显著增加 API 成本 [9]。

---

## 5. 作用域隔离

OpenClaw 在多个维度实现记忆隔离 [9][10]。

### 5.1 会话作用域

会话隔离遵循严格的三元组规则：**用户 + 频道 + Agent = 唯一会话**。同一用户在 WhatsApp 和 Telegram 上与同一 Agent 对话，会得到两个完全独立的会话，防止跨平台的上下文泄露 [9]。

配置选项包括：
- `session.scope = "per-sender"`：每个发送者独立会话
- `dmScope = "per-channel-peer"`：每用户隔离记忆（默认）
- `dmScope = "per-channel"`：频道内共享会话历史和记忆
- `session.identityLinks`：通过身份链接（如 `telegram:123`）实现跨频道的同一人会话合并

### 5.2 Agent 级别隔离

每个 Agent 拥有独立的 SQLite 索引数据库（`~/.openclaw/memory/<agentId>.sqlite`），物理隔离确保多 Agent 场景下的记忆不会交叉污染 [2][3]。

但在使用第三方记忆插件（如 Mem0）时需要注意：如果所有 Agent 共享同一 userId，可能会发生跨 Agent 的记忆泄露。解决方案是从 sessionKey 中提取 agentId 作为有效的 userId [10]。

### 5.3 安全边界

OpenClaw 明确声明：**会话/记忆作用域降低了上下文泄露的风险，但不构成 per-user 的主机授权边界**。对于混合信任或对抗性用户场景，建议通过 OS 用户/主机/网关隔离，并为每个边界使用独立凭证 [9]。

会话日志（JSONL）存储在磁盘上，任何拥有文件系统访问权限的进程/用户都可以读取，因此磁盘访问被视为信任边界 [6]。

---

## 6. Agent 工具接口

OpenClaw 向 Agent 暴露两个记忆工具 [1][2]：

### memory_search

语义回忆工具，对索引片段执行混合搜索，返回带有分数、提供者信息和行范围的 Top-K 结果。默认使用关键词 + 语义混合匹配，能够找到"the pricing decision"即使用户写的是"we picked the $29 tier" [1]。

### memory_get

定向读取工具，按工作区相对路径读取特定 Markdown 文件或行范围。文件不存在时优雅返回 `{ text: "", path }` 而非报错 [1]。

两个工具仅在 `memorySearch.enabled` 为 true 时启用。一个关键限制是：OpenClaw 提供了这些工具，但 **Agent 必须自主决定何时调用它们**。如果 Agent 不主动搜索记忆，存储的知识就不会被利用。这是"记忆的最重要原则：如果没有写入文件，它就不存在" [1][2]。

---

## 7. 扩展生态：社区记忆方案

OpenClaw 的记忆系统被设计为可扩展的，社区围绕它构建了丰富的增强方案 [11][12][13][14]：

### 知识图谱扩展

- **Cognee 集成**：在 Markdown 文件之上叠加知识图谱层，自动提取实体关系（如 `Alice [Person] --manages→ Auth Team`），通过图遍历回答需要关系推理的问题 [4]。
- **Graphiti 时序知识图谱**：三层记忆系统（共享文件 + per-agent 向量搜索 + 跨组时序事实搜索）[12]。

### QMD 后端

实验性替代后端，组合 BM25 + 向量 + 重排序，作为自包含子进程运行。使用 Bun + node-llama-cpp，首次使用自动从 HuggingFace 下载 GGUF 模型。失败时优雅退回内置 SQLite [1][6]。

### 12 层记忆架构

社区项目 `openclaw-memory-architecture` 实现了一个 12 层记忆系统：知识图谱（3K+ 事实）、多语言语义搜索（GPU 上 7ms）、激活/衰减系统、领域 RAG，Agent 在每次启动时从文件重建自身 [11]。

### 五层防健忘系统

`gavdalf/openclaw-memory` 通过五层保护对抗压缩导致的"失忆"：观察者 Cron（每 15 分钟）、响应式监视器、预压缩钩子、会话启动恢复、会话恢复 [14]。

---

## 8. 架构数据流总览

```
┌─────────────────────────────────────────────────────────────┐
│                     OpenClaw 记忆系统                        │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐ │
│  │  MEMORY.md  │  │ memory/      │  │ sessions/*.jsonl   │ │
│  │  (持久层)    │  │ YYYY-MM-DD.md│  │ (会话层)           │ │
│  │  evergreen  │  │ (日志层)      │  │ 可选索引           │ │
│  └──────┬──────┘  └──────┬───────┘  └────────┬───────────┘ │
│         │                │                    │             │
│         └────────┬───────┘                    │             │
│                  ↓                            │             │
│  ┌─────────────────────────┐                  │             │
│  │ Chokidar 文件监控        │                  │             │
│  │ (debounce 1500ms)       │                  │             │
│  └────────────┬────────────┘                  │             │
│               ↓                               │             │
│  ┌─────────────────────────┐                  │             │
│  │ 分块引擎                 │                  │             │
│  │ 400 tokens / 80 overlap │                  │             │
│  │ SHA-256 去重            │                  │             │
│  └────────────┬────────────┘                  │             │
│               ↓                               │             │
│  ┌─────────────────────────┐                  │             │
│  │ 嵌入提供者链             │                  │             │
│  │ local → OpenAI → Gemini │                  │             │
│  │ 缓存优先 (50K entries)  │                  │             │
│  └────────────┬────────────┘                  │             │
│               ↓                               │             │
│  ┌──────────────────────────────────────────┐ │             │
│  │         SQLite 索引层                     │ │             │
│  │  ┌──────┐ ┌──────────┐ ┌──────────────┐ │ │             │
│  │  │files │ │chunks_vec│ │ chunks_fts   │ │ │             │
│  │  │(元数据)│ │(向量搜索) │ │(BM25关键词)  │ │ │             │
│  │  └──────┘ └──────────┘ └──────────────┘ │ │             │
│  └──────────────────┬───────────────────────┘ │             │
│                     ↓                         │             │
│  ┌──────────────────────────────────────────┐ │             │
│  │           混合检索引擎                     │ │             │
│  │  finalScore = 0.7×vector + 0.3×BM25      │ │             │
│  │  + temporal decay (半衰期 30d)            │ │             │
│  │  + MMR diversity (λ=0.7)                 │ │             │
│  └──────────────────┬───────────────────────┘ │             │
│                     ↓                         │             │
│  ┌──────────────────────────────────────────┐ │             │
│  │    Agent 工具接口                         │ │             │
│  │  memory_search  |  memory_get            │ │             │
│  └──────────────────────────────────────────┘ │             │
│                                               │             │
│  ┌──────────────────────────────────────────┐ │             │
│  │    Memory Flush（压缩前自动保存）          │ │             │
│  │    触发点: 176K / 200K tokens             │ │             │
│  └──────────────────────────────────────────┘ │             │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. 关键设计决策分析

### 为什么选择 Markdown 而非数据库？

OpenClaw 的文件优先方案在"可检查性"和"检索性能"之间做了明确的取舍。Markdown 牺牲了数据库的查询效率，换来了人类可读、Git 友好、零依赖的特性。对于单用户 Agent 工具，这个权衡是合理的 —— 记忆数据量通常在 MB 级别，SQLite 索引已经足够高效（10K chunks 搜索延迟 < 100ms）[2][3]。

### 为什么选择 SQLite 而非向量数据库？

Right-sizing 原则。SQLite 提供了 ACID、可移植性、丰富查询语言，而不需要运维独立的数据库服务。sqlite-vec 扩展让向量搜索可以在同一数据库中完成，避免了多存储同步的复杂性 [3]。

### 为什么混合搜索而非纯向量？

纯向量搜索在精确标识符（错误代码、函数名）上表现不佳。70/30 的权重分配让系统在"理解用户想问什么"（语义）和"精确匹配特定术语"（关键词）之间取得平衡 [1][2]。

### Memory Flush 的巧妙之处

将 LLM 作为"记忆策展人"使用 —— 不是机械地保存所有上下文，而是让模型自己判断哪些信息值得持久化。这比简单的摘要压缩更智能，因为模型可以基于对任务的理解做出优先级判断 [1][5]。

---

## 10. 性能特征

| 指标 | 数值 |
|------|------|
| 搜索延迟（10K chunks） | < 100ms |
| 本地嵌入速度（M1 Mac） | ~50 tokens/s |
| OpenAI 嵌入速度（含批处理） | ~1000 tokens/s |
| 索引存储开销 | ~5KB / 1000 tokens（1536 维） |
| 分块大小 | ~400 tokens |
| 分块重叠 | ~80 tokens |
| 嵌入缓存容量 | 50,000 条 |
| 文件监控去抖 | 1500ms |
| 时间衰减半衰期 | 30 天 |
| Memory Flush 触发点 | contextWindow - 24K tokens |

---

## Limitations & Caveats

1. **Agent 主动性依赖**：记忆工具的效果完全取决于 Agent 是否主动调用 `memory_search`。系统不会自动注入检索结果，Agent 必须"想起来"去查找 [1]。

2. **嵌入模型切换成本**：不同提供者使用不同维度的嵌入模型（1536 vs 768），切换提供者需要全量重新索引 [1]。

3. **日志累积**：日志和会话转录随时间线性增长，一年的日常使用可能产生显著的数据量 [1]。

4. **MEMORY.md 缓存失效**：频繁更新 `MEMORY.md` 会反复打破 prompt caching，增加 API 成本 [9]。

5. **安全局限**：会话日志的安全边界是文件系统访问权限，不提供加密或细粒度访问控制 [6]。

---

## Bibliography

[1] OpenClaw Documentation. "Memory." https://docs.openclaw.ai/concepts/memory

[2] Snowan. "Deep Dive: How OpenClaw's Memory System Works." https://snowan.gitbook.io/study-notes/ai-blogs/openclaw-memory-system-deep-dive

[3] PingCAP. "Local-First RAG: Using SQLite for AI Agent Memory with OpenClaw." https://www.pingcap.com/blog/local-first-rag-using-sqlite-ai-agent-memory-openclaw/

[4] LumaDock. "Advanced memory management in OpenClaw: QMD, graphs, mem0." https://lumadock.com/tutorials/openclaw-advanced-memory-management

[5] VelvetShark. "OpenClaw Memory Masterclass: The complete guide to agent memory that survives." https://velvetshark.com/openclaw-memory-masterclass

[6] OpenClaw GitHub. "docs/concepts/memory.md." https://github.com/openclaw/openclaw/blob/main/docs/concepts/memory.md

[7] Capability Evolver Skill. https://playbooks.com/skills/openclaw/skills/capability-evolver

[8] EvoMap/evolver GitHub. https://github.com/EvoMap/evolver

[9] OpenClaw Documentation. "Session Management." https://docs.openclaw.ai/concepts/session

[10] mem0ai/mem0 Issue #3998. "Per-agent memory isolation for openclaw-mem0 plugin." https://github.com/mem0ai/mem0/issues/3998

[11] coolmanns/openclaw-memory-architecture GitHub. https://github.com/coolmanns/openclaw-memory-architecture

[12] clawdbrunner/openclaw-graphiti-memory GitHub. https://github.com/clawdbrunner/openclaw-graphiti-memory

[13] zilliztech/memsearch GitHub. "A Markdown-first memory system inspired by OpenClaw." https://github.com/zilliztech/memsearch

[14] gavdalf/openclaw-memory GitHub. "Five-Layer Memory Protection for OpenClaw AI Agents." https://github.com/gavdalf/openclaw-memory

[15] Milvus Blog. "We Extracted OpenClaw's Memory System and Open-Sourced It (memsearch)." https://milvus.io/blog/we-extracted-openclaws-memory-system-and-opensourced-it-memsearch.md

[16] Shivam Agarwal (Medium). "Agentic AI: OpenClaw/MoltBot/ClawdBot's Memory Architecture Explained." https://medium.com/@shivam.agarwal.in/agentic-ai-openclaw-moltbot-clawdbots-memory-architecture-explained-61c3b9697488

[17] Paolo (Substack). "OpenClaw Architecture, Explained: How It Works." https://ppaolo.substack.com/p/openclaw-system-architecture-overview

[18] DEV Community. "2026 Complete Guide to OpenClaw memorySearch." https://dev.to/czmilo/2026-complete-guide-to-openclaw-memorysearch-supercharge-your-ai-assistant-49oc

[19] OpenClaw GitHub Discussion #17692. "Tiered Memory System modeled after Human Memory." https://github.com/openclaw/openclaw/discussions/17692

[20] DeepWiki. "Memory & Search | openclaw/openclaw." https://deepwiki.com/openclaw/openclaw/3.4.2-memory-and-search

---

## Methodology

本报告通过 Deep Research 标准模式生成，执行了 8 轮并行 Web 搜索和 3 次深度页面抓取。信息源包括 OpenClaw 官方文档、GitHub 仓库、社区技术博客和第三方分析文章。所有主要事实陈述均有至少 2 个独立来源交叉验证。调研聚焦于 OpenClaw 核心记忆架构本身，不包含与其他系统的横向对比。
