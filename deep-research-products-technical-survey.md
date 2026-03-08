# Deep Research Products: Technical Architecture Survey

> Date: 2026-03-08
> Scope: Commercial and open-source deep research products, their architectures, and technical approaches

---

## 1. OpenAI Deep Research

**Launch:** February 2025 | **Model:** o3 (specialized version), later o4-mini lightweight variant

### Architecture

OpenAI Deep Research uses a **multi-agent orchestration** approach with three model calls under the hood in ChatGPT:

1. **Helper model** (GPT-4.1): Clarifies user intent, collects preferences/goals
2. **Prompt rewriter** (GPT-4.1): Expands or specifies user queries
3. **Deep research model** (o3 variant): Performs the actual research with extended reasoning

The core model was trained via **end-to-end reinforcement learning** on complex browsing and reasoning tasks in simulated research environments. It learned to plan multi-step search trajectories, backtrack unfruitful paths, and pivot strategies based on new information.

### Agent Loop: Plan-Act-Observe (ReAct)

Five-phase process:
1. **Clarification** - Follow-up questions to align with user intent
2. **Decomposition** - Break query into sub-questions with prioritization
3. **Iterative Search** - Progressive web searches with refined queries
4. **Content Analysis** - Reads HTML, PDFs, images; can execute Python
5. **Synthesis** - Structured reports with inline citations

**Stopping criteria:**
- Coverage-based: 2+ independent sources per sub-question; novelty exhaustion; contradiction resolution
- Hard limits: 20-30 min wall-clock; 30-60 web searches; 120-150 page fetches; 150-200 reasoning iterations

### Citations

Every factual claim gets an inline citation with clickable reference. API exposes annotations with `start_index` and `end_index` character spans. Raw format example: `【45†L75-L83】` (source 45, lines 75-83). All intermediate steps (reasoning, searches, code executions) are also exposed.

### Performance

- **Humanity's Last Exam:** 26.6% (vs DeepSeek R1 9.4%, GPT-4o 3.3%)
- Professionals rated outputs as "better than intern work" in blind tests
- 15,000-word building code report = 6-8 human hours saved
- Processing time: 5-30 minutes per query

### Key References
- [Introducing Deep Research - OpenAI](https://openai.com/index/introducing-deep-research/)
- [How Deep Research Works - PromptLayer](https://blog.promptlayer.com/how-deep-research-works/)
- [Deep Research System Card (PDF)](https://cdn.openai.com/deep-research-system-card.pdf)
- [Deep Research Architecture - Cobus Greyling](https://cobusgreyling.medium.com/openai-deep-research-ai-agent-architecture-7ac52b5f6a01)
- [Deep Research API Docs](https://platform.openai.com/docs/guides/deep-research)

---

## 2. Google Gemini Deep Research

**Launch:** December 2024 (Gemini 2.0) | **Current Model:** Gemini 3.1 Pro (Dec 2025 upgrade)

### Architecture

Uses a **single-agent agentic loop** with Gemini 3 Pro as the reasoning core, combined with Google Search infrastructure. The agent iteratively plans, searches, reads results, identifies gaps, and searches again in a continuous reasoning loop.

**Key technical innovation - Asynchronous Task Manager:**
Google developed a novel async task manager that maintains shared state between the planner and task models. This enables graceful error recovery without restarting the entire task when individual steps fail during the multi-minute research process.

### API Architecture (Interactions API)

Research tasks trigger dozens of search queries over 2-15 minutes. Standard synchronous HTTP would fail (timeouts at 30-60 sec), so Google built the **Interactions API** with:
- `background=True` parameter for async execution
- Polling-based interface for progress checking
- Designed for extended execution times

### Multi-Step Planning

Training focused on three challenges:
1. **Iterative planning** - Model grounds itself on all gathered info, identifies missing information and discrepancies, trades off comprehensiveness vs compute/wait time
2. **Error recovery** - Single failure doesn't restart everything thanks to shared state management
3. **Multi-step RL for search** - Agent autonomously navigates complex information landscapes

### Citations (Grounding System)

Uses `groundingMetadata` in API responses containing:
- `webSearchQueries` - queries used (for debugging/transparency)
- `groundingChunks` - source URIs and titles
- `groundingSupports` - maps text segments (`startIndex`, `endIndex`) to source chunks via `groundingChunkIndices`
- Internal indexing format: `[6.2]` = query 6, result 2

**Known issues:** Sometimes provides links to pages that don't contain referenced text, or 404 pages. Open-source tool GroundCite was created to validate citations.

### Performance

- **Humanity's Last Exam:** 46.4% (state-of-the-art, full set)
- **DeepSearchQA:** 66.1%
- **BrowseComp:** 59.2%
- Processing time: 5-10 minutes

### Enterprise Features
- Upload PDFs/images directly into research
- Google Drive document integration
- Combine internet research with internal document grounding

### Key References
- [Gemini Deep Research Overview](https://gemini.google/overview/deep-research/)
- [Build with Gemini Deep Research (API)](https://blog.google/technology/developers/deep-research-agent-gemini-api/)
- [Gemini Deep Research API Docs](https://ai.google.dev/gemini-api/docs/deep-research)
- [Grounding with Google Search](https://ai.google.dev/gemini-api/docs/google-search)
- [Gemini Deep Research Sources Panel](https://skywork.ai/blog/ai-agent/gemini-sources-panel/)

---

## 3. Perplexity Deep Research / Pro Search

**Launch:** February 14, 2025 | **Model:** Model-agnostic (Sonar proprietary + frontier models)

### Architecture

Perplexity's core philosophy: **"You are not supposed to say anything that you didn't retrieve."**

The architecture is a complete end-to-end system with model-agnostic orchestration:

**Five-Stage RAG Pipeline:**
1. **Query Intent Parsing** - LLM-based semantic understanding beyond keywords
2. **Live Web Retrieval** - Real-time search index (not static), on-demand crawling
3. **Snippet Extraction** - Relevant passages extracted, not full documents
4. **Answer Generation with Citations** - LLM generates from provided context only, with inline citations
5. **Conversational Refinement** - Maintains history for follow-ups with iterative searches

**Retrieval Engine (Vespa.ai):**
- 200+ billion URLs indexed
- 400+ petabytes in hot storage
- Tens of thousands of index updates per second
- Hybrid search: dense retrieval (vector embeddings) + sparse retrieval (BM25)
- Documents divided into chunks for fine-grained relevance scoring

**Model Routing:**
- Classifier models assess query complexity
- Route to appropriate model: proprietary Sonar (cost-effective, specialized) or frontier models (GPT, Claude via Amazon Bedrock)
- Competitive advantage is in orchestration, not any single LLM

**Inference Engine (ROSE):**
- Python/PyTorch with performance-critical components in Rust
- Speculative decoding and multi-token prediction for latency
- NVIDIA H100 GPUs via AWS, Kubernetes orchestration

### Deep Research Mode

When activated:
- Performs dozens of parallel web searches
- Reads hundreds of sources
- Iteratively searches, reads documents, reasons about next steps
- Refines research plan as it learns more
- Cross-references findings for accuracy

### Citations

Strict grounding: every claim must trace to retrieved context. Inline citations link directly to source URLs. The model is trained/prompted to never assert anything not backed by retrieval.

### Performance

- **SimpleQA:** 93.9% accuracy (factuality benchmark)
- **Humanity's Last Exam:** 21.1%
- Processing time: 2-4 minutes (fastest of the major products)
- Scale: 435 million monthly queries, 170M monthly visits

### Key References
- [Perplexity Deep Research](https://www.perplexity.ai/hub/blog/introducing-perplexity-deep-research)
- [How Perplexity Built an AI Google - ByteByteGo](https://blog.bytebytego.com/p/how-perplexity-built-an-ai-google)
- [Sonar Deep Research API Docs](https://docs.perplexity.ai/getting-started/models/models/sonar-deep-research)
- [Perplexity Architecture - FrugalTesting](https://www.frugaltesting.com/blog/behind-perplexitys-architecture-how-ai-search-handles-real-time-web-data)

---

## 4. Anthropic Claude Research System

**Architecture:** Multi-agent orchestrator-worker pattern | **Models:** Claude Opus 4 (lead) + Claude Sonnet 4 (subagents)

### Architecture

Anthropic's approach uses **decentralized intelligence** via an orchestrator-worker pattern:

- **Lead Agent (Opus 4):** Analyzes requirements, develops strategy, spawns subagents
- **Subagents (Sonnet 4):** 3-5+ instances work in parallel on different aspects
- **Citation Agent:** Post-research processing ensures claims are attributed to sources
- **Memory System:** Plans persist in external storage to survive context window truncation (200K token limit)

### Extended Thinking Integration

Two thinking modes serve as controllable scratchpads:
1. **Lead Agent Planning:** Assesses tool fit, determines complexity, calculates subagent count, defines roles
2. **Subagent Evaluation:** Interleaved thinking after tool results to evaluate quality, identify gaps, refine queries

### OODA Research Loop

Observe (what info gathered) -> Orient (what tools/queries best) -> Decide (select specific tool) -> Act -> Repeat

### Search Strategy

Mirrors expert human research:
- **Start Wide:** Short, broad queries first (counteracts agents' tendency toward overly specific queries)
- **Parallel Tool Calling:** Lead agents spin up 3-5 subagents; subagents use 3+ tools in parallel
- **Progressive Narrowing:** Explore landscape, then drill into specifics
- **Adaptive:** Continuously adjust based on discoveries

### Performance

- Multi-agent (Opus 4 lead + Sonnet 4 subagents) outperforms single-agent Opus 4 by **90.2%** on internal research evaluations
- Token usage explains 80% of performance variance; model choice + tool calls = remaining 15%
- Multi-agent uses ~15x more tokens than chat; ~4x for single-agent
- Parallel processing cuts complex query time by up to 90%

### Reliability Engineering

- **State Management:** Resume from checkpoints, never restart
- **Rainbow Deployments:** Gradually shift traffic between versions for running agents
- **Observability:** Full production tracing without accessing conversation contents
- **Effort Scaling:** Simple queries = 1 agent, 3-10 calls; complex research = 10+ subagents

### Key Design Principles

Seven core principles including mental modeling (simulate agents before production), delegation clarity, effort scaling, tool design, self-improvement (Claude 4 models diagnose failures), search progression, and thinking guidance.

### Key References
- [How We Built Our Multi-Agent Research System - Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Building Effective Agents - Anthropic](https://www.anthropic.com/research/building-effective-agents)
- [Three Ways to Build Deep Research with Claude](https://paddo.dev/blog/three-ways-deep-research-claude/)

---

## 5. xAI Grok DeepSearch / DeeperSearch

**Launch:** February 2025 (Grok 3) | **Model:** Grok 3, later Grok 4

### Architecture

**Two-Tier Crawling System:**
1. **Continuous Indexing Layer:** Distributed crawler bots systematically index high-value sources (news, Wikipedia, academic, X posts)
2. **Query-Driven Crawling Layer:** On-demand agent generates sub-queries, fetches pages in real-time, follows links

**Key distinction from competitors:** Grok WebSearch relies primarily on its pre-built index (full-text + vector search) rather than active real-time crawling, prioritizing speed.

### Reasoning

Uses chain-of-thought reasoning (ReAct-like):
- Up to 7 verification levels for source credibility
- Cross-verifies across news articles, X posts, primary documents
- Minimum 3 function calls before providing answer, up to 10 per query

### Product Evolution

- **DeepSearch (Feb 2025):** Initial deep research with Grok 3
- **Think / Big Brain modes:** Reasoning modes using more compute
- **DeeperSearch (Jul 2025):** Enhanced version with Grok 4, extended search + more reasoning
- **Grok 4 Heavy:** Multi-agent "study group" approach - agents tackle parts of a problem and collaborate

### Key References
- [xAI DeepSearch Announcement](https://x.com/xai/status/1892400134178164775)
- [Understanding Grok DeepSearch](https://www.tryprofound.com/blog/understanding-grok-a-comprehensive-guide-to-grok-websearch-grok-deepsearch)
- [Grok 4 Deep Dive](https://www.ainewshub.org/post/grok-4-grok-4-heavy-a-deep-dive-into-xai-s-2025-ai-revolution)

---

## 6. Notable Open-Source Implementations

### ByteDance DeerFlow 2.0

Multi-agent framework on LangGraph/LangChain:
- **Agents:** Coordinator -> Background Investigator -> Planner -> Research Team (Researcher + Coder) -> Reporter
- Human-in-the-loop plan modification
- Docker/K8s sandboxed execution, cloud memory, skills system
- Multimodal output (slides, podcasts, visualizations)
- 25K GitHub stars (Feb 2026)
- [GitHub](https://github.com/bytedance/deer-flow)

### LangChain Open Deep Research

Hierarchical multi-agent pattern on LangGraph:
- Research Supervisor generates sub-topics
- Sub-agents research independently (context isolation)
- Sub-agents return **processed learnings + citations** (not raw pages) - key design insight
- Supervisor iterates until complete; final agent writes coherent report
- [GitHub](https://github.com/langchain-ai/open_deep_research)

### Together AI Open Deep Research

Open-source implementation demonstrating core deep research patterns.
- [Blog post](https://www.together.ai/blog/open-deep-research)

---

## Cross-Cutting Technical Patterns

### Architecture Comparison

| Product | Architecture | Agent Type | Typical Time | HLE Score |
|---------|-------------|------------|-------------|-----------|
| OpenAI Deep Research | Multi-model pipeline + single research agent | Single-agent (multi-model) | 5-30 min | 26.6% |
| Google Gemini DR | Single-agent with async task manager | Single-agent | 5-10 min | 46.4% |
| Perplexity DR | RAG pipeline with model routing | Single-agent | 2-4 min | 21.1% |
| Anthropic Claude | Orchestrator-worker multi-agent | Multi-agent | Variable | N/A (internal) |
| Grok DeepSearch | Dual-tier index + on-demand crawl | Single-agent | ~5 min | N/A |

### Common Design Patterns

1. **Plan-Act-Observe / ReAct loops** - Universal across all products
2. **Progressive search refinement** - Start broad, narrow based on findings
3. **Inline citations with character-level attribution** - OpenAI and Google both use start/end index mapping
4. **Async execution** - Research takes minutes, not seconds; all handle this differently
5. **Clean context delivery** - Pass processed learnings between steps, not raw HTML
6. **Error recovery** - Google's shared state manager; Anthropic's checkpoint resumption

### Key Tradeoffs

- **Speed vs Depth:** Perplexity (2-4 min) fastest but lower HLE; Google (5-10 min) highest HLE
- **Single vs Multi-Agent:** Multi-agent (Anthropic) gives 90% improvement but costs 15x more tokens
- **Index vs Live Crawl:** Grok uses pre-built index (faster); OpenAI/Perplexity do live crawling (fresher)
- **Model-specific vs Model-agnostic:** Perplexity routes to best model per task; others locked to their own models

### Citation Reliability

All systems have citation quality issues to varying degrees. Google has known problems with dead links and text mismatches. OpenAI notes lower hallucination rates than base ChatGPT but still recommends verification. Perplexity's strict "never say anything unretrieved" principle provides the strongest architectural guarantee. Anthropic uses a dedicated CitationAgent for post-processing verification.
