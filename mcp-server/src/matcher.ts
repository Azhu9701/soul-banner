/** 万民幡 MCP Server — 魂匹配算法（从 match.py 移植） */

import type { SoulEntry, MatchResult } from "./types.js";
import { STOP_BIGRAMS } from "./constants.js";

/** 中文 n-gram 分词 */
function tokenize(text: string): Set<string> {
  const tokens = new Set<string>();
  const chinese = text.match(/[一-鿿]+/g) || [];
  for (const word of chinese) {
    for (let i = 0; i < word.length - 1; i++) {
      tokens.add(word.slice(i, i + 2)); // bigram
    }
    for (let i = 0; i < word.length - 2; i++) {
      tokens.add(word.slice(i, i + 3)); // trigram
    }
    if (word.length >= 2) tokens.add(word);
  }
  const eng = text.match(/[a-zA-Z0-9]+/g) || [];
  for (const w of eng) tokens.add(w.toLowerCase());
  return tokens;
}

interface KeywordResult {
  matched: string[];
  score: number;
}

/** 关键词匹配评分 */
function keywordOverlap(
  taskTokens: Set<string>,
  keywordText: string
): KeywordResult {
  if (!keywordText) return { matched: [], score: 0 };

  const keywords = keywordText.split(/[、,，/]/).map((k) => k.trim()).filter(Boolean);
  const matched: string[] = [];
  const fuzzyMatched: string[] = [];
  let matchedScore = 0;

  for (const kw of keywords) {
    const kwLower = kw.toLowerCase();
    const kwLen = kw.length;
    const kwTokens = tokenize(kw);
    const kwBigrams = new Set([...kwTokens].filter((t) => t.length === 2));
    const hasStop = [...kwBigrams].some((t) => STOP_BIGRAMS.has(t));
    const isNoisy = kwLen <= 2 && hasStop;
    const isHighSpecificity = kwLen >= 3 && !hasStop;

    let kwWeight: number;
    if (isNoisy) kwWeight = 0.15;
    else if (hasStop && kwLen <= 2) kwWeight = 0.2;
    else if (hasStop) kwWeight = 0.5;
    else if (isHighSpecificity) kwWeight = 2.0;
    else if (kwLen >= 3) kwWeight = 1.0;
    else kwWeight = 0.4;

    // 精确匹配
    const directMatch =
      taskTokens.has(kwLower) ||
      [...taskTokens].some((t) => t.length >= 2 && t === kwLower) ||
      [...kwTokens].some((kt) => kt.length >= 2 && taskTokens.has(kt));

    if (directMatch) {
      matched.push(kw);
      matchedScore += kwWeight;
      continue;
    }

    // 反向匹配
    const contained = [...taskTokens].filter(
      (t) => t.length >= 2 && kwLower.includes(t) && !STOP_BIGRAMS.has(t)
    );
    if (contained.length > 0) {
      fuzzyMatched.push(kw);
      matchedScore += kwWeight * 0.3;
    }
  }

  const score = Math.min(matchedScore / 3.0, 1.0);
  return {
    matched: [...matched, ...fuzzyMatched.map((m) => `${m}≈`)],
    score,
  };
}

interface ExcludeResult {
  triggered: string[];
  risk: "none" | "soft" | "hard";
}

/** 排除条件检查 */
function excludeCheck(taskLower: string, excludeText: string): ExcludeResult {
  if (!excludeText) return { triggered: [], risk: "none" };

  const excludes = excludeText.split(/[、,，/]/).map((e) => e.trim()).filter(Boolean);
  const hardTriggered: string[] = [];
  const softTriggered: string[] = [];
  const taskTokensLower = new Set(
    [...tokenize(taskLower)].map((t) => t.toLowerCase())
  );

  for (const ex of excludes) {
    const exLower = ex.toLowerCase();
    const exTokens = tokenize(exLower);
    const exLen = ex.length;

    if (taskLower.includes(exLower)) {
      if (exLen >= 4) {
        hardTriggered.push(ex);
      } else if (exLen >= 3) {
        const idx = taskLower.indexOf(exLower);
        const contextBefore = taskLower.slice(Math.max(0, idx - 10), idx);
        const isSubordinate = ["包括", "例如", "比如", "除了", "除", "附带", "此外", "以及"].some(
          (m) => contextBefore.includes(m)
        );
        if (isSubordinate) softTriggered.push(`${ex}~`);
        else hardTriggered.push(ex);
      } else {
        softTriggered.push(`${ex}~`);
      }
      continue;
    }

    // 模糊匹配
    if (exTokens.size >= 2) {
      const overlap = [...exTokens].filter((t) => taskTokensLower.has(t));
      if (overlap.length >= exTokens.size * 0.5) {
        softTriggered.push(`${ex}?`);
      }
    }
  }

  const allTriggered = [...hardTriggered, ...softTriggered];
  if (hardTriggered.length > 0) return { triggered: allTriggered, risk: "hard" };
  if (softTriggered.length > 0) return { triggered: allTriggered, risk: "soft" };
  return { triggered: [], risk: "none" };
}

/** 对单个魂评分 */
function scoreSoul(
  soul: SoulEntry,
  task: string
): MatchResult {
  const taskLower = task.toLowerCase();
  const taskTokensLower = new Set([...tokenize(task)].map((t) => t.toLowerCase()));
  const taskTokens = new Set([...tokenize(task), ...taskTokensLower]);

  // 1. 关键词匹配
  const kwText = soul.trigger_keywords_summary || "";
  const kwResult = keywordOverlap(taskTokens, kwText);

  // 2. 场景匹配
  const scText = soul.trigger_scenarios_summary || "";
  const scResult = keywordOverlap(taskTokens, scText);

  // 3. 排除检查
  const exText = soul.trigger_exclude_summary || "";
  const exResult = excludeCheck(taskLower, exText);

  // 4. 领域加分
  const domains = soul.domain || [];
  let domainBonus = 0;
  const domainMatches: string[] = [];
  for (const d of domains) {
    if (task.includes(d) || [...tokenize(d)].some((t) => taskLower.includes(t))) {
      domainBonus += 0.05;
      domainMatches.push(d);
    }
  }
  domainBonus = Math.min(domainBonus, 0.2);

  // 综合评分
  let score = kwResult.score * 0.5 + scResult.score * 0.3 + domainBonus;

  // 排除惩罚
  if (exResult.risk === "hard") score *= 0.1;
  else if (exResult.risk === "soft") score *= 0.5;

  return {
    name: soul.name,
    score: Math.min(score, 1.0),
    info_sufficiency: soul.info_sufficiency || "?",
    function_domains: soul.function_domains || [],
    methodology_transferability: soul.methodology_transferability || "?",
    domain: domains,
    keyword_matches: kwResult.matched,
    scenario_matches: scResult.matched,
    exclude_risk: exResult.risk,
    exclude_triggered: exResult.triggered,
    keyword_score: kwResult.score,
    scenario_score: scResult.score,
    domain_bonus: domainBonus,
    gold_review: (soul.gold_review || "").slice(0, 200),
  };
}

/** 认知距离调整：使用越少的魂越优先 */
function applyCognitiveDistance(
  results: MatchResult[],
  usageCounts: Map<string, number>
): MatchResult[] {
  if (usageCounts.size === 0) return results;

  const freshnessScores = new Map<string, number>();
  for (const r of results) {
    const usage = usageCounts.get(r.name) || 0;
    freshnessScores.set(r.name, 1.0 / (1 + Math.log(usage + 1)));
  }

  const vals = [...freshnessScores.values()];
  const minV = Math.min(...vals);
  const maxV = Math.max(...vals);
  if (maxV === minV) return results;

  for (const r of results) {
    const f = freshnessScores.get(r.name) || 0.5;
    const normalized = ((f - minV) / (maxV - minV)) * 0.1 - 0.05;
    r.score = Math.min(Math.round((r.score + normalized) * 1000) / 1000, 1.0);
    r.freshness_bonus = Math.round(normalized * 1000) / 1000;
  }

  return results;
}

const RISK_ORDER: Record<string, number> = { none: 0, soft: 1, hard: 2 };

/** 主匹配函数 */
export function matchSouls(
  task: string,
  souls: SoulEntry[],
  usageCounts: Map<string, number>,
  topN = 5
): { primary: MatchResult | null; alternatives: MatchResult[] } {
  const scored: MatchResult[] = [];

  for (const soul of souls) {
    const result = scoreSoul(soul, task);
    if (result.score > 0 || result.exclude_risk !== "none") {
      scored.push(result);
    }
  }

  applyCognitiveDistance(scored, usageCounts);

  scored.sort(
    (a, b) =>
      (RISK_ORDER[a.exclude_risk] || 0) - (RISK_ORDER[b.exclude_risk] || 0) ||
      b.score - a.score
  );

  const top = scored.slice(0, topN);
  return {
    primary: top.length > 0 ? top[0] : null,
    alternatives: top.slice(1),
  };
}

/** 生成匹配结果的 Markdown 格式 */
export function formatMatchMarkdown(
  task: string,
  primary: MatchResult | null,
  alternatives: MatchResult[]
): string {
  const lines: string[] = [];
  lines.push("## 匹配预筛选\n");
  lines.push(`**任务**: ${task}\n`);

  if (primary) {
    const p = primary;
    const funcStr = p.function_domains.join("+");
    lines.push("### 首选\n");
    lines.push(
      `**${p.name}** — 匹配分 ${p.score.toFixed(2)}`
    );
    lines.push(
      `- 功能域: ${funcStr} | 信息充分度: ${p.info_sufficiency} | 方法论: ${p.methodology_transferability}`
    );
    lines.push(`- 触发关键词: ${p.keyword_matches.slice(0, 8).join(", ") || "无"}`);
    lines.push(`- 触发场景: ${p.scenario_matches.slice(0, 5).join(", ") || "无"}`);
    const riskLabel = { none: "无", soft: "软排除", hard: "硬排除" }[p.exclude_risk];
    lines.push(
      `- 排除风险: ${riskLabel} ${p.exclude_triggered.length ? p.exclude_triggered.join(", ") : ""}`
    );
    lines.push(`- 领域: ${p.domain.join(", ")}`);
    if (p.gold_review) lines.push(`- Gold Review: ${p.gold_review}`);
    if (p.freshness_bonus) lines.push(`- 认知新鲜度调整: ${p.freshness_bonus > 0 ? "+" : ""}${p.freshness_bonus}`);
    lines.push("");
  }

  if (alternatives.length > 0) {
    lines.push("### 备选\n");
    alternatives.forEach((a, i) => {
      const funcStr = a.function_domains.join("+");
      lines.push(
        `${i + 1}. **${a.name}** (${funcStr}, ${a.score.toFixed(2)}) — ${
          a.keyword_matches.slice(0, 4).join(", ") || "无关键词命中"
        }`
      );
    });
    lines.push("");
  }

  // 排除清单
  const hardExclude = [primary, ...alternatives].filter(
    (r) => r.exclude_risk === "hard"
  );
  const softExclude = [primary, ...alternatives].filter(
    (r) => r.exclude_risk === "soft"
  );

  if (hardExclude.length > 0) {
    lines.push("### 硬排除预警\n");
    for (const e of hardExclude) {
      lines.push(
        `- **${e.name}**: 排除词命中 → ${e.exclude_triggered.slice(0, 5).join(", ")}`
      );
    }
    lines.push("");
  }
  if (softExclude.length > 0) {
    lines.push("### 软排除提示\n");
    for (const e of softExclude) {
      lines.push(
        `- **${e.name}** (评分 ×0.5): ${e.exclude_triggered.slice(0, 5).join(", ")}`
      );
    }
    lines.push("");
  }

  // 审查清单
  lines.push("### 幡主审查清单\n");
  lines.push("请逐条回答（每条一句话）：");
  lines.push("1. **领域匹配**: 首选魂的领域是否覆盖此任务？[Y/N]");
  lines.push("2. **排除风险**: 排除条件是否实质性触发？[Y/N + 哪个]");
  lines.push("3. **边界风险**: 适用边界外溢风险？[无/低/中/高 + 简述]");
  lines.push("4. **裁决**: [通过 / 换X / 加Y约束 / 需第二审查官]");

  return lines.join("\n");
}
