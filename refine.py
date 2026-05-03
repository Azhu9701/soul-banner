#!/usr/bin/env python3
"""
万民幡 - 炼化辅助脚本 (refine.py)

辅助炼化魂魄，提供结构化提取建议和品级判定参考。
实际炼化仍由 Agent 主导。

功能：
1. 接收原始素材文本
2. 输出结构化提取建议
3. 品级判定（基于素材字数、领域数、方法论明确度等）

使用方法：
python refine.py --input 素材文件.md
python refine.py --text "素材文本内容"
"""

import re
import sys
from typing import Dict, List, Tuple, Optional

# ============================================================
# 三维功能标签评估参数
# ============================================================

# 信息充分度阈值（素材字数）
INFO_SUFFICIENCY_THRESHOLDS = {
    "充分": 10000,
    "中等": 5000,
    # 低于 5000 → "不足"
}

# 功能域标签到领域关键词的映射（辅助建议，非自动判定）
FUNCTION_DOMAIN_KEYWORDS = {
    "批判型": ["批判", "解构", "揭露", "质疑", "分析前提"],
    "建设型": ["设计", "构建", "创造", "系统", "架构"],
    "组织型": ["组织", "动员", "领导", "治理", "运营"],
    "分析型": ["分析", "理论", "建模", "逻辑", "系统思维"],
    "叙事型": ["叙事", "故事", "传播", "表达", "沟通"],
    "情绪型": ["情绪", "情感", "支持", "士气", "快乐"],
}

# 关键方法论关键词
METHODOLOGY_KEYWORDS = [
    "第一性原理", "first principle", "演绎", "归纳",
    "系统思维", "批判性思维", "逆向思维",
    "方法论", "框架", "模型", "公式",
    "step", "步骤", "流程", "流程图"
]

# 关键技能领域关键词
SKILL_KEYWORDS = {
    "deep-reading": ["深度阅读", "分析", "理解复杂", "研究"],
    "topic_tracking": ["追踪", "监测", "趋势", "动态"],
    "system-thinking": ["系统", "架构", "整体", "协同"],
    "decision-making": ["决策", "判断", "选择", "战略"],
    "creative-writing": ["创作", "写作", "文案", "表达"],
    "code-generation": ["代码", "编程", "开发", "实现"],
}

# 沟通风格关键词
STYLE_KEYWORDS = {
    "简洁直接": ["短句", "直接", "废话", "简洁", "精炼"],
    "技术硬核": ["物理", "数学", "公式", "数据", "数字"],
    "类比丰富": ["类比", "比喻", "如同", "像"],
    "口头禅": ["obviously", "literally", "fundamentally", "clearly"],
    "Meme风格": ["meme", "梗", "表情包", "玩笑"],
}


# ============================================================
# 结构化提取函数
# ============================================================

def extract_structured_info(text: str) -> Dict:
    """
    从素材文本中提取结构化信息
    """
    result = {
        "estimated_words": len(text),
        "domains": [],
        "methodology_found": [],
        "skills_suggested": [],
        "style_characteristics": [],
        "key_quotes": [],
        "decision_cases": [],
    }
    
    # 1. 估算字数
    word_count = len(text)
    result["estimated_words"] = word_count
    
    # 2. 提取领域（基于关键词）
    domain_patterns = {
        "航天": ["火箭", "SpaceX", "发射", "轨道", "星舰"],
        "电动汽车": ["Tesla", "电池", "续航", "充电", "汽车"],
        "AI": ["人工智能", "AI", "AGI", "大模型", "Grok", "xAI"],
        "脑机接口": ["Neuralink", "脑机", "神经", "意念"],
        "能源": ["太阳能", "储能", "Megapack", "可持续"],
        "社交媒体": ["Twitter", "X", "推特", "meme"],
        "管理": ["管理", "团队", "裁员", "效率", "扁平"],
        "创业": ["创业", "融资", "破产", "初创"],
    }
    
    text_lower = text.lower()
    for domain, keywords in domain_patterns.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                if domain not in result["domains"]:
                    result["domains"].append(domain)
                break
    
    # 3. 提取方法论关键词
    for kw in METHODOLOGY_KEYWORDS:
        if kw.lower() in text.lower():
            if kw not in result["methodology_found"]:
                result["methodology_found"].append(kw)
    
    # 4. 匹配推荐 Skill
    text_lower = text.lower()
    for skill, keywords in SKILL_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                if skill not in result["skills_suggested"]:
                    result["skills_suggested"].append(skill)
                break
    
    # 5. 提取沟通风格
    for style, keywords in STYLE_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                if style not in result["style_characteristics"]:
                    result["style_characteristics"].append(style)
                break
    
    # 6. 提取关键语录（引号内容）
    quotes = re.findall(r'["""]([^"""]+)["""]', text)
    if quotes:
        result["key_quotes"] = quotes[:5]  # 最多5条
    
    return result


def assess_dimensions(
    word_count: int,
    domain_count: int,
    methodology_count: int,
    skill_count: int,
    source_count: int
) -> Dict:
    """
    评估三维功能标签

    返回: {info_sufficiency, suggested_domains, methodology_transferability}
    注意：function_domains 仅为辅助建议，实际判定由 Agent 在炼化时完成
    """
    # 维度一：信息充分度
    if word_count >= 10000 and source_count >= 2:
        info_suf = "充分"
        suf_reason = f"素材 {word_count} 字，{source_count} 个来源"
    elif word_count >= 5000:
        info_suf = "中等"
        suf_reason = f"素材 {word_count} 字，{source_count} 个来源"
    else:
        info_suf = "不足"
        suf_reason = f"素材仅 {word_count} 字，模拟精度有限"

    # 维度二：功能域标签由 Agent 在炼化时根据触发场景和领域手动指定
    # refine.py 不做自动判定——仅提供关键词映射表供 Agent 参考

    # 维度三：方法论可传输度（基于方法论关键词数量的启发式）
    if methodology_count >= 3 and skill_count >= 3:
        meth_trans = "可传输"
        meth_reason = "有多个明确可文本化的方法论步骤"
    elif methodology_count >= 1:
        meth_trans = "嵌入型"
        meth_reason = "方法论可描述但执行依赖判断力"
    else:
        meth_trans = "人格型"
        meth_reason = "价值即人格模拟本身"

    return {
        "info_sufficiency": info_suf,
        "info_sufficiency_reason": suf_reason,
        "function_domains_hint": "由 Agent 在炼化时根据触发场景和领域手动指定",
        "methodology_transferability": meth_trans,
        "methodology_transferability_reason": meth_reason,
    }


def generate_yaml_suggestion(info: Dict, assessment: Dict) -> str:
    """
    生成 YAML 格式的建议（三维功能标签）
    """
    yaml = f'''name: "待定"
title: "待定"
domain: {info.get("domains", [])}

mind: |
  # 从素材中提取的核心思维描述

voice: |
  # 从素材中提取的表达风格描述

skills_expertise:
  # 从素材中提取的专业技能
  - "技能1"
  - "技能2"

info_sufficiency: {assessment["info_sufficiency"]}
function_domains:
  - "# TODO: Agent 炼化时手动指定（批判型/建设型/组织型/分析型/叙事型/情绪型）"
methodology_transferability: {assessment["methodology_transferability"]}

artifacts:
  # 建议匹配的 Skill
'''

    for skill in info.get("skills_suggested", []):
        yaml += f'  - skill_name: "{skill}"\n    binding_reason: "# TODO: 填写绑定原因"\n'
    
    yaml += '''
summon_prompt: |
  # 完整的召唤 prompt
  
source_materials:
  - "# TODO: 填写素材来源"

refined_at: "YYYY-MM-DD"
'''
    return yaml


# ============================================================
# 主函数
# ============================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="万民幡炼化辅助工具")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", "-i", help="输入素材文件路径")
    group.add_argument("--text", "-t", help="输入素材文本")
    parser.add_argument("--output", "-o", help="输出YAML建议文件路径")
    
    args = parser.parse_args()
    
    # 读取素材
    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = args.text
    
    # 提取结构化信息
    print("=" * 60)
    print("🔮 万民幡 - 炼化辅助分析")
    print("=" * 60)
    
    info = extract_structured_info(text)
    
    print(f"\n📊 素材概况:")
    print(f"   字数: {info['estimated_words']:,} 字")
    print(f"   领域: {', '.join(info['domains']) if info['domains'] else '未识别'}")
    print(f"   方法论: {', '.join(info['methodology_found']) if info['methodology_found'] else '未识别'}")
    
    print(f"\n🎯 推荐Skill:")
    for skill in info.get("skills_suggested", []):
        print(f"   - {skill}")
    if not info.get("skills_suggested"):
        print("   (未匹配到预设Skill)")
    
    print(f"\n💬 风格特征:")
    for style in info.get("style_characteristics", []):
        print(f"   - {style}")
    if not info.get("style_characteristics"):
        print("   (未识别到典型风格)")
    
    print(f"\n📝 关键语录示例:")
    for i, quote in enumerate(info.get("key_quotes", [])[:3], 1):
        print(f"   {i}. \"{quote[:50]}{'...' if len(quote) > 50 else ''}\"")
    
    # 三维功能标签评估
    assessment = assess_dimensions(
        info['estimated_words'],
        len(info['domains']),
        len(info['methodology_found']),
        len(info['skills_suggested']),
        1  # 默认1个来源，Agent 炼化时可根据实际来源数调整
    )

    print(f"\n🏷️ 三维功能标签评估:")
    print(f"   信息充分度: {assessment['info_sufficiency']}（{assessment['info_sufficiency_reason']}）")
    print(f"   功能域标签: {assessment['function_domains_hint']}")
    print(f"   方法论可传输度: {assessment['methodology_transferability']}（{assessment['methodology_transferability_reason']}）")

    # 生成 YAML 建议
    yaml_suggestion = generate_yaml_suggestion(info, assessment)
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(yaml_suggestion)
        print(f"\n✅ YAML建议已保存至: {args.output}")
    else:
        print("\n" + "=" * 60)
        print("📄 YAML 结构建议:")
        print("=" * 60)
        print(yaml_suggestion)
    
    print("\n" + "=" * 60)
    print("💡 提示: 这是辅助工具，实际炼化由 Agent 主导完成")
    print("=" * 60)


# ============================================================
# YAML 格式校验
# ============================================================

REQUIRED_FIELDS = [
    'name', 'title', 'domain',
    'mind', 'voice', 'skills_expertise',
    'trigger',           # 必须是 dict，含 keywords/domains/scenarios/exclude
    'info_sufficiency', 'function_domains', 'methodology_transferability',
    'artifacts', 'summon_prompt',
    'source_materials', 'refined_at',
]

# 推荐但非必须的字段（缺了只 warning）
NICE_TO_HAVE_FIELDS = [
    'skills_expertise_description',
    'notes',
    'patches',
]

PATCH_REQUIRED_KEYS = ['version', 'applied_at', 'source', 'type', 'content', 'approved_by']
PATCH_VALID_TYPES = ['blindspot_awareness', 'boundary_refinement', 'trigger_adjustment', 'pairing_insight']
PATCH_OPTIONAL_KEYS = ['activation_conditions', 'effectiveness_tracking']
PATCH_ACTIVATION_KEYS = ['task_domains', 'task_keywords']

TRIGGER_REQUIRED_KEYS = ['keywords', 'domains', 'scenarios', 'exclude']
ARTIFACT_REQUIRED_KEYS = ['skill_name', 'binding_reason']

# 格式化陷阱检测：这些字段是 registry 用的，不应出现在魂 YAML 中
REGISTRY_ONLY_FIELDS = [
    'trigger_keywords_summary',
    'trigger_scenarios_summary',
    'trigger_exclude_summary',
    'source_summary',
]


def validate_soul(yaml_path: str) -> dict:
    """校验魂魄 YAML 文件格式

    返回: {'valid': bool, 'errors': [...], 'warnings': [...]}
    """
    import yaml as _yaml
    result = {'valid': True, 'errors': [], 'warnings': []}

    with open(yaml_path, 'r', encoding='utf-8') as f:
        soul = _yaml.safe_load(f)

    # 1. 检查必填字段
    for field in REQUIRED_FIELDS:
        if field not in soul or soul[field] is None:
            result['errors'].append(f"缺少必填字段: {field}")
            result['valid'] = False

    # 1b. 检查推荐字段
    for field in NICE_TO_HAVE_FIELDS:
        if field not in soul or soul[field] is None:
            result['warnings'].append(f"建议添加字段: {field}")

    # 2. 检查 registry 格式误用
    for field in REGISTRY_ONLY_FIELDS:
        if field in soul:
            result['errors'].append(
                f"发现 registry 专用字段 '{field}' —— 魂 YAML 应使用结构化格式 "
                f"(trigger: {{keywords: [], ...}})，而非 summary 字符串"
            )
            result['valid'] = False

    # 3. 检查 trigger 结构
    if 'trigger' in soul and isinstance(soul['trigger'], dict):
        trigger = soul['trigger']
        for key in TRIGGER_REQUIRED_KEYS:
            if key not in trigger or not trigger[key]:
                result['errors'].append(f"trigger 缺少子字段: {key}")
                result['valid'] = False

        # 检查 keywords 和 exclude 是否为列表
        for key in ['keywords', 'exclude', 'domains', 'scenarios']:
            if key in trigger and not isinstance(trigger[key], list):
                result['errors'].append(f"trigger.{key} 应为列表，当前为 {type(trigger[key]).__name__}")
                result['valid'] = False
    else:
        result['errors'].append("trigger 字段缺失或不是 dict")
        result['valid'] = False

    # 4. 检查 artifacts 结构
    if 'artifacts' in soul and isinstance(soul['artifacts'], list):
        for i, art in enumerate(soul['artifacts']):
            if isinstance(art, dict):
                for key in ARTIFACT_REQUIRED_KEYS:
                    if key not in art:
                        result['errors'].append(f"artifacts[{i}] 缺少: {key}")
                        result['valid'] = False
            else:
                result['errors'].append(
                    f"artifacts[{i}] 应为 {{skill_name, binding_reason}} dict，"
                    f"当前为 {type(art).__name__}"
                )
                result['valid'] = False

    # 4.5. 检查 patches 结构
    if 'patches' in soul and isinstance(soul['patches'], list):
        for i, patch in enumerate(soul['patches']):
            if not isinstance(patch, dict):
                result['errors'].append(f"patches[{i}] 应为 dict，当前为 {type(patch).__name__}")
                result['valid'] = False
                continue
            for key in PATCH_REQUIRED_KEYS:
                if key not in patch:
                    result['errors'].append(f"patches[{i}] 缺少: {key}")
                    result['valid'] = False
            if patch.get('type') and patch['type'] not in PATCH_VALID_TYPES:
                result['errors'].append(
                    f"patches[{i}].type 无效值 '{patch['type']}'，须为: {PATCH_VALID_TYPES}"
                )
                result['valid'] = False
            # 校验 activation_conditions 结构（可选字段）
            if 'activation_conditions' in patch and patch['activation_conditions'] is not None:
                ac = patch['activation_conditions']
                if not isinstance(ac, dict):
                    result['errors'].append(f"patches[{i}].activation_conditions 应为 dict")
                    result['valid'] = False
                else:
                    for key in ac:
                        if key not in PATCH_ACTIVATION_KEYS:
                            result['warnings'].append(
                                f"patches[{i}].activation_conditions 含未知键 '{key}'，已知键: {PATCH_ACTIVATION_KEYS}"
                            )
                    for key in PATCH_ACTIVATION_KEYS:
                        if key in ac and not isinstance(ac[key], list):
                            result['errors'].append(
                                f"patches[{i}].activation_conditions.{key} 应为列表"
                            )
                            result['valid'] = False

    # 5. 质量检查 (warnings)
    if 'summon_prompt' in soul and isinstance(soul['summon_prompt'], str):
        prompt_len = len(soul['summon_prompt'])
        if prompt_len < 2000:
            result['warnings'].append(f"summon_prompt 较短 ({prompt_len} chars)，建议 >= 5000")
    else:
        result['warnings'].append("summon_prompt 缺失或非字符串")

    if 'mind' in soul and isinstance(soul['mind'], str):
        if len(soul['mind']) < 300:
            result['warnings'].append(f"mind 较短 ({len(soul['mind'])} chars)，建议 >= 800")
    if 'voice' in soul and isinstance(soul['voice'], str):
        if len(soul['voice']) < 200:
            result['warnings'].append(f"voice 较短 ({len(soul['voice'])} chars)，建议 >= 400")

    if 'skills_expertise' in soul and isinstance(soul['skills_expertise'], list):
        if len(soul['skills_expertise']) < 3:
            result['warnings'].append(f"skills_expertise 仅有 {len(soul['skills_expertise'])} 项，建议 >= 5")

    return result


def validate_all_souls(souls_dir: str) -> dict:
    """批量校验所有魂魄"""
    from pathlib import Path
    results = {}
    for yaml_file in sorted(Path(souls_dir).glob('*.yaml')):
        results[yaml_file.name] = validate_soul(str(yaml_file))
    return results


# ============================================================
# Obsidian 自动联动
# ============================================================

OBSIDIAN_VAULT = None  # 首次使用时探测

def get_obsidian_vault() -> str | None:
    """获取 Obsidian vault 路径"""
    global OBSIDIAN_VAULT
    if OBSIDIAN_VAULT:
        return OBSIDIAN_VAULT
    import subprocess
    try:
        result = subprocess.run(
            ['obsidian', 'eval', 'code=app.vault.adapter.basePath'],
            capture_output=True, text=True, timeout=5
        )
        path = result.stdout.strip()
        if path and '=>' in path:
            path = path.split('=>')[-1].strip()
        if path and path != 'null' and path != 'undefined':
            OBSIDIAN_VAULT = path
            return path
    except Exception:
        pass
    return None


def sync_soul_to_obsidian(yaml_path: str) -> str | None:
    """将魂魄 YAML 同步为 Obsidian wiki-link 版 Markdown

    返回写入的路径，失败返回 None
    """
    vault = get_obsidian_vault()
    if not vault:
        return None

    import yaml as _yaml
    from pathlib import Path
    from datetime import datetime

    with open(yaml_path, 'r', encoding='utf-8') as f:
        soul = _yaml.safe_load(f)

    name = soul.get('name', Path(yaml_path).stem)
    vault_dir = Path(vault) / '万民幡' / '魂魄'
    vault_dir.mkdir(parents=True, exist_ok=True)

    # 生成 wiki-link 版 Markdown
    info_suf = soul.get('info_sufficiency', '?')
    func_doms = soul.get('function_domains', [])
    meth_trans = soul.get('methodology_transferability', '?')
    trigger = soul.get('trigger', {})
    mind = soul.get('mind', '')
    voice = soul.get('voice', '')

    md = f"""---
tags: [万民幡, 魂魄, {', '.join(soul.get('domain', [])[:3])}]
date: {datetime.now().strftime('%Y-%m-%d')}
info_sufficiency: {info_suf}
function_domains: {', '.join(func_doms) if isinstance(func_doms, list) else str(func_doms)}
methodology_transferability: {meth_trans}
domain: {soul.get('domain', [])}
---

# {name}

**{soul.get('title', '')}**

## 三维功能标签

- **信息充分度**: {info_suf}
- **功能域**: {', '.join(func_doms) if isinstance(func_doms, list) else str(func_doms)}
- **方法论可传输度**: {meth_trans}

## 核心哲学

{mind if mind else '（待补充）'}

## 表达风格

{voice if voice else '（待补充）'}

## 触发条件

- **关键词**: {', '.join(trigger.get('keywords', ['?'])[:10])}
- **场景**: {', '.join(trigger.get('scenarios', ['?'])[:5])}
- **排除**: {', '.join(trigger.get('exclude', ['?'])[:5])}
"""
    out_path = vault_dir / f"{name}.md"
    out_path.write_text(md, encoding='utf-8')
    return str(out_path)


if __name__ == "__main__":
    main()
