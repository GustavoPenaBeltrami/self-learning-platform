<div align="center">

<!-- omit in toc -->

# TomaNota 📚

<strong>An agent-powered hub for self-learners</strong>

*Made by [Gustavo Peña Beltrami](https://github.com/GustavoPenaBeltrami)*

[![Manual](https://img.shields.io/badge/docs-manual-blue)](docs/manual.md)
[![Stars](https://img.shields.io/github/stars/GustavoPenaBeltrami/Notas.svg)](https://github.com/GustavoPenaBeltrami/Notas/stargazers)
[![Issues](https://img.shields.io/github/issues/GustavoPenaBeltrami/Notas.svg)](https://github.com/GustavoPenaBeltrami/Notas/issues)
[![Python](https://img.shields.io/badge/python-server-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Local](https://img.shields.io/badge/local-development-2EA44F?logo=homeassistant&logoColor=white)](#installation)

</div>

---

A book, a certification, a tool's documentation, a course: everything you study is a **topic**, and Notes builds the full loop around it — preparation, practice, feedback, spaced review. It all starts with one line in your agent:

| Command | What it does |
|---|---|
| `/notes-init` | Sets up a topic: interview, structure, level check |
| `/notes-session` | What's pending today across all topics, and what to do |

## Why Notes

Studying well is harder than it looks. Reading isn't enough: you need someone to explain, quiz you, grade you and make you review right before you forget. Notes takes care of all of that. You study the material, the agent teaches and grades, and everything stays as Markdown on your disk: **with Notes, the method comes built in.**

**It doesn't depend on any particular agent.** The skills use the `SKILL.md` format and `AGENTS.md` explains the project to any of them — Claude Code, Codex, Gemini CLI, Antigravity, Cline, Cursor, opencode, with a cloud model or a local one via Ollama.

Notes has four pieces that talk to each other through the filesystem:

<table>
<tr>
<td align="center" valign="top" width="25%">
<strong>🧠 Skills</strong>
<br /><code>agent/skills/</code>
<br />Teach, build exams and exercises, grade against a rubric, review with Leitner.
</td>
<td align="center" valign="top" width="25%">
<strong>🎓 Agents</strong>
<br /><code>agent/agents/</code>
<br />A <code>researcher</code> that verifies before stating anything and a <code>teacher-&lt;slug&gt;</code> per topic.
</td>
<td align="center" valign="top" width="25%">
<strong>🗂️ Filesystem</strong>
<br /><code>topics/&lt;slug&gt;/</code>
<br />Notes in Markdown, exams in JSON, attempts, grading and progress. No database.
</td>
<td align="center" valign="top" width="25%">
<strong>📓 App</strong>
<br /><code>app/</code>
<br />Local notebook and exam simulator, with dictation, Mermaid and LaTeX.
</td>
</tr>
</table>

The **skills** are the method: teach from unconditional truths, practice and review. The **agents** give each topic the right persona. The **filesystem** reads fine on GitHub, in Obsidian or in any editor. And the **app** is where you take notes and sit exams, with voice dictation via Whisper.

Ready to start? Follow the [installation](#installation) or jump straight to the [manual](docs/manual.md).

## Three windows

Notes is used with three windows side by side:

| | Window | What for |
|---|---|---|
| 1 | **The material** | The PDF, the course, the docs. Whatever you're studying. |
| 2 | **The app** | The notebook at `localhost:8321`. Exams are in the nav bar. |
| 3 | **The agent** | Open at the repo root. Teaches, builds exams, grades. |

Then the loop: `/notes-teach` or `/notes-summarize` to prepare, `/notes-exam` and `/notes-exercises` to practice (you sit them in window 2), `/notes-grade` for feedback and `/notes-review` so it doesn't fade away. Everything they produce lands in `topics/<slug>/` and shows up in the app on its own.

`topics/example/` shows the structure. Your real topics stay out of git.

### Language

Each topic's `topic.json` has a `language` block that sets the defaults: `source` is the language of the material, `notes` is used for notes, summaries and lessons, and `exams` for exams, exercises and grading feedback. You can ask for a different language on any single request ("give me the exam in English") without touching the file. The agent chats with you in whatever language you write in.

## Installation

### Requirements

- **[uv](https://docs.astral.sh/uv/)** — the only thing you need to install. It downloads Python 3.9+ if you don't have it, and the dictation engine the first time.
  ```sh
  curl -LsSf https://astral.sh/uv/install.sh | sh                                # macOS and Linux
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"   # Windows
  ```
- **git**, to clone the repo.
- **A coding agent**, whichever you use.
- **A browser** with a microphone for dictation and oral exams.
- **Internet only the first time**, to download the packages and the voice model. After that it works offline: Mermaid, KaTeX and the reading fonts ship in the repo (`app/vendor/`).

### Platforms

| System | Dictation | Disk (packages + model) | How to start it |
|---|---|---|---|
| macOS Apple Silicon | mlx-whisper, on the GPU | ~2.7 GB | `./notes` |
| macOS Intel, Linux x64, Windows x64 | faster-whisper, on the CPU | ~0.7 GB | `./notes` (Windows: `notes`) |
| Windows ARM | faster-whisper, with emulated x64 Python | ~0.7 GB | `uv run --python cpython-3.12-windows-x86_64-none --with faster-whisper app/server.py app/notes.html` |

`./notes` is `uv run app/server.py app/notes.html`. Without uv: `python3 app/server.py app/notes.html` starts everything except dictation. On CPU, dictation uses the `small` model; on a powerful machine, `turbo` makes it more accurate. Pick the model size in `/settings`; for a local model folder you already have, see the [manual](docs/manual.md).

Without a dictation engine or model, the microphone points you to the OS dictation instead: `Fn` twice on macOS, `Win+H` on Windows, and on Linux [Speech Note](https://github.com/mkiol/dsnote) (`flatpak install flathub net.mkiol.SpeechNote`, or `yay -S dsnote` on Arch) with `ydotool` on Wayland. See the [manual](docs/manual.md).

### Steps

```sh
git clone https://github.com/GustavoPenaBeltrami/Notas.git
cd Notas
```

Open your agent in the folder and ask it:

```
Read AGENTS.md and run notes-setup-agent.
```

It detects which agent it is and exposes the skills in that agent's format — symlinks if it supports them, conversion if not. Whatever it creates goes to `.git/info/exclude`, so it doesn't clutter the repo. Then start the app:

```sh
./notes          # Windows: notes
```

**Going to keep your topics in your own repo?** Change the remote:

```sh
git remote set-url origin <your-repo>
```

## 📚 Documentation

The details of each skill, the notebook and the exam format are in the **[manual](docs/manual.md)**.

**Online or offline?** The Online profile (a paid agent) is recommended. To run everything on your machine with open-source tools, see [Profiles, offline and ownership](docs/manual.md#profiles-offline-and-ownership) and its Reference stack.

**Roadmap:** test `notes-setup-agent` on Codex, Gemini CLI, Antigravity and Cline, and native dictation on Windows ARM. See the [open issues](https://github.com/GustavoPenaBeltrami/Notas/issues).

**Thanks to** [amosblomqvist/learn](https://github.com/amosblomqvist/learn) for the method behind `notes-teach` and to [Matt Pocock](https://github.com/mattpocock) for per-topic memory and spaced review.

## Contributing

Contributions are welcome! Fork the repo, create your branch, and open a Pull Request. Skills are edited in `agent/skills/`, never inside an agent's own folder. For bugs or ideas, [open an issue](https://github.com/GustavoPenaBeltrami/Notas/issues/new).

## License

[MIT](LICENSE).
