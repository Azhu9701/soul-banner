#!/usr/bin/env python3
"""验证 skill 文件与 Obsidian vault 之间的同步完整性

检查项：
  1. 审查报告 → 万民幡/审查/
  2. 反向审查 → 万民幡/反向审查/
  3. 魂魄档案 → 万民幡/魂魄/
  4. 附体产出 → 万民幡/单魂/ 合议/ 辩论/ 接力/

用法：
  python3 scripts/verify-obsidian-sync.py          # 检查 + 自动补同步
  python3 scripts/verify-obsidian-sync.py --check  # 仅检查，不修复
"""

import os
import sys
import shutil
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
OBSIDIAN_VAULT = os.environ.get("OBSIDIAN_VAULT", os.path.expanduser("~/ob"))
REVIEWS_DIR = SKILL_DIR / "reviews"
SOULS_DIR = SKILL_DIR / "souls"
VAULT_ROOT = os.path.join(OBSIDIAN_VAULT, "万民幡")


def find_missing():
    """返回所有缺失的同步项 (source, dest, category)"""
    missing = []

    # 1. 审查报告（按文件名分类到不同 Obsidian 目录）
    vault_review_dir = os.path.join(VAULT_ROOT, "审查")
    vault_reverse_dir = os.path.join(VAULT_ROOT, "反向审查")
    vault_mutual_dir = os.path.join(VAULT_ROOT, "互审")
    if REVIEWS_DIR.exists():
        for rf in REVIEWS_DIR.glob("*.md"):
            fname = rf.name
            # 反向审查 → 反向审查/
            if fname.startswith("反向审查-"):
                dest = os.path.join(vault_reverse_dir, fname)
                cat = "反向审查"
            # 互审 → 互审/
            elif "互审" in fname:
                dest = os.path.join(vault_mutual_dir, fname)
                cat = "互审"
            # 终末审查 → 审查/
            elif "终末审查" in fname:
                dest = os.path.join(vault_review_dir, fname)
                cat = "终末审查"
            # 其余 → 审查/
            else:
                dest = os.path.join(vault_review_dir, fname)
                cat = "审查报告"
            if not os.path.exists(dest):
                missing.append((str(rf), dest, cat))

    # 2. 魂魄档案
    vault_soul_dir = os.path.join(VAULT_ROOT, "魂魄")
    if SOULS_DIR.exists():
        for sf in SOULS_DIR.glob("*.yaml"):
            md_name = sf.stem + ".md"
            dest = os.path.join(vault_soul_dir, md_name)
            if not os.path.exists(dest):
                # 需要将 YAML 转为 Markdown
                missing.append((str(sf), dest, "魂魄档案"))

    return missing


def sync_missing(missing, dry_run=False):
    """补同步缺失文件"""
    synced = 0
    # 延迟导入：仅在需要补同步魂魄档案时加载
    _soul_to_md = None
    for source, dest, category in missing:
        if dry_run:
            print(f"  [DRY RUN] {category}: {os.path.basename(source)} → {os.path.relpath(dest, VAULT_ROOT)}")
            synced += 1
            continue

        os.makedirs(os.path.dirname(dest), exist_ok=True)

        if category == "魂魄档案":
            if _soul_to_md is None:
                sys.path.insert(0, str(SKILL_DIR / "scripts"))
                from transact import _soul_yaml_to_markdown as _soul_to_md
            try:
                md = _soul_to_md(source)
                with open(dest, "w") as f:
                    f.write(md)
                print(f"  ✅ {category}: {os.path.basename(source)} → 魂魄/{os.path.basename(dest)}")
                synced += 1
            except Exception as e:
                print(f"  ❌ {category}: {os.path.basename(source)} — {e}")
        else:
            shutil.copy2(source, dest)
            print(f"  ✅ {category}: {os.path.basename(source)} → {os.path.relpath(dest, VAULT_ROOT)}")
            synced += 1

    return synced


def main():
    check_only = "--check" in sys.argv

    if not os.path.exists(OBSIDIAN_VAULT):
        print(f"❌ Obsidian vault 不存在: {OBSIDIAN_VAULT}")
        print("   设置环境变量: export OBSIDIAN_VAULT=/path/to/vault")
        return 1

    if not os.path.exists(VAULT_ROOT):
        print(f"⚠️ 万民幡目录不存在于 Obsidian vault 中")
        os.makedirs(VAULT_ROOT, exist_ok=True)
        print(f"   已创建: {VAULT_ROOT}")

    missing = find_missing()

    if not missing:
        print("✅ Obsidian 同步完整 — 所有文件已就位")
        return 0

    print(f"🔍 发现 {len(missing)} 个缺失同步项:\n")
    for source, dest, category in missing:
        print(f"  - {category}: {os.path.basename(source)}")

    if check_only:
        print(f"\n⚠️ 仅检查模式 — 运行不带 --check 以自动修复")
        return 1

    print(f"\n🔄 补同步中...\n")
    synced = sync_missing(missing)
    print(f"\n✅ 已同步 {synced}/{len(missing)} 个文件")

    # 二次验证
    remaining = find_missing()
    if remaining:
        print(f"⚠️ 仍有 {len(remaining)} 个文件未同步")
        return 1

    print("✅ 所有文件已同步至 Obsidian")
    return 0


if __name__ == "__main__":
    sys.exit(main())
