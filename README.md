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

Reading is not learning. You read, connect it to what you know, then express it again and again with someone pointing out your mistakes, until you can defend it in an exam. SLP gives you that someone: an agent that teaches, quizzes, grades and makes you review, and a local app where you take notes and sit exams.

| Path | Piece | Role |
|---|---|---|
| `agent/skills/` | skills | The method: teach, build exams and exercises, grade against a rubric, review with Leitner |
| `agent/agents/` | agents | A `researcher` that verifies before stating anything, and a `teacher-<slug>` per topic |
| `topics/<slug>/` | filesystem | Notes in Markdown, exams in JSON, attempts, grading and progress. No database |
| `app/` | app | Local notebook and exam simulator, with dictation (Whisper), Mermaid and LaTeX |

**Full documentation: [selflearningplatform.github.io/docs](https://selflearningplatform.github.io/docs/overview).**

## Requirements

- **[uv](https://docs.astral.sh/uv/)**: the only thing you need to install. It fetches Python and the packages.

  ```sh
  curl -LsSf https://astral.sh/uv/install.sh | sh                        # macOS and Linux
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows
  ```

- **Recommended**: a coding agent with permission in the repo folder ([Claude Code](https://claude.com/claude-code) recommended, any works), VS Code, and GitHub to keep your topics in your own repo.
- **Internet for the first `uv run slp`**, which downloads the packages. After that it aims to work offline: Mermaid, KaTeX and the fonts ship in `app/vendor/`.

## Installation

```sh
git clone https://github.com/GustavoPenaBeltrami/self-learning-platform.git
cd self-learning-platform
uv run slp
```

Want [dictation](https://selflearningplatform.github.io/docs/dictation) ready offline? Run `uv run slp setup` too. Going to keep your topics in your own repo? `git remote set-url origin <your-repo>`.

Work with three windows side by side: your **material** (the PDF, the course), the **app** (`uv run slp`), and your **agent**, open at the repo root.

## Getting started

Before you start, know your subject, your sources, your timeframe, how often you'll study, and your goal.

1. Open your agent in the repo folder and send:

   ```
   Read AGENTS.md, then read agent/skills/slp-setup/SKILL.md and follow it.
   ```

   On the first run your agent hasn't loaded the skills yet, so it can't call `/slp-setup`: the prompt points it at the file. It exposes the skills in your agent's format (symlinks, or conversion) and adds whatever it creates to `.git/info/exclude`.

2. Run `/slp-init`: from now on the skills load normally. The agent interviews you, creates `topics/<slug>/`, checks your level and offers a teacher for that topic. `topics/example/` shows the structure; your own topics are git-ignored.

3. Start each study session with `/slp-session`.

## Skills

Every skill can be called by name. *manual* ones run only when you call them; *auto* ones are also started by the agent when your request matches.

| Command | Step | Starts | What it does |
|---|---|---|---|
| `/slp-setup` | setup | manual | Exposes the skills and agents to your agent |
| `/slp-init` | setup | manual | Creates a topic and checks your level |
| `/slp-session` | plan | auto | What's pending today across every topic, and what to do |
| `/slp-summarize` | prepare | invoked | Summarizes material into the topic's notes |
| `/slp-teach` | prepare | auto | Teaches until it's understood, not memorized |
| `/slp-exercises` | practice | auto | An applied exercise: code, an ADR, a critique |
| `/slp-exam` | practice | invoked | Builds an exam you sit in the app |
| `/slp-grade` | feedback | auto | Grades the attempt against a rubric |
| `/slp-review` | review | auto | Spaced, interleaved Leitner review so it doesn't fade |

Everything they produce lands in the topic folder and shows up in the app on its own. Details: [skills](https://selflearningplatform.github.io/docs/skills).

## Project identity

### Name

独学 (*dokugaku*) is the Japanese word for self-study. SLP, the Self Learning Platform, is built for exactly that: one person, one topic, and the discipline to keep going. The agent teaches, quizzes and grades. The learning stays yours.

<table align="center">
  <tr>
    <td><h1 align="center">独</h1><b>doku</b> · by oneself</td>
    <td><h1 align="center">学</h1><b>gaku</b> · learning</td>
  </tr>
</table>

A book, a certification, a tool's documentation, a course: everything you study is a **topic**, and SLP builds the full loop around it (preparation, practice, feedback, spaced review). Everything stays as Markdown and JSON on your disk. No database, no account.

### Why

Studying well is harder than it looks. Reading isn't enough: you need someone to explain, quiz you, grade you and make you review right before you forget. SLP takes care of all of that. You study the material, the agent teaches and grades, and everything stays on your disk: **the method comes built in.**

**It doesn't depend on any particular agent.** The skills use the `SKILL.md` format and `AGENTS.md` explains the project to any of them: Claude Code, Codex, Gemini CLI, Antigravity, Cline, Cursor, opencode, with a cloud model or a local one via Ollama.

### Principles

Four Japanese design ideas describe what SLP does. They settle decisions; they are not decoration.

| | Idea | Meaning | In SLP |
|---|---|---|---|
| 簡素 | **kanso** | simplicity | one font, no shadows, no gradients |
| 間 | **ma** | negative space | the `~` buffer, the space around the mark |
| 渋い | **shibui** | quiet beauty | hierarchy by lightness, not size |
| 静寂 | **seijaku** | calm | chrome lives in two bars; content stays quiet |

Two themes, ink and paper: `sumi` 墨 and `kami` 紙. The full design reference is [`app/styles/Design.md`](app/styles/Design.md).

## Roadmap

Test `slp-setup` on Codex, Gemini CLI, Antigravity and Cline, native dictation on Windows ARM, and more: see the [roadmap](https://selflearningplatform.github.io/docs/roadmap) and the [open issues](https://github.com/GustavoPenaBeltrami/self-learning-platform/issues).

**Online or offline?** The online profile (a paid agent) is recommended. To run everything on your machine, use opencode + Ollama + `qwen3-coder:30b` (or `gpt-oss:20b` on 16 GB of RAM). See [profiles](https://selflearningplatform.github.io/docs/profiles).

**Thanks to** [amosblomqvist/learn](https://github.com/amosblomqvist/learn) for the method behind `slp-teach` and to [Matt Pocock](https://github.com/mattpocock) for per-topic memory and spaced review.

## Contributing

Contributions are welcome. Fork the repo, create your branch, and open a pull request. Skills are edited in `agent/skills/`, never inside an agent's own folder. For bugs or ideas, [open an issue](https://github.com/GustavoPenaBeltrami/self-learning-platform/issues/new).

## License

[MIT](LICENSE).
