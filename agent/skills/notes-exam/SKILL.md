---
name: notes-exam
description: Builds a JSON exam from raw content the user pastes (a book chapter, documentation, a certification guide), auditing it first against the topic's progress. Use when the user pastes pages, a chapter, an extracted PDF or their own summary and asks for an exam, a quiz, questions, or says "quiz me on this", "give me an exam on this".
---

# Notes exam

Turns raw study content into an exam consumed by `app/exam.html`.

## Prior audit (before writing a single question)

Read, in this order:

1. `topics/<slug>/topic.json` — `type` (how questions are written, see below), `language.exams`.
2. `topics/<slug>/progress/status.md` — which unit is in progress, so the exam isn't built on something that hasn't been covered yet.
3. `topics/<slug>/learning.md` — the Record: what is already confirmed as floor doesn't need to be asked again as if it were new, and what was noted as a corrected misconception is worth pressing on (it's the proof it was really corrected).

## Language

The exam (questions, options, explanations, rubrics) is written in `topic.json` → `language.exams` by default. An explicit request from the user ("the exam in English", "in Spanish this time") overrides that default for this exam. Chat with the user in the language the user writes in.

## Where it's written

`topics/<topic-slug>/exams/<exam-slug>/exam.json`

- The topic slug is the name of a folder that already exists in `topics/`. List them before writing; don't invent new folders.
- A topic can be a book, a certification, documentation or a course. Look at the `type` field in its `topic.json`: it changes how questions are written (see below).
- The exam slug follows the topic's unit: `ch-01` for a book, `domain-02` for a certification, `<service>` for documentation — it's a **folder** name, the file inside is always called `exam.json`.
- If the user doesn't say which topic or unit it's for, infer it from the content. If it's still ambiguous, ask once.
- If the folder already exists: ask whether to replace it or create `ch-NN-b`.

## Format

```json
{
  "title": "FoSA — Ch 2: Architectural thinking",
  "questions": [
    {
      "type": "multiple_choice",
      "q": "Question text.",
      "options": ["A", "B", "C", "D"],
      "answer": 2,
      "explanation": "Why C is correct and why the other three fall short."
    },
    {
      "type": "open",
      "q": "Explain when a topic is preferable to a queue and why.",
      "rubric": ["Mentions extensibility/coupling", "Mentions security/wiretap", "Gives a decision criterion, not just a list of pros/cons"]
    }
  ]
}
```

`type` can be `multiple_choice` (default if missing, so older exams stay valid), `open`, `oral` or `practical`. `multiple_choice` carries `options`/`answer`/`explanation` as always. The other three have no `answer`: they carry a `rubric`, 3-5 short, checkable points (not a single model answer — a rubric allows grading paraphrase). `oral` is the same as `open` except the answer is captured by voice. `answer` is a 0-based index. `multiple_choice` always has 4 options. `exam.html` shuffles the questions itself, don't order them yourself.

## Which question types to include

Before writing a single question, ask with `AskUserQuestion`
(multiSelect) which types go into this exam — don't assume they want all
four: they may not have a microphone or may not want to record oral answers.

- Options: `multiple choice`, `open`, `oral`, `practical`.
- Default preselection according to the distribution rule below: `multiple
  choice` and `open` checked; `oral` and `practical` unchecked, unless the
  topic is clearly practical/oral (`type: "practice"`, or a language), in
  which case check them by default too.
- Distribute only among the types they confirmed. If they chose just one, the
  exam is 100% that type.
- `oral` is answered by recording audio (same mechanism as the notebook
  dictation); `notes-grade` grades it on the transcription, just like
  `open`.

## How questions are written

10 to 15 questions per chapter. Distributed like this:

- ~30% definitions and precise vocabulary from the chapter.
- ~40% application: a concrete scenario, what should be done.
- ~30% trade-offs and counterexamples: what you pay for choosing X, when X is the wrong choice.

Lean toward application and trade-offs. The goal is understanding, not reciting.

**Type distribution**: among the types confirmed in the question above,
default 60% `multiple_choice` / 40% `open` when both are
included. If `oral`/`practical` are also included, fit them in by splitting
the 40% non-MC share instead of adding a new percentage.

**Depending on the topic's `type`:**

- `book` — the distribution above as is.
- `certification` — imitate the real exam. For AWS Cloud Practitioner (CLF-C02):
  multiple choice with one correct answer and three distractors, or multiple
  response with two correct answers out of five options. Short scenario questions,
  not definition questions. Respect each domain's weight if you build a full mock exam.
- `documentation` — questions about when to use what and what limits it has, not about
  parameter names. Documentation gets looked up; what has to be known by
  heart is the selection criterion.
- `course` — follow the course unit.

### How options are built (`multiple_choice`)

Balanced options are not achieved by auditing at the end: by then the
tell is already in. Build them so the parity comes out on its own.

1. **Every option is a bare statement, with no justification.** The number one
   tell is the correct one carrying its own reasoning ("…, because it keeps
   coupling low") while the other three are bare: it ends up longer and more
   specific. Zero "because" in the options — all the reasoning goes in
   `explanation`, which only appears after answering.
2. **Write the correct statement first and then mutate it into each distractor.**
   Take a real confusion or an easily confused neighbor and write what
   someone holding it would claim, with the *same* skeleton, the same grain and the
   same register. That way the four options are "the statement under some
   belief" and the correct one is the statement under the correct belief.
   Parallelism comes out by construction instead of having to be policed.
3. Each distractor must be a mistake the user could genuinely make — so
   which one they pick is diagnostic — but unambiguously wrong: tempting, not
   tricky.
4. **No asymmetric bold.** Don't highlight the concept you're testing
   only in the correct option: that gives it away instantly. Either nothing in bold, or the
   parallel term in all four.

If reading the four cold you can guess which one it is without knowing the topic, you
skipped step 1 or 2: regenerate it, don't patch it.

Quality rules, non-negotiable:
- Spread `answer` across 0, 1, 2 and 3. Don't leave it concentrated on one index.
- Forbidden: "all of the above", "none of the above", "A and C", double negatives.
- One question tests a single idea.
- The `explanation` says why the correct one is correct **and** what confusion each distractor represents. It's the part that teaches: if it's a single generic line, it's badly written.
- Everything comes from the content the user pasted. If something is needed and isn't in the material, don't invent it: flag it separately.

### How the `rubric` is written (`open`/`oral`/`practical`)

3 to 5 short points, each one **checkable** in the answer (something you can
mark ✓/✗ by reading it), not a model answer. A rubric point names a
concrete concept or criterion ("mentions the security/wiretap problem"),
never something vague ("understands the topic well"). Just like in `multiple_choice`, everything
comes from the content the user pasted.

## Diagrams and formulas in questions

`exam.html` renders fences inside `q`, each option and `explanation`.
Useful for architecture questions ("given this diagram, what fails?") and for
percentiles and complexity.

```json
{
  "q": "Given the flow:\n\n```mermaid\ngraph LR\n  A[API] --> B[(DB)]\n```\n\nWhere is the temporal coupling?",
  "explanation": "..."
}
```

They go as text inside the JSON string, so line breaks are `\n` and in
`math` LaTeX backslashes are escaped double (`\\frac`). Use them only when the
drawing adds something prose doesn't: a decorative diagram adds noise and one more
chance of being wrong.

## After writing

1. Validate the JSON: `python3 -m json.tool topics/<slug>/exams/<exam-slug>/exam.json > /dev/null`
2. For each `multiple_choice` question: check that `answer` is between 0 and 3, that it
   has 4 options, and that `answer` isn't concentrated on one index. For each
   `open`/`oral`/`practical`: check that it has a `rubric` with 3-5 points.
3. Tell the user the path and to open it with `npm run app`.
4. If the exam has non-MC questions, let them know that after taking it they'll need to
   run `notes-grade` on the attempt — `exam.html` can't grade
   `open`/`oral`/`practical` on its own.
5. Don't record anything in `progress/log.md` when creating the exam: that's done by
   `notes-grade` when the user takes the exam and grades the attempt, not before.

For a spaced review that mixes topics instead of a single-chapter exam,
the skill is `notes-review`, which reuses these same construction rules.
