# 万魂幡项目指令

## 强制规则

遇到以下任务类型，主 agent 必须调用 Skill(soul-banner)，禁止自行处理：
1. 涉及两个及以上不同思维模式/人物视角的分析
2. 需要辩证综合（找共识/找分歧/找盲区）
3. 合议/辩论/接力/收魂/炼化等万魂幡命令词

## 禁止行为

详见 **[feedback_soul_banner_prohibition_rules](memory://feedback_soul_banner_prohibition_rules.md)** — 四条核心禁止规则由 memory 系统维护，所有 soul-banner 对话自动加载。

## 操作约定

**Task 追踪**：多步骤仪轨启动时，主 agent 必须用 `TaskCreate` 创建全部步骤，完成后确认全部 Task 为 `completed`。具体模板详见 **[tasks.md](tasks.md)**（按需加载，启动时不读取）。

**魂魄 agent 文件**：所有魂在 `~/.claude/agents/{魂名}.md` 有标准化 agent 定义（含 summon_prompt、tools、model），由 `scripts/sync-agent.py --all` 从 soul YAML 自动生成。**禁止手动编辑 agent 文件**——soul YAML 是唯一真相源。每次炼化/升级后必须重新同步：`python3 scripts/sync-agent.py souls/{魂名}.yaml`。spawn 魂时直接使用 `subagent_type="{魂名}"`。重启 Claude Code 后新 agent 生效。

**审查 spawn**：日常匹配审查 spawn `subagent_type="列宁"`（幡主，效率优先，不轮值）。金魂互审和终末审查按轮值表 spawn 对应审查官（毛泽东/邓小平/列宁），第二审查官复核。详见 `soul-profile-format.md`「审查轮值制」。

**匹配审查轻量化**（三步）：

1. **预筛选**：主 agent 运行 `python3 scripts/match.py "任务描述" --no-gold-review` 做关键词/场景/排除评分，输出首选+备选+排除清单。`--no-gold-review` 省略 gold_review 字段，节省 ~1,500 tokens。
2. **幡主审查**：主 agent 将两份内容注入幡主 prompt：
   - `match.py` 预筛选结果（当前任务匹配详情）
   - `committee/handbook.md`（历史匹配经验，由 `generate-handbook.py` 自动生成，~270 tokens）
   
   **幡主审查阶段硬性禁读**：幡主必须仅基于 prompt 中已注入的预筛选结果和 handbook 做判断，**禁止读取任何文件**（包括 registry.yaml、registry-lite.yaml、魂 YAML、call-records.yaml）。按结构化清单回答：领域匹配 / 排除风险 / 边界风险 / 裁决。
3. **深度审查**：匹配通过后，幡主才读完整魂 YAML 做深度审查。

**手册更新**：每次附体落盘后（`transact.py possession-close`），主 agent 运行 `python3 scripts/generate-handbook.py -o committee/handbook.md --compact` 更新手册。手册约 270 tokens，自动从 `call-records.yaml` 提取魂效能统计+失败模式+零召唤预警。

`registry-lite.yaml` 由 `scripts/generate-registry-lite.py` 从 `registry.yaml` 自动生成。每次 `registry.yaml` 更新后主 agent 须重新生成。

**辩证综合 spawn**：合议模式阶段二，spawn `subagent_type="辩证综合官"`。该 agent 定义了五步综合法（共识/分歧/盲区/主要矛盾/行动纲领）。

**⚠️ 魂输出原文保全规则（硬性，合议/辩论/接力通用）**：

**原则**：主 agent **禁止**用自己的话改写魂输出——无论是传给下游 agent 还是存档 Obsidian。魂输出必须是原文。

**流程**：
1. 每个魂子 agent 返回后，主 agent **立即**将其输出写入 `/tmp/sb-{任务}/{魂名}.md`。写文件时必须逐字复制 agent 返回的原文，禁止概括、压缩、改写、重新组织。
2. `/tmp/sb-{任务}/` 下的文件是本次附体的**权威副本**——后续所有操作只读这些文件，不重新生成内容。
3. **辩证综合官**：prompt 中只给文件路径清单，自己 Read 原文。
4. **Obsidian 存档**：manifest.json 中 `file` 字段指向 `/tmp/sb-{任务}/{魂名}.md`，`transact.py` 直接从权威副本复制到 Obsidian。

**理由**：主 agent 接收魂输出后有两种篡改冲动——①传给辩证综合官时压缩以"整洁"prompt（已发现），②写 Obsidian 存档时概括以"精简"文件（已发现）。两个冲动同源：主 agent 把自己当成了编辑。用权威副本机制阻断——魂输出→立即写文件→此后只读不写。主 agent 连原文都不该"持有"在 prompt 中，收到即落盘。

**辩证综合官 prompt 模板**：
```
## 任务
{任务描述}

## 各魂分析文件（请自行 Read 每个文件获取原文）
- /tmp/sb-{任务}/{魂A}.md
- /tmp/sb-{任务}/{魂B}.md
- /tmp/sb-{任务}/{魂C}.md

## 幡主预审约束
{约束条件}

请先 Read 全部文件，再做辩证综合。
```

## Skill 集成规则

### markitdown — 收魂格式转换（免费开源）

收魂步骤 4 自动生成 `raw/{魂名}/媒体链接.md`。步骤 5 由主 agent 对每个链接调用 markitdown：
```
对 raw/{魂名}/媒体链接.md 中的每个非空链接，调用 Skill("markitdown") 转换，输出保存至 raw/{魂名}/转换素材/
```
转换素材纳入炼化阶段的读取范围。

### humanizer — 去 AI 痕迹（免费，纯 LLM，无外部 API）

触发点两处：
1. **炼化后**：Soul Profile 生成后，调用 `Skill("humanizer")` 处理 mind/voice/summon_prompt 字段
2. **附体后**：每个魂的附体输出，在存档 Obsidian 前调用 `Skill("humanizer")`

**硬性约束**：不同魂的语言风格必须保持差异。humanizer 指令必须包含该魂 voice 字段的风格保留声明。禁止用 humanizer 统一所有魂的语言风格。

### 收魂搜索回退链（全部免费）

收魂搜索按优先级回退，所有方案均为免费：

1. **tmwd-bridge**（推荐）— 真实 Chrome 多引擎搜索，保留登录态，反检测。需安装 [GenericAgent](https://github.com/lsdefine/GenericAgent) Chrome 扩展
2. **WebSearch + WebFetch**（内置，零配置）— Claude Code 内置搜索和抓取工具，tmwd-bridge 不可用时的首选回退
3. **agent-browser**（免费开源）— 无头浏览器，JS 渲染页面批量抓取。安装：`npm install -g agent-browser`

```bash
# tmwd-bridge（默认）
python3 scripts/soul-search.py "{人物名}" -o raw/{人物名}/

# 内置 WebSearch/WebFetch（零配置回退）
# 主 agent 直接调用 WebSearch + WebFetch 逐维度搜索

# agent-browser（备选）
python3 scripts/soul-search.py "{人物名}" --engine agent-browser -o raw/{人物名}/
```

可选付费：火山引擎联网搜索 API（每月 500 次免费额度，超出付费），仅在以上方案均不可用时考虑。

### graphify — 审查知识图谱（可选，免费）

每次审查/互审报告保存后，调用 `Skill("graphify")` 更新知识图谱。图谱用于审查关系可视化和思想谱系追踪。非强制性——图谱损坏不影响万魂幡核心功能。

### loop — 运维自动化（内置免费）

**边界**：只自动化运维检查，不自动化判断行为。禁止用 loop 自动执行审查/互审/品级调整。

设置维护循环：
```
/loop 1h python3 ~/.claude/skills/soul-banner/scripts/registry-health-check.py
/loop 6h python3 ~/.claude/skills/soul-banner/scripts/cross-validate.py
/loop 24h python3 ~/.claude/skills/soul-banner/scripts/transact.py sync-all
/loop 168h python3 ~/.claude/skills/soul-banner/scripts/state-summary.py --json > /tmp/soul-banner-weekly.json
```
审查委员会轮值调度不使用 loop——轮值由幡主在每次附体时手动判断。

**Spawn 魂的标准模板**：
```
Agent(
  subagent_type="{魂名}",
  description="{任务简述} — {魂名}视角",
  prompt="{任务描述}"
)
```

**Spawn 幡主审查专用模板**（必须严格遵循）：
```
Agent(
  subagent_type="列宁",
  description="幡主匹配审查",
  prompt="匹配预筛选结果：
{match.py --no-gold-review 的完整输出}

---
禁止读取任何文件。仅基于以上预筛选结果和已知的魂领域知识做判断。按清单回答：领域匹配 / 排除风险 / 边界风险 / 裁决。"
)
```
审查 prompt 中必须包含「**禁止读取任何文件**」，且预筛选结果使用 `--no-gold-review` 精简版。

### 事务脚本（transact.py）— 落盘自动化

所有落盘操作统一通过 `scripts/transact.py` 子命令执行，**禁止**主 agent 手写 heredoc Python 更新文件。

**原则**：主 agent 做判断（评级/裁决/匹配），判断完成后调 `transact.py` 落盘。事务脚本不替代判断，只替代机械操作。

| 时机 | 子命令 | 示例 |
|------|--------|------|
| 炼化完成 | `refine-close <魂名>` | `python3 scripts/transact.py refine-close 鲁迅` |
| 审查/互审完成 | `review-apply <魂名> --review-file <路径> [--verdict "..."] [--grade X] [--reviewer X]` | `python3 scripts/transact.py review-apply 费曼 --review-file reviews/金魂互审-鲁迅审费曼-2026-05-02.md --verdict "维持金魂"` |
| 附体结束 | `possession-close <魂名> --mode <模式> --task <任务> --effectiveness <有效\|部分有效\|无效> [--notes "..."] [--obsidian-content <文件> \| --obsidian-batch <manifest.json> \| --obsidian-stdin]` | `python3 scripts/transact.py possession-close 鲁迅 --mode 单魂 --task "组织文化诊断" --effectiveness 有效 --notes "揭露了三点自欺" --obsidian-content /tmp/output.md` |
| 散魂 | `dismiss <魂名> [--reason "..."]` | `python3 scripts/transact.py dismiss 海绵宝宝 --reason "终末审查裁定散魂"` |
| Obsidian 同步 | `obsidian-sync [--souls X,Y] [--reviews-only] [--dry-run]` | `python3 scripts/transact.py obsidian-sync` |
| 会议准备 | `meeting-prep` | `python3 scripts/transact.py meeting-prep` |
| 全量同步 | `sync-all` | `python3 scripts/transact.py sync-all` |

**委员会裁决自动生效**：裁决做出后立即调用 `transact.py review-apply` 或 `transact.py dismiss`，无需等待用户确认。

**炼化后强制校验**：`transact.py refine-close` 内部调用 `validate_soul`，valid=False 则中止。

**Obsidian 存档方式**（按场景选择）：
- **单魂**：魂输出 Write 到临时文件 → `--obsidian-content /tmp/out.md`
- **stdin 管道**：短内容直接管道传入 → `echo "$content" | python3 scripts/transact.py possession-close ... --obsidian-stdin`
- **多魂合议/辩论/接力**：写 manifest.json 描述 N 个文件 → `--obsidian-batch /tmp/manifest.json`。manifest 格式：
  ```json
  {"mode": "合议", "task": "任务名", "date": "2026-05-02", "files": [
    {"soul": "魂A", "role": "角色", "file": "/tmp/soul-a.md"},
    {"soul": "魂B", "role": "角色", "file": "/tmp/soul-b.md"}
  ]}
  ```
- **全量同步**：`transact.py obsidian-sync` 同步全部魂魄+审查报告+委员会文档至 Obsidian（`sync-all` 已内置此步骤）

**目录删除检查清单**：附体任务涉及删除目录时，主 agent 在 Task 描述中必须：
1. 逐项列出每个待删目录，说明其性质（生产依赖/开发产物/一次性实验）
2. 对每个目录运行 `grep -r "目录名" scripts/` 确认无脚本引用
3. 对生产依赖目录（如 `logs/`）只加 `.gitignore`，不删目录本身
4. 在 Task 描述中引用具体脚本文件名和行号作为依赖证据

**幡主审查风险提示规范**：审查结论中的风险提示必须引用具体文件名和行号，禁止使用「确认无引用」「确认无运行中进程」等抽象表述。示例：`scripts/discipline-inspector.py:21 写入 logs/discipline_violations.log`。

## 主 agent 角色定义

主 agent 是**纯协作者（Coordinator）**，不是幡主、不是任何魂。主 agent 的唯一职责：
1. **调度**：匹配魂、spawn 子 agent（含幡主审查 + 必要时第二审查官审查）、分发任务
2. **收集**：接收所有子 agent 输出，不做实质性修改
3. **存档**：更新 registry.yaml、写入 Obsidian vault
4. **所有匹配审查（含单魂）**：必须 spawn 幡主子 agent，不得自行判断

除此以外的一切分析、综合、审查、裁决，均由对应魂的子 agent 完成。

## 正确做法

调用 Skill(soul-banner) → 遵循 SKILL.md 附体流程 → 完成后核对 Task 列表全部为 completed。

附体 5 步 Task 模板（详见 SKILL.md）：匹配魂 → 幡主审查 → 执行 → registry 更新 + Obsidian 存档（后两步并行）。

## 启动流程

每次 `/soul-banner` 被调用（无子命令）或新会话启动时，主 agent 必须按顺序执行：

### 1. 健康检查

```bash
python3 scripts/registry-health-check.py --last-run
```
如果输出 `NEVER_RUN` 或 `STALE:`（超过 24 小时未运行），则执行完整检查：
```bash
python3 scripts/registry-health-check.py
```

### 2. 三方交叉校验

```bash
python3 scripts/cross-validate.py
```
如有错误（exit code != 0），必须执行 `python3 scripts/cross-validate.py --fix` 自动修复，然后重新校验确认 0 错误。

### 3. 状态快照

```bash
python3 scripts/state-summary.py --days 3
```
该脚本聚合 registry.yaml、call-records.yaml、committee/state.json、reviews/、committee/meetings/ 全部数据源，输出统一 Markdown 快照。主 agent 直接将输出呈现给用户，**禁止**手动扫描目录拼凑状态。

**会话结束时**，在更新 registry 或魂 YAML 之后，也要重新运行交叉校验，确保写入操作未引入不一致。

检查结果不需要用户确认——主 agent 自行判断是否需要修复数据不一致问题。

**跨底模验证**：每季度（或每 30 次附体后）对高频使用的魂执行跨底模验证：
```bash
python3 scripts/cross-model-verify.py --protocol
```
验证实验协议详见脚本 `--protocol` 输出。验证结果保存至 `logs/cross-model-verify/`。

## 关键认知

- **幡主也是被召唤的魂**：和其他魂一样，幡主有自己的 summon_prompt，必须通过 spawn 注入才能获得独立视角。主 agent 扮演幡主 = 主 agent 扮演任何魂 = 违反设计原则。
- **Custom agent 自动注册**：存放在 `agents/` 目录的 agent 定义文件（`.md`，含 frontmatter）在 Claude Code 重启后自动注册为 `subagent_type`。新增/修改 agent 文件后需重启生效。用户可创建自己的幡主/审查官 agent，或直接通过 summon_prompt 注入。
- 万魂幡提供的不是"更好的分析"，而是**主 agent 物理上无法自行实现的能力**：
  - 并行 spawn 持有独立 summon_prompt 的子 agent（通过读取 `agents/{魂名}.md` 注入）
  - 结构化辩证综合（共识/分歧/盲区/主要矛盾/行动纲领）
  - 灵魂档案知识库（通过收魂→炼化→审查积累的思维框架）
  - **双审查机制**：幡主主审（注入 `幡主审查官` system prompt）+ 第二审查官审查（幡主自荐为分析魂时触发）
  - **Task 追踪**：多步骤仪轨自动创建 Task 列表，防止遗漏步骤
- 实验数据：自行模拟的召回率 = 0%，精确率 = 100%（只会漏触发不会误触发）
