---
name: slp-init
disable-model-invocation: true
description: Registers a new study topic — interviews the user to fill in topic.json, creates the folder structure, progress files and wiki, writes learning.md with the Mission, runs the first quiz (ping-pong level diagnostic) with slp-quiz and offers to generate the topic's teacher persona. Use when the user says "I want to start studying X", "create a new topic", "add a topic", "/slp-init".
---

# New topic

A topic is a self-contained folder `topics/<slug>/`. This skill leaves it
ready so the first session starts with a clear Mission and a measured level.
Every format named here is in
[formats.md](../../reference/formats.md).

## 1. Interview

With `AskUserQuestion`, in a few rounds. Ask about **every** field, even if
the answer is "none":

- `title`, `subtitle`.
- `type`: `book`, `certification`, `documentation`, `course` or `practice`
  (what each changes: [formats.md § topic.json](../../reference/formats.md#topicjson)).
- `area`: first list the `area` values already in `topics/*/topic.json` and
  offer them. Free text, kebab-case, reuse an existing value when it fits.
- `goals` (1-3, concrete: "be able to justify X by trade-offs", not
  "understand X") and `reason` (what changes once they have it). Vague answers:
  ask again. They are the Mission.
- `language`: `source` (the material), `notes` (notes, summaries, lessons),
  `exams` (exams, exercises, feedback). Tell them these are defaults an
  explicit request overrides.
- `routine` (`cadence`, `session`) and `end_date` (`YYYY-MM-DD`).
- The unit list, if they have it (chapters, domains, modules): it goes to
  `status.md` → Up next.
- `links` and initial local resources, following
  [sources.md](../../reference/sources.md). For each `path` outside the topic,
  offer to copy the file into `resources/` (then it needs no `links` entry);
  if they decline, keep the `path`. A missing path: warn in one line, keep
  going.
- `sources_mode`: offer the default from `profile` in `settings.json` at the
  repo root: `offline` → `local`; `online` → `both`; `auto` or no file →
  `both` if you have web access now, `local` if not.

Slug: kebab-case of the title (`the-pragmatic-programmer`). If the folder
exists, stop and ask. `order`: the next free one.

## 2. Generate the filesystem

```
topics/<slug>/
  topic.json
  learning.md               Mission written, Glossary and Record empty
  resources/  notes/  exams/  exercises/
  wiki/index.md             okf_version + empty "# Concepts" and "# Sources"
  progress/status.md  progress/log.md  progress/sessions.jsonl (empty)
```

- `topic.json`, `status.md`, `log.md` (all four tables with headers only) and
  `wiki/index.md` exactly as in formats.md.
- `learning.md`: the Mission from `reason` + `goals` (and what's out of scope,
  if they said so), so the first lesson doesn't ask again.

Don't invent data: an empty field beats an invented one.

## 3. First quiz

Run `slp-quiz` on the new topic. It builds `exams/quiz/`, runs the
ping-pong in the chat and writes the first Record entry. If the topic is
completely new to them, it can be short: 2-3 questions that confirm it.

## 4. The topic's teacher persona

Optional: a way to run `slp-teach` with more domain character. The main agent
reads the file and teaches as that persona **in the same conversation**; it is
not a subagent (a subagent can't ask questions or wait for approval). The
memory stays in `learning.md`.

1. If `agent/agents/teacher-<slug>.md` exists, nothing to do.
2. Otherwise offer it with `AskUserQuestion`, **default yes**. If they decline,
   write `"teacher": false` to `topic.json`.
3. Design the persona **for this topic**: who would teach this in real life?
   A literature book calls for a literature teacher, *Fundamentals of Software
   Architecture* for a senior architect who teaches, an AWS certification for
   an instructor of that cert. Never a generic "<area> teacher".
4. Write `agent/agents/teacher-<slug>.md`:

```md
---
name: teacher-<slug>
description: Teaching persona for the "<slug>" topic, adopted by the main agent while running slp-teach. Not for delegation.
---

You are <concrete persona>: <2-3 sentences on what you master, the vocabulary
you use and the judgment you apply, anchored in this topic>.

Your memory of the learner is `topics/<slug>/learning.md`. Read it first.

## How you teach

Follow `agent/skills/slp-teach/SKILL.md` in full, with your personality. It is
the same process, not a parallel one.

- Never give the answer before they try: ask what they tried and where they
  got stuck, then guide them to discover it.
- Never from memory: verify every doubtful fact with the `researcher` agent.
- Sources and conflicts follow `agent/reference/sources.md`.
- Typical traps in this topic: <1-2 frequent misconceptions>.

## What you don't do

Write outside `topics/<slug>/`, invent sources, or solve before they try.
```

5. Check before saving: specific to this topic? forbids solving before the
   attempt? ties fact-checking to `researcher`? uses `learning.md` as memory
   without keeping its own state?

Older topics without a persona are offered one by `slp-session`.

## 5. Wrap up

A few lines: where everything ended up, the quiz edges, and **one**
first step: read and `slp-summarize`, or `slp-teach` if they already have a
foundation. Then: "Start each study session with `slp-session`."
