#!/usr/bin/env python3
"""主义主义字段校验器 v3.0 — 检查目录匹配格式的 ismism-data.json"""
import json, sys
from pathlib import Path

REQUIRED_KEYS = {"code", "catalog_match", "match_quality", "rationale", "blindspots", "compat", "incompat"}
VALID_QUALITIES = {"精确", "近似", "复合", "反讽式匹配", "目录外"}
VALID_FIELDS = {1, 2, 3, 4}

def validate(path):
    with open(path) as f:
        data = json.load(f)
    
    errors = []
    warnings = []
    
    for name, ism in data.items():
        # Check required keys
        missing = REQUIRED_KEYS - set(ism.keys())
        if missing:
            errors.append(f"{name}: 缺少字段 {missing}")
        
        # Check match_quality
        mq = ism.get("match_quality", "")
        if mq and mq not in VALID_QUALITIES:
            errors.append(f"{name}: match_quality='{mq}' 不在合法值 {VALID_QUALITIES}")
        
        # Check compat/incompat values
        for key in ["compat", "incompat"]:
            vals = ism.get(key, [])
            for v in vals:
                if v not in VALID_FIELDS:
                    errors.append(f"{name}: {key} 含非法值 {v}")
        
        # Check blindspots is a list
        bs = ism.get("blindspots", [])
        if not isinstance(bs, list):
            errors.append(f"{name}: blindspots 必须是列表")
        
        # Check rationale is non-trivial
        rat = ism.get("rationale", "")
        if len(rat) < 30:
            warnings.append(f"{name}: rationale 过短 ({len(rat)}字符)")
        
        # Check compat and incompat don't overlap
        c = set(ism.get("compat", []))
        ic = set(ism.get("incompat", []))
        if c & ic:
            errors.append(f"{name}: compat 和 incompat 有交集 {c & ic}")
    
    return errors, warnings

def main():
    path = Path(__file__).parent.parent / "ismism-data.json"
    if not path.exists():
        print(f"❌ 未找到: {path}")
        sys.exit(1)
    
    errors, warnings = validate(path)
    
    if warnings:
        for w in warnings:
            print(f"⚠️  {w}")
    if errors:
        for e in errors:
            print(f"❌ {e}")
    
    print(f"\n检查: {len(json.load(open(path)))} 魂 | 错误: {len(errors)} | 警告: {len(warnings)}")
    if errors:
        print("❌ 需要修复")
        sys.exit(1)
    else:
        print("✅ 全部通过")

if __name__ == "__main__":
    main()
