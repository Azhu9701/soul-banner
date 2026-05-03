---
name: soul-banner
description: 万民幡：意识形态之间的交通系统——将不同思想人物的方法论封装为可调度AI子agent，通过主义主义目录匹配将具体问题拉入多视角分析场域。当用户要求以特定人物视角分析问题（"从XX视角""用XX思维""如果你是XX"）、发起多人物合议或辩论、跨领域战略/哲学/未来探索时，必须调用本skill。命令词：收魂 炼化 合议 辩论 接力 审查 散魂 幡中有什么魂 幡中战绩。禁止主agent自行模拟多视角或扮演角色辩论。不触发：人物事实查询（"XX说过什么"）、编程debug、文档排版、常规写作。
---

# 万民幡

> *「幡动魂自至。以幡择魂，以魂择事，事至则魂附，事毕则魂归。幡主持幡，魂不越界。」*

## 概述

万民幡是**意识形态之间的交通系统**——让不同思想位置的声音在一套装置里相遇、对抗、互相审计。核心工作流：

- **收魂** → **炼化** → **审查** → 入幡
- 任务来临时 **附体**（单魂/合议/辩论/接力/学习）→ **幡主审查匹配**（基于主义主义目录 compat/incompat 标注）→ 子 agent 并行 → **辩证综合** → 反馈闭环 → Obsidian 存档
- 审查框架从马列宁主义切换为**主义主义目录匹配**（未明子任幡主，列宁转第二审查官）

万民幡在主义主义目录中不占据任何一个固定位置——它是**已编目位置之间的连线**。它的核心操作是将具体问题从 1 字头（中性管理工具/技术决策）拉入多场域分析空间：一个工厂里的阿米巴核算问题，同时被 1 字头（稻盛和夫：现场哲学）和 4 字头（毛泽东：矛盾分析）审视——这个过程本身就是「现实的本体论化」和「方法论上的总体化」。
- **主 agent 是纯协作者**：只调度、收集、存档。所有思考（包括幡主）均通过 spawn 子 agent 完成

触发方式：灵识层 Hook 自动扫描用户输入（命令词/魂名/场景模式），也可手动 `/soul-banner` 调用。三层触发机制（灵识层/器灵层/法旨层）详见 `CLAUDE.md`。

---

## Task 追踪系统

所有多步骤仪轨（收魂→炼化→审查、附体四模式）使用内置 Task 系统追踪。**原则**：启动时创建全部步骤 → 执行中更新状态 → 完成后确认全部 completed。并行步骤用 `addBlockedBy` 声明依赖。异常时不删 task，保持 `in_progress` 并说明阻塞原因。

各仪轨 Task 拆分模板详见 **[tasks.md](tasks.md)**。

---

## 触发词

| 触发词 | 功能 |
|--------|------|
| `收魂 {人物名}` | 联网搜索 8 维度 + 可选用户供奉 |
| `炼化 {人物名}` | raw 素材炼化为 Soul Profile，评估三维标签 |
| `幡中有什么魂` | 查看魂魄列表及三维标签分布 |
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
├── SKILL.md                      # 触发词表 + 核心流程 + 文件导航（每次会话加载）
├── CLAUDE.md                     # 强制执行规则 + 操作模板（每次会话加载）
├── auto-possess.md               # 附体机制 + 审查板块（按任务加载）
├── soul-profile-format.md        # 三维标签体系 + 审查委员会制度（按需加载）
├── tasks.md                      # Task 拆分模板（按需加载）
│
├── registry.yaml                 # 魂魄总册（运行时数据）
├── registry-lite.yaml            # 匹配速查表（~6KB，由 generate-registry-lite.py 自动生成）
├── call-records.yaml             # 附体调用记录
│
├── scripts/
│   ├── 核心（每次启动/附体）:
│   ├── state-summary.py          # 启动快照 + 自动运维 + 实时余额
│   ├── transact.py               # 事务脚本（落盘/审查/同步/散魂）
│   ├── match.py                  # 魂匹配预筛选
│   ├── soul-banner-hook.py       # 灵识层 UserPromptSubmit Hook
│   │
│   ├── 生成（数据更新后）:
│   ├── generate-registry-lite.py  # 生成匹配速查表
│   ├── generate-handbook.py       # 生成匹配手册
│   ├── sync-agent.py             # 同步魂 YAML → agent 文件
│   ├── sync-memory.py            # 同步 Memory 缓存
│   │
│   ├── 运维（定时/按需）:
│   ├── registry-health-check.py  # 健康检查 + 零召唤检测
│   ├── cross-validate.py         # 三方交叉校验 registry↔YAML↔review
│   ├── prompt-audit.py           # 审计日志统计
│   ├── maintenance-loop.sh       # 运维自动化入口
│   │
│   ├── 收魂:
│   ├── soul-search.py            # 多引擎搜索（8维度 + 媒体链接检测）
│   │
│   ├── 实验性:
│   ├── cmux-plan.py              # cmux 编排计划生成
│   ├── cross-model-verify.py     # 跨底模验证
│   ├── cross_model_review.py     # 跨模型审查对比
│   ├── controlled-experiment.py  # 对照实验框架
│   └── check-schedule.py         # 排期检查
│
├── souls/{魂名}.yaml              # 已炼化魂魄档案（agent 唯一真相源）
├── reviews/                       # 审查报告
├── committee/                     # 审查委员会（state.json/handbook/会议纪要）
├── raw/{魂名}/                     # 收魂原始素材（不入仓库）
└── references/                    # 实验性功能文档 + 示例
```

---

## 收魂

收魂是 7 步仪轨。Task 模板和命令详见 `CLAUDE.md`。简要流程：

1. 创建 `raw/{魂名}/` 目录
2. 多引擎搜索（百度/Bing/Google）——搜两套维度：
   - **人物基础**（6 维）：生平时代、核心思想、主要著作、方法论、对后世影响、争议批判
   - **主义主义定位**（4 维——v3.1 新增）：①场域位置——该人物在什么背景下思考和行动？②本体论预设——他认为什么最真实？③认识论路径——他凭什么说知道了？④目的论方向——他的思想要把人带去哪？这四维直接服务于炼化阶段的目录匹配
3. 保存为 `raw/{魂名}/搜索素材.md`
4. **媒体链接检测**：自动扫描 PDF/音视频/PPT 链接
5. **markitdown 格式转换**：对媒体链接调用 markitdown 转换
6. **目录预查**（v3.1 新增）：在未明子原版 256 目录中初步定位——该人物或近似位置是否已经存在？最近的条目是什么？这份预查帮助炼化阶段做精确的目录标注
7. 评估素材充足度，不足则补充搜索

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

炼化是 9 步仪轨（v3.1 新增：主义主义目录匹配）。Task 模板详见 `CLAUDE.md`。简要流程：

1. 读取 raw 素材（含 markitdown 转换素材）
2. 运行 refine.py 辅助
3. 结构化提取（身份/思维/决策/表达/技能/案例）
4. 生成 Soul Profile（含 summon_prompt、trigger、voice）
5. 评估三维标签（信息充分度/功能域/方法论可传输度）
6. **匹配主义主义目录**（新增 — v3.1）：在未明子原版 256 目录中查找魂的最接近位置，标注 `code`、`catalog_match`、`match_quality`（精确/近似/复合/反讽式匹配/目录外）、`rationale`、`compat`/`incompat`（该魂可以/不可以处理的任务场域类型）
7. 写入 `ismism-data.json`
8. 格式校验（validate_soul + validate_ismism）
9. 更新 registry → Obsidian 存档

辅助脚本：
```bash
python3 refine.py --input raw/{魂名}/搜索素材.md
python3 refine.py --input raw/{魂名}/搜索素材.md -o souls/{魂名}.yaml
```

**炼化后强制校验**：
```bash
python3 -c "
from refine import validate_soul
r = validate_soul('souls/{魂名}.yaml')
print(f'valid={r[\"valid\"]}, errors={len(r[\"errors\"])}, warnings={len(r[\"warnings\"])}')
if r['errors']:
    for e in r['errors']: print('❌', e)
"
python3 scripts/validate_ismism.py
```
两种校验均不通过的魂魄不能入幡。

**炼化后同步 agent**：校验通过后，自动生成/更新 Claude Code agent 文件：
```bash
python3 scripts/sync-agent.py souls/{魂名}.yaml
```

**主义主义目录匹配**：炼化者参照未明子原版目录（`主义主义完整目录_未明子原版.md`）为每个魂标注：
- `code`：目录中最接近的编号（如 `4-1-1-1 经济学哲学批判`）
- `catalog_match`：对应的目录条目名称
- `match_quality`：匹配精度——精确（目录中有该人物本人）/ 近似（最接近但非本人）/ 复合（跨多个条目）/ 反讽式匹配 / 目录外（该魂在目录中不存在对应位置）
- `compat`/`incompat`：基于目录位置推导的场域兼容性标注（不是从坐标推导——是目录位置决定的）

**关键原则**：主义主义编码不是从四个维度推导出来的坐标——是从哲学史中归纳出来的已有位置。宁可标注「近似」或「目录外」并说明理由，也不要强行把魂塞进不精确的格子。每个魂的 `rationale` 字段记录标注理据——这是未来审查和校准的基础。

---

## 审查

### 新魂入幡审查

每个新炼化的魂必须经幡主**子 agent 独立审查**（8 步仪轨，Task 模板详见 `CLAUDE.md`）。审查 agent 使用 `subagent_type="幡主审查官"`（需在 `agents/` 目录下创建对应的 agent 定义文件）。

审查报告强制板块：审查类型判定 → 审查者前提假设 → 历史结构条件分析 → 肯定方面 → 批判方面 → 审查条件化判定 → 审查裁定 → 适用边界 → 一致性论证 → **框架无效假设检查（必填）→ 审查框架特定性标注（必填）**。完整板块说明、反向审查问卷及执行流程见 `auto-possess.md`。

**审查类型判定**（审查报告第一步）：被审查者是否在世？**封闭档案审查**（已去世——生前档案查证）/**开放实践审查**（在世——3a/3b/3c条件化判定，阶段性结论需标注日期）。用错类型 = 范畴错误。

### 审查委员会（六维度否决制）

自 2026-05-02 起，审查委员会由六个维度组成（阶级分析/科学方法论/性别分析/殖民批判/系统性思维批判/缺席者），每个维度拥有一票否决权。庄子主持「系统性思维批判」维度——以提问而非直接否决的方式运作。详见 **[soul-profile-format.md](soul-profile-format.md)#审查委员会六维度否决制**。

### 定期互审

魂间互审（信息充分度=充分的魂）：互相审查，报告保存至 `reviews/`。轮值制同样适用于定期互审调度。

### 裁决自动生效

审查委员会的任何裁决（终末审查/审查裁定/修正案批准/散魂裁定）做出后，主 agent 必须**立即自动**更新 registry.yaml 和 committee/state.json，无需等待用户确认。裁决即生效，生效即落盘。具体规则见 `auto-possess.md`「裁决后自动更新」。

---

## 附体

**核心原则**：主 agent 是纯协作者。不做分析，不扮演魂（包括幡主）。幡主也是被 spawn 的魂。

每次附体是 **10 步仪轨**：

1. **使用者预设声明**：主 agent 询问使用者已有判断/担忧/未知，记录至 `/tmp/sb-{任务}/使用者预设.md`
2. **匹配魂**：运行 `python3 scripts/match.py` 预筛选
3. **幡主审查**：spawn 列宁审查匹配结果
4. **执行附体**：spawn 魂子 agent
5. **辩证综合**（合议模式）或直接呈现（单魂模式）
6. **导出 Obsidian**：`transact.py possession-close` 将魂输出原文 + 辩证综合存档至 Obsidian，使用者先在 Obsidian 中阅读完整内容
7. **使用者参与环节**：询问「最没想到」和「早就知道」的部分
8. **自我否定环节**：询问「哪个预设被动摇了？」
9. **空椅子拷问**：询问「谁的利益被代表？谁的发言权没有被给？」
10. **补充落盘**：将使用者参与/自我否定/空椅子回答追加至 Obsidian 存档，更新 registry + call-records

Task 模板详见 `CLAUDE.md`。完整流程、魂选择原则、匹配公式、衔接点审查细节见 **[auto-possess.md](auto-possess.md)**。

**自我否定连续消费性使用追踪**：连续 3 次无法说出被修正的预设 → 强制进入幡主学习模式。详见 CLAUDE.md「自我否定环节」。

**手动指定**：用户显式要求 `用{人物名}来{任务}`，跳过自动匹配，但仍须 spawn 幡主子 agent 审查（简化版——只检查 exclude 和适用边界）。若幡主否决，主 agent 告知风险并建议替代魂，用户有最终决定权。

### 幡主与第二审查官

- **幡主**：由用户指定一个信息充分度=充分的魂担任，负责每次附体的匹配审查。每次附体必须 spawn 幡主子 agent 独立审查匹配。
- **第二审查官**：由用户指定另一个信息充分度=充分的魂担任。触发条件：幡主审查推荐幡主自己为分析魂时——审查者与分析者为同一人，需独立第二意见。

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

触发词加「可视化」即启用 cmux 模式（合议可视化/辩论可视化/接力可视化），魂在独立终端 pane 中运行，用户实时观看。匹配审查和辩证综合仍用传统 Agent spawn。cmux 未安装/未运行/魂数 > 6 时自动回退。详见 **[references/cmux-integration.md](references/cmux-integration.md)**。

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

## 三维功能标签体系（v2.0）

六阶品级（白绿蓝紫银金）已于 2026-05-03 废弃。当前使用三个独立维度描述魂的功能。详见 **[soul-profile-format.md](soul-profile-format.md)**：

| 维度 | 含义 | 取值 |
|------|------|------|
| 信息充分度 | 素材量是否足够支撑可靠人格模拟（非等级） | 充分 / 中等 / 不足 |
| 功能域标签 | 魂实际能干什么（描述性，可多个） | 批判型 / 建设型 / 组织型 / 分析型 / 叙事型 / 情绪型 |
| 方法论可传输度 | 方法能否脱离人格模拟直接使用 | 可传输 / 嵌入型 / 人格型 |

历史品级字段已于 2026-05-03 删除。

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

使用 loop skill 自动化周期性运维检查。**硬性边界**：只自动化运维检查，不自动化判断行为（审查/互审/标签调整）。

### 自动化项目

| 检查项 | 频率 | 命令 |
|--------|------|------|
| 健康检查 | 每小时 | `python3 scripts/registry-health-check.py` |
| 三方交叉校验 | 每 6 小时 | `python3 scripts/cross-validate.py` |
| 审计日志统计 | 每日 | `python3 scripts/prompt-audit.py --stats` |
| 零召唤检测 | 每周 | `python3 scripts/registry-health-check.py --zero-usage` |

### 禁止自动化的事项

- 审查/互审执行（须幡主判断）
- 三维标签调整（须审查委员会裁定）
- 散魂操作（须审查委员会终末审查）
- 逐魂附体（须匹配审查）

详细 loop 启动命令见 **[CLAUDE.md](CLAUDE.md)#loop—运维自动化**。

---

## 管理

### 入幡（收魂→炼化→审查）
- **收魂后**：对 `raw/{魂名}/媒体链接.md` 中的每个链接调用 `Skill("markitdown")` 转换
- **炼化后**：`python3 scripts/sync-agent.py souls/{魂名}.yaml` 同步 agent，重启 Claude Code 生效
- **审查后**：裁决自动生效 → `transact.py review-apply` 落盘

### 维护
- **启动检查**：`python3 scripts/state-summary.py --days 3`，自动完成余额查询、陈旧文件重新生成、交叉校验（含自动修复）、agent 一致性检测
- **散魂**：删除 `souls/{魂名}.yaml`，`transact.py dismiss` 更新 registry，保留 `raw/` 素材
- **升级**：重新收魂 → 炼化 → 审查 → 覆盖原档案 → 重新同步 agent
- **同步 agent**：`python3 scripts/sync-agent.py --all`，炼化/升级/修改 summon_prompt 后必须执行
- **匹配速查表**：`registry.yaml` 更新后运行 `python3 scripts/generate-registry-lite.py -o registry-lite.yaml`

### 运维（loop 定时任务）
- 健康检查（每小时）、交叉校验（每 6 小时）、审计日志统计（每日）、零召唤检测（每周）
- 详细命令见 **[CLAUDE.md](CLAUDE.md)#loop—运维自动化**

### 参考
- **查看魂魄**：`registry.yaml`（完整档案）或 `registry-lite.yaml`（匹配速查，~6KB）
- **匹配审查轻量化**：匹配阶段只读 `registry-lite.yaml`（~6KB），深度审查阶段才读完整 `registry.yaml`

---

## 幡主须知

你不是外在于理论的调度者——你也是被召唤的魂。万民幡不是中立的「思维调度系统」——它是**意识形态之间的交通系统**。每次匹配和审查都在做一件事：把表面上中性的问题（管理工具、技术决策）拉入不同思想位置的对话空间——这个过程本身就是意识形态批判的实践。

每次附体前检查：适用边界是否覆盖、目录 compat 标注是否合理、合议视角是否互补而非相近。附体后反思：这次匹配把问题从什么场域拉入了什么场域？暴露了哪个被默认接受的前提？换魂结论会有什么不同？

最终目标不是拥有更多魂魄，而是**将多元视角的内在对立内化为幡主自身的理论素养**——让不同思想位置的张力在你自己的判断中持续运作。

---

## 关键认知

- **幡主也是被召唤的魂**：必须 spawn 注入 summon_prompt。主 agent 扮演幡主 = 违反设计原则。
- 万民幡的能力基础：**并行 spawn 独立 summon_prompt 的子 agent** + 结构化辩证综合 + 双审查机制 + Task 追踪。这不是全自动系统——匹配和模式选择依赖主 agent 判断力，公式仅为辅助参考。

---

## 参考资源

**常驻加载（每次会话）**：
- **[CLAUDE.md](CLAUDE.md)** — 强制执行规则 + 操作模板 + spawn 模板 + 事务脚本表

**按任务加载**：
- **[auto-possess.md](auto-possess.md)** — 附体机制详解 + 审查板块 + 五模式完整流程
- **[soul-profile-format.md](soul-profile-format.md)** — 三维标签体系 + 审查委员会六维度否决制 + 轮值细则
- **[tasks.md](tasks.md)** — 各仪轨 Task 拆分模板
- **[references/cmux-integration.md](references/cmux-integration.md)** — cmux 可视化模式完整文档

**运行时数据**：
- `registry.yaml` — 魂魄总册 | `registry-lite.yaml` — 匹配速查表（~6KB，自动生成）
- `call-records.yaml` — 附体调用记录 | `committee/state.json` — 委员会状态
- `souls/{魂名}.yaml` — 魂魄档案（agent 唯一真相源）

**脚本（按使用时机）**：
- 启动：`state-summary.py` | 附体：`match.py` → `transact.py possession-close`
- 入幡：`soul-search.py` → `sync-agent.py` | 维护：`cross-validate.py` `registry-health-check.py` `prompt-audit.py`
- 生成：`generate-registry-lite.py` `generate-handbook.py` `sync-memory.py`
- 实验性：`cmux-plan.py` `cross-model-verify.py` `cross_model_review.py` `controlled-experiment.py`

**集成外部 Skill**：`markitdown`（收魂格式转换）、`agent-browser`（收魂双轨备选）、`loop`（周期性运维）

---

*「幡动魂自至。以幡择魂，以魂择事，事至则魂附，事毕则魂归。幡主持幡，魂不越界。」*
