---
name: notes-setup-agent
description: Sets up this project for the agent that is using it (Claude Code, Codex, Gemini CLI, Antigravity, Cline, Cursor, opencode, or any other, with a cloud model or a local one via Ollama) — exposes the skills and agents in agent/ in the agent's native format, without touching anything versioned; reads the Profile in settings.json to recommend the paid agents (Online) or the Reference stack (Offline). Use the first time the repo is opened with a new agent, or when the user says "set up the project", "install the skills", "/notes-setup-agent" (or in Spanish: "configurá el proyecto", "instalá las skills").
---

# Agent setup

The single source is `agent/`: `agent/skills/<name>/SKILL.md` and
`agent/agents/<name>.md`. This skill doesn't copy or rewrite it: it
**exposes** it where your tool looks for it. Everything you create is local
to the user.

## 0. Read the Profile

Read `profile` from `settings.json` at the repo root (or `GET /api/settings`
if the app is running). Missing file or key = `online`.

- **Online** (recommended): the supported paid agents are Claude Code, OpenAI
  Codex, Google Antigravity and Cursor. If the learner is already in one of
  them, configure that one. If they're in another agent, say it works too
  (the agent layer is plain Markdown and JSON) and continue.
- **Offline**: point them to the Reference stack in the manual (`docs/manual.md`,
  "Profiles, offline and ownership"): opencode + Ollama + `qwen3-coder:30b`, or
  `gpt-oss:20b` on 16 GB of RAM. It's a suggestion, not tested. If they're
  already in opencode, configure it; installing Ollama or pulling a model is
  the learner's call, don't do it for them. Remind them that grading and
  teacher judgment are weaker on local models: treat that output as a draft.

Either way, the rest of this skill configures whichever agent is running it.

## 1. Identify yourself

You know which tool you are. If you're not sure (or the user is going to use
another one), ask with `AskUserQuestion`. Then look up in that tool's
**current** documentation — not from memory, it changes often — three things:

1. Which instructions file it reads when opening the repo (`AGENTS.md`,
   `CLAUDE.md`, `GEMINI.md`, a rules folder…).
2. Whether it supports skills in `SKILL.md` format, and in which project
   folder.
3. Whether it supports subagents defined in files, and in which folder and
   format.

Starting point, to be verified:

| Tool | Instructions | Skills | Subagents |
|---|---|---|---|
| Claude Code | `CLAUDE.md` (with `@AGENTS.md` inside) | `.claude/skills/` | `.claude/agents/` |
| Codex | `AGENTS.md` | `.agents/skills/` | — |
| Gemini CLI | `GEMINI.md` or `contextFileName: AGENTS.md` | `.gemini/skills/` | — |
| Others (Antigravity, Cline, Cursor, opencode) | Usually read `AGENTS.md` or a rules folder | See their docs | See their docs |

Ollama isn't an agent: it runs the model behind one of these. Configure the
agent, not Ollama (for opencode, the manual's Reference stack has the provider
block). Warn the user that a small local model may not be able to
sustain long skills like `notes-teach`.

## 2. Expose, in this order of preference

1. **Nothing to do** — the tool reads `AGENTS.md` and that's enough to load
   the skills by hand (see `AGENTS.md`). If it doesn't support native skills,
   stop here.
2. **Symlink** — the tool supports `SKILL.md`: link its folder to the
   source, so it never drifts out of sync.
   ```sh
   mkdir -p .claude && ln -s ../agent/skills .claude/skills && ln -s ../agent/agents .claude/agents
   ```
   If the subagent format differs (different frontmatter), link only the
   skills and leave the agents for step 3.
3. **Conversion** — only for what doesn't fit with a symlink. Generate the
   files in the native format from `agent/`, one per skill or agent. Put a
   line at the top of each generated file saying which file it comes from, and
   tell the user that if they edit `agent/` they have to run this skill again.
4. **Instructions** — if the tool doesn't read `AGENTS.md`, create its
   instructions file with a single line that imports it or says "Read
   `AGENTS.md`".

Never edit `agent/`, `AGENTS.md` or anything versioned to adapt it to your
tool: the tool-name translation is already in `AGENTS.md`.

## 3. Ignore what you created, for this user only

Add each path you created to `.git/info/exclude` (not to `.gitignore`: the
repo is shared by people with other agents). Check it isn't already there.

```sh
git check-ignore -v <path>   # must print .git/info/exclude
git status --short           # nothing new must show up
```

## 4. Verify

- Your tool lists `notes-session` (or, at level 1, you can read
  `agent/skills/notes-session/SKILL.md`).
- `git status --short` shows nothing that wasn't there before.

Close with a three-line summary: which level you used, which paths you
created, and "start with `notes-session`". If the tool needs a restart to see
the skills, say so.
