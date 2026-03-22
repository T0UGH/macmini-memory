#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path('/Users/haha/workspace/memory/github-ai-daily')
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
DEDUPE_LOOKBACK_DAYS = CONFIG.get('dedupe_lookback_days', 7)
DEDUPE_STATE_FILE = ROOT / CONFIG.get('dedupe_state_file', 'state/recommended_recent.json')
README_MIN_LENGTH = CONFIG.get('readme_min_length', 100)


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f'command failed: {cmd}\nSTDERR:\n{p.stderr}')
    return p.stdout


def run_maybe(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def latest_release(repo):
    code, out, err = run_maybe([
        'gh', 'release', 'view', '-R', repo,
        '--json', 'name,tagName,publishedAt,url,body,isPrerelease'
    ])
    if code != 0:
        return {'repo': repo, 'error': err.strip() or out.strip()}
    data = json.loads(out)
    data['repo'] = repo
    return data


def cleanup(s):
    s = re.sub(r'`([^`]+)`', r'\1', s)
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
    for raw in (body or '').splitlines():
        s = raw.strip()
        if s.startswith(('- ', '* ')):
            text = cleanup(s[2:].strip())
            if text:
                out.append(text)
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


def limit_lines(lines, n):
    seen = []
    for line in lines:
        if line and line not in seen:
            seen.append(line)
    return seen[:n]


def summarize_claude_code(lines):
    update_points = []
    raw_focus = []
    impacts = []

    mcp_line = first_match(lines, ['mcp', 'structured input']) or first_match(lines, ['mcp', 'interactive'])
    if mcp_line:
        update_points.append('MCP 交互能力继续增强：任务执行中可以补采结构化输入，不再只能靠单轮 prompt 把信息一次性喂完。')
        raw_focus.append(mcp_line)
        impacts.append('这会直接改善真实工作流里的“信息不齐就卡住”问题，agent 可以在中途向人要补充材料。')

    elicitation_line = first_match(lines, ['elicitation']) or first_match(lines, ['elicitationresult'])
    if elicitation_line:
        update_points.append('新增 Elicitation / ElicitationResult hooks，说明“向用户追问—拿到结果—继续执行”这条链路开始可被 hook 拦截和编排。')
        raw_focus.append(elicitation_line)
        impacts.append('对自动化团队来说，这意味着 Claude Code 的会话流转更像一条可插拔的工作流，而不只是黑盒对话。')

    name_line = first_match(lines, ['--name']) or first_match(lines, ['display name'])
    if name_line:
        update_points.append('CLI 新增 -n / --name，会话启动时就能明确命名，便于并行任务和多线程管理。')
        raw_focus.append(name_line)

    sparse_line = first_match(lines, ['sparsepaths']) or first_match(lines, ['sparse-checkout']) or first_match(lines, ['sparse paths'])
    if sparse_line:
        update_points.append('worktree.sparsePaths 进入可用状态，大仓库/monorepo 可以只检出必要目录，减小上下文和磁盘负担。')
        raw_focus.append(sparse_line)
        impacts.append('这类改动是面向重仓库场景的真优化，不是演示型功能；说明 Claude Code 在继续补企业仓库可用性。')

    postcompact_line = first_match(lines, ['postcompact'])
    if postcompact_line:
        update_points.append('新增 PostCompact hook，表示上下文压缩后也能被挂接后处理逻辑。')
        raw_focus.append(postcompact_line)
        impacts.append('这对长会话治理很关键：压缩不再只是内部动作，而是能接进可观察、可校验、可补救的链路。')

    if not update_points:
        update_points = ['本次 release 主要围绕 CLI、MCP、hook 和 worktree 的可编排性展开，方向是把 Claude Code 做得更像可控的工程系统。']
    if not raw_focus:
        raw_focus = lines[:6]
    if not impacts:
        impacts = ['如果你在用 Claude Code 跑多轮任务或大仓库，这版比“模型更聪明”更值得关注，因为它改的是工作流可用性。']

    return {
        'overview': '这版不是 flashy 新能力，而是在补 Claude Code 作为工程工具的执行链路：MCP 交互、hook 节点、会话命名和大仓库 worktree 都更完整了。',
        'update_points': limit_lines(update_points, 6),
        'raw_focus': limit_lines(raw_focus, 6),
        'impacts': limit_lines(impacts, 4),
    }


def summarize_openclaw(lines):
    update_points = []
    raw_focus = []
    impacts = []

    recover_line = first_match(lines, ['recover the broken']) or first_match(lines, ['tag/release path'])
    if recover_line:
        update_points.append('这次首先是在修补上一版损坏的 tag / release 路径，属于发布链路补丁，不是大功能更新。')
        raw_focus.append(recover_line)
        impacts.append('这类修复虽然不显眼，但会直接影响版本分发、自动升级和外部引用的可信度。')

    npm_line = first_match(lines, ['npm version is still'])
    if npm_line:
        update_points.append('npm 版本号仍是 2026.3.13，-1 只体现在 Git tag / GitHub Release，等于是在修发布包装层。')
        raw_focus.append(npm_line)

    compaction_line = first_match(lines, ['compaction'])
    if compaction_line:
        update_points.append('compaction 后置校验被补上：压缩完成后会按完整会话 token 数做 sanity check。')
        raw_focus.append(compaction_line)
        impacts.append('这会减少长会话压缩后状态异常却不自知的问题，对 always-on agent 很重要。')

    telegram_line = first_match(lines, ['telegram'])
    ssrf_line = first_match(lines, ['ssrf'])
    if telegram_line or ssrf_line:
        update_points.append('Telegram 媒体传输相关的安全策略被修正，属于 SSRF 防护链路的一部分。')
        raw_focus.extend([x for x in [telegram_line, ssrf_line] if x])
        impacts.append('说明 OpenClaw 在补“平台接入层”的边界安全，不只是堆功能；这对消息渠道型 agent 是硬需求。')

    if not update_points:
        update_points = ['这版 OpenClaw 以稳定性和安全补丁为主，重点不在新功能，而在发布链路、压缩校验和外部平台接入边界。']
    if not raw_focus:
        raw_focus = lines[:6]
    if not impacts:
        impacts = ['如果你在跑常驻 OpenClaw，这类发布链路和安全细节修补，优先级其实高于新玩具功能。']

    return {
        'overview': '这版更像“把系统做结实”的维护版本：修发布链路、补 compaction 校验、收紧 Telegram / SSRF 防护。',
        'update_points': limit_lines(update_points, 6),
        'raw_focus': limit_lines(raw_focus, 6),
        'impacts': limit_lines(impacts, 4),
    }


def summarize_opencode(lines):
    update_points = []
    raw_focus = []
    impacts = []

    effect_line = first_match(lines, ['effect-to-zod']) or first_match(lines, ['schema conversion'])
    if effect_line:
        update_points.append('补了 effect-to-zod 的 schema conversion，偏底层类型系统和结构转换能力。')
        raw_focus.append(effect_line)

    bun_line = first_match(lines, ['bun installations']) or first_match(lines, ['bun'])
    if bun_line:
        update_points.append('Bun 安装链路的配置序列化问题被处理，减少环境差异造成的安装异常。')
        raw_focus.append(bun_line)

    attachment_line = first_match(lines, ['text attachments'])
    if attachment_line:
        update_points.append('应用侧新增文本附件支持，输入材料不再只是一段 prompt，适合更复杂的资料投喂。')
        raw_focus.append(attachment_line)
        impacts.append('这会提升用 OpenCode 做分析/调试时的输入灵活性，尤其适合带日志、片段、说明一起喂。')

    history_line = first_match(lines, ['session history']) or first_match(lines, ['performance'])
    if history_line:
        update_points.append('会话历史改成分页加载，目标是把服务端性能和长会话稳定性拉上来。')
        raw_focus.append(history_line)
        impacts.append('这不是表面功能，但说明 OpenCode 也在补“越用越重”后的历史负担问题。')

    git_line = first_match(lines, ['git init']) or first_match(lines, ['sessions lost'])
    if git_line:
        update_points.append('修掉已有项目里执行 git init 后会话丢失的问题，属于真实使用中很烦人的稳定性坑。')
        raw_focus.append(git_line)

    if not update_points:
        update_points = ['这版 OpenCode 以底层能力补强和会话稳定性修复为主，同时补了输入能力。']
    if not raw_focus:
        raw_focus = lines[:6]
    if not impacts:
        impacts = ['整体看不是新叙事，而是在把 OpenCode 往“能长期用”的日常工具打磨。']

    return {
        'overview': 'OpenCode 这版重点不在宣传点，而在底层结构、历史性能和输入形态这些会影响长期使用体验的细节。',
        'update_points': limit_lines(update_points, 6),
        'raw_focus': limit_lines(raw_focus, 6),
        'impacts': limit_lines(impacts, 4),
    }


def summarize_codex(lines):
    update_points = []
    raw_focus = []
    impacts = []

    spawn_line = first_match(lines, ['spawn_agent']) or first_match(lines, ['subagents'])
    if spawn_line:
        update_points.append('这一版继续加强 Codex CLI 与 IDE/编辑器接入，方向是把终端与编辑器工作流打通。')
        raw_focus.append(spawn_line)
        impacts.append('这会继续降低从终端走向编辑器协同的切换成本。')

    codex_line = first_match(lines, ['gpt-5.3-codex']) or first_match(lines, ['openai provider'])
    if codex_line:
        update_points.append('权限/审批相关体验有更新，重点是在自动化执行时减少卡顿并保持可控。')
        raw_focus.append(codex_line)

    gateway_line = first_match(lines, ['vercel ai gateway'])
    if gateway_line:
        update_points.append('沙箱相关能力继续演进，说明 Codex 仍在强化安全边界与可执行性之间的平衡。')
        raw_focus.append(gateway_line)

    diff_line = first_match(lines, ['jump to a file from a diff']) or first_match(lines, ['open excerpts'])
    if diff_line:
        update_points.append('补丁 / diff 工作流有改进，更贴近真实代码修改与审阅场景。')
        raw_focus.append(diff_line)

    draft_line = first_match(lines, ['draft prompts']) or first_match(lines, ['thinking mode toggle']) or first_match(lines, ['thread history'])
    if draft_line:
        update_points.append('会话与上下文管理继续补强，方向是让长期使用更稳定。')
        raw_focus.append(draft_line)
        impacts.append('长期使用 Codex 时，上下文连续性和自动化执行稳定性会更关键。')

    if not update_points:
        update_points = ['这版 Codex 主要仍在打磨终端 coding agent 的执行、权限控制和编辑器协同体验。']
    if not raw_focus:
        raw_focus = lines[:6]
    if not impacts:
        impacts = ['Codex 仍然在补‘可执行 agent 工具’这条主线，而不是单纯堆模型能力。']

    return {
        'overview': '这一版继续加强 Codex CLI 与 IDE/编辑器接入，方向是把终端与编辑器工作流打通。',
        'update_points': limit_lines(update_points, 6),
        'raw_focus': limit_lines(raw_focus, 6),
        'impacts': limit_lines(impacts, 4),
    }


def summarize_release(item):
    if 'error' in item:
        return {'repo': item['repo'], 'error': item['error']}

    repo = item['repo']
    lines = bullet_lines(item.get('body') or '')
    if repo == 'anthropics/claude-code':
        data = summarize_claude_code(lines)
    elif repo == 'openclaw/openclaw':
        data = summarize_openclaw(lines)
    elif repo == 'sst/opencode':
        data = summarize_opencode(lines)
    elif repo == 'openai/codex':
        data = summarize_codex(lines)
    else:
        data = {
            'overview': '本次版本有可见更新，建议直接看 release 原文。',
            'update_points': lines[:5],
            'raw_focus': lines[:6],
            'impacts': ['对具体工作流的影响需结合仓库定位再判断。'],
        }

    return {
        'repo': repo,
        'tag': item.get('tagName'),
        'publishedAt': format_ts(item.get('publishedAt')),
        'url': item.get('url'),
        'overview': data['overview'],
        'update_points': data['update_points'],
        'raw_focus': data['raw_focus'],
        'impacts': data['impacts'],
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
    if 'notion workspace integration' in low:
        return 'Notion 集成，可搜索页面、更新文档、管理数据库，把团队知识库直接接进 Claude Code。'
    if 'browser automation' in low or 'stagehand' in low:
        return '浏览器自动化插件，可驱动网页交互、抓数据和跑流程。'
    if 'terraform' in low:
        return 'Terraform 生态集成，适合 IaC 场景的查询、生成和自动化。'
    if 'microsoft documentation' in low or 'azure' in low or '.net' in low:
        return '微软官方文档入口，适合 Azure、.NET、Windows 相关开发查询。'
    if 'intercom' in low:
        return 'Intercom 集成，可直接查客服会话、联系人和公司信息。'
    if 'neon' in low:
        return 'Neon 数据库/项目管理集成，把托管 Postgres 工作流接入 Claude Code。'
    if not s:
        return '暂无说明。'
    return s if re.search(r'[。！？]$', s) else s + '。'


def plugin_implication(diff):
    added = diff['added']
    names = {x['name'].lower() for x in added}
    points = []
    if any(n in names for n in ['stagehand', 'terraform', 'neon', 'notion', 'intercom', 'microsoft-docs']):
        points.append('这批新增插件明显更偏“真实工作系统接入”而不是 demo：知识库、数据库、浏览器、IaC、客服系统都在补。')
    if 'notion' in names and any(x['name'] == 'Notion' for x in diff['removed']):
        points.append('Notion 同时出现删除和新增，更像条目规范化/重命名，不像功能下线。')
    if not points:
        points.append('插件仓库这次变化说明 Claude Code 官方生态还在继续向生产系统接入层扩展。')
    return points


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


# ---------------------------------------------------------------------------
# 7-day deduplication + README fetching
# ---------------------------------------------------------------------------

def load_dedupe_history():
    if not DEDUPE_STATE_FILE.exists():
        return {}
    try:
        return json.loads(DEDUPE_STATE_FILE.read_text())
    except Exception:
        return {}


def get_recent_repos(lookback_days=None):
    if lookback_days is None:
        lookback_days = DEDUPE_LOOKBACK_DAYS
    history = load_dedupe_history()
    cutoff = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
    recent = set()
    for date_str, repos in history.items():
        if date_str >= cutoff:
            for r in repos:
                recent.add(r.lower())
    return recent


def save_dedupe_history(new_repos):
    history = load_dedupe_history()
    today = datetime.now().strftime('%Y-%m-%d')
    history[today] = [r['fullName'] for r in new_repos]
    cutoff = (datetime.now() - timedelta(days=DEDUPE_LOOKBACK_DAYS + 1)).strftime('%Y-%m-%d')
    history = {k: v for k, v in history.items() if k >= cutoff}
    DEDUPE_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    DEDUPE_STATE_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2))


def fetch_readme(full_name):
    code, out, err = run_maybe([
        'gh', 'api', f'repos/{full_name}/readme', '--jq', '.content'
    ])
    if code != 0:
        return '', f'README 抓取失败：{err.strip() or out.strip()}'
    try:
        import base64
        raw = base64.b64decode(out.strip()).decode('utf-8', errors='replace')
        plain = re.sub(r'[#*`\[\]()!>|_~-]', '', raw)
        plain = re.sub(r'\s+', ' ', plain).strip()
        if len(plain) < README_MIN_LENGTH:
            return raw, f'README 过短（{len(plain)} 字符，最低 {README_MIN_LENGTH}）'
        return raw, ''
    except Exception as e:
        return '', f'README 解码失败：{e}'


def summarize_readme(readme_text, max_length=220):
    if not readme_text:
        return ''
    lines = readme_text.strip().splitlines()
    summary_parts = []
    skip_prefixes = (
        'Quickstart', 'Table of Contents', 'Fork of', 'Please see', 'FREE FOR PERSONAL USE',
        'Documentation', 'English |', '中文 |', '日本語', 'Highlights',
    )
    for line in lines:
        s = line.strip()
        if not s or s.startswith(('![', '<', '[![', '---', '===')):
            continue
        if s.startswith('#'):
            s = re.sub(r'^#+\s*', '', s).strip()
            if len(s) < 5:
                continue
        s = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', s)
        s = re.sub(r'https?://\S+', '', s)
        s = re.sub(r'<[^>]+>', ' ', s)
        s = re.sub(r'[*_`|>]', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip(' -')
        if not s or any(s.startswith(prefix) for prefix in skip_prefixes):
            continue
        low = s.lower()
        if any(token in low for token in ['table of contents', 'quickstart', 'fork of', 'please see', 'documentation', 'free for personal use']):
            continue
        if len(s) > 10:
            summary_parts.append(s)
        if len(' '.join(summary_parts)) >= max_length:
            break
    result = ' '.join(summary_parts)
    if len(result) > max_length:
        result = result[:max_length] + '…'
    return result


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

    if any(k in text for k in ['claude code', 'openclaw', 'codex']):
        score += 6

    return score


def discover(limit=10):
    seen = set(r.lower() for r in CORE_RELEASE_REPOS + [PLUGIN_REPO])
    recent_repos = get_recent_repos()
    deduped = []
    readme_failures = []
    low_score_filtered = 0
    final = []

    max_rounds = CONFIG.get('discovery_max_rounds', 3)
    base_per_query = 12

    for round_num in range(max_rounds):
        per_query = base_per_query * (round_num + 1)
        pool = []

        for q in DISCOVERY_QUERIES:
            for item in search_repos(q, limit=per_query):
                name = item['fullName']
                low = name.lower()
                text = ((item.get('description') or '') + ' ' + name).lower()
                if low in seen:
                    continue
                if not any(k in text for k in ['agent', 'coding', 'code', 'mcp', 'acp', 'worktree', 'repo', 'terminal', 'plugin', 'hook', 'memory', 'observability']):
                    seen.add(low)
                    continue
                if low in recent_repos:
                    if not any(d['fullName'].lower() == low for d in deduped):
                        deduped.append({'fullName': name, 'dedupe_reason': f'最近 {DEDUPE_LOOKBACK_DAYS} 天内已推荐'})
                    seen.add(low)
                    continue
                item['matchedQuery'] = q
                item['_score'] = discovery_score(item)
                seen.add(low)
                pool.append(item)

        qualified = [x for x in pool if x['_score'] >= 4 and int(x.get('stargazersCount') or 0) >= MIN_STARS]
        low_score_filtered += len(pool) - len(qualified)
        qualified.sort(key=lambda x: (x['_score'], int(x.get('stargazersCount') or 0)), reverse=True)

        for item in qualified:
            if len(final) >= limit:
                break
            if any(f['fullName'].lower() == item['fullName'].lower() for f in final):
                continue
            readme_text, readme_err = fetch_readme(item['fullName'])
            item['readme_summary'] = summarize_readme(readme_text)
            item['readme_error'] = readme_err
            if readme_err and not readme_text:
                readme_failures.append({'fullName': item['fullName'], 'error': readme_err})
                continue
            if readme_err and readme_text:
                item['_score'] -= 3
            final.append(item)

        if len(final) >= limit:
            break

    final.sort(key=lambda x: (x['_score'], int(x.get('stargazersCount') or 0)), reverse=True)
    save_dedupe_history(final[:limit])
    return final[:limit], deduped, readme_failures, {
        'dedupe_filtered_count': len(deduped),
        'readme_skipped_count': len(readme_failures),
        'low_score_filtered_count': low_score_filtered,
        'final_count': len(final[:limit]),
    }

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


def repo_relation(item):
    text = f"{item['fullName']} {(item.get('description') or '')}".lower()
    rel = []
    if 'claude code' in text:
        rel.append('和 Claude Code 生态直接相关')
    if 'openclaw' in text:
        rel.append('和 OpenClaw / always-on agent 方向相关')
    if 'codex' in text:
        rel.append('和 Codex / 多 agent 编排方向相关')
    if any(k in text for k in ['mcp', 'acp']):
        rel.append('属于协议 / 工具接入层')
    if any(k in text for k in ['subagent', 'multi-agent']):
        rel.append('属于多 agent 编排层')
    if any(k in text for k in ['worktree', 'repo', 'memory']):
        rel.append('和仓库上下文 / 多任务管理有关')
    if not rel:
        rel.append('与 coding agent 工作流相关，但还需要进一步点进仓库确认成熟度')
    return '；'.join(rel) + '。'


def repo_keywords(item):
    text = f"{item['fullName']} {(item.get('description') or '')}".lower()
    mapping = [
        ('multi-agent', '多 Agent'), ('subagent', 'Subagent'), ('mcp', 'MCP'),
        ('acp', 'ACP'), ('worktree', 'worktree'), ('memory', 'memory'),
        ('terminal', 'terminal'), ('obsidian', 'Obsidian'), ('neovim', 'Neovim'),
        ('vscode', 'VS Code'), ('codex', 'Codex'), ('claude code', 'Claude Code'),
        ('openclaw', 'OpenClaw'), ('sandbox', 'sandbox'), ('plugin', 'plugin')
    ]
    out = []
    for raw, label in mapping:
        if raw in text and label not in out:
            out.append(label)
    return ' / '.join(out[:5]) if out else 'agentic coding / workflow'


def main():
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    core = [summarize_release(latest_release(repo)) for repo in CORE_RELEASE_REPOS]

    current_market = fetch_marketplace()
    previous_market = {}
    if PLUGIN_STATE.exists():
        previous_market = json.loads(PLUGIN_STATE.read_text())
    plugin_diff = diff_marketplace(previous_market, current_market)
    plugin_diff['implication'] = plugin_implication(plugin_diff)
    PLUGIN_STATE.write_text(json.dumps(current_market, ensure_ascii=False, indent=2))

    discovery, deduped, readme_failures, discovery_stats = discover(limit=DISCOVERY_COUNT)

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
        'readme_failures': readme_failures,
        'discovery_stats': discovery_stats,
        'discovery': discovery,
    }

    out_json = OUT_DIR / f'{now}.json'
    out_md = OUT_DIR / f'{now}.md'
    dated_md = ROOT / f"{now[:10]}.md"
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    lines = [f'# GitHub AI Daily | {now[:10]}', '', '## 核心仓库', '']
    for item in core:
        if 'error' in item:
            lines += [f"### {item['repo']}", f"- 抓取失败：{item['error']}", '']
            continue
        lines += [f"### {item['repo']} · {item.get('tag', '')}"]
        lines.append(f"- 发布时间：{item.get('publishedAt', '')}（北京时间）")
        lines.append(f"- 一句话结论：{item.get('overview', '')}")
        lines.append('- 更新点拆解：')
        for hl in item.get('update_points', [])[:6]:
            lines.append(f'  - {hl}')
        if item.get('raw_focus'):
            lines.append('- 原始变更要点：')
            for rb in item['raw_focus'][:6]:
                lines.append(f'  - {rb}')
        if item.get('impacts'):
            lines.append('- 对工作流的影响：')
            for imp in item['impacts'][:4]:
                lines.append(f'  - {imp}')
        if item.get('url'):
            lines.append(f"- 链接：{item['url']}")
        lines.append('')

    lines += ['## 官方插件仓库（marketplace.json）', '']
    lines.append(f"- 新增：{len(plugin_diff['added'])}")
    lines.append(f"- 删除：{len(plugin_diff['removed'])}")
    lines.append(f"- 版本变化：{len(plugin_diff['changed'])}")
    lines.append('- 这一轮变化说明：')
    for point in plugin_diff.get('implication', [])[:3]:
        lines.append(f'  - {point}')
    if plugin_diff['added']:
        lines.append('### 新增插件')
        for item in plugin_diff['added'][:10]:
            lines.append(f"- {item['name']}：{plugin_desc_cn(item.get('description', ''))}")
        lines.append('')
    if plugin_diff['removed']:
        lines.append('### 删除插件')
        for item in plugin_diff['removed'][:10]:
            lines.append(f"- {item['name']}：{plugin_desc_cn(item.get('description', ''))}")
        lines.append('')
    if plugin_diff['changed']:
        lines.append('### 插件版本变化')
        for item in plugin_diff['changed'][:10]:
            lines.append(f"- {item['name']}：{item.get('from')} -> {item.get('to')}；{plugin_desc_cn(item.get('description', ''))}")
        lines.append('')

    lines += [f'## 新仓候选（{DISCOVERY_COUNT} 个）', '']
    lines.append(f'> 搜索统计：去重 {discovery_stats["dedupe_filtered_count"]} | README 跳过 {discovery_stats["readme_skipped_count"]} | 低分过滤 {discovery_stats["low_score_filtered_count"]} | 最终 {discovery_stats["final_count"]}/{DISCOVERY_COUNT}')
    lines.append('')
    for idx, item in enumerate(discovery, start=1):
        lines.append(f"### {idx}. {item['fullName']}")
        lines.append(f"- 做什么：{repo_desc_cn(item.get('description', ''))}")
        readme_sum = item.get('readme_summary', '')
        if readme_sum:
            lines.append(f"- README 摘要：{readme_sum}")
        elif item.get('readme_error'):
            lines.append(f"- README 摘要：（不可用：{item['readme_error']}）")
        lines.append(f"- 核心关键词：{repo_keywords(item)}")
        lines.append(f"- 为什么现在值得看：{repo_reason(item)}")
        lines.append(f"- 与主线关系：{repo_relation(item)}")
        lines.append(f"- Stars：{item.get('stargazersCount')} | 来源查询：{item.get('matchedQuery')}")
        lines.append(f"- 链接：{item.get('url')}")
        lines.append('')

    lines += ['## 今日判断', '']
    lines.append('- 今天 GitHub 侧最强的信号不是“又多了一个 AI repo”，而是核心工具都在继续往可编排、可长期使用、可接生产系统的方向补细节。')
    lines.append('- 核心仓库部分必须优先看更新点拆解和对工作流的影响，不要只看版本号。')
    lines.append('- 新仓候选里优先关注真正碰到 Claude Code / Codex / OpenClaw 主线的项目，少看纯列表和模板型仓库。')

    md_text = '\n'.join(lines)
    out_md.write_text(md_text)
    dated_md.write_text(md_text)
    print(str(out_md))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)
