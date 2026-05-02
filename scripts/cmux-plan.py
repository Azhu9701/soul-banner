#!/usr/bin/env python3
"""cmux × 万魂幡 编排计划生成器

读取魂 YAML → 提取 summon_prompt → 生成 cmux_launch_agents 所需参数。

用法:
  # 合议模式：生成多魂并行编排计划
  python3 scripts/cmux-plan.py --task "任务描述" --souls 毛泽东,费曼,鲁迅 --era "2026年中国互联网现状" -o /tmp/cmux-plan.json

  # 辩论模式：两魂对立
  python3 scripts/cmux-plan.py --task "议题" --souls 毛泽东,鲁迅 --mode debate -o /tmp/cmux-plan.json

  # 接力模式：指定顺序
  python3 scripts/cmux-plan.py --task "任务" --souls 费曼,邓小平,毛泽东 --mode relay -o /tmp/cmux-plan.json

输出 JSON 可直接作为 cmux_launch_agents 或 cmux_orchestrate 的参考参数。
"""

import argparse
import json
import os
import sys
import yaml

SOULS_DIR = os.path.join(os.path.dirname(__file__), "..", "souls")
ERA_CONTEXT_TEMPLATE = """## 时代背景

你被召唤到{year}年的中国。此时：
{context}

你的分析对象生活在此时此地。请在分析中注意你自身时代的局限——你可能在用过去的眼光看一个你从未亲身经历的世界。"""

ASSIGNMENT_TEMPLATE = """{task_description}

{summon_prompt}

{era_context}

---
本魂基于{refined_at}收魂素材炼化，素材来源包括多引擎搜索和公开文献。这不是{name}本人——这是基于其公开文本的 AI 模拟。在用它做高利害决策前，请交叉验证。"""


def load_soul(soul_name: str) -> dict:
    """读取魂 YAML 文件，返回关键字段"""
    path = os.path.join(SOULS_DIR, f"{soul_name}.yaml")
    if not os.path.exists(path):
        print(f"错误：魂档案不存在 {path}", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        data = yaml.safe_load(f)
    return data


def generate_era_context(task_context: str = "") -> str:
    """生成时代背景卡（2026年）"""
    year = "2026"
    base = [
        "- 互联网平台（微博、抖音、小红书、微信）是主要的公共话语空间",
        "- 算法推荐以互动率为核心指标，争议性内容获得不成比例的曝光",
    ]
    if task_context:
        base.append(f"- {task_context}")
    context = "\n".join(base)
    return ERA_CONTEXT_TEMPLATE.format(year=year, context=context)


def build_assignment(task: str, soul: dict, era: str) -> str:
    """为一个魂构建完整的 prompt（任务 + summon_prompt + 时代背景）"""
    return ASSIGNMENT_TEMPLATE.format(
        task_description=task,
        summon_prompt=soul.get("summon_prompt", f"你是{soul['name']}。"),
        era_context=era,
        refined_at=soul.get("refined_at", "未知日期"),
        name=soul["name"],
    )


def plan_conference(task: str, soul_names: list[str], era_context: str = "") -> dict:
    """合议模式：多魂并行分析"""
    assignments = []
    tab_names = []
    for name in soul_names:
        soul = load_soul(name)
        era = generate_era_context(era_context)
        prompt = build_assignment(task, soul, era)
        assignments.append(prompt)
        tab_names.append(f"{soul['grade']} {name}")

    return {
        "mode": "合议",
        "workspace_name": f"合议: {task[:20]}",
        "cli": "claude",
        "count": len(soul_names),
        "assignments": assignments,
        "tab_names": tab_names,
        "status": {
            "模式": "合议",
            "参与魂": ", ".join(soul_names),
            "阶段": "并行分析中",
        },
        "progress_label": "合议进度",
    }


def plan_debate(task: str, soul_names: list[str], era_context: str = "") -> dict:
    """辩论模式：两魂对立"""
    if len(soul_names) != 2:
        print("错误：辩论模式需要恰好 2 个魂", file=sys.stderr)
        sys.exit(1)

    era = generate_era_context(era_context)
    assignments = []
    tab_names = []

    # 正方
    soul_a = load_soul(soul_names[0])
    debate_prompt_a = (
        f"## 辩论议题\n{task}\n\n"
        f"你的立场：**正方**。请提出支持该立场的核心论点，并预见反方可能的反驳。\n\n"
        f"{build_assignment(task, soul_a, era)}"
    )
    assignments.append(debate_prompt_a)
    tab_names.append(f"正方 {soul_names[0]}")

    # 反方
    soul_b = load_soul(soul_names[1])
    debate_prompt_b = (
        f"## 辩论议题\n{task}\n\n"
        f"你的立场：**反方**。请反驳正方论点，并提出替代方案。\n\n"
        f"{build_assignment(task, soul_b, era)}"
    )
    assignments.append(debate_prompt_b)
    tab_names.append(f"反方 {soul_names[1]}")

    return {
        "mode": "辩论",
        "workspace_name": f"辩论: {task[:20]}",
        "cli": "claude",
        "count": 2,
        "assignments": assignments,
        "tab_names": tab_names,
        "status": {
            "模式": "辩论",
            f"正方": soul_names[0],
            f"反方": soul_names[1],
            "阶段": "立论中",
        },
        "progress_label": "辩论进度",
    }


def plan_relay(task: str, soul_names: list[str], era_context: str = "") -> dict:
    """接力模式：按序串联，前魂输出为后魂输入"""
    era = generate_era_context(era_context)
    assignments = []
    tab_names = []

    for i, name in enumerate(soul_names):
        soul = load_soul(name)
        relay_prompt = build_assignment(task, soul, era)

        if i == 0:
            # 第一棒：独立启动
            relay_prompt = f"## 接力第 1 棒\n\n你是第一棒。请独立分析以下任务，输出完整的分析结果。\n\n{relay_prompt}"
        else:
            # 后续棒：上一位的输出会由主 agent 在后续步骤中注入
            relay_prompt = (
                f"## 接力第 {i+1} 棒\n\n"
                f"上一棒（{soul_names[i-1]}）的输出会由协调者提供给你。"
                f"请等待接收上一棒的输出后，基于其分析进行深化或转向。\n\n"
                f"{relay_prompt}"
            )

        assignments.append(relay_prompt)
        tab_names.append(f"第{i+1}棒 {name}")

    return {
        "mode": "接力",
        "workspace_name": f"接力: {task[:20]}",
        "cli": "claude",
        "count": len(soul_names),
        "assignments": assignments,
        "tab_names": tab_names,
        "status": {
            "模式": "接力",
            "顺序": " → ".join(soul_names),
            "阶段": f"第1棒 {soul_names[0]} 启动中",
        },
        "progress_label": "接力进度",
    }


def main():
    parser = argparse.ArgumentParser(description="cmux × 万魂幡 编排计划生成器")
    parser.add_argument("--task", required=True, help="任务描述")
    parser.add_argument("--souls", required=True, help="魂名列表，逗号分隔（如 毛泽东,费曼,鲁迅）")
    parser.add_argument(
        "--mode",
        choices=["conference", "debate", "relay"],
        default="conference",
        help="附体模式：conference(合议) / debate(辩论) / relay(接力)",
    )
    parser.add_argument("--era", default="", help="时代背景补充说明")
    parser.add_argument("-o", "--output", help="输出 JSON 文件路径（默认 stdout）")

    args = parser.parse_args()
    soul_names = [s.strip() for s in args.souls.split(",")]

    if args.mode == "conference":
        plan = plan_conference(args.task, soul_names, args.era)
    elif args.mode == "debate":
        plan = plan_debate(args.task, soul_names, args.era)
    elif args.mode == "relay":
        plan = plan_relay(args.task, soul_names, args.era)

    json_out = json.dumps(plan, ensure_ascii=False, indent=2)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w") as f:
            f.write(json_out)
        print(f"编排计划已写入 {args.output}")
    else:
        print(json_out)


if __name__ == "__main__":
    main()
