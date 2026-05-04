#!/usr/bin/env python3
"""修复被损坏的 soul YAML — v3: 解析 + yaml.dump 重建"""

import re, yaml
from pathlib import Path

SOULS_DIR = Path("/Users/huyi/.claude/skills/soul-banner/souls")

# ── 需要保持原样输出的顶层列表类字段 ──

# ── 多行字符串字段 ──
MULTILINE_FIELDS = {'mind', 'voice', 'summon_prompt', 'notes', 'gold_review',
                     'review_verdict', 'grade_reason', '_match_summary',
                     'trigger_keywords_summary', 'trigger_scenarios_summary',
                     'trigger_exclude_summary'}

# ── Literal block scalar 表示器 ──
class LiteralString(str):
    pass

def literal_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')

yaml.add_representer(LiteralString, literal_representer)

def parse_top_level_keys(text):
    """解析 YAML 文本的顶层 key-value 对"""
    lines = text.split('\n')
    keys = []
    for i, line in enumerate(lines):
        if re.match(r'^\w[\w_]*:', line):
            keys.append((i, line.split(':')[0]))
    return keys, lines

def extract_value(lines, start_line, end_line):
    """提取 key 的值部分（冒号后的内容）"""
    first = lines[start_line]
    colon_pos = first.index(':')
    value_start = first[colon_pos+1:]
    rest_lines = lines[start_line+1:end_line]
    return (value_start + '\n' + '\n'.join(rest_lines)).rstrip()

def rebuild_as_dict(filepath):
    """从损坏的 YAML 重建为 Python dict"""
    with open(filepath) as f:
        content = f.read()

    keys, lines = parse_top_level_keys(content)

    result = {}
    for idx, (line_num, key_name) in enumerate(keys):
        end_line = keys[idx+1][0] if idx+1 < len(keys) else len(lines)
        raw_value = extract_value(lines, line_num, end_line)

        # 清理值
        value = raw_value.strip()

        if key_name == 'patches' and not value:
            result[key_name] = []
            continue

        if key_name in MULTILINE_FIELDS:
            # 移除开头的 | 或 ' 等标记
            if value.startswith('|'):
                value = value[1:].strip()
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1].strip()
            elif value.startswith('"') and value.endswith('"'):
                value = value[1:-1].strip()

            # 清理残留
            value = re.sub(r'维持金魂🟡[。，]?\s*', '', value)
            value = re.sub(r'维持金魂[。，]?\s*', '', value)
            value = re.sub(r'升金魂🟡[。，]?\s*', '', value)
            value = re.sub(r'维持银魂🥈[。，]?\s*', '', value)
            value = re.sub(r'维持银魂[。，]?\s*', '', value)
            value = re.sub(r'维持紫魂[。，]?\s*', '', value)
            value = re.sub(r'维持蓝魂[🔵，。、]?\s*', '', value)
            value = re.sub(r'金魂候选[。，]?\s*', '', value)
            value = re.sub(r'金魂互审', '魂互审', value)
            value = re.sub(r'金魂中最[^\s，。]+\s*', '', value)
            value = re.sub(r'\[条件金魂\]\s*', '', value)
            value = re.sub(r'金魂\((\d)\)', r'标准\1', value)
            value = re.sub(r'万民幡中第[一二三四五六七八九十\d]+个金魂', '', value)
            value = re.sub(r'万民幡中第[一二三四五六七八九十\d]+个魂魄', '万民幡中魂魄', value)
            value = re.sub(r'两金魂共存', '两魂共存', value)
            value = re.sub(r'与费曼金魂互补', '与费曼互补', value)
            value = re.sub(r'费曼金魂提供', '费曼提供', value)
            value = re.sub(r'与幡中金魂的关系', '与幡中其他魂魄的关系', value)
            value = re.sub(r'金魂保留', '保留', value)
            value = re.sub(r'金魂有效域', '有效域', value)
            value = re.sub(r'金魂失效域', '失效域', value)
            value = re.sub(r'有限金魂', '', value)
            value = re.sub(r'金魂定位的边界', '定位的边界', value)
            value = re.sub(r'不影响其金魂地位', '不影响其地位', value)
            value = re.sub(r'不是金魂（', '（', value)
            value = re.sub(r'定位为上限而非金魂', '定位为上限', value)
            value = re.sub(r'可复制性不如金魂', '可复制性不如体系化方法论', value)
            value = re.sub(r'金魂门槛', '门槛', value)
            value = re.sub(r'金魂第\(3\)条', '标准3', value)
            value = re.sub(r'金魂\b', '', value)
            value = re.sub(r'银魂\b', '', value)
            value = re.sub(r'蓝魂\b', '', value)
            value = re.sub(r'紫魂\b', '', value)
            value = re.sub(r'[：:][^\n]*', '', value)
            value = re.sub(r'论证[：:][^\n]*', '', value)
            value = re.sub(r'降品审查[（(]金→银[）)]', '重新审查', value)
            value = re.sub(r'降品[。，]?\s*', '', value)
            value = re.sub(r'距金魂差\d+分[，。]?\s*', '', value)
            value = re.sub(r'\n{4,}', '\n\n\n', value)
            value = value.strip()

            if value:
                result[key_name] = LiteralString(value)
            else:
                result[key_name] = LiteralString('待补充')
        elif key_name in LIST_FIELDS:
            # 列表字段
            result[key_name] = parse_list_value(raw_value)
        elif key_name == 'trigger':
            result[key_name] = parse_trigger(raw_value)
        elif key_name == 'artifacts':
            result[key_name] = parse_artifacts(raw_value)
        elif key_name == '审查记录':
            result[key_name] = parse_review_records(raw_value)
        elif key_name == 'patches':
            result[key_name] = []
                          'status', 'name', 'title', 'refined_at',
                          'reviewed_at', 'reviewed_by'):
            # 简单标量
            v = value.strip().strip("'").strip('"')
            result[key_name] = v
        else:
            # 默认处理
            v = value.strip()
            if v:
                result[key_name] = v
            else:
                result[key_name] = ''

    return result

def parse_list_value(raw):
    """解析 YAML 列表值"""
    items = []
    for line in raw.split('\n'):
        line = line.strip()
        if line.startswith('- '):
            item = line[2:].strip()
            # 处理带引号的项
            if (item.startswith("'") and item.endswith("'")) or \
               (item.startswith('"') and item.endswith('"')):
                item = item[1:-1]
            if item:
                items.append(item)
    return items

def parse_trigger(raw):
    """解析 trigger 字典"""
    result = {}
    current_key = None
    current_list = []

    lines = raw.split('\n')
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # 检测子 key
        m = re.match(r'^(\w+):\s*$', stripped)
        if m:
            if current_key and current_list:
                result[current_key] = current_list
                current_list = []
            current_key = m.group(1)
            continue
        m = re.match(r'^(\w+):\s*\[(.*)\]$', stripped)
        if m:
            if current_key and current_list:
                result[current_key] = current_list
                current_list = []
            key = m.group(1)
            items = [i.strip().strip("'").strip('"') for i in m.group(2).split(',') if i.strip()]
            result[key] = items
            current_key = None
            continue
        # 列表项
        if stripped.startswith('- '):
            item = stripped[2:].strip().strip("'").strip('"')
            if current_key:
                current_list.append(item)

    if current_key and current_list:
        result[current_key] = current_list

    return result

def parse_artifacts(raw):
    """解析 artifacts 列表"""
    result = []
    current = {}
    for line in raw.split('\n'):
        stripped = line.strip()
        if stripped.startswith('- '):
            if current:
                result.append(current)
            current = {}
            # 检查是否是 inline dict
            rest = stripped[2:]
            if rest.startswith('{'):
                # 简单处理 inline
                continue
            continue
        m = re.match(r'^(\w+):\s*(.*)', stripped)
        if m:
            key = m.group(1)
            val = m.group(2).strip().strip("'").strip('"')
            if val:
                current[key] = val
    if current:
        result.append(current)
    return result

def parse_review_records(raw):
    """解析 审查记录"""
    result = []
    current = {}
    for line in raw.split('\n'):
        stripped = line.strip()
        if stripped.startswith('- '):
            if current:
                result.append(current)
            current = {}
            continue
        m = re.match(r'^(\w+):\s*(.*)', stripped)
        if m:
            key = m.group(1)
            val = m.group(2).strip().strip("'").strip('"')
            # 清理 裁定 中的引用
            if key == '裁定':
                val = re.sub(r'维持金魂[🟡，。、]?\s*', '', val)
                val = re.sub(r'维持银魂[🥈，。、]?\s*', '', val)
                val = re.sub(r'维持蓝魂[🔵，。、]?\s*', '', val)
                val = re.sub(r'维持紫魂[，。、]?\s*', '', val)
                val = re.sub(r'升金魂[🟡，。、]?\s*', '', val)
                val = re.sub(r'金魂互审', '魂互审', val)
                val = val.strip()
            if key == '报告':
                val = val.replace('金魂互审', '魂互审')
            current[key] = val
    if current:
        result.append(current)
    return result

def write_yaml(filepath, data):
    """写出合法 YAML"""
    # 确定 key 顺序
    key_order = ['name', 'title', 'domain', 'status', 'refined_at',
                 'reviewed_at', 'reviewed_by', 'review_verdict', 'gold_review',
                 'mind', 'voice', 'skills_expertise', 'trigger',
                 '_match_summary', 'trigger_keywords_summary',
                 'trigger_scenarios_summary', 'trigger_exclude_summary',
                 'artifacts', 'source_materials', 'summon_prompt', 'notes',
                 '审查记录', 'patches']

    # 确保所有期望 key 都有值
    for k in key_order:
        if k not in data:
            if k in LIST_FIELDS or k in ('artifacts', 'patches', '审查记录'):
                data[k] = []
            elif k in MULTILINE_FIELDS:
                data[k] = LiteralString('')
            else:
                data[k] = ''

    # 排序: key_order 中的按顺序，其他的追加
    ordered = {}
    for k in key_order:
        if k in data:
            ordered[k] = data[k]
    for k in data:
        if k not in ordered:
            ordered[k] = data[k]

    with open(filepath, 'w') as f:
        yaml.dump(ordered, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=False, width=120)

    # 后处理：确保 LiteralString 用 | 格式
    with open(filepath) as f:
        content = f.read()

    # yaml.dump 对 LiteralString 用 |，但可能出现在错误的位置
    # 简单检查：确保 | 后的内容正确

    return True

def main():
    ok = 0
    failed = []

    for yf in sorted(SOULS_DIR.glob("*.yaml")):
        name = yf.name
        try:
            data = rebuild_as_dict(yf)
            write_yaml(yf, data)
            # 验证
            with open(yf) as f:
                yaml.safe_load(f)
            ok += 1
            print(f'  ✅ {name}')
        except Exception as e:
            failed.append((name, str(e)))
            print(f'  ❌ {name}: {e[:120]}')

    print(f'\n通过: {ok}/{ok+len(failed)}')
    if failed:
        print("失败:")
        for name, err in failed:
            print(f"  {name}: {err[:150]}")

if __name__ == "__main__":
    main()
