#!/usr/bin/env python3
"""cmux × 万民幡 编排计划生成器 v4

架构：cmux_launch_agents 启动 N 个 Claude CLI，每个 CLI 只做一件事 ——
用 Agent(subagent_type="{魂名}") 召唤魂 agent。~500 token/pane 调度开销。

用法:
  python3 scripts/cmux-plan.py --task "任务" --task-slug "slug" \
    --souls 费曼,鲁迅 --mode conference --era "..." -o /tmp/plan.json
"""

import argparse
import json
import os
import re
import sys
import yaml

SOULS_DIR = os.path.join(os.path.dirname(__file__), "..", "souls")

# 魂 agent 收到的 prompt（通过 Agent() 的 prompt 参数传入）
AGENT_PROMPT = """{task}

## 时代背景

你被召唤到2026年的中国。此时：
{era}

你的分析对象生活在此时此地。请在分析中注意你自身时代的局限。

## 输出要求

请将你的完整分析结果写入 {output_file}。这将用于后续的辩证综合。

---
本魂基于{refined_at}收魂素材炼化。这不是{name}本人——AI 模拟。"""

# cmux pane 收到的调度指令（极简，~200 token）
PANE_PROMPT = """你的唯一任务：使用 Agent 工具调用魂 agent，不要自己分析。

请使用以下参数调用 Agent 工具：
  subagent_type: "{soul_name}"
  description: "{task_short}"
  prompt: 见下方「魂 agent prompt」部分

等待 agent 完成，确认 {output_file} 已写入，报告「{soul_name} 完成」即可。

---

## 魂 agent prompt

{agent_prompt}"""

def load_soul(name: str) -> dict:
    path = os.path.join(SOULS_DIR, f"{name}.yaml")
    if not os.path.exists(path):
        print(f"错误：魂档案不存在 {path}", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        return yaml.safe_load(f)

def era_lines(extra: str) -> str:
    lines = [
        "- 互联网平台（微博、抖音、小红书、微信）是主要的公共话语空间",
        "- 算法推荐以互动率为核心指标，争议性内容获得不成比例的曝光",
    ]
    if extra:
        lines.append(f"- {extra}")
    return "\n".join(lines)

def build_agent_prompt(task: str, soul: dict, output_file: str, era: str) -> str:
    return AGENT_PROMPT.format(
        task=task,
        era=era,
        output_file=output_file,
        refined_at=soul.get("refined_at", "未知"),
        name=soul["name"],
    )

def build_pane_prompt(soul_name: str, agent_prompt: str, output_file: str, task: str) -> str:
    return PANE_PROMPT.format(
        soul_name=soul_name,
        task_short=task[:50],
        agent_prompt=agent_prompt,
        output_file=output_file,
    )

def slugify(text: str) -> str:
    s = re.sub(r'[^\w\s-]', '', text)
    s = re.sub(r'[-\s]+', '-', s)
    return s.strip('-')[:40] or "task"

def plan(mode: str, task: str, soul_names: list[str], era_extra: str, slug: str) -> dict:
    era = era_lines(era_extra)
    assignments = []
    tab_names = []
    output_paths = []

    for name in soul_names:
        soul = load_soul(name)
        out = f"/tmp/sb-{slug}/{name}.md"
        output_paths.append(out)

        agent_prompt = build_agent_prompt(task, soul, out, era)
        pane_prompt = build_pane_prompt(name, agent_prompt, out, task)
        assignments.append(pane_prompt)
        tab_names.append(f"{soul.get('grade', '?')} {name}")

    return {
        "mode": mode,
        "task_slug": slug,
        "workspace_name": f"{mode}: {slug}",
        "temp_dir": f"/tmp/sb-{slug}",
        "assignments": assignments,
        "tab_names": tab_names,
        "output_paths": output_paths,
        "status": {
            "模式": mode,
            "参与魂": ", ".join(soul_names),
            "阶段": "调度魂 agent 中",
        },
        "progress_label": f"{mode}进度",
    }

def main():
    p = argparse.ArgumentParser(description="cmux × 万民幡 v4")
    p.add_argument("--task", required=True)
    p.add_argument("--souls", required=True)
    p.add_argument("--mode", choices=["conference", "debate", "relay"], default="conference")
    p.add_argument("--task-slug", default="")
    p.add_argument("--era", default="")
    p.add_argument("-o", "--output")
    args = p.parse_args()

    souls = [s.strip() for s in args.souls.split(",")]
    slug = args.task_slug or slugify(args.task)

    result = plan(args.mode, args.task, souls, args.era, slug)
    j = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w") as f:
            f.write(j)
        print(f"→ {args.output}")
    else:
        print(j)

if __name__ == "__main__":
    main()
