/** 万民幡 MCP Server — 常量与路径 */

import { fileURLToPath } from "node:url";
import path from "node:path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const MCP_DIR = path.resolve(__dirname, "..");
const SKILL_DIR = path.resolve(MCP_DIR, "..");

export const PATHS = {
  SKILL_DIR,
  REGISTRY: path.join(SKILL_DIR, "registry.yaml"),
  REGISTRY_LITE: path.join(SKILL_DIR, "registry-lite.yaml"),
  CALL_RECORDS: path.join(SKILL_DIR, "call-records.yaml"),
  SOULS_DIR: path.join(SKILL_DIR, "souls"),
  COMMITTEE_DIR: path.join(SKILL_DIR, "committee"),
} as const;

/** 高频干扰 bigram（区分度低）— 与 match.py 保持一致 */
export const STOP_BIGRAMS = new Set([
  "分析", "主义", "批判", "理论", "哲学", "制度", "组织", "建设",
  "战略", "决策", "设计", "系统", "技术", "管理", "研究", "方法",
  "实践", "科学", "思维", "认识", "社会", "革命", "政治", "经济",
  "文学", "精神", "知识", "学习", "传播", "教育", "文化", "历史",
]);
