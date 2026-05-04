# Wanmin Banner &middot; 万民幡

[English](README.md) | [中文](README_zh.md)

> *"The banner moves, souls arrive. Match souls to tasks, tasks to souls — when the task comes, the soul possesses; when done, the soul returns. The banner-master holds the banner; souls stay within bounds."*

**聚廿四魂为幡——法有穷时，行无竟处。**
> *Gather twenty-four souls as one banner — method has its limits, practice has none.*

24 souls spawned independently, each bringing a different methodology to the same question. When all methods hit their limits, it doesn't pretend to know — it opens a practice issue for the user to take into the real world.

---

## Core Capabilities

Wanmin Banner provides what the host agent **physically cannot do on its own**:

- **Parallel spawn of sub-agents with independent summon_prompts** — each soul has a complete thinking framework and distinct linguistic style
- **Structured dialectical synthesis** — consensus / divergence / blind spots / principal contradiction / action program (5-step method)
- **Dual review mechanism** — Banner-master primary review (ismism catalog matching) + Second Review Officer secondary review
- **Six-dimension veto review committee** — class analysis / scientific methodology / gender analysis / colonial critique / systemic thinking critique / absent voices
- **Soul archive knowledge base** — 24 soul thinking frameworks accumulated through collection → refinement → review

---

## Five Modes of Possession

| Mode | Use Case | Execution |
|------|----------|-----------|
| **Single Soul** | Single domain, clear objective | Match → Review → Spawn |
| **Conference** (合议) | Cross-domain complex decisions | Parallel analysis → Dialectical synthesis |
| **Debate** (辩论) | Binary dilemmas | Two opposing arguments → Banner-master ruling |
| **Relay** (接力) | Multi-stage sequential work | Output of A → Input of B → Connect-point review |
| **Banner-master Study** (学习) | Training dialectical literacy | Two opposing souls read + review each other |

---

## Review Committee (Six-Dimension Veto System)

| Dimension | Reviewer | Veto Scope |
|-----------|----------|------------|
| Class Analysis | Lenin / Mao / Deng (rotating) | Missing class perspective, depoliticization |
| Scientific Methodology | Feynman | Unfalsifiable claims, circular definitions |
| Gender Analysis | Beauvoir | Gender blind spots, patriarchal presuppositions |
| Colonial Critique | Fanon | Colonial erasure, Eurocentric frameworks |
| Systemic Thinking Critique | Zhuangzi | Categorical violence — operates by questioning, not direct veto |
| Absent Voices | (Empty Chair) | Perspectives of the oppressed that cannot be represented |

Each dimension holds **one vote veto power**. Zhuangzi operates by questioning: "In what sense is your review a violent categorization?" A reviewer unable to answer Zhuangzi's question → ruling auto-flagged "pending re-review."

---

## Current Souls (24)

**Gold Souls**: Lenin, Mao Zedong, Deng Xiaoping, Lu Xun, Feynman, Beauvoir, Fanon, Weimingzi (Banner-master), Zhuangzi, Inamori Kazuo, Ibn Khaldun, Marx, Hegel, Gramsci, Nietzsche, Confucius, Husserl

**Silver Souls**: Karpathy, Jensen Huang

**Purple Souls**: Musk, Luo Yonghao, Steve Jobs, Zhu Huaihuai

**Blue Souls**: SpongeBob

---

## Anti-Consumption Mechanisms

- **Self-Negation Check**: After each session — "Which presupposition was shaken?"
- **Empty Chair Question**: "Whose interests were represented? Whose voice was not given?"
- **User Presupposition Declaration**: Record existing judgments before possession, compare after
- **3 consecutive consumption uses** → forced Banner-master study mode
- **Practice Opening Detection**: Diagnose methodological blind spots, generate practice issues

---

## Trigger Commands

| Command | Function |
|---------|----------|
| `收魂 {name}` | Web research across 10 dimensions |
| `炼化 {name}` | Refine materials into Soul Profile + ismism catalog matching |
| `审查 {name}` | Banner-master independent review |
| `幡中有什么魂` | List all souls and distribution |
| `散魂 {name}` | Remove a soul (archive retained) |
| `用{name}来{task}` | Manual soul assignment |
| `合议 {task}` | Multi-soul parallel analysis + dialectical synthesis |
| `辩论 {topic} {A} vs {B}` | Two-soul debate |
| `接力 {task} {A}→{B}→...` | Sequential relay |
| `幡中战绩` | View possession effectiveness records |

---

## Completely Free

All core functionality runs at **zero additional cost**:

| Function | Free Solution |
|----------|---------------|
| Soul Search | WebSearch + WebFetch (built-in) or tmwd-bridge (open source) |
| Format Conversion | markitdown (MIT open source) |
| Knowledge Graph | graphify (optional, pure LLM) |
| Maintenance Automation | loop (built-in) |
| Controlled Experiments | scripts/controlled-experiment.py (built-in) |

---

## Install

```bash
# 1. Clone to Claude Code skills directory
git clone https://github.com/Azhu9701/soul-banner.git ~/.claude/skills/soul-banner

# 2. Sync agent files
python3 ~/.claude/skills/soul-banner/scripts/sync-agent.py --all

# 3. Restart Claude Code

# 4. Start using
/soul-banner
```

---

## Complete Iteration History

### v1.0 — Prototype (2026-04-27)
- **Wanmin Banner born**: Knowledge and thinking-mode orchestration system
- Collection → Refinement → Review → Registry basic pipeline established
- First commit: `d425902`

### v2.0 — Six-Tier Grade System (2026-04-28)
- **White/Green/Blue/Purple/Silver/Gold grades**: From sparse materials to independent worldview
- **Banner-master review mechanism** + independent review mechanism
- **First batch of 9 soul archives** uploaded
- Commit: `b3082ee`

### v2.1 — Four Possession Modes (2026-04-29~30)
- **Single/Conference/Debate/Relay** four possession modes
- **Feedback loop**: Effectiveness ratings (effective / partially effective / ineffective)
- **Obsidian archive integration**: Auto-save possession outputs
- Conference mode two-phase execution fix
- Commits: `57d0723`, `03bddd6`, `cf546ff`, `9b3694f`

### v2.2/v2.3 — Three-Layer Trigger System (2026-05-01 early morning)
- **Spirit-recognition / Tool-spirit / Law-decree** three-layer autonomous trigger: Hook auto-scans user input
- Obsidian archive landing + first conference summon record
- SKILL.md optimization: eliminate hardcoded paths, trim 422→357 lines
- Commits: `3f7a671`, `639c9f9`, `3f772f5`, `bcc471b`

### v2.4 — Review Deepening (2026-05-01 morning)
- **Review committee** established (Lenin presiding)
- **tmwd-bridge search integration**: Real Chrome multi-engine search
- **Full-mode mandatory review** + Second Review Officer mechanism
- **Three-way cross-validation**: Prevent manual record drift
- Hook de-hardcoding + perspective phrase supplementation
- Commits: `160a35c`, `742420c`, `aeeacf3`

### v2.5 — Repository Stabilization (2026-05-01 afternoon~evening)
- **Framework/data separation**: Strict distinction between repo (framework tools) and local data
- **Review committee pragmatic downgrade**: 16-soul election restructured committee
- **Transaction script transact.py**: Batch mechanical operations, host agent only makes judgments
- **Match pre-screening match.py** + State snapshot state-summary.py
- **Match review lightweight**: registry-lite.yaml (~6KB)
- **Soul YAML ↔ Agent auto-sync**: sync-agent.py
- Commits: `e3c8417`, `e970867`, `101e4fc`, `1548a3e`, `1cafcbb`

### v2.6 — Performance + Free Audit (2026-05-02 morning)
- **Match review Token -72%** (40.4k → 11.2k tokens)
- Banner-master review zero file reads + match.py compact output
- **Full dependency audit**: Confirmed all core functions run at zero additional cost
- **Search fallback chain**: WebSearch + WebFetch (free built-in) prioritized
- **match.py exclude two-tier judgment** (hard/soft)
- Commits: `963052d`, `5953198`

### v2.7 — Anti-Consumption Reformation (2026-05-02 noon~afternoon)
- **Weimingzi's seven reform proposals** all executed:
  1. Self-negation check mandatory (3 consecutive consumption → forced study)
  2. Zhuangzi sixth-dimension veto (systemic thinking critique)
  3. Match from grade-priority to cognitive-distance-priority
  4. Pre-possession user presupposition declaration
  5. User participation session (most unexpected / already known)
  6. Soul generation chain transparency
  7. Empty chair questioning session
- **Five action programs executed**:
  - Self-description correction: no longer pretending neutrality
  - Feynman-style controlled experiment framework
  - Review committee five-dimension veto system
  - Absentee empty chair institutionalization
  - Soul collection: Zhuangzi — anti-system's system
- **Gold soul freeze clause removed**: Local governance decisions shouldn't be hardcoded in distributed skills
- Commits: `293d3a9`, `ab7c058`, `9e9d721`

### v2.8 — Review Three Fixes + cmux (2026-05-02 evening~night)
- **Weimingzi review three fixes**:
  1. auto-possess.md formula split fix
  2. Zhuangzi self-referential paradox handling (Hundun's orifices)
  3. Code enforcement layer: --self-negation/--empty-chair required params
- **cmux visualization mode integration**: Real-time multi-pane visualization for conference/debate/relay
  - v3: tail -f display (zero token, zero latency)
  - v4: Agent scheduler (~500 token/pane)
- Commits: `625a9c9`, `73a9d25`, `4080cc2`, `03c6f40`, `4ad5adc`, `fc25923`

### v3.0 — Wanhun→Wanmin Banner (2026-05-02 late night)
- One character changed: Soul (魂) → People (民). The banner belongs to the people, not a sorcerer
- **Archive directly to Obsidian**, removing /tmp intermediary
- transact.py disk-write scheme restored
- Commits: `b479bed`, `c571523`, `94c6caa`, `058e79a`, `536da68`, `70b27bf`

### v3.1 — Ismism Catalog Matching (2026-05-02 night~03 dawn)
- **Banner-master switch**: Lenin → Weimingzi (new banner-master), Lenin → Second Review Officer
- **Ismism catalog matching**: 20 souls re-annotated with `code`/`catalog_match`/`match_quality`/`compat`/`incompat`
- **Review framework upgrade**: From Marxist-Leninist framework to ismism four-dimension coordinate review
- **Search dimension expansion**: 6 personal foundation + 4 ismism positioning dimensions
- **Catalog pre-check**: Preliminary positioning in Weimingzi's original 256-entry catalog during collection
- Commits: `380f942`, `221d5b0`

### v3.2 — Fill-Person Rules + Open Practice Review (2026-05-03)
- **Review fill-person rule**: match_quality approx/outside-catalog + framework gap is task-essential → explicitly add person in conference
- **Open practice review corrections**: Living figures must use open practice review, not closed archive review
- **Six-dimension veto review committee** formally operational
- **Gold soul mutual review** fully underway
- **Reverse review**: Marx reviewing Lenin, Hegel reviewing Lenin
- Committee internal records

### v3.3 — Broadcast Mutual Visibility (2026-05-03 late night)
- **Match Mode A (broadcast self-selection)** becomes default:
  - Round 1: 20 souls mutual visibility self-selection, forming preliminary conference team
  - Round 2: Mutual visibility challenge, all 20 souls lightweight spawn to raise objections
- **self_declare evolution mechanism**: Souls can propose changes to their declarations, accumulate 3 pending → banner-master review approval
- **Mode B (match.py algorithm matching)** demoted to fallback
- **Simplified review for manual soul assignment**: Only check exclude and applicability boundary
- Commit: `ed3ce6b`

### v3.4 — Anti-Consumption Code Enforcement + Zhu Huaihuai Entry (2026-05-03~04)
- **transact.py code enforcement layer**: possession-close missing --self-negation/--empty-chair → refuse to write
- **Zhu Huaihuai entry review**: 2026 presencer, factory-second-generation entrepreneur / embodied robotics
- **User presupposition declaration** mandatory enforcement
- **Self-negation consecutive consumption tracking**: 3 consecutive failures → forced study mode
- **Review committee meetings**: 2026-05-03, 2026-05-04 substantively convened
- **Practice opening detection v3.5**: Diagnose methodological blind spots → classify → generate practice issues
- Commit: `(pending — this push)`

### v3.5 — Grade System Removal + Full Slim-down (2026-05-04 — current)
- **Removed six-tier grade system**: White/Green/Blue/Purple/Silver/Gold grades removed from core logic. Soul functionality now uniquely determined by ismism four-dimension coordinates, no auxiliary labels
- **Removed gold soul freeze clauses and related logic**: cleanup-grade-system.py, migrate-grade-system.py, discipline-inspector.py substantially slimmed
- **Removed gold_review field**: match.py no longer outputs grade review content
- **SKILL.md grade table removed**: Function description section now uses ismism coordinates
- **Full script slim-down**: 35 files, -578 lines / +296 lines, net -282 lines
- **ismism-data.json completion**: 20+ souls' ismism four-dimension coordinate data completed
- **Review committee rotation optimization**: C1/C2/C3 metrics tracking, next meeting 2026-06-06
- **Registry data sync**: 24-soul distribution updated, 9-soul zero-summon alert
- Commit: `(this push)`

---

## Iteration Statistics

| Metric | Value |
|--------|-------|
| Total Commits | 42 |
| Iteration Days | 8 (2026-04-27 ~ 2026-05-04) |
| Total Souls | 24 |
| Gold Souls | 17 |
| Total Possessions | 74 |
| Review Reports | 14 |
| Committee Meetings | 3 |
| Script Files | 34 |
| Core Docs | 7 |

## Key Architectural Decisions

1. **Host agent is pure coordinator** — No analysis, no role-play, no synthesis. All thinking via spawned sub-agents
2. **Banner-master is also a summoned soul** — Must be spawned with summon_prompt injected; host agent cannot play banner-master
3. **Soul output verbatim preservation** — No compression, rewriting, or summarization. Write to disk immediately upon receipt
4. **Ismism catalog matching** — From coordinate arithmetic review to catalog-position-determined compat/incompat review
5. **No false neutrality** — System carries specific ideological stance (Marxist-Leninist review framework → Ismism catalog matching framework)
6. **Practice opening** — System does not attempt to fill practice blind spots. Output practice issues for the user to take into practice

---

## Related Repos

- **[soul-banner-pro](https://github.com/Azhu9701/soul-banner-pro)** — Archived snapshot

---

*"The banner moves, souls arrive. Match souls to tasks, tasks to souls. The banner-master holds the banner; souls stay within bounds."*
