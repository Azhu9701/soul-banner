#!/usr/bin/env python3
"""cmux × 万魂幡 编排计划生成器 v3

架构：cmux pane 用 tail -f 做纯显示器（零 token），魂分析由主 agent 直接 spawn。

用法:
  python3 scripts/cmux-plan.py --task "任务描述" --task-slug "ai-education" \
    --souls 费曼,鲁迅 --mode conference --era "..." -o /tmp/cmux-plan.json

输出 JSON 包含：
  - display_commands: 每个 pane 的 tail -f 命令
  - agent_tasks: 主 agent 需要 spawn 的 {subagent_type, prompt} 列表
  - output_paths: 输出文件路径，供辩证综合官读取
"""

import argparse
import json
import os
import re
import sys
import yaml

SOULS_DIR = os.path.join(os.path.dirname(__file__), "..", "souls")

AGENT_PROMPT_TEMPLATE = """{task_description}

## 时代背景

你被召唤到{year}年的中国。此时：
{era_context}

你的分析对象生活在此时此地。请在分析中注意你自身时代的局限——你可能在用过去的眼光看一个你从未亲身经历的世界。

## 输出要求

请将你的完整分析结果写入 {output_path}。这将用于后续的辩证综合。

---
本魂基于{refined_at}收魂素材炼化，素材来源包括多引擎搜索和公开文献。这不是{name}本人——这是基于其公开文本的 AI 模拟。在用它做高利害决策前，请交叉验证。"""


def load_soul(soul_name: str) -> dict:
    path = os.path.join(SOULS_DIR, f"{soul_name}.yaml")
    if not os.path.exists(path):
        print(f"错误：魂档案不存在 {path}", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        return yaml.safe_load(f)


def build_era_lines(era_extra: str = "") -> str:
    lines = [
        "- 互联网平台（微博、抖音、小红书、微信）是主要的公共话语空间",
        "- 算法推荐以互动率为核心指标，争议性内容获得不成比例的曝光",
    ]
    if era_extra:
        lines.append(f"- {era_extra}")
    return "\n".join(lines)


def build_agent_prompt(task: str, soul: dict, output_path: str, era_lines: str) -> str:
    return AGENT_PROMPT_TEMPLATE.format(
        task_description=task,
        year="2026",
        era_context=era_lines,
        output_path=output_path,
        refined_at=soul.get("refined_at", "未知日期"),
        name=soul["name"],
    )


def slugify(text: str) -> str:
    slug = re.sub(r'[^\w\s-]', '', text)
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')[:40] or "task"


def plan_common(
    mode: str,
    task: str,
    soul_names: list[str],
    era_extra: str,
    slug: str,
    soul_label: callable,
) -> dict:
    """生成编排计划：display_commands + agent_tasks + output_paths"""
    era = build_era_lines(era_extra)
    output_paths = []
    agent_tasks = []
    display_commands = []
    tab_names = []

    for name in soul_names:
        soul = load_soul(name)
        out_path = f"/tmp/sb-{slug}/{name}.md"
        output_paths.append(out_path)

        label = soul_label(name, soul)
        display_commands.append(f"tail -f {out_path}")
        tab_names.append(label)

        agent_tasks.append({
            "subagent_type": name,
            "output_file": out_path,
            "soul_grade": soul.get("grade", "?"),
            "refined_at": soul.get("refined_at", "未知日期"),
            "prompt": build_agent_prompt(task, soul, out_path, era),
        })

    return {
        "mode": mode,
        "task_slug": slug,
        "workspace_name": f"{mode}: {slug}",
        "temp_dir": f"/tmp/sb-{slug}",
        "display_commands": display_commands,
        "tab_names": tab_names,
        "agent_tasks": agent_tasks,
        "output_paths": output_paths,
        "status": {
            "模式": mode,
            "参与魂": ", ".join(soul_names),
            "阶段": "创建显示面板中",
        },
        "progress_label": f"{mode}进度",
    }


def plan_conference(task: str, soul_names: list[str], era_extra: str, slug: str) -> dict:
    return plan_common(
        "合议", task, soul_names, era_extra, slug,
        lambda name, soul: f"{soul.get('grade', '?')} {name}",
    )


def plan_debate(task: str, soul_names: list[str], era_extra: str, slug: str) -> dict:
    if len(soul_names) != 2:
        print("错误：辩论模式需要恰好 2 个魂", file=sys.stderr)
        sys.exit(1)

    plan = plan_common("辩论", task, soul_names, era_extra, slug, lambda name, soul: "")
    # 覆盖 tab 名称为正方/反方
    plan["tab_names"] = [f"正方 {soul_names[0]}", f"反方 {soul_names[1]}"]

    # 为辩论修改 agent prompt（加入立场）
    era = build_era_lines(era_extra)
    # 正方
    pos_path = plan["agent_tasks"][0]["output_file"]
    plan["display_commands"][0] = f"tail -f {pos_path}"
    plan["agent_tasks"][0]["prompt"] = build_agent_prompt(
        f"## 辩论议题\n{task}\n\n你的立场：**正方**。请提出支持该立场的核心论点，并预见反方可能的反驳。",
        load_soul(soul_names[0]), pos_path, era,
    )
    # 反方
    neg_path = plan["agent_tasks"][1]["output_file"]
    plan["display_commands"][1] = f"tail -f {neg_path}"
    plan["agent_tasks"][1]["prompt"] = build_agent_prompt(
        f"## 辩论议题\n{task}\n\n你的立场：**反方**。请反驳正方论点，并提出替代方案。",
        load_soul(soul_names[1]), neg_path, era,
    )

    plan["status"]["正方"] = soul_names[0]
    plan["status"]["反方"] = soul_names[1]
    return plan


def plan_relay(task: str, soul_names: list[str], era_extra: str, slug: str) -> dict:
    plan = plan_common("接力", task, soul_names, era_extra, slug, lambda name, soul: "")
    plan["tab_names"] = [f"第{i+1}棒 {name}" for i, name in enumerate(soul_names)]

    era = build_era_lines(era_extra)
    for i, name in enumerate(soul_names):
        out = plan["agent_tasks"][i]["output_file"]
        if i == 0:
            task_i = f"## 接力第 1 棒\n\n你是第一棒。请独立分析以下任务，输出完整的分析结果。\n\n{task}"
        else:
            prev_file = plan["agent_tasks"][i - 1]["output_file"]
            task_i = (
                f"## 接力第 {i+1} 棒\n\n"
                f"上一棒（{soul_names[i-1]}）的输出在 {prev_file}。"
                f"请 Read 该文件，然后基于上一棒的分析进行深化或转向。\n\n"
                f"原始任务：{task}"
            )
        plan["agent_tasks"][i]["prompt"] = build_agent_prompt(
            task_i, load_soul(name), out, era,
        )

    plan["status"]["顺序"] = " → ".join(soul_names)
    plan["status"]["阶段"] = f"第1棒 {soul_names[0]} 启动中"
    return plan


def main():
    parser = argparse.ArgumentParser(description="cmux × 万魂幡 编排计划生成器 v3 (tail -f 显示器)")
    parser.add_argument("--task", required=True, help="任务描述")
    parser.add_argument("--souls", required=True, help="魂名列表，逗号分隔")
    parser.add_argument("--mode", choices=["conference", "debate", "relay"], default="conference")
    parser.add_argument("--task-slug", default="", help="任务标识符（文件路径用）")
    parser.add_argument("--era", default="", help="时代背景补充说明")
    parser.add_argument("-o", "--output", help="输出 JSON 路径（默认 stdout）")

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
