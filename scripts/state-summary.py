#!/usr/bin/env python3
"""万民幡状态摘要 — 聚合所有数据源输出统一快照

数据源：
  registry.yaml       — 魂魄列表、ismism编码、gold_review
  call-records.yaml   — 近期附体记录
  committee/state.json — 委员会、预算、C指标、待办
  reviews/            — 近期审查报告文件
  committee/meetings/ — 近期会议纪要

用法：
  python3 scripts/state-summary.py              # 输出 markdown（默认7天窗口）
  python3 scripts/state-summary.py --days 3     # 最近3天
  python3 scripts/state-summary.py --json       # JSON 输出
  python3 scripts/state-summary.py --compact    # 精简模式：附体/审查只显示计数+最近5条
"""

import json
import os
import subprocess
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from utils import load_yaml, run_script

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_PATH = os.path.join(SKILL_DIR, "registry.yaml")
REGISTRY_LITE_PATH = os.path.join(SKILL_DIR, "registry-lite.yaml")
CALL_RECORDS_PATH = os.path.join(SKILL_DIR, "call-records.yaml")
STATE_PATH = os.path.join(SKILL_DIR, "committee", "state.json")
HANDBOOK_PATH = os.path.join(SKILL_DIR, "committee", "handbook.md")
REVIEWS_DIR = os.path.join(SKILL_DIR, "reviews")
MEETINGS_DIR = os.path.join(SKILL_DIR, "committee", "meetings")
AGENTS_DIR = os.path.join(os.path.expanduser("~"), ".claude", "agents")
SOULS_DIR = os.path.join(SKILL_DIR, "souls")

# 非魂 agent（不应对应 soul YAML）
SYSTEM_AGENTS = {"辩证综合官", "列宁审查官", "minimal-tool-user"}

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

def sort_by_name(s):
    return s.get("name", "?").lower()

def fetch_deepseek_balance():
    """从 DeepSeek API 拉取实时账户余额。返回 dict 或 None（失败时）。"""
    import ssl

    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        return None

    def _do_request(context=None):
        req = urllib.request.Request(
            "https://api.deepseek.com/user/balance",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )
        with urllib.request.urlopen(req, timeout=10, context=context) as resp:
            return json.loads(resp.read().decode())

    for attempt, ctx in enumerate([
        None,  # 第一次：正常 SSL 验证
        _insecure_ssl_context(),  # 第二次：跳过证书验证（公司代理环境回退）
    ]):
        try:
            data = _do_request(ctx)
            if data.get("is_available") and data.get("balance_infos"):
                cny = [b for b in data["balance_infos"] if b.get("currency") == "CNY"]
                if cny:
                    total = float(cny[0].get("total_balance", 0))
                    return {
                        "当前余额_CNY": f"{total:.2f}",
                        "查询日期": datetime.now().strftime("%Y-%m-%d"),
                        "数据来源": "api.deepseek.com/user/balance (实时)",
                    }
        except Exception:
            continue
    return None

def _insecure_ssl_context():
    """创建跳过证书验证的 SSL context（公司代理环境回退）。"""
    import ssl

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def update_state_budget(balance_info):
    """将实时余额写回 committee/state.json。"""
    if not os.path.exists(STATE_PATH):
        return
    state = load_json(STATE_PATH)
    budget = state.get("budget", {})
    budget.update(balance_info)
    budget["月度预算帽"] = budget.get("月度预算帽", "500元")
    pct = float(balance_info["当前余额_CNY"]) / 500 * 100
    if pct > 30:
        budget["状态"] = f"余额充足（{pct:.1f}%）"
    elif pct > 15:
        budget["状态"] = f"余额偏低（{pct:.1f}%），注意消耗"
    else:
        budget["状态"] = f"余额告急（{pct:.1f}%），距月度重置仍需关注"
    state["budget"] = budget
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def sync_registry_lite():
    """如果 registry.yaml 比 registry-lite.yaml 新，自动重新生成。"""
    if not os.path.exists(REGISTRY_PATH):
        return None
    if os.path.exists(REGISTRY_LITE_PATH):
        reg_mtime = os.path.getmtime(REGISTRY_PATH)
        lite_mtime = os.path.getmtime(REGISTRY_LITE_PATH)
        if reg_mtime <= lite_mtime:
            return None
    ok, out = run_script("generate-registry-lite.py", "-o", REGISTRY_LITE_PATH)
    return (ok, "registry-lite.yaml 已自动重新生成" if ok else f"生成失败: {out}")

def sync_handbook():
    """如果 call-records.yaml 比 handbook.md 新，自动重新生成。"""
    if not os.path.exists(CALL_RECORDS_PATH):
        return None
    if os.path.exists(HANDBOOK_PATH):
        cr_mtime = os.path.getmtime(CALL_RECORDS_PATH)
        hb_mtime = os.path.getmtime(HANDBOOK_PATH)
        if cr_mtime <= hb_mtime:
            return None
    ok, out = run_script("generate-handbook.py", "-o", HANDBOOK_PATH, "--compact")
    return (ok, "handbook.md 已自动重新生成" if ok else f"生成失败: {out}")

def check_agent_consistency():
    """返回 agent 文件一致性报告：stale / orphan / missing。"""
    reports = []
    if not os.path.isdir(SOULS_DIR):
        return reports
    soul_names = {os.path.splitext(f.name)[0] for f in Path(SOULS_DIR).glob("*.yaml")}
    agent_names = set()
    if os.path.isdir(AGENTS_DIR):
        for f in Path(AGENTS_DIR).glob("*.md"):
            n = os.path.splitext(f.name)[0]
            if n not in SYSTEM_AGENTS:
                agent_names.add(n)

    # 孤儿 agent（有 agent 无 soul）
    orphans = agent_names - soul_names
    if orphans:
        reports.append(f"孤儿 agent（无对应 soul YAML）：{'、'.join(sorted(orphans))}")

    # 缺 agent（有 soul 无 agent）
    missing = soul_names - agent_names
    if missing:
        reports.append(f"缺少 agent 文件（soul YAML 存在但 agent 未生成）：{'、'.join(sorted(missing))}")

    # stale agent（soul 比 agent 新）
    stale = []
    for n in soul_names & agent_names:
        soul_mtime = os.path.getmtime(os.path.join(SOULS_DIR, f"{n}.yaml"))
        agent_mtime = os.path.getmtime(os.path.join(AGENTS_DIR, f"{n}.md"))
        if soul_mtime > agent_mtime:
            stale.append(n)
    if stale:
        reports.append(f"stale agent（soul YAML 有更新但 agent 未同步）：{'、'.join(sorted(stale))}")

    return reports

def auto_fix_cross_validate():
    """运行交叉校验，有错自动 --fix。"""
    ok, out = run_script("cross-validate.py")
    if ok:
        return None  # 无错误
    # 尝试自动修复
    fix_ok, fix_out = run_script("cross-validate.py", "--fix")
    # 修复后重新校验
    re_ok, re_out = run_script("cross-validate.py")
    if re_ok:
        return (True, "交叉校验发现错误，已自动修复")
    else:
        return (False, f"交叉校验自动修复失败，残留错误:\n{re_out}")

def run_auto_maintenance():
    """执行所有自动运维检查，返回操作摘要列表。"""
    actions = []

    # 1. 交叉校验 + 自动修复（放在前面，可能有实质性数据问题）
    r = auto_fix_cross_validate()
    if r:
        actions.append(r)

    # 2. registry-lite.yaml 陈旧检测
    r = sync_registry_lite()
    if r:
        actions.append(r)

    # 3. handbook.md 陈旧检测
    r = sync_handbook()
    if r:
        actions.append(r)

    # 4. agent 一致性检测（只报告，不自动 sync——agent 需要 Claude Code 重启生效）
    agent_reports = check_agent_consistency()
    for msg in agent_reports:
        actions.append((False, msg))

    return actions

def main():
    days = 7
    as_json = False
    no_auto = False
    compact = False
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--days" and i + 1 < len(args):
            days = int(args[i + 1])
            i += 2
        elif args[i] == "--json":
            as_json = True
            i += 1
        elif args[i] == "--no-auto":
            no_auto = True
            i += 1
        elif args[i] == "--compact":
            compact = True
            i += 1
        else:
            i += 1

    # ── 自动运维（可跳过）──
    maint_actions = [] if no_auto else run_auto_maintenance()

    # ── 加载数据 ──
    registry = load_yaml(REGISTRY_PATH)
    souls = registry.get("魂魄", [])
    banner_master = registry.get("万民幡主", "未知")

    souls_sorted = sorted(souls, key=sort_by_name)

    # ismism 四维分布

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
            "souls": [{
                "name": s["name"],
                "title": s.get("title", ""),
                "refined_at": s.get("refined_at", ""),
                "ismism_code": s.get("ismism_code", ""),
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
            "maintenance": [{"ok": ok, "message": msg} for ok, msg in maint_actions],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    # ── Markdown 输出 ──
    lines = []
    lines.append(f"## 万民幡 状态快照（最近 {days} 天）\n")
    lines.append(f"**幡主**：{banner_master} | **魂魄总数**：{len(souls)} | **窗口**：{cutoff_date} ~ {datetime.now().strftime('%Y-%m-%d')}\n")

    # ── 自动运维摘要 ──
    if maint_actions:
        has_fix = any(ok for ok, _ in maint_actions)
        lines.append("### 自动运维\n")
        for ok, msg in maint_actions:
            prefix = "✅" if ok else "⚠️"
            lines.append(f"- {prefix} {msg}")
        lines.append("")

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
        # 预算 — 优先实时查询 DeepSeek API，失败回退缓存
        live_balance = fetch_deepseek_balance()
        if live_balance:
            update_state_budget(live_balance)
            committee = load_json(STATE_PATH)  # 重新读取，拿到完整 budget 含状态
        budget = committee.get("budget", {})
        if budget:
            lines.append(f"- **预算**：月度 {budget.get('月度预算帽', 'N/A')} | 余额 {budget.get('当前余额_CNY', 'N/A')} 元 ({budget.get('状态', 'N/A')})")
        lines.append("")

    # ── 近期动态 ──
    lines.append("### 近期动态\n")

    # 近期附体
    if recent_calls:
        lines.append(f"**附体记录**（{len(recent_calls)} 条）")
        if compact:
            lines.append(f"，最近 5 条：\n")
            for r in recent_calls[-5:]:
                date = r.get("date", "")
                mode = r.get("mode", "")
                eff = r.get("effectiveness", "")
                soul = r.get("soul", "")
                task = r.get("task", "")
                role = r.get("role", "")
                role_str = f" [{role}]" if role else ""
                lines.append(f"- `{date}` **{mode}** {soul}{role_str} — {task}（{eff}）")
        else:
            lines.append("：\n")
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
        lines.append(f"**审查/报告产出**（{len(recent_reviews)} 份）")
        if compact:
            lines.append("\n")
        else:
            lines.append("：\n")
            for fname, mtime in sorted(recent_reviews, key=lambda x: x[1], reverse=True):
                lines.append(f"- `{mtime}` {fname}")
        lines.append("")

    # 近期会议
    if recent_meetings:
        lines.append(f"**会议**（{len(recent_meetings)} 次）")
        if compact:
            lines.append("\n")
        else:
            lines.append("：\n")
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
