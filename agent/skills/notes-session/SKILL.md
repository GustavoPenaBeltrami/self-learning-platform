---
name: notes-session
description: Entry point of a study session — surveys the state of every topic (overdue reviews, ungraded attempts, topics without exercises, incomplete topic.json files), asks what the user wants to do today and hands off to the right skill. Use when the user says "let's start", "what do I study today", "what's pending", "/notes-session", "I want to log that…", or opens a session with no concrete request.
---

# Session

It orchestrates; it doesn't write. This skill does not write to `progress/`:
each skill that produces an event (`notes-teach`, `notes-grade`, `notes-review`)
writes its own. If the user comes to "log that they finished chapter X", hand
them off to the skill that matches that event, or update the topic's `status.md`
following the rules of `notes-teach` if it was reading only.

## 1. Survey (don't ask anything yet)

Read from the filesystem, not from memory:

- `topics/*/topic.json` and `topics/*/progress/status.md` — what exists and
  which unit each topic is on.
- **Ungraded attempts**: every `topics/*/{exams,exercises}/*/attempts/<date>.<ext>`
  (`.json` for exams; any extension for exercises) without its companion
  `<date>.md`. Careful: in exercises the artifact itself can be `.md`; it is
  pending if it's the only file with that date.
- **Overdue reviews**: apply the Leitner-box criterion from `notes-review`
  (read that skill, don't reimplement it differently) over
  `topics/*/progress/log.md` and the attempts. Also count topics with
  everything retired whose weekly maintenance review is overdue.
- **Topics with notes but zero exercises** (`notes/*.md` exists and
  `exercises/` is empty or missing). It's a signal to show: reading without
  producing doesn't close the loop.
- **Incomplete `topic.json`**: `goals` empty/missing or `reason`
  empty/missing.
- **Topics without a teacher agent**: for each `topics/<slug>/`, check whether
  `agent/agents/teacher-<slug>.md` exists. List the ones that don't — it's a
  signal to show, not a blocker.

Show the summary in a few lines, grouped by topic, only what has something.

## 2. Complete topic.json if needed

If any topic has empty `goals` or `reason`, offer to fill them in now
(one open question per field, ungraded). If the user accepts, write them to
`topic.json` and, if `learning.md` has an empty Mission, fill it with the
same. If not, move on: it doesn't block the session.

For each topic without `agent/agents/teacher-<slug>.md` (surveyed in step
1), offer to generate it with the same criterion as `notes-init` §4 (a persona
designed for that specific topic, default yes, that section's template and
check). One at a time if there are several; it doesn't block the session if
the user says no.

## 3. Ask for the session goal

With `AskUserQuestion`, in a single round:

- **Topic(s)** — one or several; suggest the ones with pending items first.
- **What to do**:

| Option | Hands off to |
|---|---|
| Read / summarize | `notes-summarize` |
| Get taught something specific | `notes-teach` |
| Take an exam | `notes-exam` (or `exam.html` if it already exists) |
| Do an applied exercise | `notes-exercises` |
| Grade a pending attempt | `notes-grade` |
| Review | `notes-review` |
| Go over existing notes | open `topics/<topic>/notes/` in the app |
| Leave it, I'll go on alone | nothing |

## 4. Hand off

Invoke the chosen skill passing along what was already gathered (topic, current
unit, the concrete pending attempt, relevant misconception). Don't re-ask what
was already asked here.

If the destination is "Get taught something specific" and the topic has
`agent/agents/teacher-<slug>.md`, invoke that agent (`Agent`,
`subagent_type: teacher-<slug>`) instead of running `notes-teach` in the
main session — the agent follows the same process, with more domain
character.

If the user says "leave me alone" or "I'll take it from here", do nothing more.
Don't force a flow.
