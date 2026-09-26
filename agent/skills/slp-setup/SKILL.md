---
name: slp-setup
disable-model-invocation: true
description: Sets up this project for the agent that is using it (Claude Code, Codex, Gemini CLI, Antigravity, Cline, Cursor, opencode, or any other, with a cloud model or a local one via Ollama) — exposes the skills and agents in agent/ in the agent's native format, without touching anything versioned; reads the Profile in settings.json to recommend the paid agents (Online) or the Reference stack (Offline). Use the first time the repo is opened with a new agent, or when the user says "set up the project", "install the skills", "/slp-setup".
---

# Agent setup

The single source is `agent/`: `agent/skills/<name>/SKILL.md` and
`agent/agents/<name>.md`. This skill doesn't copy or rewrite it: it
**exposes** it where your tool looks for it. Everything you create is local
to the user.

## 0. Read the Profile

Read `profile` from `settings.json` at the repo root (or `active_profile`
from `GET /api/settings` if the app is running). Missing file or key = `auto`.
`auto` is Online when there is a connection, Offline otherwise; recommend as
Online and mention the Reference stack in one line.

- **Online** (recommended): the supported paid agents are Claude Code, OpenAI
  Codex, Google Antigravity and Cursor. If the learner is already in one of
  them, configure that one. If they're in another agent, say it works too
  (the agent layer is plain Markdown and JSON) and continue.
- **Offline**: point them to this reference stack: opencode + Ollama + `qwen3-coder:30b`, or
  `gpt-oss:20b` on 16 GB of RAM. It's a suggestion, not tested. If they're
  already in opencode, configure it; installing Ollama or pulling a model is
  the learner's call, don't do it for them. Remind them that grading and
  teacher judgment are weaker on local models: treat that output as a draft.

Either way, the rest of this skill configures whichever agent is running it.

## 1. Identify yourself

You know which tool you are. If you're not sure (or the user is going to use
another one), ask with `AskUserQuestion`. Then look up in that tool's
**current** documentation — not from memory, it changes often — four things:

1. Which instructions file it reads when opening the repo (`AGENTS.md`,
   `CLAUDE.md`, `GEMINI.md`, a rules folder…).
2. Whether it supports skills in `SKILL.md` format, and in which project
   folder.
3. Whether it supports subagents defined in files, and in which folder and
   format.
4. Whether it has session start/end hooks (step 2b).

Starting point, to be verified:

| Tool | Instructions | Skills | Subagents | Hooks |
|---|---|---|---|---|
| Claude Code | `CLAUDE.md` (with `@AGENTS.md` inside) | `.claude/skills/` | `.claude/agents/` | `.claude/settings.local.json` |
| Codex | `AGENTS.md` | `.agents/skills/` | — | verify |
| Gemini CLI | `GEMINI.md` or `contextFileName: AGENTS.md` | `.gemini/skills/` | — | verify |
| Others (Antigravity, Cline, Cursor, opencode) | Usually read `AGENTS.md` or a rules folder | See their docs | See their docs | verify |

Ollama isn't an agent: it runs the model behind one of these. Configure the
agent, not Ollama. For opencode, start Ollama with
`OLLAMA_CONTEXT_LENGTH=32768 ollama serve` (tool calls need a 16k-32k context)
and put this in `opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "options": { "baseURL": "http://localhost:11434/v1" },
      "models": { "qwen3-coder:30b": {} }
    }
  }
}
```

Warn the user that a small local model may not be able to
sustain long skills like `slp-teach`.

## 2. Expose

Decide with what step 1 found; several can apply:

- The tool supports `SKILL.md` natively → **symlink** its folders to the
  source, so they never drift:
  ```sh
  mkdir -p .claude && ln -s ../agent/skills .claude/skills && ln -s ../agent/agents .claude/agents
  ```
  If its subagent format differs (other frontmatter), link only the skills.
- Skills or subagents exist but in another format → **convert**: generate
  one native file per skill or agent from `agent/`, with a first line naming
  the source file, and tell the user to rerun this skill after editing
  `agent/`.
- The tool doesn't read `AGENTS.md` → also create its instructions file with
  one line that imports `AGENTS.md` or says "Read `AGENTS.md`".
- The tool has neither skills nor subagents → nothing to expose: `AGENTS.md`
  already tells it to read each `SKILL.md` by hand.

Never edit `agent/`, `AGENTS.md` or anything versioned to adapt it to your
tool: the tool-name translation is already in `AGENTS.md`.

## 2b. Hooks (optional)

Hooks only sharpen the session log: the app records sessions on its own and
closes idle ones, and `slp-session` validates them. Offer them with `AskUserQuestion`; skip if the
user declines or the tool has no lifecycle hooks.

- **Claude Code**: write `.claude/settings.local.json` (merge if it exists):

  ```json
  {
    "hooks": {
      "SessionStart": [{ "hooks": [{ "type": "command", "command": "uv run slp sessions" }] }],
      "SessionEnd": [{ "hooks": [{ "type": "command", "command": "uv run slp sessions close", "timeout": 10 }] }]
    }
  }
  ```

  `uv run slp sessions` closes idle sessions and prints the open ones;
  Claude Code adds that output to your context. `uv run slp sessions close`
  ends every open session with `"by": "hook"` when the agent exits; the next
  `slp-session` corrects that end if the work had stopped earlier.
- **Other tools** (Codex, Gemini CLI, opencode, …): check their current docs
  for session start/end hooks or plugins. If they exist, run the same two
  commands; if not, skip.

## 3. Ignore what you created, for this user only

Add each path you created (including `.claude/settings.local.json`) to `.git/info/exclude` (not to `.gitignore`: the
repo is shared by people with other agents). Check it isn't already there.

```sh
git check-ignore -v <path>   # must print .git/info/exclude
git status --short           # nothing new must show up
```

## 4. Verify

- Your tool lists `slp-session` (or, with nothing exposed, you can read
  `agent/skills/slp-session/SKILL.md`).
- With hooks: `uv run slp sessions` runs and exits 0.
- `git status --short` shows nothing that wasn't there before.

Close with a short summary: what you exposed and how, which paths you
created, whether hooks are on, and "Next: `/slp-init` to create your first
topic, then `slp-session` at the start of each study session." If the tool
needs a restart to see the skills, say so.
