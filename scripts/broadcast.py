#!/usr/bin/env python3
"""广播机制 v0.2 — 互见广播。魂之间在自选阶段就能看到彼此的声明和盲区-强项关系。

任务来了不跑 match.py，广播给所有魂。魂自己判断该不该上——但同时也看到别的魂在说什么。
输出格式：含互见交叉表 + 互见指令，供主 agent 做轻量判断后执行挑战轮。
"""

import json, re, os, sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
SOULS_DIR = SKILL_DIR / "souls"
ISMISM_PATH = SKILL_DIR / "ismism-data.json"

def load_declares():
    """从 soul YAML 中提取所有魂的 self_declare + ismism 编码"""
    declares = {}
    for fp in sorted(SOULS_DIR.glob("*.yaml")):
        name = fp.stem
        raw = fp.read_text()
        m = re.search(r"self_declare:\s*\"((?:[^\"\\]|\\.)*)\"", raw)
        declare = m.group(1) if m else ""
        m2 = re.search(r'ismism:\s*\n\s+code:\s*"?([^"\n]+)"?', raw)
        code = m2.group(1).strip() if m2 else "?"
        declares[name] = {"declare": declare, "code": code}
    return declares

def load_ismism():
    """加载 ismism-data.json 获取 compat/incompat/blindspots"""
    if ISMISM_PATH.exists():
        with open(ISMISM_PATH) as f:
            return json.load(f)
    return {}

def format_broadcast(task: str, declares: dict[str, dict], ismism: dict[str, dict]) -> str:
    """生成互见广播 prompt — v0.2 新增盲区-强项交叉表和互见指令"""
    lines = ["## 广播：任务自选（互见模式 v0.2）", "", f"**任务**: {task}", "", "---", ""]
    lines.append("### 魂的轻量自我声明（按场域分组，含互见交叉表）")
    lines.append("")

    lines.append("以下每个魂只给出了 self_declare + 盲区/互补标注。请基于这些声明做初步自选判断（[Y/N] + 主力/补位）。")
    lines.append("**判断时请注意互见交叉表**——同场域内魂A的盲区是否恰好被魂B覆盖？跨场域互补关系是否提示了该补的魂？")
    lines.append("")

    # Group by ismism first digit
    groups = {"1": [], "2": [], "3": [], "4": []}
    for name, info in declares.items():
        code = info["code"]
        first_digit = code[0] if code else "?"
        if first_digit in groups:
            groups[first_digit].append(name)
        else:
            groups.setdefault("?", []).append(name)

    field_names = {"1": "1字头·形而下学", "2": "2字头·形而上学",
                   "3": "3字头·观念论", "4": "4字头·实践"}

    for digit in ["1", "2", "3", "4"]:
        souls = sorted(groups.get(digit, []))
        if not souls:
            continue

        lines.append(f"#### {field_names[digit]}（{len(souls)}魂）")
        lines.append("")

        # Individual self_declares
        for name in souls:
            info = declares[name]
            ism = ismism.get(name, {})
            bl = ", ".join(ism.get("blindspots", [])[:3]) or "未标注"
            lines.append(f"**{name}** `{info['code']}` [{ism.get('match_quality','?')}] 盲区: {bl}")
            lines.append(f"  {info['declare']}")
            lines.append("")

        # Mutual visibility cross-reference for this field group
        lines.append("**场域内互见参考：**")
        lines.append("")
        found_any = False
        for i, name_a in enumerate(souls):
            ism_a = ismism.get(name_a, {})
            bl_a = set(ism_a.get("blindspots", []))
            if not bl_a:
                continue
            complements = []
            for name_b in souls:
                if name_a == name_b:
                    continue
                ism_b = ismism.get(name_b, {})
                # Check if B's self_declare hints at covering A's blindspots
                # Simple heuristic: if B's compat overlaps with A's
                bl_a_str = ", ".join(bl_a)
                declare_b = declares.get(name_b, {}).get("declare", "")
                for bl in list(bl_a)[:2]:
                    if bl in declare_b:
                        complements.append(f"{name_b}(可补'{bl}')")
                        break
            if complements:
                found_any = True
                lines.append(f"- **{name_a}** 盲区 → {', '.join(complements)}")

        if not found_any:
            lines.append("- （此场域内未检测到明显的盲区-强项交叉）")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Cross-field complementarity hints
    lines.append("### 跨场域互补参考")
    lines.append("")
    lines.append("以下魂的 self_declare 中明确声明了与其他魂的互补关系：")
    lines.append("")
    for name, info in declares.items():
        declare = info["declare"]
        # Look for "互补：XXX" pattern in self_declare
        m = re.search(r"互补[：:](.+)", declare)
        if m:
            complement_str = m.group(1).strip()
            lines.append(f"- **{name}** `{info['code']}` → 互补：{complement_str}")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("### 自选判断 + 互见指令")
    lines.append("")
    lines.append("1. **初步自选**：基于每个魂的 self_declare 做 [Y/N/Maybe] + 主力/补位 判断")
    lines.append("2. **互见修正**：检查——自选为Y的魂之间，盲区是否被其他Y魂覆盖？如果有未被覆盖的盲区，是否有Maybe或N的魂恰好能补？")
    lines.append("3. **形成初步合议组**：主力1-2 + 补位1-2 → 不超过4魂")
    lines.append("4. **互见挑战轮**（见下节）— 将初步合议组广播给全部20魂，收集异议")
    lines.append("5. **幡主审查** — 未明子审查合议组+异议 → 最终批准")
    lines.append("")

    lines.append("### 互见挑战轮指令（在初步合议组形成后执行）")
    lines.append("")
    lines.append("将初步合议组名单 + 每个魂的 self_declare 发送给**全部 20 魂的轻量 spawn**：")
    lines.append("")
    lines.append("```")
    lines.append("轻量 spawn prompt:")
    lines.append("当前任务：{任务描述}")
    lines.append("初步合议组：{魂A}({code}, self_declare摘要) / {魂B} / {魂C} / {魂D}")
    lines.append("你的 self_declare: {你自己的声明}")
    lines.append("请回答（不超过3句话）：")
    lines.append("① 合议组是否有遗漏？你或某个魂是否该上但没上？")
    lines.append("② 合议组中是否有魂的盲区需要补充？")
    lines.append("③ 直接回答'无异议'即可——不需要为存在而存在")
    lines.append("```")
    lines.append("")
    lines.append("**回退条件**：异议魂>5个、任何魂>200字异议、幡主判定互见轮增加噪音 → 回退到单轮模式。")

    return "\n".join(lines)

def main():
    task = sys.argv[1] if len(sys.argv) > 1 else input("任务描述: ")
    declares = load_declares()
    ismism = load_ismism()
    print(format_broadcast(task, declares, ismism))
    print(f"\n> 以上 {len(declares)} 魂已就绪。互见模式启动。")

if __name__ == "__main__":
    main()
