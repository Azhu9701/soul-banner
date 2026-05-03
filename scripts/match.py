#!/usr/bin/env python3
"""万民幡匹配预筛选 — 关键词/场景/排除条件评分，替代幡主全量读 registry-lite

输入：任务描述
输出：首选魂 + 备选 + 排除清单 + 触发详情（JSON 或 Markdown）
用途：主 agent 将输出注入幡主审查 prompt，幡主只做判断不复述数据

用法：
  python3 scripts/match.py "任务描述"                    # Markdown 输出（给人看/给幡主）
  python3 scripts/match.py "任务描述" --json             # JSON 输出（给主 agent 解析）
  python3 scripts/match.py "任务描述" --top 5            # 返回 top-5 备选
  python3 scripts/match.py "任务描述" --no-review       # 省略 gold_review（更短上下文）
"""

import json
import math
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

from utils import load_yaml

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_PATH = os.path.join(SKILL_DIR, "registry.yaml")
SOULS_DIR = os.path.join(SKILL_DIR, "souls")

# ============================================================
# 主义主义四维结构匹配 (v2.0, 2026-05)
# ============================================================

def load_ismism_data():
    """从 ismism-data.json 加载所有魂的 ismism 数据。返回 {魂名: ismism_dict}"""
    import json as _json
    data_path = Path(SKILL_DIR) / "ismism-data.json"
    if not data_path.exists():
        return {}
    try:
        with open(data_path) as f:
            return _json.load(f)
    except Exception:
        return {}


def extract_task_structure(task_description):
    """从任务描述中启发式提取四维结构需求。

    规则式实现（无需LLM）。返回 TaskStructure:
      - required_field: int|None  主要场域
      - secondary_fields: list[int]  次要场域（互补参考）
      - required_ontology: int|None
      - required_epist: int|None
      - required_teleo: int|None
      - task_type: str          分析/对抗/建设/诊断
      - confidence: float
    """
    t = task_description

    # ===== 场域判断 =====
    # 加权：长关键词权重更高
    field_1_kw = {'做': 0.5, '建': 0.5, '设计': 1, '开发': 1, '产品': 1, '功能': 0.8,
                  '项目': 0.8, '方案': 0.8, '实施': 0.7, '落地': 0.7, '运营': 0.7,
                  '管理': 0.5, '效率': 0.5, '成本': 0.5, '培训': 0.7, '平台': 0.8,
                  '该不该做': 1.5, '要不要': 1, '怎么做': 1, '怎么解决': 1}
    field_2_kw = {'瞒和骗': 2, '虚伪': 1.5, '两面': 1, '性别': 1.5,
                  '种族': 1.5, '殖民': 1.5, '他者': 1.5, '黑暗': 1, '吃人': 2,
                  '男性女性': 1.5, '妇女': 1.5, '父权': 1.5, '二元': 1}
    field_3_kw = {'自我': 1.5, '主体性': 1.5, '焦虑': 1.5, '意义感': 1.5,
                  '存在主义': 2, '内心': 1, '体验': 0.8, '我是谁': 2}
    field_4_kw = {'矛盾': 1, '阶级': 1.5, '资本': 1.5, '革命': 1.5, '解放': 1.5,
                  '压迫': 1.5, '剥削': 1.5, '社会结构': 2, '生产方式': 2,
                  '上层建筑': 2, '取代': 0.7, '自动化取代': 1.5, '工人': 0.8}

    scores = {1: 0, 2: 0, 3: 0, 4: 0}
    for f, kws in [(1, field_1_kw), (2, field_2_kw), (3, field_3_kw), (4, field_4_kw)]:
        for kw, w in kws.items():
            if kw in t:
                scores[f] += w

    # 找主要场域和次要场域
    sorted_fields = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    required_field = sorted_fields[0][0] if sorted_fields[0][1] > 0 else 1
    # 次要场域：得分>=主要场域30%的非主要场域
    threshold = sorted_fields[0][1] * 0.3
    secondary_fields = [f for f, s in sorted_fields[1:] if s >= threshold and s > 0]
    total_score = sum(scores.values())
    field_confidence = sorted_fields[0][1] / max(total_score, 1) if total_score > 0 else 0.3

    # ===== 本体论判断 =====
    ont_kw = {
        1: {'物质': 1, '生产': 1, '经济': 1, '资源': 0.8, '成本': 0.8, '工厂': 1,
            '工人': 1.2, '劳动': 1.2, '实际': 0.5, '现实': 0.5},
        2: {'理念': 1.2, '精神': 0.8, '审美': 1, '品味': 1.2, '理想': 1, '道德': 1,
            '意义': 0.5, '愿景': 1, '使命': 0.8},
        3: {'生命': 1.5, '体验': 1, '快乐': 1.2, '情绪': 1, '焦虑': 1.2, '存在': 0.7,
            '活力': 1, '热情': 1},
        4: {'符号': 1.2, '建构': 1.2, '话语': 1.2, '叙事': 1, '品牌': 0.8, '身份': 1,
            '性别角色': 1.5, '标签': 0.8}
    }
    ont_scores = {}
    for v, kws in ont_kw.items():
        ont_scores[v] = sum(w for kw, w in kws.items() if kw in t)
    required_ontology = max(ont_scores, key=ont_scores.get) if max(ont_scores.values()) > 0 else 1

    # ===== 认识论判断 =====
    epist_kw = {
        1: {'数据': 1, '测试': 1, '实验': 1, '验证': 1, '看见': 0.5, '核算': 1.2,
            '观察': 0.8, '调研': 0.8, '事实': 0.7, '衡量': 1, '指标': 0.8},
        2: {'推导': 1.2, '逻辑': 1, '原理': 1.2, '推理': 1.2, '论证': 1, '体系': 0.5,
            '框架': 0.5, '分析': 0.3},
        3: {'直觉': 1.5, '品味': 1.5, '感觉': 0.8, '体悟': 1.5, '洞察': 1.2,
            '灵感': 1.2, '顿悟': 2},
        4: {'矛盾': 0.7, '辩证': 1.5, '扬弃': 2, '否定之否定': 2, '统一': 0.5,
            '张力': 0.8, '冲突': 0.5, '对立': 0.7, '转化': 0.8}
    }
    epist_scores = {}
    for v, kws in epist_kw.items():
        epist_scores[v] = sum(w for kw, w in kws.items() if kw in t)
    required_epist = max(epist_scores, key=epist_scores.get) if max(epist_scores.values()) > 0 else 1

    # 目的论判断
    teleo_kw = {
        1: {'维持': 1.5, '保持': 1, '稳定': 1.2, '持续': 0.8, '精进': 1.5, '守护': 1.5,
            '传承': 1.2},
        2: {'改良': 1.5, '改进': 1, '优化': 1, '升级': 0.8, '提升': 0.8, '设计': 0.6,
            '方案': 0.5, '产品': 0.5, '平台': 0.5},
        3: {'解放': 2, '革命': 2, '改变世界': 2, '打破': 1.2, '赋能': 1.2, '变革': 1.5,
            '颠覆': 1.2},
        4: {'消解': 2, '放下': 1.5, '超越': 0.7, '虚无': 2, '无所谓': 1.5, '无意义': 2}
    }
    teleo_scores = {}
    for v, kws in teleo_kw.items():
        teleo_scores[v] = sum(w for kw, w in kws.items() if kw in t)
    required_teleo = max(teleo_scores, key=teleo_scores.get) if max(teleo_scores.values()) > 0 else 2

    # ===== 任务类型 =====
    if any(kw in t for kw in ['驳斥', '对抗', '辩论', '反驳', '批判']):
        task_type = "对抗"
    elif any(kw in t for kw in ['设计', '开发', '方案', '产品', '项目', '怎么解决', '怎么做',
                                 '该不该', '要不要', '建一个', '做一个']):
        task_type = "建设"
    elif any(kw in t for kw in ['诊断', '本质是什么', '根本原因', '根源']):
        task_type = "诊断"
    else:
        task_type = "分析"

    return {
        "required_field": required_field,
        "secondary_fields": secondary_fields,
        "required_ontology": required_ontology,
        "required_epist": required_epist,
        "required_teleo": required_teleo,
        "task_type": task_type,
        "confidence": round(field_confidence, 2),
    }


def structural_match(task_struct, ismism_data, all_soul_names, task_desc=""):
    """基于目录 compat/incompat 的结构匹配（v3.0 — 放弃坐标算术，改用目录标注）。

    每个魂的 ismism-data.json 中 compat/incompat 标注了该魂可处理的任务场域。
    标注基于未明子原版主义主义目录——不是从四维坐标推导的。"""
    results = {}
    req_f = task_struct["required_field"]
    secondary_fs = task_struct.get("secondary_fields", [])
    task_conf = task_struct.get("confidence", 0.5)

    CONTENT_ANCHORS = {
        "稻盛和夫": ["阿米巴", "单位时间核算", "经营十二条", "六项精进", "敬天爱人"],
        "马克思": ["剩余价值", "资本论", "历史唯物主义", "唯物史观"],
        "费曼": ["费曼学习法"],
        "庄子": ["齐物", "逍遥", "心斋", "坐忘"],
        "毛泽东": ["矛盾论", "实践论", "群众路线"],
        "黑格尔": ["绝对精神", "精神现象学", "扬弃"],
        "列宁": ["帝国主义论", "先锋队"],
        "未明子": ["主义主义", "意识形态批判", "蛇皮"],
    }

    for name in all_soul_names:
        ism = ismism_data.get(name)
        if not ism:
            results[name] = {"composite": 0.5, "field_compat": 0.3,
                           "redundancy_flag": False, "blindspot_flag": False,
                           "incompat_flag": False, "tags": ["未标注"],
                           "code": "?", "catalog_match": "", "match_quality": ""}
            continue

        compat = ism.get("compat", [])
        incompat = ism.get("incompat", [])

        # 内容锚定：魂的核心概念出现在任务中 → 全兼容
        anchor_bonus = 0
        for aname, anchors in CONTENT_ANCHORS.items():
            if name == aname and any(a in task_desc for a in anchors):
                anchor_bonus = 1.0
                break

        # 场域兼容性：只看目录 compat/incompat，不做坐标算术
        if anchor_bonus:
            fc = 1.0
        elif req_f in compat:
            fc = 1.0
        elif any(sf in compat for sf in secondary_fs):
            fc = 0.7
        elif req_f in incompat:
            fc = -0.3
        else:
            fc = 0.3

        composite = max(fc, 0)
        incompat_flag = fc < 0
        if incompat_flag:
            composite *= 0.3

        # 场景加成（实务经验——不是主义主义坐标）
        edu_bonus = 0
        if any(kw in task_desc for kw in ['培训','教','学习','讲给','教育','扫盲']):
            if name in ['费曼','Karpathy']: edu_bonus = 0.05
        scene_bonus = 0
        if any(kw in task_desc for kw in ['工厂','工人','车间','制造业','产线','劳动','用工']):
            if name == '祝鹤槐': scene_bonus = 0.06
            elif name == '稻盛和夫': scene_bonus = 0.04

        composite += edu_bonus + scene_bonus

        tags = []
        if fc >= 0.7: tags.append("场域兼容")
        elif fc >= 0.3: tags.append("场域弱相关")
        elif fc >= 0: tags.append("场域互补")
        else: tags.append("场域不兼容")
        if edu_bonus > 0: tags.append("教育加成")
        if scene_bonus > 0: tags.append("场景加成")
        if anchor_bonus > 0: tags.append("内容锚定")

        results[name] = {
            "composite": round(composite, 3),
            "field_compat": fc,
            "redundancy_flag": False,
            "blindspot_flag": False,
            "incompat_flag": incompat_flag,
            "tags": tags,
            "code": ism.get("code", "?"),
            "catalog_match": ism.get("catalog_match", ""),
            "match_quality": ism.get("match_quality", ""),
        }

    # 冗余检测：同 code 标记
    code_groups = defaultdict(list)
    for name, r in results.items():
        code_groups[r.get("code", "?")].append(name)
    for code, names in code_groups.items():
        if len(names) > 1 and code != "?":
            best = max(names, key=lambda n: results[n]["composite"])
            for n in names:
                if n != best:
                    results[n]["redundancy_flag"] = True
                    results[n]["tags"].append(f"冗余→{best}")

    # 盲区互补：不同 compat 场域 + 结构分>0.4
    top_names = sorted(results, key=lambda n: results[n]["composite"], reverse=True)[:8]
    top_compat_sets = set()
    for n in top_names:
        for f in ismism_data.get(n, {}).get("compat", []):
            top_compat_sets.add(f)
    for n in results:
        soul_compat = set(ismism_data.get(n, {}).get("compat", []))
        if results[n]["composite"] > 0.4 and soul_compat and not (soul_compat & top_compat_sets):
            results[n]["blindspot_flag"] = True
            results[n]["tags"].append("盲区互补")

    return results


def fusion(surface_scores, structural_scores, task_type):
    """融合表层和结构分。权重按任务类型调整。"""
    weights = {"分析": (0.4, 0.6), "对抗": (0.2, 0.8), "建设": (0.3, 0.7), "诊断": (0.5, 0.5)}
    ws, wd = weights.get(task_type, (0.4, 0.6))

    final = {}
    for name in surface_scores:
        s = surface_scores.get(name, 0)
        d = structural_scores.get(name, {}).get("composite", 0.5)
        final[name] = round(s * ws + d * wd, 3)
    return final

def tokenize(text):
    """词级分词：提取中文词汇和英文单词。

    中文部分使用简洁的规则分词——按常见后缀切分 + 双字词 + 三字词。
    不再使用盲目的 n-gram（假阳性太高，如"异化在"匹配"异化"会导致噪声）。
    """
    tokens = set()
    text_lower = text.lower()
    tokens.add(text_lower)  # 全文精确匹配

    # 英文/数字词
    eng = re.findall(r'[a-zA-Z0-9]+', text)
    for w in eng:
        tokens.add(w.lower())

    # 中文：提取连续中文字符段
    chinese_segments = re.findall(r'[一-鿿]+', text)
    for seg in chinese_segments:
        seg_len = len(seg)
        # 双字词
        for i in range(seg_len - 1):
            tokens.add(seg[i:i+2])
        # 三字词
        for i in range(seg_len - 2):
            tokens.add(seg[i:i+3])
        # 四字词
        for i in range(seg_len - 3):
            tokens.add(seg[i:i+4])
        # 保留完整段
        tokens.add(seg)

    return tokens


# 低区分度双字词（在所有领域的魂关键词中高频出现，匹配价值低）
STOP_BIGRAMS = {
    '分析', '主义', '批判', '理论', '哲学', '制度', '组织', '建设',
    '战略', '决策', '设计', '系统', '技术', '管理', '研究', '方法',
    '实践', '科学', '思维', '认识', '社会', '革命', '政治', '经济',
    '文学', '精神', '知识', '学习', '传播', '教育', '文化', '历史',
    '领域', '发展', '结构', '体系', '关系', '问题', '能力', '创新',
}


def keyword_overlap(task_text, keyword_text, all_soul_keywords=None):
    """计算任务与关键词列表的重叠度。使用子串匹配。

    关键词匹配只使用子串精确匹配——关键词作为子串出现在任务文本中才算命中。
    n-gram 交集不上浮（假阳性太高，如"一人公司"因"公司"交集而假匹配）。
    """
    if not keyword_text:
        return [], 0.0

    task_lower = task_text.lower()
    keywords = [k.strip() for k in re.split(r'[、,，/]', keyword_text) if k.strip()]
    matched = []
    matched_score = 0

    for kw in keywords:
        kw_lower = kw.lower()
        kw_len = len(kw)

        # 关键词区分度权重
        kw_bigrams = {kw[i:i+2] for i in range(kw_len - 1)} if kw_len >= 2 else set()
        has_stop = bool(kw_bigrams & STOP_BIGRAMS)
        is_high_specificity = kw_len >= 3 and not has_stop
        is_noisy = kw_len <= 2 and has_stop

        if is_noisy:
            kw_weight = 0.15
        elif has_stop and kw_len <= 2:
            kw_weight = 0.2
        elif has_stop:
            kw_weight = 0.5
        elif is_high_specificity:
            kw_weight = 2.0
        elif kw_len >= 3:
            kw_weight = 1.0
        elif kw_len == 2:
            kw_weight = 0.8   # 双字非停用词（如"异化""齐物""坐忘"），有区分度
        else:
            kw_weight = 0.4

        # 子串精确匹配
        if kw_lower in task_lower:
            matched.append(kw)
            matched_score += kw_weight

    score = min(matched_score / 3.0, 1.0)
    return matched, score

def exclude_check(task_lower, exclude_text):
    """检查排除条件是否触发。两级排除：
    - hard: 排除词精确命中任务核心（子串匹配 + 词长>=3）→ ×0.1
    - soft: 模糊匹配或短词匹配 → ×0.5
    """
    if not exclude_text:
        return [], "none"

    excludes = [e.strip() for e in re.split(r'[、,，/]', exclude_text) if e.strip()]
    hard_triggered = []
    soft_triggered = []
    task_tokens_lower = set(t.lower() for t in tokenize(task_lower))

    for ex in excludes:
        ex_lower = ex.lower()
        ex_tokens = tokenize(ex_lower)
        ex_len = len(ex)

        # 精确子串匹配——是核心排除信号
        if ex_lower in task_lower:
            # 长词精确命中 = hard（如"纯财务会计准则合规"命中任务）
            if ex_len >= 4:
                hard_triggered.append(ex)
            # 中词精确命中 = hard，除非是明显的附属提及
            elif ex_len >= 3:
                # 检查排除词是否在任务中处于附属位置（括号内、"包括"/"如"/"除"后）
                idx = task_lower.find(ex_lower)
                context_before = task_lower[max(0, idx - 10):idx]
                is_subordinate = any(marker in context_before for marker in ['包括', '例如', '比如', '除了', '除', '附带', '此外', '以及'])
                if is_subordinate:
                    soft_triggered.append(f"{ex}~")
                else:
                    hard_triggered.append(ex)
            else:
                # 2字词精确命中 → soft（短词太容易误伤）
                soft_triggered.append(f"{ex}~")
            continue

        # 模糊匹配（token overlap >= 50%）→ soft
        if len(ex_tokens) >= 2:
            overlap = ex_tokens & task_tokens_lower
            if len(overlap) >= len(ex_tokens) * 0.5:
                soft_triggered.append(f"{ex}?")

    # 返回最高风险级别
    all_triggered = hard_triggered + soft_triggered
    if hard_triggered:
        return all_triggered, "hard"
    elif soft_triggered:
        return all_triggered, "soft"
    return [], "none"

def score_soul(soul, task):
    """对单个魂评分，返回 (score, details)"""
    task_lower = task.lower()
    task_tokens = tokenize(task)
    task_tokens_lower = {t.lower() for t in task_tokens}

    details = {}

    # 1. 关键词匹配（直接传递任务文本，支持子串匹配）
    kw_text = soul.get("trigger_keywords_summary", "")
    kw_matched, kw_score = keyword_overlap(task, kw_text)
    details["keyword_matches"] = kw_matched
    details["keyword_score"] = kw_score

    # 2. 场景匹配
    sc_text = soul.get("trigger_scenarios_summary", "")
    sc_matched, sc_score = keyword_overlap(task, sc_text)
    details["scenario_matches"] = sc_matched
    details["scenario_score"] = sc_score

    # 3. 排除检查
    ex_text = soul.get("trigger_exclude_summary", "")
    ex_triggered, ex_risk = exclude_check(task_lower, ex_text)
    details["exclude_triggered"] = ex_triggered
    details["exclude_risk"] = ex_risk

    # 4. 领域加分（直接子串匹配）
    domains = soul.get("domain", [])
    domain_bonus = 0
    for d in domains:
        if d in task:
            domain_bonus += 0.05
            if "domain_matches" not in details:
                details["domain_matches"] = []
            details["domain_matches"].append(d)
    details["domain_bonus"] = min(domain_bonus, 0.2)

    # 综合评分
    score = (
        kw_score * 0.5 +
        sc_score * 0.3 +
        details["domain_bonus"]
    )

    # 排除惩罚（两级）
    if ex_risk == "hard":
        score *= 0.1
    elif ex_risk == "soft":
        score *= 0.5

    return min(score, 1.0), details


def load_usage_counts(registry_path):
    """从 call-records.yaml 加载每个魂的使用次数。文件不存在则返回空 dict。"""
    import os as _os
    records_path = _os.path.join(_os.path.dirname(registry_path), "call-records.yaml")
    if not _os.path.exists(records_path):
        return {}
    try:
        records = load_yaml(records_path)
    except Exception:
        return {}
    counts = {}
    for entry in records if isinstance(records, list) else records.get("召唤记录", []):
        soul = entry.get("魂名") or entry.get("soul") or entry.get("魂", "")
        if soul:
            counts[soul] = counts.get(soul, 0) + 1
    return counts


def apply_cognitive_distance(scored_results, usage_counts):
    """认知距离调整：使用越频繁的魂轻微降权，优先推荐使用者较少接触的魂。

    公式：freshness = 1.0 / (1 + ln(usage + 1))，归一化到 [-0.05, +0.05]
    使用 0 次的魂 +0.05，使用 20+ 次的魂 -0.05。
    这不是品质评分——是反消费机制：强迫使用者接触陌生框架。
    """
    import math
    if not usage_counts:
        return scored_results

    freshness_scores = {}
    for r in scored_results:
        usage = usage_counts.get(r["name"], 0)
        freshness = 1.0 / (1 + math.log(usage + 1))
        freshness_scores[r["name"]] = freshness

    if not freshness_scores:
        return scored_results

    vals = list(freshness_scores.values())
    min_v, max_v = min(vals), max(vals)
    if max_v == min_v:
        return scored_results

    for r in scored_results:
        f = freshness_scores.get(r["name"], 0.5)
        # 归一化到 [-0.05, +0.05]
        normalized = (f - min_v) / (max_v - min_v) * 0.10 - 0.05
        r["score"] = min(round(r["score"] + normalized, 3), 1.0)
        r["freshness_bonus"] = round(normalized, 3)

    return scored_results

def _fmt_func_domains(entry):
    doms = entry.get('function_domains', [])
    return '+'.join(doms) if isinstance(doms, list) else str(doms)


def format_output(results, task, task_struct=None, structural_scores=None,
                   show_gold_review=True):
    """生成 Markdown 格式输出（给幡主审查用）"""
    lines = []
    lines.append(f"## 匹配预筛选\n")
    lines.append(f"**任务**: {task}\n")

    # 任务结构需求
    if task_struct:
        ts = task_struct
        lines.append(f"**四维需求**: 场域{ts['required_field']} 本体{ts['required_ontology']} "
                     f"认识{ts['required_epist']} 目的{ts['required_teleo']} "
                     f"({ts['task_type']}型, 信度{ts['confidence']:.0%})")
        lines.append("")

    primary = results[0] if results else None
    alternatives = results[1:] if len(results) > 1 else []

    if primary:
        p = primary
        func_str = _fmt_func_domains(p)
        struct = p.get("structural", {})
        code = struct.get("code", "?")
        tags_str = " ".join(struct.get("tags", []))
        lines.append("### 首选\n")
        lines.append(f"**{p['name']}** `{code}` — 表层{p.get('score',0):.2f} + 结构{struct.get('composite',0):.2f} → **{p.get('final_score',p['score']):.2f}** {tags_str}")
        lines.append(f"- 功能域: {func_str} | 信息充分度: {p.get('info_sufficiency', '?')} | 方法论: {p.get('methodology_transferability', '?')}")
        lines.append(f"- 触发关键词: {', '.join(p['keyword_matches'][:8]) or '无'}")
        risk_label = {"none":"无","soft":"软排除","hard":"硬排除"}.get(p['exclude_risk'], p['exclude_risk'])
        lines.append(f"- 排除风险: {risk_label}")
        if struct and struct.get("catalog_match"):
            lines.append(f"- 目录: {struct['catalog_match'][:80]}")
        if struct and struct.get("match_quality"):
            lines.append(f"- 匹配质量: {struct['match_quality']}")
        lines.append("")

    if alternatives:
        lines.append("### 备选\n")
        for i, a in enumerate(alternatives[:8]):
            func_str = _fmt_func_domains(a)
            struct = a.get("structural", {})
            code = struct.get("code", "?")
            tags_str = " ".join(struct.get("tags", []))
            kw_str = ', '.join(a['keyword_matches'][:4]) or '无关键词命中'
            extra = f" [{struct.get('match_quality','')}]" if struct.get('match_quality') else ""
            lines.append(f"{i+1}. **{a['name']}** `{code}`{extra} — {a.get('final_score',a['score']):.2f} "
                         f"[表层{a['score']:.2f}+结构{struct.get('composite',0):.2f}] "
                         f"{tags_str} | {kw_str}")
        lines.append("")

    # 结构分析摘要
    if structural_scores:
        incompat = [n for n, s in structural_scores.items() if s.get("incompat_flag")]
        redundant = [n for n, s in structural_scores.items() if s.get("redundancy_flag")]
        blindspots = [n for n, s in structural_scores.items() if s.get("blindspot_flag")]
        gap_souls = [(n, s) for n, s in structural_scores.items() if s.get("epist_gap")]

        # 合议建议：首选魂有认识缺口 → 推荐合议
        if primary and primary.get("structural", {}).get("epist_gap"):
            blind_candidates = [n for n, s in structural_scores.items()
                              if s.get("composite", 0) > 0.5 and not s.get("incompat_flag")
                              and s.get("epist_match", 0) >= 0.7 and n != primary['name']]
            edu_souls = ['费曼', 'Karpathy']
            edu_hits = [n for n in edu_souls if n not in blind_candidates and structural_scores.get(n, {}).get("composite", 0) > 0.3]
            lines.append("### ⚠️ 合议建议\n")
            lines.append(f"- 首选魂**{primary['name']}**存在认识缺口（任务需认识{task_struct['required_epist']} vs 魂认识不匹配）")
            if blind_candidates:
                lines.append(f"- 推荐至少搭配一个认识匹配魂: {', '.join(blind_candidates[:3])}")
            if edu_hits:
                lines.append(f"- 可加教育传播位: {', '.join(edu_hits)}")
            lines.append("")

        if incompat or redundant or blindspots:
            lines.append("### 结构提示\n")
            if incompat:
                lines.append(f"- 🔴 场域不兼容: {', '.join(incompat[:5])}")
            if redundant:
                lines.append(f"- ⚠️  冗余协同: {', '.join(redundant[:5])}")
            if blindspots:
                lines.append(f"- 🔵 盲区互补: {', '.join(blindspots[:5])}")
            lines.append("")

    # 排除清单
    hard_exclude = [r for r in results if r["exclude_risk"] == "hard"]
    soft_exclude = [r for r in results if r["exclude_risk"] == "soft"]
    if hard_exclude:
        lines.append("### 硬排除预警\n")
        for e in hard_exclude:
            lines.append(f"- **{e['name']}**: {', '.join(e['exclude_triggered'][:5])}")
        lines.append("")
    if soft_exclude:
        lines.append("### 软排除提示\n")
        for e in soft_exclude:
            lines.append(f"- **{e['name']}** (×0.5): {', '.join(e['exclude_triggered'][:5])}")
        lines.append("")

    lines.append("### 幡主审查清单\n")
    lines.append("请逐条回答（每条一句话）：")
    lines.append("1. **领域匹配**: 首选魂的领域是否覆盖此任务？[Y/N]")
    lines.append("2. **排除风险**: 排除条件是否实质性触发？[Y/N + 哪个]")
    lines.append("3. **边界风险**: 适用边界外溢风险？[无/低/中/高 + 简述]")
    lines.append("4. **结构审查**: 首选魂的场域/本体/认识/目的与任务是否兼容？冗余/盲区/不兼容需标注")
    lines.append("5. **裁决**: [通过 / 换X / 加Y约束 / 需第二审查官]")

    return "\n".join(lines)

def main():
    args = sys.argv[1:]
    if not args:
        print("用法: python3 scripts/match.py '任务描述' [--json] [--top N] [--no-review] [--no-struct]")
        sys.exit(1)

    task = args[0]
    as_json = "--json" in args
    no_struct = "--no-struct" in args
    top_n = 5
    show_gold = "--no-review" not in args

    for i, a in enumerate(args):
        if a == "--top" and i + 1 < len(args):
            top_n = int(args[i + 1])

    # 加载 registry
    registry = load_yaml(REGISTRY_PATH)
    souls = registry.get("魂魄", [])

    # 过滤已散魂
    active_souls = [s for s in souls if s.get("status") != "dismissed"]

    # ===== 第一层：表层匹配 =====
    scored = []
    for soul in active_souls:
        score, details = score_soul(soul, task)
        if score > 0 or details["exclude_risk"] in ("hard", "soft"):
            scored.append({
                "name": soul.get("name", ""),
                "info_sufficiency": soul.get("info_sufficiency", "?"),
                "function_domains": soul.get("function_domains", []),
                "methodology_transferability": soul.get("methodology_transferability", "?"),
                "domain": soul.get("domain", []),
                "gold_review": soul.get("gold_review", "") if show_gold else "",
                "score": round(score, 3),
                **{f"match_{k}": v for k, v in details.items()},
                **details,
            })

    # 认知距离调整
    usage_counts = load_usage_counts(REGISTRY_PATH)
    scored = apply_cognitive_distance(scored, usage_counts)

    # ===== 第二层：四维结构匹配 =====
    ismism_data = load_ismism_data()
    task_struct = extract_task_structure(task)
    surface_scores = {r["name"]: r["score"] for r in scored}

    if not no_struct:
        structural_scores = structural_match(task_struct, ismism_data,
                                             [s["name"] for s in active_souls],
                                             task_desc=task)
        final_scores = fusion(surface_scores, structural_scores,
                              task_struct.get("task_type", "分析"))
    else:
        structural_scores = {}
        final_scores = surface_scores.copy()

    # 注入结构和最终分
    for r in scored:
        name = r["name"]
        r["structural"] = structural_scores.get(name, {})
        r["final_score"] = final_scores.get(name, r["score"])

    # 按最终分排序
    risk_order = {"none": 0, "soft": 1, "hard": 2}
    scored.sort(key=lambda x: (
        risk_order.get(x["exclude_risk"], 0),
        -x["final_score"]
    ))
    top_results = scored[:top_n]

    # JSON 输出
    if as_json:
        output = {
            "task": task,
            "total_souls": len(active_souls),
            "task_structure": task_struct,
            "primary": top_results[0] if top_results else None,
            "alternatives": top_results[1:] if len(top_results) > 1 else [],
            "all_scored": [{k: v for k, v in r.items()
                           if k not in ("gold_review",)} for r in scored],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2, default=str))
    else:
        print(format_output(top_results, task, task_struct, structural_scores,
                           show_gold_review=show_gold))


if __name__ == "__main__":
    main()
