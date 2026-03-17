#!/usr/bin/env python3
"""Pipeline: X AI Daily → Xiaohongshu square cards → publish.

Usage examples:
  # Full pipeline (generate cards, render PNGs, publish)
  python3 scripts/pipeline_xhs_x_daily.py --date 2026-03-17 --title 'X AI 情报日报' --content '...'

  # Generate card markdowns only
  python3 scripts/pipeline_xhs_x_daily.py --date 2026-03-17 --cards-only

  # Render PNGs only (assumes cards already generated)
  python3 scripts/pipeline_xhs_x_daily.py --date 2026-03-17 --render-only

  # Skip publish (generate + render, no publish)
  python3 scripts/pipeline_xhs_x_daily.py --date 2026-03-17 --title 'X AI 情报日报' --content '...' --skip-publish

  # Dry-run (go through everything but don't actually publish)
  python3 scripts/pipeline_xhs_x_daily.py --date 2026-03-17 --title 'X AI 情报日报' --content '...' --dry-run
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
DAILY_DIR = ROOT / 'x-ai-daily'
XHS_DIR = ROOT / 'xiaohongshu' / 'x-ai-daily'
RENDER_SCRIPT = ROOT / 'scripts' / 'render_markdown_image.js'
PUBLISH_SCRIPT = ROOT / 'scripts' / 'publish_xiaohongshu_x_daily.py'

# ---------------------------------------------------------------------------
# Step 1: Parse x-ai-daily markdown into structured items
# ---------------------------------------------------------------------------

def parse_daily_markdown(md_text: str) -> list[dict]:
    """Parse x-ai-daily/<date>.md into ordered news items.

    Returns a list of dicts with keys:
      - num: int (original numbering)
      - title: str (heading text without number prefix)
      - author: str
      - source: str
      - link: str
      - summary: str (摘要)
      - why_important: str (为什么重要)
      - scores: dict[str, int] (5 scoring dimensions)
      - avg_score: float
    """
    items: list[dict] = []
    current: Optional[dict] = None
    current_field: Optional[str] = None  # track multi-line field

    for line in md_text.splitlines():
        stripped = line.strip()

        # Skip everything before first ### item and after section 5/6
        if re.match(r'^##\s+(5\.\s+值得点开|6\.\s+总结|Caveats)', stripped):
            if current:
                items.append(current)
                current = None
            break

        # Detect item heading: ### N) Title
        h3 = re.match(r'^###\s+(\d+)\)\s+(.+)$', stripped)
        if h3:
            if current:
                items.append(current)
            current = {
                'num': int(h3.group(1)),
                'title': h3.group(2).strip(),
                'author': '',
                'source': '',
                'link': '',
                'summary': '',
                'why_important': '',
                'scores': {},
                'avg_score': 0.0,
            }
            current_field = None
            continue

        if current is None:
            continue

        # Parse bullet fields
        bullet = re.match(r'^-\s+(.+)$', stripped)
        if bullet:
            text = bullet.group(1)

            if text.startswith('作者：'):
                current['author'] = text.replace('作者：', '').strip()
                current_field = None
            elif text.startswith('来源：'):
                current['source'] = text.replace('来源：', '').strip()
                current_field = None
            elif text.startswith('链接：'):
                current['link'] = text.replace('链接：', '').strip()
                current_field = None
            elif text.startswith('摘要：'):
                current['summary'] = text.replace('摘要：', '').strip()
                current_field = 'summary'
            elif text.startswith('为什么重要：'):
                current['why_important'] = text.replace('为什么重要：', '').strip()
                current_field = 'why_important'
            elif text.startswith('评分：'):
                current_field = 'scores'
            elif current_field == 'scores':
                # Score line: "重要性：9/10"
                score_m = re.match(r'^(.+?)：\s*(\d+)/10', text)
                if score_m:
                    current['scores'][score_m.group(1).strip()] = int(score_m.group(2))
            else:
                current_field = None
            continue

        # Indented score lines (under 评分：)
        if current_field == 'scores':
            score_m = re.match(r'^-\s*(.+?)：\s*(\d+)/10', stripped)
            if not score_m:
                score_m = re.match(r'^(.+?)：\s*(\d+)/10', stripped)
            if score_m:
                current['scores'][score_m.group(1).strip()] = int(score_m.group(2))
                continue

    if current:
        items.append(current)

    # Compute average scores
    for item in items:
        if item['scores']:
            item['avg_score'] = sum(item['scores'].values()) / len(item['scores'])
        else:
            item['avg_score'] = 0.0

    return items


# ---------------------------------------------------------------------------
# Step 2: Generate card markdowns (XHS style with 必看指数)
# ---------------------------------------------------------------------------

def score_to_stars(avg: float) -> str:
    """Convert average score to star rating string."""
    if avg >= 9.0:
        return '★★★★★'
    elif avg >= 8.0:
        return '★★★★☆'
    elif avg >= 7.0:
        return '★★★☆☆'
    elif avg >= 6.0:
        return '★★☆☆☆'
    else:
        return '★☆☆☆☆'


def generate_card_markdown(item: dict) -> str:
    """Generate a single Xiaohongshu card markdown for an item.

    Style: 原文内容占大头, 评价缩短, 纯中文, 必看指数替代评分.
    """
    lines: list[str] = []

    # Title: just the topic, no numbering
    lines.append(f"## {item['title']}")
    lines.append('')

    # Main body: summary content (占大头)
    if item['summary']:
        lines.append(item['summary'])
        lines.append('')

    # Why important section (shortened)
    lines.append('### 为什么值得看')
    if item['why_important']:
        # Shorten: take the core message, limit length
        why = item['why_important']
        # If too long, take first two sentences
        sentences = re.split(r'(?<=[。！？；])', why)
        if len(sentences) > 2 and len(why) > 120:
            why = ''.join(sentences[:2])
        lines.append(why)
    lines.append('')

    # 必看指数
    stars = score_to_stars(item['avg_score'])
    lines.append(f'**必看指数：{stars}**')
    lines.append('')

    # One-sentence conclusion
    lines.append('### 一句话结论')
    # Generate from summary or why_important
    conclusion = _extract_conclusion(item)
    lines.append(f'**{conclusion}**')
    lines.append('')

    return '\n'.join(lines)


def _extract_conclusion(item: dict) -> str:
    """Extract or derive a one-sentence conclusion."""
    # Use the last sentence of why_important as conclusion
    why = item['why_important']
    if why:
        sentences = re.split(r'(?<=[。！？])', why)
        sentences = [s.strip() for s in sentences if s.strip()]
        if sentences:
            last = sentences[-1]
            if not last.endswith(('。', '！', '？')):
                last += '。'
            return last

    # Fallback to summary's last sentence
    if item['summary']:
        sentences = re.split(r'(?<=[。！？])', item['summary'])
        sentences = [s.strip() for s in sentences if s.strip()]
        if sentences:
            return sentences[-1]

    return item['title']


def title_to_slug(title: str) -> str:
    """Convert a Chinese/mixed title to a short ASCII slug."""
    # Extract English words if any, otherwise use pinyin-like approach
    english = re.findall(r'[A-Za-z0-9]+', title)
    if english:
        slug = '-'.join(w.lower() for w in english[:3])
        return slug[:30]
    # Fallback: use first few chars
    return 'item'


# ---------------------------------------------------------------------------
# Step 3: Write card markdowns and render PNGs
# ---------------------------------------------------------------------------

def write_cards(date_str: str, items: list[dict], variant: str = 'square-9',
                max_cards: int = 9) -> Path:
    """Write individual card markdown files to output directory."""
    out_dir = XHS_DIR / f'{date_str}-{variant}'
    out_dir.mkdir(parents=True, exist_ok=True)

    # Take top N items by avg_score
    selected = sorted(items, key=lambda x: x['avg_score'], reverse=True)[:max_cards]

    for i, item in enumerate(selected, 1):
        md_content = generate_card_markdown(item)
        slug = title_to_slug(item['title'])
        md_file = out_dir / f'{i:02d}-{slug}.md'
        md_file.write_text(md_content, encoding='utf-8')
        print(f'  [card] {md_file.name}')

    return out_dir


def render_cards(out_dir: Path) -> list[Path]:
    """Render all card markdowns in directory to PNGs."""
    md_files = sorted(out_dir.glob('*.md'))
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
# Step 4: Publish via publish script
# ---------------------------------------------------------------------------

def publish(date_str: str, title: str, content: str, variant: str = 'square-9',
            tags: Optional[list[str]] = None, dry_run: bool = False) -> dict:
    """Call publish_xiaohongshu_x_daily.py."""
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
    return f"x ai日报 {dt.strftime('%y%m%d')}"


def default_content(date_str: str, cards_count: int) -> str:
    dt = datetime.strptime(date_str, '%Y-%m-%d')
    ymd = dt.strftime('%y%m%d')
    return (
        f"X AI 日报 {ymd} 版。\n"
        f"这次整理了 {cards_count} 张图，重点看 coding agent、OpenClaw、Claude Code、评测工具和安全风险信号。\n"
        "这一版正文尽量把原文里真正发生了什么讲清楚，不只停留在摘要。"
    )


# ---------------------------------------------------------------------------
# Step 5: Git commit
# ---------------------------------------------------------------------------

def git_commit(date_str: str, variant: str = 'square-9') -> Optional[str]:
    """Stage generated files and commit. Returns commit hash or None."""
    card_dir = XHS_DIR / f'{date_str}-{variant}'
    log_dir = ROOT / 'xiaohongshu' / 'published' / 'x-ai-daily'

    paths_to_add = []
    if card_dir.exists():
        paths_to_add.append(str(card_dir))
    if log_dir.exists():
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

    msg = f'Add Xiaohongshu cards for X AI Daily {date_str}'
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
        description='Pipeline: X AI Daily → Xiaohongshu square cards → publish.',
    )
    parser.add_argument('--date', required=True, help='Date like 2026-03-17')
    parser.add_argument('--title', default=None, help='Xiaohongshu title (<=20 chars)')
    parser.add_argument('--content', default=None, help='Post content body')
    parser.add_argument('--variant', default='square-9', help='Image folder suffix')
    parser.add_argument('--tags', nargs='*', default=None, help='Tags for Xiaohongshu post')
    parser.add_argument('--max-cards', type=int, default=9, help='Max number of cards (default 9)')
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
        items = parse_daily_markdown(md_text)
        if not items:
            print('ERROR: No items parsed from daily file.', file=sys.stderr)
            return 1
        print(f'  Found {len(items)} items')

        print(f'[2/4] Writing card markdowns to {out_dir.name}/ ...')
        write_cards(date_str, items, variant, max_cards=args.max_cards)

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
