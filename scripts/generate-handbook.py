#!/usr/bin/env python3
"""幡主匹配手册 — 从 call-records 自动生成压缩匹配经验

策略：按魂聚合有效任务 → 提取核心任务关键词 → 交叉验证排除条件
输出：~600 tokens，直接注入幡主审查 prompt（替代 registry-lite 全量加载）

用法：
  python3 scripts/generate-handbook.py                        # Markdown 输出
  python3 scripts/generate-handbook.py -o committee/handbook.md  # 写入
  python3 scripts/generate-handbook.py --compact              # ~300 tokens 极简版
"""

import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CALL_RECORDS_PATH = os.path.join(SKILL_DIR, "call-records.yaml")
REGISTRY_PATH = os.path.join(SKILL_DIR, "registry.yaml")

def load_yaml(path):
    import yaml
    with open(path) as f:
        return yaml.safe_load(f)

def task_kw(task, min_len=2):
    """从任务中提取 bigram 关键词，排除停用词"""
    if not task:
        return []
    STOP = {'分析','评估','设计','是否','如何','什么','为什么','影响','问题',
            '方法','策略','发展','趋势','未来','当前','关键','与','的','在',
            '从','了','是','不','要','可以','进行','一个','这个','通过'}
    chinese = re.findall(r'[一-鿿]+', task)
    tokens = []
    for word in chinese:
        for i in range(len(word) - min_len + 1):
            t = word[i:i+min_len]
            if t not in STOP:
                tokens.append(t)
    # 英文词
    eng = re.findall(r'[a-zA-Z0-9]+', task)
    for w in eng:
        if len(w) >= 2:
            tokens.append(w.lower())
    return tokens

def extract_topic(task):
    """从任务描述中提取最具代表性的主题短语"""
    if not task:
        return "未分类"
    # 优先用 3-gram 提取有意义的短语
    tri = task_kw(task, min_len=3)
    if tri:
        freq = Counter(tri)
        # 去重：移除子串
        top = []
        for k, c in freq.most_common(8):
            if not any(k in t for t in top):
                top.append(k)
            if len(top) >= 2:
                break
        if top:
            return "·".join(top)
    # 回退到 2-gram
    bi = task_kw(task, min_len=2)
    freq = Counter(bi)
    long = [k for k in freq if len(k) >= 3]
    top = sorted(long, key=lambda k: -freq[k])[:2] if long else [k for k, _ in freq.most_common(2)]
    return "·".join(top) if top else "未分类"

def generate_handbook(out_file=None, compact=False):
    """从 call-records 生成匹配手册，返回生成的文本。若指定 out_file 则写入文件。"""
    cr = load_yaml(CALL_RECORDS_PATH)
    records = cr.get("records", []) + cr.get("召唤记录", [])
    registry = load_yaml(REGISTRY_PATH)
    souls_index = {s["name"]: s for s in registry.get("魂魄", [])}

    # ═══════════════════════════════════════════════
    # 1. 按魂聚合有效任务，提取该魂的核心胜任领域
    # ═══════════════════════════════════════════════
    soul_successes = defaultdict(list)  # soul → [(task_topic, task_full, effectiveness)]
    soul_fails = defaultdict(list)

    for r in records:
        soul = r.get("soul", "")
        if not soul or soul == "辩证综合官":
            continue
        task = r.get("task", "")
        eff = r.get("effectiveness", "")
        topic = extract_topic(task)

        if eff == "有效":
            soul_successes[soul].append((topic, task, eff))
        elif eff == "无效":
            soul_fails[soul].append((topic, task, eff, r.get("notes", "")))

    # 对每个魂，找出频繁出现的任务主题
    soul_rules = []
    for soul, successes in soul_successes.items():
        if len(successes) < 1:
            continue
        info = souls_index.get(soul, {})
        grade = info.get("grade", "?")

        # 任务主题聚类
        topic_counter = Counter(t[0] for t in successes)
        top_topics = topic_counter.most_common(4)

        # 效能统计
        total = len(successes) + len(soul_fails.get(soul, []))
        eff_rate = len(successes) / max(total, 1)

        # 提取与该魂注册 trigger 一致的验证
        trigger_kw = info.get("trigger_keywords_summary", "")
        exclude_kw = info.get("trigger_exclude_summary", "")

        soul_rules.append({
            "soul": soul,
            "grade": grade,
            "total": total,
            "eff_rate": eff_rate,
            "topics": [(t, c) for t, c in top_topics],
            "trigger_sample": trigger_kw[:80] if trigger_kw else "",
            "exclude_note": exclude_kw[:80] if exclude_kw else "",
            "success_count": len(successes),
            "fail_count": len(soul_fails.get(soul, [])),
        })

    soul_rules.sort(key=lambda x: -x["success_count"])

    # ═══════════════════════════════════════════════
    # 2. 发现跨魂失败模式
    # ═══════════════════════════════════════════════
    failure_patterns = []
    for soul, fails in soul_fails.items():
        for topic, task, eff, notes in fails:
            # 找是否有其他魂在同主题上成功
            better_soul = None
            for other_soul, successes in soul_successes.items():
                if other_soul == soul:
                    continue
                for s_topic, s_task, _ in successes:
                    # 简单关键词重叠判断
                    if len(set(task_kw(topic)) & set(task_kw(s_topic))) >= 2:
                        better_soul = other_soul
                        break
                if better_soul:
                    break
            failure_patterns.append({
                "wrong_soul": soul,
                "better_soul": better_soul,
                "task": task[:80],
                "notes": notes[:80],
            })

    # ═══════════════════════════════════════════════
    # 3. 零召唤魂
    # ═══════════════════════════════════════════════
    called = {r.get("soul", "") for r in records}
    zero_call = [s for s in registry.get("魂魄", [])
                 if s.get("name", "") not in called
                 and s.get("status") != "dismissed"]

    # ═══════════════════════════════════════════════
    # 4. 近期统计
    # ═══════════════════════════════════════════════
    recent = [r for r in records if r.get("date", "") >= "2026-04-30"]
    recent_eff = Counter(r.get("effectiveness", "") for r in recent
                         if r.get("soul") != "辩证综合官")
    top_souls = Counter(r.get("soul", "") for r in recent).most_common(5)

    # ═══════════════════════════════════════════════
    # 生成输出
    # ═══════════════════════════════════════════════
    lines = []
    lines.append("# 幡主匹配手册")
    lines.append(f"*{len(records)}次附体 · {datetime.now().strftime('%Y-%m-%d')}生成*")
    lines.append("")

    if compact:
        # ── 极简版：每魂一行 ──
        lines.append("## 魂效能速查\n")
        for r in soul_rules:
            if r["total"] == 0:
                continue
            soul = r["soul"]
            grade = r["grade"]
            icon = "🟢" if r["eff_rate"] >= 0.8 else "🟡" if r["eff_rate"] >= 0.5 else "🔴"
            topics_str = " | ".join(f"{t}({c})" for t, c in r["topics"][:3])
            lines.append(f"- {icon} **{soul}**({grade}) {r['success_count']}/{r['total']}有效 — {topics_str}")
        lines.append("")

        # 失败模式（只列有替代方案的）
        unique_fails = []
        seen = set()
        for fp in failure_patterns:
            if fp["better_soul"]:
                key = (fp["wrong_soul"], fp["better_soul"])
                if key not in seen:
                    seen.add(key)
                    unique_fails.append(fp)
        if unique_fails:
            lines.append("## 失败修正\n")
            for fp in unique_fails[:4]:
                lines.append(f"- {fp['wrong_soul']} → **{fp['better_soul']}**: {fp['task'][:50]}")
            lines.append("")

        # 零召唤
        if zero_call:
            names = [s["name"] for s in zero_call]
            lines.append(f"## 零召唤: {', '.join(names)}\n")

    else:
        # ── 完整版：按魂展开 ──
        lines.append("## 魂效能矩阵\n")
        for r in soul_rules:
            if r["total"] == 0:
                continue
            soul = r["soul"]
            grade_emoji = {"金":"🟡","银":"🥈","紫":"🟣","蓝":"🔵","绿":"🟢","白":"⚪"}.get(r["grade"],"")
            icon = "✅" if r["eff_rate"] >= 0.8 else "⚠️" if r["eff_rate"] >= 0.5 else "❌"

            lines.append(f"### {icon} {soul} {grade_emoji} ({r['success_count']}/{r['total']}有效)")
            for topic, count in r["topics"]:
                lines.append(f"  - {topic} ×{count}")
            if r["exclude_note"]:
                lines.append(f"  - ⚠ 排除: {r['exclude_note']}")
            lines.append("")

        # 失败模式
        if failure_patterns:
            unique_fails = []
            seen = set()
            for fp in failure_patterns:
                if fp["better_soul"]:
                    key = (fp["wrong_soul"], fp["better_soul"])
                    if key not in seen:
                        seen.add(key)
                        unique_fails.append(fp)
            if unique_fails:
                lines.append("## 跨魂失败修正\n")
                for fp in unique_fails[:8]:
                    lines.append(f"- **{fp['wrong_soul']}** → {fp['better_soul']}")
                    lines.append(f"  {fp['task'][:60]}")
                lines.append("")

        # 零召唤
        if zero_call:
            lines.append("## 零召唤魂\n")
            for s in zero_call:
                name = s.get("name", "")
                grade = s.get("grade", "?")
                domain = s.get("domain", [])[:3]
                trigger = s.get("trigger_scenarios_summary", "")[:100]
                lines.append(f"- **{name}** ({grade}魂) — {', '.join(domain)}")
                lines.append(f"  {trigger}")
            lines.append("")

        # 近期统计
        lines.append("## 近期统计\n")
        lines.append(f"近期 {len(recent)}次: 有效{recent_eff.get('有效',0)}/部分{recent_eff.get('部分有效',0)}/无效{recent_eff.get('无效',0)}")
        lines.append(f"Top5: {', '.join(f'{s}({c})' for s,c in top_souls)}")
        lines.append("")

    output = "\n".join(lines)

    if out_file:
        os.makedirs(os.path.dirname(out_file) or ".", exist_ok=True)
        with open(out_file, "w") as f:
            f.write(output)
        size = len(output.encode('utf-8'))
        est_tokens = size // 4
        print(f"✅ 手册: {out_file} ({size}B, ~{est_tokens} tokens)")
    return output

def main():
    out_file = None
    compact = False
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "-o" and i + 1 < len(args):
            out_file = args[i + 1]
            i += 2
        elif args[i] == "--compact":
            compact = True
            i += 1
        else:
            i += 1

    output = generate_handbook(out_file=out_file, compact=compact)
    if not out_file:
        print(output)
        size = len(output.encode('utf-8'))
        print(f"\n*({size}B, ~{size//4} tokens)*", file=sys.stderr)

if __name__ == "__main__":
    main()
