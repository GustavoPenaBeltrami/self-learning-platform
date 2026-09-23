---
name: slp-review
description: Builds a spaced, interleaved review with Leitner cards — mixes topics, prioritizes what failed or sits in the fast box, and rewrites the questions so they require recall rather than recognition. Use when the user says "review", "/slp-review", "how long since I last saw this", "I'm forgetting this", "quiz me", or when they finished a block and it's worth consolidating before moving on.
---

# Notes review

Answering correctly at the end of a lesson measures **fluency**: being able to
retrieve it now, with the topic fresh. What matters is **retention**: being able
to retrieve it in three weeks. They feel the same from the inside, and that's
the trap — fluency gives a sense of mastery that retention doesn't back up yet.

Retention isn't built by repetition, it's built with desirable difficulty.
This skill produces that difficulty in three ways, and all three are mandatory:

- **Recall, don't recognize.** A question they've already seen word for word
  measures whether they remember the exam, not the concept.
- **Space.** What they haven't touched in months is worth more than yesterday's.
- **Interleave.** Topics mixed in the same session, never grouped.

## Where it writes

`topics/review/exams/YYYY-MM-DD/exam.json` (same folder structure as any exam —
see `slp-exam`). Attempts go in `topics/review/exams/YYYY-MM-DD/attempts/`,
same as in any other topic.

It's just another topic: if `topics/review/` doesn't exist, create the folder
with this `topic.json` and with `exams/` inside. It shows up on its own in both
lists.

```json
{ "title": "Review", "subtitle": "Spaced and interleaved", "type": "review", "order": 0, "links": [] }
```

The exam format is `slp-exam`'s, and **its option-construction rules apply in
full** — above all, write the correct statement first and mutate it into each
distractor. Don't repeat them here: read that skill.

Language: the review mixes topics, so there's no single `language.exams`. Use
the user's explicit request if there is one; otherwise, if every topic that
goes in shares the same `language.exams`, use it; if they differ, ask once.

## Where the material comes from

In this order:

1. **`topics/*/progress/log.md`** — what each topic was examined on, when and
   with what score.
2. **`topics/*/exams/*/attempts/*.json`** — individual attempts, with the
   detail of which question was right or wrong. This is the evidence the
   Leitner boxes are derived from (see below) — no separate card-state file
   is needed.
3. **`topics/*/exams/*/exam.json`** — the bank of already-written questions.
4. **`topics/*/learning.md`** — the record. **Corrected misconceptions** are
   the most valuable review material there is: a dislodged wrong belief tends
   to come back. Find them and target them.
5. **`topics/*/notes/*.md`** — if a topic has no exams yet, the questions come
   from the note.

## How to choose what goes in — Leitner cards

Every question (from any `exam.json` in the bank, from any topic) is a
**card**. It has no state file of its own: its box is recalculated every time a
review is built, from the evidence in `topics/*/exams/*/attempts/*.json` and
`topics/*/progress/log.md`.

**Boxes**: *fast* (new, or failed last time), *medium*, *slow* (several
correct answers in a row). With each consecutive correct answer it moves up one
box. With **a single miss it goes all the way back to fast** — not half a step
back, a miss is a strong signal.

**Retirement**: after **3 consecutive correct answers in the slow box**, the
card is retired from active rotation. It isn't lost: it moves to the weekly
maintenance review.

**What goes into a normal review**: aim for 12-15 questions, prioritizing the
fast box > medium > slow, and within each box the ones seen longest ago in
`progress/log.md`. If there's no evidence of anything (a topic just started or
without attempts), treat everything as the fast box and spread evenly.

**Weekly maintenance review**: when a topic runs out of active cards
(everything retired from slow), it isn't abandoned — once a week give it a
short oral/chat review of the whole retired set, without saving it as an exam
(it's not reproducible or bankable). If they pass, the set stays confirmed for
another week. If they miss something specific, that card goes back to the fast
box and enters the next normal review.

**Weakness**: within the fast box, whatever shows up as a corrected
misconception in `learning.md` goes in, no matter what.

**Interleaving.** The result mixes topics. `exam.html` already shuffles the
questions when taking the exam, so don't order them yourself — but **do** make
sure the set has at least two different topics when there's material from two
topics. A review of a single chapter isn't a review, it's retaking the exam.

**Documented alternative, not implemented**: the previous system of fixed,
growing intervals (1 → 3 → 7 → 16 → 35 → 90 days since last examined) remains
as an alternative method if Leitner falls short — don't run both engines in
parallel. SM-2/FSRS remain in the backlog, not researched yet.

## How the questions are rewritten

Never copy a question from the bank as is. Reuse the **idea**, rewrite the
**prompt**:

- Change the scenario. If the original asked about a payments service, ask
  about an inventory one.
- Change the direction. If it gave the concept and asked for the definition,
  give the situation and ask for the concept.
- Go up a step when you can: from "what is X" to "here are two options, which
  one and why". Recognizing is easier than applying, and we want the hard part.
- Rotate which one is correct. If in the original exam it was B, don't let it
  be B here.

If a question can only be asked one way, keep it — but let those be few.

## After writing

1. Validate: `python3 -m json.tool topics/review/exams/<date>/exam.json > /dev/null`.
2. Check that `answer` is between 0 and 3, that they all have 4 options, and
   that the correct index is spread out.
3. Tell them the path and to open it with `uv run slp`.
4. Tell them in two lines **why each card went in**: "six from DDIA ch. 3, in
   the fast box because of a miss last week; four from FoSA ch. 2, just coming
   in; two from AWS to interleave". The review teaches more when its criterion
   is understood.
5. When they take it, write the review row yourself in
   `topics/<topic>/progress/log.md` for each topic that went in (one row per
   topic, not one row in the review "topic") — date `YYYY-MM-DD`, never
   relative. That's what feeds the boxes next time: without that record, this
   skill is blind.

## What it doesn't do

It doesn't delete or touch the original exams: they're the bank, and their
history in `log.md`/`attempts/` is what makes spacing work. Each review is a
new, dated folder. The old ones stay, and they're a record of what was being
forgotten.
