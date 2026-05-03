/** 万民幡 MCP Server — 注册表加载与内存缓存 */

import fs from "node:fs";
import path from "node:path";
import yaml from "yaml";
import { PATHS } from "./constants.js";
import type { SoulEntry, SoulProfile, CallRecord } from "./types.js";

/** 内存缓存 */
let souls: SoulEntry[] = [];
let soulProfiles: Map<string, SoulProfile> = new Map();
let callRecords: CallRecord[] = [];
let usageCounts: Map<string, number> = new Map();
let loadedAt = 0;

function parseYamlFile<T>(filepath: string, fallback: T): T {
  try {
    const raw = fs.readFileSync(filepath, "utf-8");
    return yaml.parse(raw) as T;
  } catch {
    return fallback;
  }
}

export function loadAll(): void {
  const registry = parseYamlFile<{ 魂魄?: SoulEntry[] }>(PATHS.REGISTRY, {});
  const allSouls = (registry.魂魄 || []).filter(
    (s) => s.status !== "dismissed"
  );
  souls = allSouls;

  // 加载完整魂档案
  soulProfiles.clear();
  if (fs.existsSync(PATHS.SOULS_DIR)) {
    for (const file of fs.readdirSync(PATHS.SOULS_DIR)) {
      if (!file.endsWith(".yaml")) continue;
      try {
        const profile = parseYamlFile<SoulProfile>(
          path.join(PATHS.SOULS_DIR, file),
          {} as SoulProfile
        );
        if (profile.name) {
          soulProfiles.set(profile.name, profile);
        }
      } catch {
        // 跳过损坏文件
      }
    }
  }

  // 加载调用记录
  const cr = parseYamlFile<{ records?: CallRecord[] }>(PATHS.CALL_RECORDS, {});
  callRecords = cr.records || [];

  // 统计使用次数
  usageCounts.clear();
  for (const r of callRecords) {
    const name = r.soul;
    if (name) {
      usageCounts.set(name, (usageCounts.get(name) || 0) + 1);
    }
  }

  loadedAt = Date.now();
  console.error(
    `[soul-banner-mcp] 已加载 ${souls.length} 魂 + ${soulProfiles.size} 档案 + ${callRecords.length} 调用记录`
  );
}

/** 热重载：仅在文件有变化时重新加载 */
export function reloadIfStale(): boolean {
  try {
    const mtime = fs.statSync(PATHS.REGISTRY).mtimeMs;
    if (mtime > loadedAt) {
      loadAll();
      return true;
    }
  } catch {
    // 文件不存在，保持当前缓存
  }
  return false;
}

export function getSouls(): SoulEntry[] {
  return souls;
}

export function getSoulProfile(name: string): SoulProfile | undefined {
  // 先查完整档案
  const cached = soulProfiles.get(name);
  if (cached) return cached;

  // 回退到 registry 中的简要信息
  const entry = souls.find((s) => s.name === name);
  if (entry) return entry as SoulProfile;

  return undefined;
}

export function getUsageCounts(): Map<string, number> {
  return usageCounts;
}

export function getCallRecords(): CallRecord[] {
  return callRecords;
}
