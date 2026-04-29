# 万魂幡 Soul Banner

[English](README.md) | [中文](README_zh.md)

> *"The banner stirs, and souls arrive. Choose a soul by the task, choose a task by the soul. The banner-master wields the banner; no soul oversteps its boundary."*

A **knowledge and thinking-pattern orchestration system**. Collect thinking materials from influential figures, structure them into "soul profiles," and deploy them through four possession modes — with a banner-master preventing dogmatic misapplication.

---

## Artifact Components

| File | Description |
|------|-------------|
| `SKILL.md` / `SKILL_EN.md` | Core skill documentation (ZH/EN) |
| `soul-profile-format.md` | Soul profile YAML spec & 6-tier grade system |
| `auto-possess.md` | 4 possession modes + matching formula + feedback loop |
| `registry-template.yaml` | Initial registry template |
| `souls/` | Refined soul profiles (9 souls) |
| `reviews/` | Banner-master review reports (9 reports) |
| `references/马斯克.yaml` | Full purple-soul reference example |
| `refine.py` | Soul refinement helper script |

---

## Nine Souls

| # | Soul | Grade | Domain | Blind spot filled |
|---|------|-------|--------|-------------------|
| 1 | Elon Musk | 🟣 Purple | Aerospace/EV/AI | First-principles — a tool to deconstruct |
| 2 | Luo Yonghao | 🟣 Purple | Entrepreneurship/Branding | Brand narrative & idealist tension |
| 3 | Lenin | 🟡 Gold | Politics/Revolution/Philosophy | Class analysis & vanguard party |
| 4 | Mao Zedong | 🟡 Gold | Philosophy/Warfare/Strategy | Contradiction analysis & protracted war |
| 5 | Deng Xiaoping | 🟡 Gold | Politics/Economic Reform | Pragmatism & gradual reform |
| 6 | SpongeBob | 🔵 Blue | Life philosophy/Optimism | Joy in any circumstance |
| 7 | Karpathy | 🥈 Silver | AI/Programming/Education | AI-era coding methodology |
| 8 | Feynman | 🟡 Gold(limited) | Physics/Scientific Method | How to know — lens on nature (blind to society) |
| 9 | Steve Jobs | 🟣 Purple | Product Design/Branding | Experience-first minimalism — unreplicable |

---

## Grade System (6 Tiers)

| Grade | Symbol | Criteria | Examples |
|-------|--------|----------|----------|
| Gold | 🟡 | Independent worldview + directional judgment + self-critique | Lenin, Mao, Deng, Feynman(limited) |
| Silver | 🥈 | Top practitioner, replicable methodology, lacks worldview | Karpathy |
| Purple | 🟣 | Rich materials, clear methodology, talent-dependent | Musk, Luo, Jobs |
| Blue | 🔵 | Sufficient materials, complete skill chain | SpongeBob |
| Green | 🟢 | Moderate materials, 1-2 skills | — |
| White | ⚪ | Scarce materials, public-info simulation only | — |

---

## Four Possession Modes

| Mode | Trigger | Best for | Flow |
|------|---------|----------|------|
| **Single** | Auto-match | Routine single-domain tasks | Match→Review→Inject→Execute |
| **Council** | `council {task}` | Complex cross-domain decisions | Multi-soul parallel→Banner-master synthesis |
| **Debate** | `debate {topic} A vs B` | Dilemmas, either-or choices | Two souls debate→Banner-master ruling |
| **Chain** | `chain {task} A→B→C` | Multi-stage sequential work | Output of A→input to B→...→final review |

All modes pass through the banner-master (Lenin). A **feedback loop** records effectiveness after each possession.

---

## Banner-Master

Default: Lenin (Gold). Responsibilities:

- **Pre-possession review**: Does the soul's boundary cover this task?
- **New soul entry review**: Independent sub-agent grade and boundary review
- **Dialectical synthesis**: In council/debate/chain — find consensus, divergence, blind spots, third paths

---

## Installation & Usage

1. Copy `registry-template.yaml` → `registry.yaml`
2. Create `souls/`, `raw/`, `reviews/` directories
3. `Capture {name}` — collect materials
4. `Refine {name}` — generate soul profile
5. `Review {name}` — banner-master independent review
6. `Council {task}` / `Debate {topic}` / `Chain {task}` — four modes

---

*"The banner stirs. Souls choose their own tasks and attach. The banner-master wields the banner; no soul oversteps its boundary."*
