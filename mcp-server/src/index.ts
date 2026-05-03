#!/usr/bin/env bun
/**
 * 万民幡 MCP Server — 魂魄匹配、档案查询、注册表缓存
 *
 * 通过 stdio 与 Claude Code 通信，启动时将 registry 全量加载到内存，
 * 后续所有查询均从内存缓存读取。
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { PATHS } from "./constants.js";
import { loadAll, getSouls, getSoulProfile, getUsageCounts, getCallRecords, reloadIfStale } from "./registry.js";
import { matchSouls, formatMatchMarkdown } from "./matcher.js";

// ═══ 启动时加载全量数据 ═══
loadAll();

// ═══ 创建 MCP Server ═══
const server = new McpServer({
  name: "soul-banner-mcp-server",
  version: "1.0.0",
});

// ═══════════════════════════════════════════════
// Tool 1: soul_match — 魂魄匹配
// ═══════════════════════════════════════════════
const MatchInputSchema = z.object({
  task: z.string()
    .min(2, "任务描述至少 2 个字符")
    .describe("任务描述（中文），用于匹配最合适的魂魄"),
  top_n: z.number()
    .int().min(1).max(10).default(5)
    .describe("返回的候选魂数量"),
  include_review_checklist: z.boolean()
    .default(true)
    .describe("是否包含幡主审查清单"),
}).strict();

server.registerTool(
  "soul_match",
  {
    title: "匹配魂魄",
    description: `根据任务描述匹配最合适的万民幡魂魄。返回首选魂 + 备选清单 + 排除预警 + 幡主审查清单。

输入任务描述（如"分析杨笠段子的性别权力结构"），自动进行关键词匹配、场景匹配、排除条件检查、认知距离调整。

Returns:
  Markdown 格式的匹配报告，包含：
  - 首选魂及其匹配详情（关键词/场景/排除风险/领域/Gold Review）
  - 备选魂列表（按匹配分排序）
  - 硬排除/软排除预警
  - 幡主审查清单`,
    inputSchema: MatchInputSchema,
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: false,
    },
  },
  async ({ task, top_n, include_review_checklist }) => {
    try {
      reloadIfStale();
      const souls = getSouls();
      const usageCounts = getUsageCounts();

      const { primary, alternatives } = matchSouls(task, souls, usageCounts, top_n);

      let text = formatMatchMarkdown(task, primary, alternatives);

      if (!include_review_checklist) {
        // 去掉审查清单部分
        const idx = text.indexOf("### 幡主审查清单");
        if (idx > 0) text = text.slice(0, idx).trimEnd();
      }

      const output = {
        task,
        total_souls: souls.length,
        primary: primary
          ? {
              name: primary.name,
              score: primary.score,
              function_domains: primary.function_domains,
              info_sufficiency: primary.info_sufficiency,
              methodology_transferability: primary.methodology_transferability,
              exclude_risk: primary.exclude_risk,
              domain: primary.domain,
            }
          : null,
        alternatives_count: alternatives.length,
      };

      return {
        content: [{ type: "text", text }],
        structuredContent: output,
      };
    } catch (error) {
      return {
        content: [{
          type: "text",
          text: `匹配失败: ${error instanceof Error ? error.message : String(error)}`,
        }],
      };
    }
  }
);

// ═══════════════════════════════════════════════
// Tool 2: soul_profile — 魂档案查询
// ═══════════════════════════════════════════════
const ProfileInputSchema = z.object({
  name: z.string()
    .min(1, "魂魄名称不能为空")
    .describe("魂魄名称，如 '鲁迅'、'波伏娃'、'列宁'"),
}).strict();

server.registerTool(
  "soul_profile",
  {
    title: "查询魂魄档案",
    description: `获取指定魂魄的完整档案，包括功能域标签、方法论可传输度、触发关键词/场景/排除条件、审查记录等。

Args:
  - name: 魂魄名称

Returns:
  魂魄完整档案的 Markdown 格式，包含 YAML frontmatter 中的所有字段。`,
    inputSchema: ProfileInputSchema,
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: false,
    },
  },
  async ({ name }) => {
    try {
      const profile = getSoulProfile(name);
      if (!profile) {
        return {
          content: [{
            type: "text",
            text: `未找到魂魄「${name}」。可用 /soul-banner → 幡中有什么魂 查看所有魂魄。`,
          }],
        };
      }

      const lines: string[] = [];
      lines.push(`# ${profile.name}\n`);
      lines.push(`- **信息充分度**: ${profile.info_sufficiency || "?"}`);
      lines.push(`- **功能域**: ${(profile.function_domains || []).join("、")}`);
      lines.push(`- **方法论可传输度**: ${profile.methodology_transferability || "?"}`);
      lines.push(`- **领域**: ${(profile.domain || []).join("、")}`);
      if (profile.trigger_keywords_summary) {
        lines.push(`- **触发关键词**: ${profile.trigger_keywords_summary}`);
      }
      if (profile.trigger_scenarios_summary) {
        lines.push(`- **触发场景**: ${profile.trigger_scenarios_summary}`);
      }
      if (profile.trigger_exclude_summary) {
        lines.push(`- **排除条件**: ${profile.trigger_exclude_summary}`);
      }
      if (profile.gold_review) {
        lines.push(`\n## 审查记录\n\n${profile.gold_review}`);
      }

      return {
        content: [{ type: "text", text: lines.join("\n") }],
        structuredContent: {
          name: profile.name,
          info_sufficiency: profile.info_sufficiency,
          function_domains: profile.function_domains,
          methodology_transferability: profile.methodology_transferability,
          domain: profile.domain,
        },
      };
    } catch (error) {
      return {
        content: [{
          type: "text",
          text: `查询失败: ${error instanceof Error ? error.message : String(error)}`,
        }],
      };
    }
  }
);

// ═══════════════════════════════════════════════
// Tool 3: soul_list — 列出所有魂魄
// ═══════════════════════════════════════════════
const ListInputSchema = z.object({
  function_domain: z.string()
    .optional()
    .describe("按功能域过滤：批判型、建设型、组织型、分析型、叙事型、情绪型"),
  info_sufficiency: z.enum(["充分", "中等", "不足"])
    .optional()
    .describe("按信息充分度过滤"),
  methodology: z.enum(["可传输", "嵌入型", "人格型"])
    .optional()
    .describe("按方法论可传输度过滤"),
}).strict();

server.registerTool(
  "soul_list",
  {
    title: "列出所有魂魄",
    description: `列出万民幡中所有可用魂魄，支持按功能域、信息充分度、方法论可传输度过滤。

Args:
  - function_domain (optional): 功能域过滤
  - info_sufficiency (optional): 信息充分度过滤
  - methodology (optional): 方法论可传输度过滤

Returns:
  魂魄列表，含名称、功能域、信息充分度、方法论、领域。`,
    inputSchema: ListInputSchema,
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: false,
    },
  },
  async ({ function_domain, info_sufficiency, methodology }) => {
    try {
      reloadIfStale();
      let souls = getSouls();

      if (function_domain) {
        souls = souls.filter((s) =>
          (s.function_domains || []).includes(function_domain)
        );
      }
      if (info_sufficiency) {
        souls = souls.filter((s) => s.info_sufficiency === info_sufficiency);
      }
      if (methodology) {
        souls = souls.filter((s) => s.methodology_transferability === methodology);
      }

      const lines: string[] = [];
      lines.push(`# 万民幡魂魄列表 (${souls.length} 魂)\n`);

      // 按功能域分组
      for (const domain of ["批判型", "建设型", "组织型", "分析型", "叙事型", "情绪型"]) {
        const inDomain = souls.filter((s) =>
          (s.function_domains || []).includes(domain)
        );
        if (inDomain.length === 0) continue;
        lines.push(`## ${domain}\n`);
        for (const s of inDomain) {
          const suf = s.info_sufficiency === "充分" ? "" : ` [${s.info_sufficiency}]`;
          const meth = { "可传输": "📦", "嵌入型": "🔗", "人格型": "👤" }[s.methodology_transferability || ""] || "";
          lines.push(
            `- **${s.name}**${suf} ${meth} — ${(s.domain || []).slice(0, 3).join("、")}`
          );
        }
        lines.push("");
      }

      return {
        content: [{ type: "text", text: lines.join("\n") }],
        structuredContent: {
          total: souls.length,
          souls: souls.map((s) => ({
            name: s.name,
            function_domains: s.function_domains,
            info_sufficiency: s.info_sufficiency,
            methodology_transferability: s.methodology_transferability,
            domain: s.domain,
          })),
        },
      };
    } catch (error) {
      return {
        content: [{
          type: "text",
          text: `查询失败: ${error instanceof Error ? error.message : String(error)}`,
        }],
      };
    }
  }
);

// ═══════════════════════════════════════════════
// Tool 4: soul_handbook — 匹配手册
// ═══════════════════════════════════════════════
server.registerTool(
  "soul_handbook",
  {
    title: "获取匹配手册",
    description: `获取幡主匹配手册，包含各魂的效能统计（成功/失败次数）、失败修正建议、零召唤魂预警。

基于 call-records.yaml 自动生成，帮助幡主做出更精准的匹配审查判断。`,
    inputSchema: z.object({}).strict(),
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: false,
    },
  },
  async () => {
    try {
      reloadIfStale();
      const souls = getSouls();
      const records = getCallRecords();

      // 按魂聚合
      const soulStats = new Map<string, { success: number; fail: number; topics: string[] }>();
      for (const r of records) {
        if (!r.soul || r.soul === "辩证综合官") continue;
        const stats = soulStats.get(r.soul) || { success: 0, fail: 0, topics: [] };
        if (r.effectiveness === "有效") stats.success++;
        else if (r.effectiveness === "无效") stats.fail++;
        if (r.task) stats.topics.push(r.task);
        soulStats.set(r.soul, stats);
      }

      const called = new Set<string>();
      for (const r of records) called.add(r.soul);

      const lines: string[] = [];
      lines.push("# 幡主匹配手册\n");
      lines.push(`*${records.length}次附体 · ${new Date().toISOString().slice(0, 10)}生成*\n`);
      lines.push("## 魂效能速查\n");

      for (const [soul, stats] of [...soulStats.entries()].sort((a, b) => b[1].success - a[1].success)) {
        const total = stats.success + stats.fail;
        const rate = total > 0 ? stats.success / total : 0;
        const icon = rate >= 0.8 ? "🟢" : rate >= 0.5 ? "🟡" : "🔴";
        const entry = souls.find((s) => s.name === soul);
        const suf = entry?.info_sufficiency || "?";
        lines.push(`- ${icon} **${soul}**(${suf}) ${stats.success}/${total}有效`);
      }

      // 零召唤
      const zeroCall = souls.filter(
        (s) => !called.has(s.name) && s.status !== "dismissed"
      );
      if (zeroCall.length > 0) {
        lines.push(`\n## 零召唤: ${zeroCall.map((s) => s.name).join(", ")}\n`);
      }

      return {
        content: [{ type: "text", text: lines.join("\n") }],
      };
    } catch (error) {
      return {
        content: [{
          type: "text",
          text: `生成手册失败: ${error instanceof Error ? error.message : String(error)}`,
        }],
      };
    }
  }
);

// ═══════════════════════════════════════════════
// Tool 5: soul_reload — 热重载
// ═══════════════════════════════════════════════
server.registerTool(
  "soul_reload",
  {
    title: "热重载注册表",
    description: `重新加载 registry.yaml 和 call-records.yaml。在收魂/炼化/审查落盘后调用，使变更立即生效而不需要重启 MCP Server。`,
    inputSchema: z.object({}).strict(),
    annotations: {
      readOnlyHint: false,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: false,
    },
  },
  async () => {
    try {
      loadAll();
      const souls = getSouls();
      const records = getCallRecords();
      return {
        content: [{
          type: "text",
          text: `✅ 注册表已重载：${souls.length} 魂，${records.length} 条调用记录`,
        }],
        structuredContent: {
          soul_count: souls.length,
          record_count: records.length,
          reloaded_at: new Date().toISOString(),
        },
      };
    } catch (error) {
      return {
        content: [{
          type: "text",
          text: `重载失败: ${error instanceof Error ? error.message : String(error)}`,
        }],
      };
    }
  }
);

// ═══ 启动 stdio 传输 ═══
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("[soul-banner-mcp] 万民幡 MCP Server 已启动 (stdio)");
}

main().catch((error) => {
  console.error("启动失败:", error);
  process.exit(1);
});
