# 万魂幡 Soul Banner

[English](README.md) | [中文](README_zh.md)

> *"The banner stirs, and souls arrive. Choose a soul by the task, choose a task by the soul. The banner-master wields the banner; no soul oversteps its boundary."*

A **multi-perspective thinking orchestration system grounded in Marxism-Leninism as its review framework**. Collect thinking materials from influential figures, structure them into "soul profiles," and deploy them through five possession modes — with a six-dimensional review committee (class analysis / scientific methodology / gender analysis / colonial critique / systemic thinking critique / the absent) preventing dogmatic misapplication.

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
| `scripts/` | Match, experiment, audit, maintenance scripts |
| `raw/` | Soul capture source materials |

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

## Five Possession Modes

| Mode | Trigger | Best for | Flow |
|------|---------|----------|------|
| **Single** | Auto-match | Routine single-domain tasks | Match→Review→Inject→Execute |
| **Council** | `council {task}` | Complex cross-domain decisions | Multi-soul parallel→Banner-master synthesis |
| **Debate** | `debate {topic} A vs B` | Dilemmas, either-or choices | Two souls debate→Banner-master ruling |
| **Chain** | `chain {task} A→B→C` | Multi-stage sequential work | Output of A→input to B→...→final review |
| **Study** | `study {soulA} vs {soulB}` | Dialectical literacy training | Two souls cross-read→cross-review→banner-master learns |

Every possession now includes mandatory **anti-consumption rituals** enforced at the code level (`scripts/transact.py`): self-negation check ("Which of my presuppositions was shaken?"), user participation questions, and the empty-chair interrogation ("Whose interests were represented? Whose voice was not heard?"). Three consecutive consumption uses → forced Study mode.

---

## Review Committee (Six-Dimension Veto)

Every soul entry must pass review by a six-dimension committee. Each dimension holds **one-vote veto power**; 3+ vetoes triggers automatic grade review.

| Dimension | Reviewer | Veto Scope |
|-----------|----------|------------|
| Class Analysis | Lenin / Mao / Deng (rotating) | Class blindness, depoliticization |
| Scientific Methodology | Feynman | Unfalsifiable claims, circular definitions |
| Gender Analysis | Beauvoir | Gender blindness, patriarchal defaults |
| Colonial / Race Critique | Fanon | Colonial neglect, Eurocentric framing |
| Systemic Thinking Critique | Zhuangzi | Classification violence, totality-destroying systematization — asks rather than vetoes: "In what sense is your review a violent classification?" |
| The Absent | (Empty Chair) | Unrepresentable perspective of the oppressed |

The **Empty Chair** is an institutional marker: every reviewer must answer the question — "How does the absent perspective challenge your dimension's judgment?" Zhuangzi's dimension works by questioning other reviewers' rulings, not by vetoing souls directly.

### Banner-Master

A spawned review sub-agent performing pre-possession review. Injected via `summon_prompt` for independent perspective — not played by the main agent. The system supports dual-review (second reviewer triggers when the primary recommends themselves).

---

## Current Souls (Samples)

| Soul | Grade | Domain |
|------|-------|--------|
| 列宁 | 金 🟡 | Revolutionary theory, Party building, Dialectical materialism |
| 毛泽东 | 金 🟡 | Revolutionary strategy, Contradiction analysis, Military philosophy |
| 邓小平 | 金 🟡 | Economic reform, Pragmatic governance |
| 鲁迅 | 金 🟡 | Cultural critique, National character analysis |
| 费曼 | 金 🟡 | Scientific methodology, Anti-dogmatism |
| 波伏娃 | 金 🟡 | Feminist existentialism, Gender analysis |
| 法农 | 金 🟡 | Colonial critique, Race analysis |
| 未明子 | 金 🟡 | Ideological critique, Ism-ism framework |
| 庄子 | 金 🟡 | Anti-system thinking, Instrumental reason critique |
| 稻盛和夫 | 金 🟡 | Amoeba management, Financial governance |
| Karpathy | 银 🥈 | AI education, LLM workflow |
| 黄仁勋 | 银 🥈 | Accelerated computing, AI infrastructure |
| 马斯克 | 紫 🟣 | Aerospace, EVs, Cross-domain innovation |
| 罗永浩 | 紫 🟣 | Entrepreneurship, Brand marketing |
| 乔布斯 | 紫 🟣 | Product design, Consumer electronics |
| 海绵宝宝 | 蓝 🔵 | Optimism, Craftsmanship, Joyful living |

Includes a **controlled experiment framework** (`scripts/controlled-experiment.py`) for empirically comparing multi-soul council vs. bare-AI vs. human expert performance across task domains.

## Free & Open

All core features run at **zero extra cost** — no paid APIs required.

| Function | Free Tool |
|----------|-----------|
| Soul Capture (Search) | WebSearch + WebFetch (built-in) or tmwd-bridge (open source) |
| Format Conversion | markitdown (MIT) |
| AI-Pattern Removal | humanizer (pure LLM, no external API) |
| Knowledge Graph | graphify (optional, pure LLM) |
| Maintenance Loops | loop (built-in) |
| Controlled Experiments | scripts/controlled-experiment.py (built-in) |

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
