# File formats

Every file a skill reads or writes under `topics/<slug>/`. Skills link here
instead of restating formats. `topics/example/` is a valid instance of each
one and `app/tests/test_example.py` checks it against this page.

Everything is plain JSON and Markdown, so the learner can write any of it by
hand, without an agent: a topic, notes, cards, an exam, an exercise. Skills
only guide the process. What needs the agent is the judgment: teaching,
grading and feedback, interpreting sessions, progress and the wiki. The app
records sessions on its own.

General rules:

- Dates are `YYYY-MM-DD`, never relative. Minutes are `YYYY-MM-DDTHHmm`
  (`2026-09-25T1810`) in file names and ids, `YYYY-MM-DDTHH:MM` inside JSON.
- An empty field beats an invented one. Missing data: ask once, all together.
- Slugs are kebab-case: lowercase ASCII, accents stripped, every run of other
  characters becomes one `-` (the same rule as `text.slug` in
  `app/server/text.py`).

```
topics/<slug>/
  topic.json
  learning.md
  resources/                     raw sources, never edited by skills
  notes/NN-<slug-of-h1>.md
  wiki/index.md  wiki/concepts/  wiki/sources/
  exams/<exam>/exam.json  exams/<exam>/attempts/
  exercises/<exercise>/prompt.md  exercises/<exercise>/attempts/
  cards/cards.json  cards/reviews.jsonl
  progress/status.md  progress/log.md  progress/sessions.jsonl
```

## topic.json

```json
{
  "title": "HTTP basics", "subtitle": "…", "type": "documentation",
  "area": "web", "order": 4,
  "goals": ["…"], "reason": "…",
  "language": { "source": "en", "notes": "es", "exams": "es" },
  "routine": { "cadence": "…", "session": "…" }, "end_date": "YYYY-MM-DD",
  "sources_mode": "both",
  "links": [{ "title": "…", "url": "https://…" }, { "title": "…", "path": "~/Books/x.pdf" }]
}
```

| Field | Type | Notes |
|---|---|---|
| `title`, `subtitle` | string | shown in the app |
| `type` | enum below | missing = `book` |
| `area` | string | kebab-case, reuse existing values; tone and vocabulary context only |
| `order` | int | position in the app lists |
| `goals` | list of 1-3 strings | concrete; with `reason` they are the Mission |
| `reason` | string | what changes once they have it |
| `language` | `{source, notes, exams}` | defaults per output, see `AGENTS.md` |
| `routine` | `{cadence, session}` | may be empty strings |
| `end_date` | `YYYY-MM-DD` or `""` | |
| `sources_mode` | `web` \| `local` \| `both` | missing = `both`; see [sources.md](sources.md) |
| `links` | list | Sources: `{title, url}` (http/https) or `{title, path}`. The name `links` is historical |
| `teacher` | `false` (optional) | the user declined a teacher persona; don't offer it again |

`type` decides how exams and exercises are written:

| `type` | Exam style | Default exercise format |
|---|---|---|
| `book` | 30% definitions, 40% application, 30% trade-offs | apply, critique |
| `certification` | imitate the real exam: short scenarios, one correct answer, domain weights | apply |
| `documentation` | when to use what and its limits, never parameter names | build |
| `course` | follow the course unit | build |
| `practice` (languages, instruments, sports) | oral and practical by default | teach (spoken), build |

## Units

A **unit** is the topic's own division: a chapter, a certification domain, a
course module, a documentation section. It is named `NN — <title>` with a
two-digit number (`01 — methods and status codes`). `NN` prefixes the exams
and notes that cover it.

## learning.md

```md
# Learning — <topic title>

## Mission

Why they study this, concretely, what changes in their work, what is out of scope.

## Glossary

**Idempotent**: a request that leaves the server in the same state whether sent once or many times.
_Avoid_: repeatable, retry-safe

## Record

### 0002 — 2026-09-23 — Mixed up 404 and 503 under load — corrected
Evidence and what to check next.

### 0001 — 2026-09-22 — Declared prior knowledge: GET and POST
…
```

- **Mission**: from `goals` + `reason`. When it changes, confirm with the user, update it and add a Record entry.
- **Glossary**: a term goes in only once the user can use it well. One or two sentences on what it *is*; pick one word and list the rest under `_Avoid_`.
- **Record**: entries numbered `0001` upward, newest first, title `NNNN — YYYY-MM-DD — <what>`. Write one only when one of these happened (covering a topic is not one):
  1. They demonstrated non-trivial understanding (evidence, not exposure). New floor.
  2. They declared prior knowledge, with the depth they claimed.
  3. A misconception was corrected (title ends in `— corrected`).
  4. The Mission moved.
  5. A source conflict was resolved: title `Source choice: <claim>`, body exactly three lines `Taught:` / `Not taught:` / `Why:` ([sources.md](sources.md)).
- A new entry that contradicts an old one: add `Superseded by NNNN` to the old one, never delete it.

## Notes

- One file per h1: `notes/NN-<slug of its h1>.md`, `NN` = its position (01, 02…). The app rewrites the folder with exactly this rule on every save, so any other name gets renamed.
- A single `# ` per file. Sections `##`, subsections `###`, lists `- `.
- **No nested lists**: the app flattens them on save. Use a `###` or a second flat list instead.
- GFM pipe tables, links, inline code and code blocks survive a save. Tables: one header row, one separator row (the app writes `| --- | --- |`), then rows, with no blank lines between them.
- Notes saved from the app escape some characters as HTML entities (`&#42;` for a literal `*`, `&lt;` for `<`, `&#35;` for a leading `#`). Read them as those characters and keep them as they are when editing.
- ```` ```mermaid ```` and ```` ```math ```` (KaTeX, display only) fences render in the app. Images live in `notes/img/`.
- Raw HTML already in a note (`<mark>`, comments, margin notes) is left as is.
- **Refer to a note by its headings, never by file name**: `Methods and status codes › Status codes`. File names change when notes are inserted or retitled.

## Exams

`exams/<exam>/exam.json`. The folder name is the exam's id:

| Kind | Folder | Written by |
|---|---|---|
| unit exam | `<NN>-<kebab-title>` (`01-methods-and-codes`); a second exam on the same unit `<NN>-<kebab-title>-b` | `slp-exam` |
| quiz | `quiz` | `slp-quiz` |

```json
{
  "title": "HTTP — 01: methods and codes",
  "questions": [
    { "type": "multiple_choice", "q": "…", "options": ["…", "…", "…", "…"], "answer": 1, "explanation": "…" },
    { "type": "open", "q": "…", "rubric": ["…", "…", "…"] }
  ]
}
```

- `type`: `multiple_choice` (default when missing), `open`, `oral`, `practical`.
- `multiple_choice`: exactly 4 `options`, `answer` = 0-based int, `explanation` required.
- `open` / `oral` / `practical`: `rubric` with 3-5 checkable points, no `answer`. `oral` is answered by voice.
- `q`, options and `explanation` may hold mermaid/math fences as `\n`-escaped text, LaTeX backslashes doubled.
- Quiz only: top level `"kind": "quiz"`; per question `"thread"` and `"level"` ([§ Quiz](#quiz)).
- **Never replace or reorder an exam that has an `attempts/` folder**: attempts point at questions by index. Create `<exam>-b` instead. Validate with `uv run python -m json.tool <file> > /dev/null`, then check the rules above.

Guidance on writing questions: [graded-questions.md](graded-questions.md).

## Attempts

`attempts/<date>.<ext>` where `<date>` is `YYYY-MM-DDTHHmm`, plus `-2`, `-3`… when two land in the same minute.

**Exam attempt** (`.json`, written by the app):

```json
{ "exam": "01-methods-and-codes",
  "answers": [
    { "i": 0, "type": "multiple_choice", "chosen": 1 },
    { "i": 4, "type": "open", "text": "…" },
    { "i": 5, "type": "oral", "audio": "2026-09-23T1030-p5.webm" } ] }
```

- `i` = 0-based position of the question in `exam.json`, whatever order it was shown in. `type` is copied from the question.
- `chosen` (MC), `text` (open, practical, oral written fallback) or `audio` (oral: a file `<date>-p<i>.<ext>` next to it, not an attempt).
- `"mode": "chat"`: a quiz run in the chat and written by `slp-quiz`.

**Exercise attempt**: any file `exercises/<exercise>/attempts/<date>.<ext>` (`.md` for prose, the language's extension for code).

**Correct or missed** (used by quizzes): MC is correct when `chosen == answer`; open/oral/practical when its feedback section has no ✗. An unanswered question is a miss.

## Feedback

`attempts/<date>.feedback.md` next to the attempt, for exams and exercises. **An attempt is pending until this file exists.** Written by `slp-grade` (and `slp-quiz` for quizzes run in the chat).

```md
# Attempt — 01-methods-and-codes — 2026-09-23 10:30

**MC:** 3/4 · **Rubric points:** 2/3

## [03] Multiple choice — overloaded server
✗ Picked 404. … See *Methods and status codes › Status codes*.

## [05] Open — retrying PUT vs POST
✓ …
✗ … No note covers it yet: a gap in the notes, not in the student.
Feedback: …

## What to improve
- …
```

- `[NN]` = `i + 1`, two digits. Only missed or non-MC questions get a section.
- Score line uses the same numbers as `log.md`: `**MC:** correct/total · **Rubric points:** met/total`. Exercises: `**Prompt criteria:** met/total`. Quiz: a table `| Thread | Edge level |`.
- Each ✗ says what is missing and the note heading that covers it, or says no note covers it.

## Exercises

`exercises/<kebab-slug>/prompt.md`:

```md
# Exercise — Pick the status code

**Format:** apply · **Unit:** 01 · **Rests on:** Methods and status codes › Status codes

The task, with conditions that can be checked one by one.

**Submit:** a `.md` with …
```

`Format` ∈ apply, build, critique, teach. The conditions are the grading criteria.

## Cards

Flashcards made from the learner's notes. `cards/cards.json` is written by
`slp-cards` or by hand in the app; `cards/reviews.jsonl` only by the app (the
`3 cards` tab).

```json
[
  { "id": "put-idempotent", "front": "Why is PUT idempotent?",
    "back": "It replaces the whole resource, so repeating it leaves the same state.",
    "note": "Methods and status codes › Methods" }
]
```

- `id`: kebab-case, unique in the topic, stable forever (reviews join on it). Never reuse an id for a different fact; to retire a card, delete it.
- `front`: a question. `back`: at most 2 sentences. Plain text; inline `**`/`*` and `$…$` LaTeX are fine.
- `note`: the heading path of the note it came from (`H1 › H2`), never a file name.
- `by` (optional): `"user"` for a card written by hand in the app. `slp-cards` never edits or deletes those; missing = written by `slp-cards`.
- `flagged` (optional, boolean): `true` when the learner marked the card **unsure** after revealing it in the app: they got it but doubt it, or want to dig deeper. Only the app sets it to `true`; the agent sets it to `false` after going over the concept with the learner. Editing a card keeps the flag.

```jsonl
{"at":"2026-09-26T10:04","id":"put-idempotent","recall":"good"}
```

- Append-only, one line per rating. `recall` is `again` ("didn't know") or `good` ("knew it"), self-graded after the learner answers to themselves and reveals the back; `at` is local time `YYYY-MM-DDTHH:MM`.
- Lines whose `id` is not in `cards.json` are ignored.

**Scheduling** (Leitner, derived, no state file): a card's streak is the number of `good` since its last `again` (all of them if it was never `again`). Box = min(streak, 3). Interval by box: 0 → 0 days, 1 → 1, 2 → 3, 3 → 7. A card is **due** when it has no reviews, or now ≥ its last review `at` + interval.

## progress/status.md

Rewritten, not accumulated.

```md
# Status — <title>

**Updated:** YYYY-MM-DD

- **Current unit:** 01 — methods and status codes
- **Summary written:** yes
- **Next exam:** —

## Up next
- [ ] …
```

## progress/log.md

The human summary. Append rows at the end of a table; create a missing section; never delete rows.

```md
# Log — <title>

## Reading
| Date | Unit | Summary | Exam (score) |
|------|------|---------|--------------|

## Exams
| Date | Exam | MC | Rubric | Attempt |
|------|------|----|--------|---------|

## Exercises
| Date | Exercise | Format | Criteria | Attempt |
|------|----------|--------|----------|---------|

## Quizzes
| Date | Edges | Attempt |
|------|-------|---------|
```

| Table | Written by | When |
|---|---|---|
| Reading | `slp-session` §Unit done | the learner confirms a unit is finished. `Summary` = yes/no, `Exam (score)` left `—` |
| Exams, Exercises | `slp-grade` | after grading; also fills `Exam (score)` of the unit's Reading row |
| Quizzes | `slp-quiz`, or `slp-grade` for a quiz sat in the app | after a run. `Edges` = `thread L3, thread L2` |

`Attempt` is the path relative to the exam or exercise folder (`attempts/2026-09-23T1030.feedback.md`).

## progress/sessions.jsonl

The record of study sessions. A **session** is a block of time holding a list
of activities. Append-only, one JSON object per line; `start` and `end` lines
are never rewritten.

```jsonl
{"id":"2026-09-26T1010","event":"start","at":"2026-09-26T10:10","by":"app"}
{"id":"2026-09-26T1010","event":"activity","at":"2026-09-26T10:12","kind":"reading","by":"app","detail":"notes/01-methods-and-status-codes.md"}
{"id":"2026-09-26T1010","event":"activity","at":"2026-09-26T10:40","kind":"teaching","by":"agent","detail":"idempotency keys"}
{"id":"2026-09-26T1010","event":"end","at":"2026-09-26T11:02","by":"hook"}
{"id":"2026-09-26T1010","event":"correct","at":"2026-09-26T18:00","by":"agent","end_at":"2026-09-26T10:41","outputs":["notes/02-idempotency-keys.md"],"note":"hook closed at 11:02 but last activity 10:40"}
```

- `id` = the start minute `YYYY-MM-DDTHHmm`; every line of the session repeats it. `at` is `YYYY-MM-DDTHH:MM`.
- `event` ∈ `start`, `activity`, `end`, `correct`. `by` ∈ `app`, `agent`, `hook`, `idle`.
- `activity`: `kind` ∈ `reading`, `teaching`, `summary`, `cards`, `practice`, `exam`, `quiz`, `feedback`, plus `detail` (one line: a file, an exam, a concept, a count).
- `end`: optional `outputs` (paths relative to the topic) and `note` (one line).
- `correct`: written by the agent when it validates a session (`slp-session` §1). `end_at`, `outputs` and `note` override the end's for every reader.
- **Open** = a `start` with no `end` of the same `id`. At most one open session per topic.
- **Idle rule** (30 minutes): an open session whose last line is older than 30 minutes is closed with `{"event":"end","by":"idle","at":<that last line's at>}` before anything else is appended. The app applies it on every activity and `uv run slp sessions` applies it too.
- **Validated** = the session has a `correct` line, or its `end` is `by: "agent"`.

Who writes:

| Writer | What |
|---|---|
| app | opens a session on any activity in a topic with none open; logs `reading` (notes saved, at most one per 10 minutes; source added), `cards` (`N reviewed, M again`), `exam` / `quiz` (attempt saved); the start/stop control in the statusline writes `start` / `end` |
| skills | one `activity` when they work on a topic, opening a session (`by: "agent"`) only if none is open |
| `slp-session` | `end` when the learner says they're done; `correct` when validating |
| `uv run slp sessions close` (agent hook) | `end` with `by: "hook"` for every open session |

## Wiki

`wiki/` is the agent's own map of the subject, an [OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf) bundle following the llm-wiki pattern, plus which concepts have been studied and in which session. `notes/` is the learner's writing and `learning.md` what they demonstrably know. The app doesn't show it.

```
wiki/
  index.md             catalog, one line per page
  concepts/<kebab>.md  type: Concept, one idea per file
  sources/<kebab>.md   type: Source, one per ingested resource, link or chapter
```

```md
---
type: Concept
title: Idempotency
description: A request that leaves the server in the same state whether sent once or many times.
depends_on: [/concepts/safe-method.md]
studied: [2026-09-22T1700, 2026-09-26T1010]
generated: { by: slp-teach/<model>, at: 2026-09-22T18:30:00Z }
sources:
  - id: mdn
    resource: https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview
    title: "MDN: Overview of HTTP"
---

# Definition

N identical requests leave the server as one does.[^mdn]

# Depends on

- [Safe method](/concepts/safe-method.md): every safe method is idempotent.

# Common confusions

Idempotent doesn't mean "same response".

[^mdn]: MDN: Overview of HTTP
```

- Frontmatter: `type` (`Concept` or `Source`), `title`, `description` (one sentence, also used in the index) are required; Concepts also carry `depends_on` (list, may be empty). `generated: {by: <skill>/<model>, at: <ISO datetime with Z>}` is refreshed on every meaningful edit; `sources` lists `{id, resource, title}` when a claim comes from a source. Optional: `tags`, `status: draft`, `studied`.
- `studied` (Concepts): the ids of the sessions in which the learner studied this concept, oldest first, each once. Missing or empty = not studied yet. The session id is the date; `sessions.jsonl` says how.
- Cite each sourced claim with a footnote keyed by `sources[].id`. `resource` is a URL, or a path relative to the page for `resources/` files (`../../resources/x.txt`).
- Links and `depends_on` are bundle-relative (`/concepts/x.md`). A link to a page not written yet is fine.
- The path is the identity: never rename a page. Retire it with `status: deprecated`.
- Update before you create: search `index.md` first; one concept per file.
- Every write updates `index.md` in the same turn. `index.md` has no frontmatter except `okf_version`:

```md
---
okf_version: "0.2"
---
# Concepts

* [Idempotency](concepts/idempotency.md) - A request that leaves the server in the same state whether sent once or many times.

# Sources

* [MDN: Overview of HTTP](sources/mdn-http-overview.md) - What HTTP is, its message shape and its methods.
```

- The only learner state is `studied`: no scores, no "the user knows X" (that is the `learning.md` Record). The one learner-derived section allowed is an anonymous `# Common confusions`.
- Source conflicts: the page states the chosen version and cites it; the decision itself goes to the `learning.md` Record.
- Written in `language.notes`; frontmatter keys stay in English.

| Writer | When |
|---|---|
| `slp-teach` | end of a lesson: one Concept per node taught, `depends_on` from the plan, session added to `studied` |
| `slp-summarize` | after summarizing: one Source page, plus the Concepts it touches, session added to their `studied` |
| `slp-session` | validating or ending a session with `reading` activity: the Concepts covered by the notes changed in it, session added to their `studied` |
| caller of `researcher` | files verified findings into the matching Concept with their citation |

`slp-init` creates `wiki/index.md` with empty sections. Readers: `slp-session` (progress), `slp-teach` phase 2, `slp-exam`, `slp-exercises`, `slp-quiz`.

## Quiz

The repeatable diagnostic: the ping-pong `slp-init` runs first, run again with
`slp-quiz` to compare. `exams/quiz/exam.json`: a normal exam plus
`"kind": "quiz"`, and every question carries `"thread"` (a prerequisite line,
kebab-case) and `"level"` (1-5 difficulty). Aim for 3 levels × 1-2 questions
per thread. Existing questions are never edited or reordered; the bank grows by
appending higher levels. Run in the chat, its attempts carry `"mode": "chat"`;
the app can also sit it as a plain exam.
