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

v2.0 映射规则:
    soul YAML                          → agent frontmatter
    ─────────────────────────────────────────────────────
    name                               → name
    summon_prompt                      → agent body (核心人格)
"""

import argparse
import sys
from pathlib import Path

import yaml

AGENTS_DIR = Path.home() / ".claude" / "agents"
DEFAULT_TOOLS = "Read, Bash, Glob, Grep, Write, WebFetch"
MODEL = "sonnet"

METHODOLOGY_COLOR = {
    "可传输": "blue",
    "嵌入型": "green",
    "人格型": "purple",
}

def build_description(soul: dict) -> str:
    fd_str = ", ".join(fds) if fds else "?"
    domains = soul.get("domain", [])[:5]
    domain_str = ", ".join(domains)
    title = soul.get("title", "")

    desc = f"{fd_str} | {domain_str}"
    if title:
        desc += f"。{title}"
    if mt:
        desc += f"。方法论: {mt}"
    return desc

def generate_agent(name: str, soul: dict) -> str:
    description = build_description(soul)
    color = METHODOLOGY_COLOR.get(mt, "gray")
    summon_prompt = soul.get("summon_prompt", "").strip()

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

        soul_names = {s["name"] for s in registry.get("魂魄", [])}
        for agent_file in sorted(agents_dir.glob("*.md")):
            agent_name = agent_file.stem
            if agent_name not in soul_names:
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
