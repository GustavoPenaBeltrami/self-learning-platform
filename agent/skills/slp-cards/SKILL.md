---
name: slp-cards
description: Creates or updates the flashcards of a study topic in topics/ from the learner's own notes (notes/*.md) — one concept per card, question on the front, short answer on the back — and writes them to the topic's cards/cards.json, which the user studies in the app's cards tab with Leitner scheduling. Use when the user says "make cards", "flashcards from my notes", "update my cards", "/slp-cards", or after finishing a unit's notes.
---

# Cards

Turns what the learner wrote into flashcards. The app shows the due ones and
records each "again" or "good"; this skill only writes the cards.

## Required data (ask together if missing)

1. **Topic**: a folder in `topics/`.
2. **Scope**: the whole topic, or one unit (the note whose file starts with
   its `NN`). Default: the whole topic.

Log a `cards` activity ([slp-session §Activity](../slp-session/SKILL.md#activity)).

## 1. Read

- The notes in scope: `topics/<slug>/notes/*.md`. **Only the notes**: never
  `resources/`, sources, the wiki or your own knowledge. A fact not in the
  notes gets no card.
- `topics/<slug>/cards/cards.json`, if it exists.
- The `Source choice` entries of `learning.md`, so no card contradicts what
  was taught.

Format of every file: [formats.md § Cards](../../reference/formats.md#cards).
Language: `language.notes` of `topic.json`.

## 2. Write the cards

- One concept per card, asked as one question. Two concepts means two cards.
- `front` is a question that needs recall: "Why is PUT idempotent?", not
  "PUT: idempotent?". A cloze ("4xx blames the ___") is fine.
- `back` is at most 2 sentences, answering only the front.
- 5-15 cards per note (per h1). Favor what the note stresses: definitions,
  distinctions, reasons, trade-offs. Skip trivia and examples that are only
  illustrations.
- `note` is the heading path the fact sits under: `H1 › H2`.
- `id`: kebab-case from the fact (`put-idempotent`), unique in the topic.

## 3. Upsert, never rewrite

Match each existing card to the notes:

- Its fact is still in the notes, unchanged: **leave the card as is**, id,
  front and back.
- Its fact changed in the notes: keep the `id`, update `front`/`back`/`note`.
- Its fact left the notes: delete the card.
- A fact with no card: add one with a new `id`. Never reuse an id of a
  deleted card for another fact.

Keep `flagged` as it is on every card you keep or update: only the learner
sets it, and it is cleared after going over the concept (slp-session).

Cards with `"by": "user"` are the learner's: never edit or delete them, and
don't add a card for a fact one of them already covers. Cards outside the
scope stay untouched. Ids never change. Never touch `cards/reviews.jsonl`: it
is the app's record.

## 4. After writing

1. `uv run python -m json.tool topics/<slug>/cards/cards.json > /dev/null`.
2. Check: ids unique and kebab-case; `front`, `back`, `note` non-empty.
3. Report in one line: `N added, N changed, N removed · N total`, and where
   to study them: the `3 cards` tab of `uv run slp`
   (`http://localhost:8321/app/views/cards.html`).
