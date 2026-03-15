#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path('/Users/haha/.openclaw/workspace/github-daily')
CONFIG = json.loads((ROOT / 'config.json').read_text())
STATE_DIR = ROOT / 'state'
OUT_DIR = ROOT / 'runs'
STATE_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

CORE_RELEASE_REPOS = CONFIG['core_release_repos']
PLUGIN_REPO = CONFIG['plugin_repo']
PLUGIN_STATE = ROOT / CONFIG['plugin_state_file']
DISCOVERY_QUERIES = CONFIG['discovery_queries']
MIN_STARS = CONFIG['min_stars']
DISCOVERY_COUNT = CONFIG['discovery_count']


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
    s = re.sub(r'\(#\d+\)', '', s)
    s = re.sub(r'https?://\S+', '', s)
    s = re.sub(r'\s+', ' ', s).strip(' -')
    return s


def format_ts(ts):
    if not ts:
        return ''
    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
    bj = dt.astimezone(timezone(timedelta(hours=8)))
    return bj.strftime('%Y-%m-%d %H:%M')


def bullet_lines(body):
    out = []
    for line in (body or '').splitlines():
        s = line.strip()
        if s.startswith(('- ', '* ')):
            out.append(cleanup(s[2:].strip()))
    return out


def first_match(lines, keywords):
    for s in lines:
        low = s.lower()
        if all(k.lower() in low for k in keywords):
            return s
    return None


def any_match(lines, keywords):
    for s in lines:
        low = s.lower()
        if any(k.lower() in low for k in keywords):
            return s
    return None


def summarize_claude_code(lines):
    out = []
    if first_match(lines, ['mcp', 'structured input']) or first_match(lines, ['mcp', 'interactive']):
        out.append('新增 MCP 交互式补充输入能力：MCP 服务可以在任务进行中通过表单或网页让用户补充结构化信息。')
    if first_match(lines, ['elicitation']) and first_match(lines, ['elicitationresult']):
        out.append('新增 `Elicitation` / `ElicitationResult` hooks：可以在结果回传前拦截或改写这一步交互。')
    if first_match(lines, ['--name']) or first_match(lines, ['display name']):
        out.append('新增 `-n / --name` 参数：启动会话时可以直接设置显示名称。')
    if first_match(lines, ['sparsepaths']) or first_match(lines, ['sparse-checkout']):
        out.append('`claude --worktree` 新增 `worktree.sparsePaths`：在大型 monorepo 里可以只检出需要的目录，减小 worktree 体积。')
    if first_match(lines, ['postcompact']):
        out.append('新增 `PostCompact` hook：上下文压缩完成后会触发新的后置 hook。')
    if not out:
        out = ['本次 release 有多项 CLI、hook 和 worktree 相关改进，整体方向仍然是增强 MCP、会话管理和大型仓库下的可用性。']
    return out[:5]


def summarize_openclaw(lines):
    out = []
    if first_match(lines, ['recover the broken']) or first_match(lines, ['tag/release path']):
        out.append('这次发布主要是在修复上一版损坏的 tag / release 路径，属于发布链路补丁。')
    if first_match(lines, ['npm version is still']):
        out.append('npm 版本号仍然是 `2026.3.13`，`-1` 只体现在 Git tag 和 GitHub Release 上。')
    if first_match(lines, ['compaction']):
        out.append('修复 compaction 的后置校验：压缩后会按完整会话 token 数来做 sanity check。')
    if first_match(lines, ['telegram']) and first_match(lines, ['ssrf']):
        out.append('修复 Telegram 媒体传输相关的安全策略问题，和 SSRF 防护链路有关。')
    if not out:
        out = ['这版 OpenClaw 以稳定性修复为主，重点不在新功能，而在发布链路和安全/校验细节。']
    return out[:5]


def summarize_opencode(lines):
    out = []
    if first_match(lines, ['effect-to-zod']) or first_match(lines, ['schema conversion']):
        out.append('补上 effect-to-zod 的 schema conversion 基础能力，偏底层类型/结构转换。')
    if first_match(lines, ['bun installations']):
        out.append('为 Bun 安装场景补了配置序列化处理，减少安装链路里的环境问题。')
    if first_match(lines, ['text attachments']):
        out.append('应用侧新增文本附件支持，输入材料的形态更丰富了。')
    if first_match(lines, ['session history']) and first_match(lines, ['performance']):
        out.append('会话历史改成分页加载，重点是提升服务端性能。')
    if first_match(lines, ['git init']) and first_match(lines, ['sessions lost']):
        out.append('修复在已有项目里执行 `git init` 后会话丢失的问题。')
    if not out:
        out = ['这版 OpenCode 以底层能力补强和会话稳定性修复为主，同时增强了 app 侧输入能力。']
    return out[:5]


def summarize_zed(lines):
    out = []
    if first_match(lines, ['spawn_agent']) or first_match(lines, ['subagents']):
        out.append('Zed Agent 新增 `spawn_agent`：可以并行调度子代理，提升多任务处理和上下文管理能力。')
    if first_match(lines, ['gpt-5.3-codex']) and first_match(lines, ['openai provider']):
        out.append('OpenAI provider 新增对 GPT-5.3-Codex 自带 Key 模式的支持。')
    if first_match(lines, ['vercel ai gateway']):
        out.append('Zed 新增 Vercel AI Gateway 作为 LLM 提供商。')
    if first_match(lines, ['jump to a file from a diff']) or first_match(lines, ['open excerpts']):
        out.append('在 agent 对话里，可以直接从 diff 跳回对应文件，减少来回切换。')
    if first_match(lines, ['draft prompts']) or first_match(lines, ['thinking mode toggle']) or first_match(lines, ['thread history']):
        out.append('Agent 线程体验继续加强：草稿提示词、思考模式等状态的持久化更完整了。')
    if not out:
        out = ['这版 Zed 主要在继续打磨 Agent 工作流、提供商接入和线程体验。']
    return out[:5]


def summarize_release(item):
    if 'error' in item:
        return {'repo': item['repo'], 'error': item['error']}
    repo = item['repo']
    lines = bullet_lines(item.get('body') or '')
    if repo == 'anthropics/claude-code':
        highlights = summarize_claude_code(lines)
    elif repo == 'openclaw/openclaw':
        highlights = summarize_openclaw(lines)
    elif repo == 'sst/opencode':
        highlights = summarize_opencode(lines)
    elif repo == 'zed-industries/zed':
        highlights = summarize_zed(lines)
    else:
        highlights = lines[:5]
    return {
        'repo': repo,
        'tag': item.get('tagName'),
        'publishedAt': format_ts(item.get('publishedAt')),
        'url': item.get('url'),
        'highlights': highlights,
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
    low = s.lower()
    if 'ruby language server' in low:
        return 'Ruby 的语言服务器插件，用于代码智能和分析。'
    if 'chrome browser' in low:
        return '让 coding agent 直接控制并检查一个正在运行的 Chrome 浏览器，可看性能、网络请求和控制台。'
    if 'api lifecycle' in low or 'postman' in low:
        return 'Postman 方向的 API 全生命周期插件，可同步集合、跑测试、做 mock 和生成文档。'
    if 'project management' in low or 'asana' in low:
        return 'Asana 项目管理集成，可创建任务、查项目、跟进进度。'
    if 'atlassian' in low or 'jira' in low or 'confluence' in low:
        return 'Atlassian 集成，可连 Jira / Confluence，处理 issue、文档和迭代。'
    if 'serverless' in low:
        return 'AWS Serverless 方向插件，覆盖设计、开发、部署、测试和调试。'
    if 'development kit' in low and 'agent sdk' in low:
        return '面向 Claude Agent SDK 的开发工具包。'
    if not s:
        return '暂无说明。'
    return s if re.search(r'[。！？]$', s) else s + '。'


def search_repos(query, limit=5):
    enriched_query = f"{query} fork:false archived:false"
    code, out, err = run_maybe([
        'gh', 'search', 'repos', enriched_query,
        '--sort', 'updated', '--order', 'desc', '--limit', str(limit),
        '--json', 'fullName,description,url,updatedAt,stargazersCount'
    ])
    if code != 0:
        return []
    try:
        return json.loads(out)
    except Exception:
        return []


def discovery_score(item):
    name = item['fullName'].lower()
    desc = (item.get('description') or '').lower()
    text = f"{name} {desc}"
    stars = int(item.get('stargazersCount') or 0)

    score = 0

    high_signal = CONFIG['discovery_high_signal_keywords']
    low_signal = CONFIG['discovery_low_signal_keywords']

    for k in high_signal:
        if k in text:
            score += 5
    for k in low_signal:
        if k in text:
            score -= 6

    if stars >= 500:
        score += 12
    elif stars >= 100:
        score += 8
    elif stars >= 50:
        score += 5
    elif stars == 0:
        score -= 4
    else:
        score -= 6

    if not desc:
        score -= 4
    if len(desc) < 20:
        score -= 2

    if any(k in text for k in ['claude code', 'openclaw']):
        score += 6

    return score


def discover(limit=10):
    seen = set(r.lower() for r in CORE_RELEASE_REPOS + [PLUGIN_REPO])
    pool = []
    for q in DISCOVERY_QUERIES:
        for item in search_repos(q, limit=12):
            name = item['fullName']
            low = name.lower()
            text = ((item.get('description') or '') + ' ' + name).lower()
            if low in seen:
                continue
            if not any(k in text for k in ['agent', 'coding', 'code', 'mcp', 'acp', 'worktree', 'repo', 'terminal', 'plugin', 'hook', 'memory', 'observability']):
                continue
            item['matchedQuery'] = q
            item['_score'] = discovery_score(item)
            seen.add(low)
            pool.append(item)

    pool = [x for x in pool if x['_score'] >= 4 and int(x.get('stargazersCount') or 0) >= MIN_STARS]
    pool.sort(key=lambda x: (x['_score'], int(x.get('stargazersCount') or 0)), reverse=True)
    return pool[:limit]


def repo_desc_cn(text):
    s = cleanup(text)
    low = s.lower()
    if 'forgets everything between sessions' in low:
        return '解决 coding agent 在多次会话之间容易“失忆”的问题。'
    if 'desktop notifications' in low:
        return '给 LLM coding agent 提供桌面通知能力。'
    if 'hook event tracking' in low or 'observability' in low:
        return '面向 Claude Code agent 的可观测性工具，可跟踪 hook 事件并观察多个 agent 的运行情况。'
    if 'manager for podman containers' in low:
        return '给 AI coding agent 管理 podman 容器的工具。'
    if 'visual studio code' in low and 'coding agent' in low:
        return '一个面向 Visual Studio Code 的 coding agent。'
    if 'claude code agents offer specialized ai agents' in low:
        return '一组面向 Claude Code 的专用 agents，覆盖代码、架构、本地化和自动化等任务。'
    if 'orchestrator for coding agents' in low and 'humans in the loop' in low:
        return '一个面向 coding agent 的编排器，强调人在回路中的协作。'
    if 'autonomous claude code agent runner' in low:
        return '一个自动化的 Claude Code 运行器，并带有更偏验证导向的 TDD 检查。'
    if 'terminal-based multi-agent orchestrator' in low:
        return '一个终端里的多 Agent 编排器，可在多个仓库之间统一调度 Claude Code。'
    if 'mobile client for claude code and codex' in low:
        return 'Claude Code / Codex 的移动端控制客户端，可通过手机远程操控。'
    if 'reusable skills for ai coding agents' in low:
        return '一个面向 AI coding agent 的可复用 skills 集合，偏 Claude Code 生态。'
    if 'framework for agentic coding' in low:
        return '一个支持多种主流 agent coding 工具的框架。'
    if 'multi-agent coding workspace' in low:
        return '一个面向企业场景的多 Agent coding 工作台。'
    if 'ubuntu vps' in low and 'multi-agent ai development environment' in low:
        return '把一台 Ubuntu VPS 快速搭成多 Agent AI 开发环境，包含会话管理、安全工具和协作基础设施。'
    if 'multi-agent coordination platform' in low and 'mcp/acp/a2a' in low:
        return '一个多 Agent 协调平台：把用户意图解析成结构化规格，再通过 MCP / ACP / A2A 协议把任务路由给 Claude Code、OpenCode、Gemini 等工具。'
    if 'agent client protocol' in low and 'obsidian' in low:
        return '把 Claude Code、Codex、Gemini CLI 等 AI agent 通过 ACP 接进 Obsidian。'
    if 'unified agent orchestration hub' in low and 'yaml' in low:
        return '一个统一的 agent 编排中枢：可以用 YAML 管理多种 AI agent，并通过 ACP / OpenCode Server 等标准协议对外暴露。'
    if 'turn gemini cli into a multi-agent platform' in low:
        return '把 Gemini CLI 扩成多 Agent 平台，带专用子代理、并行分发和分阶段编排。'
    if 'git worktrees, terminals, and diffs' in low:
        return '一个原生桌面应用，用来承载 agentic coding 工作流，重点围绕 git worktree、终端和 diff。'
    if 'git-native ai agent framework' in low:
        return '一个 git 原生的 AI agent 框架：身份、规则、记忆、工具和 skills 都作为版本化文件存放在仓库里。'
    if 'lightweight coding agent that runs in your terminal' in low:
        return '一个运行在终端里的轻量级 coding agent。'
    if 'acp adapter' in low:
        return '一个给 pi coding agent 用的 ACP 适配器。'
    if 'open-source coding agent in the terminal' in low:
        return '一个开源的终端 coding agent。'
    if not s:
        return '暂无简介，需点进仓库进一步看。'
    return s if re.search(r'[。！？]$', s) else s + '。'


def repo_reason(item):
    q = item.get('matchedQuery', '')
    if 'worktree' in q:
        return '命中 worktree / 多任务协作方向。'
    if 'subagent' in q:
        return '命中 subagent 方向。'
    if 'terminal' in q:
        return '命中终端 coding agent 方向。'
    if 'repo memory' in q:
        return '命中 repo memory / 上下文方向。'
    if 'mcp' in q.lower() or 'acp' in q.lower():
        return '命中协议 / 工具接入方向。'
    if 'agentic' in q or 'coding agent' in q:
        return '命中 coding agent 主查询。'
    return '来自 coding agent 生态搜索。'


def main():
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    core = [summarize_release(latest_release(repo)) for repo in CORE_RELEASE_REPOS]

    current_market = fetch_marketplace()
    previous_market = {}
    if PLUGIN_STATE.exists():
        previous_market = json.loads(PLUGIN_STATE.read_text())
    plugin_diff = diff_marketplace(previous_market, current_market)
    PLUGIN_STATE.write_text(json.dumps(current_market, ensure_ascii=False, indent=2))

    discovery = discover(limit=DISCOVERY_COUNT)

    result = {
        'generatedAt': now,
        'language': CONFIG['language'],
        'config': {
            'min_stars': MIN_STARS,
            'discovery_count': DISCOVERY_COUNT,
            'core_release_repos': CORE_RELEASE_REPOS,
            'plugin_repo': PLUGIN_REPO,
        },
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
        lines += [f"### {item['repo']} · {item.get('tag','')}", f"- 发布时间：{item.get('publishedAt','')}（北京时间）"]
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

    lines += [f"## 新仓候选（{DISCOVERY_COUNT} 个）", '']
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
