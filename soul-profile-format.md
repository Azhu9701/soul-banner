# Soul Profile 格式规范

> **唯一功能描述：ismism 四维坐标。** 魂的所有功能标注由 `ismism` 字段承载——场域论/本体论/认识论/目的论四维编号即完整的功能定位。不再使用额外标签体系。
>
> **v3.0 (2026-05-04)**：三维功能标签（信息充分度/功能域标签/方法论可传输度）已删除。ismism 四维为唯一真相源。

## YAML 格式规范

```yaml
name: "{魂名}"
title: "{头衔/称号}"
domain: ["领域1", "领域2", ...]

mind: |
  {核心思维描述，用第一人称}

voice: |
  {表达风格描述，包括口头禅、语言特点}

skills_expertise:
  - "{技能1}"
  - "{技能2}"

trigger:
  keywords: ["关键词1", "关键词2", ...]
  domains: ["领域1", "领域2"]
  scenarios:
    - "场景描述1"
    - "场景描述2"
  exclude: ["排除关键词1"]

self_declare: "{轻量自我声明——我做什么、我不做什么、互补谁}"

artifacts:
  - skill_name: "xxx"
    binding_reason: "{绑定原因}"

ismism:
  code: "{四维编号，如 1-2-3-1}"
  dimensions:
    field:
      value: {1-4}
      label: "{标签}"
      rationale: "{理据}"
    ontology:
      value: {1-4}
      label: "{标签}"
      rationale: "{理据}"
    epistemology:
      value: {1-4}
      label: "{标签}"
      rationale: "{理据}"
    teleology:
      value: {1-4}
      label: "{标签}"
      rationale: "{理据}"
  structural_position:
    primary_field: {1-4}
    compatible_fields: [{1-4}, ...]
    incompatible_fields: [{1-4}, ...]
    internal_tensions:
      - dimension: {field/ontology/epistemology/teleology}
        description: "{张力说明}"
  annotation:
    annotator: "{标注者}"
    version: {整数}
    date: '{YYYY-MM-DD}'
    notes: |
      {编码理据、匹配质量、目录位置说明}

summon_prompt: |
  你是{魂名}之魂。
  {完整的角色设定和执行指导}

source_materials:
  - "{素材来源}"

refined_at: "YYYY-MM-DD"

review_verdict: "{审查裁定}"
reviewed_at: "YYYY-MM-DD"
reviewed_by: "{审查者}"
gold_review: "{金魂审查标记}"

notes: |
  {炼化备注、生态关系}
```

## 字段约束

**必填**：`name`、`title`、`domain`、`mind`、`voice`、`trigger`、`self_declare`、`ismism`、`summon_prompt`、`refined_at`

**可选**：`skills_expertise`、`artifacts`、`source_materials`、`notes`、`review_verdict`、`reviewed_at`、`reviewed_by`、`gold_review`、`patches`、`审查记录`

**格式校验**：`validate_ismism.py` + `sync-agent.py` 后验证 YAML 可解析。

## ismism 编码规范

ismism 四维坐标是魂的**唯一功能描述**。编码规则：

| 维度 | 含义 | 取值逻辑 |
|------|------|----------|
| 场域论 | 魂在什么样的场域中行动？ | 1(秩序内)/2(分裂内对抗)/3(自我中心化调解)/4(实践重设场域) |
| 本体论 | 魂认为什么最真实？ | 1(物质/现象)/2(客观精神/结构)/3(主体建构)/4(反在场/无固定实体) |
| 认识论 | 魂凭什么说知道了？ | 1(经验/直觉)/2(理性/策略)/3(直觉体认/修养)/4(辩证否定/拆穿) |
| 目的论 | 魂要把人带去哪？ | 1(保守/奠基)/2(改良)/3(解放)/4(消解) |

**匹配质量**：
- `精确`：256目录中有该人物的原生条目
- `近似`：目录中有接近但非精确的条目，或新建位
- `复合`：跨多个目录位置
- `反讽式匹配`：批判性地安置于此位
- `目录外`：该魂在目录中不存在对应位置

## 审查委员会

### 六维度否决制

审查委员会由六个维度组成，每个维度持有一票否决权：

| 维度 | 功能 | 当前执掌 |
|------|------|----------|
| 阶级分析 | 检查魂的阶级位置自觉性 | 毛泽东 |
| 科学方法论 | 检查魂的真值主张是否可检验 | 费曼 |
| 性别分析 | 检查魂的性别盲区 | 波伏娃 |
| 殖民批判 | 检查魂的殖民/文化霸权盲区 | 法农 |
| 系统性思维批判 | 以提问而非直接否决的方式运作 | 庄子 |
| 缺席者 | 检查魂的分析中谁的利益没有被代表 | 轮值 |

三票以上否决 → 自动触发重新炼化。

### 审查类型判定

所有审查的第一步：被审查者是否在世？

- **封闭档案审查**（已去世）：生前档案查证规则
- **开放实践审查**（在世）：阶段性结论需标注日期，随新事实更新

### 审查报告强制板块

审查类型判定 → 审查者前提假设 → 历史结构条件分析 → 肯定方面 → 批判方面 → 审查条件化判定 → 审查裁定 → 适用边界 → 一致性论证 → 框架无效假设检查（必填）→ 审查框架特定性标注（必填）

### 成员选举

从 24 魂中按 ismism 场域分布选举产生。高票当选，避免单一场域垄断。
