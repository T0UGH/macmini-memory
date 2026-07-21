#!/usr/bin/env python3
"""Validate Product Hunt AI Daily 输出质量。

检查项：
1. 文件存在且非空
2. 产品数量合理（0 也允许，但需有说明）
3. 每个条目必填字段完整
4. 中文化质量（不能全是英文）
5. "为什么值得看"不能空泛
"""
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CONFIG = json.loads((SCRIPT_DIR / 'config_product_hunt.json').read_text())
OUTPUT_DIR = Path(CONFIG['output_dir'])
TZ_CST = timezone(timedelta(hours=8))
TODAY = datetime.now(TZ_CST).strftime('%Y-%m-%d')

GENERIC_PHRASES = [
    '命中 AI 方向',
    '命中 AI 方向关键词',
    '待分析',
    '值得关注',
    '有潜力',
]


def validate():
    errors = []
    warnings = []

    # 1. 文件存在
    md_path = OUTPUT_DIR / f'{TODAY}.md'
    if not md_path.exists():
        errors.append(f'输出文件不存在：{md_path}')
        return report(errors, warnings)

    content = md_path.read_text()
    if len(content.strip()) < 50:
        errors.append(f'输出文件内容过短：{len(content)} 字符')
        return report(errors, warnings)

    # 2. 标题格式
    if f'# Product Hunt AI Daily | {TODAY}' not in content:
        warnings.append(f'标题格式不符预期（缺少日期 {TODAY}）')

    # 3. 今日判断
    if '## 今日判断' not in content:
        errors.append('缺少"今日判断"段落')

    # 4. 产品条目检查
    product_sections = re.findall(r'### \d+\. (.+)', content)
    if not product_sections:
        # 允许 0 个产品，但需有说明
        if '高信号' not in content and '偏少' not in content:
            warnings.append('没有产品条目，且缺少"今天高信号不多"的说明')
    else:
        # 检查每个条目
        sections = re.split(r'### \d+\. ', content)[1:]  # 跳过第一段
        for i, section in enumerate(sections):
            name = product_sections[i] if i < len(product_sections) else f'#{i+1}'
            # 必填字段
            if '它是做什么的' not in section:
                errors.append(f'{name}: 缺少"它是做什么的"')
            if '为什么值得看' not in section:
                errors.append(f'{name}: 缺少"为什么值得看"')

            # 中文化检查
            desc_match = re.search(r'它是做什么的：(.+)', section)
            if desc_match:
                desc = desc_match.group(1)
                chn = len(re.findall(r'[\u4e00-\u9fff]', desc))
                if chn < 3:
                    warnings.append(f'{name}: "它是做什么的"中文字符过少（{chn}）')

            # 空泛检查
            why_match = re.search(r'为什么值得看：(.+)', section)
            if why_match:
                why = why_match.group(1).strip()
                if why in GENERIC_PHRASES or len(why) < 10:
                    warnings.append(f'{name}: "为什么值得看"过于空泛：{why[:50]}')

    # 5. 数据源标注
    if '数据源' not in content:
        warnings.append('缺少数据源标注')

    return report(errors, warnings)


def report(errors, warnings):
    result = {
        'date': TODAY,
        'output_md': str(OUTPUT_DIR / f'{TODAY}.md'),
        'errors': errors,
        'warnings': warnings,
        'ok': len(errors) == 0,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result['ok'] else 1)


if __name__ == '__main__':
    validate()
