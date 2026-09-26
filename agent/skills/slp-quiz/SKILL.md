---
name: slp-quiz
description: Measures the learner's level in a study topic in topics/ with a repeatable ping-pong quiz in the chat — graded questions that go up on a hit and down on a miss per prerequisite thread — using a fixed bank in exams/quiz/, so results are comparable over time. Use when slp-init diagnoses a new topic, when slp-session says a quiz is due, or when the user says "quiz me on my level", "check my level", "where am I on this topic", "/slp-quiz". For questions on what is being taught right now use slp-teach.
---

# Quiz

The same bank every time, so today's result can be compared with the first
one. Formats: [formats.md § Quiz](../../reference/formats.md#quiz).

## 1. Open

1. Pick the topic (list `topics/`). Log a `quiz` activity
   ([slp-session §Activity](../slp-session/SKILL.md#activity)).
2. Read `topic.json` (Mission, `type`, `language.exams`), `learning.md` and
   `wiki/index.md`.

## 2. The bank

`topics/<slug>/exams/quiz/exam.json`.

- **Missing**: build it. Pick 3-6 **threads**: the prerequisite lines the
  Mission rests on (kebab-case, e.g. `methods`, `status-codes`). Per thread
  write questions at 3 levels (1 = basic vocabulary, 3 = application, 5 =
  trade-offs an expert weighs), 1-2 per level, following
  [graded-questions.md](../../reference/graded-questions.md). Mostly
  `multiple_choice`; one `open` per thread at level 4-5 is fine. Add
  `"kind": "quiz"` and `thread`/`level` on every question. Verify
  doubtful facts with `researcher`. Validate with
  `uv run python -m json.tool <file> > /dev/null`.
- **Exists**: never edit or reorder its questions. If a thread's ceiling was
  never found last time (all correct at the top level), **append** questions
  at a higher level to the end of `questions`.

## 3. Run (ping-pong, in the chat)

Per thread, start at level 3. Ask a question from the bank with
`AskUserQuestion` (an `open` one as a plain question), grade it in your next
message, then go **up** on a hit and **down** on a miss. Stop when the thread
is bounded on both sides (a hit at level L, a miss at L+1), or at the ends of
the scale. An "I don't know" is a miss. Don't teach mid-quiz: note the
misconception and move on.

The app can also run the bank as a plain, non-adaptive exam; grade such an
attempt with `slp-grade`.

## 4. Write

1. **Attempt**: `exams/quiz/attempts/<date>.json`, the normal attempt
   format plus `"mode": "chat"`: one answer per question asked, with `i` (its
   index in the bank), `type`, and `chosen` or `text`.
2. **Feedback**: `<date>.feedback.md` next to it: the header, a table
   `| Thread | Edge level |` (the highest level answered correctly, `0` if
   none), then one ✗ section per missed question, as in
   [formats.md § Feedback](../../reference/formats.md#feedback).
3. **Log**: a row in `## Quizzes` of `progress/log.md`:
   `| YYYY-MM-DD | methods L3, status-codes L2 | attempts/<date>.feedback.md |`.
4. **learning.md**: a Record entry only for what a Record rule covers: on the
   first quiz, "declared prior knowledge" plus the edges; later, a
   misconception found, or a thread whose edge moved (compare with the
   previous feedback).

## 5. Wrap-up

Two or three lines: the edge per thread, what moved since last time, and one
suggested next step (usually `slp-teach` on the lowest thread).
