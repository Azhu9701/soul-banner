#!/usr/bin/env python3
"""附体上下文注入 — 「系统帮魂记住」而不是魂自己记忆

查询 call-records 中与当前任务相似的最近附体，生成 ≤200 token 上下文摘要，
在 spawn 魂时注入到 prompt 中。魂无状态——系统帮它记住。

用法：
  # 查询某魂与当前任务相关的历史附体
  python3 scripts/possession-context.py --soul "费曼" --task "分析具身智能的技术瓶颈"

  # 输出 JSON（供程序调用）
  python3 scripts/possession-context.py --soul "费曼" --task "..." --json

  # 限制输出 token 数（默认 200）
  python3 scripts/possession-context.py --soul "费曼" --task "..." --max-tokens 150

输出格式：
  {context_summary: "..."}   # Markdown 格式的上下文段，可直接拼接到 spawn prompt
  {context_found: bool}      # 是否找到相关历史
  {similar_possessions: int} # 找到的相关附体数
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CALL_RECORDS_PATH = os.path.join(SKILL_DIR, "call-records.yaml")
MAX_TOKENS_DEFAULT = 200

def load_call_records():
    """加载召唤记录，返回记录列表"""
    try:
        import yaml
    except ImportError:
        print("ERROR: PyYAML not available", file=sys.stderr)
        return []

    if not os.path.exists(CALL_RECORDS_PATH):
        return []

    with open(CALL_RECORDS_PATH) as f:
        data = yaml.safe_load(f.read())

    if isinstance(data, dict):
        return data.get("召唤记录", data.get("records", []))
    return data if isinstance(data, list) else []

def tokenize_keywords(text: str) -> set[str]:
    """提取关键词：中文用n-gram（2-4字）+ 英文词"""
    tokens = set()
    # 英文：取连续的字母
    tokens.update(re.findall(r'[a-zA-Z]{2,}', text.lower()))
    # 中文：先提取连续中文字段，再用 n-gram 切分（2-4字）
    chinese_spans = re.findall(r'[一-鿿]{2,}', text)
    for span in chinese_spans:
        for n in (2, 3, 4):
            for i in range(len(span) - n + 1):
                tokens.add(span[i:i+n])
    return tokens

def jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """Jaccard 相似度"""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0

def direct_keyword_overlap(text_a: str, text_b: str) -> float:
    """直接关键词重叠：检查短文本的关键词是否在长文本中出现"""
    # 取较短文本的 2-4 字中文词，检查在长文本中是否出现
    shorter = text_a if len(text_a) <= len(text_b) else text_b
    longer = text_b if len(text_a) <= len(text_b) else text_a

    # 提取短文本中可能的关键词（2-4字连续中文）
    keywords = set(re.findall(r'[一-鿿]{2,4}', shorter))
    if not keywords:
        return 0.0

    hits = sum(1 for kw in keywords if kw in longer)
    return hits / len(keywords)

def combined_similarity(task_a: str, task_b: str) -> float:
    """组合相似度：Jaccard + 直接关键词重叠"""
    kws_a = tokenize_keywords(task_a)
    kws_b = tokenize_keywords(task_b)
    jac = jaccard_similarity(kws_a, kws_b)
    direct = direct_keyword_overlap(task_a, task_b)
    return jac * 0.4 + direct * 0.6  # 直接匹配权重更高

def find_similar_possessions(records: list, soul: str, task: str, top_n: int = 5, min_similarity: float = 0.1) -> list:
    """查找与当前任务相似的历史附体。
    若相似匹配不足，回退到最近附体（recency 也是相关性信号）。
    """
    candidates = []
    all_soul_records = []
    for r in records:
        if not isinstance(r, dict):
            continue
        if r.get("soul") != soul:
            continue

        r_task = r.get("task", "")
        sim = combined_similarity(task, r_task)

        entry = {
            "date": r.get("date", "?"),
            "mode": r.get("mode", "?"),
            "task": r_task,
            "effectiveness": r.get("effectiveness", "N/A"),
            "notes": r.get("notes", ""),
            "similarity": round(sim, 2),
        }

        if sim >= min_similarity:
            candidates.append(entry)
        all_soul_records.append(entry)

    candidates.sort(key=lambda x: (-x["similarity"], x.get("date", "")))

    # 回退：相似匹配不足时，取最近 N 条附体（标注为 recency fallback）
    if not candidates and all_soul_records:
        all_soul_records.sort(key=lambda x: x.get("date", ""), reverse=True)
        candidates = all_soul_records[:3]
        for c in candidates:
            c["similarity"] = 0.0
            c["fallback"] = True

    return candidates[:top_n]

def estimate_tokens(text: str) -> int:
    """粗略估计 token 数：中文 ≈ 字符数/1.5，英文 ≈ 词数"""
    chinese_chars = len(re.findall(r'[一-鿿]', text))
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    return int(chinese_chars / 1.5 + english_words) + 50  # +50 缓冲

def format_context(similar: list, max_tokens: int = MAX_TOKENS_DEFAULT) -> str:
    """将相似附体格式化为上下文注入段"""
    if not similar:
        return ""

    is_fallback = similar[0].get("fallback", False)
    lines = [
        "## 涉及本魂的历史附体上下文"
        + ("（无高度相似记录，显示最近附体）" if is_fallback else "")
    ]
    total_tokens = estimate_tokens(lines[0])

    for item in similar:
        notes_short = item["notes"][:80].replace("\n", " ")
        # 只取最近3条的详细 notes，其余仅一行
        eff_mark = {"有效": "✓", "部分有效": "~", "无效": "✗"}.get(item["effectiveness"], "?")
        line = f"- {item['date']} [{item['mode']}] {eff_mark} {item['task'][:60]}"
        line_tokens = estimate_tokens(line)

        if total_tokens + line_tokens > max_tokens:
            break

        lines.append(line)
        total_tokens += line_tokens

        # 为高相似度（≥0.3）的附体追加上下文
        if item["similarity"] >= 0.3 and notes_short:
            note_line = f"  → {notes_short}"
            note_tokens = estimate_tokens(note_line)
            if total_tokens + note_tokens <= max_tokens:
                lines.append(note_line)
                total_tokens += note_tokens

    # 如果找到了相关附体，追加提示行
    if len(lines) > 1:
        lines.append("\n当前任务与以上历史附体触发条件高度重合。请参考过往反馈调整分析精度。")
    else:
        return ""

    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="附体上下文注入")
    parser.add_argument("--soul", required=True, help="魂名")
    parser.add_argument("--task", required=True, help="当前任务描述")
    parser.add_argument("--max-tokens", type=int, default=MAX_TOKENS_DEFAULT, help="最大输出 token 数")
    parser.add_argument("--min-similarity", type=float, default=0.03, help="最小相似度阈值")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--raw", action="store_true", help="仅输出上下文文本（不包装）")
    args = parser.parse_args()

    records = load_call_records()
    if not records:
        result = {"context_found": False, "context_summary": "", "similar_possessions": 0}
        if args.json:
            print(json.dumps(result, ensure_ascii=False))
        sys.exit(0)

    similar = find_similar_possessions(records, args.soul, args.task, min_similarity=args.min_similarity)
    context = format_context(similar, args.max_tokens)

    if args.raw:
        print(context if context else "")
        sys.exit(0)

    result = {
        "context_found": bool(context),
        "context_summary": context,
        "similar_possessions": len(similar),
        "top_similarity": similar[0]["similarity"] if similar else 0.0,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result["context_found"]:
            print(context)
            print(f"\n<!-- 找到 {result['similar_possessions']} 条相关附体，最高相似度 {result['top_similarity']} -->")
        else:
            print(f"# 无相关历史附体（查询了 {len(records)} 条记录）")

if __name__ == "__main__":
    main()
