---
name: notes-grade
description: Grades an exam or exercise attempt — checks each rubric or prompt point, writes the feedback next to the attempt, updates learning.md and the topic's progress. Use when the user says "grade this attempt", "how did I do", "grade my exercise", "/notes-grade" (or in Spanish: "corregime este intento", "cómo me fue", "corregí mi ejercicio"), or after taking an exam with non-MC questions in exam.html or submitting an exercise from notes-exercises.
---

# Grade

An attempt without feedback is practice in the dark. This skill closes the loop:
it compares what was submitted against what was asked, says what's missing (not "it's wrong"), and
leaves everything recorded so `notes-review` and the next session can use it.

## Which attempt to grade

An attempt is **pending** when `attempts/<date>.<ext>` exists without its
companion `attempts/<date>.md`. If the user doesn't say which one, look in
`topics/*/exams/*/attempts/` and `topics/*/exercises/*/attempts/`; if there's
only one, grade that one; if there are several, ask with `AskUserQuestion`.

## Language

Feedback (the `attempts/<date>.md` file) is written in `topic.json` →
`language.exams` by default. An explicit request from the user ("give me the
feedback in Spanish") overrides that default for that output. Chat with the user
in the language the user writes in.

## Two sources, one mechanism

The only thing that changes is what you compare against.

**Exam attempt** — read `exams/<slug>/attempts/<date>.json` (raw),
`exams/<slug>/exam.json` (questions and rubrics) and the relevant `notes/*.md`.
- `multiple_choice`: already graded by the client; recompute the score
  comparing `chosen` with `answer` and list the missed ones with their `explanation`.
- `open`, `practical`: check the answer against **each point**
  of the `rubric`. Paraphrasing counts; touching the word without the concept doesn't.
- `oral`: if the answer comes with `text` (the student used the written fallback),
  grade it the same as `open`. If it comes with `audio` (a file name in
  `attempts/`), that's the source of truth — you can't listen to the file
  directly, so transcribe it with the same engine the server uses,
  in the exam's language (`topic.json` → `language.exams`, or the language the
  exam was actually written in if the user overrode it):

  ```bash
  uv run app/server.py --transcribe \
      topics/<slug>/exams/<exam>/attempts/<audio-file> [lang]
  ```

  `lang` is optional; if omitted, the engine auto-detects the language.
  Grade the transcription against the `rubric` the same as a written answer.
  Don't touch the audio. Make clear in the feedback that the transcription doesn't assess
  pronunciation or prosody, only content.

**Exercise attempt** — read `exercises/<slug>/prompt.md`, the artifact
(`exercises/<slug>/attempts/<date>.<ext>`) and the notes it rests on. There's
no rubric: derive the criteria from the prompt and assess whether the artifact **uses**
the concept, not whether it "touches on the topic". An ADR that doesn't weigh trade-offs against
each other doesn't pass even if it mentions the right words. Format *teach*: it's
graded the same as an `oral` answer.

If something you're about to mark as correct isn't in the notes or in
`resources/` and you have even the slightest doubt, verify it with the `researcher`
subagent before marking it.

## What you write

**1. `attempts/<date>.md`**, next to the attempt, same format for exams and
exercises:

```md
# Attempt — <slug> — YYYY-MM-DD HH:MM

**MC score:** 4/5 · **Open/oral rubric:** 2 of 3 questions with full feedback

## [02] Open — topic vs queue trade-offs
✓ Mentioned extensibility and coupling.
✗ Didn't mention the security problem (wiretap). See `notes/02-....md#analyzing-trade-offs`.
Feedback: on the right track, but the complete answer needs the security side to be defensible in a real review.

## What to improve
- Review the topics/queues security section before the next attempt.
```

- ✓/✗ per point, each ✗ with what's missing and the note section that covers it.
- For exercises, the score line is `**Prompt criteria:** N of M`.
- If no note covers it, say so: it's a gap in the notes, not in the student.

**2. The topic's `learning.md`** — same Record rules as
`notes-teach`: what goes in is whatever reveals a **misconception** (what they
believed and what it actually is) or a non-trivial demonstration of understanding. In exercises
it counts double: a misconception that survives all the way to producing an artifact
is more serious than one that only shows up in a short answer. Getting the
expected right isn't recorded.

**3. The topic's progress** — see below.

## Progress

You write to `topics/<topic>/progress/` when grading, never before (an exam built
but not taken isn't recorded).

- **`log.md`**: one row at the end of the matching table; if the section doesn't
  exist, create it. Don't delete old rows.

  ```md
  ## Exams
  | Date | Exam | MC | Rubric | Attempt |
  ## Exercises
  | Date | Exercise | Format | Criteria | Attempt |
  ```

  If the exam corresponds to a `## Reading` row, also fill in its
  `Exam (score)` column. If it was a review (`topics/review/`), record which topics
  were included: that moves the clock of those units, not that of the "review" topic.
- **`status.md`**: it's rewritten, not accumulated. Only touch it if something about the
  present changed (next exam, immediate pending item). Don't dress up the status.
- Date always `YYYY-MM-DD`, never relative. If a piece of data is missing, ask
  once and all together. Don't invent grades or dates.

## Wrap-up in the chat

Three or four lines: score or criteria met, the weakest point, and **a single**
concrete recommendation of what to reinforce before the next attempt (the right
skill: `notes-teach`, `notes-exercises` or `notes-review`).
