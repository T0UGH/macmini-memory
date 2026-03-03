# agent-cron Skill Design

**Date:** 2026-03-03

## Overview

A Claude Code skill bundled in the `agent-cron` GitHub repository, distributed as a marketplace plugin. Covers four user scenarios: create task, list tasks, run task, and setup auto-start.

## Repository Structure

```
agent-cron/
  .claude-plugin/
    plugin.json          # plugin metadata
    marketplace.json     # marketplace registry
  skills/
    agent-cron/
      SKILL.md           # single skill covering all 4 scenarios
  src/ ...               # existing CLI code (unchanged)
  package.json
  README.md
```

**Install command (users run once):**
```bash
/claude install marketplace https://github.com/T0UGH/agent-cron/raw/main/.claude-plugin/marketplace.json
```

## plugin.json

```json
{
  "name": "agent-cron",
  "description": "Claude Code skill for managing agent-cron scheduled tasks",
  "version": "0.1.0",
  "author": { "name": "T0UGH", "email": "tough.neu.edu@gmail.com" },
  "homepage": "https://github.com/T0UGH/agent-cron",
  "repository": "https://github.com/T0UGH/agent-cron",
  "license": "MIT",
  "keywords": ["agent-cron", "cron", "scheduler", "claude", "ai"]
}
```

## marketplace.json

```json
{
  "name": "agent-cron",
  "description": "Claude Code skill for managing agent-cron scheduled tasks",
  "owner": { "name": "T0UGH", "email": "tough.neu.edu@gmail.com" },
  "plugins": [
    {
      "name": "agent-cron",
      "description": "Claude Code skill for managing agent-cron scheduled tasks",
      "version": "0.1.0",
      "source": "./",
      "author": { "name": "T0UGH", "email": "tough.neu.edu@gmail.com" }
    }
  ]
}
```

## SKILL.md Design

### Frontmatter

```yaml
---
name: agent-cron
description: Use when user wants to manage agent-cron scheduled tasks: create a new scheduled task, list existing tasks, run a task immediately, or set up agent-cron as a macOS background service with auto-start on login. Triggers on phrases like "创建定时任务", "add a cron task", "列出任务", "list tasks", "run task", "立即运行", "开机自启", "setup agent-cron".
---
```

### Four Branches

#### Branch 1 — create

**Trigger:** User wants to create a new scheduled task.

**Flow:**
1. Infer task intent from user's natural language description
2. Ask for schedule frequency (e.g. "每天早9点", "工作日8点", "每小时") → convert to cron expression (timezone: Asia/Shanghai)
3. Ask for output channel:
   - `file` → ask for `outputDir` (default `./output`)
   - `feishu` → ask for webhook URL (or confirm using `FEISHU_WEBHOOK` env)
   - `github` → ask for `githubRepo` (owner/repo format), confirm token via `GITHUB_TOKEN` env
4. Polish user's description into a complete prompt body:
   - Include `{date}` placeholder where appropriate
   - End with: `如果没有值得关注的新内容，直接输出：HEARTBEAT_OK`
5. Infer slug from task name (kebab-case), write `./tasks/<slug>.md`
6. **Auto-check service:** Check if `~/Library/LaunchAgents/com.agent-cron.plist` exists:
   - **Not found** → Inform user "检测到尚未配置自启动，帮你自动配置" → execute setup flow inline (no separate trigger needed)
   - **Found** → Inform user "agent-cron 已在运行，新任务将在下次触发时执行"

#### Branch 2 — list

**Trigger:** User asks to see existing tasks.

**Flow:**
```bash
npx @t0u9h/agent-cron list
```

#### Branch 3 — run

**Trigger:** User wants to run a task immediately.

**Flow:**
- If slug specified by user: run directly
- If no slug: first run `list`, then ask which task to run
```bash
npx @t0u9h/agent-cron run [slug]
```

#### Branch 4 — setup

**Trigger:** User asks to configure auto-start, or triggered automatically after task creation when plist not found.

**Flow:**
1. Ask for tasks directory path (default: `./tasks`, current working directory)
2. Read `ANTHROPIC_API_KEY` from current environment
3. Write `~/Library/LaunchAgents/com.agent-cron.plist`:
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
     <key>Label</key>
     <string>com.agent-cron</string>
     <key>ProgramArguments</key>
     <array>
       <string>/usr/local/bin/npx</string>
       <string>@t0u9h/agent-cron</string>
       <string>start</string>
       <string>{tasksDir}</string>
     </array>
     <key>EnvironmentVariables</key>
     <dict>
       <key>ANTHROPIC_API_KEY</key>
       <string>{ANTHROPIC_API_KEY}</string>
     </dict>
     <key>WorkingDirectory</key>
     <string>{cwd}</string>
     <key>RunAtLoad</key>
     <true/>
     <key>KeepAlive</key>
     <true/>
     <key>StandardOutPath</key>
     <string>/tmp/agent-cron.log</string>
     <key>StandardErrorPath</key>
     <string>/tmp/agent-cron.error.log</string>
   </dict>
   </plist>
   ```
4. Run: `launchctl load ~/Library/LaunchAgents/com.agent-cron.plist`
5. Verify: `launchctl list | grep agent-cron`
6. Confirm to user: "agent-cron 已启动并配置开机自启，日志见 /tmp/agent-cron.log"

## Key Design Decisions

- **Single skill, four branches** — one trigger description covers all scenarios; Claude infers intent
- **create auto-triggers setup** — user never needs to manually run setup after creating first task
- **npx for list/run** — no global install required, always uses latest version
- **launchctl load = immediate + persistent** — no reboot required, takes effect instantly
- **HEARTBEAT_OK in all prompts** — prevents unnecessary output when no new content
- **Timezone: Asia/Shanghai** — hardcoded, consistent with CLI default
