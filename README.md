<div align="center">

<!-- omit in toc -->

<img src="app/assets/readme-header.png" alt="独学 SLP · Self Learning Platform" width="640">

**an agent-powered hub for self-learners**

[![Website](https://img.shields.io/badge/website-selflearningplatform.github.io-262626?style=flat-square&labelColor=0c0c0c)](https://selflearningplatform.github.io)
[![Stars](https://img.shields.io/github/stars/GustavoPenaBeltrami/self-learning-platform.svg?style=flat-square&color=262626&labelColor=0c0c0c)](https://github.com/GustavoPenaBeltrami/self-learning-platform/stargazers)
[![Issues](https://img.shields.io/github/issues/GustavoPenaBeltrami/self-learning-platform.svg?style=flat-square&color=262626&labelColor=0c0c0c)](https://github.com/GustavoPenaBeltrami/self-learning-platform/issues)
[![Python](https://img.shields.io/badge/python-server-262626?style=flat-square&logo=python&logoColor=e6e6e6&labelColor=0c0c0c)](https://www.python.org/)
[![Local](https://img.shields.io/badge/local-first-262626?style=flat-square&labelColor=0c0c0c)](#installation)

<sub>made by [Gustavo Peña Beltrami](https://github.com/GustavoPenaBeltrami)</sub>

</div>

SLP is a self-hosted study environment you fully own: it runs on your machine, needs no subscription, and works with any agent and any model, local or paid.

Reading is not learning. You learn when you express the material again and again, with someone pointing out your mistakes. SLP gives you that someone: an agent that teaches, quizzes, grades and brings your mistakes back before you forget them, plus a local app to take notes and sit exams.

**Full documentation: [selflearningplatform.github.io/docs](https://selflearningplatform.github.io/docs/overview)** · also as [`llms.txt`](https://selflearningplatform.github.io/llms.txt)

## Quick start

You only need [uv](https://docs.astral.sh/uv/). It fetches Python and the packages.

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh    # Windows: see the installation docs
git clone https://github.com/GustavoPenaBeltrami/self-learning-platform.git
cd self-learning-platform
uv run slp
```

Then open your agent ([Claude Code](https://claude.com/claude-code) recommended, any works) at the repo root:

```
Read AGENTS.md, then read agent/skills/slp-setup/SKILL.md and follow it.
```

1. `/slp-init`: create a topic. The agent interviews you and checks your level
2. `/slp-session`: start every study session here. It tells you what's pending, makes sense of the sessions the app recorded and shows what's missing when you finish a unit

Recommended setup: three windows side by side, your material, the app and the agent. More in [installation](https://selflearningplatform.github.io/docs/install) and [getting started](https://selflearningplatform.github.io/docs/getting-started).

## How it works

```
self-learning-platform/
├── AGENTS.md    # read by any agent
├── agent/
│   ├── skills/     # the method: slp-*/SKILL.md
│   ├── agents/     # researcher, teacher-<slug> personas
│   └── reference/  # shared file formats, source rules, question rules
├── app/         # local notebook and exam simulator
└── topics/      # your study, as Markdown and JSON. No database
```

- **core**: the app, your notes, exams, cards and session tracking. Works without an agent or a model, and every file is plain JSON or Markdown you can write by hand
- **agent layer** (optional): skills that guide the process and bring the judgment (teaching, grading, feedback, progress, the wiki), on whatever model you plug in

## AI teacher

| Skill | Step | What it does |
|---|---|---|
| [`/slp-setup`](https://selflearningplatform.github.io/docs/slp-setup) | setup | Exposes the skills and agents to your agent |
| [`/slp-init`](https://selflearningplatform.github.io/docs/slp-init) | setup | Creates a topic and checks your level |
| [`/slp-session`](https://selflearningplatform.github.io/docs/slp-session) | plan | What's pending today; validates recorded sessions and feeds the wiki |
| [`/slp-quiz`](agent/skills/slp-quiz/SKILL.md) | control | Repeatable level quiz: the same bank, ping-pong in the chat |
| [`/slp-summarize`](https://selflearningplatform.github.io/docs/slp-summarize) | prepare | Summarizes material into the topic's notes and wiki |
| [`/slp-teach`](https://selflearningplatform.github.io/docs/slp-teach) | prepare | Teaches until it's understood, not memorized, and writes the note and wiki |
| [`/slp-exercises`](https://selflearningplatform.github.io/docs/slp-exercises) | practice | An applied exercise: code, an ADR, a critique |
| [`/slp-exam`](https://selflearningplatform.github.io/docs/slp-exam) | practice | Builds an exam you sit in the app |
| [`/slp-grade`](https://selflearningplatform.github.io/docs/slp-grade) | feedback | Grades the attempt against a rubric |
| [`/slp-cards`](agent/skills/slp-cards/SKILL.md) | review | Flashcards from your notes, studied in the app |

Study sessions are tracked by the app behind the scenes: any activity in a topic opens one, 30 idle minutes close it, and the statusline has a start/stop control. Each session is a time block with a list of activities (reading, teaching, cards, exam…) in `progress/sessions.jsonl`. At the next `slp-session` the agent validates it: fixes an end that doesn't match your last activity and turns the notes you wrote into progress. Each topic also keeps a **wiki**: the agent's map of concepts, dependencies and sources in the [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf), with which concepts you studied and when. File formats: [`agent/reference/formats.md`](agent/reference/formats.md).

Skills use the Agent Skills format, so they work with Claude Code, Codex, Gemini CLI, Cursor, opencode and others, with a cloud model or a local one via Ollama. See [skills](https://selflearningplatform.github.io/docs/skills) and [profiles](https://selflearningplatform.github.io/docs/profiles).

## Visual interface

`uv run slp` serves the app at `http://localhost:8321`, local only.

- **[notes](https://selflearningplatform.github.io/docs/editor)**: a notebook per topic, saved as Markdown as you type. Tables, Mermaid, LaTeX and images. Upload sources to the topic and open local `path` sources from the app
- **[exams](https://selflearningplatform.github.io/docs/exam-app)**: sit exams built by the agent: multiple choice, open, practical and oral
- **cards** (`3 cards` tab): study flashcards from your notes, one concept each, written by `/slp-cards` or by hand (`N` in the cards view, or select text in a note). Answer to yourself, click the card to reveal it, then "knew it", "don't know" or **unsure**: unsure cards wait for `/slp-session` to go over them with you. Leitner scheduling shows only the due ones
- **[dictation](https://selflearningplatform.github.io/docs/dictation)**: speak your notes or oral answers. Runs locally with Whisper, on a key you choose (`ctrl+m` by default)
- **[settings](https://selflearningplatform.github.io/docs/settings)**: profile, fonts, and themes: two built in, or a theme builder that derives a whole palette from one color. Plus slash commands and keyboard [shortcuts](https://selflearningplatform.github.io/docs/shortcuts)

## Your topics

Everything you study is a topic, and everything a topic holds is plain files you own:

```
topics/<slug>/
├── topic.json    # goals, languages, sources, routine
├── learning.md   # mission, glossary, your mistakes
├── notes/  cards/  exams/  exercises/  resources/
├── wiki/         # the agent's map of the subject (OKF)
└── progress/     # status, log, sessions.jsonl
```

Your topics are git-ignored; `topics/example/` shows the shape. To keep them, point the repo at your own: `git remote set-url origin <your-repo>`. See [filesystem](https://selflearningplatform.github.io/docs/topics).

## Roadmap

Study time from the session log in the app, wiki linting, and more agents and local models tested. See the [roadmap](https://selflearningplatform.github.io/docs/roadmap).

## Contributing

Contributions are welcome: fork, branch, pull request. Skills are edited in `agent/skills/`, never inside an agent's own folder. Bugs and ideas: [open an issue](https://github.com/GustavoPenaBeltrami/self-learning-platform/issues/new).

Thanks to [amosblomqvist/learn](https://github.com/amosblomqvist/learn) for the method behind `slp-teach` and to [Matt Pocock](https://github.com/mattpocock) for per-topic memory.

## License

[MIT](LICENSE)
