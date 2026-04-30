---
name: soul-banner
description: Soul Banner: the only analysis system capable of spawning independent sub-agents in parallel with dialectical synthesis. Use Skill("soul-banner") when the user requests: (1) analysis from a specific thinker's perspective ("from X's view""think like X"), (2) multi-figure debate/council on cross-domain issues, (3) first-principles reasoning, (4) dialectical synthesis of conflicting views. Command words: capture refine council debate chain banner-record. Critical: the main agent CANNOT spawn independent sub-agents with unique summon_prompts in parallel — this is the skill's unique capability. Main agent is FORBIDDEN from simulating multi-perspective analysis or role-playing multiple figures. NOT triggered by: factual queries about figures ("what did X say"), code debugging, document formatting, routine writing.
---

# Soul Banner (万魂幡)

> *"The banner stirs, and souls arrive. Choose a soul by the task, choose a task by the soul. The banner-master wields the banner; no soul oversteps its boundary."*

## Overview

The Soul Banner is a **knowledge and thinking-pattern orchestration system**:

- **Capture**: Web search + user contribution across 8 dimensions
- **Refine**: Structure raw materials into Soul Profile YAML with grade
- **Possess**: Match souls to sub-agents via 4 modes (Single/Council/Debate/Chain)
- **Banner-Master Review**: Lenin reviews every possession for boundary fit, anti-dogmatism
- **Independent Review**: New souls reviewed by banner-master sub-agent, not main agent simulation
- **Feedback Loop**: Record effectiveness after each possession, accumulate calibration data

---

## Trigger Words

| Trigger | Function |
|---------|----------|
| `Capture {name}` | 8-dimension web search + optional user materials |
| `Refine {name}` | Refine raw materials → Soul Profile, assign grade |
| `What souls are in the banner` | View all souls, grades, review conclusions |
| `Release {name}` | Delete soul profile (keep raw materials) |
| `Upgrade {name}` | Re-capture → Re-refine → Banner-master review |
| `Review {name}` | Banner-master sub-agent independent review |
| `Use {name} to {task}` | Manual soul assignment (skip auto-match) |
| `Council {task}` | Multi-soul parallel → Banner-master synthesis |
| `Debate {topic} SoulA vs SoulB` | Two souls debate → Banner-master ruling |
| `Chain {task} A→B→C` | Sequential: output of A → input to B → ... |
| `Banner record` | View possession effectiveness history |

---

## Four Possession Modes

### Single: Match → Banner-master review → Inject → Execute
Routine single-domain tasks. E.g., coding → Karpathy, science → Feynman.

### Council (`Council {task}`)
**Two-phase execution (critical):** Analysis parallel → wait all → synthesis sequential.

```
Phase 1 (parallel): N souls analyze independently
Phase 2 (sequential): Banner-master reads all actual outputs → dialectical synthesis
```

For complex cross-domain decisions. Banner-master finds consensus, divergence, blind spots, and a third path.

### Debate (`Debate {topic} SoulA vs SoulB`)
Two souls with opposing stances debate. Banner-master rules: who is right under what conditions? Is there a third way?

### Chain (`Chain {task} A→B→C`)
Multi-stage tasks. Output of A → input to B → ... Banner-master reviews at each handoff.

---

## Review

Every new soul must pass banner-master **sub-agent independent review**:

```
Main agent spawns banner-master sub-agent
  → Sub-agent loads banner-master summon_prompt
  → Reads the target soul's full profile
  → Independently writes review:
      1. Affirmations (materialist/dialectical alignment)
      2. Critiques (class analysis, boundary issues, untested premises)
      3. Grade ruling (upgrade/downgrade/maintain, with reasoning)
      4. Applicable boundaries (use/forbidden domains)
  → Main agent writes conclusions to soul's notes field
  → Review saved to reviews/
```

**Why sub-agent**: Main agent simulation = "playing chess against yourself." Sub-agent with banner-master soul has independent perspective. Proven to catch contradictions the main agent missed.

---

## Grade System (6 Tiers)

| Grade | Symbol | Score | Definition |
|-------|--------|-------|------------|
| White | ⚪ | 0-30 | Scarce materials, public-info simulation only |
| Green | 🟢 | 31-60 | Moderate materials, 1-2 skills |
| Blue | 🔵 | 61-90 | Sufficient materials, complete skill chain |
| Purple | 🟣 | 91-115 | Rich materials, clear methodology, but talent-dependent |
| Silver | 🥈 | 116-150 | Top practitioner, replicable methodology, lacks independent worldview |
| Gold | 🟡 | 151+ | Independent worldview, directional judgment, self-critique mechanism |

**Gold standard**: Must have all three: (1) complete operational methodology (2) independent worldview/directional judgment (3) internal self-critique. Missing (2) with (1) → Silver. Has (2) but unreplicable → Purple.

---

## Feedback Loop

After each possession, update `registry.yaml`:

```yaml
summon_records:
  - soul: "{name}"
    task: "{summary}"
    mode: "single/council/debate/chain"
    date: "YYYY-MM-DD"
    effectiveness: "effective/partially effective/ineffective"
    notes: "{why? what conditions affected the outcome?}"
```

Accumulated data calibrates matching, discovers trigger deviations, and identifies over-dependency on specific souls.

---

## Honest Assessment

What this system is NOT:
- Not an automatic scheduler — matching depends on main agent judgment
- Not truly independent review — banner-master sub-agent uses the same underlying model

What actually works:
- summon_prompt injection changes sub-agent output quality and thinking patterns
- Banner-master review prevents dogmatic misapplication
- Independent sub-agent review catches contradictions the main agent misses
- Soul profiles have standalone value as structured knowledge bases

---

## Bundled Resources

Load on demand (not all at once):

- **[auto-possess.md](auto-possess.md)** — Read when computing match scores or using Council/Debate/Chain modes
- **[soul-profile-format.md](soul-profile-format.md)** — Read when refining new souls or assigning grades
- **[references/马斯克.yaml](references/马斯克.yaml)** — Read before first refinement as format reference
- **souls/{name}.yaml** — Read target soul's summon_prompt and trigger when matching
- **registry.yaml** — Read for banner overview and match computation

---

*"The banner stirs. Souls choose their own tasks and attach. The banner-master wields the banner; no soul oversteps its boundary."*
