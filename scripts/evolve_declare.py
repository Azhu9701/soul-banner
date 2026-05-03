#!/usr/bin/env python3
"""self_declare 演化机制 — 附体后魂可以提出修改自己的轻量声明。

用法：
  python3 scripts/evolve_declare.py propose <魂名> --task "任务简述" --text "新声明文本" --reason "为什么改"
  python3 scripts/evolve_declare.py review <魂名>                     # 检查是否有待审修改
  python3 scripts/evolve_declare.py accept <魂名> --version N          # 幡主批准→正式更新
  python3 scripts/evolve_declare.py reject <魂名> --version N --reason "..."  # 幡主驳回
"""

import json, re, sys, os
from pathlib import Path
from datetime import datetime

SKILL_DIR = Path(__file__).parent.parent
SOULS_DIR = SKILL_DIR / "souls"


def load_soul(name):
    path = SOULS_DIR / f"{name}.yaml"
    if not path.exists():
        return None, None
    return path, path.read_text()


def save_soul(path, content):
    path.write_text(content)


def get_history(content):
    """从 YAML 中提取 declare_history 列表"""
    m = re.search(r"declare_history:\s*\n(\s*-.*(?:\n\s+.*?)*)", content, re.DOTALL)
    if not m:
        return []
    # Crude YAML list parsing
    history_raw = m.group(1)
    entries = []
    current = {}
    for line in history_raw.split('\n'):
        line = line.strip()
        if line.startswith('- version:'):
            if current:
                entries.append(current)
            current = {'version': int(re.search(r'version:\s*(\d+)', line).group(1))}
        elif line.startswith('proposed_at:'):
            current['proposed_at'] = line.split(':', 1)[1].strip().strip('"').strip("'")
        elif line.startswith('proposed_text:'):
            current['proposed_text'] = line.split(':', 1)[1].strip().strip('"').strip("'")
        elif line.startswith('trigger:'):
            current['trigger'] = line.split(':', 1)[1].strip().strip('"').strip("'")
        elif line.startswith('reason:'):
            current['reason'] = line.split(':', 1)[1].strip().strip('"').strip("'")
        elif line.startswith('accepted:'):
            val = line.split(':', 1)[1].strip()
            current['accepted'] = val.lower() in ('true', 'yes', '1')
    if current:
        entries.append(current)
    return entries


def propose(name, task, text, reason):
    path, content = load_soul(name)
    if not path:
        print(f"❌ 魂不存在: {name}")
        return 1

    history = get_history(content)
    next_ver = max([h.get('version', 0) for h in history], default=0) + 1
    today = datetime.now().strftime("%Y-%m-%d")

    entry = {
        "version": next_ver,
        "proposed_at": today,
        "proposed_text": text,
        "trigger": task,
        "reason": reason,
        "accepted": False
    }

    # Check similar pending proposals
    pending_similar = [h for h in history if not h.get('accepted') and h.get('trigger') == task]
    pending_count = len([h for h in history if not h.get('accepted')])

    # Update or insert declare_history
    if "declare_history:" in content:
        # Append to existing list
        content = content.rstrip()
        new_entry_yaml = (
            f"\n  - version: {next_ver}\n"
            f"    proposed_at: \"{today}\"\n"
            f"    proposed_text: \"{text}\"\n"
            f"    trigger: \"{task}\"\n"
            f"    reason: \"{reason}\"\n"
            f"    accepted: false"
        )
        content = content + new_entry_yaml
    else:
        # Insert before summon_prompt or at end
        history_block = (
            f"\ndeclare_history:\n"
            f"  - version: {next_ver}\n"
            f"    proposed_at: \"{today}\"\n"
            f"    proposed_text: \"{text}\"\n"
            f"    trigger: \"{task}\"\n"
            f"    reason: \"{reason}\"\n"
            f"    accepted: false"
        )
        if "\nsummon_prompt:" in content:
            content = content.replace("\nsummon_prompt:", f"{history_block}\nsummon_prompt:")
        else:
            content = content.rstrip() + history_block + "\n"

    save_soul(path, content)

    # Flag for review if threshold reached
    new_pending = pending_count + 1
    if new_pending >= 3:
        print(f"✅ {name} v{next_ver} 已记录（{new_pending}次待审 → ⚠️ 需幡主审查）")
    elif pending_similar:
        print(f"✅ {name} v{next_ver} 已记录（同类提案已有 {len(pending_similar)} 次）")
    else:
        print(f"✅ {name} v{next_ver} 已记录")
    return 0


def review(name):
    _, content = load_soul(name)
    if not content:
        print(f"❌ 魂不存在: {name}")
        return 1
    history = get_history(content)
    pending = [h for h in history if not h.get('accepted')]
    if not pending:
        print(f"✅ {name}: 无待审修改")
        return 0
    print(f"⚠️  {name}: {len(pending)} 次待审")
    for h in pending:
        print(f"  v{h['version']}: {h['trigger']} — {h['proposed_text'][:60]}...")
    return len(pending)


def accept(name, version):
    path, content = load_soul(name)
    if not path:
        print(f"❌ 魂不存在: {name}")
        return 1
    history = get_history(content)
    target = None
    for h in history:
        if h.get('version') == version:
            target = h
            break
    if not target:
        print(f"❌ v{version} 不存在")
        return 1

    # Update self_declare
    new_declare = json.dumps(target['proposed_text'], ensure_ascii=False)
    content = re.sub(
        r'self_declare:\s*"((?:[^"\\]|\\.)*)"',
        f'self_declare: {new_declare}',
        content
    )

    # Mark accepted in history
    content = content.replace(
        f"version: {version}\n    proposed_at:",
        f"version: {version}\n    accepted: true\n    accepted_at: \"{datetime.now().strftime('%Y-%m-%d')}\"\n    proposed_at:"
    )

    save_soul(path, content)
    print(f"✅ {name} self_declare 已更新到 v{version}: {target['proposed_text'][:60]}...")

    # Clean up old history (keep last 5)
    if history:
        all_versions = sorted(set(h['version'] for h in history), reverse=True)
        if len(all_versions) > 5:
            print(f"  ℹ️  历史版本超过5个，建议手动清理")
    return 0


def main():
    args = sys.argv[1:]
    if len(args) < 1:
        print("用法: evolve_declare.py <propose|review|accept> ...")
        sys.exit(1)

    cmd = args[0]
    if cmd == "propose":
        name = args[1]
        task = text = reason = ""
        i = 2
        while i < len(args):
            if args[i] == "--task" and i+1 < len(args):
                task = args[i+1]; i += 2
            elif args[i] == "--text" and i+1 < len(args):
                text = args[i+1]; i += 2
            elif args[i] == "--reason" and i+1 < len(args):
                reason = args[i+1]; i += 2
            else:
                i += 1
        if not task or not text:
            print("❌ 需要 --task 和 --text")
            sys.exit(1)
        sys.exit(propose(name, task, text, reason))

    elif cmd == "review":
        sys.exit(review(args[1]) if len(args) > 1 else 1)

    elif cmd == "accept":
        name = args[1]
        ver = int(args[3]) if len(args) > 3 and args[2] == "--version" else 0
        if not ver:
            print("❌ 需要 --version N")
            sys.exit(1)
        sys.exit(accept(name, ver))

    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
