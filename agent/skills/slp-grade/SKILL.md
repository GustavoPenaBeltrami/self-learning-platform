---
name: slp-grade
description: Grades any exam, quiz or exercise attempt in topics/ — recomputes multiple-choice scores, checks each rubric or prompt criterion, writes the feedback file next to the attempt, and updates learning.md and the topic's progress log. Use when the user says "grade this attempt", "how did I do", "grade my exercise", "/slp-grade", or after sitting any exam or quiz in the app or submitting an exercise.
---

# Grade

An attempt without feedback is practice in the dark. This skill closes the
loop for **every** attempt, MC-only ones included: it is the only writer of
the `## Exams` and `## Exercises` rows of `log.md` (and `## Quizzes` for a quiz sat in the app). Formats:
[formats.md](../../reference/formats.md) (§ Attempts, § Feedback,
§ progress/log.md).

## 1. Which attempt

Pending = `attempts/<date>.<ext>` with no `<date>.feedback.md`. Files
`<date>-p<i>.<ext>` are exam audio, not attempts. If the user doesn't say
which, look in `topics/*/exams/*/attempts/` and `topics/*/exercises/*/attempts/`:
one pending, grade it; several, ask with `AskUserQuestion`.

Log a `feedback` activity ([slp-session §Activity](../slp-session/SKILL.md#activity)).

Language: feedback is written in `language.exams` unless the user asks for
another.

## 2. Grade

**Exam attempt**: read the attempt, its `exam.json` and the relevant notes.
Each answer's `i` is the question's position in `exam.json`.

- `multiple_choice`: recompute: correct when `chosen == answer`. List misses
  with the question's `explanation`.
- `open`, `practical`: check the answer against **each** rubric point.
  Paraphrase counts; the word without the concept doesn't.
- `oral` with `text`: as `open`. With `audio`: transcribe it, in the exam's
  language (`lang` optional, auto-detected if omitted), and grade the
  transcription. Don't touch the audio; say that pronunciation isn't assessed.

  ```bash
  uv run slp transcribe topics/<slug>/exams/<exam>/attempts/<audio-file> [lang]
  ```

**Exercise attempt**: read `prompt.md`, the artifact and the notes it rests
on. The prompt's conditions are the criteria: judge whether the artifact
**uses** the concept, not whether it mentions it. An ADR that doesn't weigh
trade-offs fails even with the right words. Format `teach` is graded like an
`oral` answer.

**Facts**: before judging a factual answer, read the `Source choice` entries
in the Record and grade against the version that was taught. Anything you'd
mark correct that isn't in the notes, `resources/` or a `path` source, and you
doubt at all: verify it with `researcher`. Conflicts with no entry: resolve
them per [sources.md](../../reference/sources.md) and record the choice.

## 3. Write

1. **Feedback** `attempts/<date>.feedback.md`, format in
   [formats.md § Feedback](../../reference/formats.md#feedback):
   `[NN]` = `i + 1`; score line with the same numbers as the log row; ✓/✗
   per point, each ✗ with what's missing and the note heading that covers it
   (or "no note covers it yet: a gap in the notes, not in the student"). A ✗
   on a fact cites the source of the correct version.
2. **learning.md**: a Record entry only for a misconception (what they
   believed and what is true) or a non-trivial demonstration. In exercises a
   misconception that survived into an artifact counts double. Getting the
   expected right isn't recorded.
3. **log.md**, one row at the end of the matching table:
   - unit exam → `## Exams`: `| date | exam | MC c/t | Rubric met/total | attempts/<date>.feedback.md |`;
     also fill `Exam (score)` of that unit's `## Reading` row if it's `—`.
   - exercise → `## Exercises`: `| date | exercise | format | criteria met/total | attempts/<date>.feedback.md |`.
   - quiz (`exams/quiz/`) → `## Quizzes` as in
     [slp-quiz §4](../slp-quiz/SKILL.md#4-write), the edges read from its
     `thread`/`level` fields.
4. **status.md**: only if something about the present changed (next exam,
   immediate pending item).

Dates `YYYY-MM-DD`. Missing data: ask once, all together. Don't invent grades.

## 4. Wrap-up

Three or four lines: score or criteria met, the weakest point, and **one**
recommendation (`slp-teach`, `slp-exercises`, or `slp-cards` to keep it).
