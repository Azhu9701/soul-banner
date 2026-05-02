# 万魂幡 Soul Banner

[English](README.md) | [中文](README_zh.md)

> *"The banner stirs, and souls arrive. Choose a soul by the task, choose a task by the soul. The banner-master wields the banner; no soul oversteps its boundary."*

A **knowledge and thinking-pattern orchestration system**. Collect thinking materials from influential figures, structure them into "soul profiles," and deploy them through four possession modes — with a banner-master preventing dogmatic misapplication.

---

## Artifact Components

| File | Description |
|------|-------------|
| `SKILL.md` | Core skill documentation |
| `soul-profile-format.md` | Soul profile YAML spec & 6-tier grade system |
| `auto-possess.md` | 4 possession modes + matching formula + feedback loop |
| `registry-template.yaml` | Initial registry template |
| `souls/` | Refined soul profiles (includes SpongeBob sample) |
| `reviews/` | Review reports directory |
| `references/马斯克.yaml` | Full purple-soul reference example |
| `refine.py` | Soul refinement helper script |
| `scripts/` | Search, discipline, audit tool scripts |

---

## Quick Start

1. Copy `registry-template.yaml` → `registry.yaml`
2. Create `raw/` directory
3. **Capture**: `收魂 {name}` — web search to collect materials
4. **Refine**: `炼化 {name}` — generate soul profile YAML
5. **Review**: `审查 {name}` — banner-master independent review
6. **Possess**: `用{name}来{task}` / `合议 {task}` / `辩论 {topic}` / `接力 {task}`

The repo ships with `souls/海绵宝宝.yaml` as a sample soul demonstrating the full YAML format. `references/马斯克.yaml` provides a purple-soul format reference.

---

## Grade System (6 Tiers)

| Grade | Symbol | Criteria |
|-------|--------|----------|
| Gold | 🟡 | Independent worldview + directional judgment + institutional self-critique |
| Silver | 🥈 | Top practitioner, replicable methodology, lacks independent worldview |
| Purple | 🟣 | Rich materials, clear methodology, talent-dependent |
| Blue | 🔵 | Sufficient materials, complete skill chain |
| Green | 🟢 | Moderate materials, 1-2 skills |
| White | ⚪ | Scarce materials, public-info simulation only |

---

## Four Possession Modes

| Mode | Trigger | Best for | Flow |
|------|---------|----------|------|
| **Single** | Auto-match | Routine single-domain tasks | Match→Review→Inject→Execute |
| **Council** | `council {task}` | Complex cross-domain decisions | Multi-soul parallel→Banner-master synthesis |
| **Debate** | `debate {topic} A vs B` | Dilemmas, either-or choices | Two souls debate→Banner-master ruling |
| **Chain** | `chain {task} A→B→C` | Multi-stage sequential work | Output of A→input to B→...→final review |
| **Study** | `study {soulA} vs {soulB}` | Dialectical literacy training | Two souls cross-read→cross-review→banner-master learns |

All modes pass through the banner-master review. A **feedback loop** records effectiveness after each possession.

---

## Banner-Master

A spawned gold-soul sub-agent serving as the system's quality control. Injected via `summon_prompt` for independent perspective — not played by the main agent.

- **Pre-possession review**: Does the soul's boundary cover this task?
- **New soul entry review**: Independent sub-agent grade and boundary review (8 mandatory sections)
- **Dialectical synthesis**: In council/debate/chain — find consensus, divergence, blind spots, principal contradiction, action plan

The banner-master role is configurable — choose your most trusted reviewing soul. The system supports a dual-review mechanism (second reviewer triggers when the primary recommends themselves).

---

## Free & Open

All core features run at **zero extra cost** — no paid APIs required.

| Function | Free Tool |
|----------|-----------|
| Soul Capture (Search) | WebSearch + WebFetch (built-in) or tmwd-bridge (open source) |
| Format Conversion | markitdown (MIT) |
| AI-Pattern Removal | humanizer (pure LLM, no external API) |
| Knowledge Graph | graphify (optional, pure LLM) |
| Maintenance Loops | loop (built-in) |

See [免费使用指南](SKILL.md#免费使用指南) in SKILL.md for details.

---

## Installation & Usage

1. Clone into your Claude Code skills directory
2. Copy `registry-template.yaml` → `registry.yaml`
3. Create `raw/` directory (for collected materials)
4. Optional env vars: `OBSIDIAN_VAULT` (archive path), `SOUL_BANNER_HOME` (install path)
5. `Capture {name}` — collect materials
6. `Refine {name}` — generate soul profile
7. `Review {name}` — banner-master independent review
8. `Council {task}` / `Debate {topic}` / `Chain {task}` — four modes

---

*"The banner stirs. Souls choose their own tasks and attach. The banner-master wields the banner; no soul oversteps its boundary."*
