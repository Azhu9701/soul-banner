# cmux × 万魂幡 集成设计

> **分支**: `feature/cmux-integration` | **状态**: 实验阶段 | **不合并主干**

## 核心理念

万魂幡目前通过 `Agent(subagent_type="{魂名}")` 并行 spawn 魂子 agent，魂在后台运行，用户**看不到**思考过程。cmux 将这个过程**可视化**——每个魂在独立的终端 pane 中运行，用户可以实时观看多视角并行展开。

**实质变化**：从「主 agent 告诉你魂想了什么」变成「你看着魂为自己思考」。

## 架构

```
主 agent（纯协作者）             cmux Workspace             Agent 系统
┌──────────────────┐          ┌────────────────────┐     ┌──────────────┐
│ 1. match.py      │          │ pane 1: 调度器      │     │ 毛泽东 agent │
│ 2. spawn 幡主审查  │ cmux MCP│  → Agent("毛泽东") ──▶│ summon_prompt │
│ 3. cmux-plan.py  │─────────▶│    "分析中..."       │     │ 自动注入     │
│ 4. 分发任务       │          │                     │     └──────────────┘
│ 5. 监控进度       │◀─────────│ pane 2: 调度器      │     ┌──────────────┐
│ 6. Read 输出文件   │          │  → Agent("费曼")  ──▶│ 费曼 agent   │
│ 7. spawn 辩证综合官│          │    "分析中..."       │     │ summon_prompt │
│ 8. 落盘          │          │                     │     │ 自动注入     │
└──────────────────┘          └────────────────────┘     └──────────────┘
```

### 四层分工

| 层 | 工具 | 可视化 | 职责 |
|----|------|--------|------|
| 匹配审查 | `Agent(subagent_type="列宁")` | 不可见 | 快速匹配判断 |
| cmux 调度 | `cmux pane (cli="claude")` | **实时可见** | 调用 Agent 工具，不做分析 |
| 魂分析 | `Agent(subagent_type="{魂名}")` | 不可见（agent 内部） | summon_prompt 由 agent 系统注入 |
| 辩证综合 | `Agent(subagent_type="辩证综合官")` | 不可见 | 读文件做五步综合 |

**关键**：cmux pane 不直接回答问题——它调用 `Agent(subagent_type="{魂名}")` 来保证分析质量与主线一致。

## 新增/修改文件

| 文件 | 类型 | 说明 |
|------|------|------|
| `scripts/cmux-plan.py` | 新增 | 编排计划生成器：读魂 YAML → 生成 cmux 参数 JSON |
| `CLAUDE.md` | 修改 | 新增 cmux 操作模板（§cmux 可视化模式） |
| `SKILL.md` | 修改 | 新增 cmux 可视化模式章节 |
| `references/cmux-integration.md` | 新增 | 本文档 |

## 工作流

### 合议模式（cmux 版）

```
1. 使用者预设声明（主 agent 询问）
2. match.py ↓
3. 幡主审查（spawn 列宁子 agent，禁止读文件）↓
4. cmux-plan.py --task "..." --souls A,B,C --mode conference -o /tmp/cmux-plan.json
5. cmux_new_workspace（以任务名命名）
6. cmux_launch_agents + cmux_set_progress(0.3)
   ┌────────────────────────────────────────┐
   │ 此时用户可以实时观看 3 个 pane 并行分析  │
   │ 主 agent 周期性 cmux_read_all 监控进度   │
   └────────────────────────────────────────┘
7. cmux_set_progress(0.7)
8. cmux_read_all_deep → 获取每个魂的最终输出
9. 写 /tmp/sb-{任务}/{魂名}.md（逐字复制）
10. spawn 辩证综合官（读文件 → 五步综合）
11. cmux_set_progress(1.0)
12. 使用者参与 / 自我否定 / 空椅子
13. transact.py possession-close
14. 可选：关闭或保留 cmux workspace
```

### 辩论模式（cmux 版）

```
1-3. 同合议
4. cmux-plan.py --task "..." --souls A,B --mode debate -o /tmp/cmux-plan.json
5. cmux_new_workspace
6. cmux_launch_agents（正方 + 反方，左右分屏）
7. 两魂各独立输出立论
8. 主 agent 读双方立论 → 用 cmux_orchestrate 交换论点
   - 正方 pane 收到反方论点 → 反驳
   - 反方 pane 收到正方论点 → 反驳
9. cmux_read_all_deep → 获取双方最终输出
10. spawn 辩证综合官（读双方文件 → 裁决）
11-14. 同合议
```

### 接力模式（cmux 版）

```
1-3. 同合议
4. cmux-plan.py --task "..." --souls A,B,C --mode relay -o /tmp/cmux-plan.json
5. cmux_new_workspace
6. cmux_launch_agents（3 个 pane，第 1 棒先启动）
7. 第 1 棒完成 → cmux_read_all_deep 获取输出
8. cmux_orchestrate 将第 1 棒输出注入第 2 棒 pane
9. 第 2 棒基于上一位输出继续 → 重复
10. 收集所有输出 → 写文件
11. 衔接点审查（spawn 幡主）
12-14. 同合议
```

## 实时质询

cmux 让质询从「事后追问」变成「事中介入」：

```
用户观察魂的分析过程中想追问
  → 主 agent 用 cmux_broadcast 向所有 pane 广播质询
  → 所有魂实时收到质询，在各自分析中回应
  → cmux_read_all_deep 获取质询回应
  → 追加至 Obsidian 存档
```

## 魂 prompt 格式

通过 cmux 启动的魂使用独立 Claude CLI，不经过 `Agent(subagent_type=...)` 机制。prompt 直接包含 summon_prompt：

```markdown
{任务描述}

{该魂的 summon_prompt（从 souls/{魂名}.yaml 提取）}

## 时代背景
你被召唤到 2026 年的中国。此时：
- 互联网平台是主要的公共话语空间
- 算法推荐以互动率为核心指标
- {任务相关的当代环境说明}

你的分析对象生活在此时此地。请在分析中注意你自身时代的局限。

---
本魂基于{炼化日期}收魂素材炼化，素材来源包括多引擎搜索和公开文献。
这不是{魂名}本人——这是基于其公开文本的 AI 模拟。
```

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
  "mode": "合议",
  "workspace_name": "合议: 分析小红书平台知识内容竞争力",
  "cli": "claude",
  "count": 3,
  "assignments": ["{毛泽东完整prompt}", "{费曼完整prompt}", "{鲁迅完整prompt}"],
  "tab_names": ["🟡 毛泽东", "🟡 费曼", "🟡 鲁迅"],
  "status": {"模式": "合议", "参与魂": "毛泽东, 费曼, 鲁迅", "阶段": "并行分析中"},
  "progress_label": "合议进度"
}
```

## 与主干的关键差异

| 项目 | 主干（Agent 子 agent） | 分支（cmux 可视化） |
|------|----------------------|-------------------|
| 魂运行方式 | `Agent(subagent_type="{魂名}")` | cmux pane 中的独立 CLI |
| summon_prompt 注入 | 自动（agent 文件） | 手动（cmux-plan.py 拼接） |
| 思考过程 | 不可见 | 实时可见 |
| 质询时机 | 事后 | 事中 |
| 状态追踪 | 无 | 进度条 + 状态栏 |
| 输出收集 | Agent 返回结果 | cmux_read_all_deep |

## 决策点（待实验验证）

1. **魂 CLI 实例的自主性**：cmux pane 中的 Claude CLI 是否能像子 agent 一样完成复杂分析？还是需要更明确的指令引导？
2. **输出格式一致性**：独立 CLI 的输出格式可能与子 agent 不同，辩证综合官是否能有效解析？
3. **资源消耗**：N 个独立 CLI 实例 vs N 个子 agent，token 和时间成本对比？
4. **是否需要回退机制**：当 cmux 不可用时（未安装/未运行），是否自动回退到传统 Agent 模式？
5. **质询的实时性**：cmux_broadcast 后魂是否能实时回应？还是需要等当前分析完成？

## 后续计划

- [ ] 完成首次 cmux 合议实验，记录效果对比
- [ ] 根据实验反馈调整 prompt 模板
- [ ] 考虑是否需要 `cmux-possess.py` 封装完整流程
- [ ] 评估是否值得合并回主干
