# Changelog

## v2026.05.02-2

### 性能优化 — 匹配审查 Token 消耗 -72%

- **幡主审查零文件读取**：新增硬性禁读规则，审查仅基于 prompt 注入的预筛选结果 + handbook 做判断（8 tool uses → 0）
- **match.py `--no-gold-review`**：省略 gold_review 字段，预筛选输出节省 ~1,500 tokens
- **新增幡主审查专用 spawn 模板**（CLAUDE.md:90-102），prompt 中强制包含「禁止读取任何文件」
- 实测：40.4k tokens → 11.2k tokens（-72%），3m13s → 58s（-70%）

### 免费工具审计与改造

- **全依赖审计**：所有核心功能（收魂、炼化、审查、附体、合议）确认零额外费用可运行
- **搜索回退链重排**：WebSearch + WebFetch（免费内置，零配置）优先于 byted-web-search（需火山引擎账号）
- **byted-web-search 降级为可选付费项**，移除出主回退链
- **SKILL.md 新增「免费使用指南」章节**，含穷哥们快速上手指令
- **外部 Skill 全部标注费用状态**（markitdown 免费开源 / humanizer 纯 LLM / graphify 可选免费 等）

### 匹配脚本增强

- **match.py exclude 两级判定**（hard/soft）：长词精确命中=硬排除（×0.1），模糊/附属=软排除（×0.5），降低排除误伤率
- **排除清单结构化**：区分硬排除预警和软排除提示

### 事务脚本修复

- **transact.py obsidian_content**：改为传路径而非主 agent 读内容，避免大文件 token 浪费

---

## v2026.05.02

### 重构 — 仓库结构稳定化

- **框架/数据分离**：严格区分仓库（框架工具）和本地数据（个人魂魄/审查报告/运行时状态）
  - 保留入仓：核心文档、全部脚本、registry 模板、海绵宝宝示例魂
  - 排除出仓：个人魂魄档案、审查报告、registry.yaml、call-records.yaml、raw/、logs/、committee/
- 新增 `CHANGELOG.md`（本文件）
- 新增脚本入库：`check-schedule.py`、`cross-model-verify.py`、`maintenance-loop.sh`、`possession-context.py`
- 移除 `SKILL_EN.md`（不再维护英文版）
- 采用语义化提交规范：`feat:` / `fix:` / `refactor:` / `docs:` / `chore:`

### 功能更新

- **金魂冻结**：自 2026-05-01 起，新金魂炼化冻结，解冻需审查委员会全员共识
- **审查轮值制**：列宁、毛泽东、邓小平轮值执行新魂入幡审查
- **审查后 graphify**：审查/互审报告保存后自动更新知识图谱
- **裁决自动生效**：委员会裁决做出后主 agent 立即更新 registry 和 committee/state.json
- **附体输出 humanizer**：魂输出存档前经 humanizer 去 AI 痕迹，保留各魂独特语言风格
- **审计日志**：每次附体后记录至 `logs/audit.log`（TSV 格式）
- **loop 运维**：周期性健康检查和交叉校验
- **收魂双轨**：tmwd-bridge + agent-browser 互补搜索
- **markitdown 集成**：收魂后自动转换 PDF/音视频/PPT 为 Markdown

### 魂魄更新

- 金魂：列宁、毛泽东、邓小平、费曼（有限金魂）、鲁迅、稻盛和夫、波伏娃（条件金魂）、伊本赫勒敦（观察期）、法农、未明子
- 银魂：Karpathy、黄仁勋
- 紫魂：马斯克、罗永浩、乔布斯
- 蓝魂：海绵宝宝

---

## v2.2 (2026-04-30)

- 自检优化：描述触发、文件结构、英文版同步

## v2.1 (2026-04-29)

- 四种附体模式 + 反馈闭环 + 有效性评分
- 合议模式两阶段执行修复
- Obsidian 存档集成

## v2.0 (2026-04-28)

- 六阶品级体系（白/绿/蓝/紫/银/金）
- 幡主审查机制 + 独立审查机制
- 九魂档案首次上传

## v1.0 (2026-04-27)

- 万魂幡：知识与思维模式的自动调度系统
- 收魂 → 炼化 → 审查 → 入幡基本流程
