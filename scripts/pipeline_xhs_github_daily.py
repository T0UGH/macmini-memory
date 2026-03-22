#!/usr/bin/env python3
"""Pipeline: GitHub AI Daily → Xiaohongshu square cards → publish.

Usage examples:
  # Full pipeline (generate cards, render PNGs, publish)
  python3 scripts/pipeline_xhs_github_daily.py --date 2026-03-17 --title 'GitHub AI 日报' --content '...'

  # Generate card markdowns only
  python3 scripts/pipeline_xhs_github_daily.py --date 2026-03-17 --cards-only

  # Render PNGs only (assumes cards already generated)
  python3 scripts/pipeline_xhs_github_daily.py --date 2026-03-17 --render-only

  # Skip publish (generate + render, no publish)
  python3 scripts/pipeline_xhs_github_daily.py --date 2026-03-17 --title 'GitHub AI 日报' --content '...' --skip-publish

  # Dry-run (go through everything but don't actually publish)
  python3 scripts/pipeline_xhs_github_daily.py --date 2026-03-17 --title 'GitHub AI 日报' --content '...' --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parent.parent
DAILY_DIR = ROOT / 'github-ai-daily'
XHS_DIR = ROOT / 'xiaohongshu' / 'github-ai-daily'
RENDER_SCRIPT = ROOT / 'scripts' / 'render_markdown_image.js'
PUBLISH_SCRIPT = ROOT / 'scripts' / 'publish_xiaohongshu_github_daily.py'

# ---------------------------------------------------------------------------
# Step 1: Parse daily markdown into per-repo structured data
# ---------------------------------------------------------------------------

def parse_daily_markdown(md_text: str) -> list[dict]:
    """Parse a github-ai-daily/<date>.md into ordered repo entries.

    Returns a list of dicts with keys:
      - slug: e.g. 'claude-code'
      - owner_repo: e.g. 'anthropics/claude-code'
      - section: 'core' | 'new'
      - version: str or None
      - release_time: str or None
      - stars: str or None
      - bullets: list[str]
      - intro: str (opening paragraph, if any)
      - link: str or None
    """
    repos: list[dict] = []
    current_section: Optional[str] = None
    current_repo: Optional[dict] = None

    for line in md_text.splitlines():
        stripped = line.strip()

        # Detect sections
        if re.match(r'^##\s+核心仓库', stripped):
            current_section = 'core'
            continue
        if re.match(r'^##\s+官方插件仓库', stripped):
            current_section = 'plugin'
            continue
        if re.match(r'^##\s+新仓候选', stripped):
            current_section = 'new'
            continue
        if re.match(r'^##\s+今日判断', stripped):
            current_section = 'summary'
            continue

        if current_section not in ('core', 'new'):
            continue

        # Detect repo heading
        # Core: ### anthropics/claude-code · v2.1.77
        # New:  ### 1. phodal/routa
        h3 = re.match(r'^###\s+(.+)$', stripped)
        if h3:
            heading_text = h3.group(1)

            if current_section == 'core':
                m = re.match(r'([\w\-\.]+/[\w\-\.]+)\s*·\s*(.+)', heading_text)
                if m:
                    if current_repo:
                        repos.append(current_repo)
                    owner_repo = m.group(1)
                    slug = owner_repo.split('/')[-1]
                    current_repo = {
                        'slug': slug,
                        'owner_repo': owner_repo,
                        'section': 'core',
                        'version': m.group(2).strip(),
                        'release_time': None,
                        'stars': None,
                        'readme_summary': None,
                        'bullets': [],
                        'intro': '',
                        'link': None,
                    }
            elif current_section == 'new':
                m = re.match(r'\d+\.\s*([\w\-\.]+/[\w\-\.]+)', heading_text)
                if m:
                    if current_repo:
                        repos.append(current_repo)
                    owner_repo = m.group(1)
                    slug = owner_repo.split('/')[-1]
                    current_repo = {
                        'slug': slug,
                        'owner_repo': owner_repo,
                        'section': 'new',
                        'version': None,
                        'release_time': None,
                        'stars': None,
                        'readme_summary': None,
                        'bullets': [],
                        'intro': '',
                        'link': None,
                    }
            continue

        if current_repo is None:
            continue

        # Extract bullet lines (supports both top-level and indented bullets)
        bullet_m = re.match(r'^-\s+(.+)$', stripped)
        nested_m = re.match(r'^[ \t]+-\s+(.+)$', line)
        if bullet_m or nested_m:
            text = (bullet_m.group(1) if bullet_m else nested_m.group(1)).strip()

            # Extract special fields from bullets
            if text.startswith('发布时间：'):
                t = re.sub(r'[（(].*$', '', text.replace('发布时间：', '')).strip()
                current_repo['release_time'] = t
            elif text.startswith('链接：'):
                current_repo['link'] = text.replace('链接：', '').strip()
            elif re.match(r'^Stars[：:]', text):
                sm = re.search(r'Stars[：:]\s*(\d[\d,]*)', text)
                if sm:
                    current_repo['stars'] = sm.group(1)
            elif re.match(r'^README 摘要[：:]', text):
                current_repo['readme_summary'] = re.sub(r'^README 摘要[：:]\s*', '', text).strip()
            elif re.match(r'^(简介|一句话结论)：', text):
                current_repo['intro'] = re.sub(r'^(简介|一句话结论)：', '', text).strip()
            elif re.match(r'^成熟度判断：', text):
                sm = re.search(r'Stars?\s+(\d[\d,]*)', text)
                if sm and not current_repo.get('stars'):
                    current_repo['stars'] = sm.group(1)
                current_repo['bullets'].append(text)
            elif text in ('更新点拆解：', '原始变更要点：', '对工作流的影响：', '这一轮变化说明：'):
                continue
            else:
                current_repo['bullets'].append(text)

    if current_repo:
        repos.append(current_repo)

    return repos


# ---------------------------------------------------------------------------
# Step 2: Generate card markdowns (one per repo, no slide numbering)
# ---------------------------------------------------------------------------

def generate_card_markdown(repo: dict) -> str:
    """Generate a single Xiaohongshu card markdown for a repo."""
    lines: list[str] = []

    lines.append(f"## {repo['owner_repo']}")

    if repo['section'] == 'core':
        name = repo['slug']
        lines.append(f"**{name} {repo['version']}**" if repo['version'] else f"**{name}**")
        lines.append('')
        if repo['release_time']:
            lines.append(f"发布时间：{repo['release_time']}")
            lines.append('')
        if repo['intro']:
            lines.append(repo['intro'])
            lines.append('')
        core_sections = _build_core_sections(repo)
        for title, section_lines in core_sections:
            if not section_lines:
                continue
            lines.append(f'**{title}**')
            for item in section_lines:
                lines.append(f'- {item}')
            lines.append('')
    else:
        lines.append(f"**{repo['slug']}**")
        lines.append('')
        lines.append(f"⭐ Stars：{repo['stars'] if repo.get('stars') else '未知'}")
        lines.append('')
        lines.append('**它是做什么的**')
        lines.append(_normalize_new_intro(repo))
        lines.append('')

        readme_sum = _clean_readme_summary(repo.get('readme_summary') or '')
        lines.append('**README 要点**')
        lines.append(readme_sum or '（README 内容不可用）')
        lines.append('')

        relation = _extract_relation(repo)
        if relation:
            lines.append('**和主线的关系**')
            lines.append(relation)
            lines.append('')

    summary = _extract_summary(repo)
    if summary:
        lines.append('**一句判断**')
        lines.append(summary)
        lines.append('')

    return '\n'.join(lines)


def _extract_relation(repo: dict) -> Optional[str]:
    for b in repo['bullets']:
        if b.startswith('与主线关系：'):
            return b.replace('与主线关系：', '').strip()
    return None


def _clean_bullet_text(text: str) -> str:
    text = re.sub(r'^与主线关系：\s*', '', text).strip()
    text = re.sub(r'^做什么：\s*', '', text).strip()
    text = re.sub(r'^核心关键词：\s*', '', text).strip()
    text = re.sub(r'^为什么现在值得看：\s*', '', text).strip()
    return text


def _clean_readme_summary(text: str) -> str:
    if not text:
        return ''
    text = re.sub(r'https?://\S+', '', text)
    text = text.replace('<br />', ' ').replace('&nbsp;', ' ')
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip(' -|>')
    skip_prefixes = (
        'Quickstart', 'Table of Contents', 'Fork of', 'Please see', 'FREE FOR PERSONAL USE',
        'Documentation', 'English |', '中文 |', '日本語', 'Docs', 'Highlights',
    )
    parts = re.split(r'(?<=[.!?。！？])\s+|\s+-\s+|\s+>\s+', text)
    kept = []
    for part in parts:
        s = part.strip(' -|>')
        if not s:
            continue
        if any(s.startswith(prefix) for prefix in skip_prefixes):
            continue
        low = s.lower()
        if any(token in low for token in ['table of contents', 'quickstart', 'fork of', 'please see', 'documentation', 'free for personal use']):
            continue
        kept.append(s)
        if len(' '.join(kept)) >= 180:
            break
    result = ' '.join(kept) if kept else text
    result = re.sub(r'\s+', ' ', result).strip()
    return (result[:177] + '…') if len(result) > 180 else result


def _build_core_sections(repo: dict) -> list[tuple[str, list[str]]]:
    cn = []
    evidence = []
    impacts = []
    seen = set()
    for raw in repo['bullets']:
        b = _clean_bullet_text(raw)
        if not b or b in seen:
            continue
        seen.add(b)
        if re.search(r'[A-Za-z]{4,}', b) and not re.search(r'[一-鿿]', b):
            evidence.append(b)
        elif any(token in b for token in ['工作流', '长期使用', '值得关注', '优先级', '很重要', '受益']):
            impacts.append(b)
        else:
            cn.append(b)
    if repo['intro'] in cn:
        cn.remove(repo['intro'])
    merged_impacts = []
    for item in impacts + _infer_core_impacts(repo, cn):
        if item and item not in merged_impacts:
            merged_impacts.append(item)
    return [
        ('这次具体改了什么', cn[:3]),
        ('这意味着什么', merged_impacts[:2]),
        ('原始证据', evidence[:1]),
    ]


def _infer_core_impacts(repo: dict, cn_bullets: list[str]) -> list[str]:
    out = []
    text = ' '.join(cn_bullets + [repo.get('intro', '')])
    low = text.lower()
    if 'worktree' in low or 'mcp' in low or 'hook' in low:
        out.append('更偏工程执行链路补强，不是表面功能加法。')
    if '发布链路' in text or '校验' in text or 'ssrf' in low:
        out.append('这类改动对常驻运行和生产使用更关键。')
    if '历史' in text or '稳定性' in text or '会话' in text:
        out.append('长期使用时的稳定性和可维护性会比短期演示更受益。')
    if 'ide' in low or '编辑器' in text or 'subagents' in low:
        out.append('说明工具还在继续往可执行 agent 工作流靠，而不是只拼模型能力。')
    if not out and cn_bullets:
        out.append('这次重点是把已有工作流做顺，而不是新增一个 flashy 卖点。')
    return out


def _normalize_new_intro(repo: dict) -> str:
    if repo.get('intro'):
        return repo['intro']
    for b in repo['bullets']:
        if b.startswith('做什么：'):
            return b.replace('做什么：', '').strip()
    return '需要点进仓库进一步确认。'


def _extract_summary(repo: dict) -> Optional[str]:
    if repo['section'] == 'new':
        reason = None
        relation = _extract_relation(repo) or ''
        intro = _normalize_new_intro(repo)
        for b in repo['bullets']:
            if b.startswith('为什么现在值得看：'):
                reason = b.replace('为什么现在值得看：', '').strip().rstrip('。')
                break
        if reason and 'Claude Code' in relation:
            return f'{reason}，而且和 Claude Code 主线贴得比较近。'
        if reason and 'Codex' in relation:
            return f'{reason}，也能接到 Codex / 多 agent 这条线。'
        if reason and '仓库上下文' in relation:
            return f'{reason}，更偏仓库上下文和多任务管理。'
        if reason:
            return reason + '。'
        return intro[:60]

    if repo.get('intro'):
        return repo['intro']
    for b in repo['bullets']:
        clean = _clean_bullet_text(b)
        if clean:
            return clean
    return None


# ---------------------------------------------------------------------------
# Step 3: Write card markdowns and render PNGs
# ---------------------------------------------------------------------------

def write_cards(date_str: str, repos: list[dict], variant: str = 'square-9') -> Path:
    """Write individual card markdown files to output directory."""
    out_dir = XHS_DIR / f'{date_str}-{variant}'
    out_dir.mkdir(parents=True, exist_ok=True)

    # Clean stale card artifacts from previous runs for the same date/variant.
    for old_file in out_dir.iterdir():
        if old_file.name == 'README.md':
            continue
        if old_file.suffix.lower() in {'.md', '.png'}:
            old_file.unlink()

    for i, repo in enumerate(repos, 1):
        md_content = generate_card_markdown(repo)
        md_file = out_dir / f'{i:02d}-{repo["slug"]}.md'
        md_file.write_text(md_content, encoding='utf-8')
        print(f'  [card] {md_file.name}')

    # Write README
    readme = out_dir / 'README.md'
    readme.write_text(
        f'# {date_str} GitHub square cards\n\n'
        f'- Generated by pipeline_xhs_github_daily.py\n'
        f'- {len(repos)} cards\n',
        encoding='utf-8',
    )
    return out_dir


def render_cards(out_dir: Path) -> list[Path]:
    """Render all card markdowns in directory to PNGs."""
    md_files = sorted(out_dir.glob('*.md'))
    md_files = [f for f in md_files if f.name != 'README.md']
    pngs: list[Path] = []

    for md_file in md_files:
        png_file = md_file.with_suffix('.png')
        print(f'  [render] {md_file.name} → {png_file.name}')
        subprocess.run(
            [str(RENDER_SCRIPT), str(md_file), str(png_file), '--xhs'],
            check=True,
            capture_output=True,
            text=True,
        )
        pngs.append(png_file)

    return pngs


# ---------------------------------------------------------------------------
# Step 4: Publish via existing publish script
# ---------------------------------------------------------------------------

def publish(date_str: str, title: str, content: str, variant: str = 'square-9',
            tags: Optional[list[str]] = None, dry_run: bool = False) -> dict:
    """Call publish_xiaohongshu_github_daily.py."""
    cmd = [
        sys.executable, str(PUBLISH_SCRIPT),
        '--date', date_str,
        '--title', title,
        '--content', content,
        '--variant', variant,
    ]
    if tags:
        cmd += ['--tags'] + tags
    if dry_run:
        cmd.append('--dry-run')

    proc = subprocess.run(cmd, check=True, text=True, capture_output=True)
    print(proc.stdout)
    return {'stdout': proc.stdout.strip(), 'returncode': proc.returncode}


# ---------------------------------------------------------------------------
# Helpers: default publish metadata
# ---------------------------------------------------------------------------

def default_title(date_str: str) -> str:
    dt = datetime.strptime(date_str, '%Y-%m-%d')
    return f"github-ai日报 {dt.strftime('%y%m%d')}版"


def default_content(date_str: str, repos_count: int) -> str:
    dt = datetime.strptime(date_str, '%Y-%m-%d')
    ymd = dt.strftime('%y%m%d')
    return (
        f"GitHub AI 日报 {ymd} 版。\n"
        f"这次整理了 {repos_count} 张图，按一仓一图展开，重点看 Claude Code、OpenClaw、Codex、OpenCode，以及值得继续跟踪的新项目。\n"
        "内容尽量把原文里真正发生了什么讲清楚，方便直接翻看。"
    )


# ---------------------------------------------------------------------------
# Step 5: Git commit
# ---------------------------------------------------------------------------

def git_commit(date_str: str, variant: str = 'square-9') -> Optional[str]:
    """Stage generated files and commit. Returns commit hash or None."""
    card_dir = XHS_DIR / f'{date_str}-{variant}'
    log_dir = ROOT / 'xiaohongshu' / 'published' / 'github-ai-daily'

    paths_to_add = []
    if card_dir.exists():
        paths_to_add.append(str(card_dir))
    if log_dir.exists():
        # Add any new publish logs for this date
        for f in log_dir.glob(f'{date_str}_*.json'):
            paths_to_add.append(str(f))

    if not paths_to_add:
        print('  [git] Nothing to commit.')
        return None

    subprocess.run(['git', 'add'] + paths_to_add, check=True, cwd=str(ROOT))
    result = subprocess.run(
        ['git', 'status', '--porcelain'], check=True, text=True,
        capture_output=True, cwd=str(ROOT),
    )
    if not result.stdout.strip():
        print('  [git] No changes to commit.')
        return None

    msg = f'Add Xiaohongshu cards for GitHub AI Daily {date_str}'
    subprocess.run(
        ['git', 'commit', '-m', msg],
        check=True, cwd=str(ROOT),
    )
    hash_result = subprocess.run(
        ['git', 'rev-parse', '--short', 'HEAD'],
        check=True, text=True, capture_output=True, cwd=str(ROOT),
    )
    return hash_result.stdout.strip()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description='Pipeline: GitHub AI Daily → Xiaohongshu square cards → publish.',
    )
    parser.add_argument('--date', required=True, help='Date like 2026-03-17')
    parser.add_argument('--title', default=None, help='Xiaohongshu title (<=20 chars)')
    parser.add_argument('--content', default=None, help='Post content body')
    parser.add_argument('--variant', default='square-9', help='Image folder suffix')
    parser.add_argument('--tags', nargs='*', default=None, help='Tags for Xiaohongshu post')
    parser.add_argument('--cards-only', action='store_true', help='Only generate card markdowns')
    parser.add_argument('--render-only', action='store_true', help='Only render PNGs (cards must exist)')
    parser.add_argument('--skip-publish', action='store_true', help='Skip publishing step')
    parser.add_argument('--dry-run', action='store_true', help='Dry-run: generate and render but do not actually publish')
    parser.add_argument('--no-commit', action='store_true', help='Skip git commit')
    args = parser.parse_args()

    date_str = args.date
    variant = args.variant
    out_dir = XHS_DIR / f'{date_str}-{variant}'

    # ---- Step 1 & 2: Generate card markdowns ----
    if not args.render_only:
        daily_file = DAILY_DIR / f'{date_str}.md'
        if not daily_file.exists():
            print(f'ERROR: Daily file not found: {daily_file}', file=sys.stderr)
            return 1

        print(f'[1/4] Parsing {daily_file.name} ...')
        md_text = daily_file.read_text(encoding='utf-8')
        repos = parse_daily_markdown(md_text)
        if not repos:
            print('ERROR: No repos parsed from daily file.', file=sys.stderr)
            return 1
        print(f'  Found {len(repos)} repos')

        print(f'[2/4] Writing card markdowns to {out_dir.name}/ ...')
        write_cards(date_str, repos, variant)

        if args.cards_only:
            print('Done (--cards-only).')
            return 0

    # ---- Step 3: Render PNGs ----
    print(f'[3/4] Rendering PNGs ...')
    if not out_dir.exists():
        print(f'ERROR: Card directory not found: {out_dir}', file=sys.stderr)
        return 1
    pngs = render_cards(out_dir)
    print(f'  Rendered {len(pngs)} images')

    if args.render_only:
        print('Done (--render-only).')
        return 0

    # ---- Step 4: Publish ----
    if not args.skip_publish:
        title = args.title or default_title(date_str)
        content = args.content or default_content(date_str, len(pngs))

        print(f'[4/4] Publishing to Xiaohongshu ...')
        print(f'  Title: {title}')
        publish(date_str, title, content, variant,
                tags=args.tags, dry_run=args.dry_run)
    else:
        print('[4/4] Skipping publish (--skip-publish).')

    # ---- Step 5: Git commit ----
    if not args.no_commit:
        print('[git] Committing ...')
        commit_hash = git_commit(date_str, variant)
        if commit_hash:
            print(f'  Committed: {commit_hash}')
    else:
        print('[git] Skipping commit (--no-commit).')

    print('Pipeline complete.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
