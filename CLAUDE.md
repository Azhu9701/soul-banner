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

**魂魄 agent 文件**：常用魂在 `~/.claude/agents/{魂名}.md` 有标准化 agent 定义（含 summon_prompt、tools、model）。当前已入驻：列宁、毛泽东、费曼、鲁迅、未明子、邓小平。spawn 魂时直接使用 `subagent_type="{魂名}"`。

**审查 spawn**：新魂入幡审查和附体前匹配审查，spawn `subagent_type="幡主审查官"`。用户需在 `agents/` 目录下创建对应的 agent 定义文件，注入幡主的 summon_prompt 和三模式审查职责（匹配审查/品级审查/金魂互审）。

**辩证综合 spawn**：合议模式阶段二，spawn `subagent_type="辩证综合官"`。该 agent 定义了五步综合法（共识/分歧/盲区/主要矛盾/行动纲领）。

**Spawn 魂的标准模板**：
```
Agent(
  subagent_type="{魂名}",
  description="{任务简述} — {魂名}视角",
  prompt="{任务描述}"
)
```

**更新 registry.yaml**：使用 Python 脚本（heredoc 方式）。召唤记录追加至 `call-records.yaml` 而非 registry。示例：
```bash
python3 << 'PYEOF'
import yaml, datetime
...
PYEOF
```

**炼化后强制校验**：见 SKILL.md「炼化后强制校验」章节。校验不通过（valid=False）的魂魄不能入幡。

**Obsidian 自动同步**：每个新魂魄炼化完成后，用 `refine.py` 同步至 Obsidian vault：
```python
from refine import sync_soul_to_obsidian
sync_soul_to_obsidian('souls/{魂名}.yaml')
```
审查报告则直接从 `reviews/` 复制至 `{vault}/万魂幡/审查/`。

**存档 Obsidian**：直接写入 vault 文件系统（vault 路径通过 `$OBSIDIAN_VAULT` 环境变量配置，默认为 `$HOME/ob`）。长内容用 Write 工具，短内容可用 `obsidian create` CLI。

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

## 健康检查规则

每次启动新会话时，主 agent 必须检查 registry 健康状态：
```bash
python3 scripts/registry-health-check.py --last-run
```
如果输出 `NEVER_RUN` 或 `STALE:`（超过 24 小时未运行），则执行完整检查：
```bash
python3 scripts/registry-health-check.py
```

健康检查后，必须运行三方交叉校验：
```bash
python3 scripts/cross-validate.py
```
如有错误（exit code != 0），必须执行 `python3 scripts/cross-validate.py --fix` 自动修复，然后重新校验确认 0 错误。

**会话结束时**，在更新 registry 或魂 YAML 之后，也要重新运行交叉校验，确保写入操作未引入不一致。

检查结果不需要用户确认——主 agent 自行判断是否需要修复数据不一致问题。

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
