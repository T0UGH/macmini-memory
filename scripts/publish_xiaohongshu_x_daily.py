#!/usr/bin/env python3
"""Publish X AI Daily square cards to Xiaohongshu via mcporter."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List

ROOT = Path('/Users/haha/workspace/memory')
XHS_ROOT = ROOT / 'xiaohongshu' / 'x-ai-daily'
PUBLISH_LOG_ROOT = ROOT / 'xiaohongshu' / 'published' / 'x-ai-daily'


def run(cmd: List[str], *, capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, text=True, capture_output=capture)


def find_images(date_str: str, variant: str) -> List[str]:
    folder = XHS_ROOT / f'{date_str}-{variant}'
    if not folder.exists():
        raise FileNotFoundError(f'Image folder not found: {folder}')
    images = sorted(str(p) for p in folder.glob('*.png'))
    if not images:
        raise FileNotFoundError(f'No PNG images found in: {folder}')
    return images


def build_mcporter_call(title: str, content: str, images: List[str], tags: List[str], visibility: str) -> str:
    def q(s: str) -> str:
        return json.dumps(s, ensure_ascii=False)

    images_expr = '[' + ', '.join(q(i) for i in images) + ']'
    tags_expr = '[' + ', '.join(q(t) for t in tags) + ']'
    return (
        'xiaohongshu.publish_content('
        f'title: {q(title)}, '
        f'content: {q(content)}, '
        f'images: {images_expr}, '
        f'tags: {tags_expr}, '
        f'visibility: {q(visibility)}'
        ')'
    )


def write_publish_log(date_str: str, payload: dict, result: dict) -> Path:
    PUBLISH_LOG_ROOT.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    path = PUBLISH_LOG_ROOT / f'{date_str}_{ts}.json'
    path.write_text(json.dumps({
        'publishedAt': datetime.now().astimezone().isoformat(),
        'payload': payload,
        'result': result,
    }, ensure_ascii=False, indent=2) + '\n')
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description='Publish X AI Daily square cards to Xiaohongshu via mcporter.')
    parser.add_argument('--date', required=True, help='Date like 2026-03-17')
    parser.add_argument('--title', required=True, help='Xiaohongshu title, <=20 chars')
    parser.add_argument('--content', required=True, help='Post content body')
    parser.add_argument('--tags', nargs='*', default=['AI日报', 'AI情报', 'CodingAgent', 'ClaudeCode', 'OpenClaw'])
    parser.add_argument('--variant', default='square-9', help='Image folder suffix, default: square-9')
    parser.add_argument('--visibility', default='公开可见', help='Visibility, default: 公开可见')
    parser.add_argument('--timeout-ms', type=int, default=300000, help='mcporter timeout in ms')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    images = find_images(args.date, args.variant)
    payload = {
        'date': args.date,
        'title': args.title,
        'content': args.content,
        'tags': args.tags,
        'variant': args.variant,
        'visibility': args.visibility,
        'images': images,
    }

    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    call_expr = build_mcporter_call(args.title, args.content, images, args.tags, args.visibility)
    proc = run([
        'mcporter', 'call', '--timeout', str(args.timeout_ms), call_expr
    ])
    stdout = proc.stdout.strip()
    result = {'stdout': stdout}
    log_path = write_publish_log(args.date, payload, result)

    print(stdout)
    print(f'LOG_FILE={log_path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
