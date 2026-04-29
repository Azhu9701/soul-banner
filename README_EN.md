# 万魂幡 Soul Banner

[中文](README.md) | [English](README_EN.md)

> *"The banner stirs, and souls arrive unsummoned. Choose a soul by the task, choose a task by the soul. When the task comes, the soul attaches. When the task ends, the soul returns."*

A **knowledge and thinking-pattern orchestration system**. Collect thinking materials from influential figures, structure them into "soul profiles," and automatically match the best soul to possess sub-agents for any given task.

---

## Artifact Components

| File | Description |
|------|-------------|
| `SKILL.md` | Core skill documentation |
| `refine.py` | Soul refinement helper script |
| `soul-profile-format.md` | Soul profile YAML spec & grade system |
| `auto-possess.md` | Auto-possession mechanism |
| `registry-template.yaml` | Initial registry template |

---

## Soul Refinement Chronicle

> The first refining session of the Soul Banner was itself an arc of thought experiments. The sequence below documents the real order of soul capture — and what it reveals.

| # | Choice | Grade | What the user was seeking | Blind spot this soul filled |
|---|--------|-------|--------------------------|---------------------------|
| 1 | Elon Musk | 🟣 Purple | "How do I reason from first principles?" | First-principles thinking — a tool to deconstruct the world |
| 2 | Luo Yonghao | 🟣 Purple | "How do you do things right, with integrity?" | Ethics & narrative — finding a decent path between idealism and reality |
| 3 | Lenin | 🟡 Gold | "How is an organization forged?" | Class analysis & vanguard party — thinking alone is not enough |
| 4 | Mao Zedong | 🟡 Gold | "How does the weak side win?" | Contradiction analysis & protracted war — a complete strategic framework |
| 5 | Deng Xiaoping | 🟡 Gold | "How do you get things done in the mud?" | Practice-first pragmatism — market-economy methodology |
| 6 | SpongeBob SquarePants | 🔵 Blue | Not chosen by the refiner | **How to find joy in any circumstance** |

### A Spiral Arc

```
Tool → Ethics → Organization → Strategy → Execution → Living

Musk ──→ Luo ──→ Lenin ──→ Mao ──→ Deng ──→ SpongeBob
```

The first five souls cover the full spectrum of "fighting outward" — from deconstructing problems to organizing forces to strategic planning to pragmatic execution. Each filled the blind spot of the previous: Musk lacked class analysis, Luo lacked organizational capability, Lenin lacked a weak-against-strong strategic framework, Mao lacked a pragmatic market-economy path.

The sixth soul was chosen by someone else. While the refiner obsessively pursued "how to do things," she asked a question he never thought to ask: **"What is all this effort even for?"**

SpongeBob is the only soul in the Banner whose core competency is not "solving problems." He solves exactly one thing: whether all your problems are still unsolved, or all of them are already solved — **how do you first learn to live happily?**

### What the Banner Means

> It's not about which souls you chose. It's about the souls that thought of things you never would have.

Someone who lacks joy will never think to capture a joy soul — precisely because they lack it. This is the true value of the Soul Banner — **not reinforcing the direction you already have, but filling the blind spots you never knew you had.**

---

## Grade System

| Grade | Symbol | Criteria | Example |
|-------|--------|----------|---------|
| Gold | 🟡 | Independent, complete knowledge system; systematic methodology; high reusability | Lenin, Mao, Deng |
| Purple | 🟣 | Rich materials; clear methodology; multiple skill bindings | Musk, Luo Yonghao |
| Blue | 🔵 | Sufficient materials; complete skill chain; unique thinking pattern | SpongeBob |
| Green | 🟢 | Moderate materials; 1-2 matchable skills | — |
| White | ⚪ | Scarce materials; public-information simulation only | — |

---

## The Tri-Gold Governance

Within the Soul Banner, three gold souls form a structure of mutual checks:

```
        Mao Zedong (Thesis · Direction)
              /\
             /  \
            /    \
   Critique dogma   Warn against market class logic
          /            \
         /              \
   Deng Xiaoping —————— Lenin
  (Antithesis · Practice)  (Synthesis · Analysis)
```

- Mao ensures the flag stays red, Deng ensures bellies stay full, Lenin ensures brains stay clear
- Mao and Lenin ally on class questions; Deng and Lenin echo on anti-dogmatism
- Three gold souls balance each other — no single one dominates

---

## Installation & Usage

1. Copy `registry-template.yaml` to your project root and rename to `registry.yaml`
2. Create `souls/` and `raw/` directories
3. Say "Capture {name}" to start collecting materials
4. Say "Refine {name}" to generate a soul profile
5. When a task arrives, the Soul Banner auto-matches the best soul to possess

---

## Disclaimer

This repository contains only the Soul Banner artifact itself — SKILL.md, refinement script, format specs, and templates. **No refined soul profiles are included.** Souls are the user's private thinking assets and should not — will not — be uploaded.

The artifact is open-source. Souls you refine yourself.

---

*"The banner stirs once. Souls choose their own tasks and attach. The banner-bearer simply walks the path — the ten thousand souls within will find their moment."*
