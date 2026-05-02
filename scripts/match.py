#!/usr/bin/env python3
"""万魂幡匹配预筛选 — 关键词/场景/排除条件评分，替代幡主全量读 registry-lite

输入：任务描述
输出：首选魂 + 备选 + 排除清单 + 触发详情（JSON 或 Markdown）
用途：主 agent 将输出注入幡主审查 prompt，幡主只做判断不复述数据

用法：
  python3 scripts/match.py "任务描述"                    # Markdown 输出（给人看/给幡主）
  python3 scripts/match.py "任务描述" --json             # JSON 输出（给主 agent 解析）
  python3 scripts/match.py "任务描述" --top 5            # 返回 top-5 备选
  python3 scripts/match.py "任务描述" --no-gold-review   # 省略 gold_review（更短上下文）
"""

import json
import os
import re
import sys
from collections import defaultdict

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_PATH = os.path.join(SKILL_DIR, "registry.yaml")

def load_yaml(path):
    import yaml
    with open(path) as f:
        return yaml.safe_load(f)

def tokenize(text):
    """中文 n-gram 分词：只保留 bigram 和 trigram，不保留单字（假阳性太高）"""
    tokens = set()
    chinese = re.findall(r'[一-鿿]+', text)
    for word in chinese:
        # Bigram
        for i in range(len(word) - 1):
            tokens.add(word[i:i+2])
        # Trigram（更精确的短语匹配）
        for i in range(len(word) - 2):
            tokens.add(word[i:i+3])
        # 保留原词（长词直接匹配）
        if len(word) >= 2:
            tokens.add(word)
    # 英文/数字词
    eng = re.findall(r'[a-zA-Z0-9]+', text)
    for w in eng:
        tokens.add(w.lower())
    return tokens

# 高频干扰 bigram（在多个魂的关键词中出现，区分度低）
STOP_BIGRAMS = {
    '分析', '主义', '批判', '理论', '哲学', '制度', '组织', '建设',
    '战略', '决策', '设计', '系统', '技术', '管理', '研究', '方法',
    '实践', '科学', '思维', '认识', '社会', '革命', '政治', '经济',
    '文学', '精神', '知识', '学习', '传播', '教育', '文化', '历史',
}

def keyword_overlap(task_tokens, keyword_text, all_soul_keywords=None):
    """计算任务与关键词列表的重叠度。使用绝对匹配分（不限总分），避免宽领域魂被稀释"""
    if not keyword_text:
        return [], 0.0

    keywords = [k.strip() for k in re.split(r'[、,，/]', keyword_text) if k.strip()]
    matched = []
    fuzzy_matched = []
    matched_score = 0  # 绝对分，不归一化

    for kw in keywords:
        kw_lower = kw.lower()
        kw_len = len(kw)
        kw_tokens = tokenize(kw)

        # 关键词区分度：长关键词+无停用词=高区分度
        kw_bigrams = {t for t in kw_tokens if len(t) == 2}
        has_stop = bool(kw_bigrams & STOP_BIGRAMS)
        is_noisy = kw_len <= 2 and has_stop
        is_high_specificity = kw_len >= 3 and not has_stop

        if is_noisy:
            kw_weight = 0.15  # 2字停用词（"分析""主义"）几乎无效
        elif has_stop and kw_len <= 2:
            kw_weight = 0.2   # 2字含停用词
        elif has_stop:
            kw_weight = 0.5   # 3+字含停用词（如"帝国主义"→可能真匹配"帝国"，也可能假匹配"主义"）
        elif is_high_specificity:
            kw_weight = 2.0   # 高区分度（如"瞒和骗""阿米巴"）
        elif kw_len >= 3:
            kw_weight = 1.0
        else:
            kw_weight = 0.4

        # 精确匹配
        direct_match = (
            kw_lower in task_tokens or
            any(t == kw_lower for t in task_tokens if len(t) >= 2) or
            any(kw_t in task_tokens for kw_t in kw_tokens if len(kw_t) >= 2)
        )
        if direct_match:
            matched.append(kw)
            matched_score += kw_weight
            continue

        # 反向匹配
        contained = [t for t in task_tokens if len(t) >= 2 and t in kw_lower and t not in STOP_BIGRAMS]
        if contained:
            fuzzy_matched.append(kw)
            matched_score += kw_weight * 0.3

    score = min(matched_score / 3.0, 1.0)  # 归一化到 [0,1]，3 个高区分度命中 = 满分
    result_list = matched + [f"{m}≈" for m in fuzzy_matched]
    return result_list, score

def exclude_check(task_lower, exclude_text):
    """检查排除条件是否触发。两级排除：
    - hard: 排除词精确命中任务核心（子串匹配 + 词长>=3）→ ×0.1
    - soft: 模糊匹配或短词匹配 → ×0.5
    """
    if not exclude_text:
        return [], "none"

    excludes = [e.strip() for e in re.split(r'[、,，/]', exclude_text) if e.strip()]
    hard_triggered = []
    soft_triggered = []
    task_tokens_lower = set(t.lower() for t in tokenize(task_lower))

    for ex in excludes:
        ex_lower = ex.lower()
        ex_tokens = tokenize(ex_lower)
        ex_len = len(ex)

        # 精确子串匹配——是核心排除信号
        if ex_lower in task_lower:
            # 长词精确命中 = hard（如"纯财务会计准则合规"命中任务）
            if ex_len >= 4:
                hard_triggered.append(ex)
            # 中词精确命中 = hard，除非是明显的附属提及
            elif ex_len >= 3:
                # 检查排除词是否在任务中处于附属位置（括号内、"包括"/"如"/"除"后）
                idx = task_lower.find(ex_lower)
                context_before = task_lower[max(0, idx - 10):idx]
                is_subordinate = any(marker in context_before for marker in ['包括', '例如', '比如', '除了', '除', '附带', '此外', '以及'])
                if is_subordinate:
                    soft_triggered.append(f"{ex}~")
                else:
                    hard_triggered.append(ex)
            else:
                # 2字词精确命中 → soft（短词太容易误伤）
                soft_triggered.append(f"{ex}~")
            continue

        # 模糊匹配（token overlap >= 50%）→ soft
        if len(ex_tokens) >= 2:
            overlap = ex_tokens & task_tokens_lower
            if len(overlap) >= len(ex_tokens) * 0.5:
                soft_triggered.append(f"{ex}?")

    # 返回最高风险级别
    all_triggered = hard_triggered + soft_triggered
    if hard_triggered:
        return all_triggered, "hard"
    elif soft_triggered:
        return all_triggered, "soft"
    return [], "none"

def score_soul(soul, task):
    """对单个魂评分，返回 (score, details)"""
    task_lower = task.lower()
    task_tokens_lower = set(t.lower() for t in tokenize(task))
    task_tokens = tokenize(task) | task_tokens_lower

    details = {}

    # 1. 关键词匹配
    kw_text = soul.get("trigger_keywords_summary", "")
    kw_matched, kw_score = keyword_overlap(task_tokens, kw_text)
    details["keyword_matches"] = kw_matched
    details["keyword_score"] = kw_score

    # 2. 场景匹配
    sc_text = soul.get("trigger_scenarios_summary", "")
    sc_matched, sc_score = keyword_overlap(task_tokens, sc_text)
    details["scenario_matches"] = sc_matched
    details["scenario_score"] = sc_score

    # 3. 排除检查
    ex_text = soul.get("trigger_exclude_summary", "")
    ex_triggered, ex_risk = exclude_check(task_lower, ex_text)
    details["exclude_triggered"] = ex_triggered
    details["exclude_risk"] = ex_risk

    # 4. 领域加分
    domains = soul.get("domain", [])
    domain_bonus = 0
    for d in domains:
        if d in task or any(t in task_lower for t in tokenize(d)):
            domain_bonus += 0.05
            if "domain_matches" not in details:
                details["domain_matches"] = []
            details["domain_matches"].append(d)
    details["domain_bonus"] = min(domain_bonus, 0.2)

    # 综合评分
    score = (
        kw_score * 0.5 +
        sc_score * 0.3 +
        details["domain_bonus"]
    )

    # 排除惩罚（两级）
    if ex_risk == "hard":
        score *= 0.1
    elif ex_risk == "soft":
        score *= 0.5

    return min(score, 1.0), details


def load_usage_counts(registry_path):
    """从 call-records.yaml 加载每个魂的使用次数。文件不存在则返回空 dict。"""
    import os as _os
    records_path = _os.path.join(_os.path.dirname(registry_path), "call-records.yaml")
    if not _os.path.exists(records_path):
        return {}
    try:
        records = load_yaml(records_path)
    except Exception:
        return {}
    counts = {}
    for entry in records if isinstance(records, list) else records.get("召唤记录", []):
        soul = entry.get("魂名") or entry.get("soul") or entry.get("魂", "")
        if soul:
            counts[soul] = counts.get(soul, 0) + 1
    return counts


def apply_cognitive_distance(scored_results, usage_counts):
    """认知距离调整：使用越频繁的魂轻微降权，优先推荐使用者较少接触的魂。

    公式：freshness = 1.0 / (1 + ln(usage + 1))，归一化到 [-0.05, +0.05]
    使用 0 次的魂 +0.05，使用 20+ 次的魂 -0.05。
    这不是品质评分——是反消费机制：强迫使用者接触陌生框架。
    """
    import math
    if not usage_counts:
        return scored_results

    freshness_scores = {}
    for r in scored_results:
        usage = usage_counts.get(r["name"], 0)
        freshness = 1.0 / (1 + math.log(usage + 1))
        freshness_scores[r["name"]] = freshness

    if not freshness_scores:
        return scored_results

    vals = list(freshness_scores.values())
    min_v, max_v = min(vals), max(vals)
    if max_v == min_v:
        return scored_results

    for r in scored_results:
        f = freshness_scores.get(r["name"], 0.5)
        # 归一化到 [-0.05, +0.05]
        normalized = (f - min_v) / (max_v - min_v) * 0.10 - 0.05
        r["score"] = min(round(r["score"] + normalized, 3), 1.0)
        r["freshness_bonus"] = round(normalized, 3)

    return scored_results

def format_output(results, task, show_gold_review=True):
    """生成 Markdown 格式输出（给幡主审查用）"""
    lines = []
    lines.append(f"## 匹配预筛选\n")
    lines.append(f"**任务**: {task}\n")

    primary = results[0] if results else None
    alternatives = results[1:] if len(results) > 1 else []
    excluded = [r for r in results if r["exclude_risk"] == "high" and r["score"] < 0.15]

    if primary:
        p = primary
        lines.append("### 首选\n")
        lines.append(f"**{p['name']}** ({p['grade']}魂) — 匹配分 {p['score']:.2f}")
        lines.append(f"- 触发关键词: {', '.join(p['keyword_matches'][:8]) or '无'}")
        lines.append(f"- 触发场景: {', '.join(p['scenario_matches'][:5]) or '无'}")
        risk_label = {"none":"无","soft":"软排除","hard":"硬排除"}.get(p['exclude_risk'], p['exclude_risk'])
        lines.append(f"- 排除风险: {risk_label} {p['exclude_triggered'] if p['exclude_triggered'] else ''}")
        lines.append(f"- 领域: {', '.join(p.get('domain', []))}")
        if show_gold_review and p.get("gold_review"):
            lines.append(f"- Gold Review: {p['gold_review'][:200]}")
        lines.append("")

    if alternatives:
        lines.append("### 备选\n")
        for i, a in enumerate(alternatives[:4]):
            lines.append(f"{i+1}. **{a['name']}** ({a['grade']}魂, {a['score']:.2f}) — {', '.join(a['keyword_matches'][:4]) or '无关键词命中'}")
        lines.append("")

    # 排除清单（区分硬排除和软排除）
    hard_exclude = [r for r in results if r["exclude_risk"] == "hard"]
    soft_exclude = [r for r in results if r["exclude_risk"] == "soft"]
    if hard_exclude:
        lines.append("### 硬排除预警\n")
        for e in hard_exclude:
            lines.append(f"- **{e['name']}**: 排除词命中 → {', '.join(e['exclude_triggered'][:5])}")
        lines.append("")
    if soft_exclude:
        lines.append("### 软排除提示\n")
        for e in soft_exclude:
            suffix = "~" if any(t.endswith("~") for t in e.get("exclude_triggered", [])) else ""
            lines.append(f"- **{e['name']}** (评分 ×0.5): {', '.join(e['exclude_triggered'][:5])}")
        lines.append("")

    # 结构化审查清单
    lines.append("### 幡主审查清单\n")
    lines.append("请逐条回答（每条一句话）：")
    lines.append("1. **领域匹配**: 首选魂的领域是否覆盖此任务？[Y/N]")
    lines.append("2. **排除风险**: 排除条件是否实质性触发？[Y/N + 哪个]")
    lines.append("3. **边界风险**: 适用边界外溢风险？[无/低/中/高 + 简述]")
    lines.append("4. **裁决**: [通过 / 换X / 加Y约束 / 需第二审查官]")

    return "\n".join(lines)

def main():
    args = sys.argv[1:]
    if not args:
        print("用法: python3 scripts/match.py '任务描述' [--json] [--top N] [--no-gold-review]")
        sys.exit(1)

    task = args[0]
    as_json = "--json" in args
    top_n = 5
    show_gold = "--no-gold-review" not in args

    for i, a in enumerate(args):
        if a == "--top" and i + 1 < len(args):
            top_n = int(args[i + 1])

    # 加载 registry
    registry = load_yaml(REGISTRY_PATH)
    souls = registry.get("魂魄", [])

    # 过滤已散魂
    active_souls = [s for s in souls if s.get("status") != "dismissed"]

    # 评分
    scored = []
    for soul in active_souls:
        score, details = score_soul(soul, task)
        if score > 0 or details["exclude_risk"] in ("hard", "soft"):
            scored.append({
                "name": soul.get("name", ""),
                "grade": soul.get("grade", "?"),
                "domain": soul.get("domain", []),
                "gold_review": soul.get("gold_review", "") if show_gold else "",
                "score": round(score, 3),
                **{f"match_{k}": v for k, v in details.items()},
                **details,
            })

    # 认知距离调整：使用越少的魂越优先（反消费机制）
    usage_counts = load_usage_counts(REGISTRY_PATH)
    scored = apply_cognitive_distance(scored, usage_counts)

    # 排序：排除风险低的优先，同风险按分数
    risk_order = {"none": 0, "soft": 1, "hard": 2}
    scored.sort(key=lambda x: (
        risk_order.get(x["exclude_risk"], 0),
        -x["score"]
    ))
    top_results = scored[:top_n]

    # JSON 输出
    if as_json:
        output = {
            "task": task,
            "total_souls": len(active_souls),
            "primary": top_results[0] if top_results else None,
            "alternatives": top_results[1:] if len(top_results) > 1 else [],
            "all_scored": scored,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(format_output(top_results, task, show_gold_review=show_gold))


if __name__ == "__main__":
    main()
