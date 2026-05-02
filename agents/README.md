# Custom Agent 定义

此目录用于存放幡主/审查官/辩证综合官的自定义 agent 定义文件（`.md`，含 YAML frontmatter）。

Claude Code 重启后自动注册 `subagent_type`，spawn 时通过 `subagent_type="{agent名}"` 调用。

## 示例结构

```markdown
---
name: 我的审查官
description: 自定义审查用 agent
tools: Read, Grep, Glob, Bash
model: sonnet
---

你是万民幡的审查官。你的职责是...
```

## 使用方式

1. 创建 `agents/{名称}.md`
2. 重启 Claude Code
3. 在 spawn 时使用 `subagent_type="{名称}"`
