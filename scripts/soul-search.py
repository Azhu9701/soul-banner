#!/usr/bin/env python3
"""万魂幡收魂搜索脚本 — 通过 tmwd-bridge 在百度/Bing/Google 搜索 8 维度素材."""

import sys, time, random, json, os

SEARCH_DIMENSIONS = {
    "核心思维框架": ("{name} 思维框架 思考方式", "{name} thinking framework methodology"),
    "决策模式": ("{name} 决策 判断 案例", "{name} decision making approach"),
    "管理风格": ("{name} 管理风格 团队", "{name} management style leadership"),
    "技术愿景": ("{name} 技术方向 愿景 预言", "{name} technology vision prediction"),
    "沟通风格": ("{name} 演讲 沟通 写作风格", "{name} communication style speech"),
    "工作方法": ("{name} 工作方法 习惯 效率", "{name} workflow productivity method"),
    "代表性言论": ("{name} 名言 经典语录", "{name} famous quotes key statements"),
    "争议素材": ("{name} 争议 批评 负面", "{name} controversy criticism"),
}

ENGINES = {
    "baidu": "https://www.baidu.com/s?wd={query}",
    "bing": "https://www.bing.com/search?q={query}",
    "google": "https://www.google.com/search?q={query}",
}

# CSS selectors per engine for extracting results
RESULT_SELECTORS = {
    "baidu": (".result, .c-container", "h3", "a", ".c-abstract"),
    "bing": ("li.b_algo", "h2 a", "h2 a", ".b_caption p"),
    "google": ("div.g", "h3", "a", ".VwiC3b, span.aCOpRe"),
}


def init_driver():
    sys.path.insert(0, os.path.expanduser("~/GenericAgent"))
    from TMWebDriver import TMWebDriver
    d = TMWebDriver()
    time.sleep(2)
    sessions = d.get_all_sessions()
    if not sessions:
        raise RuntimeError("tmwd-bridge: no active sessions. Open Chrome and verify extension.")
    return d


def search_engine(d, engine, query):
    """Search one engine, return top 8 results."""
    url = ENGINES[engine].format(query=query)
    d.execute_js(f"window.location.href='{url}'")
    time.sleep(2 + random.uniform(0, 1.5))

    container_sel, title_sel, link_sel, snippet_sel = RESULT_SELECTORS[engine]
    js = f"""
    (async () => {{
        const items = [];
        document.querySelectorAll('{container_sel}').forEach(el => {{
            const titleEl = el.querySelector('{title_sel}');
            const linkEl = el.querySelector('{link_sel}');
            const snippetEl = el.querySelector('{snippet_sel}');
            const title = titleEl?.textContent?.trim();
            const link = linkEl?.href;
            const snippet = snippetEl?.textContent?.trim();
            if (title && link) items.push({{title, link, snippet}});
        }});
        return items.slice(0, 8);
    }})()
    """
    result = d.execute_js(js)
    return result.get("data", []) if isinstance(result, dict) else []


def search_dimension(d, dim_name, query_cn, query_en, engines=("baidu", "bing", "google")):
    """Search one dimension across specified engines."""
    all_results = []
    for engine in engines:
        query = query_cn if engine == "baidu" else query_en
        try:
            results = search_engine(d, engine, query)
            for r in results:
                r["engine"] = engine
            all_results.extend(results)
            time.sleep(5 + random.uniform(0, 3))  # gap between engines
        except Exception as e:
            print(f"  [{engine}] ERROR: {e}", file=sys.stderr)
    return all_results


def collect(name, output_dir=None):
    """Main entry: search all 8 dimensions for a person, save results."""
    if output_dir is None:
        output_dir = f"raw/{name}"
    os.makedirs(output_dir, exist_ok=True)

    print(f"=== 收魂: {name} ===")
    d = init_driver()

    all_data = {}
    for dim_name, (query_cn, query_en) in SEARCH_DIMENSIONS.items():
        print(f"\n--- {dim_name} ---")
        results = search_dimension(d, dim_name, query_cn.replace("{name}", name), query_en.replace("{name}", name))
        all_data[dim_name] = results
        print(f"  {len(results)} results")

    # Save as Markdown
    md_path = os.path.join(output_dir, "搜索素材.md")
    with open(md_path, "w") as f:
        f.write(f"# {name} 收魂搜索素材\n\n")
        f.write(f"搜索时间：{time.strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"搜索引擎：百度、Bing、Google\n\n")
        for dim_name, results in all_data.items():
            f.write(f"## {dim_name}\n\n")
            if not results:
                f.write("（未找到结果）\n\n")
                continue
            for i, r in enumerate(results[:10], 1):
                f.write(f"### {i}. {r['title']}\n")
                f.write(f"- 来源：[{r['engine']}] {r['link']}\n")
                if r.get("snippet"):
                    f.write(f"- 摘要：{r['snippet']}\n")
                f.write("\n")

    print(f"\n素材已保存至 {md_path}")
    return all_data


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="万魂幡收魂搜索")
    parser.add_argument("name", help="人物名")
    parser.add_argument("-o", "--output", help="输出目录", default=None)
    args = parser.parse_args()
    collect(args.name, args.output)
