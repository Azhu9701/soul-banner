#!/bin/bash
# 万魂幡运维自动化脚本 — 由 loop skill 周期性触发
# 只做运维检查，不碰判断行为（审查/互审/品级调整）
# 用法：/loop 1h bash ~/.claude/skills/soul-banner/scripts/maintenance-loop.sh --health
#       /loop 6h bash ~/.claude/skills/soul-banner/scripts/maintenance-loop.sh --validate

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

run_health() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 健康检查..."
    python3 "$SCRIPT_DIR/registry-health-check.py"
}

run_validate() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 交叉校验..."
    python3 "$SCRIPT_DIR/cross-validate.py" || {
        echo "[WARN] 交叉校验发现不一致，尝试自动修复..."
        python3 "$SCRIPT_DIR/cross-validate.py" --fix
    }
}

run_audit_stats() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 审计日志统计..."
    python3 "$SCRIPT_DIR/prompt-audit.py" --stats 2>/dev/null || echo "(审计日志为空或脚本不支持 --stats)"
}

run_zero_usage() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 零召唤检测..."
    python3 "$SCRIPT_DIR/registry-health-check.py" --zero-usage 2>/dev/null || echo "(零召唤检测不可用)"
}

case "${1:-}" in
    --health)    run_health ;;
    --validate)  run_validate ;;
    --audit)     run_audit_stats ;;
    --zero)      run_zero_usage ;;
    --all)
        run_health
        run_validate
        run_audit_stats
        run_zero_usage
        ;;
    *)
        echo "用法: $0 --health|--validate|--audit|--zero|--all"
        exit 1
        ;;
esac
