---
name: soul-banner
description: 万魂幡：多人物视角并行分析与辩证综合系统。当用户要求以特定人物视角分析问题（"从XX视角""用XX思维""如果你是XX"）、发起多人物合议或辩论、跨领域战略/哲学/未来探索时，必须调用本skill——主agent无法自行并行spawn持有独立思维框架的子agent。命令词：收魂 炼化 合议 辩论 接力 审查 散魂 幡中有什么魂 幡中战绩。禁止主agent自行模拟多视角或扮演角色辩论。不触发：人物事实查询（"XX说过什么"）、编程debug、文档排版、常规写作。
---

# 万魂幡

> *「幡动魂自至。以幡择魂，以魂择事，事至则魂附，事毕则魂归。幡主持幡，魂不越界。」*

## 概述

万魂幡是**以马克思主义-列宁主义为审查框架的多元思维调度系统**。核心工作流：

- **收魂** → **炼化** → **审查** → 入幡
- 任务来临时 **附体**（单魂/合议/辩论/接力/学习）→ **幡主审查匹配** → 子 agent 并行 → **幡主辩证综合** → 反馈闭环 → Obsidian 存档
- **主 agent 是纯协作者**：只调度、收集、存档。所有思考（包括幡主）均通过 spawn 子 agent 完成

触发方式：灵识层 Hook 自动扫描用户输入（命令词/魂名/场景模式），也可手动 `/soul-banner` 调用。三层触发机制（灵识层/器灵层/法旨层）详见 `CLAUDE.md`。

---

## Task 追踪系统

所有多步骤仪轨（收魂→炼化→审查、附体四模式）使用内置 Task 系统追踪。**原则**：启动时创建全部步骤 → 执行中更新状态 → 完成后确认全部 completed。并行步骤用 `addBlockedBy` 声明依赖。异常时不删 task，保持 `in_progress` 并说明阻塞原因。

各仪轨 Task 拆分模板和 TaskCreate 命令详见 `CLAUDE.md`。

---

## 触发词

| 触发词 | 功能 |
|--------|------|
| `收魂 {人物名}` | 联网搜索 8 维度 + 可选用户供奉 |
| `炼化 {人物名}` | raw 素材炼化为 Soul Profile，判定品级 |
| `幡中有什么魂` | 查看魂魄列表及品级分布 |
| `散魂 {人物名}` | 删除魂魄档案（保留 raw 素材） |
| `升级魂魄 {人物名}` | 重新收魂 → 炼化 → 审查 → 覆盖原档案 |
| `审查 {人物名}` | 幡主子 agent 独立审查指定魂魄 |
| `用{人物名}来{任务}` | 手动指定魂魄执行任务 |
| `合议 {任务}` | 多魂并行分析，幡主辩证综合 |
| `辩论 {议题} {魂A} vs {魂B}` | 两魂对立辩论，幡主裁决 |
| `接力 {任务} {魂A}→{魂B}→...` | 串联：前魂输出为后魂输入 |
| `学习 {魂A} vs {魂B}` | 幡主学习模式：两对立魂互读互审，训练辩证素养 |
| `幡中战绩` | 查看附体效果反馈记录 |
| `合议可视化 {任务}` | 合议 + cmux 实时可视化（实验性） |
| `辩论可视化 {议题} {A} vs {B}` | 辩论 + cmux 分屏可视化（实验性） |
| `接力可视化 {任务} {A}→{B}→...` | 接力 + cmux 串联可视化（实验性） |

---

## 文件结构

```
soul-banner/
├── SKILL.md                        # 技能文档（系统加载）
├── CLAUDE.md                        # 法旨层常驻指令
├── auto-possess.md                  # 附体机制详解
├── soul-profile-format.md           # 品级标准 + 金魂定义
├── registry.yaml                    # 魂魄总册（运行时数据）
├── refine.py                        # 炼化辅助脚本（含 validate_soul / sync_soul_to_obsidian）
├── scripts/
│   ├── soul-banner-hook.py          # 灵识层 Hook
│   ├── soul-search.py               # tmwd-bridge 收魂搜索（8维度多引擎 + 媒体链接检测）
│   ├── cross-validate.py              # 三方交叉校验（registry↔魂YAML↔审查报告）
│   ├── registry-health-check.py     # registry 健康检查
│   ├── cross_model_review.py        # 跨模型审查对比
│   ├── cross-model-verify.py        # 跨底模验证（真多视角 vs 同模型换帽子）
│   ├── possession-context.py        # 附体上下文注入（系统帮魂记住）
│   ├── discipline-inspector.py      # 纪律检查器
│   ├── prompt-audit.py              # Prompt 审计日志
│   ├── maintenance-loop.sh          # 运维自动化脚本（health/validate/audit/zero）
│   ├── sync-memory.py               # Memory 缓存同步
│   └── test_hook.py                 # Hook 单元测试
├── souls/{魂名}.yaml                 # 已炼化魂魄档案
├── reviews/                          # 审查报告
├── raw/{魂名}/                        # 收魂原始素材（不入仓库）
├── agents/                           # Custom agent 定义（可选）
└── agents/审查官.md / 辩证综合官.md    # 自定义审查/综合 agent
```

---

## 收魂

收魂是 6 步仪轨。Task 模板和命令详见 `CLAUDE.md`。简要流程：

1. 创建 `raw/{魂名}/` 目录
2. 通过 tmwd-bridge（默认）或 agent-browser 多引擎搜索 8 个维度（百度/Bing/Google）
3. 保存为 `raw/{魂名}/搜索素材.md`
4. **媒体链接检测**：自动扫描搜索结果中的 PDF/音视频/PPT 链接，输出至 `raw/{魂名}/媒体链接.md`
5. **markitdown 格式转换**：对 `媒体链接.md` 中的资源调用 markitdown skill 转换为 Markdown，保存至 `raw/{魂名}/转换素材/`
6. 评估素材充足度（字数、维度覆盖），不足则补充搜索

用户可额外提供素材 → `raw/{魂名}/用户供奉.md`。

**搜索方法**：通过 tmwd-bridge 控制真实 Chrome 浏览器。使用方式：
```bash
python3 scripts/soul-search.py "{人物名}" -o raw/{人物名}/
```
反检测：每次搜索间隔 2-4s 随机延迟，引擎间 5s+，模拟滚动。若 tmwd-bridge 不可用，回退到内置 **WebSearch + WebFetch**（免费，零配置），或可选 `byted-web-search`（需火山引擎账号，个人每月 500 次免费额度）。

**收魂双轨**：tmwd-bridge（交互式真实浏览器，处理搜索交互）与 agent-browser（程序化无头浏览器，处理 JS 渲染/登录/翻页的批量抓取）互补。使用 agent-browser 后端：
```bash
python3 scripts/soul-search.py "{人物名}" --engine agent-browser -o raw/{人物名}/
```

**markitdown 格式转换**：收魂搜索结果可能包含 PDF 著作、PPT 演讲、音视频访谈等非文本资源。步骤 4 自动检测媒体链接，步骤 5 由主 agent 调用 markitdown skill 逐条转换：
```
对 raw/{魂名}/媒体链接.md 中的每个链接，调用 Skill("markitdown") 转换为 Markdown，保存至 raw/{魂名}/转换素材/
```

---

## 炼化

炼化是 8 步仪轨。Task 模板详见 `CLAUDE.md`。简要流程：读取 raw 素材（含 markitdown 转换素材）→ 运行 refine.py 辅助 → 结构化提取（身份/思维/决策/表达/技能/案例）→ 生成 Soul Profile → **humanizer 去 AI 痕迹** → 判定品级 → 格式校验（validate_soul）→ 更新 registry → Obsidian 存档。

辅助脚本：
```bash
python3 refine.py --input raw/{魂名}/搜索素材.md
python3 refine.py --input raw/{魂名}/搜索素材.md -o souls/{魂名}.yaml
```

**humanizer 处理**：Soul Profile 生成后，调用 humanizer skill 去除 AI 写作痕迹，保持人格真实性。**硬性约束**：不同魂的语言风格必须保持差异——列宁的尖锐、费曼的通俗、鲁迅的冷峻不能被 humanizer 磨成统一腔调。处理时传入风格保留指令：`保持以下风格特征不变：{该魂的 voice 字段}`。

**炼化后强制校验**：
```bash
python3 -c "
from refine import validate_soul
r = validate_soul('souls/{魂名}.yaml')
print(f'valid={r[\"valid\"]}, errors={len(r[\"errors\"])}, warnings={len(r[\"warnings\"])}')
if r['errors']:
    for e in r['errors']: print('❌', e)
"
```
校验不通过（valid=False）的魂魄不能入幡。

**炼化后同步 agent**：校验通过后，自动生成/更新 Claude Code agent 文件：
```bash
python3 scripts/sync-agent.py souls/{魂名}.yaml
```
agent 文件写入 `~/.claude/agents/{魂名}.md`，重启 Claude Code 后即可通过 `subagent_type="{魂名}"` 直接召唤。**soul YAML 是 agent 的唯一真相源**——禁止手动编辑 agent 文件。

金魂品级自 `soul-profile-format.md` 定义的三条标准判定：可操作方法论 + 独立世界观 + 自我修正机制，三者缺一不可。不同团队可根据自身需求和实践数据调整金魂名单。

---

## 审查

### 新魂入幡审查

每个新炼化的魂必须经幡主**子 agent 独立审查**（8 步仪轨，Task 模板详见 `CLAUDE.md`）。审查 agent 使用 `subagent_type="幡主审查官"`（需在 `agents/` 目录下创建对应的 agent 定义文件）。

审查报告强制板块：审查类型判定 → 审查者前提假设 → 历史结构条件分析 → 肯定方面 → 批判方面 → 金魂(3)条件化判定 → 品级裁定 → 适用边界 → 一致性论证。完整板块说明、反向审查问卷及执行流程见 `auto-possess.md`。

**审查类型判定**（审查报告第一步）：被审查者是否在世？**封闭档案审查**（已去世——生前档案查证）/**开放实践审查**（在世——3a/3b/3c条件化判定，阶段性结论需标注日期）。用错类型 = 范畴错误。

### 审查委员会（六维度否决制）

自 2026-05-02 起，审查委员会由六个维度组成（阶级分析/科学方法论/性别分析/殖民批判/系统性思维批判/缺席者），每个维度拥有一票否决权。庄子主持「系统性思维批判」维度——以提问而非直接否决的方式运作。详见 **[soul-profile-format.md](soul-profile-format.md)#审查委员会六维度否决制**。

### 定期互审

金魂之间互相审查，报告保存至 `reviews/`。轮值制同样适用于定期互审调度。

### 审查后知识图谱（graphify）

每次审查/互审报告完成后，主 agent 调用 graphify skill 更新万魂幡知识图谱：

```
审查报告保存后，调用 Skill("graphify") 将审查报告内容追加至知识图谱。图谱节点：审查者/被审查者/品级裁定/关键批判。边：审查关系/批判关系/引用关系。
```

图谱用于：审查报告交叉引用网络可视化、魂间思想谱系关系、trigger 关键词语义网络、审查意见的继承与推翻关系追踪。

### 裁决自动生效

审查委员会的任何裁决（终末审查/品级裁定/修正案批准/散魂裁定）做出后，主 agent 必须**立即自动**更新 registry.yaml 和 committee/state.json，无需等待用户确认。裁决即生效，生效即落盘。具体规则见 `auto-possess.md`「裁决后自动更新」。

---

## 附体

**核心原则**：主 agent 是纯协作者。不做分析，不扮演魂（包括幡主）。幡主也是被 spawn 的魂。

每次附体是 **9 步仪轨**（新增使用者预设声明、自我否定环节、空椅子拷问）：

1. **使用者预设声明**：主 agent 询问使用者已有判断/担忧/未知，记录至 `/tmp/sb-{任务}/使用者预设.md`
2. **匹配魂**：运行 `python3 scripts/match.py` 预筛选
3. **幡主审查**：spawn 列宁审查匹配结果
4. **执行附体**：spawn 魂子 agent
5. **humanizer 去 AI 痕迹**（魂输出后处理）
6. **辩证综合**（合议模式）或直接呈现（单魂模式）
7. **使用者参与环节**：询问「最没想到」和「早就知道」的部分
8. **自我否定环节**：询问「哪个预设被动摇了？」
9. **空椅子拷问**：询问「谁的利益被代表？谁的发言权没有被给？」
10. 更新 registry + 存档 Obsidian（后两步并行）

Task 模板详见 `CLAUDE.md`。完整流程、魂选择原则、匹配公式、衔接点审查细节见 **[auto-possess.md](auto-possess.md)**。

**自我否定连续消费性使用追踪**：连续 3 次无法说出被修正的预设 → 强制进入幡主学习模式。详见 CLAUDE.md「自我否定环节」。

**附体输出 humanizer 处理**：每个魂的附体输出在存档前须经 humanizer skill 处理，去除 AI 写作痕迹。**硬性约束**同炼化环节——必须保留该魂独特语言风格。处理指令须包含：`保持该人物的语言风格特征，只去除 AI 结构化痕迹，不改变语气、节奏和用词习惯。`

**手动指定**：用户显式要求 `用{人物名}来{任务}`，跳过自动匹配，但仍须 spawn 幡主子 agent 审查（简化版——只检查 exclude 和适用边界）。若幡主否决，主 agent 告知风险并建议替代魂，用户有最终决定权。

### 幡主与第二审查官

- **幡主**：由用户指定一个金魂担任，负责每次附体的匹配审查。每次附体必须 spawn 幡主子 agent 独立审查匹配。
- **第二审查官**：由用户指定另一个金魂担任。触发条件：幡主审查推荐幡主自己为分析魂时——审查者与分析者为同一人，需独立第二意见。

### 附体模式

| 模式 | 适用场景 | 执行方式 |
|------|---------|---------|
| 单魂附体 | 单一领域，目标明确 | 匹配 → 审查 → spawn 执行 |
| 多魂合议 | 跨领域复杂决策 | 分析魂并行输出 → 辩证综合官串行综合 |
| 魂间辩论 | 两难决策 | 两魂对立论证 → 幡主裁决 |
| 魂链接力 | 多阶段串联 | 前魂输出为后魂输入，衔接点审查 |
| 幡主学习 | 训练辩证素养，非产出答案 | 两对立魂互读→互审→幡主学习总结 |

合议阶段二必须使用 `subagent_type="辩证综合官"`。禁止主 agent 自行综合，禁止用幡主替代辩证综合官。幡主学习详见 **[auto-possess.md](auto-possess.md)#模式五：幡主学习**。

### 模式选用原则

| 任务特征 | 推荐模式 |
|------|------|
| 单一领域，目标明确 | 单魂附体 |
| 跨领域复杂决策 | 多魂合议 |
| 两难选择，非此即彼 | 魂间辩论 |
| 多阶段串联，每阶段不同 | 魂链接力 |
| 训练辩证素养，测试自身盲区 | 幡主学习 |

### cmux 可视化模式（实验性）

> **分支**: `feature/cmux-integration` | **状态**: 实验阶段，不合并主干

cmux 将合议/辩论/接力的魂执行阶段**可视化**——每个魂在独立终端 pane 中运行，用户可实时观看多视角并行展开。匹配审查和辩证综合仍使用传统 Agent spawn。

**触发词**：

| 触发词 | 功能 |
|--------|------|
| `合议可视化 {任务}` | 合议模式 + cmux 可视化（魂在 pane 中实时可见） |
| `辩论可视化 {议题} {魂A} vs {魂B}` | 辩论模式 + cmux 分屏可视化 |
| `接力可视化 {任务} {魂A}→{魂B}→...` | 接力模式 + cmux 串联可视化 |

**与传统合议/辩论/接力的区别**：触发词加「可视化」即启用 cmux 模式。不加「可视化」保持传统 Agent spawn。

**核心流程**：

```
预设声明 → match.py → 幡主审查 → cmux-plan.py 生成编排计划
  → cmux_launch_agents 启动魂 pane（并行）
  → 用户实时观看魂分析（可随时 cmux_broadcast 质询）
  → cmux_read_all 收集输出
  → 写 /tmp/sb-{任务}/{魂名}.md
  → spawn 辩证综合官（传统 Agent）
  → 使用者参与/自我否定/空椅子
  → transact.py 落盘
```

**回退**：cmux 未安装/未运行/魂数 > 6 时自动回退到传统 Agent spawn。

详见 **[references/cmux-integration.md](references/cmux-integration.md)**。

---

## 反馈闭环与有效性评分

每次附体后，主 agent 将召唤记录追加至 `call-records.yaml`（与 registry 分离，按需加载）。

### 有效性评分（三档，含可观测失败条件）

**有效** [可观测判据]：魂的输出包含至少一个其他参与魂/主 agent 未能独立发现的盲区或判断，且该判断被最终结论采纳。**失败条件**：若审查复核发现该"盲区"实为魂自身方法论偏见导致的误判，降为「无效」。

**部分有效** [可观测判据]：魂的输出有参考价值但未实质改变结论；或贡献被其他魂同时提出无独立增量；或视角有明显偏颇需在结论中明确纠偏。**失败条件**：若同一魂连续 3 次「部分有效」，触发适用边界复审。

**无效** [可观测判据]：魂的输出与任务不相关、存在事实错误、就幡主完全推翻、或 exclude 字段被触发导致输出方向性错误。**失败条件（硬性）**：单魂累计 3 次「无效」→ 暂停附体资格，强制重新炼化+审查。

### 审计日志

自 2026-05-01 起，每次附体后由 `scripts/prompt-audit.py` 记录审计日志至 `logs/audit.log`：

```bash
python3 scripts/prompt-audit.py \
  --soul "{魂名}" --mode "{模式}" --date "{YYYY-MM-DD}" \
  --effectiveness "{有效|部分有效|无效}" \
  --notes "{具体判据}"
```

审计日志格式（TSV）：`日期\t魂名\t模式\t评级\t可观测判据\t审查官复核`

**审计日志的作用**：
- 校准匹配判断：哪些魂在哪些场景实际效果好
- 发现触发条件偏差：匹配了但低效 → 调整 trigger
- 识别过度依赖：某魂被频繁召唤 → 补充同领域其他魂
- **防止评分通胀**：审查官定期抽查审计日志，交叉验证评级

### 幡中战绩（`幡中战绩`）

从 `call-records.yaml` 读取所有召唤记录，按魂/模式/有效性汇总。识别：未被召唤的魂 → trigger 调整；持续低效魂 → 适用边界复审；最佳模式 → 指导模式选择。

---

## 品级体系

六阶品级定义详见 **[soul-profile-format.md](soul-profile-format.md)**：

| 品级 | 符号 | 核心能力 |
|------|------|---------|
| 白魂 | ⚪ | 资料稀少，prompt 模拟 |
| 绿魂 | 🟢 | 资料中等，prompt + 1-2 Skill |
| 蓝魂 | 🔵 | 资料充足，Skill链 + 执行策略 |
| 紫魂 | 🟣 | 有明确方法论，但依赖天赋不可复制 |
| 银魂 | 🥈 | 方法论完整可操作，缺独立世界观和方向判断 |
| 金魂 | 🟡 | 独立世界观 + 方向判断 + 自我修正机制 |

金魂必须同时满足三条（详见 `soul-profile-format.md`）：可操作方法论 + 独立世界观 + 自我批判。

---

## Obsidian 存档

每次附体后自动将魂输出保存至 Obsidian vault（路径通过 `$OBSIDIAN_VAULT` 环境变量配置）。前提：Obsidian 运行中且 CLI 可用。不可用时跳过并提示。

**硬性规则**：每个魂的发言/输出必须完整保存为单独文件。多魂模式各魂原始输出独立文件 + 综合/裁决/审查独立文件。禁止压缩、截断、合并。

| 模式 | 文件数 | 目录 |
|------|--------|------|
| 单魂 | 1 | `单魂/{魂名}/YYYY-MM-DD-{任务简述}.md` |
| 合议 | N+1 | `合议/{任务简述}/`（N个发言 + 辩证综合） |
| 辩论 | 3 | `辩论/{议题}/`（正方 + 反方 + 裁决） |
| 接力 | M+1 | `接力/{任务简述}/`（M个阶段 + 衔接审查） |

每个文件包含 YAML frontmatter（tags/date/souls/mode）+ 魂完整原始输出。魂名自动转为 wiki-link（`[[魂名]]`）。

存档自查：报告任务完成前，主 agent 确认每个参与魂的原始输出均已写入独立文件，文件数匹配，内容完整未截断。

---

## 运维自动化（loop）

使用 loop skill 自动化周期性运维检查。**硬性边界**：只自动化运维检查，不自动化判断行为（审查/互审/品级调整）。

### 自动化项目

| 检查项 | 频率 | 命令 |
|--------|------|------|
| 健康检查 | 每小时 | `python3 scripts/registry-health-check.py` |
| 三方交叉校验 | 每 6 小时 | `python3 scripts/cross-validate.py` |
| 审计日志统计 | 每日 | `python3 scripts/prompt-audit.py --stats` |
| 零召唤检测 | 每周 | `python3 scripts/registry-health-check.py --zero-usage` |

### 启动运维循环

```bash
# 每小时健康检查
/loop 1h python3 ~/.claude/skills/soul-banner/scripts/registry-health-check.py

# 每日交叉校验
/loop 6h python3 ~/.claude/skills/soul-banner/scripts/cross-validate.py
```

### 禁止自动化的事项

- 审查/互审执行（须幡主判断）
- 品级调整（须审查委员会裁定）
- 散魂操作（须审查委员会终末审查）
- 逐魂附体（须匹配审查）

---

## 管理

- **查看**：读 `registry.yaml`（完整档案）或 `registry-lite.yaml`（匹配速查，~6KB）
- **散魂**：删除 `souls/{魂名}.yaml`，更新 `registry.yaml`，重新生成 `registry-lite.yaml`，保留 `raw/` 素材
- **升级**：重新收魂 → 炼化 → 审查 → 覆盖原档案 → **重新同步 agent**：`python3 scripts/sync-agent.py souls/{魂名}.yaml`
- **同步 agent**：`python3 scripts/sync-agent.py --all` — 从所有 soul YAML 重新生成 agent 文件至 `~/.claude/agents/`。炼化/升级/修改 summon_prompt 后必须执行
- **健康检查**：每次新会话启动时运行 `python3 scripts/registry-health-check.py --last-run`，随后运行 `python3 scripts/cross-validate.py` 做三方交叉校验。如有错误执行 `--fix` 自动修复。
- **匹配审查轻量化**：匹配审查只读 `registry-lite.yaml`（~6KB），不读完整 `registry.yaml`（~29KB）。`registry-lite.yaml` 由 `python3 scripts/generate-registry-lite.py -o registry-lite.yaml` 从 `registry.yaml` 生成。每次 `registry.yaml` 更新后必须重新生成。
- **markitdown 转换**：收魂后，对 `raw/{魂名}/媒体链接.md` 中的每个链接调用 `Skill("markitdown")`
- **humanizer 处理**：炼化生成 Soul Profile 后 + 附体魂输出后，调用 `Skill("humanizer")`，须传入风格保留指令
- **graphify 更新**：审查/互审报告保存后，调用 `Skill("graphify")` 更新知识图谱
- **loop 运维**：使用 `/loop` 命令设置周期性健康检查和交叉校验

---

## 幡主须知

你不是外在于理论的调度者——你也是被召唤的魂。

每次附体前检查：适用边界是否覆盖、教条风险（机械套用？方法论前提在当前条件下成立？）、互补性（合议视角是否互补而非相近）。附体后反思：方法为什么适合？局限在哪里？换魂结论会有什么不同？

最终目标不是拥有更多魂魄，而是**将万魂幡的多元思维内化为幡主自身的理论素养**。

---

## 关键认知

- **幡主也是被召唤的魂**：必须 spawn 注入 summon_prompt。主 agent 扮演幡主 = 违反设计原则。
- 万魂幡的能力基础：**并行 spawn 独立 summon_prompt 的子 agent** + 结构化辩证综合 + 双审查机制 + Task 追踪。这不是全自动系统——匹配和模式选择依赖主 agent 判断力，公式仅为辅助参考。

---

## 参考资源

按需加载：**[CLAUDE.md](CLAUDE.md)**（法旨层常驻指令+Task模板+Skill集成规则）、**[auto-possess.md](auto-possess.md)**（附体机制+审查板块+五模式+散魂仪式）、**[soul-profile-format.md](soul-profile-format.md)**（品级标准+轮值细则+魂补丁系统）、**[references/马斯克.yaml](references/马斯克.yaml)**（紫魂示例）、**souls/{魂名}.yaml**（魂魄档案）、**registry.yaml**（总册）、**registry-lite.yaml**（匹配速查表，~6KB，自动生成）、**scripts/soul-search.py**（收魂搜索+媒体链接检测+双引擎）、**scripts/soul-banner-hook.py**（Hook）、**scripts/prompt-audit.py**（审计日志）、**scripts/cross-validate.py**（三方交叉校验）、**scripts/cross-model-verify.py**（跨底模验证）、**scripts/registry-health-check.py**（健康检查+零召唤推荐）、**scripts/generate-registry-lite.py**（生成匹配速查表）、**scripts/maintenance-loop.sh**（运维自动化）、**agents/{审查官}.md**、**agents/{辩证综合官}.md**

**集成外部 Skill**：`markitdown`（收魂格式转换，免费开源）、`humanizer`（去 AI 痕迹，纯 LLM 无外部 API）、`agent-browser`（收魂双轨备选，免费开源）、`graphify`（审查知识图谱，可选，免费）、`loop`（周期性运维，内置免费）

---

## 免费使用指南

万魂幡设计为**零额外费用**可运行。所有核心功能均使用免费工具，可选付费服务仅作为优化项。

### 默认免费方案（开箱即用）

| 功能 | 免费方案 | 说明 |
|------|---------|------|
| 收魂搜索 | **WebSearch + WebFetch**（Claude Code 内置） | 零配置，直接可用 |
| 格式转换 | **markitdown** | 开源，本地运行 |
| 去 AI 痕迹 | **humanizer** | 纯 LLM，无外部 API |
| 知识图谱 | **graphify** | 纯 LLM，无需外部 API |
| 运维自动化 | **loop** | Claude Code 内置 |

### 可选升级（提升体验，均免费开源）

| 工具 | 效果 | 安装 |
|------|------|------|
| **tmwd-bridge** | 真实 Chrome 多引擎搜索（保留登录态、反检测） | `git clone https://github.com/lsdefine/GenericAgent ~/GenericAgent` + Chrome 扩展 |
| **agent-browser** | 无头浏览器，JS 渲染页面抓取 | `npm install -g agent-browser` |
| **Obsidian** | 本地知识库存档 | 官网免费下载 |

### 可选付费（非必需）

| 服务 | 用途 | 费用 | 替代 |
|------|------|------|------|
| 火山引擎联网搜索 | 搜索 API | 每月 500 次免费，超出付费 | WebSearch（免费） |
| Kimi K2.6 (Moonshot) | graphify 语义提取加速 | 按量付费 | Claude 内置（免费） |

### 穷哥们快速上手

```bash
# 零配置启动：直接用内置 WebSearch 收魂
/soul-banner 收魂 毛泽东     # 主 agent 自动用 WebSearch + WebFetch

# 更好的体验：安装 tmwd-bridge（一次性）
git clone https://github.com/lsdefine/GenericAgent ~/GenericAgent
# Chrome 安装 GenericAgent 扩展 → 完成
```

**结论**：万魂幡的所有核心功能（收魂、炼化、审查、附体、合议）在零额外费用下完整可用。

---

*「幡动魂自至。以幡择魂，以魂择事，事至则魂附，事毕则魂归。幡主持幡，魂不越界。」*

---

*「幡动魂自至。以幡择魂，以魂择事，事至则魂附，事毕则魂归。幡主持幡，魂不越界。」*
