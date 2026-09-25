# Notes — instructions for the agent

This repo is a study system: skills and agents (`agent/`), a filesystem of
topics (`topics/<slug>/`) and a local app (`uv run slp`). You are the third
window: the user studies in one, takes exams and notes in the app, and talks
to you in this one.

## First time

The user starts with this prompt:

```
Read AGENTS.md, then read agent/skills/slp-setup/SKILL.md and follow it.
```

On the first run your tool hasn't loaded the skills in `agent/skills/` yet,
so it can't invoke `slp-setup` by name: read that file and follow it. It
configures the project for you without touching anything under version
control. After that, skills load normally.

## Skills

Each skill is `agent/skills/<name>/SKILL.md` (Agent Skills format:
`name` + `description` frontmatter, instructions below). If your tool doesn't
load skills on its own, whenever a request matches a `description`, read that
whole `SKILL.md` and follow it. The entry point is `slp-session`.
Skills with `disable-model-invocation: true` in their frontmatter
(`slp-setup`, `slp-init`) run only when the user asks for them by name:
never start them on your own.

The agents in `agent/agents/*.md` are subagents: `researcher` and one
`teacher-<slug>` per topic. Without subagents, read the file and do its work
yourself, as a separate step.

## Tool names

The skills name Claude Code tools. Map them to yours:

| In the skill | What it means |
|---|---|
| `AskUserQuestion` | Ask with options. Without that tool: ask a numbered question in the chat and wait for the answer. |
| `Agent` / `subagent_type: X` | Delegate to the subagent `agent/agents/X.md`. Without subagents: follow that file yourself. |
| `WebSearch` / `WebFetch` | Search and read the web, as the topic's `sources_mode` allows (`web`, `local`, `both`). With `local` or without web access: use the local sources (`resources/` and `path` entries in `links`), say plainly what was not verified on the web, and don't state things from memory. |
| `Read` / `Write` / `Edit` / `Grep` / `Glob` | Read, write and search files. |

## Language

Chat with the user in the language they write in. For generated files,
`topic.json` `language` sets the defaults: `notes` for notes, summaries and
lessons; `exams` for exams, exercises and grading feedback; `source` is the
language of the material. An explicit request ("give me the exam in English")
overrides the default for that output.

## Repo rules

- Everything the skills produce goes to `topics/`, not to the chat.
- `topics/*` is ignored except `topics/example/`: real topics belong to the user.
- The `teacher-*` agents in `agent/agents/` are personal and ignored.
- Each agent's own config (`.claude/`, `CLAUDE.md`, etc.) goes to
  `.git/info/exclude`, never to `.gitignore`.
- `local/` is the user's own scratch space (references, drafts), git-ignored.
  Don't write there unless asked.
