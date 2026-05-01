#!/usr/bin/env python3
"""万魂幡 Prompt 审计

分析 souls/ 目录下所有魂的 summon_prompt 长度，输出：
  - 每个魂的 summon_prompt 行数和估算 token 数
  - 标记超过 100 行的魂
  - 识别 mind/voice/summon_prompt 三部分中的重复内容（简单句子相似度）

不修改魂文件——只做审计和输出建议。
"""

import json
import os
import re
import sys
from collections import defaultdict
from difflib import SequenceMatcher

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOULS_DIR = os.path.join(SKILL_DIR, "souls")

# 估算 token 的粗略比例：中文约 1.5 字符/token，英文约 4 字符/token
CHINESE_CHAR_RATIO = 1.5
ENGLISH_CHAR_RATIO = 4.0

# 标记阈值
LINE_THRESHOLD = 100
SIMILARITY_THRESHOLD = 0.6  # 句子相似度阈值


def estimate_tokens(text: str) -> int:
    """估算 token 数（粗略：中文 1.5 字符/token，英文 4 字符/token）"""
    if not text:
        return 0
    chinese_chars = len(re.findall(r"[一-鿿]", text))
    total_chars = len(text)
    other_chars = total_chars - chinese_chars
    return int(chinese_chars / CHINESE_CHAR_RATIO + other_chars / ENGLISH_CHAR_RATIO)


def split_sentences(text: str) -> list[str]:
    """将文本拆分为句子（中英文句号、换行等）"""
    # 按中英文句号、分号、换行、破折号拆分
    sentences = re.split(r"[。！？\n;；!?]+", text)
    # 过滤空句和过短句（< 10 字符的没有比较价值）
    return [s.strip() for s in sentences if len(s.strip()) >= 10]


def sentence_similarity(s1: str, s2: str) -> float:
    """计算两个句子的相似度（0-1）"""
    return SequenceMatcher(None, s1, s2).ratio()


def find_overlaps(mind: str, voice: str, summon_prompt: str) -> list[dict]:
    """识别 mind/voice/summon_prompt 三部分之间的重复内容"""
    overlaps = []

    sections = [
        ("mind", mind),
        ("voice", voice),
        ("summon_prompt", summon_prompt),
    ]

    for i in range(len(sections)):
        for j in range(i + 1, len(sections)):
            name1, text1 = sections[i]
            name2, text2 = sections[j]
            if not text1 or not text2:
                continue

            sents1 = split_sentences(text1)
            sents2 = split_sentences(text2)

            for si, s1 in enumerate(sents1):
                for sj, s2 in enumerate(sents2):
                    sim = sentence_similarity(s1, s2)
                    if sim >= SIMILARITY_THRESHOLD:
                        overlaps.append(
                            {
                                "section_pair": f"{name1} ↔ {name2}",
                                "similarity": round(sim, 2),
                                "sentence_1": s1[:120],
                                "sentence_2": s2[:120],
                            }
                        )

    # 去重（按相似度降序排列，只保留最相似的）
    seen = set()
    unique_overlaps = []
    for o in sorted(overlaps, key=lambda x: x["similarity"], reverse=True):
        key = (o["section_pair"], o["sentence_1"][:50])
        if key not in seen:
            seen.add(key)
            unique_overlaps.append(o)

    return unique_overlaps[:15]  # 最多显示15条


def audit_soul(filepath: str) -> dict:
    """审计单个魂文件"""
    try:
        import yaml
    except ImportError:
        print("ERROR: PyYAML not available", file=sys.stderr)
        sys.exit(1)

    filename = os.path.basename(filepath)

    with open(filepath) as f:
        try:
            data = yaml.safe_load(f.read())
        except Exception as e:
            return {"file": filename, "error": str(e)}

    name = data.get("name", filename.replace(".yaml", ""))
    mind = data.get("mind", "")
    voice = data.get("voice", "")
    summon_prompt = data.get("summon_prompt", "")

    sp_lines = summon_prompt.count("\n") + 1 if summon_prompt else 0
    sp_chars = len(summon_prompt) if summon_prompt else 0
    sp_tokens = estimate_tokens(summon_prompt) if summon_prompt else 0

    mind_lines = mind.count("\n") + 1 if mind else 0
    voice_lines = voice.count("\n") + 1 if voice else 0

    overlaps = find_overlaps(mind, voice, summon_prompt)

    result = {
        "file": filename,
        "name": name,
        "summon_prompt": {
            "lines": sp_lines,
            "chars": sp_chars,
            "estimated_tokens": sp_tokens,
            "over_threshold": sp_lines > LINE_THRESHOLD,
        },
        "mind_lines": mind_lines,
        "voice_lines": voice_lines,
        "overlaps": overlaps,
        "overlap_count": len(overlaps),
    }

    return result


def main():
    output_json = "--json" in sys.argv

    results = []
    soul_files = sorted(
        [f for f in os.listdir(SOULS_DIR) if f.endswith(".yaml")]
    )

    for sf in soul_files:
        filepath = os.path.join(SOULS_DIR, sf)
        result = audit_soul(filepath)
        results.append(result)

    # 统计
    over_threshold = [r for r in results if r.get("summon_prompt", {}).get("over_threshold")]
    total_souls = len(results)
    avg_lines = (
        sum(r.get("summon_prompt", {}).get("lines", 0) for r in results) / total_souls
        if total_souls > 0
        else 0
    )
    avg_tokens = (
        sum(r.get("summon_prompt", {}).get("estimated_tokens", 0) for r in results) / total_souls
        if total_souls > 0
        else 0
    )
    souls_with_overlaps = [r for r in results if r.get("overlap_count", 0) > 0]

    if output_json:
        output = {
            "summary": {
                "total_souls": total_souls,
                "average_summon_prompt_lines": round(avg_lines, 1),
                "average_summon_prompt_tokens": round(avg_tokens, 1),
                "over_threshold_count": len(over_threshold),
                "souls_with_overlaps_count": len(souls_with_overlaps),
            },
            "souls": results,
            "recommendations": [],
        }

        # 生成建议
        if over_threshold:
            names = [r["name"] for r in over_threshold]
            output["recommendations"].append(
                {
                    "type": "trim",
                    "severity": "warning",
                    "detail": f"以下魂魄 summon_prompt 超过 {LINE_THRESHOLD} 行：{', '.join(names)}",
                    "suggestion": "考虑将 summon_prompt 中的详细方法论移至 mind，summon_prompt 聚焦于操作指令和角色设定",
                }
            )

        for r in souls_with_overlaps:
            output["recommendations"].append(
                {
                    "type": "deduplicate",
                    "severity": "info",
                    "soul": r["name"],
                    "overlap_count": r["overlap_count"],
                    "detail": f"{r['name']} 的 mind/voice/summon_prompt 之间存在 {r['overlap_count']} 处相似内容",
                    "suggestion": "检查是否有重复定义，归属于最合适的部分（mind=思维内核, voice=表达风格, summon_prompt=运行时指令）",
                }
            )

        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print("=" * 70)
        print(f"万魂幡 Prompt 审计 — {total_souls} 个魂魄")
        print(f"平均 summon_prompt: {avg_lines:.1f} 行 / {avg_tokens:.0f} tokens")
        print("=" * 70)

        # 表格输出
        print(f"\n{'魂魄':<12} {'SP行数':<8} {'SP Token':<10} {'Mind行':<8} {'Voice行':<8} {'超标':<6} {'重复处':<8}")
        print("-" * 70)
        for r in results:
            sp = r.get("summon_prompt", {})
            flag = "⚠️" if sp.get("over_threshold") else ""
            overlaps = r.get("overlap_count", 0)
            o_flag = f"🔄 {overlaps}" if overlaps > 0 else str(overlaps)
            print(
                f"{r['name']:<12} "
                f"{sp.get('lines', 0):<8} "
                f"{sp.get('estimated_tokens', 0):<10} "
                f"{r.get('mind_lines', 0):<8} "
                f"{r.get('voice_lines', 0):<8} "
                f"{flag:<6} "
                f"{o_flag:<8}"
            )

        # 超标魂魄
        if over_threshold:
            print(f"\n⚠️ 超过 {LINE_THRESHOLD} 行的魂魄：")
            for r in over_threshold:
                sp = r.get("summon_prompt", {})
                print(f"   {r['name']}: {sp['lines']} 行 / ~{sp['estimated_tokens']} tokens")

        # 重复内容
        if souls_with_overlaps:
            print(f"\n🔄 mind/voice/summon_prompt 之间存在重复内容的魂魄：")
            for r in souls_with_overlaps:
                print(f"\n   [{r['name']}] ({r['overlap_count']} 处重复)")
                for o in r.get("overlaps", [])[:5]:
                    print(f"     {o['section_pair']} (相似度: {o['similarity']})")
                    print(f"       → {o['sentence_1'][:80]}...")

        # 建议
        print(f"\n📋 建议：")
        if over_threshold:
            print(f"   1. 精简 {len(over_threshold)} 个超标魂魄的 summon_prompt")
        if souls_with_overlaps:
            print(f"   2. 消除 {len(souls_with_overlaps)} 个魂魄的 mind/voice/summon_prompt 重复内容")
        if not over_threshold and not souls_with_overlaps:
            print("   无需操作。所有魂魄 summon_prompt 长度正常，无重复内容。")


if __name__ == "__main__":
    main()
