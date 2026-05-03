/** 万民幡 MCP Server — 类型定义 */

export interface SoulEntry {
  name: string;
  info_sufficiency: "充分" | "中等" | "不足";
  function_domains: string[];
  methodology_transferability: "可传输" | "嵌入型" | "人格型";
  domain: string[];
  trigger_keywords_summary: string;
  trigger_scenarios_summary: string;
  trigger_exclude_summary: string;
  gold_review?: string;
  status?: string;
  [key: string]: unknown;
}

export interface SoulProfile extends SoulEntry {
  mind?: string;
  voice?: string;
  summon_prompt?: string;
  reviewed_at?: string;
  reviewed_by?: string;
  review_verdict?: string;
}

export interface CallRecord {
  date: string;
  soul: string;
  mode: string;
  task: string;
  effectiveness: string;
  notes?: string;
  self_negation?: string;
  empty_chair?: string;
}

export interface MatchResult {
  name: string;
  score: number;
  info_sufficiency: string;
  function_domains: string[];
  methodology_transferability: string;
  domain: string[];
  keyword_matches: string[];
  scenario_matches: string[];
  exclude_risk: "none" | "soft" | "hard";
  exclude_triggered: string[];
  keyword_score: number;
  scenario_score: number;
  domain_bonus: number;
  freshness_bonus?: number;
  gold_review?: string;
}

export interface MatchOutput {
  task: string;
  total_souls: number;
  primary: MatchResult | null;
  alternatives: MatchResult[];
}
