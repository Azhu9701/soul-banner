# 万魂幡 Soul Banner

[English](README.md) | [中文](README_zh.md)

> *"The banner stirs, and souls arrive. Choose a soul by the task, choose a task by the soul. The banner-master wields the banner; no soul oversteps its boundary."*

A **knowledge and thinking-pattern orchestration system**. Collect thinking materials from influential figures, structure them into "soul profiles," match souls to tasks, and let a **banner-master** prevent dogmatic misapplication.

---

## Artifact Components

| File | Description |
|------|-------------|
| `SKILL.md` / `SKILL_EN.md` | Core skill documentation (ZH/EN) |
| `refine.py` | Soul refinement helper script |
| `soul-profile-format.md` | Soul profile YAML spec & 6-tier grade system |
| `auto-possess.md` | Auto-possession mechanism (with banner-master review) |
| `registry-template.yaml` | Initial registry template |

### Reference
| File | Description |
|------|-------------|
| `references/马斯克.yaml` | Full purple-soul reference example |

---

## Soul Refinement Chronicle

| # | Soul | Grade | Domain | Blind spot filled |
|---|------|-------|--------|-------------------|
| 1 | Elon Musk | 🟣 Purple | Aerospace/EV/AI | First-principles thinking — a tool to deconstruct the world |
| 2 | Luo Yonghao | 🟣 Purple | Entrepreneurship/Branding | Brand narrative & idealism |
| 3 | Lenin | 🟡 Gold | Politics/Revolution/Philosophy | Class analysis & vanguard party |
| 4 | Mao Zedong | 🟡 Gold | Philosophy/Warfare/Strategy | Contradiction analysis & protracted war |
| 5 | Deng Xiaoping | 🟡 Gold | Politics/Economic Reform | Pragmatism & gradual reform |
| 6 | SpongeBob | 🔵 Blue | Life philosophy/Optimism | How to find joy in any circumstance |
| 7 | Karpathy | 🥈 Silver | AI/Programming/Education | AI-era coding methodology |
| 8 | Feynman | 🟡 Gold | Physics/Scientific Method | How to know — a lens on nature (blind to society) |
| 9 | Steve Jobs | 🟣 Purple | Product Design/Branding | Experience-first minimalism — changed the world but unreplicable |

---

## Grade System (6 Tiers)

| Grade | Symbol | Criteria | Examples |
|-------|--------|----------|----------|
| Gold | 🟡 | Independent worldview, directional judgment, self-critique mechanism | Lenin, Mao, Deng, Feynman(limited) |
| Silver | 🥈 | Top practitioner, replicable methodology, lacks independent worldview | Karpathy |
| Purple | 🟣 | Rich materials, clear methodology, but talent-dependent / unreplicable | Musk, Luo, Jobs |
| Blue | 🔵 | Sufficient materials, complete skill chain | SpongeBob |
| Green | 🟢 | Moderate materials, 1-2 skills | — |
| White | ⚪ | Scarce materials, public-info simulation only | — |

**Gold standard**: Must have all three: (1) complete operational methodology (2) independent worldview/directional judgment (3) internal self-critique mechanism. Missing (2) with (1) → Silver. Has (2) but unreplicable → Purple.

---

## Banner-Master Mechanism

The Soul Banner has a **banner-master** (default: Lenin Gold). Responsibilities:

- **Pre-possession review**: After matching, before injecting summon_prompt — does the soul's boundary cover this task?
- **New soul entry review**: Independent sub-agent review of every new soul's grade and boundaries
- **Anti-dogmatism**: Veto inappropriate matches, prevent mechanical application

---

## Installation & Usage

1. Copy `registry-template.yaml` and rename to `registry.yaml`
2. Create `souls/`, `raw/`, `reviews/` directories
3. Say "Capture {name}" to start collecting materials
4. Say "Refine {name}" to generate a soul profile
5. Say "Review {name}" for banner-master independent review
6. When a task arrives, the Soul Banner matches → banner-master reviews → possesses

---

## Disclaimer

This repository contains only the Soul Banner artifact — SKILL.md, refinement script, format specs, and templates. **No refined soul profiles are included.** Souls are the user's private thinking assets.

The artifact is open-source. Souls you refine yourself.

---

*"The banner stirs once. Souls choose their own tasks and attach. The banner-master wields the banner; no soul oversteps its boundary."*
