# Self Learning Platform

A self-hosted study environment the learner fully owns: it runs on their machine, needs no subscription or network to use, and works with any agent and any model, local or paid.

## Principles

**Ownership**:
The learner holds everything: their data as plain files, the code as open source, and the freedom to swap any agent or model without losing anything.
_Avoid_: Lock-in, vendor account

**Offline**:
Usable with no network connection once installed; nothing in daily use calls out to the internet, and a skipped install step degrades a feature instead of breaking it.
_Avoid_: Local-only, air-gapped

**Setup**:
The moment meant to use the network: fetching dependencies and models, or pointing at ones the learner already has. After it, daily use aims to need no network; that is a goal, not a rule, and the Online profile may still fetch what is missing.
_Avoid_: Bootstrap, first run

**Profile**:
The learner's choice, made at Setup and changeable in the settings page, of how the agent layer and dictation run: Auto, Online or Offline. The core is the same in all of them.
_Avoid_: Mode, edition

**Auto profile**:
The default: Online when the server finds a connection at start, Offline otherwise.
_Avoid_: Smart mode

**Online profile**:
A paid agent and model, web lookups, and the largest dictation model, fetched when missing; comfort over independence.
_Avoid_: Cloud mode, default mode

**Offline profile**:
The profile where everything runs on the learner's machine: the reference stack, local sources, and a dictation model sized to the hardware. Nothing is fetched; what is missing falls back.
_Avoid_: Air-gapped mode, local mode

## Layers

**Core**:
The part that needs no model at all: the app, handwritten notes, studying cards, sitting exams, and recording sessions. Every file is plain JSON or Markdown, so topics, cards, exams and exercises can also be written by hand.
_Avoid_: Base app, manual mode

**Agent layer**:
The skills and agents that guide the process and supply the judgment: teaching, grading and feedback, interpreting sessions, progress and the wiki; it runs on whatever model the learner plugs in.
_Avoid_: AI features, Claude integration

**Model**:
Whatever LLM executes the agent layer, local or paid; the project treats them the same.
_Avoid_: Provider, backend

**Reference stack**:
The one fully open-source combination of agent, model and runtime that the project documents as a way to run the agent layer offline; a suggestion, not a tested requirement.
_Avoid_: Recommended setup, supported stack

## Study material

**Topic**:
One thing being studied (a book, a certification, a course), self-contained in its own folder.
_Avoid_: Subject, course, tema

**Source**:
Anything a topic declares as study material: a URL, or a path to a file anywhere on disk. The `topic.json` field is called `links` for historical reasons.
_Avoid_: Link, reference

**Local resource**:
Study material saved on disk inside a topic (Markdown, PDF, text, CSV, a database file), readable as plain-text context; always part of the topic's sources without being declared.
_Avoid_: Attachment, upload

**Source mode**:
A topic's standing preference for where the agent looks things up: web, local, or both; with no connection it is local regardless.
_Avoid_: Search mode, research setting

**Online feature**:
A capability that uses the network, such as web search; preferred when a connection exists, with local resources as the fallback, and never required by the core.
_Avoid_: Cloud feature

**Attempt**:
One sitting of an exam, or one submission of an exercise, saved under its `attempts/` folder and named by the minute it was made; exam answers point at questions by their position in the exam, whatever order they were shown in. An attempt is pending until its Feedback is written next to it.
_Avoid_: Submission, try, result

**Feedback**:
The grading of one Attempt, written next to it as `<date>.feedback.md`: what was met, what is missing, and which note heading covers it.
_Avoid_: Correction, result

## Studying

File formats for every term below: [agent/reference/formats.md](agent/reference/formats.md).

**Unit**:
The topic's own division (a chapter, a certification domain, a course module), numbered `NN`; exams and notes about it carry that number.
_Avoid_: Chapter, block, lesson (as generic terms)

**Mission**:
Why the learner studies a topic and what changes once they have it; the top of `learning.md`, built from `goals` and `reason`.
_Avoid_: Objective, purpose

**Record**:
The numbered entries in `learning.md` of what the learner demonstrably knows, declared, got corrected, or which source was chosen; covering a topic is never an entry.
_Avoid_: History, progress

**Source choice**:
A Record entry that settles which of two disagreeing sources is taught, so lessons, exams and grading stay consistent.
_Avoid_: Conflict note

**Exam**:
A fixed set of questions for one Unit, in `exam.json`, sat in the app.
_Avoid_: Test

**Exercise**:
A prompt that makes the learner produce an artifact (code, a decision document, a critique, an explanation) with a concept.
_Avoid_: Assignment, homework

**Card**:
One concept from the learner's notes as a question (front) and a short answer (back), written by the agent or by hand in the app. The learner answers it to themselves, reveals the back and self-grades "knew it" or "didn't know"; they can also flag it **unsure** to go over it later with the agent.
_Avoid_: Flashcard

**Deck**:
All the Cards of one topic, in `cards/cards.json`; studying it shows the due ones.
_Avoid_: Set, pack

**Box**:
A Card's Leitner level, 0 to 3, derived from its "good" streak since the last "again"; it sets how many days until the Card is due again.
_Avoid_: Stage, bucket

**Quiz**:
The repeatable level diagnostic: a fixed bank of questions per prerequisite thread and difficulty level, run as a ping-pong in the chat when a topic starts and again later, so the learner's edge can be compared over time.
_Avoid_: Level check, placement test

**Session**:
A block of study time in one topic holding a list of Activities, recorded in `sessions.jsonl` by the app (automatically, or with the start/stop control), closed by the learner, the agent hook or 30 idle minutes, and validated by the agent afterwards.
_Avoid_: Sitting, class

**Activity**:
One thing done inside a Session: reading, teaching, summary, cards, practice, exam, quiz or feedback.
_Avoid_: Event, task

**Wiki**:
The agent's own map of a topic's subject (concepts, their dependencies and sources) in the Open Knowledge Format, with each concept's progress: whether it was studied and in which Sessions. Fed by lessons, summaries and the learner's own notes; the notes themselves and what the learner demonstrably knows (`learning.md`) stay out of it.
_Avoid_: Knowledge base, notes

**Teacher persona**:
A per-topic file the agent reads to teach with that topic's character; it keeps no memory of its own.
_Avoid_: Teacher agent, tutor bot
