# 自动附体机制详解

## 执行流程

```
主agent收到任务
  → 判断需要 spawn sub-agent
  → 读取 registry.yaml
  → 遍历每个魂的 trigger，计算匹配度
  → 最高匹配度 ≥ 70？
      → 是：读取该魂 souls/{name}.yaml
            → 检查 artifacts 中 Skill 是否已安装
            → 将 summon_prompt 拼接至 sub-agent task 前缀
            → sessions_spawn 执行
      → 否：不附体，正常 spawn sub-agent
```

## 触发条件结构（trigger 字段）

```yaml
trigger:
  keywords: ["关键词1", "关键词2", ...]     # 直接关键词匹配
  domains: ["领域1", "领域2"]              # 领域匹配
  scenarios:                               # 场景描述（语义匹配）
    - "需要从本质分析复杂系统"
    - "做高风险决策评估"
  exclude: ["不触发的场景关键词"]            # 排除条件
```

**触发条件生成规则**：
- `keywords`：从素材中提取高频核心词 + 专业术语
- `domains`：直接复用 `domain` 字段
- `scenarios`：从素材中提炼该人物最擅长的 3-5 类场景
- `exclude`：明确不适用该魂的场景

## 匹配度评分公式

```
匹配度 = keywords命中数/总keywords × 30
       + domains命中数/总domains × 25
       + scenarios语义相似度 × 35
       + 品级加成(白+0, 绿+2, 蓝+5, 紫+8, 金+12)
       - exclude命中 × 30
```

- **品级加成**：品级越高，同等匹配度下优先级越高
- **exclude惩罚**：触发排除条件直接扣 30 分

## 决策阈值

| 匹配度 | 行为 |
|--------|------|
| ≥ 70 | 自动注入 sub-agent task 前缀 |
| 50-69 | 不注入，主agent可选择手动指定 |
| < 50 | 不触发 |

若多个魂匹配度 ≥ 70，取最高分者附体。

## 手动指定

用户显式要求使用某个魂时（`用<人物名>来<任务>`），跳过自动匹配，直接注入指定魂魄。
