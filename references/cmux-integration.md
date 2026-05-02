# cmux × 万民幡 集成设计

> **分支**: `feature/cmux-integration` | **状态**: 实验阶段 | **不合并主干**

## 核心理念

万民幡目前通过 `Agent(subagent_type="{魂名}")` 并行 spawn 魂子 agent，魂在后台运行，用户**看不到**思考过程。cmux 将这个过程**可视化**——每个魂在独立的终端 pane 中运行，用户可以实时观看多视角并行展开。

**实质变化**：从「主 agent 告诉你魂想了什么」变成「你看着魂为自己思考」。

## 架构（v4: Agent 调度器 — ~500 token/pane）

```
主 agent（纯协作者）              cmux Workspace（AI CLI pane）        魂 Agent
┌────────────────────┐       ┌─────────────────────────────┐     ┌──────────────┐
│ 1. cmux-plan.py    │       │ pane 1: 🟡 费曼              │     │ 费曼 agent   │
│    → plan JSON     │       │  收到调度指令                │     │ Write → 文件 │
│ 2. mkdir + touch   │       │  → Agent(subagent_type      │     └──────────────┘
│ 3. cmux_launch_    │──────▶│    ="费曼")                 │     ┌──────────────┐
│    agents(assign-  │       │  → 等待完成                  │     │ 鲁迅 agent   │
│    ments=[...])    │       │  → 报告「费曼 完成」         │     │ Write → 文件 │
│ 4. cmux_read_all   │       ├─────────────────────────────┤     └──────────────┘
│    监控进度         │◀──────│ pane 2: 🟡 鲁迅              │
│ 5. Read 文件        │       │  收到调度指令                │
│ 6. spawn 辩证综合官  │       │  → Agent(subagent_type      │
└────────────────────┘       │    ="鲁迅")                 │
                             └─────────────────────────────┘
```

### 三层分工

| 层 | 工具 | 可视化 | token |
|----|------|--------|-------|
| 匹配审查 | `Agent(subagent_type="列宁")` | 不可见 | 正常 |
| cmux 调度 | `cmux_launch_agents` AI CLI pane | **实时可见** | **~500/pane** |
| 魂分析 | `Agent(subagent_type="{魂名}")`（pane 内调用） | 不可见 | 正常 |
| 辩证综合 | `Agent(subagent_type="辩证综合官")` | 不可见 | 正常 |

**核心**：cmux pane 只做调度——收到指令 → 调用 Agent(subagent_type) → 等待完成。分析由魂 agent 完成，质量与传统模式完全一致。额外开销仅每 pane ~500 token 调度指令。

## 新增/修改文件

| 文件 | 类型 | 说明 |
|------|------|------|
| `scripts/cmux-plan.py` | 新增 | 编排计划生成器：读魂 YAML → 生成 pane 调度 prompt + agent 分析 prompt → JSON |
| `CLAUDE.md` | 修改 | 新增 cmux 操作模板（§cmux 可视化模式 v4） |
| `SKILL.md` | 修改 | 新增 cmux 可视化模式章节（v4） |
| `references/cmux-integration.md` | 新增 | 本文档 |

## 工作流

### 合议模式（cmux 版）

```
1. 使用者预设声明（主 agent 询问）
2. match.py ↓
3. 幡主审查（spawn 列宁子 agent，禁止读文件）↓
4. cmux-plan.py --task "..." --souls A,B,C --mode conference -o /tmp/cmux-plan.json
5. mkdir -p /tmp/sb-{slug} && touch /tmp/sb-{slug}/{A}.md /tmp/sb-{slug}/{B}.md ...
6. cmux_launch_agents(cli="claude", count=N, assignments=[...], tab_names=[...], progress=0.3)
   ┌────────────────────────────────────────┐
   │ 每个 pane 收到调度指令                   │
   │ → Agent(subagent_type="{魂名}")         │
   │ → 魂 agent 分析 → Write 输出文件         │
   │ → 报告「{魂名} 完成」                    │
   │ 主 agent 周期性 cmux_read_all 监控进度   │
   └────────────────────────────────────────┘
7. cmux_set_progress(0.7)
8. 主 agent Read /tmp/sb-{slug}/*.md（逐字复制）
9. spawn 辩证综合官（读文件 → 五步综合）
10. cmux_set_progress(1.0)
11. 使用者参与 / 自我否定 / 空椅子
12. transact.py possession-close
13. 可选：关闭或保留 cmux workspace
```

### 辩论模式（cmux 版）

```
1-3. 同合议
4. cmux-plan.py --task "..." --souls A,B --mode debate -o /tmp/cmux-plan.json
5. cmux_launch_agents（正方 + 反方，左右分屏）
6. 两魂各独立输出立论
7. 主 agent 读双方立论 → cmux_orchestrate 交换论点
   - 正方 pane 收到反方论点 → 反驳
   - 反方 pane 收到正方论点 → 反驳
8. cmux_read_all → 获取双方最终输出
9. spawn 辩证综合官（读双方文件 → 裁决）
10-13. 同合议
```

### 接力模式（cmux 版）

```
1-3. 同合议
4. cmux-plan.py --task "..." --souls A,B,C --mode relay -o /tmp/cmux-plan.json
5. cmux_launch_agents（3 个 pane，第 1 棒先启动）
6. 第 1 棒完成 → Read 输出 → cmux_orchestrate 注入第 2 棒 pane
7. 第 2 棒基于上一位输出继续 → 重复
8. 收集所有输出 → 写文件
9. 衔接点审查（spawn 幡主）
10-13. 同合议
```

## 实时质询

cmux 让质询从「事后追问」变成「事中介入」：

```
用户观察魂的分析过程中想追问
  → 主 agent 用 cmux_broadcast 向所有 pane 广播质询
  → 所有魂实时收到质询，在各自分析中回应
  → cmux_read_all 获取质询回应
  → 追加至 Obsidian 存档
```

## 魂 prompt 格式

v4 中，魂的分析 prompt 通过 pane 调度指令中的 `Agent(prompt=...)` 参数传入，summon_prompt 由 Agent 系统自动注入（与主线一致）：

**Pane 调度指令**（~500 token）：
```markdown
你的唯一任务：使用 Agent 工具调用魂 agent，不要自己分析。

请使用以下参数调用 Agent 工具：
  subagent_type: "费曼"
  description: "{任务简述}"
  prompt: 见下方「魂 agent prompt」部分

等待 agent 完成，确认 /tmp/sb-{slug}/费曼.md 已写入，报告「费曼 完成」即可。

---

## 魂 agent prompt

{任务描述}

## 时代背景
你被召唤到2026年的中国。此时：
- 互联网平台是主要的公共话语空间
- 算法推荐以互动率为核心指标
- {任务相关的当代环境说明}

## 输出要求
请将你的完整分析结果写入 /tmp/sb-{slug}/费曼.md。这将用于后续的辩证综合。

---
本魂基于{炼化日期}收魂素材炼化。这不是费曼本人——AI 模拟。
```

**关键设计决策**：pane CLI 自身不做分析，只做 Agent 调用。这保证了：
- summon_prompt 自动注入（通过 Agent 系统）
- 分析质量与主线完全一致
- pane 间无 summon_prompt 差异风险

## cmux-plan.py 用法

```bash
# 合议
python3 scripts/cmux-plan.py \
  --task "分析小红书平台上知识类内容的竞争力" \
  --souls 毛泽东,费曼,鲁迅 \
  --mode conference \
  --era "小红书以图文笔记为主，知识类内容面临娱乐化的竞争" \
  -o /tmp/cmux-plan.json

# 辩论
python3 scripts/cmux-plan.py \
  --task "是否应该在产品中引入算法推荐" \
  --souls 邓小平,鲁迅 \
  --mode debate \
  -o /tmp/cmux-plan.json

# 接力
python3 scripts/cmux-plan.py \
  --task "设计一个AI教育产品的市场策略" \
  --souls 费曼,邓小平,毛泽东 \
  --mode relay \
  -o /tmp/cmux-plan.json
```

输出 JSON 示例：
```json
{
  "mode": "conference",
  "task_slug": "分析小红书平台知识内容竞争力",
  "workspace_name": "conference: 分析小红书平台知识内容竞争力",
  "temp_dir": "/tmp/sb-分析小红书平台知识内容竞争力",
  "assignments": [
    "{毛泽东 pane 调度 prompt（~500 char）}",
    "{费曼 pane 调度 prompt（~500 char）}",
    "{鲁迅 pane 调度 prompt（~500 char）}"
  ],
  "tab_names": ["🟡 毛泽东", "🟡 费曼", "🟡 鲁迅"],
  "output_paths": [
    "/tmp/sb-.../毛泽东.md",
    "/tmp/sb-.../费曼.md",
    "/tmp/sb-.../鲁迅.md"
  ],
  "status": {"模式": "conference", "参与魂": "毛泽东, 费曼, 鲁迅", "阶段": "调度魂 agent 中"},
  "progress_label": "conference进度"
}
```

## 与主干的关键差异

| 项目 | 主干（Agent 子 agent） | 分支（cmux v4） |
|------|----------------------|-------------------|
| 魂运行方式 | 主 agent spawn `Agent(subagent_type)` | cmux pane → `Agent(subagent_type)` |
| summon_prompt 注入 | Agent 系统自动注入 | **完全一致**（pane 内 Agent 调用） |
| 分析质量 | Agent 保证 | **完全一致** |
| 思考过程 | 不可见 | **实时可见**（pane 显示调度和文件写入确认） |
| 额外 token | 0 | ~500/pane（调度指令） |
| 质询 | 事后 spawn agent | 事中 `cmux_broadcast` 或 spawn agent |

## 设计演进

| 版本 | 架构 | 问题 |
|------|------|------|
| v1 | cmux pane 直接分析（粘贴 summon_prompt） | 质量差——无 Agent 系统注入 |
| v2 | cmux pane 调用 Agent(subagent_type) | 每 pane ~16K token 调度开销 |
| v3 | cmux pane 纯 tail -f 显示器 | cmux 不支持程序化创建终端类型 pane |
| v4 | cmux_launch_agents + 极简调度 prompt | ✅ 当前方案 |

## 决策点（待实验验证）

1. **调度 prompt 最小化**：~500 token/pane 是否足够引导 pane CLI 正确调用 Agent？是否需要更详细的错误处理指令？
2. **cmux_launch_agents 投递可靠性**：首次投递偶有丢失（v2 测试观察），需验证 cmux 侧是否已修复。
3. **资源消耗**：N 个独立 CLI 实例 + N 个 Agent 子 agent，与主线 N 个 Agent 子 agent 对比？
4. **回退机制**：cmux 未安装/未运行/魂数 > 6 时自动回退传统 Agent spawn。
5. **质询实时性**：cmux_broadcast 后魂是否能实时回应？还是需要等当前 Agent 调用完成？

## 后续计划

- [ ] 完成首次 v4 cmux 合议实验，记录效果对比
- [ ] 对比 v4 与主线的 token 消耗和完成时间
- [ ] 考虑是否需要 `cmux-possess.py` 封装完整流程
- [ ] 评估是否值得合并回主干
