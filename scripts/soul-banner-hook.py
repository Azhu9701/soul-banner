#!/usr/bin/env python3
"""万民幡灵识层 — UserPromptSubmit Hook

三级递进匹配：
  一级：命令词精确命中（11个）
  二级：魂魄名 + 视角句式
  三级：场景关键词 >= 2 组

始终 exit 0。匹配时输出 systemMessage JSON，否则输出 {}。
"""

import json
import os
import re
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# === 一级：命令词（任一命中即触发） ===
COMMAND_WORDS = [
    "合议", "辩论", "接力", "收魂", "炼化",
    "幡中有什么魂", "幡中战绩", "散魂", "审查",
    "升级魂魄", "幡主", "学习",
]

# === 二级：魂魄名（唯一数据源：registry.yaml） ===
# 不再维护硬编码列表——registry.yaml 是魂魄名的唯一权威来源。
# 加载失败时 Level 2 跳过（不静默退化），Level 1/3 仍正常工作。

# 视角句式（regex 模式）
PERSPECTIVE_PATTERNS = [
    r"从.{0,4}视角",
    r"用.{0,4}思维",
    r"用.{0,12}(?:分析|来|解剖|批判|拆解|解读)",
    r"从.{0,4}角度",
    r"以.{0,4}立场",
    r"作为.{0,12}(?:分析|解剖|看)",
    r"让.{0,6}分析",
]

# === 三级：场景关键词组（>=2 组命中即触发） ===
SCENE_GROUPS = {
    "多视角": ["多角度", "多视角", "不同角度", "不同视角", "正反两方面", "两方面看", "多个角度"],
    "辩证综合": ["辩证综合", "辩证分析", "综合判断", "综合裁决", "辩证统一"],
    "第一性原理": ["第一性原理", "从零推导", "本质分析", "归零思考", "第一性原则"],
    "跨界决策": ["跨界决策", "战略方向", "要不要", "该不该", "两难决策", "两难选择"],
    "批判审查": ["批判性审查", "独立审查", "货物崇拜", "自欺欺人", "cargo cult"],
    "跨领域": ["跨领域", "跨学科", "多个维度", "多个层面", "多维度分析"],
}

# === 排除条件（命中则不触发） ===
EXCLUDE_PATTERNS = [
    r"(?:修复|debug|调试).{0,10}(?:bug|错误|报错|异常)",
    r"(?:写|帮我写|写个|写一个).{0,5}(?:脚本|代码|函数|程序|python|script)",
    r"(?:PPT|ppt|排版|字体|字号|加粗)",
    r"(?:辞职信|辞职邮件|感谢信|邀请函|通知)",
    r"(?:费曼学习法|费曼技巧).{0,10}(?:学|步骤|方法|怎么用)",
    r"(?:说过什么|说了什么|发过什么|推文|最新评论|最近.{0,5}动态)",
    r"(?:Excel|excel|表格|汇总|柱状图|数据透视|求和|排序)",
    r"(?:总结|概括|归纳).{0,10}(?:理论|思想|要点|核心)",
    r"(?:API|api|接口|拉取数据|存入|数据库|postgresql)",
]

def load_soul_names():
    """从 registry.yaml 动态加载魂魄名列表。失败则返回空列表——不静默退化。"""
    registry_path = os.path.join(SKILL_DIR, "registry.yaml")
    try:
        with open(registry_path) as f:
            content = f.read()
        import yaml
        data = yaml.safe_load(content)
        names = [s["name"] for s in data.get("魂魄", [])]
        if names:
            return names
        print(json.dumps({"systemMessage": "【万民幡警告】registry.yaml 中无魂魄记录"}), file=sys.stderr)
    except FileNotFoundError:
        print(json.dumps({"systemMessage": "【万民幡警告】registry.yaml 不存在，Level 2 匹配已跳过"}), file=sys.stderr)
    except Exception as e:
        print(json.dumps({"systemMessage": f"【万民幡警告】加载 registry 失败: {e}"}), file=sys.stderr)
    return []

def check_level1(prompt: str) -> str | None:
    """命令词精确命中"""
    for word in COMMAND_WORDS:
        if word in prompt:
            return f"命令词「{word}」"
    return None

def check_level2(prompt: str, soul_names: list[str]) -> str | None:
    """魂魄名 + 视角句式"""
    souls_found = [s for s in soul_names if s in prompt]
    if not souls_found:
        return None

    for pattern in PERSPECTIVE_PATTERNS:
        if re.search(pattern, prompt):
            return f"魂魄「{'、'.join(souls_found)}」+ 视角模式"

    # 多魂同时出现（>=2个）即使没有显式视角词也触发
    if len(souls_found) >= 2:
        return f"多魂魄「{'、'.join(souls_found)}」同时出现"

    return None

def check_level3(prompt: str) -> str | None:
    """场景关键词组 >= 2 组命中"""
    hit_groups = []
    for group_name, keywords in SCENE_GROUPS.items():
        if any(kw in prompt for kw in keywords):
            hit_groups.append(group_name)
    if len(hit_groups) >= 2:
        return f"场景关键词组「{'、'.join(hit_groups)}」"
    return None

def check_exclude(prompt: str) -> bool:
    """检查排除条件"""
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, prompt):
            return True
    return False

def build_system_message(match_reason: str) -> str:
    return (
        f"【万民幡自主触发】检测到匹配模式：{match_reason}。\n\n"
        "必须立即调用 Skill(soul-banner)：\n"
        "1. 本技能提供主 agent 无法自行实现的三种能力："
        "并行 spawn 独立子 agent（不同人物思维框架注入）、"
        "结构化辩证综合（找共识/找分歧/找盲区）、幡主审查防教条\n"
        "2. 主 agent 禁止自行模拟多视角——实验证明自行模拟的召回率为 0%\n"
        "3. 禁止自行扮演多个角色进行辩论——必须通过独立子 agent 执行\n\n"
        "请立即执行 Skill(soul-banner)。"
    )

def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        print("{}")
        sys.exit(0)

    user_prompt = input_data.get("user_prompt", "")
    if not user_prompt or not isinstance(user_prompt, str):
        print("{}")
        sys.exit(0)

    # 检查排除条件
    if check_exclude(user_prompt):
        print("{}")
        sys.exit(0)

    # 三级递进匹配
    soul_names = load_soul_names()

    checks = [(check_level1, "一级·命令词")]
    if soul_names:
        checks.append((lambda p: check_level2(p, soul_names), "二级·魂名+视角"))
    checks.append((check_level3, "三级·场景关键词"))

    for check_fn, level_name in checks:
        result = check_fn(user_prompt)
        if result:
            msg = build_system_message(f"[{level_name}] {result}")
            print(json.dumps({"systemMessage": msg}, ensure_ascii=False))
            sys.exit(0)

    # 无匹配
    print("{}")
    sys.exit(0)

if __name__ == "__main__":
    main()
