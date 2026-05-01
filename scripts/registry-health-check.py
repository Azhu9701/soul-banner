#!/usr/bin/env python3
"""万魂幡 Registry 健康检查

检查项：
  1. 是否有魂从未被召唤（trigger 可能太窄）
  2. 是否有魂召唤 > 5 次但无 effectiveness: 有效
  3. 是否有魂炼化超过 3 个月未更新 refined_at
  4. 顶层召唤记录中是否有孤魂引用（魂名不在魂魄列表中）

用法：
  python3 scripts/registry-health-check.py          # 输出到 stdout
  python3 scripts/registry-health-check.py --json   # JSON 输出
  python3 scripts/registry-health-check.py --last-run  # 检查上次运行时间（给 CLAUDE.md 用）

输出写入 logs/registry-health-check.log，同时打印到 stdout。
"""

import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_PATH = os.path.join(SKILL_DIR, "registry.yaml")
CALL_RECORDS_PATH = os.path.join(SKILL_DIR, "call-records.yaml")
LOG_FILE = os.path.join(SKILL_DIR, "logs", "registry-health-check.log")
LAST_RUN_FILE = os.path.join(SKILL_DIR, "logs", "health-check-last-run.txt")

STALE_THRESHOLD_DAYS = 90
HIGH_SUMMON_THRESHOLD = 5


def load_registry():
    """加载 registry.yaml 和 call-records.yaml，返回 (souls, global_records)"""
    try:
        import yaml
    except ImportError:
        print("ERROR: PyYAML not available")
        sys.exit(1)

    with open(REGISTRY_PATH) as f:
        data = yaml.safe_load(f.read())
    souls = data.get("魂魄", [])

    # 召唤记录从 call-records.yaml 按需加载
    records = []
    if os.path.exists(CALL_RECORDS_PATH):
        with open(CALL_RECORDS_PATH) as f:
            cr = yaml.safe_load(f.read())
        records = cr.get("召唤记录", []) if cr else []

    return souls, records


def get_summon_counts(global_records: list[dict]) -> Counter:
    """从顶层召唤记录统计每个魂的召唤次数"""
    return Counter(r["soul"] for r in global_records if isinstance(r, dict) and "soul" in r)


def get_effectiveness_summary(global_records: list[dict]) -> dict:
    """按魂统计 effectiveness 分布"""
    summary = {}
    for r in global_records:
        if not isinstance(r, dict):
            continue
        name = r.get("soul", "?")
        eff = r.get("effectiveness", "N/A")
        if name not in summary:
            summary[name] = {"total": 0, "有效": 0, "部分有效": 0, "无效": 0, "N/A": 0}
        summary[name]["total"] += 1
        summary[name][eff] = summary[name].get(eff, 0) + 1
    return summary


def check_never_summoned(souls: list[dict], counts: Counter) -> list[dict]:
    """检查是否有魂从未被召唤（trigger 可能太窄）"""
    issues = []
    for s in souls:
        name = s.get("name", "?")
        if name not in counts or counts[name] == 0:
            trigger = s.get("trigger_keywords_summary", "N/A")
            issues.append(
                {
                    "soul": name,
                    "type": "never_summoned",
                    "summoned_count": 0,
                    "trigger_summary": trigger[:100] if trigger else "N/A",
                    "detail": "从未被召唤，trigger 可能太窄",
                }
            )
    return issues


def check_high_summon_no_effect(souls: list[dict], counts: Counter, eff_summary: dict, threshold: int = HIGH_SUMMON_THRESHOLD) -> list[dict]:
    """检查召唤次数 > threshold 但无 effectiveness: 有效"""
    issues = []
    soul_names = {s.get("name", "?") for s in souls}
    for name, count in counts.items():
        if count <= threshold:
            continue
        if name not in soul_names:
            continue
        eff = eff_summary.get(name, {})
        if eff.get("有效", 0) == 0:
            issues.append(
                {
                    "soul": name,
                    "type": "high_summon_no_effect",
                    "summoned_count": count,
                    "effectiveness_values": {k: v for k, v in eff.items() if k != "total"},
                    "detail": f"召唤 {count} 次，但没有任何 effectiveness=有效 的记录",
                }
            )
    return issues


def check_stale_refinement(souls: list[dict], threshold_days: int = STALE_THRESHOLD_DAYS) -> list[dict]:
    """检查是否有魂炼化超过 threshold_days 天未更新 refined_at"""
    issues = []
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=threshold_days)

    for s in souls:
        name = s.get("name", "?")
        refined_at = s.get("refined_at", "")
        if not refined_at:
            issues.append({"soul": name, "type": "no_refined_at", "detail": "缺少 refined_at 字段"})
            continue

        try:
            if hasattr(refined_at, 'strftime'):
                dt = datetime.combine(refined_at, datetime.min.time())
                dt = dt.replace(tzinfo=timezone.utc)
            elif isinstance(refined_at, str):
                parsed = None
                for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"]:
                    try:
                        parsed = datetime.strptime(refined_at.strip()[:19], fmt)
                        break
                    except ValueError:
                        continue
                if parsed is None:
                    issues.append({"soul": name, "type": "unparseable_refined_at", "detail": f"无法解析 refined_at: {refined_at}"})
                    continue
                dt = parsed.replace(tzinfo=timezone.utc)
            else:
                continue

            if dt < cutoff:
                days_ago = (now - dt).days
                issues.append(
                    {
                        "soul": name,
                        "type": "stale_refinement",
                        "refined_at": str(refined_at),
                        "days_since": days_ago,
                        "detail": f"上次炼化距今 {days_ago} 天，超过阈值 {threshold_days} 天",
                    }
                )
        except Exception:
            pass

    return issues


def check_orphan_records(global_records: list[dict], souls: list[dict]) -> list[dict]:
    """检查顶层召唤记录中是否有孤魂引用（魂名不在魂魄列表中）"""
    issues = []
    soul_names = {s.get("name", "?") for s in souls}
    for r in global_records:
        if not isinstance(r, dict):
            continue
        name = r.get("soul", "?")
        if name not in soul_names:
            issues.append(
                {
                    "soul": name,
                    "type": "orphan_record",
                    "task": r.get("task", "?"),
                    "detail": f"召唤记录引用不存在的魂 '{name}'",
                }
            )
    return issues


def save_last_run():
    """保存本次运行时间戳"""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(LAST_RUN_FILE, "w") as f:
        f.write(timestamp)
    return timestamp


def check_last_run_age() -> tuple[str, float]:
    """检查上次运行距今多久（小时）"""
    try:
        with open(LAST_RUN_FILE) as f:
            last = f.read().strip()
        last_dt = datetime.strptime(last, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        hours = (now - last_dt).total_seconds() / 3600
        return last, hours
    except (FileNotFoundError, ValueError):
        return "从未运行", 999.0


def write_log(all_issues: list[dict], timestamp: str):
    """写入日志文件"""
    with open(LOG_FILE, "a") as f:
        f.write(f"\n{'=' * 60}\n")
        f.write(f"健康检查 — {timestamp}\n")
        f.write(f"{'=' * 60}\n")
        if not all_issues:
            f.write("全部检查通过，无异常。\n")
        else:
            f.write(f"共发现 {len(all_issues)} 个问题：\n\n")
            for i, issue in enumerate(all_issues, 1):
                soul = issue.get("soul", "?")
                itype = issue.get("type", "?")
                detail = issue.get("detail", "")
                f.write(f"  [{i}] {soul} — {itype}\n")
                f.write(f"      {detail}\n")


def main():
    output_json = "--json" in sys.argv
    check_last = "--last-run" in sys.argv

    if check_last:
        last, hours = check_last_run_age()
        if last == "从未运行":
            print("NEVER_RUN")
        elif hours > 24:
            print(f"STALE: {last} ({hours:.1f}h ago)")
        else:
            print(f"OK: {last} ({hours:.1f}h ago)")
        sys.exit(0)

    souls, global_records = load_registry()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    counts = get_summon_counts(global_records)
    eff_summary = get_effectiveness_summary(global_records)

    all_issues = []
    all_issues.extend(check_never_summoned(souls, counts))
    all_issues.extend(check_high_summon_no_effect(souls, counts, eff_summary))
    all_issues.extend(check_stale_refinement(souls))
    all_issues.extend(check_orphan_records(global_records, souls))

    write_log(all_issues, timestamp)
    save_last_run()

    # Computed grade statistics
    grade_symbol_map = {'白': '⚪', '绿': '🟢', '蓝': '🔵', '紫': '🟣', '银': '🥈', '金': '🟡'}
    grade_order = ['金', '银', '紫', '蓝', '绿', '白']
    grade_dist = {}
    for s in souls:
        g = s.get('grade', '?')
        grade_dist[g] = grade_dist.get(g, 0) + 1

    if output_json:
        print(json.dumps({
            "timestamp": timestamp,
            "issues": all_issues,
            "total": len(all_issues),
            "summon_counts": dict(counts),
            "grade_distribution": grade_dist,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"万魂幡 Registry 健康检查 — {timestamp}")
        print(f"共 {len(souls)} 魂 | 顶层召唤记录 {len(global_records)} 条\n")
        print("品级分布（自动统计）：")
        for g in grade_order:
            if g in grade_dist:
                symbol = grade_symbol_map.get(g, '')
                print(f"  {symbol} {g}魂: {grade_dist[g]}")
        print()
        print("召唤统计（来自顶层 召唤记录）：")
        for name, count in sorted(counts.items(), key=lambda x: -x[1]):
            eff = eff_summary.get(name, {})
            print(f"  {name}: {count} 次 (有效 {eff.get('有效', 0)} | 部分有效 {eff.get('部分有效', 0)} | 无效 {eff.get('无效', 0)})")
        for s in souls:
            name = s.get("name", "?")
            if name not in counts:
                print(f"  {name}: 0 次")

        if all_issues:
            print(f"\n发现 {len(all_issues)} 个问题：\n")
            for i, issue in enumerate(all_issues, 1):
                soul = issue.get("soul", "?")
                itype = issue.get("type", "?")
                detail = issue.get("detail", "")
                print(f"  [{i}] {soul} — {itype}")
                print(f"      {detail}")
        else:
            print("\n全部检查通过，无异常。")

    sys.exit(0)


if __name__ == "__main__":
    main()
