# agent-cron CLI Design

**Date:** 2026-03-03

## Overview

`agent-cron` is a CLI tool published to npm that runs Claude Agent SDK tasks on a cron schedule. Tasks are defined as `.md` files with YAML frontmatter. The tool is independent of any specific project (not tied to ai-news-bot).

```bash
npx agent-cron start              # start scheduler, watches ./tasks/
npx agent-cron start ./my-tasks   # specify tasks directory
npx agent-cron run                # run all tasks immediately
npx agent-cron run daily-ai-news  # run one task by slug (filename without .md)
npx agent-cron list               # list all tasks with next run time
```

## Task File Format

Tasks live in a directory (default: `./tasks/`). Each task is a `.md` file:

```markdown
---
name: Daily AI News          # display name
cron: "0 9 * * *"            # cron expression (Asia/Shanghai timezone)
output: feishu               # file | github | feishu

# output: file
outputDir: ./output          # optional, default ./output

# output: github
githubRepo: owner/repo       # required
githubBranch: main           # optional, default main
githubDir: daily             # optional, default repo root
githubToken: ghp_xxx         # optional, falls back to GITHUB_TOKEN env var

# output: feishu
feishuWebhook: https://open.feishu.cn/open-apis/bot/v2/hook/xxx
# optional, falls back to FEISHU_WEBHOOK env var
---

Today is {date}. Search for the latest AI news...
```

**Frontmatter fields:**

| Field | Required | Default | Notes |
|-------|----------|---------|-------|
| `name` | no | filename slug | display name |
| `cron` | yes | — | standard cron expression |
| `output` | yes | — | `file`, `github`, or `feishu` |
| `outputDir` | no | `./output` | for `output: file` |
| `githubRepo` | if github | — | `owner/repo` format |
| `githubBranch` | no | `main` | for `output: github` |
| `githubDir` | no | `` (root) | subdirectory in repo |
| `githubToken` | no | `GITHUB_TOKEN` env | for `output: github` |
| `feishuWebhook` | no | `FEISHU_WEBHOOK` env | for `output: feishu` |

**Prompt template variables:**
- `{date}` — replaced with today's date (locale: zh-CN)

## Output Behavior

**`file`** — writes `{outputDir}/{slug}-{YYYY-MM-DD}.md`

**`github`** — uses GitHub Contents API to create/update `{githubDir}/{slug}-{YYYY-MM-DD}.md` in the specified repo/branch. No local git required.

**`feishu`** — POST to webhook with `msg_type: post` rich text. Markdown is converted: h1→title, h2/h3→bold, `**bold**`→bold style, `[text](url)`→link, list items→`•` prefix.

**HEARTBEAT_OK protocol** — if the agent returns exactly `HEARTBEAT_OK`, the output step is skipped silently. Useful for tasks that only push when there's new content.

## Project Structure

```
agent-cron/
  src/
    cli.ts          # entry point: parse argv → start | run | list
    loader.ts       # loadTasks(dir: string): Task[]
    runner.ts       # runTask(task: Task): Promise<void>
    outputs/
      file.ts       # write local file
      github.ts     # GitHub Contents API
      feishu.ts     # Feishu webhook (post rich text)
  package.json      # bin: { "agent-cron": "dist/cli.js" }
  tsconfig.json
```

## Output Channel Architecture

Output channels are pluggable via a common interface. Adding a new channel (Slack, Telegram, Discord, etc.) requires only implementing the interface and registering it.

```typescript
// Every output channel implements this interface
interface OutputChannel {
  send(result: string, task: Task): Promise<void>
}

// Built-in channels registry — add new channels here
const channels: Record<string, OutputChannel> = {
  file:   new FileChannel(),
  github: new GithubChannel(),
  feishu: new FeishuChannel(),
  // future: slack, telegram, discord, webhook, ...
}

// runner.ts dispatch
async function dispatch(result: string, task: Task): Promise<void> {
  const channel = channels[task.output]
  if (!channel) throw new Error(`Unknown output: ${task.output}`)
  await channel.send(result, task)
}
```

Each channel reads its own config from the `task` object (which carries all frontmatter fields). Channel-specific frontmatter fields are namespaced by convention: `feishuWebhook`, `githubRepo`, etc.

## Core Types

```typescript
interface Task {
  slug: string           // filename without .md
  name: string
  cron: string
  output: string         // channel name: 'file' | 'github' | 'feishu' | ...
  prompt: string         // template body, {date} substituted at runtime
  // channel-specific config (all optional, channels read what they need)
  [key: string]: unknown
}

interface OutputChannel {
  send(result: string, task: Task): Promise<void>
}
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `@anthropic-ai/claude-agent-sdk` | run Claude Agent tasks |
| `node-cron` | cron scheduling |
| `gray-matter` | parse YAML frontmatter |
| `@octokit/rest` | GitHub Contents API |

## Environment Variables

```
ANTHROPIC_API_KEY=      # required
GITHUB_TOKEN=           # required for output: github (unless set in frontmatter)
FEISHU_WEBHOOK=         # required for output: feishu (unless set in frontmatter)
```

## Agent Runner Architecture

Agent backends are pluggable via a common interface. Currently only Claude Code is implemented, but the interface is designed to support Codex, OpenCode, Copilot, etc.

```typescript
interface AgentRunner {
  run(prompt: string, task: Task): Promise<string>
}

// Built-in runners registry
const runners: Record<string, AgentRunner> = {
  claude: new ClaudeRunner(),
  // future: codex, opencode, copilot...
}
```

Task files can specify `agent:` frontmatter (defaults to `claude`):
```yaml
agent: claude    # optional, default
```

**ClaudeRunner** uses `@anthropic-ai/claude-agent-sdk` `query()` with:
- `permissionMode: 'bypassPermissions'` — required for unattended execution
- `settingSources: ['user']` — loads skills from `~/.claude/` by default
- `cwd: process.cwd()`

Tasks can opt out of local skills:
```yaml
skills: false    # disable loading ~/.claude/ skills for this task
```

## Local Skills Support

By default, all tasks load the user's locally installed Claude Code skills (`~/.claude/plugins/`, `~/.claude/skills/`). This allows tasks to use any skill installed on the machine (e.g., `memory`, `agent-browser`, etc.).

To disable for a specific task (isolation/security):
```yaml
skills: false
```

## File Structure (updated)

```
agent-cron/
  src/
    types.ts            # Task, OutputChannel, AgentRunner interfaces
    loader.ts           # loadTasks(dir) → Task[]
    runner.ts           # runTask(task), dispatch to agent + output channel
    agents/
      index.ts          # runners registry
      claude.ts         # ClaudeRunner (default)
    outputs/
      index.ts          # channels registry
      file.ts           # FileChannel
      github.ts         # GithubChannel
      feishu.ts         # FeishuChannel
    scheduler.ts        # start(tasks), runNow(tasks, slug?)
    cli.ts              # argv parsing → start | run | list
  tasks/
    example.md
  .env.example
  package.json
  tsconfig.json
  README.md
```

## Decisions Not Made

- **Timezone**: hardcoded to `Asia/Shanghai` (can add `timezone` frontmatter field later)
- **Concurrency**: tasks run sequentially if triggered at the same time (simple, avoids API rate issues)
- **Error handling**: log error, continue to next task (no retry, no circuit breaker in v1)
