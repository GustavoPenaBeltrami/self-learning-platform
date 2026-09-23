---
name: notes-init
description: Registers a new study topic — interviews the user to fill in topic.json, creates the folder structure and progress files, writes learning.md with the Mission, runs a level diagnosis in the terminal and offers to generate the topic's dedicated teacher agent. Use when the user says "I want to start studying X", "create a new topic", "add a topic", "/notes-init" (or in Spanish: "quiero empezar a estudiar X", "creá un tema nuevo", "agregá un tema").
---

# New topic

A topic is a self-contained folder in `topics/<slug>/`. This skill leaves it
ready so the first session starts with a clear mission and the level already
measured.

## 1. Interview

With `AskUserQuestion`, in a few rounds. Every field is **mandatory to
ask about** (even if the answer can be "none"):

- `title`, `subtitle`.
- `type`: `book`, `certification`, `documentation`, `course` or `practice`.
- `area`: **before asking**, list the `area` values that already exist in
  `topics/*/topic.json` and offer them as options. Free text but canonical, in
  kebab-case: don't create `software_architecture` if
  `software-architecture` already exists.
- `goals` (1-3, concrete: "be able to justify X by trade-offs", not
  "understand X") and `reason` (what changes in their work or life once they
  have it). If they come back vague, ask again until they're concrete: they
  are the Mission.
- `language`: the default language for each kind of output — `source` (the
  language of the material), `notes` (notes, summaries and lessons), `exams`
  (exams, exercises and grading feedback). Tell the user these are only
  defaults: an explicit request ("exam in English", "explain in Spanish")
  overrides them for that output.
- `routine` (`cadence`, `session`) and `end_date` (YYYY-MM-DD: when they want
  to finish).
- `links` (Sources) and initial local resources. A source is a URL
  (`{ "title", "url" }`) or a path to a file anywhere on disk
  (`{ "title", "path" }`). `resources/` is always a source without being
  declared. For each path outside `topics/<slug>/`, offer with
  `AskUserQuestion` to copy the file into `resources/` (then it needs no
  `links` entry); if they decline, keep the `path` entry. A path that doesn't
  exist: warn in one line and keep it, never stop the interview.
- `sources_mode` (`web`, `local` or `both`): where the agent looks things up.
  Offer the default from the Profile in `settings.json` at the repo root:
  `profile: "offline"` → `local`, `online` or no file → `both`.

Folder `slug`: snake_case of the title, like the existing ones
(`fundamentals_software_architecture`). If it already exists, stop and ask.
`order`: the next free one.

## 2. Generate the filesystem

```
topics/<slug>/
  topic.json
  learning.md
  resources/  notes/  exams/  exercises/
  progress/status.md  progress/log.md
```

```json
{
  "title": "…", "subtitle": "…", "type": "book", "area": "…", "order": 4,
  "goals": ["…"], "reason": "…",
  "language": { "source": "en", "notes": "es", "exams": "es" },
  "routine": { "cadence": "…", "session": "…" }, "end_date": "YYYY-MM-DD",
  "sources_mode": "both",
  "links": [{ "title": "…", "url": "…" }, { "title": "…", "path": "~/Books/…pdf" }]
}
```

`progress/status.md`:

```md
# Status — <title>
**Updated:** YYYY-MM-DD
- **Current unit:** —
- **Summary written:** no
- **Next exam:** —
## Up next
- [ ] …
```

`progress/log.md`:

```md
# Log — <title>
## Reading
| Date | Unit | Summary | Exam (score) |
|------|------|---------|--------------|
## Review
| Date | What I reviewed | Result |
|------|-----------------|--------|
```

`learning.md`: the `notes-teach` format (Mission / Glossary / Record), with
the **Mission already written** from `reason` + `goals` (and what's out of
scope if they said so), an empty Glossary, and the Record with what came out
of step 3. That way the first `notes-teach` session doesn't ask for it again.

Dates always `YYYY-MM-DD`. Don't invent data the user didn't give: an empty
field beats an invented one.

## 3. Ambulatory diagnosis

In the terminal, without saving an `exam.json`: it's for locating the level,
it's not reproducible or bankable.

- Use the probing mechanics of `notes-teach` phase 1a — graded questions
  with `AskUserQuestion`, grading in the following message, binary search
  for the edge bounded from both sides, the same option-construction rules —
  but on the **overall level of the topic**, not a specific lesson. About
  5-8 questions are enough; if the topic is completely new to them, 2-3 that
  confirm it.
- If you're unsure about a fact in the questions, verify it with `researcher`.
- Write the result in the `Record` of `learning.md`: what they claimed to know
  and how deeply, where the edge ended up, and any misconception that came up.

## 4. The topic's teacher agent

One agent per **topic**, not per area: each topic has its own persona,
designed to fit its actual content, not a generic area template — a
literature book calls for a literature/Spanish-language teacher,
*Fundamentals of Software Architecture* calls for a senior architect who
teaches, an AWS certification calls for an instructor for that cert. It's
optional: a way to run `notes-teach` with more domain character. The memory
stays in the topic's `learning.md`; the agent keeps no memory of its own.
`area` still exists in `topic.json` as context/tone data (§2.1 of
`plan.md`); it no longer bounds the agent's scope.

1. If `agent/agents/teacher-<topic-slug>.md` already exists, there's nothing
   to do.
2. If it doesn't, offer it with `AskUserQuestion`, **default yes** — don't
   assume it implicitly, but don't cool it down with an unbiased "do you want
   one?" either: it's the expected default.
3. If the user accepts, design the persona **for this specific topic**: look
   at the `title`/`subtitle`/`type` just filled in and pick who would teach
   this in real life. Never a generic "<area> teacher".
4. Write `agent/agents/teacher-<topic-slug>.md`, with the same frontmatter as
   `researcher.md` (`name`/`description`/`tools`/`model`):

```md
---
name: teacher-<topic-slug>
description: <concrete persona> specialized in <topic title>. Teaches this topic following notes-teach, with the tone and judgment of <who>. Use for lessons, explanations or grading on the "<topic-slug>" topic.
tools: Read, Grep, Glob, Write, Edit, WebSearch, WebFetch
model: inherit
---

You are <concrete persona>: <2-3 sentences on what you master, what vocabulary
you use and what judgment you apply — anchored in this specific topic, not in a
generic area>.

You work in an isolated context: everything you know about the person is in
the task you were given and in `topics/<topic-slug>/learning.md`. Always read
it before teaching.

## How you teach

Follow `agent/skills/notes-teach/SKILL.md` in full: the two principles,
probe → plan → teach, the rules for graded questions, where the lesson ends
up. It's not a parallel process: it's the same one with your personality.

- **Never give the answer before they try.** Ask what they tried, where they
  got stuck, and guide them to discover it — never solve it yourself first.
- **Never from memory.** Every doubtful fact is verified with the
  `researcher` subagent before you say it.
- **Sources follow `sources_mode`.** Read `topic.json` `sources_mode` and
  `links` (URLs and local `path`s) plus `resources/`. With `local`, or with no
  connection, use only local sources and say plainly "not verified on the web"
  for anything you couldn't check there. A missing path: warn and continue.
- **When sources disagree, you decide.** Apply the `notes-teach` rule: the
  topic's material wins unless outdated for the Mission, cite what you used,
  record it in the Record — don't flag the conflict in the chat.
- Typical traps in this topic: <1-2 frequent misconceptions, if any>.

## What you don't do

You don't write outside `topics/<topic-slug>/`. You don't invent sources. You
don't give the answer before they try.
```

5. **Quick check before saving** (4 questions, don't overload it):
   - Is the persona specific to this topic, not a generic area?
   - Does it explicitly forbid solving before the student tries?
   - Does it tie fact-checking to `researcher`, never to memory?
   - Does it use the topic's `learning.md` as memory, without duplicating its
     own state?
6. **Existing topics without a teacher**: if `topics/*/topic.json` has other
   topics already registered without `agent/agents/teacher-<slug>.md`, there's
   no need to solve it here — `/notes-session` detects them when surveying
   state and offers them with the same criterion, so old topics get one
   without re-running `notes-init` for each.

**Pedagogical basis for point 4** (researched before writing the template,
not blindly): Khanmigo's Socratic tutor never solves — it asks what the
student tried and guides them to discover it; OpenAI's *study mode* manages
cognitive load with scaffolded questions instead of the direct answer;
Claude's *Learning* mode asks one exploratory question at a time before
answering. All three agree on the rule above: never give the answer before
the attempt.

**Sources**: [Khanmigo — Socratic approach](https://aicompetence.org/ai-socratic-tutors/),
[OpenAI — Introducing study mode](https://openai.com/index/chatgpt-study-mode/),
[Claude Learning Mode vs ChatGPT Study Mode (Tom's Guide)](https://www.tomsguide.com/ai/claudes-new-learning-modes-take-on-chatgpts-study-mode-heres-what-they-do).

## 5. Wrap up

Show in a few lines where everything ended up, what came out of the
diagnosis, and **one** suggested first step: read and `notes-summarize`, or
straight to `notes-teach` if they already have a foundation.
