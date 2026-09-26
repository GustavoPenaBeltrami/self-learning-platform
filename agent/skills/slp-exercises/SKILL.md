---
name: slp-exercises
description: Builds an applied exercise on a unit of a study topic in topics/ — forces producing an artifact (code, ADR, critique, explanation) instead of answering questions. Use when the user says "I want an exercise", "do something practical with this", "apply what I learned", "/slp-exercises", or when slp-session recommends one for a finished unit.
---

# Exercises

An exam tests whether something was understood. An exercise forces **using**
the concept to produce something new. This skill writes the prompt; grading
belongs to `slp-grade`.

## Where it writes

```
topics/<topic>/exercises/<exercise-slug>/
  prompt.md
  attempts/            the user submits here
```

`<exercise-slug>`: kebab-case, descriptive (`adr-topic-vs-queue`). Prompt
format: [formats.md § Exercises](../../reference/formats.md#exercises).
Language: `language.exams` unless the user asks for another.

## Process

1. **Context**: log a `practice` activity
   ([slp-session §Activity](../slp-session/SKILL.md#activity)). Read
   `topic.json` (`type`, `language`), `status.md` (current unit),
   `learning.md`, the unit's notes and its `wiki/` pages. Look at
   `exercises/` so you don't repeat one.
2. **Aim** at the latest thing learned or at a **corrected misconception**
   from the Record: producing something with it is the acid test. Don't
   exercise what's already solid.
3. **Format**, the one that best forces use of the concept:
   - **apply**: use the concept in a concrete case.
   - **build**: produce an artifact from scratch (code, diagram, decision
     document).
   - **critique**: point out what's wrong in a given design or code, and why,
     with the topic's vocabulary.
   - **teach**: explain the concept from scratch to a third party (Feynman),
     written or recorded.

   Default per topic `type`: the table in
   [formats.md § topic.json](../../reference/formats.md#topicjson). Not
   obvious: ask with `AskUserQuestion`.
4. **Real case**: for apply or critique, offer to use something from their
   work. If not, invent an equally concrete case. It never blocks.
5. **Write `prompt.md`**:

   ```md
   # Exercise — Topic vs queue ADR

   **Format:** build · **Unit:** 02 · **Rests on:** Architectural thinking › Analyzing trade-offs

   Pick a real asynchronous integration between two services. Write an ADR
   deciding topic vs queue, with at least two trade-offs weighed against each
   other and why the other option was discarded.

   **Submit:** a `.md` with the ADR.
   ```

   `Rests on` names note headings, never file names. Hard rule: a verifiable
   result, never "think about this". Each condition is a grading criterion:
   write them so they can be checked one by one.
6. **Close**: tell them where to submit,
   `topics/<topic>/exercises/<slug>/attempts/<YYYY-MM-DDTHHmm>.<ext>` (`.md`
   for prose, the language's extension for code, `.md` with the transcription
   if it was spoken), and that `slp-grade` gives the feedback. Write nothing else
   to `progress/`.
