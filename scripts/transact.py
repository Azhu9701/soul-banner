#!/usr/bin/env python3
"""万民幡事务脚本 — 封装所有落盘操作，主 agent 只需调子命令

子命令：
  refine-close     炼化完成后落盘（validate → agent → obsidian → registry → lite → 校验）
  review-apply     审查/互审完成后落盘（gold_review → 审查记录 → lite → 校验）
  possession-close 附体结束后落盘（call-records → audit → obsidian → lite → 校验）
  dismiss          散魂（归档YAML → 标记registry → lite → 校验）
  task-save        持久化 Task 到 state.json（跨会话恢复）
  task-restore     从 state.json 恢复 pending Task
  meeting-prep     会前准备（扫描失败条件 → 待办 → 输出议程模板）
  sync-all         全量同步（lite → agent --all → 校验 → 健康检查）

用法：
  python3 scripts/transact.py <subcommand> [options]

设计原则：
  - 只做落盘，不做判断。评级/裁决/匹配由主 agent 完成后再调用。
  - 幂等：重复执行安全。
  - 失败不静默：每个步骤的异常都报告，但后续步骤继续执行（best-effort）。
"""

import glob
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

from utils import load_yaml, save_yaml, run_cmd

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SKILL_DIR)
SCRIPTS_DIR = os.path.join(SKILL_DIR, "scripts")
sys.path.insert(0, SCRIPTS_DIR)
REGISTRY_PATH = os.path.join(SKILL_DIR, "registry.yaml")
REGISTRY_LITE_PATH = os.path.join(SKILL_DIR, "registry-lite.yaml")
CALL_RECORDS_PATH = os.path.join(SKILL_DIR, "call-records.yaml")
STATE_PATH = os.path.join(SKILL_DIR, "committee", "state.json")
FAILURE_CONDITIONS_PATH = os.path.join(SKILL_DIR, "committee", "failure-conditions.md")
REVIEWS_DIR = os.path.join(SKILL_DIR, "reviews")
SOULS_DIR = os.path.join(SKILL_DIR, "souls")
ARCHIVE_DIR = os.path.join(SKILL_DIR, "archive", "dismissed")
MEETINGS_DIR = os.path.join(SKILL_DIR, "committee", "meetings")
OBSIDIAN_VAULT = os.environ.get("OBSIDIAN_VAULT", os.path.expanduser("~/ob"))

# -- 导入同目录脚本（避免子进程开销，共享已加载的 YAML） --
import importlib.util as _importlib_util

def _import_script(name):
    """导入 scripts/ 下的脚本模块（支持带连字符的文件名）。"""
    filepath = os.path.join(SCRIPTS_DIR, name)
    mod_name = name.replace("-", "_").replace(".py", "")
    spec = _importlib_util.spec_from_file_location(mod_name, filepath)
    mod = _importlib_util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_cross_validate = _import_script("cross-validate.py")
_registry_lite = _import_script("generate-registry-lite.py")
_handbook = _import_script("generate-handbook.py")

check_cross_validate = _cross_validate.check
generate_registry_lite_data = _registry_lite.generate
generate_handbook = _handbook.generate_handbook

def load_json(path):
    with open(path) as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def today_str():
    return datetime.now().strftime("%Y-%m-%d")

# -- section dividers --

def regenerate_lite():
    """重新生成 registry-lite.yaml（仅在 registry.yaml 更新后）"""
    if os.path.exists(REGISTRY_LITE_PATH) and os.path.exists(REGISTRY_PATH):
        if os.path.getmtime(REGISTRY_LITE_PATH) >= os.path.getmtime(REGISTRY_PATH):
            return True
    try:
        lite = generate_registry_lite_data(Path(REGISTRY_PATH))
        import yaml
        yaml_str = yaml.dump(lite, allow_unicode=True, default_flow_style=False, sort_keys=False)
        header = f"# 自动生成于 {datetime.now().isoformat()}\n# 匹配审查速查表 — 只读，勿手动编辑\n\n"
        with open(REGISTRY_LITE_PATH, "w") as f:
            f.write(header + yaml_str)
        print(f"  ✅ registry-lite.yaml 已更新 ({len(lite['魂魄'])} 魂)")
        return True
    except Exception as e:
        print(f"  ⚠ 重生成 registry-lite.yaml 失败: {e}")
        return False

def cross_validate(fix=False):
    """运行交叉校验，有错误则自动修复后重新校验"""
    try:
        ok = check_cross_validate(fix=fix)
        if ok:
            print("  ✅ 交叉校验通过")
            return True
        elif fix:
            # fix=True 时 check 内部已修复，再校验一次确认
            print("  ⚠ 自动修复后重新校验...")
            ok2 = check_cross_validate(fix=False)
            if ok2:
                print("  ✅ 修复后交叉校验通过")
            return ok2
        else:
            print("  ⚠ 交叉校验有错误（未修复）")
            return False
    except Exception as e:
        print(f"  ⚠ 交叉校验异常: {e}")
        return False

def health_check():
    """快速健康检查"""
    return cross_validate(fix=False)

# ══════════════════════════════════════════════════════════════════
# 子命令实现
# ══════════════════════════════════════════════════════════════════

def cmd_refine_close(soul_name):
    """炼化完成后：校验 → 同步 agent → 同步 Obsidian → 写 registry → 同步 lite → 交叉校验"""
    yaml_path = os.path.join(SOULS_DIR, f"{soul_name}.yaml")
    if not os.path.exists(yaml_path):
        print(f"❌ 魂魄文件不存在: {yaml_path}")
        return 1

    print(f"🏗 炼化落盘: {soul_name}")

    # 1. 格式校验
    print("\n[1/5] 格式校验...")
    try:
        from refine import validate_soul
        r = validate_soul(yaml_path)
        print(f"  valid={r['valid']} errors={len(r.get('errors',[]))} warnings={len(r.get('warnings',[]))}")
        if r.get('errors'):
            for e in r['errors']:
                print(f"  ❌ {e}")
        if not r['valid']:
            print("❌ 校验不通过，中止落盘。请修复错误后重试。")
            return 1
        if r.get('warnings'):
            for w in r['warnings']:
                print(f"  ⚠ {w}")
    except ImportError:
        print("  ⚠ 无法导入 refine 模块，跳过校验")

    # 2. 同步 agent 文件
    print("\n[2/5] 同步 agent 文件...")
    run_cmd(f"python3 {SCRIPTS_DIR}/sync-agent.py {yaml_path}", "sync-agent")

    # 3. 同步 Obsidian
    print("\n[3/5] 同步 Obsidian...")
    try:
        from refine import sync_soul_to_obsidian
        sync_soul_to_obsidian(yaml_path)
        print("  ✅ Obsidian 已同步")
    except ImportError:
        print("  ⚠ 无法导入 refine 模块，跳过 Obsidian 同步")
    except Exception as e:
        print(f"  ⚠ Obsidian 同步失败: {e}")

    # 4. 确保 registry 中有该魂
    print("\n[4/5] 更新 registry...")
    registry = load_yaml(REGISTRY_PATH)
    souls = registry.get("魂魄", [])
    existing = [s for s in souls if s.get("name") == soul_name]
    if not existing:
        soul_data = load_yaml(yaml_path)
        soul_data.pop("召唤记录", None)
        # 从结构化 trigger 提取 summary 字符串（registry 用 summary 做匹配，魂 YAML 用结构化格式）
        trigger = soul_data.pop("trigger", None)
        if trigger and isinstance(trigger, dict):
            soul_data["trigger_keywords_summary"] = ", ".join(trigger.get("keywords", []))
            soul_data["trigger_scenarios_summary"] = ", ".join(trigger.get("scenarios", []))
            soul_data["trigger_exclude_summary"] = ", ".join(trigger.get("exclude", []))
        souls.append(soul_data)
        registry["魂魄"] = souls
        registry["更新时间"] = today_str()
        save_yaml(REGISTRY_PATH, registry)
        print(f"  ✅ {soul_name} 已写入 registry.yaml")
    else:
        print(f"  · {soul_name} 已在 registry 中，跳过添加")

    # 5. 重生成 lite + 交叉校验
    print("\n[5/5] 同步与校验...")
    regenerate_lite()
    cross_validate()

    print(f"\n✅ 炼化落盘完成: {soul_name}")
    print("   → humanizer: 若 Soul Profile 尚未经 humanizer 处理，请手动调用 Skill(\"humanizer\")")
    print("   → graphify: 审查完成后调用 transact.py review-apply")
    return 0

def cmd_review_apply(soul_name, review_file, verdict=None, reviewer=None):
    """审查/互审完成后：更新 gold_review → 追加审查记录 → 更新 committee state → 同步 lite → 交叉校验"""
    if not os.path.exists(review_file):
        print(f"❌ 审查报告不存在: {review_file}")
        return 1

    print(f"📋 审查落盘: {soul_name} ← {review_file}")

    # 1. 读取审查报告提取关键信息
    print("\n[1/5] 更新 registry gold_review...")
    registry = load_yaml(REGISTRY_PATH)
    souls = registry.get("魂魄", [])

    target = None
    for s in souls:
        if s.get("name") == soul_name:
            target = s
            break

    if not target:
        print(f"❌ {soul_name} 不在 registry 中")
        return 1

    review_filename = os.path.basename(review_file)
    review_rel_path = os.path.relpath(review_file, SKILL_DIR)

    # 更新 gold_review
    if verdict:
        target["gold_review"] = verdict

    # 追加审查记录
    if "审查记录" not in target:
        target["审查记录"] = []
    review_record = {
        "审查官": reviewer or "见审查报告",
        "日期": today_str(),
        "报告": review_rel_path,
    }
    if verdict:
        review_record["裁定"] = verdict
    target["审查记录"].append(review_record)

    registry["魂魄"] = souls
    registry["更新时间"] = today_str()
    save_yaml(REGISTRY_PATH, registry)
    print(f"  ✅ {soul_name} gold_review + 审查记录 已更新")

    # 2. 更新 committee state
    print("\n[2/5] 更新 committee state...")
    if os.path.exists(STATE_PATH):
        state = load_json(STATE_PATH)
        updated = False
        verdict_lower = (verdict or "").lower()

        # 任何非空裁定都应触发更新，不限于包含"裁定"/"散魂"字面
        if verdict:
            # 更新 verification_conditions 中与该魂相关的条目
            for key in list(state.get("verification_conditions", {}).keys()):
                if soul_name in key:
                    state["verification_conditions"][key] = f"✅ {today_str()} — {verdict[:80]}"
                    updated = True

            # 更新 pending_tasks 中与该魂审查相关的待办
            pending = state.get("pending_tasks", [])
            for task in pending:
                if task.get("status") in ("已完成",):
                    continue
                task_text = (task.get("name", "") + task.get("描述", "")).lower()
                if soul_name.lower() in task_text and any(
                    kw in task_text for kw in ["审查", "入幡", "review", "炼化"]
                ):
                    task["status"] = "已完成"
                    task["完成日期"] = today_str()
                    task["产出"] = f"审查报告: {review_rel_path}" + (f" — {verdict[:60]}" if verdict else "")
                    task["上次更新"] = today_str()
                    updated = True
                    print(f"  ✅ pending_task [{task['id']}] → 已完成")

            if updated:
                save_json(STATE_PATH, state)
                print(f"  ✅ committee state 已更新")
            else:
                print("  · 无需更新 committee state")
        else:
            print("  · 无裁定，跳过 committee state 更新")

    # 3. 重生成 lite
    print("\n[3/5] 同步 registry-lite...")
    regenerate_lite()

    # 4. 交叉校验
    print("\n[4/5] 交叉校验...")
    cross_validate()

    # 5. 同步 Obsidian（主审查报告 + 反向审查 + 魂 YAML）
    print("\n[5/5] Obsidian 同步...")
    synced = _sync_review_to_obsidian(soul_name, review_file, review_filename, reviewer)
    for item in synced:
        print(f"  ✅ {item}")

    print(f"\n✅ 审查落盘完成: {soul_name}")
    print("   → graphify: 调用 Skill(\"graphify\") 更新审查知识图谱")
    return 0

def cmd_possession_close(soul_name, mode, task, effectiveness, notes="", output_file=None,
                         souls_list=None, obsidian_content=None, obsidian_batch=None, obsidian_stdin=None,
                         self_negation="", empty_chair=""):
    """附体结束后：追加 call-records → prompt-audit → Obsidian 存档 → 重生成 lite → 交叉校验

    --self-negation 和 --empty-chair 在 Pro 模式为必填（SKILL.md 强制），
    在 Lite 模式为可选（Lite 分支已精简使用者参与环节）。
    代码层降级为警告——是否必填由 SKILL.md 决定。
    """
    # 软检查：Lite 模式下 --self-negation 和 --empty-chair 可选
    if not self_negation or not self_negation.strip():
        print("  ⚠ 未提供 --self-negation（Lite 模式下可选，Pro 模式由 SKILL.md 强制）", file=sys.stderr)
    if not empty_chair or not empty_chair.strip():
        print("  ⚠ 未提供 --empty-chair（Lite 模式下可选，Pro 模式由 SKILL.md 强制）", file=sys.stderr)

    # 检测消费性使用模式：notes 中记录连续消费次数
    import re as _re
    consumption_match = _re.search(r'第(\d+)次连续', self_negation)
    consecutive_consumption = int(consumption_match.group(1)) if consumption_match else 0
    if consecutive_consumption >= 3:
        print(f"⚠️  警告：连续 {consecutive_consumption} 次消费性使用！", file=sys.stderr)
        print("   下一轮必须使用幡主学习模式，不得使用单魂附体。", file=sys.stderr)
        print("   此警告已写入附体记录。", file=sys.stderr)

    print(f"📝 附体落盘: {soul_name} [{mode}] {task}")

    # 1. 追加 call-records.yaml
    print("\n[1/7] 追加附体记录...")
    try:
        cr = load_yaml(CALL_RECORDS_PATH)
    except Exception:
        cr = {"records": [], "召唤记录": [], "总记录数": 0, "更新时间": today_str(), "说明": ""}

    record = {
        "date": today_str(),
        "effectiveness": effectiveness,
        "mode": mode,
        "notes": notes,
        "soul": soul_name,
        "task": task,
        "self_negation": self_negation,
        "empty_chair": empty_chair,
    }
    if souls_list:
        record["souls"] = souls_list

    if "records" not in cr:
        cr["records"] = []
    cr["records"].insert(0, record)
    cr["更新时间"] = today_str()
    save_yaml(CALL_RECORDS_PATH, cr)
    print(f"  ✅ 附体记录已追加（含自我否定 + 空椅子）")

    # 2. 审计日志（TSV 格式，直接追加）
    print("\n[2/7] 审计日志...")
    try:
        audit_dir = os.path.join(SKILL_DIR, "logs")
        os.makedirs(audit_dir, exist_ok=True)
        audit_path = os.path.join(audit_dir, "audit.log")
        # 格式：日期\t魂名\t模式\t评级\t可观测判据\t审查官复核
        audit_line = f"{today_str()}\t{soul_name}\t{mode}\t{effectiveness}\t{notes}\t\n"
        with open(audit_path, "a") as af:
            af.write(audit_line)
        print(f"  ✅ 审计日志已追加")
    except Exception as e:
        print(f"  ⚠ 审计日志写入失败: {e}")

    # 3. Obsidian 存档（支持四种输入方式，含空椅子回答）
    print("\n[3/7] Obsidian 存档...")
    archived = []

    # 方式 A: 批量模式（合议/辩论/接力多魂输出）
    if obsidian_batch:
        archived = _obsidian_batch(obsidian_batch)

    # 方式 B: stdin 模式
    elif obsidian_stdin:
        content = sys.stdin.read()
        # 追加空椅子拷问回答
        if empty_chair:
            content += f"\n\n---\n## 空椅子拷问\n\n{empty_chair}"
        dest = _obsidian_write(mode, task, soul_name, today_str(), content)
        archived.append(dest)
        print(f"  ✅ Obsidian 存档: {dest}")

    # 方式 C: 文件模式（原有）
    elif obsidian_content:
        with open(obsidian_content) as f:
            content = f.read()
        # 追加空椅子拷问回答
        if empty_chair:
            content += f"\n\n---\n## 空椅子拷问\n\n{empty_chair}"
        dest = _obsidian_write(mode, task, soul_name, today_str(), content)
        archived.append(dest)
        print(f"  ✅ Obsidian 存档: {dest}")

    else:
        print("  · 无 Obsidian 内容（支持 --obsidian-content/--obsidian-batch/--obsidian-stdin）")

    # 4. 重生成 lite
    print("\n[4/7] 同步 registry-lite...")
    regenerate_lite()

    # 5. 交叉校验
    print("\n[5/7] 交叉校验...")
    cross_validate(fix=True)

    # 6. 更新匹配手册
    print("\n[6/7] 更新匹配手册...")
    handbook_path = os.path.join(SKILL_DIR, "committee", "handbook.md")
    generate_handbook(out_file=handbook_path, compact=True)

    # 7. 消费性使用检测
    print("\n[7/7] 消费性使用追踪...")
    if not self_negation or not self_negation.strip():
        print(f"  · 未提供自我否定（Lite 模式）")
    elif consecutive_consumption >= 3:
        print(f"  ⚠️  连续 {consecutive_consumption} 次消费性使用 → 下一轮强制幡主学习模式")
    elif "消费性使用" in self_negation:
        print(f"  消费性使用 ({consecutive_consumption}/3 次连续)")
    else:
        print(f"  学习性使用 ✓")

    print(f"\n✅ 附体落盘完成: {soul_name} | Obsidian: {len(archived)} 文件")
    print("   → humanizer: 若魂输出尚未经 humanizer 处理，请调用 Skill(\"humanizer\")")
    return 0

def cmd_dismiss(soul_name, reason=""):
    """散魂：移动 YAML 至归档 → 标记 registry → 重生成 lite → 交叉校验"""
    yaml_path = os.path.join(SOULS_DIR, f"{soul_name}.yaml")
    if not os.path.exists(yaml_path):
        print(f"❌ 魂魄文件不存在: {yaml_path}")
        return 1

    print(f"⚰ 散魂: {soul_name}")
    if reason:
        print(f"  原因: {reason}")

    # 1. 移动 YAML 至归档
    print("\n[1/3] 归档 YAML...")
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    dest = os.path.join(ARCHIVE_DIR, f"{soul_name}-{today_str()}.yaml")
    os.rename(yaml_path, dest)
    print(f"  ✅ {yaml_path} → {dest}")

    # 2. 标记 registry（不删除，标记为 dismissed）
    print("\n[2/3] 更新 registry...")
    registry = load_yaml(REGISTRY_PATH)
    souls = registry.get("魂魄", [])
    for s in souls:
        if s.get("name") == soul_name:
            s["status"] = "dismissed"
            s["dismissed_at"] = today_str()
            if reason:
                s["dismiss_reason"] = reason
            break
    registry["魂魄"] = souls
    registry["更新时间"] = today_str()
    save_yaml(REGISTRY_PATH, registry)
    print(f"  ✅ {soul_name} 已在 registry 中标记为 dismissed")

    # 3. 重生成 lite + 交叉校验
    print("\n[3/3] 同步与校验...")
    regenerate_lite()
    cross_validate()

    print(f"\n✅ 散魂完成: {soul_name}")
    return 0

def cmd_meeting_prep():
    """会前准备：扫描失败条件 → 检查待办 → 输出议程模板"""
    print("📅 会议准备\n")

    today = datetime.now()
    next_saturday = today + timedelta((5 - today.weekday()) % 7)

    # 1. 读取 state.json 待办和 C 指标
    print("── 待办事项 ──")
    if os.path.exists(STATE_PATH):
        state = load_json(STATE_PATH)
        pending = state.get("pending_tasks", [])
        for t in pending:
            status = t.get("status", "未知")
            icon = {"已完成": "✅", "部分推进": "🔄", "未开始": "⬜"}.get(status, "❓")
            print(f"  {icon} {t.get('id','')} {t.get('name','')} — {status}")
            if t.get("进度"):
                print(f"     进度: {t['进度']}")

        print("\n── C指标状态 ──")
        for key, val in state.get("费曼C指标", {}).items():
            print(f"  {key}: {val.get('当前状态','?')}")

        print("\n── 预算 ──")
        budget = state.get("budget", {})
        print(f"  月度上限: {budget.get('月度预算帽','?')} | 当前余额: {budget.get('当前余额_CNY','?')} 元")

        verification = state.get("verification_conditions", {})
        overdue = [k for k, v in verification.items() if not v.startswith("✅") and k < today_str()]
        if overdue:
            print(f"\n── 过期验收条件 ⚠ ──")
            for k in overdue:
                print(f"  ❌ {k}: {verification[k][:100]}")

    # 2. 输出议程模板
    print(f"\n── 建议议程（下次会议: {next_saturday.strftime('%Y-%m-%d')}）──")
    print("""
1. 失败条件到期检查（30天窗口内 → failure-conditions.md）
2. 开放实践审查魂（未明子）新事实评估
3. 金魂互审排期检查
4. 待办事项追踪（见上）
5. 预算执行报告
6. 其他动议

→ 生成 agenda 文件: committee/meetings/{date}-agenda.md
""")

    return 0

def _get_soul_names():
    """从 registry 读取所有已注册魂名"""
    try:
        import yaml
        with open(REGISTRY_PATH) as f:
            registry = yaml.safe_load(f)
        return [s.get("name", "") for s in registry.get("魂魄", []) if s.get("name")]
    except Exception:
        return []

def _convert_to_wikilinks(content, soul_names=None):
    """将正文中的魂名替换为 [[魂名]]"""
    if soul_names is None:
        soul_names = _get_soul_names()
    if not soul_names:
        return content

    result = content
    for name in sorted(soul_names, key=len, reverse=True):
        # 跳过已在 [[...]] 中的
        if f"[[{name}]]" in result:
            continue
        # 替换独立的魂名（不在 [[ 之后、不在 ]] 之前，不在 YAML 块中）
        import re
        # 分块处理：只替换非 frontmatter 区域
        parts = result.split("---")
        for i in range(len(parts)):
            if i % 2 == 0:  # 偶数索引是非 frontmatter 区域
                parts[i] = re.sub(
                    r"(?<!\[\[)" + re.escape(name) + r"(?!\])",
                    f"[[{name}]]",
                    parts[i]
                )
        result = "---".join(parts)
    return result

def _copy_to_vault(source, vault_subdir, filename=None):
    """复制单个文件到 Obsidian vault 子目录，返回目标路径"""
    dest_dir = os.path.join(OBSIDIAN_VAULT, "万民幡", vault_subdir)
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, filename or os.path.basename(source))
    shutil.copy2(source, dest)
    return dest

def _sync_review_to_obsidian(soul_name, review_file, review_filename, reviewer):
    """审查落盘时同步所有关联文件到 Obsidian：主审查报告 + 反向审查 + 魂 YAML"""
    synced = []

    # 5a. 主审查报告 → 万民幡/审查/
    _copy_to_vault(review_file, "审查", review_filename)
    synced.append(f"审查报告 → 审查/{review_filename}")

    # 5b. 反向审查 → 万民幡/反向审查/
    reverse_pattern = os.path.join(REVIEWS_DIR, f"反向审查-{soul_name}审*-{today_str()}.md")
    for rf in glob.glob(reverse_pattern):
        _copy_to_vault(rf, "反向审查")
        synced.append(f"反向审查 → 反向审查/{os.path.basename(rf)}")

    # 5c. 魂 YAML → 万民幡/魂魄/
    soul_yaml = os.path.join(SOULS_DIR, f"{soul_name}.yaml")
    try:
        soul_md = _soul_yaml_to_markdown(soul_yaml)
        soul_md_path = os.path.join(OBSIDIAN_VAULT, "万民幡", "魂魄", f"{soul_name}.md")
        os.makedirs(os.path.dirname(soul_md_path), exist_ok=True)
        with open(soul_md_path, "w") as f:
            f.write(soul_md)
        synced.append(f"魂魄档案 → 魂魄/{soul_name}.md")
    except FileNotFoundError:
        pass  # soul YAML not found — skip silently
    except Exception as e:
        print(f"  ⚠️ 魂魄归档失败: {e}")

    return synced

def _soul_yaml_to_markdown(yaml_path):
    """将魂 YAML 转为 Obsidian Markdown（frontmatter + 可读正文）"""
    soul = load_yaml(yaml_path)
    name = soul.get("name", os.path.basename(yaml_path).replace(".yaml", ""))
    title = soul.get("title", "")

    # 构建 frontmatter
    fm = {
        "name": name,
        "title": title,
        "date": soul.get("refined_at", ""),
        "reviewed_at": soul.get("reviewed_at", ""),
        "reviewed_by": soul.get("reviewed_by", ""),
    }

    lines = ["---"]
    for k, v in fm.items():
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(v)}]")
        elif v:
            lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {name} — {title}")
    lines.append("")

    # 核心段落
    for section, key in [("## 核心思维", "mind"), ("## 表达风格", "voice"),
                          ("## 擅长技能", "skills_expertise"),
                          ("## 触发条件", None), ("## 召唤提示", "summon_prompt"),
                          ("## 审查记录", "审查记录")]:
        if key is None and section == "## 触发条件":
            trig = soul.get("trigger", {})
            if trig:
                lines.append(section)
                lines.append("")
                for tk in ["keywords", "domains", "scenarios", "exclude"]:
                    val = trig.get(tk, [])
                    if val:
                        lines.append(f"- **{tk}**: {', '.join(val[:10])}")
                lines.append("")
            continue
        val = soul.get(key, "")
        if isinstance(val, list) and key == "skills_expertise":
            lines.append(section)
            lines.append("")
            for item in val:
                lines.append(f"- {item}")
            lines.append("")
        elif isinstance(val, list) and key == "审查记录":
            lines.append(section)
            lines.append("")
            for r in val:
                lines.append(f"- {r.get('审查官', '?')} ({r.get('日期', '?')}): {r.get('裁定', '见报告')[:80]}")
            lines.append("")
        elif isinstance(val, str) and val.strip():
            lines.append(section)
            lines.append("")
            lines.append(val.strip())
            lines.append("")

    return "\n".join(lines)

def _obsidian_write(mode, task, soul_name, date_str, content, extra_frontmatter=None, filename_suffix=None):
    """向 Obsidian vault 写入单个文件，返回文件路径"""
    vault_path = os.path.join(OBSIDIAN_VAULT, "万民幡")
    # 统一审查目录：所有审查类型均写入 审查/
    review_modes = {"审查", "互审", "反向审查", "终末审查", "幡主审查", "新魂审查", "新魂互审"}
    if mode in review_modes:
        rel_dir = "审查"
    else:
        mode_dirs = {
            "单魂": os.path.join("单魂", soul_name),
            "合议": os.path.join("合议", task),
            "辩论": os.path.join("辩论", task),
            "接力": os.path.join("接力", task),
        }
        rel_dir = mode_dirs.get(mode, os.path.join(mode, task))
    archive_dir = os.path.join(vault_path, rel_dir)
    os.makedirs(archive_dir, exist_ok=True)

    safe_task = task.replace("/", "-")[:50]
    if filename_suffix:
        filename = f"{date_str}-{safe_task}-{filename_suffix}.md"
    else:
        filename = f"{date_str}-{safe_task}.md"
    filepath = os.path.join(archive_dir, filename)

    # 收集 souls
    souls = [soul_name] if soul_name else []
    if extra_frontmatter:
        extra_souls = extra_frontmatter.get("souls", [])
        if isinstance(extra_souls, str):
            extra_souls = [s.strip() for s in extra_souls.split(",")]
        for s in extra_souls:
            if s and s not in souls:
                souls.append(s)

    # 构建 frontmatter
    review_type = extra_frontmatter.get("review_type", "") if extra_frontmatter else ""
    mode_fm = mode if mode not in review_modes else ("互审" if "互审" in mode else "审查")
    tags = ["万民幡", mode_fm]
    if review_type:
        tags.append(review_type)

    fm_lines = ["---"]
    fm_lines.append(f"date: {date_str}")
    fm_lines.append(f"souls: [{', '.join(souls)}]")
    fm_lines.append(f"mode: {mode_fm}")
    if review_type:
        fm_lines.append(f"review_type: {review_type}")
    fm_lines.append(f"tags: [{', '.join(tags)}]")
    if extra_frontmatter:
        for k, v in extra_frontmatter.items():
            if k in ("souls", "review_type"):
                continue
            fm_lines.append(f"{k}: {v}")
    fm_lines.append("---")
    fm = "\n".join(fm_lines) + "\n\n"

    # 转换 wiki-links（_convert_to_wikilinks 内部自动从 registry 加载魂名）
    content = _convert_to_wikilinks(content)

    with open(filepath, "w") as f:
        f.write(fm + content)
    return filepath

def _obsidian_batch(manifest_path):
    """从 manifest JSON 批量写入 Obsidian。manifest 格式：
    {"mode": "合议", "task": "...", "date": "2026-05-02", "files": [
      {"soul": "魂名", "role": "角色", "file": "相对路径", "extra_frontmatter": {...}}
    ]}
    """
    with open(manifest_path) as f:
        manifest = json.load(f)

    mode = manifest.get("mode", "单魂")
    task = manifest.get("task", "")
    date_str = manifest.get("date", today_str())
    files = manifest.get("files", [])

    written = []
    for entry in files:
        soul = entry.get("soul", "未知")
        role = entry.get("role", "")
        file_path = entry.get("file", "")
        extra = entry.get("extra_frontmatter", {})
        if role:
            extra["role"] = role
            suffix = f"{soul}-{role}"
        else:
            suffix = soul

        if not os.path.exists(file_path):
            print(f"  ⚠ 文件不存在: {file_path}")
            continue

        # 若源文件已在 Obsidian vault 内，跳过复制（直接写入模式）
        if os.path.abspath(file_path).startswith(os.path.abspath(OBSIDIAN_VAULT)):
            written.append(file_path)
            print(f"  ✅ [{soul}] {file_path} (已在 Obsidian)")
            continue

        with open(file_path) as f:
            content = f.read()

        dest = _obsidian_write(mode, task, soul, date_str, content, extra, filename_suffix=suffix)
        written.append(dest)
        print(f"  ✅ [{soul}] {dest}")

    return written

def _load_soul_names():
    """从 registry 加载魂名 + 系统角色名"""
    names = _get_soul_names()
    names.extend(["辩证综合官", "审查委员会", "幡主", "万民幡"])
    return names

def _copy_with_wiki_links(src, dest, soul_names):
    """复制文件，注入 wiki-link 后写入目标"""
    with open(src, 'r', encoding='utf-8') as f:
        content = f.read()
    content = _convert_to_wikilinks(content, soul_names)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, 'w', encoding='utf-8') as f:
        f.write(content)

def cmd_obsidian_sync(souls_filter=None, reviews_only=False, dry_run=False):
    """同步 Obsidian vault：魂魄 + 审查报告 + 委员会文档"""
    print("📓 Obsidian 同步\n")

    soul_names = _load_soul_names()

    vault_base = os.path.join(OBSIDIAN_VAULT, "万民幡")
    if dry_run:
        print(f"  [dry-run] vault: {vault_base}\n")

    synced = []

    # 1. 魂魄 YAML → Obsidian
    if not reviews_only:
        print("── 魂魄 ──")
        for f in sorted(Path(SOULS_DIR).glob("*.yaml")):
            name = f.stem
            if souls_filter and name not in souls_filter:
                continue
            try:
                from refine import sync_soul_to_obsidian
                if not dry_run:
                    sync_soul_to_obsidian(str(f))
                synced.append(f"魂魄/{name}")
                print(f"  ✅ {name}")
            except ImportError:
                print(f"  ⚠ 无法导入 refine 模块，跳过魂魄同步")
                break
            except Exception as e:
                print(f"  ⚠ {name} 同步失败: {e}")

    # 2. 审查报告 → Obsidian
    print("\n── 审查报告 ──")
    review_patterns = {
        "审查": "*.md",
    }
    for f in sorted(Path(REVIEWS_DIR).glob("*.md")):
        fname = f.name
        if fname.startswith("."):
            continue
        dest_path = os.path.join(vault_base, "审查", fname)
        if not dry_run:
            _copy_with_wiki_links(str(f), dest_path, soul_names)
        synced.append(f"审查/{fname}")
        print(f"  ✅ {fname}")

    # 子目录（合议等；互审已统一到审查目录）
    for sub in ["合议"]:
        subdir = os.path.join(REVIEWS_DIR, sub)
        if not os.path.isdir(subdir):
            continue
        for f in sorted(Path(subdir).glob("*.md")):
            fname = f.name
            if fname.startswith("."):
                continue
            dest_path = os.path.join(vault_base, sub, fname)
            if not dry_run:
                _copy_with_wiki_links(str(f), dest_path, soul_names)
            synced.append(f"{sub}/{fname}")
            print(f"  ✅ {sub}/{fname}")

    # 3. 委员会文档 → Obsidian
    print("\n── 委员会文档 ──")
    # 会议纪要
    for f in sorted(Path(MEETINGS_DIR).glob("*会议纪要*.md")):
        fname = f.name
        dest_path = os.path.join(vault_base, "委员会", fname)
        if not dry_run:
            _copy_with_wiki_links(str(f), dest_path, soul_names)
        synced.append(f"委员会/{fname}")
        print(f"  ✅ 委员会/{fname}")

    print(f"\n✅ Obsidian 同步完成: {len(synced)} 个文件")
    return 0

def cmd_sync_all():
    """全量同步：lite → agent --all → 交叉校验 → 健康检查 → Obsidian"""
    print("🔄 全量同步\n")

    # 1. 重生成 lite
    print("[1/5] 重生成 registry-lite.yaml...")
    regenerate_lite()

    # 2. 同步所有 agent
    print("\n[2/5] 同步所有 agent 文件...")
    run_cmd(f"python3 {SCRIPTS_DIR}/sync-agent.py --all", "sync-agent --all")

    # 3. 交叉校验
    print("\n[3/5] 交叉校验...")
    cross_validate()

    # 4. 健康检查
    print("\n[4/5] 健康检查...")
    health_check()

    # 5. Obsidian 同步
    print("\n[5/5] Obsidian 同步...")
    cmd_obsidian_sync()

    print("\n✅ 全量同步完成")
    return 0

# ══════════════════════════════════════════════════════════════════
# 入口
# ══════════════════════════════════════════════════════════════════

USAGE = """用法:
  python3 scripts/transact.py refine-close <魂名>
  python3 scripts/transact.py review-apply <魂名> --review-file <路径> [--verdict "..."] [--reviewer 列宁]
  python3 scripts/transact.py possession-close <魂名> --mode <模式> --task <任务> --effectiveness <有效|部分有效|无效>
        [--self-negation "<...>"] [--empty-chair "<...>"] [--notes "..."]
        [--obsidian-content <文件> | --obsidian-batch <manifest.json> | --obsidian-stdin]
  python3 scripts/transact.py dismiss <魂名> [--reason "..."]
  python3 scripts/transact.py obsidian-sync [--souls 鲁迅,费曼] [--reviews-only] [--dry-run]
  python3 scripts/transact.py meeting-prep
  python3 scripts/transact.py sync-all
"""

def parse_args():
    args = sys.argv[1:]
    if not args:
        print(USAGE)
        sys.exit(1)

    cmd = args[0]
    kwargs = {}
    i = 1
    while i < len(args):
        if args[i].startswith("--"):
            key = args[i][2:].replace("-", "_")
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                kwargs[key] = args[i + 1]
                i += 2
            else:
                kwargs[key] = True
                i += 1
        else:
            i += 1

    positional = [a for a in args[1:] if not a.startswith("--")]
    # Remove values after --key pairs
    cleaned = []
    skip = False
    for a in positional:
        if skip:
            skip = False
            continue
        cleaned.append(a)

    return cmd, cleaned, kwargs

# task save/restore

def cmd_task_save(tasks_json):
    """持久化 Task 到 state.json，合并策略：以 id 为键"""
    try:
        tasks = json.loads(tasks_json)
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}"); return 1
    if not isinstance(tasks, list):
        print("❌ tasks must be JSON array"); return 1

    try:
        state = load_json(STATE_PATH)
    except FileNotFoundError:
        state = {}

    existing = {t.get("id"): t for t in state.get("pending_tasks", [])}
    for t in tasks:
        tid = t.get("id", "")
        if not tid:
            print("⚠ skip: no id"); continue
        t["上次更新"] = today_str()
        if "status" not in t:
            t["status"] = "pending"
        existing[tid] = t

    state["pending_tasks"] = list(existing.values())
    save_json(STATE_PATH, state)
    print(f"task-save: {len(tasks)} tasks → state.json ({len(state['pending_tasks'])} total)")
    return 0

def cmd_task_restore():
    """从 state.json 恢复活跃 Task"""
    try:
        state = load_json(STATE_PATH)
    except FileNotFoundError:
        print("[]"); return 0

    active = [t for t in state.get("pending_tasks", [])
              if t.get("status") not in ("已完成", "已取消")]
    if not active:
        print("[]"); return 0

    output = [{"id": t.get("id",""), "subject": t.get("name",""),
               "description": t.get("description", t.get("name","")),
               "status": t.get("status","pending"), "进度": t.get("进度","")}
              for t in active]
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    cmd, pos, kw = parse_args()

    if cmd == "refine-close":
        if not pos:
            print("❌ 缺少魂名"); sys.exit(1)
        sys.exit(cmd_refine_close(pos[0]))

    elif cmd == "review-apply":
        if not pos:
            print("❌ 缺少魂名"); sys.exit(1)
        if "review_file" not in kw:
            print("❌ 需要 --review-file"); sys.exit(1)
        sys.exit(cmd_review_apply(
            pos[0], kw["review_file"],
            verdict=kw.get("verdict"),
            reviewer=kw.get("reviewer"),
        ))

    elif cmd == "possession-close":
        if not pos:
            print("❌ 缺少魂名"); sys.exit(1)
        for req in ["mode", "task", "effectiveness"]:
            if req not in kw:
                print(f"❌ 缺少 --{req}"); sys.exit(1)
        # 代码强制层：--self-negation 和 --empty-chair 必填
        self_negation = kw.get("self_negation", "")
        empty_chair = kw.get("empty_chair", "")
        # Obsidian 存档输入（四选一：文件/stdin/批量/none）
        obsidian_content = None
        obsidian_batch = kw.get("obsidian_batch")
        obsidian_stdin = kw.get("obsidian_stdin", False)
        if "obsidian_content" in kw:
            obsidian_content = kw["obsidian_content"]  # pass path, not content — cmd_possession_close handles reading
        sys.exit(cmd_possession_close(
            pos[0],
            mode=kw["mode"],
            task=kw["task"],
            effectiveness=kw["effectiveness"],
            notes=kw.get("notes", ""),
            obsidian_content=obsidian_content,
            obsidian_batch=obsidian_batch,
            obsidian_stdin=obsidian_stdin,
            self_negation=self_negation,
            empty_chair=empty_chair,
        ))

    elif cmd == "dismiss":
        if not pos:
            print("❌ 缺少魂名"); sys.exit(1)
        sys.exit(cmd_dismiss(pos[0], reason=kw.get("reason", "")))

    elif cmd == "obsidian-sync":
        souls_filter = None
        if "souls" in kw:
            souls_filter = set(kw["souls"].split(","))
        reviews_only = kw.get("reviews_only", False)
        dry_run = kw.get("dry_run", False)
        sys.exit(cmd_obsidian_sync(souls_filter=souls_filter, reviews_only=reviews_only, dry_run=dry_run))

    elif cmd == "task-save":
        tasks_json = kw.get("tasks") or (pos[0] if pos else "")
        if not tasks_json:
            print("❌ 需要 --tasks '[...]' 或管道传入 JSON")
            sys.exit(1)
        sys.exit(cmd_task_save(tasks_json))

    elif cmd == "task-restore":
        sys.exit(cmd_task_restore())

    elif cmd == "meeting-prep":
        sys.exit(cmd_meeting_prep())

    elif cmd == "sync-all":
        sys.exit(cmd_sync_all())

    else:
        print(f"❌ 未知子命令: {cmd}")
        print(USAGE)
        sys.exit(1)
