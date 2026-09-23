---
name: slp-exercises
description: Builds an applied exercise on a topic — forces producing an artifact (code, ADR, critique, explanation) instead of answering questions. Use when the user says "I want an exercise", "do something practical with this", "apply what I learned", "/slp-exercises", or when slp-session detects a topic with notes but no exercises.
---

# Exercises

An exam tests whether something was understood. An exercise forces you to **use** the
concept to produce something new. It's the difference between recognizing/recalling and
reasoning with it. This skill builds the prompt; grading belongs to `slp-grade`.

## Where it writes

```
topics/<topic>/exercises/<exercise-slug>/
  prompt.md
  attempts/            # the user submits here
```

`<exercise-slug>` in kebab-case, descriptive (`adr-topic-vs-queue`). If
`exercises/` doesn't exist in the topic, create it.

## Language

`prompt.md` is written in `topic.json` → `language.exams` by default. An explicit
request from the user ("the exercise in English") overrides that default for that
exercise. Chat with the user in the language the user writes in.

## Process

1. **Read the context**: `topic.json` (`type`, `language`), `progress/status.md`
   (current unit), `learning.md` and the notes for that unit. Look at
   `exercises/` so you don't repeat an exercise already done.
2. **Aim**: at the latest thing learned or at a **corrected misconception**
   from the Record — exercising it by producing something is the acid test that it
   really was corrected. Don't exercise what's already solid as if it were new.
3. **Choose the format** that best forces use of the concept, not the easiest one to
   build:
   - **apply** — use the concept in a concrete case.
   - **build** — produce an artifact from scratch: code, diagram, decision
     document.
   - **critique** — given someone else's design/code (real or made up for the
     exercise), point out what's wrong and why, with the topic's vocabulary.
   - **teach** — explain the concept from scratch to a hypothetical third party
     (Feynman), written or recorded.

   Guide: tool `documentation`/`course` → *build*; architecture `book` →
   *apply*/*critique*; language → spoken *teach*. If it's not
   obvious, ask with `AskUserQuestion`.
4. **Offer, don't force, the real case**: if the format is *apply* or *critique*,
   ask whether they want to use something from their work. If they say no or it doesn't apply,
   make up an equally concrete case. It never blocks the exercise.
5. **Write `prompt.md`**, in the language from *Language*:

   ```md
   # Exercise — Real topic vs queue ADR

   **Format:** build · **Topic:** FoSA ch 2 · **Rests on:** notes/02-...md#analyzing-trade-offs

   Pick a real asynchronous integration (from work, or made up if you don't have one at hand)
   between two services. Write a complete ADR deciding topic vs queue, with at least two
   trade-offs explicitly weighed against each other. Listing pros/cons isn't enough:
   there has to be a decision and why the other option was discarded.

   **Submit:** a `.md` with the ADR.
   ```

   Hard rule: verifiable result. Never "apply what you saw" or "think
   about this"; always something with a decision made, code that runs, a
   list of justified flaws. The prompt's conditions are the
   criteria it's graded against later: write them so they can be
   checked one by one.
6. **Close** by saying where to submit and what comes next:
   - `topics/<topic>/exercises/<slug>/attempts/<YYYY-MM-DDTHHmm>.<ext>` — `.md`
     for ADR/critique/explanation, the language's extension if it's code, `.md`
     with the transcription if it was oral (via `/api/voice`).
   - When they submit it, `slp-grade` gives the feedback and records the progress.
     This skill doesn't write to `progress/`: an unsubmitted exercise isn't an
     event.
