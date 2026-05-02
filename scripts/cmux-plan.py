#!/usr/bin/env python3
"""cmux × 万魂幡 编排计划生成器

读取魂 YAML → 生成 cmux pane 调度 prompt（调用 Agent(subagent_type) 而非裸回答）。

用法:
  # 合议模式：生成多魂并行编排计划
  python3 scripts/cmux-plan.py --task "任务描述" --task-slug "ai-education" \
    --souls 费曼,鲁迅 --era "2026年中国互联网现状" -o /tmp/cmux-plan.json

  # 辩论模式：两魂对立
  python3 scripts/cmux-plan.py --task "议题" --task-slug "debate-topic" \
    --souls 毛泽东,鲁迅 --mode debate -o /tmp/cmux-plan.json

  # 接力模式：指定顺序
  python3 scripts/cmux-plan.py --task "任务" --task-slug "relay-task" \
    --souls 费曼,邓小平,毛泽东 --mode relay -o /tmp/cmux-plan.json

架构:
  cmux pane（调度器）→ Agent(subagent_type="{魂名}") → 魂 agent 分析 → 写入文件
  cmux pane 只做调度，不直接回答。分析质量由魂 agent 保证。
"""

import argparse
import json
import os
import re
import sys
import yaml

SOULS_DIR = os.path.join(os.path.dirname(__file__), "..", "souls")

# cmux pane 收到的 prompt：召唤魂 agent 的调度指令
# 注意：agent_prompt 会被直接替换进 Agent() 调用的 prompt 参数中
COORDINATOR_TEMPLATE = """你的任务是调度指定的魂 agent 来分析问题。不要自己回答——使用 Agent 工具调用魂 agent。

请执行以下操作：

1. 调用 Agent 工具，参数如下：

subagent_type: "{soul_name}"
description: "{task_short} — {soul_name}视角"
prompt: 见下方「魂 agent prompt」部分

2. 等待 agent 完成分析

3. 确认输出文件已写入 {output_path}，并简要报告 agent 已完成

---

## 魂 agent prompt（直接复制给 Agent 的 prompt 参数）

{agent_prompt}"""

# 魂 agent 收到的 prompt（通过 Agent() 的 prompt 参数传入，summon_prompt 由 agent 系统自动注入）
AGENT_PROMPT_TEMPLATE = """{task_description}

## 时代背景

你被召唤到{year}年的中国。此时：
{era_context}

你的分析对象生活在此时此地。请在分析中注意你自身时代的局限——你可能在用过去的眼光看一个你从未亲身经历的世界。

## 输出要求

请将你的完整分析结果写入 {output_path}。这将用于后续的辩证综合。

---
本魂基于{refined_at}收魂素材炼化，素材来源包括多引擎搜索和公开文献。这不是{name}本人——这是基于其公开文本的 AI 模拟。在用它做高利害决策前，请交叉验证。"""

ERA_CONTEXT_TEMPLATE = """你被召唤到{year}年的中国。此时：
{context}

你的分析对象生活在此时此地。请在分析中注意你自身时代的局限——你可能在用过去的眼光看一个你从未亲身经历的世界。"""


def load_soul(soul_name: str) -> dict:
    """读取魂 YAML 文件，返回关键字段"""
    path = os.path.join(SOULS_DIR, f"{soul_name}.yaml")
    if not os.path.exists(path):
        print(f"错误：魂档案不存在 {path}", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        data = yaml.safe_load(f)
    return data


def generate_era_lines(era_context: str = "") -> str:
    """生成时代背景行"""
    lines = [
        "- 互联网平台（微博、抖音、小红书、微信）是主要的公共话语空间",
        "- 算法推荐以互动率为核心指标，争议性内容获得不成比例的曝光",
    ]
    if era_context:
        lines.append(f"- {era_context}")
    return "\n".join(lines)


def build_agent_prompt(task: str, soul: dict, era: str, output_path: str) -> str:
    """构建传给魂 agent 的 prompt（包含任务 + 时代背景 + 输出要求）"""
    return AGENT_PROMPT_TEMPLATE.format(
        task_description=task,
        year="2026",
        era_context=era,
        output_path=output_path,
        refined_at=soul.get("refined_at", "未知日期"),
        name=soul["name"],
    )


def build_coordinator_prompt(task: str, soul: dict, era: str, output_path: str) -> str:
    """构建传给 cmux pane 的调度 prompt（让 CLI 调用 Agent）"""
    agent_prompt = build_agent_prompt(task, soul, era, output_path)
    # 转义 agent_prompt 中的特殊字符，使其可以嵌套在 Python 字符串中
    # 实际上不需要——这是传给 CLI 的文本，CLI 会自己解析
    task_short = task[:40] + ("..." if len(task) > 40 else "")
    return COORDINATOR_TEMPLATE.format(
        soul_name=soul["name"],
        task_short=task_short,
        agent_prompt=agent_prompt,
        output_path=output_path,
    )


def plan_conference(task: str, soul_names: list[str], era_context: str = "", task_slug: str = "") -> dict:
    """合议模式：多魂并行分析"""
    slug = task_slug or slugify(task)
    era = generate_era_lines(era_context)
    assignments = []
    tab_names = []
    output_paths = []

    for name in soul_names:
        soul = load_soul(name)
        out_path = f"/tmp/sb-{slug}/{name}.md"
        output_paths.append(out_path)
        prompt = build_coordinator_prompt(task, soul, era, out_path)
        assignments.append(prompt)
        tab_names.append(f"{soul['grade']} {name}")

    return {
        "mode": "合议",
        "workspace_name": f"合议: {slug}",
        "task_slug": slug,
        "cli": "claude",
        "count": len(soul_names),
        "assignments": assignments,
        "tab_names": tab_names,
        "output_paths": output_paths,
        "status": {
            "模式": "合议",
            "参与魂": ", ".join(soul_names),
            "阶段": "调度魂 agent 中",
        },
        "progress_label": "合议进度",
    }


def plan_debate(task: str, soul_names: list[str], era_context: str = "", task_slug: str = "") -> dict:
    """辩论模式：两魂对立"""
    if len(soul_names) != 2:
        print("错误：辩论模式需要恰好 2 个魂", file=sys.stderr)
        sys.exit(1)

    slug = task_slug or slugify(task)
    era = generate_era_lines(era_context)
    assignments = []
    tab_names = []
    output_paths = []

    # 正方
    soul_a = load_soul(soul_names[0])
    out_a = f"/tmp/sb-{slug}/{soul_names[0]}-正方.md"
    output_paths.append(out_a)
    task_a = (
        f"## 辩论议题\n{task}\n\n"
        f"你的立场：**正方**。请提出支持该立场的核心论点，并预见反方可能的反驳。"
    )
    prompt_a = build_coordinator_prompt(task_a, soul_a, era, out_a)
    assignments.append(prompt_a)
    tab_names.append(f"正方 {soul_names[0]}")

    # 反方
    soul_b = load_soul(soul_names[1])
    out_b = f"/tmp/sb-{slug}/{soul_names[1]}-反方.md"
    output_paths.append(out_b)
    task_b = (
        f"## 辩论议题\n{task}\n\n"
        f"你的立场：**反方**。请反驳正方论点，并提出替代方案。"
    )
    prompt_b = build_coordinator_prompt(task_b, soul_b, era, out_b)
    assignments.append(prompt_b)
    tab_names.append(f"反方 {soul_names[1]}")

    return {
        "mode": "辩论",
        "workspace_name": f"辩论: {slug}",
        "task_slug": slug,
        "cli": "claude",
        "count": 2,
        "assignments": assignments,
        "tab_names": tab_names,
        "output_paths": output_paths,
        "status": {
            "模式": "辩论",
            "正方": soul_names[0],
            "反方": soul_names[1],
            "阶段": "立论中",
        },
        "progress_label": "辩论进度",
    }


def plan_relay(task: str, soul_names: list[str], era_context: str = "", task_slug: str = "") -> dict:
    """接力模式：按序串联，前魂输出为后魂输入"""
    slug = task_slug or slugify(task)
    era = generate_era_lines(era_context)
    assignments = []
    tab_names = []
    output_paths = []

    for i, name in enumerate(soul_names):
        soul = load_soul(name)
        out_path = f"/tmp/sb-{slug}/{name}-第{i+1}棒.md"
        output_paths.append(out_path)

        if i == 0:
            task_i = f"## 接力第 1 棒\n\n你是第一棒。请独立分析以下任务，输出完整的分析结果。\n\n{task}"
        else:
            task_i = (
                f"## 接力第 {i+1} 棒\n\n"
                f"上一棒（{soul_names[i-1]}）的输出在 {output_paths[i-1]}。"
                f"请 Read 该文件，然后基于上一棒的分析进行深化或转向。\n\n"
                f"原始任务：{task}"
            )

        prompt = build_coordinator_prompt(task_i, soul, era, out_path)
        assignments.append(prompt)
        tab_names.append(f"第{i+1}棒 {name}")

    return {
        "mode": "接力",
        "workspace_name": f"接力: {slug}",
        "task_slug": slug,
        "cli": "claude",
        "count": len(soul_names),
        "assignments": assignments,
        "tab_names": tab_names,
        "output_paths": output_paths,
        "status": {
            "模式": "接力",
            "顺序": " → ".join(soul_names),
            "阶段": f"第1棒 {soul_names[0]} 启动中",
        },
        "progress_label": "接力进度",
    }


def slugify(text: str) -> str:
    """将任务描述转为文件系统友好的 slug"""
    slug = re.sub(r'[^\w\s-]', '', text)
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')[:40] or "task"


def main():
    parser = argparse.ArgumentParser(description="cmux × 万魂幡 编排计划生成器")
    parser.add_argument("--task", required=True, help="任务描述（传给魂 agent）")
    parser.add_argument("--souls", required=True, help="魂名列表，逗号分隔（如 费曼,鲁迅）")
    parser.add_argument(
        "--mode",
        choices=["conference", "debate", "relay"],
        default="conference",
        help="附体模式：conference(合议) / debate(辩论) / relay(接力)",
    )
    parser.add_argument("--task-slug", default="", help="任务标识符（用于文件路径，如 ai-education）")
    parser.add_argument("--era", default="", help="时代背景补充说明")
    parser.add_argument("-o", "--output", help="输出 JSON 文件路径（默认 stdout）")

    args = parser.parse_args()
    soul_names = [s.strip() for s in args.souls.split(",")]

    slug = args.task_slug or slugify(args.task)

    if args.mode == "conference":
        plan = plan_conference(args.task, soul_names, args.era, slug)
    elif args.mode == "debate":
        plan = plan_debate(args.task, soul_names, args.era, slug)
    elif args.mode == "relay":
        plan = plan_relay(args.task, soul_names, args.era, slug)

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
