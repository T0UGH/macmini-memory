---
name: github-daily
description: Generate a GitHub daily brief for coding-agent ecosystem tracking. Use when the user wants the daily GitHub roundup, wants to track the fixed core repos (anthropics/claude-code, openclaw/openclaw, sst/opencode, zed-industries/zed, anthropics/claude-plugins-official), or wants 10 discovery candidates from the coding-agent ecosystem.
---

Run `scripts/run_github_daily.py` from this skill directory.

Behavior:
- Pull the latest release notes for 4 release-driven core repos.
- Diff `anthropics/claude-plugins-official` via `.claude-plugin/marketplace.json`.
- Generate 10 discovery candidates using GitHub search for coding-agent related terms.
- Write results to `runs/<timestamp>.md` and `runs/<timestamp>.json`.

When refining output:
- Prioritize `anthropics/claude-code` as the highest-signal repo.
- Keep Zed in the core brief, but do not use it as an expansion source for discovery.
- Keep discovery broad across the coding-agent ecosystem, not just Claude Code-specific repos.
- Prefer short, high-signal summaries over exhaustive dumps.
