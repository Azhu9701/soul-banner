#!/usr/bin/env python3
"""万魂幡自动纠察队 — PostToolUse Hook

检测主 agent 的违规行为：
  1. 主 agent 自行模拟多视角分析（没有 spawn 魂却有分析行为）
  2. 主 agent 跳过列宁审查直接附体
  3. 主 agent 在合议/辩论中自行做辩证综合而非 spawn 列宁

始终 exit 0（warning 性质，不阻断）。
违规输出到 logs/discipline_violations.log。
累计统计跨会话持久化到 logs/discipline_cumulative.json。
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(SKILL_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "discipline_violations.log")
STATE_FILE = os.path.join(LOG_DIR, "discipline_state.json")
CUMULATIVE_FILE = os.path.join(LOG_DIR, "discipline_cumulative.json")

# === 违规检测模式 ===

# 模式组1：自行模拟多视角分析
MULTI_PERSPECTIVE_PATTERNS = [
    # 中文
    r"从.{0,4}(?:角度|视角|方面|维度).{0,6}(?:来看|分析|思考|看)",
    r"让我.{0,4}(?:从.{0,4}(?:视角|角度|思维).{0,4}分析)",
    r"以.{0,4}(?:思维|视角|立场|角度).{0,6}(?:分析|来看|思考)",
    r"从多个.{0,4}(?:角度|视角|方面|维度)",
    r"换个.{0,4}(?:角度|视角|思维)",
    r"综合.{0,4}(?:来看|视角|角度|各方)",
    r"站在.{0,4}(?:角度|立场|视角)",
    r"我来.{0,3}分析.{0,3}(?:一下|这个|当前)",
    r"我们来看",
    r"多.{0,2}视角.{0,3}分析",
    r"多方.{0,2}(?:面|位).{0,3}分析",
    r"辩证.{0,2}地.{0,2}(?:看|分析|考察)",
    r"从(?:积极|消极|正面|负面|乐观|悲观).{0,4}(?:面|角度)",
    # 英文
    r"from\s+(?:\w+\s+)?(?:perspective|angle|viewpoint|standpoint)",
    r"let\s+me\s+analyze\s+(?:from|this\s+from)",
    r"look(?:ing)?\s+at\s+(?:this|it)\s+from\s+(?:\w+\s+)?(?:perspective|angle)",
    r"multiple\s+(?:perspectives|angles|viewpoints|lenses)",
    r"different\s+(?:perspective|angle|lens|view)",
    r"in\s+(?:\w+'s)\s+(?:view|opinion|perspective)",
]

# 模式组2：自行辩证综合（没有 spawn 列宁）
DIALECTICAL_SYNTHESIS_PATTERNS = [
    # 中文
    r"综合.{0,3}(?:以上|各方|所述|来看|观点)",
    r"共识.{0,4}(?:是|在于|：).{0,6}分歧.{0,4}(?:是|在于|：)",
    r"主要矛盾.{0,4}(?:是|在于|：)",
    r"辩证综合",
    r"总结.{0,2}(?:各方|不同|以上).{0,4}(?:观点|意见|视角)",
    r"正反两方面",
    r"(?:综上所述|总的来看|总体而言).{0,3}(?:分歧|共识|矛盾)",
    r"各方.{0,2}(?:核心|主要).{0,4}(?:分歧|共识)",
    r"批判.{0,2}(?:角度|视角).{0,4}(?:审查|检验|检查)",
    r"合议.{0,4}(?:结论|结果|裁决|判断)",
    r"辩论.{0,4}(?:裁决|结论|胜方|结果)",
    r"行动纲领",
    # 英文
    r"in\s+summary.{0,20}(?:consensus|agreement).{0,20}(?:disagreement|divergence)",
    r"dialectical\s+synthesis",
    r"principal\s+contradiction",
    r"synthesiz(?:e|ing).{0,10}(?:perspectives|views|opinions)",
    r"(?:to\s+sum\s+up|in\s+conclusion).{0,10}(?:consensus|disagreement)",
    r"both\s+sides.{0,20}(?:agree|disagree|argue)",
    r"action\s+(?:plan|program|agenda)",
]

# 模式组3：跳过列宁审查的信号
SKIP_LENIN_PATTERNS = [
    r"我.{0,3}(?:认为|觉得|判断).{0,6}(?:匹配|适用|适合).{0,6}(?:恰当|正确|合理|没问题)",
    r"(?:快速|直接|跳过).{0,4}(?:审查|审查流程|匹配审查)",
    r"(?:不?需要|不用).{0,3}spawn.{0,3}(?:列宁|审查)",
    r"单魂.{0,4}(?:也|就|可以).{0,3}(?:不.{0,3}审查|跳过|直接)",
    r"快速路径",
    # 英文
    r"skip.{0,5}(?:review|inspection|lenin)",
    r"no\s+need.{0,10}(?:spawn|review|lenin)",
    r"don't\s+need.{0,10}(?:spawn|review|lenin)",
    r"fast\s+(?:path|track)",
    r"this\s+match\s+is\s+(?:fine|ok|correct|appropriate)",
]

# === 豁免模式 ===
# 只有明确的 Skill(soul-banner) 调用或 spawn 魂的行为才豁免。
# 裸词 "万魂幡" / "soul-banner" 不再豁免 —— 提及不等于执行。

EXEMPTION_PATTERNS = [
    # 明确调用 Skill
    r"Skill\(\s*soul-banner\s*\)",
    # 明确的 spawn + 魂名 组合（确实在 spawn）
    r"spawn.{0,8}(?:子\s*agent|列宁|审查|魂)",
    r"Spawn.{0,8}(?:列宁|Lenin|审查|魂)",
    # 通过 Agent tool 实际 spawn
    r'"name":\s*".{0,20}(?:列宁|Lenin|审查|Karpathy|费曼|Feynman|毛泽东|Mao|鲁迅|LuXun|未明子)"',
]

# === 报告性上下文标记 ===
# 当违规模式出现在这些上下文中，说明主 agent 在报告/转述子 agent 输出而非自行分析
# 此时降级为 WARNING 而非 VIOLATION
REPORTING_CONTEXT_PATTERNS = [
    r"(?:子\s*agent|魂)\s*(?:输出|报告|分析|认为|指出|说)",
    r"(?:审查|分析)\s*(?:报告|结论|结果)",
    r"(?:以上|以下)\s*(?:是|为)\s*(?:.{0,4}魂|.{0,4}agent)\s*(?:的|之)?\s*(?:输出|报告|审查)",
    r"\[.{0,20}(?:审查|报告|输出).{0,20}\]",
]


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "conversation_start": datetime.now(timezone.utc).isoformat(),
            "soul_banner_invocations": 0,
            "lenin_spawns": 0,
            "violation_count": 0,
            "last_violation_at": None,
            "tool_calls_tracked": [],
        }


def load_cumulative():
    try:
        with open(CUMULATIVE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "total_violations": 0,
            "total_invocations": 0,
            "total_spawns": 0,
            "total_checks": 0,
            "by_type": {"multi_perspective": 0, "dialectical_synthesis": 0, "skip_lenin_review": 0},
            "first_seen": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }


def save_cumulative(cumulative):
    cumulative["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(CUMULATIVE_FILE, "w") as f:
        json.dump(cumulative, f, ensure_ascii=False, indent=2)


def save_state(state):
    state["tool_calls_tracked"] = state["tool_calls_tracked"][-50:]
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def log_violation(violation_type: str, detail: str, evidence: str, is_warning: bool = False):
    """记录违规到日志文件"""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    level = "WARNING" if is_warning else "VIOLATION"
    entry = (
        f"[{timestamp}] [{level}] [{violation_type}]\n"
        f"  Detail: {detail}\n"
        f"  Evidence: {evidence[:300]}\n"
        f"{'─' * 60}\n"
    )
    with open(LOG_FILE, "a") as f:
        f.write(entry)

    if not is_warning:
        msg = (
            f"【万魂幡纠察队】检测到疑似违规：[{violation_type}]\n"
            f"  {detail}\n\n"
            f"  提示：\n"
            f"  - 涉及多视角分析或辩证综合时，请调用 Skill(soul-banner) 并 spawn 列宁审查\n"
            f"  - 主 agent 禁止自行模拟多视角、禁止自行辩证综合\n"
            f"  - 实验数据：自行模拟召回率 = 0%\n\n"
            f"  本次不阻断操作，但请留意上述提醒。"
        )
        print(json.dumps({"systemMessage": msg}, ensure_ascii=False))


def extract_all_text(obj, max_depth=5):
    if max_depth <= 0:
        return ""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        return " ".join(extract_all_text(v, max_depth - 1) for v in obj.values())
    if isinstance(obj, list):
        return " ".join(extract_all_text(v, max_depth - 1) for v in obj)
    return ""


def find_patterns(text: str, patterns: list[str]) -> list[str]:
    matches = []
    for pattern in patterns:
        found = re.findall(pattern, text)
        matches.extend(found)
    return matches


def check_exemptions(text: str) -> bool:
    """只在明确调用 Skill(soul-banner) 或 spawn 魂时豁免。
    裸词'万魂幡'/'soul-banner'不再豁免——提及不等于执行。"""
    for pattern in EXEMPTION_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def check_reporting_context(text: str) -> bool:
    """检查违规模式是否出现在报告/转述子 agent 输出的上下文中"""
    for pattern in REPORTING_CONTEXT_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        print("{}")
        sys.exit(0)

    os.makedirs(LOG_DIR, exist_ok=True)

    state = load_state()
    cumulative = load_cumulative()
    cumulative["total_checks"] += 1

    all_text = extract_all_text(input_data)

    if not all_text or len(all_text) < 10:
        save_state(state)
        print("{}")
        sys.exit(0)

    tool_name = input_data.get("tool_name", input_data.get("name", "unknown"))

    # 精确计数：只在明确的调用上下文中计数，避免路径名匹配膨胀
    if re.search(r"Skill\(\s*soul-banner\s*\)", all_text) or re.search(r"调用.{0,4}soul-banner", all_text):
        state["soul_banner_invocations"] += 1
        cumulative["total_invocations"] += 1
    if re.search(r"(?:spawn|Spawn|Agent\().{0,15}(?:列宁|Lenin|审查官)", all_text):
        state["lenin_spawns"] += 1
        cumulative["total_spawns"] += 1

    state["tool_calls_tracked"].append(
        {
            "tool": tool_name,
            "time": datetime.now(timezone.utc).isoformat(),
            "text_preview": all_text[:200],
        }
    )

    # 豁免检查 —— 只有明确调用 soul-banner 或 spawn 魂时才跳过
    if check_exemptions(all_text):
        save_state(state)
        save_cumulative(cumulative)
        print("{}")
        sys.exit(0)

    # === 违规检测（非互斥 —— 收集所有匹配的违规类型）===

    violations = []
    is_reporting = check_reporting_context(all_text)

    mp_matches = find_patterns(all_text, MULTI_PERSPECTIVE_PATTERNS)
    if mp_matches:
        violations.append((
            "multi_perspective",
            "自行模拟多视角分析",
            f"检测到 {len(mp_matches)} 个多视角分析模式，但未调用 Skill(soul-banner)",
            " | ".join(mp_matches[:5]),
        ))

    ds_matches = find_patterns(all_text, DIALECTICAL_SYNTHESIS_PATTERNS)
    if ds_matches:
        violations.append((
            "dialectical_synthesis",
            "自行辩证综合",
            f"检测到 {len(ds_matches)} 个辩证综合模式，但未 spawn 列宁进行辩证综合",
            " | ".join(ds_matches[:5]),
        ))

    sl_matches = find_patterns(all_text, SKIP_LENIN_PATTERNS)
    if sl_matches:
        violations.append((
            "skip_lenin_review",
            "疑似跳过列宁审查",
            f"检测到 {len(sl_matches)} 个跳过审查信号",
            " | ".join(sl_matches[:5]),
        ))

    if violations:
        for vtype, vname, detail, evidence in violations:
            log_violation(vname, detail, evidence, is_warning=is_reporting)
            if not is_reporting:
                state["violation_count"] += 1
                cumulative["total_violations"] += 1
                cumulative["by_type"][vtype] += 1
                state["last_violation_at"] = datetime.now(timezone.utc).isoformat()

    save_state(state)
    if cumulative["total_checks"] % 10 == 0:
        save_cumulative(cumulative)
    print("{}")
    sys.exit(0)


if __name__ == "__main__":
    main()
