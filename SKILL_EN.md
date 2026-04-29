---
name: soul-banner
description: A knowledge and thinking-pattern orchestration system. Collect thinking materials from influential figures (Soul Capture), structure them into soul profiles (Soul Refine), and auto-match souls to possess sub-agents when tasks arrive (Auto-Possess). Trigger words include: capture, refine, what souls are in the banner, release soul, upgrade soul, use [figure] to [task]. Also used for any scenario involving domain-expert thinking simulation, cross-boundary analysis, high-risk decision assessment, or first-principles analysis — the Soul Banner auto-senses tasks and matches the best soul.
---

# Soul Banner (万魂幡)

> *"The banner stirs, and souls arrive unsummoned. Choose a soul by the task, choose a task by the soul. When the task comes, the soul attaches. When the task ends, the soul returns."*

## Overview

The Soul Banner is a **knowledge and thinking-pattern orchestration system**:

- **Capture**: Web search + user contribution — collect multi-dimensional materials on target figures
- **Refine**: Structure raw materials into Soul Profile YAML, assign a grade
- **Auto-Possess**: When the main agent prepares to spawn a sub-agent, auto-scan and match the best soul to inject
- **Manage**: View grades, upgrade souls, release souls

---

## Trigger Words

| Trigger | Function |
|---------|----------|
| `Capture {name}` | Start soul capture (8-dimension web search + optional user material) |
| `Refine {name}` | Refine raw materials into a Soul Profile |
| `What souls are in the banner` | View list of refined souls |
| `Release {name}` | Delete soul profile (keep raw materials) |
| `Upgrade {name}` | Re-refine with new materials |
| `Use {name} to {task}` | Manually specify a soul for a task |

---

## File Structure

```
Project Root/
├── registry.yaml          # Soul registry (runtime data)
├── souls/{name}.yaml      # Refined soul profiles (runtime data)
└── raw/{name}/            # Raw capture materials (runtime data)
```

Initialize by copying `assets/registry.yaml` to `registry.yaml` on first use.

---

## Soul Capture

1. Create `raw/{name}/` directory
2. Web search across 8 dimensions: core thinking framework, decision patterns, management style, tech vision, communication style, work methods, representative quotes, controversy materials
3. User may provide additional materials → `raw/{name}/user_contribution.md`
4. Save as `raw/{name}/search_materials.md`
5. Evaluate material sufficiency, supplement if lacking

## Soul Refine

1. Read all materials under `raw/{name}/`
2. Structured extraction: identity, core thinking, decision patterns, expression style, expertise, representative cases
3. Assign grade → match bindable Skills → generate `souls/{name}.yaml` → update `registry.yaml`

Helper: `python3 scripts/refine.py --input raw/{name}/search_materials.md`

> Grade system, scoring formula, and YAML format: see **[references/soul-profile-format.md](references/soul-profile-format.md)**

### Gold Soul Review

If a Gold soul exists in the banner, all newly refined souls must pass a **theoretical review** by the Gold soul before entering:

- Gold soul examines whether the new soul's methodology is internally coherent
- Gold soul annotates the new soul's applicable boundaries and potential biases
- Gold soul adds a `gold_review` field in the registry

This is not hierarchical suppression — the Gold soul review ensures **quality reliability and boundary clarity** for all souls. After review, Gold and other souls collaborate as equals.

## Auto-Possess

When the main agent prepares to spawn a sub-agent:

1. Read `registry.yaml`, iterate over each soul's `trigger`, compute match score
2. Match ≥ 70 → auto-inject `summon_prompt` into sub-agent task prefix
3. Multiple matches ≥ 70 → take the highest score; no match → no possession
4. If a Gold soul is online, Gold soul performs **final confirmation** on the match result

> Match scoring formula, decision thresholds, and trigger design: see **[references/auto-possess.md](references/auto-possess.md)**

## Correction & Evolution

After each soul execution:

1. Update `summoned_count`
2. Record actual effectiveness and user feedback
3. If 3 consecutive possessions underperform, trigger **soul correction** — re-examine trigger conditions and methodology applicability
4. Gold soul periodically (every 5 new souls or every month) conducts a **dialectical analysis** of all souls

> Souls are not static archives. Revolutionary thinking is forged in practice. Your souls need practice too.

---

## Banner Master's Notes

You are not an external scheduler standing outside theory. After each soul possession, reflect:

- **Why** was this soul's method suitable for this task?
- What are its **limitations**? Which judgments were the soul's biases?
- If a different soul handled the same task, how would the conclusion differ?

The ultimate goal is not to own more souls — it's to **internalize the Soul Banner's pluralistic thinking into your own theoretical literacy**. The banner's final purpose is for you to no longer need the banner.

---

## Management

- **View**: Read `registry.yaml`, list soul names, grades, domains, summon counts
- **Release**: Delete `souls/{name}.yaml`, update `registry.yaml`, keep `raw/` materials
- **Upgrade**: Re-capture → Re-refine → Overwrite original profile

---

## Refinement Helper Script

```bash
python3 scripts/refine.py --input raw/{name}/search_materials.md
python3 scripts/refine.py --input raw/{name}/search_materials.md -o souls/{name}.yaml
```

Provides: word count stats, domain identification, methodology keyword matching, skill recommendations, style characteristic recognition, grade scoring.

---

## References

- **[Soul Profile Format & Grade System](references/soul-profile-format.md)** — YAML template, scoring formula, five-grade system
- **[Auto-Possess Mechanism](references/auto-possess.md)** — Match scoring, decision thresholds, trigger design
- **[Musk Soul Example](references/马斯克.yaml)** — Complete Purple soul reference (🟣)

---

*"The banner stirs once. Souls choose their own tasks and attach. The banner-bearer simply walks the path — the ten thousand souls within will find their moment."*
