# 万民幡 &middot; Wanmin Banner

> *「幡动魂自至。以幡择魂，以魂择事，事至则魂附，事毕则魂归。」*

**A Marxist-Leninist review-framework multi-perspective thinking system.**

This is the full edition of Wanmin Banner — a Claude Code skill that spawns independent AI agents embodying distinct thinkers, with a structured review committee, grade system, and five modes of "possession" (附体).

For a simpler entry point, see **[soul-banner-lite](https://github.com/Azhu9701/soul-banner-lite)**.

---

## What It Does

Wanmin Banner is a **knowledge and thinking-mode orchestration system**. It:

1. **Collects** thinkers ("souls") through web research and distills their methodologies into structured profiles
2. **Reviews** each soul through a committee framework (class analysis, scientific methodology, gender analysis, colonial critique, systemic thinking critique, absent voices — each with veto power)
3. **Deploys** souls in parallel to analyze problems from multiple perspectives simultaneously
4. **Archives** all outputs to Obsidian for long-term reference

---

## Modes of Operation

| Mode | Use Case | Execution |
|------|----------|-----------|
| **Single Soul** (单魂附体) | Single-domain, clear objective | Match → Review → Spawn |
| **Conference** (合议) | Cross-domain complex decisions | Parallel analysis → Dialectical synthesis |
| **Debate** (辩论) | Binary dilemmas | Two opposing arguments → Banner-master ruling |
| **Relay** (接力) | Multi-stage sequential work | Output of A → Input of B → Input of C |
| **Study** (学习) | Training dialectical literacy | Two opposing souls read + review each other |

---

## Grade System

| Grade | Symbol | Criteria |
|-------|--------|----------|
| White (白魂) | ⚪ | Sparse material, prompt simulation |
| Green (绿魂) | 🟢 | Moderate material, prompt + 1-2 skills |
| Blue (蓝魂) | 🔵 | Sufficient material, skill chains |
| Purple (紫魂) | 🟣 | Clear methodology, talent-dependent (not replicable) |
| Silver (银魂) | 🥈 | Complete replicable methodology, no independent worldview |
| Gold (金魂) | 🟡 | Independent worldview + methodology + self-correction |

---

## Review Committee (Six-Dimension Veto System)

Since 2026-05-02, the review committee consists of six dimensions, each with veto power:

1. **Class Analysis** (阶级分析) — Lenin
2. **Scientific Methodology** (科学方法论) — Feynman
3. **Gender Analysis** (性别分析) — Beauvoir
4. **Colonial Critique** (殖民批判) — Fanon
5. **Systemic Thinking Critique** (系统性思维批判) — Zhuangzi (operates by questioning, not direct veto)
6. **Absent Voices** (缺席者) — Rotating chair

---

## Core Pipeline

```
Soul Collection (收魂) → Refinement (炼化) → Review (审查) → Registry
                                                          ↓
Task arrives → Match → Banner-master Review → Spawn Souls → Dialectical Synthesis → Archive
```

The **host agent is a pure coordinator**. It spawns, collects, and archives. All thinking — including the banner-master's — happens through spawned sub-agents.

---

## File Structure

```
soul-banner/
├── SKILL.md                    # Skill documentation (loaded by system)
├── CLAUDE.md                   # Persistent instructions layer
├── auto-possess.md             # Possession mechanics (5 modes + review sections)
├── soul-profile-format.md      # Grade standards + gold soul criteria
├── registry.yaml               # Soul registry (runtime data)
├── refine.py                   # Refinement helper (validate_soul, sync to Obsidian)
├── scripts/
│   ├── soul-search.py          # Web research (multi-engine + media link detection)
│   ├── match.py                # Soul matching pre-screening
│   ├── sync-agent.py           # Generate Claude Code agent files
│   ├── transact.py             # Transaction script (possession-close, review-apply, etc.)
│   ├── cross-validate.py       # Three-way cross-validation
│   ├── registry-health-check.py
│   ├── prompt-audit.py         # Audit logging
│   └── maintenance-loop.sh     # Automated maintenance
├── souls/{Name}.yaml            # Refined soul profiles
├── reviews/                     # Review reports
├── raw/{Name}/                  # Raw research materials
└── agents/                      # Custom agent definitions
```

---

## Key Rules

- The host agent must **never** simulate or role-play multiple perspectives
- Soul outputs must be **archived verbatim** — no rewriting, no summarizing
- `summon_prompt` is the **irreducible core** of each soul — never cut or paraphrase
- Every possession must go through **banner-master review** via spawned sub-agent

---

## Anti-Consumption Mechanisms

- **Self-Negation Check** (自我否定): After each session, the user must name at least one prior assumption that was challenged. 3 consecutive failures → mandatory study mode.
- **Empty Chair Question** (空椅子拷问): "Whose interests were represented? Whose voice was not given?"
- **Consumption Tracking**: All sessions rated as learning vs. consumption use

---

## Why "Wanmin Banner"?

Originally 万魂幡 ("Banner of Ten Thousand Souls"). One character changed — 魂 (soul) → 民 (people). The banner belongs to the people, not a sorcerer.

---

## Related Repos

- **[soul-banner-lite](https://github.com/Azhu9701/soul-banner-lite)** — Anti-consumption edition. Self-negation + empty chair + 3x consumption lockout. No review committee. Just spawn, read, judge.
- **[soul-banner-pro](https://github.com/Azhu9701/soul-banner-pro)** — Archived full edition snapshot.

---

## Install

1. Copy to `~/.claude/skills/soul-banner/`
2. Run `python3 scripts/sync-agent.py --all`
3. Restart Claude Code
4. Start with `/召唤 your question SoulA SoulB`

**Prerequisite**: [Claude Code](https://claude.ai/code). Zero additional cost.

---

*「幡动魂自至。以幡择魂，以魂择事，事至则魂附，事毕则魂归。幡主持幡，魂不越界。」*
