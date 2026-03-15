#!/usr/bin/env python3
import json
import re
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

PHRASE_MAP = [
    ('Added support for', '新增对'),
    ('Added support to', '新增对'),
    ('Added support', '新增支持'),
    ('Added the ability to', '新增能力：'),
    ('Added a new', '新增'),
    ('Added', '新增'),
    ('Improved', '改进'),
    ('Fixed', '修复'),
    ('Fix', '修复'),
    ('Support', '支持'),
    ('Supports', '支持'),
    ('Refactor', '重构'),
    ('Refactored', '重构'),
    ('Restore', '恢复'),
    ('Restored', '恢复'),
    ('Remove', '移除'),
    ('Removed', '移除'),
    ('Hide', '隐藏'),
    ('Reorder', '重排'),
    ('Paginate', '分页处理'),
    ('Serialize', '序列化'),
    ('Scaffold', '搭建基础能力'),
    ('Filter', '过滤'),
    ('Synchronize', '同步'),
    ('Polish', '优化'),
    ('Avoid', '避免'),
    ('Increase', '提升'),
    ('Thank you to', '感谢'),
    ('Latest', '最新'),
]

WORD_MAP = [
    ('worktree', 'worktree'),
    ('sparse-checkout', '稀疏检出'),
    ('sparsePaths', 'sparsePaths'),
    ('session history', '会话历史'),
    ('text attachments', '文本附件'),
    ('server performance', '服务端性能'),
    ('git init', 'git init'),
    ('parallel subagents', '并行子代理'),
    ('subagents', '子代理'),
    ('LLM provider', 'LLM 提供商'),
    ('provider', '提供商'),
    ('sidebar', '侧边栏'),
    ('Desktop', '桌面端'),
    ('Core', '核心层'),
    ('TUI', '终端界面'),
    ('GitHub Action', 'GitHub Action'),
    ('plugin', '插件'),
    ('plugins', '插件'),
    ('terminal', '终端'),
    ('code review', '代码审查'),
    ('security', '安全'),
    ('documentation', '文档'),
    ('language server', '语言服务器'),
    ('browser', '浏览器'),
    ('workspace', '工作区'),
    ('workflow', '工作流'),
    ('session', '会话'),
    ('prompt', '提示词'),
    ('thinking mode', '思考模式'),
    ('diff', 'diff'),
    ('hook', 'hook'),
    ('hooks', 'hooks'),
]

PLUGIN_WORDS = [
    ('integration', '集成'),
    ('language server', '语言服务器'),
    ('code intelligence', '代码智能'),
    ('analysis', '分析'),
    ('browser', '浏览器'),
    ('performance', '性能'),
    ('network requests', '网络请求'),
    ('API', 'API'),
    ('deploy', '部署'),
    ('serverless', '无服务器'),
    ('database', '数据库'),
    ('project management', '项目管理'),
    ('documentation', '文档'),
    ('payment', '支付'),
    ('ads', '广告'),
    ('risk scoring', '风险评分'),
]


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f'command failed: {cmd}\nSTDERR:\n{p.stderr}')
    return p.stdout


def run_maybe(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def latest_release(repo):
    code, out, err = run_maybe(['gh', 'release', 'view', '-R', repo, '--json', 'name,tagName,publishedAt,url,body,isPrerelease'])
    if code != 0:
        return {'repo': repo, 'error': err.strip() or out.strip()}
    data = json.loads(out)
    data['repo'] = repo
    return data


def cleanup(s):
    s = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def to_cn_line(text):
    s = cleanup(text)
    for a, b in PHRASE_MAP:
        if s.startswith(a):
            s = b + s[len(a):]
            break
    for a, b in WORD_MAP:
        s = re.sub(re.escape(a), b, s, flags=re.I)
    return s


def summarize_release(item):
    if 'error' in item:
        return {'repo': item['repo'], 'error': item['error']}
    body = (item.get('body') or '').splitlines()
    bullets = []
    for line in body:
        s = line.strip()
        if s.startswith(('- ', '* ')):
            bullets.append(to_cn_line(s[2:].strip()))
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
                'description': old[k].get('description', '') or new[k].get('description', ''),
                'url': new[k].get('url', ''),
            })
    return {
        'added': [{'name': k, **new[k]} for k in added],
        'removed': [{'name': k, **old[k]} for k in removed],
        'changed': changed,
    }


def plugin_desc_cn(text):
    s = cleanup(text)
    for a, b in PLUGIN_WORDS:
        s = re.sub(re.escape(a), b, s, flags=re.I)
    if s and not re.search(r'[\u4e00-\u9fff]', s):
        s = '用途：' + s
    return s


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
        for item in search_repos(q, limit=6):
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


def repo_reason(item):
    q = item.get('matchedQuery', '')
    if 'worktree' in q:
        return '命中 worktree / 多任务协作方向'
    if 'subagent' in q:
        return '命中 subagent 方向'
    if 'terminal' in q:
        return '命中终端 coding agent 方向'
    if 'repo memory' in q:
        return '命中 repo memory / 上下文方向'
    if 'mcp' in q.lower() or 'acp' in q.lower():
        return '命中协议 / 工具接入方向'
    if 'agentic' in q or 'coding agent' in q:
        return '命中 coding agent 主查询'
    return '来自 coding agent 生态搜索'


def repo_desc_cn(text):
    s = cleanup(text)
    s = re.sub(r'AI', 'AI', s)
    for a, b in PLUGIN_WORDS + WORD_MAP:
        s = re.sub(re.escape(a), b, s, flags=re.I)
    if s and not re.search(r'[\u4e00-\u9fff]', s):
        s = '简介：' + s
    return s


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
        'language': 'zh-CN',
        'core': core,
        'plugins': plugin_diff,
        'discovery': discovery,
    }

    out_json = OUT_DIR / f'{now}.json'
    out_md = OUT_DIR / f'{now}.md'
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    lines = [f'# GitHub 日报试运行（{now}）', '', '## 核心仓库', '']
    for item in core:
        if 'error' in item:
            lines += [f"### {item['repo']}", f"- 抓取失败：{item['error']}", '']
            continue
        lines += [f"### {item['repo']} · {item.get('tag','')}", f"- 发布时间：{item.get('publishedAt','')}"]
        for hl in item.get('highlights', [])[:5]:
            lines.append(f'- {hl}')
        if item.get('url'):
            lines.append(f"- 链接：{item['url']}")
        lines.append('')

    lines += ['## 官方插件仓库（marketplace.json）', '']
    lines.append(f"- 新增：{len(plugin_diff['added'])}")
    lines.append(f"- 删除：{len(plugin_diff['removed'])}")
    lines.append(f"- 版本变化：{len(plugin_diff['changed'])}")
    if plugin_diff['added']:
        lines.append('### 新增插件')
        for item in plugin_diff['added'][:10]:
            lines.append(f"- {item['name']}：{plugin_desc_cn(item.get('description',''))}")
        lines.append('')
    if plugin_diff['removed']:
        lines.append('### 删除插件')
        for item in plugin_diff['removed'][:10]:
            lines.append(f"- {item['name']}：{plugin_desc_cn(item.get('description',''))}")
        lines.append('')
    if plugin_diff['changed']:
        lines.append('### 插件版本变化')
        for item in plugin_diff['changed'][:10]:
            lines.append(f"- {item['name']}：{item.get('from')} -> {item.get('to')}；{plugin_desc_cn(item.get('description',''))}")
        lines.append('')

    lines += ['## 新仓候选（10 个）', '']
    for idx, item in enumerate(discovery, start=1):
        lines.append(f"### {idx}. {item['fullName']}")
        lines.append(f"- 简介：{repo_desc_cn(item.get('description',''))}")
        lines.append(f"- 为什么值得看：{repo_reason(item)}")
        lines.append(f"- Stars：{item.get('stargazersCount')} | 来源查询：{item.get('matchedQuery')}")
        lines.append(f"- 链接：{item.get('url')}")
        lines.append('')

    out_md.write_text('\n'.join(lines))
    print(str(out_md))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)
