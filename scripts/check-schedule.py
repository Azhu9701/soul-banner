#!/usr/bin/env python3
"""检查 .tasks/schedule.yaml 中的任务排期，报告过期/即将到期的任务。

设计：无状态机、无依赖图、无owner字段——只做一件事：到期提醒。
用法：python3 scripts/check-schedule.py [--json]
"""

import sys
from datetime import date, timedelta
from pathlib import Path

import yaml

SCHEDULE_PATH = Path(__file__).resolve().parent.parent / "committee" / ".tasks" / "schedule.yaml"


def load_schedule(path: Path) -> dict:
    if not path.exists():
        return {"tasks": [], "reviews": []}
    with open(path) as f:
        return yaml.safe_load(f) or {"tasks": [], "reviews": []}


def check_task(task: dict, today: date) -> dict | None:
    """检查单个任务，如有问题返回警告，否则返回 None。"""
    due_val = task.get("due")
    if not due_val:
        return None

    if isinstance(due_val, date):
        due_date = due_val
    else:
        due_date = date.fromisoformat(str(due_val))
    days_left = (due_date - today).days
    status = task.get("status", "pending")

    if status == "completed":
        return None

    if days_left < 0:
        return {
            "id": task["id"],
            "subject": task["subject"],
            "level": "过期",
            "days": abs(days_left),
            "due": str(due_date),
        }
    elif days_left <= 7:
        return {
            "id": task["id"],
            "subject": task["subject"],
            "level": "即将到期",
            "days": days_left,
            "due": str(due_date),
        }
    return None


def check_review(review: dict, today: date) -> dict | None:
    """检查审查排期是否有到期的。"""
    if review.get("status") == "completed":
        return None

    date_val = review.get("date")
    window_str = review.get("window")

    if date_val:
        if isinstance(date_val, date):
            review_date = date_val
        else:
            review_date = date.fromisoformat(str(date_val))
        days_left = (review_date - today).days
        if days_left < 0:
            return {
                "id": review["id"],
                "subject": f"{review['type']}: {review.get('who', review.get('date', ''))}",
                "level": "过期",
                "days": abs(days_left),
                "due": str(date_val),
            }
        elif days_left <= 14:
            return {
                "id": review["id"],
                "subject": f"{review['type']}: {review.get('who', review.get('date', ''))}",
                "level": "即将到期",
                "days": days_left,
                "due": str(date_val),
            }

    if window_str:
        start_str, end_str = window_str.split("..")
        end_date = date.fromisoformat(end_str)
        days_left = (end_date - today).days
        if days_left < 0:
            return {
                "id": review["id"],
                "subject": f"{review['type']}: {review.get('who', '')} (窗口: {window_str})",
                "level": "过期",
                "days": abs(days_left),
                "due": end_str,
            }
        elif days_left <= 14:
            return {
                "id": review["id"],
                "subject": f"{review['type']}: {review.get('who', '')} (窗口: {window_str})",
                "level": "即将到期",
                "days": days_left,
                "due": end_str,
            }
    return None


def main():
    today = date.today()
    schedule = load_schedule(SCHEDULE_PATH)
    tasks = schedule.get("tasks", [])
    reviews = schedule.get("reviews", [])

    warnings = []
    for task in tasks:
        w = check_task(task, today)
        if w:
            warnings.append(w)

    for review in reviews:
        w = check_review(review, today)
        if w:
            warnings.append(w)

    json_mode = "--json" in sys.argv

    if json_mode:
        import json
        print(json.dumps({"date": today.isoformat(), "warnings": warnings}, ensure_ascii=False, indent=2))
        return

    print(f"=== 任务排期检查 — {today} ===\n")

    if not tasks and not reviews:
        print("无任务。")
        return

    # 任务状态
    pending = [t for t in tasks if t.get("status") != "completed"]
    completed = [t for t in tasks if t.get("status") == "completed"]
    print(f"任务: {len(pending)} 待办 / {len(completed)} 已完成")

    for t in tasks:
        marker = {"pending": "[ ]", "completed": "[x]"}.get(t.get("status", "pending"), "[?]")
        due = f" 到期: {t['due']}" if t.get("due") else ""
        print(f"  {marker} {t['id']}: {t['subject']}{due}")

    # 审查排期
    print(f"\n审查排期: {len(reviews)} 项")
    for r in reviews:
        marker = {"pending": "[ ]", "completed": "[x]"}.get(r.get("status", "pending"), "[?]")
        detail = r.get("date") or r.get("window", "")
        print(f"  {marker} {r['id']}: {r['type']} ({detail})")

    # 警告
    if warnings:
        print(f"\n⚠️  警告 ({len(warnings)} 项):")
        overdue = [w for w in warnings if w["level"] == "过期"]
        upcoming = [w for w in warnings if w["level"] == "即将到期"]

        if overdue:
            print(f"\n  🔴 过期 ({len(overdue)} 项):")
            for w in overdue:
                print(f"     {w['id']}: {w['subject'][:60]} (过期 {w['days']} 天, 到期日: {w['due']})")

        if upcoming:
            print(f"\n  🟡 即将到期 ({len(upcoming)} 项):")
            for w in upcoming:
                print(f"     {w['id']}: {w['subject'][:60]} (还剩 {w['days']} 天, 到期日: {w['due']})")
    else:
        print("\n✅ 无过期或即将到期任务。")

    # 上次更新检查
    updated = schedule.get("updated", "未知")
    try:
        updated_date = date.fromisoformat(updated)
        days_since = (today - updated_date).days
        if days_since > 14:
            print(f"\n⚠️  schedule.yaml 上次更新于 {updated} ({days_since} 天前)，可能需要同步 state.json。")
    except (ValueError, TypeError):
        pass


if __name__ == "__main__":
    main()
