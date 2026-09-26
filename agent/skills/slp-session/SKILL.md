---
name: slp-session
description: Entry point of a study session — validates the sessions recorded since the last one (corrects wrong ends, lists what was produced, feeds the wiki from notes written by hand), surveys every topic in topics/ (pending attempts, due cards, finished units missing cards, exercise or exam), asks what the user wants to do today and hands off to the right skill; also ends a session and marks a unit done. Use when the user says "let's start", "what do I study today", "what's pending", "/slp-session", "I'm done for today", "I finished chapter X", or opens a study session with no concrete request.
---

# Session

Sessions are recorded mostly by the app, behind the scenes: any activity in a
topic opens one, 30 idle minutes close it, and the statusline has a start/stop
control. The agent's job is to **interpret** them: validate what was recorded,
turn it into progress, and log its own activities. Format and idle rule:
[formats.md § sessions.jsonl](../../reference/formats.md#progresssessionsjsonl).

This skill writes `end` and `correct` lines, the `## Reading` table of
`progress/log.md`, and whatever the user accepts in step 3. Every skill logs
its work with [§Activity](#activity).

## 1. Validate

Run `uv run slp sessions`: it closes idle sessions and prints the open ones.
Without a shell, apply the idle rule yourself while reading the files.

Then, for each topic, take every closed session that is not **validated** (no
`correct` line and an `end` not written `by: "agent"`), oldest first:

1. **Window**: from its `start.at` to the next session's `start.at` (or now).
   **Evidence**: the files under `topics/<slug>/` modified inside the window,
   ignoring `progress/sessions.jsonl`, and the `at` of its own activities.
2. **Real end** = the latest evidence. Nothing changed and no activity: the
   real end is `start.at`.
3. **Discrepancy** when any holds: the recorded end is 30+ minutes after the
   real end (the hook closed it when the agent exited, long after the work),
   a file changed after the recorded end, or the end has no `outputs` while
   files changed.
4. Append `{"id":…,"event":"correct","at":<now>,"by":"agent","end_at":<real end>,"outputs":[<changed files>],"note":<one line>}`.
   Without a discrepancy, `end_at` is the recorded end and `note` is
   `"checked"`: the line marks the session validated.
5. It has a `reading` activity or changed notes: [feed the wiki](#feed-the-wiki).

Tell the user in one line per topic, only what matters: "HTTP: the 24/09
practice session was closed by the hook at 19:30; the last change was your
attempt at 18:00. Fixed. 25 min of reading on 26/09, wiki updated: idempotency."

Open sessions are left open: the user may still be in the middle of one.

## Feed the wiki

For each note changed in the session, read the changed sections and, per
[formats.md § Wiki](../../reference/formats.md#wiki):

- Upsert the Concept pages those sections cover (update before create, cite
  the note's sources, never the note itself), and update `wiki/index.md`.
- Add the session `id` to each covered Concept's `studied` (once per session).

The notes are the learner's: never edit them here.

## 2. Survey (don't ask anything yet)

Read from the filesystem, not from memory. A few lines grouped by topic, only
what has something:

- `topic.json` and `progress/status.md`: current unit.
- **Pending attempts**: every `topics/*/{exams,exercises}/*/attempts/<date>.<ext>`
  without `<date>.feedback.md`. `<date>-p<i>.<ext>` files are exam audio, not
  attempts; `.feedback.md` files are not attempts.
- **Due cards**: count per topic from `cards/cards.json` and
  `cards/reviews.jsonl` with the rule in
  [formats.md § Cards](../../reference/formats.md#cards).
- **Unsure cards**: cards with `"flagged": true` in `cards/cards.json`, per
  topic, with their fronts. The learner marked them to go over with you.
- **Finished units** with something missing: the
  [checklist](#end-of-unit-checklist).
- **Quiz due**: the last `## Quizzes` row is 30+ days old, or 2+ units were
  finished since it.
- **Incomplete `topic.json`**: `goals` or `reason` empty or missing.
- **No teacher persona**: `agent/agents/teacher-<slug>.md` missing and
  `topic.json` has no `"teacher": false`.

## 3. Complete topic.json if needed

- Empty `goals` or `reason`: offer to fill them now (one open question per
  field). If accepted, write them to `topic.json` and fill an empty Mission in
  `learning.md` with the same. It never blocks the session.
- No teacher persona: offer to create it following
  [slp-init §4](../slp-init/SKILL.md#4-the-topics-teacher-persona), one topic
  at a time. If the user declines, write `"teacher": false` to that
  `topic.json` so it isn't offered again.

## 4. Ask what to do

With `AskUserQuestion`, one round: **topic(s)** (pending ones first) and
**what to do**:

| Option | Hands off to |
|---|---|
| Read on my own | nothing: the app records the reading as they take notes |
| Summarize material | `slp-summarize` |
| Get taught something | `slp-teach` |
| Make flashcards from my notes | `slp-cards` |
| Study my cards | the `3 cards` tab (`/app/views/cards.html`) |
| Go over my unsure cards | [§ Unsure cards](#unsure-cards) |
| Do an applied exercise | `slp-exercises` |
| Sit an exam | an exam for the unit with no attempt yet: open it in the app. Otherwise `slp-exam` |
| Check my level | `slp-quiz` |
| Grade a pending attempt | `slp-grade` |
| Leave it | nothing |

The app is at `http://localhost:8321` (`uv run slp`). An exam opens at
`/app/views/exam.html?f=topics/<slug>/exams/<exam>/exam.json`.

## 5. Hand off

Invoke the chosen skill with what was gathered (topic, unit, the pending
attempt, the relevant misconception). Don't re-ask. If the user says "I'll
take it from here", stop: the app keeps recording.

## Unsure cards

For each flagged card of the chosen topic, one at a time: ask the learner
what they're unsure about, then teach the concept behind it following
`slp-teach` (probe first, short, from the card's `note` and the topic's
sources). When the learner can explain it back, set `"flagged": false` on that
card in `cards/cards.json` (change nothing else) and move on. Log a
`teaching` activity with the card ids as `detail`.

## Activity

Every skill runs this when it starts work on a topic:

1. Read `progress/sessions.jsonl`. If the last session is open and its last
   line is 30+ minutes old, close it first by the idle rule.
2. No open session: append `{"id":<now as YYYY-MM-DDTHHmm>,"event":"start","at":<now>,"by":"agent"}`.
3. Append `{"id":<open id>,"event":"activity","at":<now>,"kind":<kind>,"by":"agent","detail":<one line>}`.

Kinds: `summary` (slp-summarize), `teaching` (slp-teach), `cards`
(slp-cards), `practice` (slp-exercises), `exam` (slp-exam), `quiz`
(slp-quiz), `feedback` (slp-grade). Skills never write `start` otherwise, and
never write `end`.

## End

When the user says they're done:

1. Append `{"id":…,"event":"end","at":<now>,"by":"agent","outputs":[<files changed since start, relative to the topic>],"note":"<one line>"}`
   to each topic with an open session.
2. It had a `reading` activity or changed notes: [feed the wiki](#feed-the-wiki).
3. Ask whether a unit was finished; if yes, [§Unit done](#unit-done).

If they just leave, the hook or the idle rule closes the session and the next
§1 validates it.

## Unit done

When the user confirms a unit is finished (at §End, from a skill's wrap-up,
or "I finished chapter 3"):

1. Append to `## Reading` in `progress/log.md`:
   `| YYYY-MM-DD | NN — <unit title> | yes/no (a note or summary covers it) | — |`.
2. Move `status.md` → Current unit to the next unit.
3. Show the unit's [checklist](#end-of-unit-checklist).

## End-of-unit checklist

For each finished unit U (a `## Reading` row), in this order, with the first
unchecked item marked as next:

```
01 — methods and status codes
- [x] cards: 6, 2 due → 3 cards tab
- [ ] exercise → slp-exercises        ← next
- [ ] exam → slp-exam
```

| Item | Done when | Otherwise |
|---|---|---|
| cards | a card in `cards/cards.json` has a `note` under U's note | `slp-cards` for U; cards due → the `3 cards` tab |
| exercise | an exercise's prompt has `**Unit:** U` and an attempt | none: `slp-exercises`; no attempt: submit it; no feedback: `slp-grade` |
| exam | an `exams/<U>-*` exam has a graded attempt | none: `slp-exam`; not sat: open it in the app; no feedback: `slp-grade` |

Show only units with something unchecked. A quiz due (§2) goes on one extra
line: `quiz: last one 34 days ago → slp-quiz`.
