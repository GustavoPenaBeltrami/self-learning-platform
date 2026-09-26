---
name: slp-exam
description: Builds an exam file (exam.json) for one unit of a study topic in topics/, that the user sits later in the app — from pasted material, or else from the unit's notes, wiki and sources — auditing the topic's progress first. Use when the user asks for an exam, a test, "exam on this", "give me questions to sit", "/slp-exam", or pastes a chapter and asks for an exam on it. For questions in the chat use slp-teach; for a level diagnostic use slp-quiz.
---

# Exam

Writes `topics/<slug>/exams/<exam>/exam.json`, sat in the app
(`app/views/exam.html`). Format and rules:
[formats.md § Exams](../../reference/formats.md#exams).

## 1. Audit (before writing a single question)

1. List `topics/` and pick the topic; don't invent folders. Unclear topic or
   unit: infer it from the content, else ask once.
2. Log an `exam` activity ([slp-session §Activity](../slp-session/SKILL.md#activity)).
3. Read `topic.json` (`type`, `language.exams`), `progress/status.md` (don't
   examine what hasn't been covered), and `learning.md`: Record floor isn't
   asked as new; corrected misconceptions are worth pressing on.

## 2. Source material, in this order

1. Content the user pasted or attached in this conversation.
2. Otherwise the unit's `notes/*.md` and the `wiki/` pages for that unit.
3. Otherwise the topic's sources ([sources.md](../../reference/sources.md)).

Everything in the exam comes from that material. What's needed and missing:
flag it, don't invent it.

## 3. Where it goes

- Folder: `<NN>-<kebab-title>` for unit NN (`01-methods-and-codes`).
- The folder exists **and has `attempts/`**: never replace it (attempts point
  at questions by index). Create `<NN>-<kebab-title>-b`.
  It exists with no attempts: ask whether to replace it or create `-b`.

## 4. Question types

Ask with `AskUserQuestion` (multiSelect) which types go in: `multiple choice`,
`open`, `oral` (answered by voice), `practical`. Preselect multiple choice and
open; also oral and practical when `type` is `practice`. Use only the
confirmed types.

## 5. Writing the questions

10 to 15 per unit. Mix: about 30% definitions and precise vocabulary, 40%
application (a concrete scenario, what should be done), 30% trade-offs and
counterexamples. Lean toward application and trade-offs. Adapt to the topic's
`type` ([formats.md § topic.json](../../reference/formats.md#topicjson)):
`certification` imitates the real exam (short scenarios, one correct answer
out of four, domain weights in a full mock); `documentation` asks when to use
what and its limits, never parameter names.

Type split among the confirmed types: 60% `multiple_choice` / 40% the rest,
the 40% shared among open, oral and practical.

Options, explanations and rubrics follow
[graded-questions.md](../../reference/graded-questions.md): bare statements,
correct one first and mutated into distractors, `answer` spread over 0-3,
3-5 checkable rubric points.

Language: `language.exams`, unless the user asked for another.

Fences in `q`, options or `explanation` render in the app; only when the
drawing adds something:

```json
{ "q": "Given the flow:\n\n```mermaid\ngraph LR\n  A[API] --> B[(DB)]\n```\n\nWhere is the temporal coupling?" }
```

Line breaks are `\n`; LaTeX backslashes are doubled (`\\frac`).

## 6. After writing

1. `uv run python -m json.tool topics/<slug>/exams/<exam>/exam.json > /dev/null`.
2. Check: MC has 4 options and `answer` in 0-3, spread; every non-MC question
   has a 3-5 point `rubric`.
3. Tell the user the path and how to open it: `uv run slp`, then
   `http://localhost:8321/app/views/exam.html?f=topics/<slug>/exams/<exam>/exam.json`.
4. Tell them: after sitting it, run `slp-grade` on the attempt. Every attempt
   goes through `slp-grade`, MC-only too: it is what logs the score.
5. Write nothing else to `progress/`: an exam not yet sat isn't an event.
