#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

ROOT = Path('/Users/haha/.openclaw/workspace/github-daily')
CONFIG = json.loads((ROOT / 'config.json').read_text())
RUNS = ROOT / 'runs'


def latest_run_json():
    files = sorted(RUNS.glob('*.json'))
    if not files:
        raise SystemExit('ERROR: runs/ 下没有 json 结果文件')
    return files[-1]


def count_english_ratio(text: str) -> float:
    english = len(re.findall(r'[A-Za-z]{3,}', text))
    chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
    if chinese == 0:
        return 999.0
    return english / chinese


def main():
    path = latest_run_json()
    data = json.loads(path.read_text())
    errors = []
    warnings = []

    core = data.get('core', [])
    if len(core) != len(CONFIG['core_release_repos']):
        errors.append(f"核心仓数量不对：期望 {len(CONFIG['core_release_repos'])}，实际 {len(core)}")

    core_repos = [x.get('repo') for x in core]
    for repo in CONFIG['core_release_repos']:
        if repo not in core_repos:
            errors.append(f"缺少核心仓：{repo}")

    discovery = data.get('discovery', [])
    if len(discovery) != CONFIG['discovery_count']:
        warnings.append(f"新仓候选数量不是 {CONFIG['discovery_count']}，实际为 {len(discovery)}")

    for item in discovery:
        stars = int(item.get('stargazersCount') or 0)
        if stars < CONFIG['min_stars']:
            errors.append(f"发现低于最小 stars 门槛的仓：{item.get('fullName')} ({stars})")

    md_path = path.with_suffix('.md')
    if not md_path.exists():
        errors.append(f"缺少对应 markdown 输出：{md_path.name}")
    else:
        md = md_path.read_text()
        ratio = count_english_ratio(md)
        if ratio > 0.20:
            warnings.append(f"英文占比偏高：{ratio:.2f}")
        if '## 核心仓库' not in md or '## 新仓候选（10 个）' not in md:
            errors.append('markdown 结果缺少关键章节')

    report = {
        'run_json': path.name,
        'run_md': md_path.name,
        'errors': errors,
        'warnings': warnings,
        'ok': len(errors) == 0,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
