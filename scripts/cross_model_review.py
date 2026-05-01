#!/usr/bin/env python3
"""跨底模对抗性审查实验 —— 调用不同模型API进行独立审查

API Keys 通过环境变量配置，不写死在代码中：
  export DEEPSEEK_API_KEY="sk-xxx"
  export KIMI_API_KEY="sk-xxx"
  export GLM_API_KEY="xxx"
"""

import sys, os, json, time

DEEPSEEK_CONFIG = {
    "base_url": os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/anthropic"),
    "api_key": os.environ.get("DEEPSEEK_API_KEY", ""),
    "model": os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")
}

KIMI_CONFIG = {
    "base_url": os.environ.get("KIMI_BASE_URL", "https://api.kimi.com/v1/chat/completions"),
    "api_key": os.environ.get("KIMI_API_KEY", ""),
    "model": os.environ.get("KIMI_MODEL", "kimi-for-coding")
}

GLM_CONFIG = {
    "base_url": os.environ.get("GLM_BASE_URL", "https://api.z.ai/api/coding/paas/v4/chat/completions"),
    "api_key": os.environ.get("GLM_API_KEY", ""),
    "model": os.environ.get("GLM_MODEL", "glm-5.1")
}

def load_soul_prompt(soul_name):
    """Load soul's mind/voice/approach from YAML"""
    souls_dir = os.environ.get(
        "SOUL_BANNER_HOME",
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    with open(os.path.join(souls_dir, "souls", f"{soul_name}.yaml"), "r") as f:
        import yaml
        soul = yaml.safe_load(f)
    return soul

def call_kimi(system_prompt, user_prompt, max_tokens=4096):
    """Call Kimi API (OpenAI-compatible)"""
    import requests
    resp = requests.post(
        KIMI_CONFIG["base_url"],
        headers={
            "Authorization": f"Bearer {KIMI_CONFIG['api_key']}",
            "Content-Type": "application/json"
        },
        json={
            "model": KIMI_CONFIG["model"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7
        },
        timeout=120
    )
    if resp.status_code != 200:
        return {"error": f"Kimi API error {resp.status_code}", "body": resp.text[:500]}
    data = resp.json()
    return {"model": KIMI_CONFIG["model"], "content": data["choices"][0]["message"]["content"]}

def call_glm(system_prompt, user_prompt, max_tokens=4096):
    """Call GLM-5.1 API"""
    import requests
    resp = requests.post(
        GLM_CONFIG["base_url"],
        headers={
            "Authorization": f"Bearer {GLM_CONFIG['api_key']}",
            "Content-Type": "application/json"
        },
        json={
            "model": GLM_CONFIG["model"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7
        },
        timeout=120
    )
    if resp.status_code != 200:
        return {"error": f"GLM API error {resp.status_code}", "body": resp.text[:500]}
    data = resp.json()
    return {"model": GLM_CONFIG["model"], "content": data["choices"][0]["message"]["content"]}

def build_review_prompt(soul, content_to_review, role="reviewer"):
    """Build review prompt for a soul"""
    mind = soul.get("mind", "")
    voice = soul.get("voice", "")
    name = soul.get("name", "")

    review_template = f"""你是一个内容审查者。用你独特的思维方法，审查以下小红书机器人产品内容。

审查要求：
1. 找到至少3个具体的问题（事实错误、逻辑漏洞、偏见、遗漏、或营销过度）
2. 对每个问题，引用原文中的具体内容作为证据
3. 考虑一个不同意该分析的读者会说什么
4. 对你发现的每个问题，给出1-5的严重程度评分（5=最严重）
5. 如果你不确定某件事，明确说"我不确定"
6. 最后给出整体评价：这篇内容最大的优点和最大的缺陷

不要做的事：
- 不要只说"这篇文章写得不错"
- 不要复述原文内容而不加批评
- 不要给出模糊的赞扬或模糊的批评

待审查内容：
---
{content_to_review}
---
"""
    system_prompt = f"""你是{name}。{mind}

{voice}

请用中文回复。保持你的思维风格和方法论特征。"""
    return system_prompt, review_template

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 cross_model_review.py <soul_name> <model_name> [content_file]")
        print("  model_name: kimi | glm")
        sys.exit(1)

    soul_name = sys.argv[1]
    model_name = sys.argv[2]
    content_file = sys.argv[3] if len(sys.argv) > 3 else None

    if content_file:
        with open(content_file, "r") as f:
            content = f.read()
    else:
        content = sys.stdin.read()

    soul = load_soul_prompt(soul_name)
    system_prompt, user_prompt = build_review_prompt(soul, content)

    print(f"=== {soul_name} on {model_name.upper()} ===")
    print(f"System prompt length: {len(system_prompt)} chars")
    print(f"Content length: {len(content)} chars")
    print("Calling API...")

    start = time.time()
    if model_name == "kimi":
        result = call_kimi(system_prompt, user_prompt)
    elif model_name == "glm":
        result = call_glm(system_prompt, user_prompt)
    else:
        result = {"error": f"Unknown model: {model_name}"}

    elapsed = time.time() - start

    if "error" in result:
        print(f"ERROR ({elapsed:.1f}s): {result['error']}")
        print(result.get("body", ""))
        sys.exit(1)

    print(f"OK ({elapsed:.1f}s)")
    print(f"Model: {result['model']}")
    print()
    print(result["content"])

if __name__ == "__main__":
    main()
