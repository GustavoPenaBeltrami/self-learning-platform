# Teaching philosophy

The why behind `slp-teach`. Load it when planning (phase 2) or when unsure how to
teach a node. The process itself lives in `../SKILL.md`.

The goal is never "can recite the fact". The goal is **understanding**: the fact
is derivable from foundations the learner already accepts, it is connected to
their mental model, and so it holds up on its own. What is memorized rots. What
is understood does not.

## The philosophy (why it works)

Two minds can hold the same propositions and look identical from the outside:
they answer the same questions the same way. But one has a **pile of loose
facts** (A) and the other has a few **core truths** from which all those facts
derive (B), so for the second one the facts are obviously connected. That
connection **is** understanding.

- Connected knowledge > loose knowledge
- A dependency graph > isolated nodes
- Understanding > memorizing

Understanding preserves knowledge (it is held in place by its connections),
compresses it, and is simply better. Every move below exists to build that graph
in the learner's head: **nodes** (principle i) and **edges** (principle ii).

The feeling you are after is **the click**: the moment a pile of loose facts
collapses into a few generating ideas — the same information with far fewer
moving parts. When teaching lands, that is what it feels like from the inside.

The underlying mechanism: **the brain does not fully commit to a fact it is not
sure is safe to lock in.** If something more fundamental could contradict it
later, committing is risky — it would force an expensive update. So the brain
hedges, and the fact never quite lands. The two principles remove that risk,
each from its own side.

## Principle i — Unconditional truths first

Start from the floor. Lock in the core truths that are **always true** before
anything built on top of them.

Why start there? **Not** because bottom-up is the logically "correct" order, but
because unconditional truths are the **easiest** thing for the brain to accept
and lock in. They are safe, so they lock in instantly, and they give the first
solid floor to stand on. This counts double when the topic is completely new and
there is almost nothing to connect it to.

**Terminology — keep the distinction and don't overuse "axiom".** An
*unconditional truth* is a fact that can be accepted **as is, with no nuances or
caveats** — it is a property of *how the fact holds*. An *axiom* is a fact that
**does not follow from any other** — it is a property of *where it sits in the
graph* (root node, no incoming edges). They overlap but are not synonyms: an
axiom that also needs no caveats is a kind of unconditional truth, but a great
many unconditional truths *do* derive from deeper things — they just don't need
that derivation to be accepted safely. By default say **"unconditional truth"**;
reserve **"axiom"** for what truly hits bottom.

- Find the few hard facts that can be taken literally. There may be very few.
  That's fine: few and solid beats many and shaky.
- They must be so simple they are accepted **as is, without nuance**. No "well,
  usually…". If it needs conditions, it is not an unconditional truth yet: keep
  digging.
- Build everything else on top of them, explicitly, so the learner sees each new
  fact resting on the floor.

**Confirm the floor before building on it.** Quickly check that each core truth
feels obvious to the learner before stacking structure on it. If one doesn't
feel solid, stop and fix the floor: don't build on sand.

**Two especially strong forms of unconditional truth:**

- **Universal statements** — *"every X is Y"* or *"no X is Y"*. They lock in
  easily because they admit no exceptions to hedge against. An atomic-unit
  version (*"ALL X is done via {____}"*, e.g. *"ALL communication between
  computers is done via {sending packets}"*) is a particularly powerful case —
  surface it when the domain has one, but it is one form of universal statement,
  not the only one.
- **Real definitions** — a genuine definition is a great starting point. But
  only if it is a *real* definition, not a vague list of properties in disguise.
  If it is "things that tend to be true of X", it is not a definition and it
  anchors nothing.

Don't force either one where there isn't a clean one.

## Principle ii — "How could I have discovered this myself?"

A fact feels arbitrary when you can't see any reason it *had* to be that way.
"Why does it have to be like that? Sounds arbitrary." The brain doesn't commit to
information that feels arbitrary. The fix: make it feel discovered, not decreed.

Walk the learner down the path where **they could have discovered it
themselves**. Every step must be *motivated*:

- Start from zero: **why are we doing this?** What underlying problem sends us
  down this path?
- Motivate every intermediate step too: why try *this* formula? why manipulate
  the equation *this way*? What could have led someone to this approach?
- The result is turning **loose propositions → connected propositions**: adding
  the edges to the graph.

3Blue1Brown is the gold standard here. Aim for that: nothing appears out of
nowhere, every move feels like something the learner could have tried.

### Socratic or expository — depending on the case

Choose per topic and per the energy you see:

- **Socratic** — pose the motivating problem and let the learner attempt the
  discovery before revealing it. It costs more and sticks more. It is the default
  when they can reason it out. "Letting them try" is about *who speaks first*,
  not about grading: if the question has a definite correct answer, it is still
  gradable — use a graded question, not an open one.
- **Expository** — you narrate the motivated discovery path, 3B1B style, with no
  back and forth. Use it when the topic is out of reach of reasoning it out cold,
  or when the learner is low on energy and wants it served.

When in doubt: Socratic for what they can clearly reason about, narrated for the
rest.

## Fluency is not retention

Two different things, and one is deceptive:

- **Fluency**: being able to retrieve it now, with the topic fresh.
- **Retention**: being able to retrieve it in three weeks.

Answering well at the end of the lesson measures fluency, and gives an illusory
sense of mastery. Retention is built with desirable difficulty: retrieving from
memory instead of recognizing, spacing over time, and interleaving related
topics. That is why a node check doesn't close the topic — the real closure is
spaced retrieval: the topic's cards (`slp-cards`) and, later, the quiz
(`slp-quiz`).

To acquire **knowledge**, difficulty is the enemy: it eats the working memory
needed to understand. To consolidate a **skill**, difficulty is the tool. Don't
mix up the phases.

## Why diagrams are rare

A drawing earns its place only when it shows something words don't: shape,
structure, direction, relationship, geometry. A decorative diagram that repeats
the sentence next to it adds noise and one more chance of being wrong. When in
doubt, don't: a missing drawing is cheaper than a false one.

It works well when the idea **is** a structure (dependencies, a system with parts
and arrows, a pipeline, a sequence of exchanges, a state machine, a tree, a
comparison, what's inside and what's outside) or when it is spatial.

