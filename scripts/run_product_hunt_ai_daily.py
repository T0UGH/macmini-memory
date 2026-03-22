#!/usr/bin/env python3
"""Product Hunt AI Daily — 每日 AI 产品简报生成器。

数据源优先级：
1. Product Hunt GraphQL API v2（需要 OAuth token）
2. hunted.space 第三方聚合（公开可访问）
3. Anthropic API 兜底（基于模型知识生成）

输出：中文 markdown 简报 → memory repo
"""
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).parent
CONFIG = json.loads((SCRIPT_DIR / 'config_product_hunt.json').read_text())
OUTPUT_DIR = Path(CONFIG['output_dir'])
TZ_CST = timezone(timedelta(hours=8))
TODAY = datetime.now(TZ_CST).strftime('%Y-%m-%d')


# ── 数据获取层 ──────────────────────────────────────────────

def get_ph_token() -> str:
    """获取 PH API access token（client_credentials 模式）。"""
    token = CONFIG.get('ph_access_token', '')
    if token:
        return token
    cid = CONFIG.get('ph_client_id', '')
    csec = CONFIG.get('ph_client_secret', '')
    if not cid or not csec:
        return ''
    try:
        resp = requests.post('https://api.producthunt.com/v2/oauth/token', json={
            'client_id': cid,
            'client_secret': csec,
            'grant_type': 'client_credentials',
        }, timeout=15)
        if resp.status_code == 200:
            token = resp.json().get('access_token', '')
            if token:
                CONFIG['ph_access_token'] = token
                (SCRIPT_DIR / 'config_product_hunt.json').write_text(
                    json.dumps(CONFIG, ensure_ascii=False, indent=2))
            return token
    except Exception as e:
        print(f'[ph_token] failed: {e}', file=sys.stderr)
    return ''


def fetch_from_ph_api(token: str) -> list[dict]:
    """通过 PH GraphQL API 获取近 24h 产品。"""
    yesterday = (datetime.now(TZ_CST) - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ')
    query = '''
    query($after: DateTime!) {
      posts(first: 50, order: VOTES, postedAfter: $after) {
        edges {
          node {
            id name tagline description votesCount
            url website
            topics { edges { node { name } } }
            createdAt
          }
        }
      }
    }
    '''
    try:
        resp = requests.post(CONFIG['ph_api_url'],
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
            },
            json={'query': query, 'variables': {'after': yesterday}},
            timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            edges = data.get('data', {}).get('posts', {}).get('edges', [])
            products = []
            for edge in edges:
                node = edge['node']
                topics = [t['node']['name'] for t in node.get('topics', {}).get('edges', [])]
                products.append({
                    'name': node['name'],
                    'tagline': node.get('tagline', ''),
                    'description': node.get('description', ''),
                    'votes': node.get('votesCount', 0),
                    'ph_url': node.get('url', ''),
                    'website': node.get('website', ''),
                    'topics': topics,
                    'created_at': node.get('createdAt', ''),
                    'source': 'ph_api',
                })
            return products
        else:
            print(f'[ph_api] {resp.status_code}: {resp.text[:200]}', file=sys.stderr)
    except Exception as e:
        print(f'[ph_api] failed: {e}', file=sys.stderr)
    return []


def fetch_from_hunted_space() -> list[dict]:
    """从 hunted.space 获取近期 PH 产品（公开可访问）。"""
    try:
        resp = requests.get('https://hunted.space/top-products/latest',
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'},
            timeout=20)
        if resp.status_code != 200:
            print(f'[hunted] {resp.status_code}', file=sys.stderr)
            return []
        # 解析 HTML 中的产品数据（hunted.space 是 Next.js 应用）
        html = resp.text
        # 尝试提取 __NEXT_DATA__ JSON
        match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
        if match:
            try:
                next_data = json.loads(match.group(1))
                return _parse_hunted_next_data(next_data)
            except json.JSONDecodeError:
                pass
        # 简单文本解析 fallback
        return _parse_hunted_html(html)
    except Exception as e:
        print(f'[hunted] failed: {e}', file=sys.stderr)
    return []


def _parse_hunted_next_data(data: dict) -> list[dict]:
    """解析 hunted.space 的 __NEXT_DATA__ JSON。"""
    products = []
    try:
        stats = data.get('props', {}).get('pageProps', {}).get('initialStats', {})
        posts_by_topic = stats.get('postsByTopicId', {})
        seen = set()
        # 遍历所有 topic 的产品
        for topic_id, posts in posts_by_topic.items():
            for post in posts:
                name = post.get('name', '')
                if name in seen:
                    continue
                seen.add(name)
                products.append({
                    'name': name,
                    'tagline': post.get('tagline', ''),
                    'description': '',
                    'votes': post.get('votesCount', 0),
                    'ph_url': post.get('url', ''),
                    'website': post.get('website', ''),
                    'topics': [],
                    'created_at': post.get('featuredAt', ''),
                    'source': 'hunted_space',
                })
    except Exception as e:
        print(f'[hunted_parse] {e}', file=sys.stderr)
    return products


def _parse_hunted_html(html: str) -> list[dict]:
    """简单 HTML 文本解析 hunted.space（fallback）。"""
    # 基础正则提取产品名和票数
    products = []
    for m in re.finditer(r'<h3[^>]*>([^<]+)</h3>.*?(\d+)\s*votes?', html, re.DOTALL):
        products.append({
            'name': m.group(1).strip(),
            'tagline': '',
            'description': '',
            'votes': int(m.group(2)),
            'ph_url': '',
            'website': '',
            'topics': [],
            'created_at': '',
            'source': 'hunted_html',
        })
    return products


def fetch_products() -> tuple[list[dict], str]:
    """获取产品列表，返回 (products, source_name)。"""
    # 方案 1: PH API
    token = get_ph_token()
    if token:
        products = fetch_from_ph_api(token)
        if products:
            print(f'[fetch] PH API: {len(products)} products', file=sys.stderr)
            return products, 'Product Hunt API'

    # 方案 2: hunted.space
    products = fetch_from_hunted_space()
    if products:
        print(f'[fetch] hunted.space: {len(products)} products', file=sys.stderr)
        return products, 'hunted.space'

    # 方案 3: Anthropic API 兜底
    products = fetch_via_anthropic()
    if products:
        print(f'[fetch] Anthropic API: {len(products)} products', file=sys.stderr)
        return products, 'Anthropic API (模型知识)'

    return [], 'none'


def fetch_via_anthropic() -> list[dict]:
    """使用 Anthropic API 基于模型知识生成近期 AI 产品列表。"""
    base_url = os.environ.get('ANTHROPIC_BASE_URL', 'https://api.anthropic.com')
    api_key = os.environ.get('ANTHROPIC_AUTH_TOKEN') or os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key:
        return []

    prompt = f"""请列出近期（{TODAY} 前后）在科技产品发布平台上值得关注的 AI 方向新产品/新工具。
重点关注：AI coding、AI agent、AI workflow、AI developer tools、AI productivity。
排除：纯娱乐 AI 工具、套壳 chatbot、与 AI 关系很弱的 SaaS。

请以 JSON 数组格式输出，每个产品包含：
- name: 产品名
- tagline: 一句话介绍（英文原文）
- description_cn: 中文描述（2-3句，说清做什么、解决什么问题）
- why_notable: 为什么值得看（中文，具体到功能/场景）
- relevance: 与 agent/coding/workflow 主线的关系（中文）
- votes: 预估热度（数字）
- website: 官网链接（如果知道）

输出 5-10 个高质量候选，不要凑数。只输出 JSON 数组，不要其他内容。"""

    try:
        resp = requests.post(f'{base_url}/v1/messages',
            headers={
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json',
            },
            json={
                'model': CONFIG.get('anthropic_model', 'claude-haiku-4-5-20251001'),
                'max_tokens': 4000,
                'messages': [{'role': 'user', 'content': prompt}],
            },
            timeout=60)
        if resp.status_code == 200:
            text = resp.json()['content'][0]['text'].strip()
            # 提取 JSON
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                items = json.loads(match.group())
                products = []
                for item in items:
                    products.append({
                        'name': item.get('name', ''),
                        'tagline': item.get('tagline', ''),
                        'description': item.get('description', ''),
                        'description_cn': item.get('description_cn', ''),
                        'why_notable': item.get('why_notable', ''),
                        'relevance': item.get('relevance', ''),
                        'votes': item.get('votes', 0),
                        'ph_url': item.get('ph_url', ''),
                        'website': item.get('website', ''),
                        'topics': [],
                        'created_at': '',
                        'source': 'anthropic',
                    })
                return products
        else:
            print(f'[anthropic] {resp.status_code}: {resp.text[:200]}', file=sys.stderr)
    except Exception as e:
        print(f'[anthropic] failed: {e}', file=sys.stderr)
    return []


# ── AI 筛选与评分 ──────────────────────────────────────────

def is_ai_related(product: dict) -> bool:
    """判断产品是否与 AI 相关。"""
    ai_topics = [t.lower() for t in CONFIG['ai_topics']]
    exclude_kw = [k.lower() for k in CONFIG['exclude_keywords']]

    text = ' '.join([
        product.get('name', ''),
        product.get('tagline', ''),
        product.get('description', ''),
        ' '.join(product.get('topics', [])),
    ]).lower()

    # 排除
    for kw in exclude_kw:
        if kw in text:
            return False

    # 匹配 AI 关键词
    for topic in ai_topics:
        if topic.lower() in text:
            return True

    # 检查 topics 分类
    for t in product.get('topics', []):
        if 'artificial intelligence' in t.lower() or 'ai' == t.lower():
            return True

    return False


def score_product(product: dict) -> float:
    """给产品打分（越高越好）。"""
    score = 0.0
    text = ' '.join([
        product.get('name', ''),
        product.get('tagline', ''),
        product.get('description', ''),
    ]).lower()

    # 票数权重
    votes = product.get('votes', 0)
    score += min(votes / 100, 5.0)

    # 主线相关性加分
    high_priority = ['agent', 'coding', 'developer', 'workflow', 'automation', 'cli', 'ide']
    for kw in high_priority:
        if kw in text:
            score += 2.0

    mid_priority = ['llm', 'rag', 'vector', 'embedding', 'prompt', 'copilot']
    for kw in mid_priority:
        if kw in text:
            score += 1.0

    return score


def filter_and_rank(products: list[dict]) -> list[dict]:
    """筛选 AI 产品并排序。"""
    ai_products = [p for p in products if is_ai_related(p)]
    for p in ai_products:
        p['_score'] = score_product(p)
    ai_products.sort(key=lambda x: x['_score'], reverse=True)
    return ai_products[:CONFIG['max_products']]


# ── 中文摘要生成 ──────────────────────────────────────────

def generate_chinese_summary(product: dict) -> dict:
    """为单个产品生成中文摘要。"""
    # 如果已有中文字段（来自 anthropic 源），直接用
    if product.get('description_cn'):
        return product

    base_url = os.environ.get('ANTHROPIC_BASE_URL', 'https://api.anthropic.com')
    api_key = os.environ.get('ANTHROPIC_AUTH_TOKEN') or os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key:
        product['description_cn'] = product.get('tagline', '')
        product['why_notable'] = '命中 AI 方向'
        product['relevance'] = '待分析'
        return product

    prompt = f"""请为以下 Product Hunt 产品生成中文简介。

产品名：{product['name']}
Tagline：{product.get('tagline', '')}
Description：{product.get('description', '')[:500]}
Topics：{', '.join(product.get('topics', []))}
Votes：{product.get('votes', 0)}

请输出 JSON，包含：
- description_cn: 中文描述（2-3句，说清做什么、解决什么问题）
- why_notable: 为什么值得看（具体到功能/场景，不要空泛）
- relevance: 与 agent/coding/workflow 主线的关系
- action: 建议动作（继续观察/可试用/暂不跟）

只输出 JSON，不要其他内容。"""

    try:
        resp = requests.post(f'{base_url}/v1/messages',
            headers={
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json',
            },
            json={
                'model': CONFIG.get('anthropic_model', 'claude-haiku-4-5-20251001'),
                'max_tokens': 500,
                'messages': [{'role': 'user', 'content': prompt}],
            },
            timeout=30)
        if resp.status_code == 200:
            text = resp.json()['content'][0]['text'].strip()
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                info = json.loads(match.group())
                product['description_cn'] = info.get('description_cn', '')
                product['why_notable'] = info.get('why_notable', '')
                product['relevance'] = info.get('relevance', '')
                product['action'] = info.get('action', '继续观察')
                return product
    except Exception as e:
        print(f'[summary] {product["name"]}: {e}', file=sys.stderr)

    # fallback
    product['description_cn'] = product.get('tagline', '')
    product['why_notable'] = '命中 AI 方向关键词'
    product['relevance'] = '待分析'
    product['action'] = '继续观察'
    return product


def generate_overview(products: list[dict]) -> str:
    """生成今日总览判断。"""
    base_url = os.environ.get('ANTHROPIC_BASE_URL', 'https://api.anthropic.com')
    api_key = os.environ.get('ANTHROPIC_AUTH_TOKEN') or os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key or not products:
        return f'- 今天筛选出 {len(products)} 个 AI 方向产品'

    names = [f"{p['name']}（{p.get('description_cn', p.get('tagline', '')[:60])}）" for p in products[:10]]
    prompt = f"""以下是今天 Product Hunt 上筛选出的 AI 方向产品：

{chr(10).join(f'- {n}' for n in names)}

请用 2-3 句中文写一个"今日判断"，风格参考：
- 今天 Product Hunt 的 AI 产品偏消费娱乐，真正值得看的不多
- 今天出现 2 个和 agent workflow 相关的新工具，值得继续跟踪

要求：简洁、有判断、不空泛。只输出判断文本，每句一行，以 - 开头。"""

    try:
        resp = requests.post(f'{base_url}/v1/messages',
            headers={
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json',
            },
            json={
                'model': CONFIG.get('anthropic_model', 'claude-haiku-4-5-20251001'),
                'max_tokens': 300,
                'messages': [{'role': 'user', 'content': prompt}],
            },
            timeout=30)
        if resp.status_code == 200:
            return resp.json()['content'][0]['text'].strip()
    except Exception as e:
        print(f'[overview] {e}', file=sys.stderr)

    return f'- 今天筛选出 {len(products)} 个 AI 方向产品'


# ── Markdown 生成 ──────────────────────────────────────────

def generate_markdown(products: list[dict], overview: str, source: str) -> str:
    """生成最终 markdown 简报。"""
    lines = [
        f'# Product Hunt AI Daily | {TODAY}',
        '',
        '## 今日判断',
        overview,
        '',
    ]

    if not products:
        lines += ['> 今天高信号 AI 产品偏少，没有值得单独列出的候选。', '']
    else:
        lines += [f'## 今日值得看（{len(products)} 个）', '']
        for idx, p in enumerate(products, 1):
            lines.append(f"### {idx}. {p['name']}")
            if p.get('ph_url'):
                lines.append(f"- Product Hunt：{p['ph_url']}")
            if p.get('website'):
                lines.append(f"- 官网：{p['website']}")
            if p.get('votes'):
                lines.append(f"- 热度：{p['votes']} votes")
            if p.get('tagline'):
                lines.append(f"- Tagline：{p['tagline']}")
            lines.append(f"- 它是做什么的：{p.get('description_cn', p.get('tagline', ''))}")
            if p.get('why_notable'):
                lines.append(f"- 为什么值得看：{p['why_notable']}")
            if p.get('relevance'):
                lines.append(f"- 与主线关系：{p['relevance']}")
            if p.get('action'):
                lines.append(f"- 建议动作：{p['action']}")
            lines.append('')

    lines += [
        '---',
        f'> 数据源：{source} | 生成时间：{datetime.now(TZ_CST).strftime("%Y-%m-%d %H:%M")} CST',
    ]
    return '\n'.join(lines)


# ── 主流程 ──────────────────────────────────────────────────

def main():
    print(f'[start] Product Hunt AI Daily for {TODAY}', file=sys.stderr)

    # 1. 获取产品数据
    products, source = fetch_products()
    if not products:
        print('[warn] no products fetched from any source', file=sys.stderr)

    # 2. 筛选 AI 产品（anthropic 源已经过筛选）
    if source != 'Anthropic API (模型知识)':
        ai_products = filter_and_rank(products)
    else:
        ai_products = products[:CONFIG['max_products']]

    print(f'[filter] {len(ai_products)}/{len(products)} AI products selected', file=sys.stderr)

    # 3. 生成中文摘要
    for p in ai_products:
        generate_chinese_summary(p)
        print(f'[summary] {p["name"]}: done', file=sys.stderr)

    # 4. 生成今日总览
    overview = generate_overview(ai_products)

    # 5. 生成 markdown
    md = generate_markdown(ai_products, overview, source)

    # 6. 写入文件
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    md_path = OUTPUT_DIR / f'{TODAY}.md'
    md_path.write_text(md)
    print(f'[output] {md_path}', file=sys.stderr)

    # 7. 输出结构化结果（供 validate 和调用方使用）
    result = {
        'date': TODAY,
        'source': source,
        'total_fetched': len(products),
        'ai_filtered': len(ai_products),
        'output_md': str(md_path),
        'products': [{
            'name': p['name'],
            'votes': p.get('votes', 0),
            'description_cn': p.get('description_cn', ''),
            'why_notable': p.get('why_notable', ''),
            'relevance': p.get('relevance', ''),
            'action': p.get('action', ''),
            'source': p.get('source', ''),
        } for p in ai_products],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
