#!/usr/bin/env python3
"""从 registry.yaml 生成 registry-lite.yaml — 仅含匹配审查所需字段。

用法:
    python3 scripts/generate-registry-lite.py                    # 生成到 stdout
    python3 scripts/generate-registry-lite.py -o registry-lite.yaml  # 写入文件
"""

import argparse
import sys
from pathlib import Path

import yaml

LITE_FIELDS = [
    "name",
    "grade",
    "domain",
    "trigger_keywords_summary",
    "trigger_scenarios_summary",
    "trigger_exclude_summary",
]


def generate(registry_path: Path) -> dict:
    with open(registry_path) as f:
        data = yaml.safe_load(f)

    lite = {
        "description": "匹配审查速查表 — 从 registry.yaml 自动生成，仅含匹配所需字段",
        "generated_from": str(registry_path),
        "魂魄": [],
    }

    for soul in data.get("魂魄", []):
        entry = {}
        for field in LITE_FIELDS:
            if field in soul:
                entry[field] = soul[field]
        lite["魂魄"].append(entry)

    return lite


def main():
    parser = argparse.ArgumentParser(description="生成 registry-lite.yaml")
    parser.add_argument(
        "-i", "--input",
        default=str(Path(__file__).resolve().parent.parent / "registry.yaml"),
        help="registry.yaml 路径",
    )
    parser.add_argument(
        "-o", "--output",
        help="输出文件路径（默认 stdout）",
    )
    args = parser.parse_args()

    lite = generate(Path(args.input))

    yaml_str = yaml.dump(lite, allow_unicode=True, default_flow_style=False, sort_keys=False)

    if args.output:
        out_path = Path(args.output)
        # 添加生成时间注释
        from datetime import datetime
        header = f"# 自动生成于 {datetime.now().isoformat()}\n# 匹配审查速查表 — 只读，勿手动编辑\n\n"
        with open(out_path, "w") as f:
            f.write(header + yaml_str)
        print(f"OK: {out_path} ({len(lite['魂魄'])} 魂, {len(yaml_str)} chars)")
    else:
        print(yaml_str)


if __name__ == "__main__":
    main()
