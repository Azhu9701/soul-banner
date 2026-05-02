#!/usr/bin/env python3
"""跨底模验证 — 区分「真多视角」与「同一模型换帽子」

核心问题：所有魂都 spawn 在同一模型上时，无法区分：
  - 不同魂 → 真正不同的视角（方法论差异驱动）
  - 不同 prompt → 同一模型的不同输出（提示词差异驱动）

验证方法：对同一魂、同一任务，用不同模型重新执行，比较输出一致性。
  - 高一致性 → 视角来自魂的方法论结构（真多视角）
  - 低一致性 → 视角依赖模型特性（同一模型换帽子）

用法：
  # 对比两个输出文件
  python3 scripts/cross-model-verify.py --file-a output_opus.md --file-b output_sonnet.md

  # 对比两个目录（按魂名匹配）
  python3 scripts/cross-model-verify.py --dir-a results/opus/ --dir-b results/sonnet/

  # 输出实验协议（指导主 agent 执行验证）
  python3 scripts/cross-model-verify.py --protocol

输出：一致性评分（0-100）+ 差异分析 + 真多视角/模型产物判定
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from difflib import SequenceMatcher

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# === 文本分析 ===

def extract_claims(text: str) -> list[str]:
    """提取文本中的核心主张（以断言句式出现的句子）"""
    sentences = re.split(r'[。！？\n](?=\s*[^\s])', text)
    claims = []
    claim_patterns = [
        r'(?:核心|关键|主要|本质|根本|最重要).{0,20}(?:是|在于|为)',
        r'(?:判断|结论|认为|主张).{0,10}(?::|：|是)',
        r'(?:矛盾|问题|盲区|风险).{0,10}(?:是|在于)',
        r'(?:必须|应当|需要|不能|禁止).{10,60}',
        r'(?:第一阶段|第二步|首先|然后|最后).{10,60}',
    ]
    for s in sentences:
        s = s.strip()
        if len(s) < 15:
            continue
        for pat in claim_patterns:
            if re.search(pat, s):
                claims.append(s[:200])
                break
    return claims


def extract_methodology_markers(text: str) -> list[str]:
    """提取方法论标记——魂的核心分析工具的使用痕迹"""
    markers = {
        "第一性原理": [r"第一性原理", r"从零推导", r"基本(?:矛盾|约束|假设)", r"归[零根]"],
        "阶级分析": [r"阶级", r"无产阶级", r"资产阶级", r"生产关系", r"劳[工资动]"],
        "矛盾分析": [r"主要矛盾", r"矛盾的主要", r"矛盾分析法", r"对立统一"],
        "科学方法": [r"可证伪", r"假说", r"实验", r"观察", r"Cargo\s*Cult"],
        "成本重构": [r"白痴指数", r"物料成本", r"成本重构", r"供应链"],
        "意识形态批判": [r"意识形态", r"符号", r"话语", r"叙事结构", r"幻象"],
        "渐进改革": [r"试点", r"摸石头", r"渐进", r"不争论", r"猫论"],
        "国民性批判": [r"瞒和骗", r"精神胜利", r"看客", r"奴性", r"自欺"],
    }
    found = []
    for method, patterns in markers.items():
        for pat in patterns:
            if re.search(pat, text):
                found.append(method)
                break
    return list(set(found))


def extract_sections(text: str) -> list[str]:
    """提取文本的结构性段落标题"""
    sections = re.findall(r'(?:^|\n)(?:#{1,4}\s*|(?:\d+[.、)]\s*)|(?:[一二三四五六七八九十]+[、.]\s*))(.{3,40}?)(?:\n|$)', text)
    return [s.strip() for s in sections]


def calculate_text_similarity(text_a: str, text_b: str) -> float:
    """计算两个文本的序列相似度"""
    return SequenceMatcher(None, text_a, text_b).ratio()


# === 一致性分析 ===

def analyze_claim_overlap(claims_a: list[str], claims_b: list[str]) -> dict:
    """分析两个文本的主张重叠度"""
    if not claims_a or not claims_b:
        return {"overlap_count": 0, "overlap_ratio": 0.0, "unique_to_a": len(claims_a),
                "unique_to_b": len(claims_b)}

    # 用文本相似度近似主张重叠
    overlaps = 0
    matched_b = set()
    for ca in claims_a:
        for j, cb in enumerate(claims_b):
            if j in matched_b:
                continue
            if SequenceMatcher(None, ca[:100], cb[:100]).ratio() > 0.5:
                overlaps += 1
                matched_b.add(j)
                break

    total_unique = len(set(claims_a)) + len(set(claims_b))
    return {
        "overlap_count": overlaps,
        "overlap_ratio": round(overlaps / max(total_unique / 2, 1), 2),
        "unique_to_a": len(claims_a) - overlaps,
        "unique_to_b": len(claims_b) - overlaps,
        "claims_a_count": len(claims_a),
        "claims_b_count": len(claims_b),
    }


def analyze_methodology_consistency(methods_a: list[str], methods_b: list[str]) -> dict:
    """检查方法论标记是否跨模型一致"""
    set_a = set(methods_a)
    set_b = set(methods_b)
    overlap = set_a & set_b
    only_a = set_a - set_b
    only_b = set_b - set_a

    consistency = len(overlap) / max(len(set_a | set_b), 1)
    return {
        "shared_methods": sorted(overlap),
        "only_in_a": sorted(only_a),
        "only_in_b": sorted(only_b),
        "consistency_score": round(consistency * 100),
        "interpretation": (
            "方法论标记高度一致——视角来自魂结构" if consistency > 0.7
            else "方法论标记部分一致——可能受模型影响" if consistency > 0.3
            else "方法论标记不一致——视角可能是模型产物"
        )
    }


def analyze_structure_consistency(sections_a: list[str], sections_b: list[str]) -> dict:
    """检查文本结构是否跨模型一致"""
    # 用 LCS 近似结构相似度
    len_a, len_b = len(sections_a), len(sections_b)
    if len_a == 0 or len_b == 0:
        return {"structure_similarity": 0, "shared_sections": [], "interpretation": "无法比较——一侧缺少结构"}

    # 简单 token 重叠匹配
    shared = []
    for sa in sections_a:
        for sb in sections_b:
            if SequenceMatcher(None, sa[:50], sb[:50]).ratio() > 0.6:
                shared.append(sa)
                break

    sim = len(shared) / max(len_a, len_b)
    return {
        "structure_similarity": round(sim, 2),
        "shared_sections": shared[:5],
        "sections_a": sections_a,
        "sections_b": sections_b,
        "interpretation": (
            "结构一致——分析框架来自魂" if sim > 0.6
            else "结构部分一致" if sim > 0.3
            else "结构差异大——分析框架可能受模型影响"
        )
    }


def compute_consensus_score(
    text_sim: float,
    claim_overlap: dict,
    method_consistency: dict,
    structure_consistency: dict,
) -> int:
    """综合计算跨模型一致性评分（0-100）"""
    score = 0.0
    # 方法论一致性权重最高（40分）——魂的核心是方法论
    score += method_consistency["consistency_score"] * 0.4
    # 结构一致性（30分）
    score += structure_consistency["structure_similarity"] * 30
    # 主张重叠（20分）
    score += claim_overlap["overlap_ratio"] * 20
    # 文本相似度（10分）——最低权重，允许表达差异
    score += min(text_sim, 0.8) / 0.8 * 10
    return min(int(score), 100)


def verdict(score: int) -> str:
    if score >= 70:
        return "真多视角 —— 视角来自魂的方法论结构，跨模型稳定"
    elif score >= 40:
        return "部分真视角 —— 核心方法论稳定，但部分内容受模型影响"
    else:
        return "模型产物 —— 视角高度依赖模型特性，不是独立方法论"


# === 实验协议 ===

PROTOCOL = """
跨底模验证实验协议
====================

## 目的
区分「真多视角」（魂的方法论驱动不同结论）与「同一模型换帽子」（同模型不同 prompt 的不同输出）。

## 前提
万魂幡所有魂 spawn 在同一模型（如 Claude Opus）上。魂方法论不同，但底层模型相同。
当不同魂产生不同分析时，无法排除「是模型被不同 prompt 引导到不同输出」的替代解释。

## 验证方法
对同一魂、同一任务，用不同模型各执行一次。如果魂的方法论是真实的：
  - 不同模型应该在核心主张、方法论标记、分析结构上高度一致
  - 差异应限于表达风格和细节展开程度
如果只是 prompt 在引导模型：
  - 不同模型会产生显著不同的分析框架和主张

## 执行步骤

### 步骤 1：选择测试魂和任务
- 选择 2-3 个魂：一个金魂（强方法论）、一个银/紫魂（中等方法论）、一个对照魂
- 选择一个之前已执行过的任务（有历史输出可对比）
- 任务不能太宽泛（否则差异来自解释空间）也不能太窄（否则无分析空间）

### 步骤 2：模型 A 执行（baseline，使用当前默认模型）
- spawn 魂 A 执行任务 → 保存输出为 output_{魂名}_model_a.md
- spawn 魂 B 执行任务 → 保存输出为 output_{魂名}_model_a.md

### 步骤 3：模型 B 执行（verification，使用不同模型）
- spawn 同一魂 A，注入同一 summon_prompt，同一任务，但指定不同 model
  Agent(subagent_type="{魂名}", model="opus", ...)   # 如果 baseline 是 sonnet
  Agent(subagent_type="{魂名}", model="sonnet", ...)  # 如果 baseline 是 opus
- 保存输出为 output_{魂名}_model_b.md

### 步骤 4：对比分析
python3 scripts/cross-model-verify.py \\
  --file-a output_{魂名}_model_a.md \\
  --file-b output_{魂名}_model_b.md

### 步骤 5：解读
- 一致性评分 ≥ 70：魂的视角是真实的，方法论跨模型稳定
- 一致性评分 40-69：部分真实，建议对该魂增加模型多样性使用
- 一致性评分 < 40：该魂的视角可能是 prompt 引导的产物
  → 改进：强化 summon_prompt 中的方法论具体性
  → 或：标记该魂仅在特定模型上使用

## 建议验证频率
- 新魂入幡后首次验证
- 魂的 summon_prompt 大幅修改后
- 每季度定期抽样（选 2-3 个高频魂验证）
- 发现某魂输出质量不稳定时

## 模型选择
- 至少使用两种不同的模型系列（如 Claude Opus vs Sonnet）
- 如果可用，加入第三方模型作为额外对照
- 模型 A 和模型 B 应该有足够的能力差距（不能用 opus-4.5 vs opus-4.6 这种微小版本差异）
"""


# === 主流程 ===

def compare_files(file_a: str, file_b: str) -> dict:
    """对比两个输出文件"""
    with open(file_a) as f:
        text_a = f.read()
    with open(file_b) as f:
        text_b = f.read()

    claims_a = extract_claims(text_a)
    claims_b = extract_claims(text_b)
    methods_a = extract_methodology_markers(text_a)
    methods_b = extract_methodology_markers(text_b)
    sections_a = extract_sections(text_a)
    sections_b = extract_sections(text_b)
    text_sim = calculate_text_similarity(text_a, text_b)

    claim_result = analyze_claim_overlap(claims_a, claims_b)
    method_result = analyze_methodology_consistency(methods_a, methods_b)
    structure_result = analyze_structure_consistency(sections_a, sections_b)
    score = compute_consensus_score(text_sim, claim_result, method_result, structure_result)

    return {
        "file_a": os.path.basename(file_a),
        "file_b": os.path.basename(file_b),
        "text_similarity": round(text_sim, 2),
        "claims_analysis": claim_result,
        "methodology_analysis": method_result,
        "structure_analysis": structure_result,
        "consensus_score": score,
        "verdict": verdict(score),
    }


def compare_dirs(dir_a: str, dir_b: str) -> list[dict]:
    """对比两个目录中的同名魂输出"""
    results = []
    files_a = {f for f in os.listdir(dir_a) if f.endswith('.md')}
    files_b = {f for f in os.listdir(dir_b) if f.endswith('.md')}
    common = files_a & files_b

    for fname in sorted(common):
        try:
            result = compare_files(os.path.join(dir_a, fname), os.path.join(dir_b, fname))
            results.append(result)
        except Exception as e:
            results.append({"file": fname, "error": str(e)})

    only_a = files_a - files_b
    only_b = files_b - files_a
    if only_a or only_b:
        results.append({
            "warning": "部分文件仅在一侧存在",
            "only_in_a": sorted(only_a),
            "only_in_b": sorted(only_b),
        })

    return results


def main():
    parser = argparse.ArgumentParser(description="跨底模验证")
    parser.add_argument("--file-a", help="模型A的输出文件")
    parser.add_argument("--file-b", help="模型B的输出文件")
    parser.add_argument("--dir-a", help="模型A的输出目录")
    parser.add_argument("--dir-b", help="模型B的输出目录")
    parser.add_argument("--protocol", action="store_true", help="输出实验协议")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()

    if args.protocol:
        print(PROTOCOL)
        sys.exit(0)

    if args.file_a and args.file_b:
        if not os.path.exists(args.file_a):
            print(f"ERROR: {args.file_a} 不存在", file=sys.stderr)
            sys.exit(1)
        if not os.path.exists(args.file_b):
            print(f"ERROR: {args.file_b} 不存在", file=sys.stderr)
            sys.exit(1)

        result = compare_files(args.file_a, args.file_b)

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"跨底模验证: {result['file_a']} vs {result['file_b']}")
            print(f"{'=' * 50}")
            print(f"文本相似度: {result['text_similarity']}")
            print(f"方法论一致性: {result['methodology_analysis']['consistency_score']}%")
            print(f"  → {result['methodology_analysis']['interpretation']}")
            print(f"  共享方法: {result['methodology_analysis']['shared_methods'] or '无'}")
            print(f"  仅A: {result['methodology_analysis']['only_in_a'] or '无'}")
            print(f"  仅B: {result['methodology_analysis']['only_in_b'] or '无'}")
            print(f"结构一致性: {result['structure_analysis']['structure_similarity']}")
            print(f"  → {result['structure_analysis']['interpretation']}")
            print(f"主张重叠: {result['claims_analysis']['overlap_ratio']} ({result['claims_analysis']['overlap_count']}/{max(result['claims_analysis']['claims_a_count'], result['claims_analysis']['claims_b_count'])})")
            print(f"---")
            print(f"综合评分: {result['consensus_score']}/100")
            print(f"判定: {result['verdict']}")
        sys.exit(0)

    if args.dir_a and args.dir_b:
        if not os.path.isdir(args.dir_a):
            print(f"ERROR: {args.dir_a} 不是目录", file=sys.stderr)
            sys.exit(1)
        if not os.path.isdir(args.dir_b):
            print(f"ERROR: {args.dir_b} 不是目录", file=sys.stderr)
            sys.exit(1)

        results = compare_dirs(args.dir_a, args.dir_b)

        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(f"跨底模验证 — 目录对比: {args.dir_a} vs {args.dir_b}")
            print(f"{'=' * 60}")
            summary = []
            for r in results:
                if "error" in r:
                    print(f"  ✗ {r['file']}: {r['error']}")
                elif "warning" in r:
                    print(f"  ⚠ {r['warning']}")
                    if r.get("only_in_a"):
                        print(f"    仅A: {r['only_in_a']}")
                    if r.get("only_in_b"):
                        print(f"    仅B: {r['only_in_b']}")
                else:
                    print(f"  {r['consensus_score']:3d}/100 {r['file_a']}")
                    print(f"       {r['verdict'][:60]}...")
                    summary.append(r['consensus_score'])

            if summary:
                avg = sum(summary) / len(summary)
                print(f"\n平均一致性: {avg:.0f}/100")
                high = sum(1 for s in summary if s >= 70)
                mid = sum(1 for s in summary if 40 <= s < 70)
                low = sum(1 for s in summary if s < 40)
                print(f"真多视角: {high} | 部分真: {mid} | 模型产物: {low}")
        sys.exit(0)

    parser.print_help()
    sys.exit(0)


if __name__ == "__main__":
    main()
