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
The part that needs no model at all: the app, handwritten notes, sitting exams and reviewing.
_Avoid_: Base app, manual mode

**Agent layer**:
The skills and agents that automate teaching, exam building, grading and review; it runs on whatever model the learner plugs in.
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
Anything a topic declares as study material: a URL, or a path to a file anywhere on disk.
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
