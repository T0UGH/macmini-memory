# agent-cron Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build `agent-cron`, a standalone npm CLI that runs Claude Agent SDK tasks defined as `.md` files on a cron schedule, with pluggable output channels (file, GitHub, Feishu) and pluggable agent backends.

**Architecture:** A single TypeScript package with a `bin` entry (`agent-cron`). Tasks are `.md` files with YAML frontmatter. The runner dispatches to an `AgentRunner` (default: Claude Code with local skills enabled via `settingSources: ['user']`), then dispatches output to a channel registry. Both runners and channels implement a single-method interface for extensibility.

**Tech Stack:** TypeScript, Node.js ESM, `node-cron`, `gray-matter`, `@anthropic-ai/claude-agent-sdk`, `@octokit/rest`, `tsx` (dev)

---

## Project Layout (final state)

```
agent-cron/
  src/
    types.ts            # Task, OutputChannel, AgentRunner interfaces
    loader.ts           # loadTasks(dir) → Task[]
    runner.ts           # runTask(task): dispatch to agent + output channel
    agents/
      index.ts          # runners registry
      claude.ts         # ClaudeRunner (default, settingSources: ['user'])
    outputs/
      index.ts          # channels registry
      file.ts           # FileChannel
      github.ts         # GithubChannel
      feishu.ts         # FeishuChannel
    scheduler.ts        # start(tasks), runNow(tasks, slug?)
    cli.ts              # argv parsing → start | run | list
  tasks/
    example.md          # example task file
  .env.example
  package.json
  tsconfig.json
  README.md
```

---

### Task 1: Scaffold project

**Files:**
- Create: `agent-cron/package.json`
- Create: `agent-cron/tsconfig.json`
- Create: `agent-cron/.env.example`

**Step 1: Create the project directory**

```bash
mkdir -p /Users/haha/workspace/github/agent-cron/src/outputs
mkdir -p /Users/haha/workspace/github/agent-cron/src/agents
mkdir -p /Users/haha/workspace/github/agent-cron/tasks
cd /Users/haha/workspace/github/agent-cron
```

**Step 2: Write package.json**

```json
{
  "name": "agent-cron",
  "version": "0.1.0",
  "description": "Run Claude Agent SDK tasks on a cron schedule",
  "type": "module",
  "bin": {
    "agent-cron": "dist/cli.js"
  },
  "main": "dist/cli.js",
  "files": ["dist"],
  "scripts": {
    "build": "tsc",
    "dev": "node --import tsx/esm src/cli.ts",
    "start": "node dist/cli.js"
  },
  "dependencies": {
    "@anthropic-ai/claude-agent-sdk": "latest",
    "@octokit/rest": "^21.0.0",
    "dotenv": "^16.0.0",
    "gray-matter": "^4.0.3",
    "node-cron": "^3.0.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/node-cron": "^3.0.0",
    "tsx": "^4.0.0",
    "typescript": "^5.0.0"
  }
}
```

**Step 3: Write tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src"]
}
```

**Step 4: Write .env.example**

```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx

# Required for output: github (unless set in task frontmatter)
GITHUB_TOKEN=ghp_xxxxxxxxxxxx

# Required for output: feishu (unless set in task frontmatter)
FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx
```

**Step 5: Install dependencies**

```bash
cd /Users/haha/workspace/github/agent-cron
npm install
```

Expected: `node_modules/` created, no errors.

**Step 6: Commit**

```bash
cd /Users/haha/workspace/github/agent-cron
git init
git add package.json tsconfig.json .env.example
git commit -m "chore: scaffold agent-cron project"
```

---

### Task 2: Core types

**Files:**
- Create: `src/types.ts`

**Step 1: Write types.ts**

```typescript
export interface Task {
  slug: string           // filename without .md
  name: string
  cron: string
  output: string         // channel name: 'file' | 'github' | 'feishu'
  agent?: string         // agent runner name, default 'claude'
  skills?: boolean       // load local ~/.claude/ skills, default true
  prompt: string         // template body with {date} placeholder
  [key: string]: unknown // channel-specific frontmatter fields
}

export interface OutputChannel {
  send(result: string, task: Task): Promise<void>
}

export interface AgentRunner {
  run(prompt: string, task: Task): Promise<string>
}
```

**Step 2: Verify TypeScript compiles**

```bash
cd /Users/haha/workspace/github/agent-cron
npx tsc --noEmit
```

Expected: no errors.

**Step 3: Commit**

```bash
git add src/types.ts
git commit -m "feat: add core Task and OutputChannel types"
```

---

### Task 3: Task loader

**Files:**
- Create: `src/loader.ts`

**Step 1: Write loader.ts**

```typescript
import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import type { Task } from './types.js';

export function loadTasks(dir: string): Task[] {
  if (!fs.existsSync(dir)) {
    console.warn(`[agent-cron] tasks directory not found: ${dir}`);
    return [];
  }

  return fs
    .readdirSync(dir)
    .filter((f) => f.endsWith('.md'))
    .map((f) => {
      const filePath = path.join(dir, f);
      const raw = fs.readFileSync(filePath, 'utf-8');
      const { data, content } = matter(raw);
      const slug = f.replace(/\.md$/, '');

      if (!data.cron) {
        console.warn(`[agent-cron] missing cron in ${f}, skipping`);
        return null;
      }
      if (!data.output) {
        console.warn(`[agent-cron] missing output in ${f}, skipping`);
        return null;
      }

      return {
        slug,
        name: String(data.name ?? slug),
        cron: String(data.cron),
        output: String(data.output),
        prompt: content.trim(),
        ...data,
      } as Task;
    })
    .filter((t): t is Task => t !== null);
}
```

**Step 2: Verify TypeScript compiles**

```bash
npx tsc --noEmit
```

Expected: no errors.

**Step 3: Commit**

```bash
git add src/loader.ts
git commit -m "feat: add task loader (loadTasks from .md files)"
```

---

### Task 4: Output channels — file

**Files:**
- Create: `src/outputs/file.ts`

**Step 1: Write file.ts**

```typescript
import fs from 'fs';
import path from 'path';
import type { OutputChannel, Task } from '../types.js';

export class FileChannel implements OutputChannel {
  async send(result: string, task: Task): Promise<void> {
    const outputDir = String(task.outputDir ?? './output');
    fs.mkdirSync(outputDir, { recursive: true });
    const date = new Date().toISOString().split('T')[0];
    const filePath = path.join(outputDir, `${task.slug}-${date}.md`);
    fs.writeFileSync(filePath, result, 'utf-8');
    console.log(`[agent-cron] written to ${filePath}`);
  }
}
```

**Step 2: Compile check**

```bash
npx tsc --noEmit
```

**Step 3: Commit**

```bash
git add src/outputs/file.ts
git commit -m "feat: add FileChannel output"
```

---

### Task 5: Output channels — Feishu

**Files:**
- Create: `src/outputs/feishu.ts`

**Step 1: Write feishu.ts**

Feishu custom bot accepts `msg_type: "post"` with a content array. Markdown is converted: h1→title, h2/h3→bold line, `**text**`→bold style, `[text](url)`→link tag, list items→`•` prefix.

```typescript
import type { OutputChannel, Task } from '../types.js';

type FeishuInlineElement =
  | { tag: 'text'; text: string; style?: string[] }
  | { tag: 'a'; text: string; href: string };

type FeishuLine = FeishuInlineElement[];

function parseInline(raw: string): FeishuInlineElement[] {
  const elements: FeishuInlineElement[] = [];
  const re = /\[([^\]]+)\]\((https?:\/\/[^)]+)\)|\*\*([^*]+)\*\*/g;
  let last = 0;
  let m: RegExpExecArray | null;

  while ((m = re.exec(raw)) !== null) {
    if (m.index > last) {
      elements.push({ tag: 'text', text: raw.slice(last, m.index) });
    }
    if (m[1] && m[2]) {
      elements.push({ tag: 'a', text: m[1], href: m[2] });
    } else if (m[3]) {
      elements.push({ tag: 'text', text: m[3], style: ['bold'] });
    }
    last = re.lastIndex;
  }
  if (last < raw.length) {
    elements.push({ tag: 'text', text: raw.slice(last) });
  }
  return elements.length > 0 ? elements : [{ tag: 'text', text: raw }];
}

function markdownToFeishuPost(markdown: string): { title: string; content: FeishuLine[] } {
  const lines = markdown.split('\n');
  let title = '';
  const content: FeishuLine[] = [];

  for (const raw of lines) {
    const line = raw.trimEnd();
    if (/^#\s+/.test(line)) {
      if (!title) title = line.replace(/^#\s+/, '');
      continue;
    }
    if (/^#{2,3}\s+/.test(line)) {
      content.push([{ tag: 'text', text: line.replace(/^#{2,3}\s+/, ''), style: ['bold'] }]);
      continue;
    }
    if (/^---+$/.test(line) || line === '') {
      content.push([{ tag: 'text', text: '' }]);
      continue;
    }
    if (/^[-*]\s+/.test(line)) {
      content.push(parseInline(line.replace(/^[-*]\s+/, '• ')));
      continue;
    }
    content.push(parseInline(line));
  }

  return { title: title || 'agent-cron', content };
}

export class FeishuChannel implements OutputChannel {
  async send(result: string, task: Task): Promise<void> {
    const webhook =
      (task.feishuWebhook as string | undefined) ?? process.env.FEISHU_WEBHOOK;
    if (!webhook) {
      throw new Error(`[agent-cron] feishu: missing webhook for task "${task.name}". Set feishuWebhook in frontmatter or FEISHU_WEBHOOK env var.`);
    }

    const { title, content } = markdownToFeishuPost(result);
    const body = {
      msg_type: 'post',
      content: { post: { zh_cn: { title, content } } },
    };

    const res = await fetch(webhook, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      throw new Error(`[agent-cron] feishu: HTTP ${res.status} ${await res.text()}`);
    }
    const json = await res.json() as { code?: number; msg?: string };
    if (json.code !== 0) {
      throw new Error(`[agent-cron] feishu: API error code=${json.code} msg=${json.msg}`);
    }
    console.log(`[agent-cron] pushed to Feishu (${task.name})`);
  }
}
```

**Step 2: Compile check**

```bash
npx tsc --noEmit
```

**Step 3: Commit**

```bash
git add src/outputs/feishu.ts
git commit -m "feat: add FeishuChannel output (post rich text)"
```

---

### Task 6: Output channels — GitHub

**Files:**
- Create: `src/outputs/github.ts`

**Step 1: Write github.ts**

Uses GitHub Contents API via `@octokit/rest`. Creates or updates a file in the target repo. No local git required.

```typescript
import { Octokit } from '@octokit/rest';
import type { OutputChannel, Task } from '../types.js';

export class GithubChannel implements OutputChannel {
  async send(result: string, task: Task): Promise<void> {
    const repo = task.githubRepo as string | undefined;
    if (!repo) {
      throw new Error(`[agent-cron] github: missing githubRepo for task "${task.name}"`);
    }

    const [owner, repoName] = repo.split('/');
    if (!owner || !repoName) {
      throw new Error(`[agent-cron] github: invalid githubRepo format "${repo}", expected "owner/repo"`);
    }

    const token =
      (task.githubToken as string | undefined) ?? process.env.GITHUB_TOKEN;
    if (!token) {
      throw new Error(`[agent-cron] github: missing token for task "${task.name}". Set githubToken in frontmatter or GITHUB_TOKEN env var.`);
    }

    const branch = String(task.githubBranch ?? 'main');
    const dir = task.githubDir ? String(task.githubDir) : '';
    const date = new Date().toISOString().split('T')[0];
    const fileName = `${task.slug}-${date}.md`;
    const filePath = dir ? `${dir}/${fileName}` : fileName;

    const octokit = new Octokit({ auth: token });
    const content = Buffer.from(result, 'utf-8').toString('base64');
    const message = `chore: ${task.name} ${date}`;

    // Check if file exists (to get sha for update)
    let sha: string | undefined;
    try {
      const { data } = await octokit.repos.getContent({ owner, repo: repoName, path: filePath, ref: branch });
      if (!Array.isArray(data) && data.type === 'file') sha = data.sha;
    } catch {
      // file doesn't exist yet, sha stays undefined
    }

    await octokit.repos.createOrUpdateFileContents({
      owner,
      repo: repoName,
      path: filePath,
      message,
      content,
      branch,
      ...(sha ? { sha } : {}),
    });

    console.log(`[agent-cron] pushed to GitHub ${repo}/${filePath} (${task.name})`);
  }
}
```

**Step 2: Compile check**

```bash
npx tsc --noEmit
```

**Step 3: Commit**

```bash
git add src/outputs/github.ts
git commit -m "feat: add GithubChannel output (Contents API)"
```

---

### Task 7: Channel registry

**Files:**
- Create: `src/outputs/index.ts`

**Step 1: Write outputs/index.ts**

```typescript
import type { OutputChannel } from '../types.js';
import { FileChannel } from './file.js';
import { FeishuChannel } from './feishu.js';
import { GithubChannel } from './github.js';

export const channels: Record<string, OutputChannel> = {
  file:   new FileChannel(),
  feishu: new FeishuChannel(),
  github: new GithubChannel(),
};
```

**Step 2: Compile check**

```bash
npx tsc --noEmit
```

**Step 3: Commit**

```bash
git add src/outputs/index.ts
git commit -m "feat: add output channel registry"
```

---

### Task 8: Agent runner — Claude

**Files:**
- Create: `src/agents/claude.ts`
- Create: `src/agents/index.ts`

**Step 1: Write agents/claude.ts**

`ClaudeRunner` calls `query()` with `settingSources: ['user']` by default so locally installed Claude Code skills (`~/.claude/plugins/`, `~/.claude/skills/`) are available to the agent. Set `skills: false` in frontmatter to disable.

```typescript
import { query } from '@anthropic-ai/claude-agent-sdk';
import type { AgentRunner, Task } from '../types.js';

export class ClaudeRunner implements AgentRunner {
  async run(prompt: string, task: Task): Promise<string> {
    const loadSkills = task.skills !== false;
    let result = '';

    const q = query({
      prompt,
      options: {
        cwd: process.cwd(),
        permissionMode: 'bypassPermissions',
        ...(loadSkills ? { settingSources: ['user'] } : {}),
      },
    });

    for await (const message of q) {
      if (message.type === 'result' && 'result' in message && message.result) {
        result = message.result;
      }
    }

    return result;
  }
}
```

**Step 2: Write agents/index.ts**

```typescript
import type { AgentRunner } from '../types.js';
import { ClaudeRunner } from './claude.js';

export const runners: Record<string, AgentRunner> = {
  claude: new ClaudeRunner(),
  // future: codex, opencode, copilot...
};
```

**Step 3: Compile check**

```bash
npx tsc --noEmit
```

**Step 4: Commit**

```bash
git add src/agents/claude.ts src/agents/index.ts
git commit -m "feat: add ClaudeRunner with local skills support (settingSources)"
```

---

### Task 9: Runner (task orchestrator)

**Files:**
- Create: `src/runner.ts`

**Step 1: Write runner.ts**

```typescript
import type { Task } from './types.js';
import { runners } from './agents/index.js';
import { channels } from './outputs/index.js';

function buildPrompt(template: string): string {
  const date = new Date().toLocaleDateString('zh-CN');
  return template.replace(/\{date\}/g, date);
}

export async function runTask(task: Task): Promise<void> {
  console.log(`[agent-cron] starting: ${task.name} (${new Date().toLocaleString('zh-CN')})`);

  const agentName = String(task.agent ?? 'claude');
  const agentRunner = runners[agentName];
  if (!agentRunner) {
    console.error(`[agent-cron] unknown agent: "${agentName}" (${task.name})`);
    return;
  }

  const prompt = buildPrompt(task.prompt);
  let result = '';

  try {
    result = await agentRunner.run(prompt, task);
  } catch (err) {
    console.error(`[agent-cron] agent error (${task.name}):`, err);
    return;
  }

  if (!result) {
    console.error(`[agent-cron] no result returned (${task.name})`);
    return;
  }

  if (result.trim() === 'HEARTBEAT_OK') {
    console.log(`[agent-cron] OK — no new content (${task.name})`);
    return;
  }

  const channel = channels[task.output];
  if (!channel) {
    console.error(`[agent-cron] unknown output channel: "${task.output}" (${task.name})`);
    return;
  }

  try {
    await channel.send(result, task);
  } catch (err) {
    console.error(`[agent-cron] output error (${task.name}):`, err);
  }
}
```

**Step 2: Compile check**

```bash
npx tsc --noEmit
```

**Step 3: Commit**

```bash
git add src/runner.ts
git commit -m "feat: add task runner with agent dispatch and HEARTBEAT_OK protocol"
```

---

### Task 10: Scheduler

**Files:**
- Create: `src/scheduler.ts`

**Step 1: Write scheduler.ts**

```typescript
import cron from 'node-cron';
import type { Task } from './types.js';
import { runTask } from './runner.js';

const TIMEZONE = 'Asia/Shanghai';

export function startScheduler(tasks: Task[]): void {
  if (tasks.length === 0) {
    console.warn('[agent-cron] no tasks found, nothing to schedule');
    return;
  }

  for (const task of tasks) {
    if (!cron.validate(task.cron)) {
      console.warn(`[agent-cron] invalid cron expression "${task.cron}" in task "${task.name}", skipping`);
      continue;
    }
    cron.schedule(task.cron, () => runTask(task), { timezone: TIMEZONE });
    console.log(`[agent-cron] scheduled: ${task.name} → ${task.cron} (${TIMEZONE})`);
  }

  console.log(`[agent-cron] scheduler running with ${tasks.length} task(s). Press Ctrl+C to stop.`);
}

export async function runNow(tasks: Task[], slug?: string): Promise<void> {
  const targets = slug
    ? tasks.filter((t) => t.slug === slug)
    : tasks;

  if (targets.length === 0) {
    console.error(slug
      ? `[agent-cron] task not found: "${slug}"`
      : '[agent-cron] no tasks to run');
    process.exit(1);
  }

  for (const task of targets) {
    await runTask(task);
  }
}

export function listTasks(tasks: Task[]): void {
  if (tasks.length === 0) {
    console.log('[agent-cron] no tasks found');
    return;
  }
  console.log('\nRegistered tasks:\n');
  for (const task of tasks) {
    console.log(`  ${task.slug}`);
    console.log(`    name:   ${task.name}`);
    console.log(`    cron:   ${task.cron}`);
    console.log(`    output: ${task.output}`);
    console.log('');
  }
}
```

**Step 2: Compile check**

```bash
npx tsc --noEmit
```

**Step 3: Commit**

```bash
git add src/scheduler.ts
git commit -m "feat: add scheduler (start, runNow, list)"
```

---

### Task 11: CLI entry point

**Files:**
- Create: `src/cli.ts`

**Step 1: Write cli.ts**

```typescript
import 'dotenv/config';
import path from 'path';
import { loadTasks } from './loader.js';
import { startScheduler, runNow, listTasks } from './scheduler.js';

const args = process.argv.slice(2);
const command = args[0];

// Resolve tasks directory: default ./tasks, or explicit argument after command
const dirArg = args[1] && !args[1].startsWith('-') && command !== 'run'
  ? args[1]
  : undefined;
const tasksDir = path.resolve(dirArg ?? './tasks');

const tasks = loadTasks(tasksDir);

switch (command) {
  case 'start':
    startScheduler(tasks);
    break;

  case 'run': {
    // agent-cron run [slug]
    const slug = args[1] && !args[1].startsWith('-') ? args[1] : undefined;
    await runNow(tasks, slug);
    break;
  }

  case 'list':
    listTasks(tasks);
    break;

  default:
    console.log(`
agent-cron — run Claude Agent SDK tasks on a cron schedule

Usage:
  agent-cron start [dir]        Start scheduler (default dir: ./tasks)
  agent-cron run [slug]         Run all tasks or one by slug immediately
  agent-cron list               List all registered tasks

Options:
  dir     Path to tasks directory (default: ./tasks)
  slug    Task filename without .md extension
`);
    process.exit(command ? 1 : 0);
}
```

**Step 2: Compile check**

```bash
npx tsc --noEmit
```

**Step 3: Commit**

```bash
git add src/cli.ts
git commit -m "feat: add CLI entry point (start | run | list)"
```

---

### Task 12: Example task file and README

**Files:**
- Create: `tasks/example.md`
- Create: `README.md`

**Step 1: Write tasks/example.md**

```markdown
---
name: Example Task
cron: "0 9 * * *"
output: file
outputDir: ./output
---

Today is {date}.

Search for the latest news about AI coding tools and summarize in 3 bullet points.

If there is nothing interesting to report, output exactly: HEARTBEAT_OK
```

**Step 2: Write README.md**

```markdown
# agent-cron

Run Claude Agent SDK tasks on a cron schedule. Tasks are defined as `.md` files.

## Install

\`\`\`bash
npm install -g agent-cron
# or use npx
npx agent-cron list
\`\`\`

## Usage

\`\`\`bash
agent-cron start              # start scheduler (reads ./tasks/)
agent-cron start ./my-tasks   # specify tasks directory
agent-cron run                # run all tasks now
agent-cron run daily-news     # run one task by slug
agent-cron list               # list all tasks
\`\`\`

## Task File Format

Create `.md` files in your `tasks/` directory:

\`\`\`markdown
---
name: Daily AI News
cron: "0 9 * * *"
output: feishu
feishuWebhook: https://open.feishu.cn/open-apis/bot/v2/hook/xxx
---

Today is {date}. Search for the latest AI news and summarize.

If nothing new, output exactly: HEARTBEAT_OK
\`\`\`

## Output Channels

| Channel  | Required config |
|----------|----------------|
| `file`   | `outputDir` (default `./output`) |
| `feishu` | `feishuWebhook` or `FEISHU_WEBHOOK` env |
| `github` | `githubRepo`, `githubToken` or `GITHUB_TOKEN` env |

## Environment Variables

\`\`\`
ANTHROPIC_API_KEY=      # required
GITHUB_TOKEN=           # for output: github
FEISHU_WEBHOOK=         # for output: feishu
\`\`\`
```

**Step 3: Commit**

```bash
git add tasks/example.md README.md
git commit -m "docs: add example task and README"
```

---

### Task 13: Build and smoke test

**Step 1: Build**

```bash
cd /Users/haha/workspace/github/agent-cron
npm run build
```

Expected: `dist/` directory created with `cli.js` and all output files. No TypeScript errors.

**Step 2: Smoke test — list**

```bash
node dist/cli.js list
```

Expected: prints the example task (name, cron, output).

**Step 3: Smoke test — run with file output**

```bash
ANTHROPIC_API_KEY=<your-key> node dist/cli.js run example
```

Expected: agent runs, result written to `./output/example-YYYY-MM-DD.md`.

**Step 4: Final commit**

```bash
git add dist/
git commit -m "build: add compiled output"
```

---

## Summary

| Task | What it builds |
|------|---------------|
| 1 | Project scaffold, package.json, tsconfig |
| 2 | Core types (Task, OutputChannel) |
| 3 | Task loader (loadTasks from .md files) |
| 4 | FileChannel |
| 5 | FeishuChannel (Markdown → rich text) |
| 6 | GithubChannel (Contents API) |
| 7 | Channel registry |
| 8 | Agent runner (ClaudeRunner + runners registry) |
| 9 | Runner (agent dispatch + HEARTBEAT_OK protocol) |
| 10 | Scheduler (start, runNow, list) |
| 11 | CLI entry point |
| 12 | Example task + README |
| 13 | Build + smoke test |
