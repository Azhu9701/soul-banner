#!/usr/bin/env python3
"""万民幡 Memory 同步脚本

从 registry.yaml + call-records.yaml 自动生成 project memory 缓存文件，
保持 memory 与数据源一致。解决手动维护导致漂移的问题。

用法：
  python3 scripts/sync-memory.py --check    # 检查 memory 是否过期（不写入）
  python3 scripts/sync-memory.py --sync     # 同步 memory（覆盖写入）
  python3 scripts/sync-memory.py --diff     # 显示当前 registry 与 memory 差异

v2.0 — 体系（已废弃）。
"""

import os
import sys
from datetime import datetime, timezone
from collections import Counter

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_PATH = os.path.join(SKILL_DIR, "registry.yaml")
CALL_RECORDS_PATH = os.path.join(SKILL_DIR, "call-records.yaml")
MEMORY_DIR = os.path.join(os.path.expanduser("~"), ".claude/projects/-Users-huyi/memory")
CACHE_PATH = os.path.join(MEMORY_DIR, "project_soul_banner_registry_cache.md")

def load_data():
    try:
        import yaml
    except ImportError:
        print("ERROR: PyYAML not available", file=sys.stderr)
        sys.exit(1)

    with open(REGISTRY_PATH) as f:
        reg = yaml.safe_load(f.read())
    souls = reg.get("魂魄", [])

    records = []
    if os.path.exists(CALL_RECORDS_PATH):
        with open(CALL_RECORDS_PATH) as f:
            cr = yaml.safe_load(f.read())
        records = cr.get("召唤记录", []) if cr else []

    return souls, records

def build_cache(souls, records, timestamp):
    n = len(souls)

    # 分布
    sufficiency = {"充分": [], "中等": [], "不足": []}
    transferability = {"可传输": [], "嵌入型": [], "人格型": []}
    for s in souls:
        sufficiency.setdefault(sf, []).append(s["name"])
        transferability.setdefault(mt, []).append(s["name"])

    suf_lines = []
    for k in ["充分", "中等", "不足"]:
        if sufficiency.get(k):
            suf_lines.append(f"**{k}**({len(sufficiency[k])}): {', '.join(sufficiency[k])}")
    mt_lines = []
    for k in ["可传输", "嵌入型", "人格型"]:
        if transferability.get(k):
            mt_lines.append(f"**{k}**({len(transferability[k])}): {', '.join(transferability[k])}")

    # 召唤统计
    counts = Counter(r.get("soul") for r in records if isinstance(r, dict) and "soul" in r)
    eff_summary = {}
    for r in records:
        if not isinstance(r, dict):
            continue
        name = r.get("soul", "?")
        eff = r.get("effectiveness", "N/A")
        if name not in eff_summary:
            eff_summary[name] = {"有效": 0, "部分有效": 0, "无效": 0}
        eff_summary[name][eff] = eff_summary[name].get(eff, 0) + 1

    # 快速参考表 — 按信息 + 召唤次数排序
    def sort_key(s):
        return (sf_rank, -counts.get(s.get("name", ""), 0), s.get("name", ""))

    table_rows = []
    for s in sorted(souls, key=sort_key):
        name = s.get("name", "?")
        domains = ", ".join(s.get("domain", [])[:3])
        exclude = s.get("trigger_exclude_summary", "")
        if exclude and len(exclude) > 40:
            exclude = exclude[:40] + "..."
        table_rows.append(f"| {name} | {fds} | {mt} | {domains} | {exclude} |")

    # 召唤统计表 — 按召唤次数降序
    summon_rows = []
    zero_summons = []
    for s in sorted(souls, key=lambda x: (-counts.get(x.get("name", ""), 0), x.get("name", ""))):
        name = s.get("name", "?")
        count = counts.get(name, 0)
        if count > 0:
            eff = eff_summary.get(name, {})
            parts = []
            for k in ["有效", "部分有效", "无效"]:
                if eff.get(k, 0) > 0:
                    parts.append(f"{k}{eff[k]}")
            summon_rows.append(f"| {name} | {count} | {' '.join(parts)} |")
        else:
            zero_summons.append(name)

    if zero_summons:
        summon_rows.append(f"| {'/'.join(zero_summons)} | 0 | — |")

    cache = f"""---
name: 万民幡 Registry 热缓存
description: {n} 魂摘要缓存——用于简单查询和匹配阶段，避免每次读取完整 registry.yaml。v2.0 体系，已废弃。由 scripts/sync-memory.py 自动维护。
type: project
---

> **自动生成于 {timestamp}。** 此文件由 `scripts/sync-memory.py --sync` 从 `registry.yaml` 生成。

## 分布

**信息**: {', '.join(suf_lines)}
**方法论**: {', '.join(mt_lines)}
****: {fd_str}

## 快速参考

| 魂 | ismism | 关键领域 | 排除场景 |
|------|------|------|------|------|
{chr(10).join(table_rows)}

## 召唤统计

| 魂 | 次数 | 评级分布 |
|------|------|------|
{chr(10).join(summon_rows)}

---
*最后同步: {timestamp}*
"""
    return cache

def check_staleness():
    if not os.path.exists(CACHE_PATH):
        return True, "缓存文件不存在"

    cache_mtime = os.path.getmtime(CACHE_PATH)
    reg_mtime = os.path.getmtime(REGISTRY_PATH)
    records_mtime = os.path.getmtime(CALL_RECORDS_PATH) if os.path.exists(CALL_RECORDS_PATH) else 0

    if reg_mtime > cache_mtime:
        return True, f"registry.yaml 已更新 ({datetime.fromtimestamp(reg_mtime).strftime('%H:%M:%S')} > {datetime.fromtimestamp(cache_mtime).strftime('%H:%M:%S')})"
    if records_mtime > cache_mtime:
        return True, "call-records.yaml 已更新"

    return False, "缓存有效"

def show_diff():
    souls, records = load_data()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_cache = build_cache(souls, records, timestamp)

    if not os.path.exists(CACHE_PATH):
        print("缓存文件不存在。运行 --sync 创建。")
        return

    with open(CACHE_PATH) as f:
        old_cache = f.read()

    if old_cache == new_cache:
        print("✅ 缓存与数据源一致，无需同步。")
    else:
        print("❌ 缓存过期。差异摘要：")
        old_lines = set(old_cache.split("\n"))
        new_lines = set(new_cache.split("\n"))
        added = new_lines - old_lines
        removed = old_lines - new_lines
        if added:
            print(f"  新增 {len(added)} 行")
        if removed:
            print(f"  移除 {len(removed)} 行")
        print("运行 --sync 更新。")

def do_sync():
    souls, records = load_data()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cache = build_cache(souls, records, timestamp)

    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        f.write(cache)

    print(f"✅ 已同步: {CACHE_PATH}")
    print(f"   {len(souls)} 魂 | {len(records)} 条召唤记录 | {len(cache):,} chars")

def main():
    if "--check" in sys.argv:
        stale, reason = check_staleness()
        if stale:
            print(f"STALE: {reason}")
            sys.exit(1)
        else:
            print(f"OK: {reason}")
            sys.exit(0)
    elif "--diff" in sys.argv:
        show_diff()
    elif "--sync" in sys.argv:
        do_sync()
    else:
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
