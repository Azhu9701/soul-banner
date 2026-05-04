#!/usr/bin/env python3
"""清理体系残留 v2 — 深度清洗 gold_review / 审查记录 / _match_summary"""

import yaml
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
REGISTRY_PATH = SKILL_DIR / "registry.yaml"
SOULS_DIR = SKILL_DIR / "souls"

# ── 替换规则（按顺序应用）──
REPLACEMENTS = [
    # 裁决标记
    (r'维持金魂🟡[，。、]?\s*', ''),
    (r'维持金魂[，。、]?\s*', ''),
    (r'升金魂🟡[，。、]?\s*', ''),
    (r'升金魂[，。、]?\s*', ''),
    (r'维持银魂🥈[，。、]?\s*', ''),
    (r'维持银魂[，。、]?\s*', ''),
    (r'维持紫魂[，。、]?\s*', ''),
    (r'维持蓝魂[🔵，。、]?\s*', ''),
    (r'维持蓝魂[，。、]?\s*', ''),
    (r'维持绿魂[，。、]?\s*', ''),
    (r'维持白魂[，。、]?\s*', ''),
    # 引用
    (r'金魂候选[。，]?\s*', ''),
    (r'满足金魂三条标准[：:]\s*', ''),
    (r'金魂三条', ''),
    (r'\[条件金魂\]\s*', ''),
    (r'金魂中最[^\s，。]+的\s*', ''),
    # 两金魂/三金魂等
    (r'两金魂共存', '两魂共存'),
    (r'三金魂', '三魂'),
    # 金魂(1)/金魂(2)/金魂(3) — 旧的标准引用
    (r'金魂\(1\)', '标准1'),
    (r'金魂\(2\)', '标准2'),
    (r'金魂\(3\)', '标准3'),
    # 银魂相关
    (r'银魂🥈[，。、]?\s*', ''),
    (r'银魂[，。、]?\s*', ''),
    # 紫魂相关
    (r'紫魂[，。、]?\s*', ''),
    (r'定位[：:]紫魂[。]?', ''),
    (r'维持紫魂[，。]?\s*', ''),
    # 蓝魂相关
    (r'蓝魂[🔵，。、]?\s*', ''),
    (r'[：:]\s*蓝魂[🔵\s]*[。，]?\s*', ''),
    # 体系术语
    (r'论证[：:][^。\n]*[。]?', ''),
    (r'论证成立[，。]?\s*', ''),
    (r'原论证[：:]?\s*', ''),
    (r'降品审查[（(]金→银[）)]', '重新审查'),
    (r'降品[。，]?\s*', ''),
    (r'不降品[。，]?\s*', ''),
    (r'距金魂差\d+分[，。]?\s*', ''),
    (r'金魂=\d+分[，。]?\s*', ''),
    # 文件路径中的金魂
    (r'金魂互审', '魂互审'),
    # 通用金魂/银魂引用（在非代码上下文中）
    (r'搭配马克思主义金魂', '搭配马克思主义信息充分的魂'),
    (r'搭配金魂', '搭配信息充分的魂'),
]

def clean_text(text):
    if not text:
        return text
    for pattern, replacement in REPLACEMENTS:
        text = re.sub(pattern, replacement, text)
    # 清理多余空白和标点
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'  +', ' ', text)
    text = re.sub(r'[，。]\s*[，。]', '。', text)
    text = re.sub(r'^\s*[，。]\s*', '', text)
    return text.strip()

def fix_registry():
    print("=" * 60)
    print("1. 深度清洗 registry.yaml")
    with open(REGISTRY_PATH) as f:
        reg = yaml.safe_load(f)

    changes = 0
    for s in reg.get('魂魄', []):
        name = s.get('name', '?')

        # 清洗 gold_review
        if 'gold_review' in s and s['gold_review']:
            old = s['gold_review']
            new = clean_text(old)
            if old != new:
                s['gold_review'] = new
                changes += 1
                print(f"  {name}.gold_review 清洗")

        # 清洗 审查记录
        if '审查记录' in s:
            for r in s['审查记录']:
                if '裁定' in r and r['裁定']:
                    old = r['裁定']
                    new = clean_text(old)
                    if old != new:
                        r['裁定'] = new
                        changes += 1
                        print(f"  {name}.审查记录.裁定 清洗: {old[:40]}... → {new[:40]}...")
                if '报告' in r and r['报告']:
                    r['报告'] = r['报告'].replace('金魂互审', '魂互审')

        # 清洗 notes
        if 'notes' in s and s['notes']:
            old = s['notes']
            new = clean_text(old)
            if old != new:
                s['notes'] = new
                changes += 1
                print(f"  {name}.notes 清洗")

    # 保存
    with open(REGISTRY_PATH, 'w') as f:
        yaml.dump(reg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    print(f"  registry.yaml: {changes} 处修改")

def fix_soul_yamls():
    print("\n" + "=" * 60)
    print("2. 深度清洗 soul YAML 文件")
    total = 0

    for yaml_file in sorted(SOULS_DIR.glob("*.yaml")):
        name = yaml_file.stem
        with open(yaml_file) as f:
            content = f.read()

        original = content
        changes = []

        # 清洗 gold_review
        content = re.sub(
            r'(^gold_review:.*?)(?=^\w+:\s|\Z)',
            lambda m: clean_text(m.group(1)),
            content,
            flags=re.MULTILINE | re.DOTALL
        )

        # 清洗 review_verdict
        content = re.sub(
            r'(^review_verdict:.*?)(?=^\w+:\s|\Z)',
            lambda m: clean_text(m.group(1)),
            content,
            flags=re.MULTILINE | re.DOTALL
        )

        # 清洗 _match_summary 中的金魂前缀
        content = re.sub(r'^(_match_summary:.*?)金魂\s*\|', r'\1', content, flags=re.MULTILINE)

        # 清洗 notes
        content = re.sub(
            r'(^notes:.*?)(?=^\w+:\s|\Z)',
            lambda m: clean_text(m.group(1)),
            content,
            flags=re.MULTILINE | re.DOTALL
        )

        # 清洗 grade_reason (仍然存在的)
        if 'grade_reason:' in content:
            content = re.sub(
                r'^grade_reason:.*?(?=^\w+:\s|\Z)',
                '',
                content,
                flags=re.MULTILINE | re.DOTALL
            )

        # 清洗 审查记录 块
        content = re.sub(r'维持金魂🟡', '', content)
        content = re.sub(r'维持金魂', '', content)
        content = re.sub(r'升金魂🟡', '', content)
        content = re.sub(r'升金魂', '', content)
        content = re.sub(r'维持银魂🥈', '', content)
        content = re.sub(r'维持银魂', '', content)
        content = re.sub(r'维持紫魂', '', content)
        content = re.sub(r'维持蓝魂[🔵\s]*', '', content)
        content = re.sub(r'金魂互审', '魂互审', content)
        content = re.sub(r'金魂候选', '', content)
        content = re.sub(r'银魂🥈', '', content)
        content = re.sub(r'银魂', '', content)

        if content != original:
            with open(yaml_file, 'w') as f:
                f.write(content)
            file_changes = content.count('\n') - original.count('\n')  # rough
            total += 1
            print(f"  {name}.yaml: 已清洗")

    print(f"  soul YAMLs: {total} 文件修改")

def final_check():
    print("\n" + "=" * 60)
    print("3. 最终残留检查")
    import subprocess

    # Check registry
    r = subprocess.run(
        ['grep', '-c', '金魂|银魂|蓝魂|紫魂|绿魂|白魂|[^说]|grade_reason'],
        cwd=str(SKILL_DIR), capture_output=True, text=True,
        input='registry.yaml'
    )
    # Simpler approach:
    for path in [REGISTRY_PATH] + list(SOULS_DIR.glob("*.yaml")):
        with open(path) as f:
            content = f.read()
        # Find remaining grade references
        lines_with_grades = []
        for i, line in enumerate(content.split('\n'), 1):
            if re.search(r'金魂|银魂|蓝魂|紫魂|绿魂|白魂|(?!说明)', line):
                # Skip summon_prompt/mind/voice - these are soul self-descriptions
                lines_with_grades.append(f"  L{i}: {line.strip()[:100]}")
        if lines_with_grades:
            print(f"\n{path.relative_to(SKILL_DIR)}: {len(lines_with_grades)} 残留行")
            for l in lines_with_grades[:5]:
                print(l)
            if len(lines_with_grades) > 5:
                print(f"  ... 及其他 {len(lines_with_grades) - 5} 行")

if __name__ == "__main__":
    fix_registry()
    fix_soul_yamls()
    final_check()
    print("\n✅ 第二轮清洗完成")
