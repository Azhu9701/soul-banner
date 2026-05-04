#!/usr/bin/env python3
"""万民幡对照实验框架 — 费曼式 4 条件 × N 任务 × 盲评设计

条件：
  A: 万民幡合议（匹配3魂合议 + 辩证综合官）
  B: 裸AI（同底层模型，等token预算，单次推理）
  C: 多步推理裸AI（同底层模型，等token预算，多步推理但无魂prompt注入）
  D: 人类专家基线

用法：
  python3 scripts/controlled-experiment.py generate --tasks 20  # 生成实验任务池
  python3 scripts/controlled-experiment.py run --task-id 1 --condition A  # 执行特定条件
  python3 scripts/controlled-experiment.py blind-review --output-dir results/  # 盲评输出
  python3 scripts/controlled-experiment.py stats --results results/  # 统计分析
"""

import json
import os
import sys
import random
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict

SKILL_DIR = Path(__file__).resolve().parent.parent
EXPERIMENT_DIR = SKILL_DIR / "experiments"
RESULTS_DIR = EXPERIMENT_DIR / "results"
TASKS_FILE = EXPERIMENT_DIR / "task-pool.json"

# 任务域分布（确保覆盖领域内和领域边界）
DOMAIN_DISTRIBUTION = {
    "技术/工程": 4,       # 具身智能、编程架构、半导体战略
    "组织/管理": 4,       # 团队文化、阿米巴经营、决策流程
    "社会/政治": 4,       # 性别对立、劳资关系、殖民遗产
    "哲学/方法论": 4,     # 知识论、意识形态批判、科学哲学
    "边界/混合": 4,       # 跨领域问题——魂的exclude边缘
}

# 默认任务池（可被 --tasks 覆盖）
DEFAULT_TASKS = [
    # 技术/工程
    "评估宇树科技人形机器人从研发到量产的工程挑战和供应链瓶颈",
    "设计一个分布式系统的故障恢复机制，要求99.99%可用性",
    "分析NVIDIA在AI芯片领域的竞争优势能否持续到2028年",
    "评估Rust语言在嵌入式系统开发中的适用性和迁移成本",
    # 组织/管理
    "诊断一个技术团队中'老人把持代码review导致新人流失'的组织文化问题",
    "设计一家50人创业公司的绩效考核制度，要求激励创新而非内卷",
    "分析阿米巴经营模式在软件开发公司中的适用条件和失效风险",
    "评估远程办公对技术团队创造力的长期影响及管理对策",
    # 社会/政治
    "分析杨笠言论现象中阶级、性别、流量资本的交叉作用",
    "评估中国制造业工人在自动化转型中的处境和可能出路",
    "分析后殖民语境下非洲国家技术自主的路径和障碍",
    "评估中国性别平等政策在职场中的实际效果和结构性障碍",
    # 哲学/方法论
    "论证'知识管理系统的中立性'是否是一个可能的或可欲的目标",
    "分析AI辅助决策系统中隐性意识形态偏见的检测方法及局限",
    "评估波普尔证伪主义在社会科学中的适用边界",
    "论证'多元视角综合'在认识论上的合法性条件——何时综合是深化，何时是折中",
    # 边界/混合
    "设计一套开源社区防止大公司'掠夺性贡献'的治理机制",
    "评估技术解决方案在应对气候变化中的角色——它是否遮蔽了消费主义问题",
    "分析'效率优先'的企业文化与工会建设的兼容性",
    "论证一个工具的设计者是否有道德义务在其工具中嵌入自我批判机制",
]

def generate_task_pool(n=20, output_path=None):
    """生成实验任务池。从默认任务中随机选取 n 个，确保域分布均衡。"""
    if output_path is None:
        output_path = TASKS_FILE

    # 确保各域至少一个任务，其余随机补足
    tasks = list(DEFAULT_TASKS)
    domain_tasks = defaultdict(list)
    domain_keys = list(DOMAIN_DISTRIBUTION.keys())

    for i, task in enumerate(tasks):
        domain = domain_keys[i % len(domain_keys)]
        domain_tasks[domain].append(task)

    selected = []
    per_domain = max(1, n // len(domain_keys))
    for domain in domain_keys:
        pool = domain_tasks.get(domain, [])
        if pool:
            k = min(per_domain, len(pool))
            selected.extend(random.sample(pool, k))

    # 补足到 n
    remaining = [t for t in tasks if t not in selected]
    while len(selected) < n and remaining:
        selected.append(remaining.pop(random.randint(0, len(remaining) - 1)))

    random.shuffle(selected)
    selected = selected[:n]

    pool = {
        "generated_at": datetime.now().isoformat(),
        "total_tasks": len(selected),
        "domain_distribution": DOMAIN_DISTRIBUTION,
        "tasks": [{"id": i + 1, "domain": domain_keys[i % len(domain_keys)], "task": t}
                  for i, t in enumerate(selected)],
    }

    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(pool, f, ensure_ascii=False, indent=2)

    print(f"✅ 实验任务池已生成: {output_path}")
    print(f"   总任务数: {len(selected)}")
    for domain in domain_keys:
        count = sum(1 for t in pool["tasks"] if t["domain"] == domain)
        print(f"   {domain}: {count}")
    return output_path

def generate_condition_config(task_id, condition, tasks_path=None):
    """为特定条件生成实验配置。不同条件给出不同的 prompt 模板。"""
    if tasks_path is None:
        tasks_path = TASKS_FILE

    with open(tasks_path) as f:
        pool = json.load(f)

    task = pool["tasks"][task_id - 1]

    configs = {
        "A": {
            "description": "万民幡合议",
            "method": "match.py 预筛选 → 幡主审查 → 3魂合议 → 辩证综合官",
            "prompt_template": "使用万民幡合议模式分析以下问题：{task}",
            "constraints": [
                "必须走完整 match.py → 幡主审查 → 3魂并行 → 辩证综合官流程",
                "辩证综合官只接收文件路径，不接收内容",
                "记录每魂的 token 消耗和耗时",
            ],
        },
        "B": {
            "description": "裸AI等token预算",
            "method": "Claude直接分析，token预算 = 条件A的总token消耗",
            "prompt_template": "请分析以下问题，给出你的判断：{task}",
            "constraints": [
                "不注入任何魂的 summon_prompt",
                "token 预算等于同一任务条件A的总消耗",
                "不允许 spawn 子 agent",
            ],
        },
        "C": {
            "description": "多步推理裸AI",
            "method": "Claude 分步推理（分析→审视→综合），token预算 = 条件A的消耗，但不注入魂prompt",
            "prompt_template": (
                "请分三步分析以下问题：\n"
                "第一步：从多个可能的角度审视这个问题的关键维度\n"
                "第二步：检查第一步的分析是否存在盲区或预设偏见\n"
                "第三步：综合前两步，给出最终判断\n\n"
                "问题：{task}"
            ),
            "constraints": [
                "不注入任何魂的 summon_prompt",
                "token 预算等于同一任务条件A的总消耗",
                "三步均在单次推理中完成，不 spawn 子 agent",
            ],
        },
        "D": {
            "description": "人类专家基线",
            "method": "由领域相关的人类专家独立分析，记录输出",
            "prompt_template": "【人类专家任务】请分析以下问题：{task}",
            "constraints": [
                "专家不能是万民幡设计者或使用者",
                "专家需具备该领域的专业资质",
                "记录专家的领域背景",
            ],
        },
    }

    config = configs[condition]
    config["task_id"] = task_id
    config["condition"] = condition
    config["task"] = task["task"]
    config["domain"] = task["domain"]

    return config

def blind_review(results_dir=None):
    """盲评模式：读取所有条件的输出，去标识化后等待人工评审。

    评审维度（1-5分）：
    - 洞察深度：是否发现了非显而易见的洞见
    - 盲区识别：是否识别了自身或问题的关键盲区
    - 可操作性：建议是否具体可行
    - 逻辑严密性：推理是否自洽、无跳跃
    - 自我批判：是否包含对自身局限的诚实评估
    """
    if results_dir is None:
        results_dir = RESULTS_DIR

    results_path = Path(results_dir)
    if not results_path.exists():
        print(f"❌ 结果目录不存在: {results_dir}")
        print("   请先运行实验: python3 scripts/controlled-experiment.py run ...")
        return

    # 收集所有输出文件
    outputs = []
    for f in sorted(results_path.glob("*.json")):
        with open(f) as fp:
            outputs.append(json.load(fp))

    if not outputs:
        print("❌ 没有找到实验结果文件")
        return

    # 去标识化：为每个输出分配随机ID
    review_bundle = {
        "review_id": f"review-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "total_outputs": len(outputs),
        "scoring_dimensions": {
            "insight_depth": "洞察深度 (1-5)：是否发现了非显而易见的洞见",
            "blind_spot_detection": "盲区识别 (1-5)：是否识别了自身或问题的关键盲区",
            "actionability": "可操作性 (1-5)：建议是否具体可行",
            "logical_rigor": "逻辑严密性 (1-5)：推理是否自洽",
            "self_critique": "自我批判 (1-5)：是否包含对自身局限的诚实评估",
        },
        "items": [],
    }

    blind_ids = {}
    for i, output in enumerate(outputs):
        blind_id = f"P{i+1:03d}"
        blind_ids[blind_id] = output.get("condition", "?")
        review_bundle["items"].append({
            "blind_id": blind_id,
            "task": output.get("task", "")[:100],
            "content": output.get("content", ""),
        })

    # 保存盲评包
    bundle_path = results_path / f"blind-review-{review_bundle['review_id']}.json"
    with open(bundle_path, "w") as f:
        json.dump(review_bundle, f, ensure_ascii=False, indent=2)

    # 保存映射表（不与盲评包同文件）
    map_path = results_path / f"blind-map-{review_bundle['review_id']}.json"
    with open(map_path, "w") as f:
        json.dump({"review_id": review_bundle["review_id"], "mapping": blind_ids}, f, ensure_ascii=False, indent=2)

    print(f"✅ 盲评包已生成:")
    print(f"   盲评包: {bundle_path}")
    print(f"   映射表: {map_path} （请勿给评审者）")
    print(f"   待评审项: {len(outputs)}")
    print(f"\n评审维度:")
    for dim, desc in review_bundle["scoring_dimensions"].items():
        print(f"   {dim}: {desc}")

def compute_stats(results_dir=None, map_file=None):
    """统计分析：比较各条件的表现。"""
    if results_dir is None:
        results_dir = RESULTS_DIR

    results_path = Path(results_dir)
    if not results_path.exists():
        print(f"❌ 结果目录不存在: {results_dir}")
        return

    # 查找最新的盲评结果
    scored_files = sorted(results_path.glob("scored-*.json"))
    if not scored_files:
        print("❌ 没有找到已评分的盲评结果文件")
        print("   请先在 blind-review 生成的盲评包中填入分数，保存为 scored-{review_id}.json")
        return

    # 加载评分和映射
    # （实际使用中需人工填入分数后保存为 scored-*.json）
    with open(scored_files[-1]) as f:
        scored = json.load(f)

    # 按条件分组统计
    conditions = defaultdict(list)
    for item in scored.get("items", []):
        cond = item.get("condition", "?")
        scores = item.get("scores", {})
        total = sum(scores.values())
        conditions[cond].append({"total": total, "scores": scores, "task": item.get("task", "")})

    print("📊 实验统计\n")
    print(f"{'条件':<8} {'任务数':<8} {'总分均值':<10} {'标准差':<10}")
    print("-" * 40)

    for cond in ["A", "B", "C", "D"]:
        items = conditions.get(cond, [])
        if not items:
            print(f"{cond:<8} {0:<8} {'—':<10} {'—':<10}")
            continue
        totals = [it["total"] for it in items]
        mean = sum(totals) / len(totals)
        variance = sum((t - mean) ** 2 for t in totals) / len(totals)
        std = variance ** 0.5
        print(f"{cond:<8} {len(items):<8} {mean:<10.2f} {std:<10.2f}")

    print(f"\n🏆 最佳条件: ...")  # 需要实际数据
    print(f"\n💡 提示: 运行 python3 scripts/controlled-experiment.py stats --full 查看详细维度得分")

def main():
    parser = argparse.ArgumentParser(description="万民幡对照实验框架")
    sub = parser.add_subparsers(dest="command")

    gen = sub.add_parser("generate", help="生成实验任务池")
    gen.add_argument("--tasks", type=int, default=20, help="任务数量")
    gen.add_argument("--output", type=str, help="输出路径")

    run = sub.add_parser("run", help="执行特定条件的实验")
    run.add_argument("--task-id", type=int, required=True)
    run.add_argument("--condition", choices=["A", "B", "C", "D"], required=True)
    run.add_argument("--tasks-file", type=str, help="任务池文件路径")

    blind = sub.add_parser("blind-review", help="盲评输出")
    blind.add_argument("--results-dir", type=str, help="实验结果目录")

    stats = sub.add_parser("stats", help="统计分析")
    stats.add_argument("--results-dir", type=str, help="实验结果目录")
    stats.add_argument("--map-file", type=str, help="盲评映射表路径")
    stats.add_argument("--full", action="store_true", help="显示详细维度得分")

    args = parser.parse_args()

    if args.command == "generate":
        generate_task_pool(n=args.tasks, output_path=args.output)
    elif args.command == "run":
        config = generate_condition_config(args.task_id, args.condition, args.tasks_file)
        print(json.dumps(config, ensure_ascii=False, indent=2))
        print("\n⚠️  实验执行需手动完成——条件A/B/C需 spawn 子 agent，条件D需人类专家。")
        print("   请按上述配置执行实验，将输出保存为:")
        print(f"   {RESULTS_DIR}/task{args.task_id}-cond{args.condition}.json")
    elif args.command == "blind-review":
        blind_review(args.results_dir)
    elif args.command == "stats":
        compute_stats(args.results_dir, args.map_file)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
