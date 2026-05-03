#!/usr/bin/env python3
""" registry ↔ soul YAML ↔ review reports 三方交叉校验与自动修复

用法:
  python3 scripts/cross-validate.py              # 只检查，不修复
  python3 scripts/cross-validate.py --fix        # 检查并自动修复

检查项目:
  1. soul YAML 中三维标签（info_sufficiency/function_domains/methodology_transferability）与 registry 是否一致
  2. soul YAML 是否有 reviewed_at/reviewed_by/review_verdict
  3. registry 中是否有 gold_review（金/银/紫魂）
  4. reviews/ 目录中存在的审查报告是否在 registry 审查记录中有对应条目
  5. 审查记录的裁定与 soul YAML 的 review_verdict 是否一致
"""

import yaml
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict

from utils import load_yaml, save_yaml

BASE = Path(__file__).resolve().parent.parent
REGISTRY_PATH = BASE / 'registry.yaml'
SOULS_DIR = BASE / 'souls'
REVIEWS_DIR = BASE / 'reviews'

REVIEW_SOUL_MAP = {
    '波伏娃': ['幡主审查-列宁审波伏娃-2026-04-30.md'],
    '稻盛和夫': ['列宁审稻盛和夫-2026-04-30.md'],
    '法农': ['列宁审法农-2026-04-30.md'],
    '费曼': ['幡主审查-列宁审费曼-2026-04-29.md', '新魂审查-毛泽东审费曼乔布斯-2026-04-29.md'],
    '黄仁勋': ['幡主审查-列宁审黄仁勋-2026-04-30.md'],
    '罗永浩': ['幡主审查-列宁审罗永浩-2026-04-29.md'],
    '鲁迅': ['列宁审鲁迅-2026-04-30.md'],
    '马斯克': ['幡主审查-列宁审马斯克-2026-04-29.md'],
    '毛泽东': ['充分度魂互审-列宁审毛泽东-2026-04-29.md'],
    '乔布斯': ['幡主审查-列宁审乔布斯-2026-04-29.md', '新魂审查-毛泽东审费曼乔布斯-2026-04-29.md'],
    '伊本赫勒敦': ['列宁审伊本赫勒敦-2026-04-30.md'],
    '未明子': [
        '列宁审未明子-2026-05-01.md',
        '列宁审未明子-第二次-2026-05-01.md',
        '列宁审未明子-第三次-2026-05-01.md',
        '幡主审查-列宁审未明子-2026-04-30.md',
    ],
    'Karpathy': ['新魂互审-费曼审Karpathy-2026-04-29.md'],
    '列宁': [
        '充分度魂互审-费曼审列宁-2026-05-01.md',
        '充分度魂互审-鲁迅审列宁-2026-05-01.md',
        '反向审查-未明子审列宁-2026-05-01.md',
    ],
}


def check(fix=False):
    errors = []
    warnings = []
    fixes_applied = []

    # ── Load data ──
    registry = load_yaml(REGISTRY_PATH)
    souls_registry = {s['name']: s for s in registry.get('魂魄', [])}
    souls_yaml = {}
    for fpath in SOULS_DIR.glob('*.yaml'):
        data = load_yaml(fpath)
        souls_yaml[data['name']] = {'path': fpath, 'data': data}

    review_files = set(os.listdir(REVIEWS_DIR))

    # ── Check 1: 3D fields consistency ──
    for name, entry in souls_registry.items():
        if name not in souls_yaml:
            errors.append(f'Soul {name} in registry but YAML missing')
            continue
        for field in ['info_sufficiency', 'function_domains', 'methodology_transferability']:
            reg_val = entry.get(field)
            yaml_val = souls_yaml[name]['data'].get(field)
            if reg_val != yaml_val:
                msg = f'3D mismatch for {name}: registry.{field}={reg_val} YAML={yaml_val}'
                if fix:
                    # 以 YAML 为准修复 registry
                    entry[field] = yaml_val
                    fixes_applied.append(f'Fixed (YAML→registry): {msg}')
                else:
                    errors.append(msg)

    # ── Check 2: soul YAML review fields ──
    for name, info in souls_yaml.items():
        data = info['data']
        missing = []
        for field in ['reviewed_at', 'reviewed_by', 'review_verdict']:
            if field not in data or not data[field]:
                missing.append(field)
        if missing:
            info_suf = data.get('info_sufficiency', '?')
            # 信息充分度不足的魂无审查要求
            if info_suf == '不足':
                continue
            warnings.append(f'Soul YAML {name} (info_suf={info_suf}) missing: {missing}')

    # ── Check 3: registry gold_review for 信息充分度=充分的魂 ──
    for name, entry in souls_registry.items():
        if entry.get('info_sufficiency') == '充分':
            if 'gold_review' not in entry or not entry.get('gold_review'):
                if name in souls_yaml:
                    ydata = souls_yaml[name]['data']
                    verdict = ydata.get('review_verdict', '')
                    if verdict:
                        if fix:
                            entry['gold_review'] = verdict
                            fixes_applied.append(f'Added gold_review for {name} from YAML review_verdict')
                        else:
                            errors.append(f'Registry missing gold_review for {name}')
                    else:
                        warnings.append(f'Registry missing gold_review for {name}, no YAML verdict to source')

    # ── Check 4: review reports referenced in registry ──
    for name, expected_files in REVIEW_SOUL_MAP.items():
        for f in expected_files:
            if f not in review_files:
                warnings.append(f'Review report {f} expected but not found on disk')

    # ── Check 5: 审查记录 completeness vs actual review files ──
    for name, expected_files in REVIEW_SOUL_MAP.items():
        if name not in souls_registry:
            continue
        entry = souls_registry[name]
        records = entry.get('审查记录', [])
        recorded_files = set()
        for r in records:
            if isinstance(r, dict):
                report = r.get('报告', '')
                # Normalize: strip reviews/ prefix if present
                recorded_files.add(report.replace('reviews/', ''))
        actual = set(expected_files)
        missing_records = actual - recorded_files
        if missing_records:
            if fix:
                new_records = list(records)
                for fname in sorted(missing_records):
                    new_records.append({
                        '审查官': '见审查报告',
                        '日期': '见审查报告',
                        '报告': f'reviews/{fname}',
                    })
                entry['审查记录'] = new_records
                fixes_applied.append(f'Added {len(missing_records)} 审查记录 entries for {name}')
            else:
                warnings.append(f'{name}: 审查记录 missing entries for: {missing_records}')

    # ── Save if fixed ──
    if fix and fixes_applied:
        save_yaml(REGISTRY_PATH, registry)
        print(f'Saved registry with {len(fixes_applied)} fixes')

    # ── Report ──
    print(f'\n{"="*60}')
    print(f'Registry ↔ Soul YAML 交叉校验报告 — {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print(f'总魂魄数: {len(souls_registry)} | 魂YAML数: {len(souls_yaml)} | 审查报告数: {len(review_files)}')
    print(f'{"="*60}')

    if errors:
        print(f'\n❌ 错误 ({len(errors)}):')
        for e in errors:
            print(f'  • {e}')
    else:
        print(f'\n✅ 无错误')

    if warnings:
        print(f'\n⚠️  警告 ({len(warnings)}):')
        for w in warnings:
            print(f'  • {w}')
    else:
        print(f'\n✅ 无警告')

    if fixes_applied:
        print(f'\n🔧 已修复 ({len(fixes_applied)}):')
        for f in fixes_applied:
            print(f'  • {f}')

    return len(errors) == 0


if __name__ == '__main__':
    fix_mode = '--fix' in sys.argv
    ok = check(fix=fix_mode)
    sys.exit(0 if ok else 1)
