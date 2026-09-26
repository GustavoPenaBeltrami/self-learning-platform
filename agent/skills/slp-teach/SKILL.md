---
name: slp-teach
description: Teaches a unit of a study topic in topics/ interactively in the chat so it ends up understood, not memorized — probes the real level with graded questions, plans the lesson as a dependency graph, builds it node by node, then writes the lesson note, the learning record and the topic wiki. Use when the user wants to learn or understand something from one of their topics, from a one-line clarification to a long session. Triggers on "/slp-teach", "teach me", "I don't get it", "ask me questions on this" (in the chat), or pasted study material they want to understand. Don't use for questions about this repository's own code.
---

# Teach

The goal is never "can recite the fact". It is **understanding**: the fact
derives from foundations the learner already accepts, is connected to their
mental model, and so holds up on its own. Two principles do that, always, in a
one-line answer or a two-hour session:

- **i. Unconditional truths first.** Start from facts that can be accepted as
  is, with no caveats ("every X is Y", a real definition, an atomic unit like
  "ALL communication between computers is done via {sending packets}"). They
  lock in instantly and give a floor. Confirm each one feels obvious before
  building on it. Say "unconditional truth"; keep "axiom" for what truly has
  nothing beneath it.
- **ii. "How could I have discovered this myself?"** Nothing appears out of
  nowhere. Motivate every step: what problem sends us here, why try *this*
  move. That turns loose facts into connected ones. Socratic (they try first)
  when they can reason it out; expository (you narrate the discovery path,
  3Blue1Brown style) when it's out of reach or they're low on energy.

The reasoning behind both, and why fluency isn't retention:
[references/philosophy.md](references/philosophy.md). Read it before phase 2
when the lesson is more than a small request.

If you are answering in a compressed or terse style, drop it while teaching:
the full explanation is the work.

## Before starting

1. **Topic.** List `topics/` and pick the folder; don't invent slugs. If the
   topic doesn't exist, offer `/slp-init` and stop: this skill doesn't create
   topics.
2. **Session.** Log a `teaching` activity with the lesson's subject as
   `detail` ([slp-session §Activity](../slp-session/SKILL.md#activity)).
3. **Persona.** If `agent/agents/teacher-<slug>.md` exists, read it and teach as
   that persona in this conversation. It is a persona, not a subagent: you
   still run everything below yourself.
4. **Memory.** Read `learning.md` (Mission, Glossary, Record) and
   `wiki/index.md`. Format: [formats.md](../../reference/formats.md#learningmd).

## Tools

| What for | Use |
|---|---|
| Question with a correct answer (probing, node check) | `AskUserQuestion`, graded in your next message ([graded-questions.md](../../reference/graded-questions.md)) |
| Question without one (goals, direction) | `AskUserQuestion`, not graded |
| Verify a fact, survey a topic | the `researcher` agent (`Agent`, `subagent_type: researcher`) |
| Diagram or formula | a ```` ```mermaid ```` or ```` ```math ```` fence in the note |
| Questions worth sitting later | `slp-exam` |

Language: chat in the user's language; the note and wiki default to
`topic.json` → `language.notes` (see `AGENTS.md`).

**Accuracy is non-negotiable.** The moment you doubt a fact, name, date,
formula or definition even slightly, verify it with `researcher` before
saying it. Pausing to verify is always fine. If the check corrects you, say
so. A wrong unconditional truth corrupts every node resting on it.

**Sources and conflicts** follow [sources.md](../../reference/sources.md):
use the topic's `links` and `resources/` first, respect `sources_mode`, and
when sources disagree pick one without flagging it in the chat, then record
the `Source choice`.

## The process: probe → plan → teach

Always the three phases, in order. The size of each phase scales with the
request; the shape never does.

### Phase 1 — Probe (never skip it)

**1a. Their current level — graded questions.** Locate the edge of what they
understand in every thread the lesson rests on, bounded on both sides, by
binary search: the rules are in
[graded-questions.md § Locating the edge](../../reference/graded-questions.md#locating-the-edge-of-what-they-know).
What the Record already shows is floor and isn't probed again; recorded
misconceptions are. This phase lasts as long as it needs. Don't move on until
you can say, per thread, what they have and where it runs out.

**1b. Their goal — open question, ungraded.** If the Mission is written,
confirm it and trim it to this session. Otherwise interrogate what they want
until it is concrete: "understand hexagonal architecture" can mean ten things.
An empty or vague Mission is the first thing to fix.

### Phase 2 — Plan (think hard here)

The highest-leverage step. With level and goal in hand:

- Read the relevant `wiki/` concept pages: their `depends_on` is the graph from
  earlier lessons. Then the topic's sources.
- Survey the field with `researcher` (core concepts, real first principles,
  standard framings, common pitfalls) unless the wiki already covers it.
- Find the unconditional truths this rests on, and an atomic unit if one fits.
- Start from what they already have (1a): no lower, no higher.
- Trace the motivated discovery path from those truths to the goal. Pick
  Socratic or expository per stretch.
- **Test the roots**: is each root genuinely unconditional *for this learner*,
  or a theorem in disguise? If it derives from something simpler, push it down.

**Present the plan in the chat, always, before teaching:**

1. The approach in a few sentences: what, in what order, and why, given their
   edge and goal.
2. The dependency map: a small nested list (a DAG) with unconditional truths at
   the roots and their goal as the destination. It is the order of phase 3.

**Then stop and wait for the go-ahead.** A wrong root or scope is cheap to fix
now and expensive mid-lesson.

### Phase 3 — Teach (the loop)

Build the graph one node at a time. For **each node**, foundations included:

1. **Motivate**: why this node, why now; what problem it solves.
2. **Establish**: a foundation is stated bare, literally, with no caveats. A
   derived step is built from what's in place with a motivated move. When the
   Socratic step has a correct answer, make it a graded question.
3. **Connect**: make the edge explicit, how it hangs off the nodes in place.
4. **Check**: a short graded question. A miss means the node isn't solid: fix
   it before building on it.

If you catch yourself asserting something they'd have to take on faith, stop:
motivate it and check it, or rest it on something established.

## Diagrams and formulas

Only when the idea *is* a structure (dependencies, parts and arrows, a
sequence, a state machine, a tree) or is spatial. When in doubt, don't.

- One fence = one idea, about 7 nodes at most; split bigger ones.
- Mermaid types that render: `graph TD`/`LR`, `sequenceDiagram`,
  `stateDiagram-v2`, `erDiagram`, `classDiagram`, `timeline`.
- `math` is KaTeX, display blocks only; inline math stays as text or `code`.
- A fence that doesn't compile shows its source and error in the app: fix it.

## Where the lesson goes

A session that isn't written down evaporates. When it ends, or when the user
cuts it off:

1. **Note.** Write the lesson as a new `notes/NN-<slug of its h1>.md`, numbered
   after the existing ones, one `# ` at the top
   ([formats.md § Notes](../../reference/formats.md#notes)). Include the
   dependency map as a `graph TD` fence, each node with its motivation and
   connection, and the diagrams used. Don't copy the probing questions. Cite
   every sourced claim and close with the best primary source to read or
   watch. Refer to other notes by heading, never by file name. No nested lists.
2. **learning.md.** Terms they can now use go to the Glossary; anything that
   meets a Record rule goes to the Record. Neither happened: write nothing.
3. **Wiki.** Upsert one `wiki/concepts/<kebab>.md` per node taught, with
   `depends_on` from the map and footnote citations, and update
   `wiki/index.md` ([formats.md § Wiki](../../reference/formats.md#wiki)).
   Update an existing page before creating a new one. Add the open session's
   `id` to each page's `studied`: that is the concept's progress.
4. **Exam material.** Questions worth sitting again go to `slp-exam`, not the
   note.
5. **status.md.** Update current unit and date; don't invent grades or dates.
6. **Unit.** Ask whether the lesson finished the unit; if yes, run
   [slp-session §Unit done](../slp-session/SKILL.md#unit-done). Otherwise
   remind them that cards (`slp-cards`) are what turn this into retention.

## If the request is small

A one-line clarification doesn't get subagents or a written plan, but it gets
the same shape: a quick question to know where to start, the answer resting
on something they accept, and a check that it landed, graded. Small requests
write nothing unless a Record rule fires; then only step 2.
