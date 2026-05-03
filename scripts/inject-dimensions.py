#!/usr/bin/env python3
"""用文本注入方式为 soul YAML 添加三维标签，保留所有 multiline 格式。"""
import os
import re

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOULS_DIR = os.path.join(SKILL_DIR, "souls")

MIGRATION_MAP = {
    "列宁":      ("充分", ["批判型", "组织型", "分析型"], "可传输"),
    "毛泽东":    ("充分", ["组织型", "批判型", "叙事型"], "嵌入型"),
    "邓小平":    ("充分", ["建设型", "分析型"], "可传输"),
    "鲁迅":      ("充分", ["批判型", "叙事型"], "人格型"),
    "费曼":      ("充分", ["分析型", "批判型"], "可传输"),
    "波伏娃":    ("充分", ["批判型", "叙事型", "分析型"], "可传输"),
    "法农":      ("充分", ["批判型", "组织型"], "嵌入型"),
    "伊本赫勒敦": ("充分", ["分析型"], "可传输"),
    "稻盛和夫":   ("充分", ["建设型", "分析型"], "可传输"),
    "未明子":    ("充分", ["批判型", "组织型"], "嵌入型"),
    "庄子":      ("充分", ["批判型"], "人格型"),
    "Karpathy":  ("充分", ["分析型"], "可传输"),
    "黄仁勋":    ("充分", ["建设型", "分析型"], "嵌入型"),
    "马斯克":    ("充分", ["建设型"], "嵌入型"),
    "乔布斯":    ("中等", ["建设型", "叙事型"], "人格型"),
    "罗永浩":    ("充分", ["叙事型"], "人格型"),
    "海绵宝宝":  ("充分", ["情绪型", "叙事型"], "人格型"),
    "祝鹤槐":    ("充分", ["组织型", "情绪型"], "人格型"),
}

dry_run = "--dry-run" in __import__("sys").argv

for fname in sorted(os.listdir(SOULS_DIR)):
    if not fname.endswith(".yaml"):
        continue
    fpath = os.path.join(SOULS_DIR, fname)
    with open(fpath, "r") as f:
        text = f.read()

    name_match = re.search(r'^name:\s*(.+)', text, re.MULTILINE)
    if not name_match:
        continue
    name = name_match.group(1).strip()
    if name not in MIGRATION_MAP:
        print(f"  ⚠ {name}: 无映射")
        continue

    info_suf, func_doms, meth_trans = MIGRATION_MAP[name]

    # 1. grade: → legacy_grade:
    if '\ngrade:' in text and '\nlegacy_grade:' not in text:
        text = text.replace('\ngrade:', '\nlegacy_grade:')

    # 2. grade_reason: → legacy_grade_reason:
    if '\ngrade_reason:' in text and '\nlegacy_grade_reason:' not in text:
        text = text.replace('\ngrade_reason:', '\nlegacy_grade_reason:')

    # 3. 在 legacy_grade_reason: | 块结束后注入三维标签
    # 找到 grade_reason 块的结束位置（下一个顶级字段开始处）
    # 简单策略：在 refined_at 行后注入
    if '\ninfo_sufficiency:' not in text:
        func_str = str(func_doms)
        injection = f"""info_sufficiency: {info_suf}
function_domains: {func_str}
methodology_transferability: {meth_trans}
"""
        # 找到 refined_at 或 reviewed_at 行后插入
        for anchor in ["reviewed_at:", "refined_at:"]:
            pattern = rf'^({anchor}\s*.+)$'
            m = re.search(pattern, text, re.MULTILINE)
            if m:
                insert_pos = m.end()
                text = text[:insert_pos] + "\n" + injection + text[insert_pos:]
                break

    if not dry_run:
        with open(fpath, "w") as f:
            f.write(text)
    print(f"  ✅ {name}: {info_suf} | {'+'.join(func_doms)} | {meth_trans}")

if dry_run:
    print(f"\n[dry-run] 预览模式")
else:
    print(f"\n✅ 完成")
