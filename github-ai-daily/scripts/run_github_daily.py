#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path('/Users/haha/.openclaw/workspace/github-daily')
STATE_DIR = ROOT / 'state'
OUT_DIR = ROOT / 'runs'
STATE_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

CORE_RELEASE_REPOS = [
    'anthropics/claude-code',
    'openclaw/openclaw',
    'sst/opencode',
    'zed-industries/zed',
]
PLUGIN_REPO = 'anthropics/claude-plugins-official'
PLUGIN_STATE = STATE_DIR / 'claude_plugins_marketplace.json'

DISCOVERY_QUERIES = [
    'coding agent',
    'agentic coding',
    'terminal coding agent',
    'repo memory agent',
    'subagent coding',
    'worktree coding agent',
    'MCP server coding',
    'ACP coding agent',
]


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f'command failed: {cmd}\nSTDERR:\n{p.stderr}')
    return p.stdout


def run_maybe(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def gh_json(args):
    return json.loads(run(['gh', *args]))


def latest_release(repo):
    code, out, err = run_maybe(['gh', 'release', 'view', '-R', repo, '--json', 'name,tagName,publishedAt,url,body,isPrerelease'])
    if code != 0:
        return {'repo': repo, 'error': err.strip() or out.strip()}
    data = json.loads(out)
    data['repo'] = repo
    return data


def summarize_release(item):
    if 'error' in item:
        return {'repo': item['repo'], 'error': item['error']}
    body = (item.get('body') or '').splitlines()
    bullets = []
    for line in body:
        s = line.strip()
        if s.startswith(('- ', '* ')):
            bullets.append(s[2:].strip())
        if len(bullets) >= 5:
            break
    return {
        'repo': item['repo'],
        'tag': item.get('tagName'),
        'publishedAt': item.get('publishedAt'),
        'url': item.get('url'),
        'highlights': bullets,
    }


def fetch_marketplace():
    txt = run(['gh', 'api', f'repos/{PLUGIN_REPO}/contents/.claude-plugin/marketplace.json', '--jq', '.content'])
    raw = subprocess.run(['base64', '-d'], input=txt, capture_output=True, text=True).stdout
    data = json.loads(raw)
    items = data.get('plugins') if isinstance(data, dict) else None
    if not isinstance(items, list):
        items = data.get('items', []) if isinstance(data, dict) else []
    normalized = {}
    for item in items:
        name = item.get('name') or item.get('id') or item.get('slug')
        if not name:
            continue
        normalized[name] = {
            'version': item.get('version') or item.get('latestVersion'),
            'description': item.get('description') or item.get('summary') or item.get('shortDescription') or '',
            'url': item.get('homepage') or item.get('url') or item.get('repository') or '',
        }
    return normalized


def diff_marketplace(old, new):
    old_keys = set(old)
    new_keys = set(new)
    added = sorted(new_keys - old_keys)
    removed = sorted(old_keys - new_keys)
    changed = []
    for k in sorted(old_keys & new_keys):
        if (old[k].get('version') or '') != (new[k].get('version') or ''):
            changed.append({
                'name': k,
                'from': old[k].get('version'),
                'to': new[k].get('version'),
                'description': new[k].get('description', ''),
                'url': new[k].get('url', ''),
            })
    return {
        'added': [{ 'name': k, **new[k]} for k in added],
        'removed': [{ 'name': k, **old[k]} for k in removed],
        'changed': changed,
    }


def search_repos(query, limit=5):
    code, out, err = run_maybe([
        'gh', 'search', 'repos', query,
        '--sort', 'updated', '--order', 'desc', '--limit', str(limit),
        '--json', 'fullName,description,url,updatedAt,stargazersCount'
    ])
    if code != 0:
        return []
    try:
        return json.loads(out)
    except Exception:
        return []


def discover(limit=10):
    seen = set(r.lower() for r in CORE_RELEASE_REPOS + [PLUGIN_REPO])
    picks = []
    for q in DISCOVERY_QUERIES:
        for item in search_repos(q, limit=4):
            name = item['fullName']
            low = name.lower()
            text = ((item.get('description') or '') + ' ' + name).lower()
            if low in seen:
                continue
            if not any(k in text for k in ['agent', 'coding', 'code', 'mcp', 'acp', 'worktree', 'repo', 'terminal', 'plugin']):
                continue
            seen.add(low)
            item['matchedQuery'] = q
            picks.append(item)
            if len(picks) >= limit:
                return picks
    return picks[:limit]


def main():
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    core = [summarize_release(latest_release(repo)) for repo in CORE_RELEASE_REPOS]

    current_market = fetch_marketplace()
    previous_market = {}
    if PLUGIN_STATE.exists():
        previous_market = json.loads(PLUGIN_STATE.read_text())
    plugin_diff = diff_marketplace(previous_market, current_market)
    PLUGIN_STATE.write_text(json.dumps(current_market, ensure_ascii=False, indent=2))

    discovery = discover(limit=10)

    result = {
        'generatedAt': now,
        'core': core,
        'plugins': plugin_diff,
        'discovery': discovery,
    }

    out_json = OUT_DIR / f'{now}.json'
    out_md = OUT_DIR / f'{now}.md'
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    lines = [f'# GitHub Daily Trial ({now})', '', '## Core repos', '']
    for item in core:
        if 'error' in item:
            lines += [f"### {item['repo']}", f"- error: {item['error']}", '']
            continue
        lines += [f"### {item['repo']} · {item.get('tag','')}", f"- published: {item.get('publishedAt','')}"]
        for hl in item.get('highlights', [])[:5]:
            lines.append(f'- {hl}')
        if item.get('url'):
            lines.append(f"- url: {item['url']}")
        lines.append('')

    lines += ['## Claude plugins marketplace', '']
    lines.append(f"- added: {len(plugin_diff['added'])}")
    lines.append(f"- removed: {len(plugin_diff['removed'])}")
    lines.append(f"- version changes: {len(plugin_diff['changed'])}")
    for bucket in ['added', 'removed', 'changed']:
        items = plugin_diff[bucket][:10]
        if not items:
            continue
        lines.append(f'### {bucket}')
        for item in items:
            if bucket == 'changed':
                lines.append(f"- {item['name']}: {item.get('from')} -> {item.get('to')}")
            else:
                desc = item.get('description', '')
                lines.append(f"- {item['name']}: {desc}")
        lines.append('')

    lines += ['## Discovery (10 candidates)', '']
    for item in discovery:
        lines.append(f"- {item['fullName']} — {item.get('description','')} | stars={item.get('stargazersCount')} | matched={item.get('matchedQuery')}")
    lines.append('')

    out_md.write_text('\n'.join(lines))
    print(str(out_md))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)
