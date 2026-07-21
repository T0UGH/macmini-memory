#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path

ROOT = Path('/Users/haha/workspace/memory')
XHS_DIR = ROOT / 'xiaohongshu' / 'github-ai-daily'

NOISY_README_PATTERNS = [
    'Quickstart', 'Table of Contents', 'Fork of', 'Please see',
    'FREE FOR PERSONAL USE', 'Documentation', 'English |', '中文 |', '日本語'
]
BAD_SUMMARY_PATTERNS = [
    '命中协议', '命中 subagent', '命中 worktree', '命中 repo memory', '命中 coding agent'
]


def section_text(text: str, heading: str) -> str:
    m = re.search(rf'\*\*{re.escape(heading)}\*\*\n(.*?)(?:\n\*\*|\Z)', text, re.S)
    return m.group(1).strip() if m else ''


def validate_card(path: Path) -> list[str]:
    errors = []
    text = path.read_text()
    is_core = '发布时间：' in text

    if is_core:
        for heading in ['这次具体改了什么', '这意味着什么', '原始证据', '一句判断']:
            if f'**{heading}**' not in text:
                errors.append(f'{path.name}: 缺少核心卡段落 {heading}')
        evidence = section_text(text, '原始证据')
        if evidence.count('\n- ') > 0:
            bullet_count = evidence.count('\n- ') + 1
        else:
            bullet_count = 1 if evidence else 0
        if bullet_count > 1:
            errors.append(f'{path.name}: 原始证据超过 1 条')
    else:
        for heading in ['它是做什么的', 'README 要点', '和主线的关系', '一句判断']:
            if f'**{heading}**' not in text:
                errors.append(f'{path.name}: 缺少新仓卡段落 {heading}')
        readme = section_text(text, 'README 要点')
        for pattern in NOISY_README_PATTERNS:
            if pattern in readme:
                errors.append(f'{path.name}: README 要点仍含噪音词 {pattern}')
                break
        summary = section_text(text, '一句判断')
        for pattern in BAD_SUMMARY_PATTERNS:
            if summary.startswith(pattern):
                errors.append(f'{path.name}: 一句判断仍像内部标签 -> {summary}')
                break
    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', required=True)
    ap.add_argument('--variant', default='square-9')
    args = ap.parse_args()

    card_dir = XHS_DIR / f'{args.date}-{args.variant}'
    if not card_dir.exists():
        print(f'ERROR: card dir not found: {card_dir}', file=sys.stderr)
        raise SystemExit(1)

    errors = []
    md_files = sorted(p for p in card_dir.glob('*.md') if p.name != 'README.md')
    for path in md_files:
        errors.extend(validate_card(path))

    print({'date': args.date, 'variant': args.variant, 'cards': len(md_files), 'errors': errors, 'ok': not errors})
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
