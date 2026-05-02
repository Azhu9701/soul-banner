#!/usr/bin/env python3
"""从 soul YAML 自动生成/更新 Claude Code agent 文件。

用法:
    # 单个魂
    python3 scripts/sync-agent.py souls/海绵宝宝.yaml

    # 全部魂（从 registry.yaml 读取列表）
    python3 scripts/sync-agent.py --all

    # 预览（不写入）
    python3 scripts/sync-agent.py --all --dry-run

    # 指定输出目录
    python3 scripts/sync-agent.py souls/海绵宝宝.yaml -o ~/.claude/agents/

映射规则:
    soul YAML                          → agent frontmatter
    ─────────────────────────────────────────────────────
    name                               → name
    grade + domain + title + trigger   → description
    grade                              → color (金=yellow, 银=gray, 紫=purple, 蓝=blue, 绿=green, 白=white)
    summon_prompt                      → agent body (核心人格)
"""

import argparse
import sys
from pathlib import Path

import yaml

AGENTS_DIR = Path.home() / ".claude" / "agents"
DEFAULT_TOOLS = "Read, Bash, Glob, Grep, Write, WebFetch"
MODEL = "sonnet"

GRADE_COLOR = {
    "金": "yellow",
    "银": "gray",
    "紫": "purple",
    "蓝": "blue",
    "绿": "green",
    "白": "white",
}

GRADE_EMOJI = {
    "金": "\U0001f7e1",  # 🟡
    "银": "\U0001f948",  # 🥈
    "紫": "\U0001f7e3",  # 🟣
    "蓝": "\U0001f535",  # 🔵
    "绿": "\U0001f7e2",  # 🟢
    "白": "⚪",       # ⚪
}


def build_description(soul: dict) -> str:
    """生成 agent description 字段."""
    grade = soul.get("grade", "?")
    emoji = GRADE_EMOJI.get(grade, "")
    domains = soul.get("domain", [])[:5]  # 最多取5个领域
    domain_str = ", ".join(domains)
    title = soul.get("title", "")
    trigger = soul.get("trigger_keywords_summary", "")

    desc = f"{emoji} {grade}魂 | {domain_str}"
    if title:
        desc += f"。{title}"
    if trigger:
        desc += f"。用于{trigger}等任务"
    return desc


def generate_agent(name: str, soul: dict) -> str:
    """生成完整的 agent .md 内容."""
    description = build_description(soul)
    color = GRADE_COLOR.get(soul.get("grade", ""), "gray")
    summon_prompt = soul.get("summon_prompt", "")

    # 清理 summon_prompt 中可能存在的异常缩进
    summon_prompt = summon_prompt.strip()

    frontmatter = f"""---
name: "{name}"
description: "{description}"
tools: {DEFAULT_TOOLS}
model: {MODEL}
color: {color}
memory: project
---

{summon_prompt}
"""
    return frontmatter


def sync_one(soul_path: Path, agents_dir: Path, dry_run: bool = False) -> tuple[str, int, bool]:
    """同步单个魂 YAML → agent 文件。返回 (魂名, 原行数, 是否已存在)。"""
    with open(soul_path) as f:
        soul = yaml.safe_load(f)

    name = soul.get("name", soul_path.stem)
    content = generate_agent(name, soul)

    agent_path = agents_dir / f"{name}.md"
    existed = agent_path.exists()

    if dry_run:
        print(f"[DRY RUN] {'更新' if existed else '创建'} {agent_path} ({len(content)} chars)")
    else:
        agents_dir.mkdir(parents=True, exist_ok=True)
        with open(agent_path, "w") as f:
            f.write(content)

    return name, len(content), existed


def sync_all(registry_path: Path, agents_dir: Path, dry_run: bool = False):
    """从 registry.yaml 读取魂列表，逐个同步."""
    with open(registry_path) as f:
        registry = yaml.safe_load(f)

    souls_dir = registry_path.parent / "souls"
    results = []

    for soul_entry in registry.get("魂魄", []):
        name = soul_entry["name"]
        soul_path = souls_dir / f"{name}.yaml"
        if not soul_path.exists():
            print(f"⚠  跳过 {name}: soul YAML 不存在 ({soul_path})")
            continue
        r = sync_one(soul_path, agents_dir, dry_run)
        results.append(r)

    created = sum(1 for _, _, existed in results if not existed)
    updated = sum(1 for _, _, existed in results if existed)

    if dry_run:
        print(f"\n[DRY RUN] 共 {len(results)} 魂: {created} 新建, {updated} 更新")
    else:
        print(f"\n同步完成: {len(results)} 魂 → {agents_dir}")
        print(f"  新建: {created}, 更新: {updated}")

        # 列出 agents_dir 中孤立的 agent 文件（无对应 soul YAML）
        soul_names = {s["name"] for s in registry.get("魂魄", [])}
        for agent_file in sorted(agents_dir.glob("*.md")):
            agent_name = agent_file.stem
            if agent_name not in soul_names:
                # 排除系统 agent（审查官、辩证综合官等）
                if agent_name not in ("列宁审查官", "辩证综合官"):
                    print(f"  ⚠  孤立 agent: {agent_file}（无对应 soul YAML）")


def main():
    parser = argparse.ArgumentParser(description="从 soul YAML 同步 agent 文件")
    parser.add_argument("soul", nargs="?", help="soul YAML 文件路径")
    parser.add_argument("--all", action="store_true", help="同步全部魂魄")
    parser.add_argument("-o", "--output", default=str(AGENTS_DIR), help=f"agent 输出目录 (默认 {AGENTS_DIR})")
    parser.add_argument("-r", "--registry", default=None, help="registry.yaml 路径 (默认自动查找)")
    parser.add_argument("--dry-run", action="store_true", help="预览，不写入")
    args = parser.parse_args()

    agents_dir = Path(args.output)

    if args.all:
        if args.registry:
            registry_path = Path(args.registry)
        else:
            # 自动查找：脚本同级目录的 registry.yaml
            registry_path = Path(__file__).resolve().parent.parent / "registry.yaml"
        if not registry_path.exists():
            print(f"错误: registry.yaml 不存在 ({registry_path})")
            sys.exit(1)
        sync_all(registry_path, agents_dir, args.dry_run)
    elif args.soul:
        sync_one(Path(args.soul), agents_dir, args.dry_run)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
