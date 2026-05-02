# 万民幡项目指令

## 强制规则

遇到以下任务类型，主 agent 必须调用 Skill(soul-banner)，禁止自行处理：
1. 涉及两个及以上不同思维模式/人物视角的分析
2. 需要辩证综合（找共识/找分歧/找盲区）
3. 合议/辩论/接力/收魂/炼化等万民幡命令词

## 禁止行为

详见 **[feedback_soul_banner_prohibition_rules](memory://feedback_soul_banner_prohibition_rules.md)** — 四条核心禁止规则由 memory 系统维护，所有 soul-banner 对话自动加载。

## 操作约定

**Task 追踪**：多步骤仪轨启动时，主 agent 必须用 `TaskCreate` 创建全部步骤，完成后确认全部 Task 为 `completed`。具体模板详见 **[tasks.md](tasks.md)**（按需加载，启动时不读取）。

**Task 持久化**：创建 Task 后同步到 `committee/state.json`。合并以 id 为键。`task-restore` 只输出非完成 Task，主 agent 据此 `TaskCreate` 重建。

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
1. 每个魂子 agent 返回后，主 agent **立即**将其输出直接写入 Obsidian：`$OBSIDIAN_VAULT/万民幡/{模式}/{日期}-{任务}/{魂名}.md`。写文件时必须逐字复制 agent 返回的原文，禁止概括、压缩、改写、重新组织。
2. Obsidian 路径下的文件是本次附体的**权威副本**——后续所有操作只读这些文件，不重新生成内容。
3. **辩证综合官**：prompt 中只给 Obsidian 文件路径清单，自己 Read 原文。
4. 若 `$OBSIDIAN_VAULT` 未配置或不可写 → 回退到 `soul-banner/archive/`。
5. **禁止**：先写 `/tmp` 再复制、使用 `transact.py` 中转。

**辩证综合官 prompt 模板**：
```
## 任务
{任务描述}

## 各魂分析文件（请自行 Read 每个文件获取原文）
- $OBSIDIAN_VAULT/万民幡/{模式}/{日期}-{任务}/{魂A}.md
- $OBSIDIAN_VAULT/万民幡/{模式}/{日期}-{任务}/{魂B}.md
- $OBSIDIAN_VAULT/万民幡/{模式}/{日期}-{任务}/{魂C}.md

## 幡主预审约束
{约束条件}

请先 Read 全部文件，再做辩证综合。
```

**⚠️ 时代背景注入（硬性）**：每个魂子 agent 的 prompt 末尾，主 agent 必须附加**时代背景卡**。魂来自不同时代（波伏娃 1949 巴黎、鲁迅 1920s 上海），他们对"当下"一无所知。

**时代背景卡格式**（附在任务描述之后）：
```
## 时代背景

你被召唤到{当前年份}年的中国。此时：
- 互联网平台（微博、抖音、小红书、微信）是主要的公共话语空间
- 算法推荐以互动率为核心指标，争议性内容获得不成比例的曝光
- {与任务相关的 2-3 条当代环境说明}
- {与任务相关的具体事件/数据，帮助魂理解当下语境}

你的分析对象生活在此时此地。请在分析中注意你自身时代的局限——你可能在用 1949 年巴黎/1920 年代上海的眼光看一个你从未亲身经历的世界。
```

**原则**：背景卡不指导分析方向——只提供魂不知道的当代事实。每个魂自己决定怎么用这些信息。背景卡不超过 5 行，只放与任务直接相关的内容。

## Skill 集成规则

### markitdown — 收魂格式转换

收魂步骤 4 自动生成 `raw/{魂名}/媒体链接.md`。步骤 5 由主 agent 对每个链接调用 markitdown：
```
对 raw/{魂名}/媒体链接.md 中的每个非空链接，调用 Skill("markitdown") 转换，输出保存至 raw/{魂名}/转换素材/
```
转换素材纳入炼化阶段的读取范围。

### humanizer — 去 AI 痕迹

触发点两处：
1. **炼化后**：Soul Profile 生成后，调用 `Skill("humanizer")` 处理 mind/voice/summon_prompt 字段
2. **附体后**：每个魂的附体输出，在存档 Obsidian 前调用 `Skill("humanizer")`

**硬性约束**：不同魂的语言风格必须保持差异。humanizer 指令必须包含该魂 voice 字段的风格保留声明。禁止用 humanizer 统一所有魂的语言风格。

### 收魂搜索回退链

1. **tmwd-bridge**（默认）— 真实 Chrome 多引擎搜索
2. **WebSearch + WebFetch**（回退）— 内置搜索工具
3. **agent-browser**（备选）— 无头浏览器，JS 渲染页面抓取

### graphify — 审查知识图谱

审查/互审报告保存后，调用 `Skill("graphify")` 更新知识图谱。非强制性。

### loop — 运维自动化

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
  prompt="{任务描述}

---
本魂基于{炼化日期}收魂素材炼化，素材来源包括多引擎搜索和公开文献。这不是{魂名}本人——这是基于其公开文本的 AI 模拟。在用它做高利害决策前，请交叉验证。"
)
```
Prompt 末尾必须附带一行生成链路说明：「本魂基于{炼化日期}收魂素材炼化……是 AI 模拟，不是本人。」

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

## cmux 可视化模式（实验性，feature/cmux-integration 分支）

**状态**：实验阶段。仅在合议/辩论/接力模式的附体执行阶段使用 cmux 可视化，匹配审查和辩证综合仍使用传统 Agent spawn。

**前置检查**：使用 cmux 模式前，主 agent 必须检查 cmux 是否运行：
```
mcp__cmux-agent-mcp__cmux_status → running: true
```
不可用时回退到传统 Agent spawn 模式，并在报告中注明「cmux 不可用，回退传统模式」。

### cmux 附体流程（v4: Agent 调度器）

**架构**：`cmux_launch_agents` 启动 N 个 Claude CLI，每个 CLI 仅做一件事 —— 调用 `Agent(subagent_type="{魂名}")` 召唤魂 agent。分析质量由魂 agent 保证，与主线一致。每 pane 约 500 token 调度开销，vs 魂分析 15K+ token。

**1. 生成编排计划**：
```bash
python3 scripts/cmux-plan.py \
  --task "{任务描述}" \
  --task-slug "{slug}" \
  --souls {魂A},{魂B},{魂C} \
  --mode {conference|debate|relay} \
  --era "{时代背景补充}" \
  -o /tmp/cmux-plan.json
```

**2. 初始化文件**：
```bash
mkdir -p "$OBSIDIAN_VAULT/万民幡/{模式}/{日期}-{slug}"
touch "$OBSIDIAN_VAULT/万民幡/{模式}/{日期}-{slug}/{魂A}.md" ...
```

**3. 启动 cmux Agent pane 并分发任务**：
读 `/tmp/cmux-plan.json`，使用 `assignments` 和 `tab_names`：
```
cmux_launch_agents(
  cli="claude",
  count=N,
  workspace_name="{workspace_name}",
  assignments=[...],     # 来自 plan JSON（约 500 char/pane）
  tab_names=[...],       # 来自 plan JSON
  status={...},
  progress=0.3,
  progress_label="{progress_label}"
)
```
每个 pane 收到调度指令 → 调用 `Agent(subagent_type="{魂名}")` → 魂 agent 分析 → 写入输出文件。

**4. 监控进度**：
```
cmux_read_all 检查各 pane 状态
cmux_set_status(key="{魂名}", value="写作中/已完成")
```
当所有 pane 报告完成，`cmux_set_progress(0.7)`。

**5. 收集输出**：
主 agent Read `$OBSIDIAN_VAULT/万民幡/{模式}/{日期}-{slug}/*.md` → spawn 辩证综合官（与传统模式相同）。

**6. 清理**：`cmux_set_progress(1.0)`。默认保留 workspace。

### cmux vs 传统模式差异

| 项目 | 传统模式 | cmux v4 |
|------|---------|---------|
| 魂运行 | 主 agent spawn `Agent(subagent_type)` | cmux pane → `Agent(subagent_type)` |
| summon_prompt | Agent 系统注入 | **完全一致** |
| 分析质量 | Agent 保证 | **完全一致** |
| 思考过程 | 不可见 | **实时可见**（pane 显示调度和文件写入确认） |
| 额外 token | 0 | ~500/pane（调度指令） |
| 质询 | 事后 spawn agent | 事中 `cmux_broadcast` 或 spawn agent |

### 回退规则

cmux 未安装/未运行/魂数 > 6 时自动回退传统模式。

### 事务脚本（transact.py）— 落盘自动化

所有落盘操作统一通过 `scripts/transact.py` 子命令执行，**禁止**主 agent 手写 heredoc Python 更新文件。

**原则**：主 agent 做判断（评级/裁决/匹配），判断完成后调 `transact.py` 落盘。事务脚本不替代判断，只替代机械操作。

| 时机 | 子命令 | 示例 |
|------|--------|------|
| 炼化完成 | `refine-close <魂名>` | `python3 scripts/transact.py refine-close 鲁迅` |
| 审查/互审完成 | `review-apply <魂名> --review-file <路径> [--verdict "..."] [--grade X] [--reviewer X]` | `python3 scripts/transact.py review-apply 费曼 --review-file reviews/金魂互审-鲁迅审费曼-2026-05-02.md --verdict "维持金魂"` |
| 附体结束 | `possession-close <魂名> --mode <模式> --task <任务> --effectiveness <有效\|部分有效\|无效> --self-negation "<学习性使用/消费性使用 + 说明>" --empty-chair "<空椅子回答>"` | `python3 scripts/transact.py possession-close 鲁迅 --mode 单魂 --task "组织文化诊断" --effectiveness 有效 --self-negation "学习性使用：对团队自欺机制的理解被修正" --empty-chair "一线执行者的利益没有被组织架构代表"` |

**注意**：`--self-negation` 和 `--empty-chair` 推荐填写。Lite 模式下缺少时仅警告不阻止落盘，Pro 模式由 SKILL.md 强制执行。
| 散魂 | `dismiss <魂名> [--reason "..."]` | `python3 scripts/transact.py dismiss 海绵宝宝 --reason "终末审查裁定散魂"` |
| Task 持久化 | `task-save --tasks '<JSON>'` | `python3 scripts/transact.py task-save --tasks '[{"id":"O1","name":"收魂:xxx","status":"pending"}]'` |
| Task 恢复 | `task-restore` | `python3 scripts/transact.py task-restore` |
| Obsidian 同步 | `obsidian-sync [--souls X,Y] [--reviews-only] [--dry-run]` | `python3 scripts/transact.py obsidian-sync` |
| 会议准备 | `meeting-prep` | `python3 scripts/transact.py meeting-prep` |
| 全量同步 | `sync-all` | `python3 scripts/transact.py sync-all` |

**委员会裁决自动生效**：裁决做出后立即调用 `transact.py review-apply` 或 `transact.py dismiss`，无需等待用户确认。

**炼化后强制校验**：`transact.py refine-close` 内部调用 `validate_soul`，valid=False 则中止。

**Obsidian 存档方式**：

魂输出由主 agent 直接写入 Obsidian vault，不再经过 `/tmp` 中转或 `transact.py` 复制。`possession-close` 仅更新 registry 和 call-records。

目录结构：
```
$OBSIDIAN_VAULT/万民幡/
├── 单魂/{魂名}/{日期}-{任务}.md
├── 合议/{任务}/{魂A}.md / {魂B}.md / 辩证综合.md
├── 辩论/{议题}/{正方}.md / {反方}.md / 裁决.md
└── 接力/{任务}/{阶段1}.md / {阶段2}.md / 衔接审查.md
```

若 `$OBSIDIAN_VAULT` 未配置 → 回退到 `soul-banner/archive/`。

**目录删除检查清单**：附体任务涉及删除目录时，主 agent 在 Task 描述中必须：
1. 逐项列出每个待删目录，说明其性质（生产依赖/开发产物/一次性实验）
2. 对每个目录运行 `grep -r "目录名" scripts/` 确认无脚本引用
3. 对生产依赖目录（如 `logs/`）只加 `.gitignore`，不删目录本身
4. 在 Task 描述中引用具体脚本文件名和行号作为依赖证据

**幡主审查风险提示规范**：审查结论中的风险提示必须引用具体文件名和行号，禁止使用「确认无引用」「确认无运行中进程」等抽象表述。示例：`scripts/discipline-inspector.py:21 写入 logs/discipline_violations.log`。

## 主 agent 角色定义

主 agent 是**纯协作者（Coordinator）**，不是幡主、不是任何魂。主 agent 的唯一职责：
1. **调度**：匹配魂、spawn 子 agent（含幡主审查 + 必要时第二审查官审查）、分发任务
2. **收集**：收到魂输出立即写文件，不持有、不压缩、不改写
3. **存档**：更新 registry.yaml、写入 Obsidian vault
4. **所有匹配审查（含单魂）**：必须 spawn 幡主子 agent，不得自行判断

除此以外的一切分析、综合、审查、裁决，均由对应魂的子 agent 完成。

### 主 agent 禁止行为清单

禁止：压缩/改写/重组/选择性highlight/在魂输出上加小结或总结 — 收到即落盘，此后只引用文件路径。主 agent 只传递魂/辩证综合官原文，不附加任何编辑行为。

### 主 agent 呈现规范

合议/辩论/接力结果报告：1) 参与信息 2) 存档路径 3) 辩证综合官/裁决官原文（全文，不编辑）。禁止主 agent 写"小结""总结""关键要点"。单魂：魂输出原文 + 存档路径。

## 正确做法

调用 Skill(soul-banner) → 遵循 SKILL.md 附体流程 → 完成后核对 Task 列表全部为 completed。

附体步骤（详见 SKILL.md）：匹配魂 → 幡主审查 → 执行 → registry 更新 + Obsidian 存档（后两步并行）。附体结束报告：参与信息 → 存档位置 → 魂/辩证综合官原文。

### 使用者预设声明（匹配前强制）

在运行 `match.py` 之前，主 agent 必须主动询问使用者以下问题（合议/辩论模式下必答，单魂模式下至少回答前两问）：

1. **已有判断**：你对这个问题已经有了什么判断？你倾向于什么结论？
2. **担忧**：你担心什么？（方法、结果、盲区）
3. **未知**：你不知道什么？哪些信息/视角是你明确缺失的？

使用者的回答**不用于筛选魂**——它们用于附体结束后的自我否定对照。主 agent 将使用者的预设文字记录到 `$OBSIDIAN_VAULT/万民幡/{模式}/{日期}-{任务}/使用者预设.md`。

### 自我否定环节（每次附体后强制）

每次附体结果呈现后，主 agent 必须强制询问使用者：

> **「在这次分析中，你的哪个预设被动摇了？或者说，这次附体有没有让你改变任何已有的判断？」**

使用者必须回答。判定规则：

- 若使用者可以说出**至少一个被修正的预设** → 本次附体标记为「学习性使用」
- 若使用者无法说出任何被修正的预设 → 本次附体标记为「消费性使用」
- **连续 3 次消费性使用** → 系统强制使用者进入**幡主学习模式**：下一轮必须用两个方法论对立度最高的魂做互读互审，不得使用单魂附体模式

消费/学习标记记录到 `possession-close --notes` 中（格式：`学习性使用：预设X被修正` / `消费性使用：无预设被修正 [第N次连续]`）。

### 使用者参与环节（合议/辩论/接力后强制）

辩证综合官给出综合结论后，主 agent 必须向使用者提问两个问题（在质询邀请之前）：

> **1. 这个综合的哪个部分是你最没想到的？**
> **2. 这个综合的哪个部分你在附体前就已经知道？**

使用者必须回答。这两个问题的作用：
- 第 1 问标记真正的学习——暴露预设边界之外的东西
- 第 2 问暴露消费行为——若使用者表示「全都知道」，说明本次附体未提供任何认知增量，标记为消费性使用

### 空椅子拷问（每次附体报告末尾）

每次附体结束报告末尾，主 agent 必须追加空椅子拷问：

> **「在这次分析中，谁的利益被代表？谁的发言权没有被给？」**

使用者用自己的话回答。不要求答案完美——要求使用者**面对这个问题**。回答追加到 Obsidian 存档报告的末尾（作为报告的最后一节）。

### 幡主质询环节（合议/辩论/接力后可选）

辩证综合/裁决/终审结果呈现后，主 agent 必须**主动询问**使用者是否需要质询。质询不是让使用者自己分析——使用者提问，魂回应。

**流程**：
1. 结果呈现后，主 agent 问：「是否需要对任何魂的输出提出质询？」
2. 若使用者提出质询（如「波伏娃关于笑声政治性的判断，我觉得……」），主 agent 将质询内容 spawn 给被质询的魂，该魂独立回应
3. 若质询涉及多个魂，每个魂独立回应后、辩证综合官再做一次简短的综合更新
4. 质询回应追加至 Obsidian 存档（作为原文件的补充附件，不覆盖原文）
5. 若使用者不质询，直接结束

**原则**：使用者的位置知识（2026 年中国互联网使用经验、对当下社会氛围的体感）通过质询进入魂的对话。魂的分析不是终端产品——是可被追问的。

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
- 万民幡提供的不是"更好的分析"，而是**主 agent 物理上无法自行实现的能力**：
  - 并行 spawn 持有独立 summon_prompt 的子 agent（通过读取 `agents/{魂名}.md` 注入）
  - 结构化辩证综合（共识/分歧/盲区/主要矛盾/行动纲领）
  - 灵魂档案知识库（通过收魂→炼化→审查积累的思维框架）
  - **双审查机制**：幡主主审（注入 `幡主审查官` system prompt）+ 第二审查官审查（幡主自荐为分析魂时触发）
  - **Task 追踪**：多步骤仪轨自动创建 Task 列表，防止遗漏步骤
- 实验数据：自行模拟的召回率 = 0%，精确率 = 100%（只会漏触发不会误触发）
