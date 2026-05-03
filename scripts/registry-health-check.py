#!/usr/bin/env python3
"""万民幡 Registry 健康检查

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

def _parse_refined_date(refined_at):
    """解析 refined_at 字段，返回 timezone-aware datetime 或 None"""
    if not refined_at:
        return None
    try:
        if hasattr(refined_at, 'strftime'):
            dt = datetime.combine(refined_at, datetime.min.time())
            return dt.replace(tzinfo=timezone.utc)
        if isinstance(refined_at, str):
            for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"]:
                try:
                    return datetime.strptime(refined_at.strip()[:19], fmt).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
    except (ValueError, TypeError):
        pass
    return None
HIGH_SUMMON_THRESHOLD = 5
DECAY_CONSECUTIVE_NO_EFFECT = 5   # 连续N次无「有效」→ 召唤限制
DECAY_ZERO_SUMMON_DAYS = 90       # 连续N天零召唤 → 散魂警告


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
    """检查是否有魂从未被召唤（trigger 可能太窄），并生成推荐信息"""
    issues = []
    for s in souls:
        name = s.get("name", "?")
        if name not in counts or counts[name] == 0:
            trigger = s.get("trigger_keywords_summary", "N/A")
            scenarios = s.get("trigger_scenarios_summary", "N/A")
            func_doms = s.get("function_domains", [])
            domains = s.get("domain", [])

            # 生成推荐信息
            recommendation = _build_zero_summon_recommendation(
                name, func_doms, domains, scenarios, souls
            )

            issues.append(
                {
                    "soul": name,
                    "type": "never_summoned",
                    "summoned_count": 0,
                    "function_domains": func_doms,
                    "domains": domains,
                    "trigger_summary": trigger[:100] if trigger else "N/A",
                    "scenarios": scenarios if scenarios else "N/A",
                    "recommendation": recommendation,
                    "detail": "从未被召唤，trigger 可能太窄",
                }
            )
    return issues


def _build_zero_summon_recommendation(name: str, func_doms: list[str], domains: list[str], scenarios: str, all_souls: list[dict]) -> dict:
    """为零召唤魂生成推荐：适用场景、兼容魂配对、推荐任务类型"""
    paired_souls = []
    for other in all_souls:
        other_name = other.get("name", "?")
        if other_name == name:
            continue
        other_domains = set(other.get("domain", []))
        my_domains = set(domains)
        overlap = my_domains & other_domains
        complement = other_domains - my_domains
        if overlap and complement:
            paired_souls.append({
                "soul": other_name,
                "overlap_domains": sorted(overlap),
                "complement_domains": sorted(complement)[:3],
                "rationale": f"{other_name}的{'、'.join(sorted(complement)[:3])}补充本魂视角"
            })

    paired_souls.sort(key=lambda x: len(x["complement_domains"]), reverse=True)
    top_pairs = paired_souls[:3]

    dom_str = '+'.join(func_doms) if func_doms else '?'
    task_types = [
        f"在涉及{'/'.join(domains[:2]) if domains else '其领域'}的任务中使用{name}（{dom_str}）",
        f"合议中让{name}和互补魂配对（{'、'.join([p['soul'] for p in top_pairs[:2]]) if top_pairs else '无'}）"
    ]

    return {
        "scenarios": scenarios if scenarios else "N/A",
        "compatible_pairs": [
            {
                "soul": p["soul"],
                "rationale": p["rationale"]
            } for p in top_pairs
        ],
        "suggested_task_types": task_types,
        "zero_summon_risk": (
            f"{dom_str}功能域魂零召唤——该领域视角未激活"
        )
    }


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

        dt = _parse_refined_date(refined_at)
        if dt is None:
            issues.append({"soul": name, "type": "unparseable_refined_at", "detail": f"无法解析 refined_at: {refined_at}"})
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


def check_decay(souls: list[dict], global_records: list[dict], counts: Counter) -> list[dict]:
    """定期衰减审查：
    - 连续 N 次附体无「有效」评级 → 触发召唤限制
    - 连续 N 天零召唤 → 触发散魂警告
    """
    issues = []
    now = datetime.now(timezone.utc)

    # 按魂分析最近附体记录
    soul_records = {}
    for r in global_records:
        if not isinstance(r, dict):
            continue
        name = r.get("soul", "?")
        if name not in soul_records:
            soul_records[name] = []
        soul_records[name].append(r)

    for s in souls:
        name = s.get("name", "?")
        func_doms = s.get("function_domains", [])
        info_suf = s.get("info_sufficiency", "?")
        records = soul_records.get(name, [])

        # 1) 连续低效检测
        if records:
            sorted_records = sorted(
                records,
                key=lambda r: r.get("date", "0000-00-00"),
                reverse=True,
            )
            consecutive_no_effect = 0
            for r in sorted_records:
                if r.get("effectiveness") in ("有效",):
                    break
                consecutive_no_effect += 1

            if consecutive_no_effect >= DECAY_CONSECUTIVE_NO_EFFECT:
                issues.append({
                    "soul": name,
                    "type": "decay_low_effectiveness",
                    "function_domains": func_doms,
                    "consecutive_no_effect": consecutive_no_effect,
                    "detail": (
                        f"连续 {consecutive_no_effect} 次附体无「有效」评级 → "
                        f"触发召唤限制：暂停附体资格，强制重新炼化+审查"
                    ),
                    "recommended_action": "暂停附体 → 重新炼化 → 重新审查 → 适用边界复审",
                })

        # 2) 长期零召唤检测
        count = counts.get(name, 0)
        if count == 0:
            dt = _parse_refined_date(s.get("refined_at", ""))
            if dt:
                days_since_refine = (now - dt).days
                if days_since_refine >= DECAY_ZERO_SUMMON_DAYS:
                    issues.append({
                        "soul": name,
                        "type": "decay_zero_summon",
                        "function_domains": func_doms,
                        "info_sufficiency": info_suf,
                        "days_since_refined": days_since_refine,
                        "detail": (
                            f"炼化 {days_since_refine} 天，零召唤 → "
                            f"触发散魂警告：建议触发条件复审，仍无改善则强制散魂"
                        ),
                        "recommended_action": (
                            "1) 调整 trigger 条件扩大匹配 "
                            "2) 手动试用 1-2 次 "
                            "3) 30天后仍零召唤 → 强制散魂（保留 raw 素材）"
                        ),
                    })

        # 3) 方法论前提被历史证伪检测（标记——需人工判断）
        # 当前标记逻辑：信息充分度=充分且零召唤且炼化超过 180 天
        if info_suf == "充分" and count == 0:
            dt = _parse_refined_date(s.get("refined_at", ""))
            if dt:
                days_since_refine = (now - dt).days
                if days_since_refine >= 180:
                    issues.append({
                        "soul": name,
                        "type": "decay_premise_review",
                        "function_domains": func_doms,
                        "info_sufficiency": info_suf,
                        "days_since_refined": days_since_refine,
                        "detail": (
                            f"信息充分度=充分的魂炼化 {days_since_refine} 天，零召唤 → "
                            f"审查委员会需裁定：方法论前提是否已被历史证伪？"
                        ),
                        "recommended_action": "审查委员会复审 → 维持/调整/散魂",
                    })

    return issues


# === 三维遗忘审查 ===

def check_substitutability(souls: list, counts: Counter, eff_summary: dict) -> list[dict]:
    """维度二：可替代性——是否有另一魂覆盖相同领域且表现更精确

    判定规则：若魂B在重叠领域被召唤≥5次且有效占比≥80%，而魂A在重叠领域零召唤或低效，
    则魂A在重叠领域被魂B替代。
    """
    issues = []
    # 取每个魂的 domain 集合
    soul_domains = {}
    for s in souls:
        name = s.get("name", "?")
        soul_domains[name] = set(s.get("domain", []))

    for i, s_a in enumerate(souls):
        name_a = s_a.get("name", "?")
        domains_a = soul_domains.get(name_a, set())
        if not domains_a:
            continue
        count_a = counts.get(name_a, 0)
        eff_a = eff_summary.get(name_a, {})

        for j, s_b in enumerate(souls):
            if i >= j:
                continue
            name_b = s_b.get("name", "?")
            domains_b = soul_domains.get(name_b, set())
            if not domains_b:
                continue
            overlap = domains_a & domains_b
            if not overlap:
                continue

            count_b = counts.get(name_b, 0)
            eff_b = eff_summary.get(name_b, {})

            # 魂B在重叠领域表现显著优于魂A
            b_total = eff_b.get("total", 0)
            b_effective = eff_b.get("有效", 0)
            a_total = eff_a.get("total", 0)
            a_effective = eff_a.get("有效", 0)

            b_strong = b_total >= 5 and (b_effective / max(b_total, 1)) >= 0.8
            a_weak = a_total == 0 or (a_effective / max(a_total, 1)) < 0.5

            if b_strong and a_weak:
                issues.append({
                    "soul": name_a,
                    "type": "decay_substitutability",
                    "function_domains": s_a.get("function_domains", []),
                    "overlapping_domains": sorted(overlap),
                    "substituted_by": name_b,
                    "substitute_stats": f"{name_b}: {b_total}次召唤, 有效{b_effective}",
                    "soul_stats": f"{name_a}: {a_total}次召唤, 有效{a_effective}",
                    "detail": (
                        f"{name_b}在重叠领域{'、'.join(sorted(overlap))}上表现显著优于{name_a}"
                    ),
                    "recommended_action": f"审查委员会评估：{name_a}在{'、'.join(sorted(overlap))}领域是否需要保留？",
                })

    return issues


def check_premise_validity(souls: list, counts: Counter) -> list[dict]:
    """维度三：方法论前提——核心前提是否已被历史证伪或消失

    仅标记需人工审查的候选。标准：
    - 封闭档案魂（已去世）+ 方法论前提可能因历史变迁失效
    - 开放实践魂（在世）+ 自身后续实践已部分证伪早期主张
    """
    issues = []
    now = datetime.now(timezone.utc)

    # 已知的方法论前提脆弱魂对（需定期复审）
    known_fragile_premises = {
        "伊本赫勒敦": {
            "premise": "循环论前提——生产力基本不变、社会凝聚力周期性涨落",
            "risk": "工业革命后生产力可持续增长，制度创新可阻断循环。方向判断（等下一拨游牧民族）在现代条件下不成立",
            "action": "维持但标记方向判断能力降格。不触发散魂（诊断框架仍有价值）"
        },
        "法农": {
            "premise": "暴力'净化'论——把暴力从工具提升到存在论-心理学圣化层面",
            "risk": "列宁审查已指出：暴力净化论已部分被历史证伪。需区分'暴力作为工具'（毛的枪杆子）vs '暴力作为净化'（法的存在论）",
            "action": "维持但强制搭配物质分析魂魄。单独使用的条件需更严格"
        },
    }

    for s in souls:
        name = s.get("name", "?")
        if name in known_fragile_premises:
            kfp = known_fragile_premises[name]
            count = counts.get(name, 0)
            issues.append({
                "soul": name,
                "type": "decay_premise_fragile",
                "function_domains": s.get("function_domains", []),
                "info_sufficiency": s.get("info_sufficiency", "?"),
                "premise": kfp["premise"],
                "risk": kfp["risk"],
                "recommended_action": kfp["action"],
                "summon_count": count,
                "detail": f"方法论前提脆弱：{kfp['premise']}。风险：{kfp['risk']}",
            })

    return issues


def generate_forgetting_recommendations(souls: list, all_issues: list) -> list[dict]:
    """汇总三维遗忘分析，生成遗忘审查建议。

    仅建议，不自动散魂。建议包含：
    - 终末审查四问的草稿
    - 散魂后的替代方案
    """
    recs = []
    decay_types = {"decay_low_effectiveness", "decay_zero_summon", "decay_premise_review",
                   "decay_substitutability", "decay_premise_fragile"}

    for issue in all_issues:
        if issue.get("type") not in decay_types:
            continue

        name = issue.get("soul", "?")
        func_doms = issue.get("function_domains", [])

        rec = {
            "soul": name,
            "function_domains": func_doms,
            "decay_type": issue["type"],
            "detail": issue.get("detail", ""),
            "終末審查四問": [
                f"1. {name}没有被使用/低效的原因是：(a)幡主任务分布不覆盖其领域 (b)方法论前提已消失 (c)有更好的魂替代了它 (d)功能域标签本身是错的？",
                f"2. 如果{name}在今天才被收魂炼化，三维标签会不同吗？",
                f"3. {name}在幡期间是否产生过间接价值（审查对照角色/学习答辩对立面/匹配审查参照物）？",
                f"4. 散魂后，{name}覆盖的领域是否出现空白？如果是——谁来补？",
            ],
            "recommended_action": issue.get("recommended_action", "审查委员会评估"),
        }
        recs.append(rec)

    return recs


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
    all_issues.extend(check_decay(souls, global_records, counts))
    # 三维遗忘分析
    all_issues.extend(check_substitutability(souls, counts, eff_summary))
    all_issues.extend(check_premise_validity(souls, counts))
    forgetting_recs = generate_forgetting_recommendations(souls, all_issues)

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
            "forgetting_recommendations": forgetting_recs,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"万民幡 Registry 健康检查 — {timestamp}")
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

                # 零召唤魂的推荐信息
                if itype == "never_summoned" and "recommendation" in issue:
                    rec = issue["recommendation"]
                    grade = issue.get("grade", "?")
                    print(f"      品级: {grade}")
                    print(f"      风险: {rec.get('zero_summon_risk', 'N/A')}")
                    print(f"      适用场景: {rec.get('scenarios', 'N/A')[:120]}")
                    pairs = rec.get("compatible_pairs", [])
                    if pairs:
                        print(f"      推荐配对:")
                        for p in pairs:
                            print(f"        + {p['soul']}: {p['rationale']}")
                    tasks = rec.get("suggested_task_types", [])
                    if tasks:
                        print(f"      推荐任务:")
                        for t in tasks:
                            print(f"        → {t}")

                # 衰减审查的操作建议
                if "recommended_action" in issue:
                    print(f"      操作建议: {issue['recommended_action']}")
        else:
            # 遗忘审查建议
            if forgetting_recs:
                print(f"\n{'=' * 50}")
                print(f"三维遗忘审查建议（共 {len(forgetting_recs)} 条）")
                print(f"{'=' * 50}")
                for i, rec in enumerate(forgetting_recs, 1):
                    print(f"\n  [{i}] {rec['soul']} ({rec['grade']}魂) — {rec['decay_type']}")
                    print(f"      {rec['detail'][:120]}")
                    print(f"      终末审查四问:")
                    for q in rec["終末審查四問"]:
                        print(f"        {q}")
                    print(f"      建议: {rec['recommended_action']}")

            print("\n全部检查通过，无异常。")

    sys.exit(0)


if __name__ == "__main__":
    main()
