#!/usr/bin/env python3
"""万魂幡状态摘要 — 聚合所有数据源输出统一快照

数据源：
  registry.yaml       — 魂魄列表、品级、gold_review
  call-records.yaml   — 近期附体记录
  committee/state.json — 委员会、预算、C指标、待办
  reviews/            — 近期审查报告文件
  committee/meetings/ — 近期会议纪要

用法：
  python3 scripts/state-summary.py              # 输出 markdown（默认7天窗口）
  python3 scripts/state-summary.py --days 3     # 最近3天
  python3 scripts/state-summary.py --json       # JSON 输出
"""

import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_PATH = os.path.join(SKILL_DIR, "registry.yaml")
CALL_RECORDS_PATH = os.path.join(SKILL_DIR, "call-records.yaml")
STATE_PATH = os.path.join(SKILL_DIR, "committee", "state.json")
REVIEWS_DIR = os.path.join(SKILL_DIR, "reviews")
MEETINGS_DIR = os.path.join(SKILL_DIR, "committee", "meetings")


def load_yaml(path):
    import yaml
    with open(path) as f:
        return yaml.safe_load(f)


def load_json(path):
    with open(path) as f:
        return json.load(f)


def get_recent_files(directory, pattern, days):
    """返回最近 N 天内的文件列表（名称+修改时间）"""
    if not os.path.isdir(directory):
        return []
    cutoff = datetime.now() - timedelta(days=days)
    results = []
    for f in sorted(Path(directory).glob(pattern)):
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        if mtime >= cutoff:
            results.append((f.name, mtime.strftime("%m-%d %H:%M")))
    return results


def grade_order(grade):
    order = {"金": 0, "银": 1, "紫": 2, "蓝": 3, "绿": 4, "白": 5}
    return order.get(grade, 99)


def grade_emoji(grade):
    return {"金": "🟡", "银": "🥈", "紫": "🟣", "蓝": "🔵", "绿": "🟢", "白": "⚪"}.get(grade, "❓")


def main():
    days = 7
    as_json = False
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--days" and i + 1 < len(args):
            days = int(args[i + 1])
            i += 2
        elif args[i] == "--json":
            as_json = True
            i += 1
        else:
            i += 1

    # ── 加载数据 ──
    registry = load_yaml(REGISTRY_PATH)
    souls = registry.get("魂魄", [])
    banner_master = registry.get("万魂幡主", "未知")

    # 按品级排序
    souls_sorted = sorted(souls, key=lambda s: (grade_order(s.get("grade", "白")), s.get("name", "")))

    # 品级分布
    grade_counts = Counter(s.get("grade", "白") for s in souls)

    # 审查委员会状态
    committee = {}
    if os.path.exists(STATE_PATH):
        committee = load_json(STATE_PATH)

    # 附体记录（合并 records + 召唤记录 两个列表）
    call_records_raw = []
    if os.path.exists(CALL_RECORDS_PATH):
        cr = load_yaml(CALL_RECORDS_PATH)
        call_records_raw = cr.get("records", []) + cr.get("召唤记录", [])

    # 过滤近期记录
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    recent_calls = [r for r in call_records_raw if r.get("date", "") >= cutoff_date]

    # 近期审查文件
    recent_reviews = get_recent_files(REVIEWS_DIR, "*.md", days)
    # 也检查合议/互审子目录
    for sub in ["合议", "互审"]:
        subdir = os.path.join(REVIEWS_DIR, sub)
        for fname, mtime in get_recent_files(subdir, "*.md", days):
            recent_reviews.append((f"{sub}/{fname}", mtime))

    # 近期会议
    recent_meetings = get_recent_files(MEETINGS_DIR, "*会议纪要*.md", days)
    recent_agendas = get_recent_files(MEETINGS_DIR, "*agenda*.md", days)

    # ── JSON 输出 ──
    if as_json:
        output = {
            "banner_master": banner_master,
            "total_souls": len(souls),
            "grade_distribution": dict(grade_counts),
            "souls": [{
                "name": s["name"],
                "grade": s.get("grade"),
                "title": s.get("title", ""),
                "refined_at": s.get("refined_at", ""),
            } for s in souls_sorted],
            "committee": {
                "members": committee.get("成员", []),
                "next_meeting": committee.get("schedule", {}).get("常规会议", {}).get("下次会议", ""),
                "last_meeting": committee.get("schedule", {}).get("常规会议", {}).get("上次会议", ""),
                "c_indicators": committee.get("费曼C指标", {}),
                "budget": committee.get("budget", {}),
            },
            "recent_calls": recent_calls,
            "recent_reviews": [{"file": f, "mtime": t} for f, t in recent_reviews],
            "recent_meetings": [{"file": f, "mtime": t} for f, t in recent_meetings],
            "pending_tasks": committee.get("pending_tasks", []),
            "window_days": days,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    # ── Markdown 输出 ──
    lines = []
    lines.append(f"## 万魂幡 状态快照（最近 {days} 天）\n")
    lines.append(f"**幡主**：{banner_master} | **魂魄总数**：{len(souls)} | **窗口**：{cutoff_date} ~ {datetime.now().strftime('%Y-%m-%d')}\n")

    # ── 品级分布 ──
    lines.append("### 品级分布\n")
    grade_order_list = ["金", "银", "紫", "蓝", "绿", "白"]
    parts = []
    for g in grade_order_list:
        c = grade_counts.get(g, 0)
        if c > 0:
            emoji = grade_emoji(g)
            names = [s["name"] for s in souls_sorted if s.get("grade") == g]
            parts.append(f"**{emoji} {g}魂 {c}**：{'、'.join(names)}")
    lines.append(" | ".join(parts) + "\n")

    # ── 审查委员会 ──
    if committee:
        lines.append("### 审查委员会\n")
        members = committee.get("成员", [])
        if members:
            lines.append(f"- **成员**（16魂选举）：{'、'.join(members)}")
        schedule = committee.get("schedule", {}).get("常规会议", {})
        if schedule:
            lines.append(f"- **上次会议**：{schedule.get('上次会议', 'N/A')}（{'实质召开' if schedule.get('上次会议实质召开') else '未实质召开'}）")
            lines.append(f"- **下次会议**：{schedule.get('下次会议', 'N/A')}")
        # C 指标
        c_indicators = committee.get("费曼C指标", {})
        if c_indicators:
            c_parts = []
            for key, val in c_indicators.items():
                name = val.get("定义", key)
                status = val.get("当前状态", "未知")
                c_parts.append(f"{key}({status})")
            lines.append(f"- **C指标**：{' | '.join(c_parts)}")
        # 预算
        budget = committee.get("budget", {})
        if budget:
            lines.append(f"- **预算**：月度 {budget.get('月度预算帽', 'N/A')} | 余额 {budget.get('当前余额_CNY', 'N/A')} 元 ({budget.get('状态', 'N/A')})")
        lines.append("")

    # ── 近期动态 ──
    lines.append("### 近期动态\n")

    # 近期附体
    if recent_calls:
        lines.append(f"**附体记录**（{len(recent_calls)} 条）：\n")
        for r in recent_calls:
            date = r.get("date", "")
            mode = r.get("mode", "")
            eff = r.get("effectiveness", "")
            soul = r.get("soul", "")
            task = r.get("task", "")
            role = r.get("role", "")
            role_str = f" [{role}]" if role else ""
            lines.append(f"- `{date}` **{mode}** {soul}{role_str} — {task}（{eff}）")
        lines.append("")

    # 近期审查/报告
    if recent_reviews:
        lines.append(f"**审查/报告产出**（{len(recent_reviews)} 份）：\n")
        for fname, mtime in sorted(recent_reviews, key=lambda x: x[1], reverse=True):
            lines.append(f"- `{mtime}` {fname}")
        lines.append("")

    # 近期会议
    if recent_meetings:
        lines.append(f"**会议**（{len(recent_meetings)} 次）：\n")
        for fname, mtime in recent_meetings:
            lines.append(f"- `{mtime}` {fname}")
        lines.append("")

    if not recent_calls and not recent_reviews and not recent_meetings:
        lines.append(f"最近 {days} 天无新动态。\n")

    # ── 待办事项 ──
    pending = committee.get("pending_tasks", [])
    if pending:
        lines.append("### 待办事项\n")
        status_order = {"已完成": 0, "部分推进": 1, "未开始": 2}
        for t in sorted(pending, key=lambda x: status_order.get(x.get("status", ""), 99)):
            tid = t.get("id", "")
            name = t.get("name", "")
            status = t.get("status", "")
            lines.append(f"- **{tid}** {name} — *{status}*")
        lines.append("")

    # ── 零召唤检测 ──
    all_names = {s["name"] for s in souls}
    called_names = set()
    for r in call_records_raw:
        soul_val = r.get("soul")
        souls_val = r.get("souls")
        if isinstance(soul_val, str) and soul_val:
            called_names.add(soul_val)
        elif isinstance(souls_val, list):
            for s in souls_val:
                if isinstance(s, dict) and s.get("name"):
                    called_names.add(s["name"])
                elif isinstance(s, str) and s:
                    called_names.add(s)
    zero_call = all_names - called_names
    if zero_call:
        lines.append("### 零召唤预警\n")
        lines.append(f"以下 {len(zero_call)} 魂从未被召唤：{'、'.join(sorted(zero_call))}\n")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
