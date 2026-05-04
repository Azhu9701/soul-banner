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

**审查 spawn**：日常匹配审查 spawn `subagent_type="未明子"`（幡主，主义主义四维坐标+拉康-马克思互读）。金魂互审和终末审查按轮值表 spawn 对应审查官（毛泽东/邓小平/列宁），第二审查官复核（列宁，老幡主，保留复审位）。详见 `soul-profile-format.md`「审查轮值制」。

**附体匹配**（v3.3 — 两种模式。默认广播自选）：

### 模式 A：广播自选（默认，v3.3 互见模式）

匹配是魂之间的对话，不是外部引擎的计算。两轮广播：

**第一轮：互见自选**
1. **广播格式化**：`python3 scripts/broadcast.py "任务描述"` — 含 20 魂 self_declare + 场域内互见交叉表 + 跨场域互补参考
2. **互见修正**：主 agent 做 [Y/N] + 主力/补位 判断时，检查自选 Y 的魂之间盲区是否互相覆盖。有缺口→从 Maybe/N 中补
3. **初步合议组**：主力1-2 + 补位1-2 ≤ 4魂

**第二轮：互见挑战**
4. **轻量广播**：将初步合议组名单 + self_declare 发送给全部 20 魂的轻量 spawn（每魂 ~500 字 prompt）：
   - ① 合议组是否有遗漏？② 是否有盲区需要补充？③ 无异议直接回"无异议"
   - 并行 spawn，30秒超时→视为无异议
5. **收集异议**：非"无异议"的回答 → 如有魂提出新候选 → 追加进入幡主审查
6. **幡主审查**：spawn 未明子审查合议组+异议 → 按 v3.2 补人规则。如互见轮增加噪音（异议>5/单魂>200字）→ 幡主可指令回退
7. **正式 spawn**：合议组 → 完整 summon_prompt → 辩证综合

**self_declare 演化**（每次附体后）：
```bash
# 魂提出修改 → pending 状态，不立即替换正式版本
python3 scripts/evolve_declare.py propose <魂名> --task "任务简述" --text "新声明" --reason "为什么改"

# 检查待审修改
python3 scripts/evolve_declare.py review <魂名>

# 积累 3 次待审 → 幡主审查后批准
python3 scripts/evolve_declare.py accept <魂名> --version N
```

### 模式 B：match.py 算法匹配（回退）

当用户显式要求算法匹配、或需要精确的定量对比（如对照实验）时使用：

1. **预筛选**：`python3 scripts/match.py "任务描述" --no-review`
2. **幡主审查**：spawn 未明子审查算法推荐（8 问清单 v3.1）
3. **正式 spawn**：审查通过 → 合议/单魂

**手册更新**：每次附体落盘后运行 `python3 scripts/generate-handbook.py -o committee/handbook.md --compact`

`registry-lite.yaml` 由 `scripts/generate-registry-lite.py` 自动生成。

**辩证综合 spawn**：合议模式阶段二，spawn `subagent_type="辩证综合官"`。该 agent 定义了五步综合法（共识/分歧/盲区/主要矛盾/行动纲领）。

**⚠️ 魂输出原文保全规则（硬性，合议/辩论/接力通用）**：

**原则**：主 agent **禁止**用自己的话改写魂输出——无论是传给下游 agent 还是存档 Obsidian。魂输出必须是原文。

**流程**：
1. 每个魂子 agent 返回后，主 agent **立即**将其输出直接写入 Obsidian vault：`$OBSIDIAN_VAULT/万民幡/{模式}/{任务简述}/{魂名}.md`。写文件时必须逐字复制 agent 返回的原文，禁止概括、压缩、改写、重新组织。若 `$OBSIDIAN_VAULT` 未配置，回退到 `/tmp/sb-{任务}/`。
2. 辩证综合官 prompt 中给出 Obsidian 路径清单（或回退 /tmp 路径），辩证综合官自己 Read 原文。
3. 辩证综合完成后，辩证综合结果同样直接写入 Obsidian 同一目录。
4. **落盘**：调用 `transact.py possession-close`，此时文件已在 Obsidian 中，transact.py 只更新 registry + call-records + 交叉校验 + 匹配手册，不再复制文件：
   ```bash
   python3 scripts/transact.py possession-close {魂名} \
     --mode {模式} --task "{任务简述}" \
     --obsidian-batch $OBSIDIAN_VAULT/万民幡/{模式}/{任务简述}/manifest.json
   ```
5. 使用者阅读 Obsidian 后，主 agent 依次执行使用者参与环节 → 自我否定 → 空椅子拷问。
6. **补充落盘**：将使用者回答直接追加至 Obsidian 对应文件末尾，更新 registry + call-records（含 effectiveness/self-negation/empty-chair）。

**辩证综合官 prompt 模板**：
```
## 任务
{任务描述}

## 各魂分析文件（请自行 Read 每个文件获取原文）
- $OBSIDIAN_VAULT/万民幡/{模式}/{任务简述}/{魂A}.md
- $OBSIDIAN_VAULT/万民幡/{模式}/{任务简述}/{魂B}.md
- $OBSIDIAN_VAULT/万民幡/{模式}/{任务简述}/{魂C}.md

## 幡主预审约束
{约束条件}

请先 Read 全部文件，再做辩证综合。按五步法输出后，追加**实践开口检测**（v3.5）：诊断本次分析的盲区是否可在现有 24 魂内解决，若不可——生成一个实践议题，包含需要去现实世界确认的具体问题。
```

若 `$OBSIDIAN_VAULT` 未配置，路径改为 `/tmp/sb-{任务}/`。

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

**⚠️ 共享事实简报（硬性，合议/辩论/接力模式强制）**：多魂并行时，每个魂独立介绍背景会重复铺陈。主 agent 必须在 spawn 魂之前创建一份**共享事实简报**，写入 Obsidian 任务目录（或回退 `/tmp/sb-{任务}/`），附在每个魂的 prompt 中。魂直接引用简报，**禁止**在分析中重复铺陈背景。

**共享事实简报格式**（不超过 6 行，只列魂需要知道但无法自行获取的事实）：
```
## 共享事实简报

以下事实已确认，请直接在分析中使用，无需重复介绍：
- {事件}: {关键人物/时间/地点/性质}
- {数据}: {与任务相关的统计或调查结果}
- {语境}: {当代特有的概念或背景}
```

**原则**：简报是事实，不是分析方向。魂 prompt 中同时附上简报和时代背景卡。简报消除重复铺陈，背景卡提醒时代局限。两者不互相替代。

### markitdown — 收魂格式转换

收魂步骤 4 自动生成 `raw/{魂名}/媒体链接.md`。步骤 5 由主 agent 对每个链接调用 markitdown：
```
对 raw/{魂名}/媒体链接.md 中的每个非空链接，调用 Skill("markitdown") 转换，输出保存至 raw/{魂名}/转换素材/
```
转换素材纳入炼化阶段的读取范围。

### 收魂搜索回退链

1. **tmwd-bridge**（默认）— 真实 Chrome 多引擎搜索
2. **WebSearch + WebFetch**（回退）— 内置搜索工具
3. **agent-browser**（备选）— 无头浏览器，JS 渲染页面抓取

**v3.1 搜索维度**（两套并行）：

人物基础 6 维：生平时代 / 核心思想 / 主要著作 / 方法论特征 / 对后世影响 / 争议批判

主义主义定位 4 维（服务于炼化阶段目录匹配）：
- **场域位置**：该人物在什么背景下思考和行动？他的思想发生在什么样的存在论框架中？
- **本体论预设**：他认为什么最真实？物质/精神/生命/符号？这个预设是显式的还是隐式的？
- **认识论路径**：他凭什么说知道了？经验观察/理性推导/直觉体认/辩证否定？
- **目的论方向**：他的思想要把人带去哪？保守/改良/解放/消解？

收魂完成后，增加**目录预查**：在未明子原版 256 目录中初步定位——该人物或近似位置是否已存在？最近的条目是什么？

### loop — 运维自动化

**边界**：只自动化运维检查，不自动化判断行为。禁止用 loop 自动执行审查/互审/标签调整。

设置维护循环：
```
/loop 1h python3 ~/.claude/skills/soul-banner/scripts/registry-health-check.py
/loop 6h python3 ~/.claude/skills/soul-banner/scripts/cross-validate.py
/loop 24h python3 ~/.claude/skills/soul-banner/scripts/transact.py sync-all
/loop 168h python3 ~/.claude/skills/soul-banner/scripts/state-summary.py --json > /tmp/soul-banner-weekly.json
```
审查委员会轮值调度不使用 loop——轮值由幡主在每次附体时手动判断。

**Spawn 魂的标准模板**（合议/辩论/接力模式）：
```
Agent(
  subagent_type="{魂名}",
  description="{任务简述} — {魂名}视角",
  prompt="## 任务
{任务描述}

## 共享事实简报（已确认，直接使用，无需重复介绍）
Read $OBSIDIAN_VAULT/万民幡/{模式}/{任务简述}/事实简报.md

## 时代背景
{时代背景卡}

## 约束条件
{幡主审查给定的约束}

---
本魂基于{炼化日期}收魂素材炼化，素材来源包括多引擎搜索和公开文献。这不是{魂名}本人——这是基于其公开文本的 AI 模拟。在用它做高利害决策前，请交叉验证。"
)
```
单魂模式下共享事实简报和时代背景卡合并到 prompt 中，不单独写文件。

若 `$OBSIDIAN_VAULT` 未配置，路径改为 `/tmp/sb-{任务}/`。

**Spawn 幡主审查专用模板**（v3.1，含主义主义目录匹配审查。必须严格遵循）：

```
Agent(
  subagent_type="未明子",
  description="幡主匹配审查",
  prompt="## 匹配预筛选结果（match.py v3.0 双层输出）

{match.py --no-review 的完整输出}

以上输出包含：
- 算法提取的任务场域 — 用于 compat/incompat 检查
- 表层分 + 结构分 + 融合分
- ismism 目录编码 + 目录条目 + 匹配质量（精确/近似/复合/反讽/目录外）
- 结构提示（场域不兼容/冗余协同/盲区互补/内容锚定）

---
禁止读取任何文件。仅基于以上预筛选结果和已知的魂领域知识做判断。

## 审查清单（逐条回答，每条一句话）

### 领域与排除
1. **领域匹配**: 首选魂的领域是否实质性覆盖此任务？算法判断对吗？[Y/N + 简述]
2. **排除风险**: 有无排斥条件实质性触发？算法漏了或误判了吗？[Y/N + 哪个]

### 结构审查（基于主义主义目录 compat，非坐标算术）
3. **场域审查**: 算法的场域判断对吗？有没有场域不兼容被误标？有没有该上但被排除的魂（如内容锚定检测漏了）？
4. **目录匹配审查**: 首选魂的 ismism 目录匹配是否合理？匹配质量标注对吗？
5. **冗余/盲区审查**: 算法的冗余标注和盲区互补标注对吗？
6. **合议审查**: 需要合议吗？算法推荐的人选是否合适？

### 裁决
7. **边界风险**: 适用边界外溢风险？[无/低/中/高 + 简述]
8. **裁决**: [通过 / 条件通过(加约束) / 换X / 需合议 / 需第二审查官]
   - 如加约束：具体是什么约束？
   - 如换魂：换谁？为什么？
   - 如合议：推荐哪几个魂？"
)
```

审查 prompt 中必须包含「**禁止读取任何文件**」。
预筛选结果使用 `--no-review` 精简版。
审查清单 v3.1 — 从坐标算术审查改为目录匹配审查。移除「认识审查」（不再独立追踪本体/认识/目的），新增「目录匹配审查」。

**审查补人规则**（v3.2 新增——来自全链路测试反馈）：
当首选魂的 `match_quality` 为「近似」或「目录外」，且任务涉及该魂 compat 盲区（如批判型魂被要求处理建构型任务），幡主审查必须执行：
> 「当框架短板恰好是任务必需能力时，不在条件中模糊化——直接在合议中补人。」
即在合议建议中显式指定承担该能力的魂，而非仅加「需补充过渡策略」之类的模糊约束。

## cmux 可视化模式（实验性）

**状态**：实验阶段，不合并主干。触发词加「可视化」启用（合议可视化/辩论可视化/接力可视化）。

**架构**：`cmux_launch_agents` → N 个 Claude CLI pane → 每个 pane 调用 `Agent(subagent_type="{魂名}")` → 魂分析 → 写 `/tmp/sb-{slug}/{魂名}.md`。分析质量与传统模式完全一致（同一套 summon_prompt），区别仅在于思考过程实时可见。

**前置检查**：`mcp__cmux-agent-mcp__cmux_status → running: true`，不可用时自动回退传统模式。魂数 > 6 时也回退。

**流程**：`cmux-plan.py` 生成编排计划 → `cmux_launch_agents` 启动 pane → `cmux_read_all` 监控 → 主 agent Read 输出 → spawn 辩证综合官（同传统模式）。完整文档见 **[references/cmux-integration.md](references/cmux-integration.md)**。

### 事务脚本（transact.py）— 落盘自动化

所有落盘操作统一通过 `scripts/transact.py` 子命令执行，**禁止**主 agent 手写 heredoc Python 更新文件。

**原则**：主 agent 做判断（评级/裁决/匹配），判断完成后调 `transact.py` 落盘。事务脚本不替代判断，只替代机械操作。

| 时机 | 子命令 | 示例 |
|------|--------|------|
| 炼化完成 | `refine-close <魂名>` | `python3 scripts/transact.py refine-close 鲁迅` |
| 审查/互审完成 | `review-apply <魂名> --review-file <路径> [--verdict "..."] [--reviewer X]` | `python3 scripts/transact.py review-apply 费曼 --review-file reviews/金魂互审-鲁迅审费曼-2026-05-02.md --verdict "裁定维持"` |
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

魂输出和辩证综合**直接写入** Obsidian vault（`$OBSIDIAN_VAULT/万民幡/{模式}/{任务简述}/`），不再经过 `/tmp` 中转。`transact.py possession-close` 只更新 registry + call-records + 交叉校验 + 匹配手册，不再复制文件。

manifest.json 中的 file 路径指向 Obsidian（或回退 /tmp）：
```json
{"mode": "合议", "task": "任务简述", "date": "2026-05-02", "files": [
  {"soul": "魂A", "role": "角色", "file": "$OBSIDIAN_VAULT/万民幡/合议/任务简述/魂A.md"},
  {"soul": "辩证综合官", "role": "辩证综合", "file": "$OBSIDIAN_VAULT/万民幡/合议/任务简述/辩证综合.md"}
]}
```

`transact.py` 自动：检测文件已在 Obsidian → 跳过复制 → 更新 registry → 记录 call-records。若 `$OBSIDIAN_VAULT` 未配置 → 回退 `/tmp/sb-{任务}/`，仅更新 registry。

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

附体步骤（详见 SKILL.md）：匹配魂 → 幡主审查 → 执行 → 导出 Obsidian → 使用者参与/自我否定/空椅子 → 补充落盘。附体结束报告：先导出 Obsidian 让使用者阅读，再提问。魂/辩证综合官原文在 Obsidian 中完整呈现。

### 使用者预设声明（匹配前强制）

在运行 `match.py` 之前，主 agent 必须主动询问使用者以下问题（合议/辩论模式下必答，单魂模式下至少回答前两问）：

1. **已有判断**：你对这个问题已经有了什么判断？你倾向于什么结论？
2. **担忧**：你担心什么？（方法、结果、盲区）
3. **未知**：你不知道什么？哪些信息/视角是你明确缺失的？

使用者的回答**不用于筛选魂**——它们用于附体结束后的自我否定对照。主 agent 将使用者的预设文字记录到 `/tmp/sb-{任务}/使用者预设.md`。（`transact.py` 落盘时随其他文件一起同步至 Obsidian。）

### 自我否定环节（每次附体后强制）

每次附体结果呈现后，主 agent 必须强制询问使用者：

> **「在这次分析中，你的哪个预设被动摇了？或者说，这次附体有没有让你改变任何已有的判断？」**

使用者必须回答。判定规则：

- 若使用者可以说出**至少一个被修正的预设** → 本次附体标记为「学习性使用」
- 若使用者无法说出任何被修正的预设 → 本次附体标记为「消费性使用」
- **连续 3 次消费性使用** → 系统强制使用者进入**幡主学习模式**：下一轮必须用两个方法论对立度最高的魂做互读互审，不得使用单魂附体模式

消费/学习标记记录到 `possession-close --notes` 中（格式：`学习性使用：预设X被修正` / `消费性使用：无预设被修正 [第N次连续]`）。

### 使用者参与环节（合议/辩论/接力后强制）

辩证综合官给出综合结论后，主 agent **先导出 Obsidian**，让使用者在 Obsidian 中阅读完整魂输出和辩证综合。之后再提问两个问题（在质询邀请之前）：

> **1. 这个综合的哪个部分是你最没想到的？**
> **2. 这个综合的哪个部分你在附体前就已经知道？**

使用者必须回答。这两个问题的作用：
- 第 1 问标记真正的学习——暴露预设边界之外的东西
- 第 2 问暴露消费行为——若使用者表示「全都知道」，说明本次附体未提供任何认知增量，标记为消费性使用

### 空椅子拷问（每次附体报告末尾）

每次附体结束报告末尾，主 agent 必须追加空椅子拷问：

> **「在这次分析中，谁的利益被代表？谁的发言权没有被给？」**

使用者用自己的话回答。不要求答案完美——要求使用者**面对这个问题**。回答追加到 Obsidian 存档报告的末尾（作为报告的最后一节）。

### 实践开口检测（每次附体后强制 — v3.5）

辩证综合完成后（或单魂输出后），主 agent 必须执行实践开口检测。这是将万民幡从「过去知识的交通系统」转向「实践-理论的反馈循环」的关键机制。

**执行方式**（合议模式）：辩证综合官 prompt 末尾追加实践开口检测指令；**单魂模式**：幡主审查时一并执行。

**输出三问**：

1. **盲区判定**：本次分析是否存在现有 24 魂的方法论无法覆盖的盲区？[是/否]
2. **分类**：若存在——这些盲区是"可收魂填充的经典位"还是"必须从实践中获取的新经验"？
3. **若是实践盲区**：生成一个实践议题，包含：
   - 需要去现实世界观察/确认/碰触的具体问题
   - 为什么 AI 搜不到、魂推不出
   - 方向提示（不替代实践者判断）

**落地规则**：实践议题随辩证综合结果一同写入 Obsidian 存档（作为报告的独立一节：「实践议题」）。使用者带着议题去实践，回来后新发现更新相关魂的 profile（开放实践审查）或触发新魂炼化。

**关键原则**：系统不试图用现有魂填实践盲区。实践开口不是漏洞——是系统设计的意图。

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

每次 `/soul-banner` 被调用（无子命令）或新会话启动时，主 agent 执行一条命令：

```bash
python3 scripts/state-summary.py --days 3 --compact
```

该脚本自动完成：实时余额查询、registry-lite 陈旧检测与重新生成、handbook 陈旧检测与重新生成、交叉校验（含自动修复）、agent 一致性检测、多数据源聚合快照输出。主 agent 直接将快照呈现给用户，**禁止**手动扫描目录拼凑状态。

**会话结束时**，在更新 registry 或魂 YAML 之后，运行 `python3 scripts/cross-validate.py` 确保写入操作未引入不一致。

**跨底模验证**：每季度（或每 30 次附体后）对高频使用的魂执行：
```bash
python3 scripts/cross-model-verify.py --protocol
```

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
