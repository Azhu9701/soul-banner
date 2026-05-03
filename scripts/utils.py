"""万民幡共享工具函数"""

import os
import subprocess
import sys


def load_yaml(path):
    import yaml
    with open(path) as f:
        return yaml.safe_load(f)


def save_yaml(path, data):
    import yaml
    with open(path, "w") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=False, width=200)


SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_script(script_rel_path, *args):
    """运行 scripts/ 下的 Python 脚本，返回 (ok, stdout)。"""
    script = os.path.join(SKILL_DIR, "scripts", script_rel_path)
    if not os.path.isfile(script):
        return False, f"脚本不存在: {script}"
    try:
        r = subprocess.run(
            [sys.executable, script, *args],
            capture_output=True, text=True, timeout=30,
        )
        return r.returncode == 0, r.stdout.strip() + "\n" + r.stderr.strip()
    except Exception as e:
        return False, str(e)


def run_cmd(cmd, description="", cwd=None):
    """运行 shell 命令，返回 (success, output)。cwd 默认为 SKILL_DIR。"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=60,
            cwd=cwd or SKILL_DIR,
        )
        ok = result.returncode == 0
        if not ok:
            print(f"  ⚠ {description} 失败: {result.stderr.strip()[:200]}")
        return ok, result.stdout.strip()
    except Exception as e:
        print(f"  ⚠ {description} 异常: {e}")
        return False, str(e)
