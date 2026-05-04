#!/usr/bin/env python3
"""万民幡 Hook 脚本单元测试"""
import json
import os
import subprocess
import sys

HOOK_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "soul-banner-hook.py")

EVAL_QUERIES = [
    ("我想听听乔布斯和马斯克对产品定位的不同看法，然后你来辩证综合一下", True),
    ("从毛泽东的视角分析一下当前中美关系的本质矛盾", True),
    ("帮我分析一下新能源汽车行业，我想听不同角度的观点，最后给一个综合判断", True),
    ("收魂 黄仁勋", True),
    ("幡中有什么魂", True),
    ("合议 量子计算商业化还需要多久", True),
    ("辩论 要不要做开源 乔布斯 vs 马斯克", True),
    ("用费曼的思维方式来审视一下我们团队的研发流程，看看有没有自欺欺人的地方", True),
    ("接力 写一个新产品上市方案 费曼→邓小平→罗永浩→列宁", True),
    ("幡中战绩", True),
    ("我最近在思考要不要辞职创业，帮我用第一性原理分析一下", True),
    ("我们公司战略方向有分歧，能不能让几个不同的思维模式的人来辩论一下然后辩证综合？不用告诉我他们是谁，你直接分析就行", True),
    ("帮我修复一个 bug，这个函数在处理空数组时会报 TypeError: Cannot read properties of undefined", False),
    ("马斯克最近一条推文说了什么？帮我查一下他关于特斯拉股价的最新评论", False),
    ("帮我搜索一下费曼学习法的具体步骤，我想用这个方法学线性代数", False),
    ("把这张 Excel 表里的 Q4 销售数据按地区汇总，做成柱状图", False),
    ("写一封辞职邮件，要专业但不太正式，主要感谢团队的帮助和领导的指导", False),
    ("我想了解一下邓小平理论的要点，帮我总结一下改革开放的核心思想", False),
    ("这个 PPT 的排版帮我优化一下，字体用思源黑体，标题加粗，正文 14pt", False),
    ("帮我写个 Python 脚本，从 API 拉取数据存入 PostgreSQL，加上错误重试和日志", False),
]

def run_hook(prompt: str) -> dict:
    """运行 hook 脚本并返回解析后的 JSON 输出"""
    input_data = json.dumps({"user_prompt": prompt})
    result = subprocess.run(
        [sys.executable, HOOK_SCRIPT],
        input=input_data,
        capture_output=True,
        text=True,
        timeout=5,
    )
    return json.loads(result.stdout.strip() or "{}")

def main():
    should_trigger_tests = [(q, e) for q, e in EVAL_QUERIES if e]
    should_not_trigger_tests = [(q, e) for q, e in EVAL_QUERIES if not e]

    print("=" * 70)
    print("万民幡 Hook 脚本单元测试")
    print("=" * 70)

    results = {"tp": 0, "tn": 0, "fp": 0, "fn": 0, "errors": []}

    print("\n--- Should Trigger (应触发) ---")
    for prompt, _ in should_trigger_tests:
        output = run_hook(prompt)
        triggered = "systemMessage" in output
        reason = output.get("systemMessage", "")[:80] if triggered else "无匹配"
        status = "PASS" if triggered else "FAIL"
        if triggered:
            results["tp"] += 1
        else:
            results["fn"] += 1
            results["errors"].append(f"FN: {prompt[:60]}...")
        print(f"  [{status}] {prompt[:60]}...")
        if status == "FAIL":
            print(f"         -> {reason}")

    print("\n--- Should NOT Trigger (不应触发) ---")
    for prompt, _ in should_not_trigger_tests:
        output = run_hook(prompt)
        triggered = "systemMessage" in output
        status = "PASS" if not triggered else "FAIL"
        if not triggered:
            results["tn"] += 1
        else:
            results["fp"] += 1
            results["errors"].append(f"FP: {prompt[:60]}...")
        print(f"  [{status}] {prompt[:60]}...")

    total = len(EVAL_QUERIES)
    correct = results["tp"] + results["tn"]
    precision = results["tp"] / (results["tp"] + results["fp"]) if (results["tp"] + results["fp"]) > 0 else 0
    recall = results["tp"] / (results["tp"] + results["fn"]) if (results["tp"] + results["fn"]) > 0 else 0

    print("\n" + "=" * 70)
    print(f"正确: {correct}/{total} ({correct/total*100:.0f}%)")
    print(f"精确率: {precision:.0%}  召回率: {recall:.0%}")
    print(f"TP={results['tp']} FN={results['fn']} FP={results['fp']} TN={results['tn']}")
    if results["errors"]:
        print(f"\n错误详情:")
        for e in results["errors"]:
            print(f"  - {e}")
    print("=" * 70)

    return 0 if correct == total else 1

if __name__ == "__main__":
    sys.exit(main())
