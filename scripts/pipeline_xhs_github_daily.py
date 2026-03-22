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

    # Title: just owner/repo, NO "图 N｜" prefix
    lines.append(f"## {repo['owner_repo']}")

    if repo['section'] == 'core':
        # Product name + version
        name = repo['slug']
        if repo['version']:
            lines.append(f"**{name} {repo['version']}**")
        else:
            lines.append(f"**{name}**")
        lines.append('')
        if repo['release_time']:
            lines.append(f"发布时间：{repo['release_time']}")
            lines.append('')
    else:
        lines.append(f"**{repo['slug']}**")
        lines.append('')
        # Stars — mandatory for new repos
        if repo.get('stars'):
            lines.append(f"⭐ Stars：{repo['stars']}")
            lines.append('')
        else:
            lines.append('⭐ Stars：未知')
            lines.append('')

    # Intro paragraph
    if repo['intro']:
        lines.append(repo['intro'])
        lines.append('')

    # README summary — mandatory for new repos
    if repo['section'] == 'new':
        readme_sum = repo.get('readme_summary')
        if readme_sum:
            lines.append('**README 要点**')
            lines.append(readme_sum)
            lines.append('')
        else:
            lines.append('**README 要点**')
            lines.append('（README 内容不可用）')
            lines.append('')

    # Select display bullets
    display_bullets = _select_display_bullets(repo)
    for b in display_bullets:
        lines.append(f"- {b}")
    lines.append('')

    # One-sentence summary
    summary = _extract_summary(repo)
    if summary:
        lines.append('**一句话**')
        lines.append(summary)
        lines.append('')

    return '\n'.join(lines)


def _select_display_bullets(repo: dict) -> list[str]:
    """Pick the most important bullets for card display (max 5)."""
    content_bullets = []
    relation_bullet = None
    for b in repo['bullets']:
        if re.match(r'^(链接|简介)：', b):
            continue
        if re.match(r'^(建议动作|成熟度判断)：', b):
            continue
        if re.match(r'^为什么现在值得看：', b):
            continue
        if re.match(r'^与主线关系：', b):
            relation_bullet = b.replace('与主线关系：', '').strip()
            continue
        content_bullets.append(b)

    # For core repos: take up to 5 content bullets
    if repo['section'] == 'core':
        return content_bullets[:5]

    # For new repos: use relation + remaining content bullets (max 3 total)
    result = []
    if relation_bullet:
        result.append(relation_bullet)
    result.extend(content_bullets[:3 - len(result)])
    return result


def _extract_summary(repo: dict) -> Optional[str]:
    """Extract or generate a one-sentence summary."""
    # For new repos, look for "为什么现在值得看" bullet
    if repo['section'] == 'new':
        for b in repo['bullets']:
            if b.startswith('为什么现在值得看：'):
                return b.replace('为什么现在值得看：', '').strip()

    # For core repos, use the first bullet (usually the overview statement)
    if repo['section'] == 'core' and repo['bullets']:
        first = repo['bullets'][0]
        # If the first bullet is already a good summary (short enough), use it
        if len(first) <= 60:
            return first
        # Otherwise, take the intro-style first line
        return first

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
