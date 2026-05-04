#!/usr/bin/env python3
"""将系统迁移到系统。

用法：python3 scripts/migrate-grade-system.py [--dry-run]
"""
import os
import sys
import yaml

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_PATH = os.path.join(SKILL_DIR, "registry.yaml")
SOULS_DIR = os.path.join(SKILL_DIR, "souls")

# 来自未明子表A的映射
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

dry_run = "--dry-run" in sys.argv

print("🔄 系统迁移：等级 → \n")

# ── 1. 更新 soul YAML ──
print("── Soul YAML ──")
updated_souls = 0
for fname in sorted(os.listdir(SOULS_DIR)):
    if not fname.endswith(".yaml"):
        continue
    fpath = os.path.join(SOULS_DIR, fname)
    with open(fpath) as f:
        soul = yaml.safe_load(f)

    name = soul.get("name", "")
    if name not in MIGRATION_MAP:
        print(f"  ⚠ {name}: 无映射，跳过")
        continue

    info_suf, func_doms, meth_trans = MIGRATION_MAP[name]

    # 保留原
    if "grade" in soul:
        soul["legacy_grade"] = soul.pop("grade")
    # 保留原 grade_reason
    if "grade_reason" in soul:
        soul["legacy_grade_reason"] = soul.pop("grade_reason")

    # 写入三维

    if not dry_run:
        with open(fpath, "w") as f:
            yaml.dump(soul, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    updated_souls += 1
    print(f"  ✅ {name}: {info_suf} | {'+'.join(func_doms)} | {meth_trans}")

# ── 2. 更新 registry.yaml ──
print("\n── Registry ──")
with open(REGISTRY_PATH) as f:
    registry = yaml.safe_load(f)

for s in registry.get("魂魄", []):
    name = s.get("name", "")
    if name not in MIGRATION_MAP:
        continue

    info_suf, func_doms, meth_trans = MIGRATION_MAP[name]

    if "grade" in s:
        s["legacy_grade"] = s.pop("grade")
    if "grade_symbol" in s:
        s.pop("grade_symbol", None)

# 更新版本
registry["版本"] = "2.0"
if not dry_run:
    with open(REGISTRY_PATH, "w") as f:
        yaml.dump(registry, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
print(f"  ✅ registry.yaml → 版本 2.0")

if dry_run:
    print(f"\n[dry-run] 将更新 {updated_souls} 个 soul YAML + registry.yaml")
else:
    print(f"\n✅ 迁移完成: {updated_souls} souls + registry")
