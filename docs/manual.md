# Manual

Full reference. The introduction is in the [README](../README.md).

## Getting started

```sh
./notes setup    # once, fetches what needs the network (Windows: notes setup)
./notes          # opens the notebooks; exams are in the nav (Windows: notes)
```

`./notes setup` is interactive and safe to re-run (it offers to keep the
current choices). It fetches the dependencies in the header of `app/server/server.py`
— `mlx-whisper` (GPU) on Apple Silicon Macs, `faster-whisper` (CPU) on Linux,
Windows and Intel Macs — asks for the profile and resolves the dictation model:

- **Auto** (recommended) or **Online**: downloads `turbo` (~1.6 GB), no more questions.
- **Offline**: shows the machine's RAM and free disk next to each size (`tiny`
  to `large-v3`) and asks for a size, the path to a model folder you
  already have, or `none`.

The model goes to `models/` at the repo root (git-ignored) and its path, with
the profile, to `settings.json`. The profile also sets the default
`sources_mode` for new topics: `both` for Online, `local` for Offline. A failed
download or `none` leaves dictation on the OS fallback; nothing else changes.

`./notes` starts the server at `http://localhost:8321/` and opens `notes.html`. If one is
already running, it opens the tab and exits. No build: it runs on the Python stdlib,
with `uv run --offline` so daily use never touches the network. If setup never
ran, it falls back to `python3`: everything works except dictation. The model is set in `/settings` (see Dictation below). On Windows ARM, dictation needs x64 Python
(emulated): `uv run --python cpython-3.12-windows-x86_64-none --with faster-whisper app/server/server.py app/views/notes.html`.
Without `uv`, `python3 app/server/server.py app/views/notes.html` starts everything except dictation.

## Profiles, offline and ownership

Everything is yours: topics and notes are plain files, the code is MIT, and
any agent or model can be swapped without losing anything. The **Profile**
(`profile` in `settings.json`: `auto`, `online` or `offline`) is picked at Setup,
changed any time in `/settings`, and only decides whether missing dictation
models may be fetched, the `sources_mode` of new topics, and which agents
`notes-setup-agent` recommends. The core never reads it. `auto`, the default,
works like Steam: the server checks for a connection when it starts and acts
Online if it finds one, Offline if not. Pick `offline` by hand to never fetch.

| | Online (auto with a connection) | Offline (auto without one) |
|---|---|---|
| Agent | A paid one: Claude Code, OpenAI Codex, Google Antigravity, Cursor… | The Reference stack below, or any agent on a local model |
| Dictation | The largest model (`turbo`, ~1.6 GB) at Setup; a missing size is fetched on first use | A size your RAM and disk handle, or a model you already have; nothing is fetched (Hugging Face cache only) |
| New topics look things up in | Web and local sources (`both`) | Local sources (`local`) |

**What the Setup fetches.** The Setup is the moment meant for the network:
Python dependencies (dictation engine) and the dictation model, or a path to
ones you already have. Working offline afterwards is a goal, not a rule: the
Online profile may still fetch a missing model, and `/settings` can download one. Fonts, Mermaid and KaTeX already ship in `app/vendor/`.

**What works with no network.** The whole core: the app, notebooks, exams,
review, settings and fonts. Dictation works once its model is on disk; without
it, the microphone points to the OS dictation (see Dictation under Notebook).
The agent layer works if its model is local; with no connection, the agents
use local sources and say they didn't verify on the web.

**Settings and fonts.** `settings.json` (profile, theme, reading font,
dictation model) and `fonts/` (your uploaded fonts) live at the repo root,
git-ignored like `topics/`. The server reads and writes them and builds the
`@font-face` rules for your fonts (`/api/fonts.css`), so they survive a new
browser or cleared data. The browser keeps a copy in localStorage only to paint
the theme before the server answers; `settings.json` always wins.

### Reference stack

One fully open-source way to run the agent layer offline. **It is a suggestion,
not tested by the project**: skills and agents are Markdown and topics are
Markdown and JSON, so any terminal agent with local file access works.

- **Agent**: [opencode](https://opencode.ai) (MIT). Reads `AGENTS.md` and
  `SKILL.md`, has subagents.
- **Runtime**: [Ollama](https://ollama.com).
- **Model**: `qwen3-coder:30b` (~19 GB disk, 32 GB RAM recommended), or
  `gpt-oss:20b` (~14 GB disk, 16 GB RAM floor) on smaller machines. Below
  16 GB of RAM the agent layer isn't viable locally.

```sh
curl -fsSL https://opencode.ai/install | bash      # opencode
curl -fsSL https://ollama.com/install.sh | sh      # Ollama on Linux; macOS/Windows: installer at ollama.com
ollama pull qwen3-coder:30b                        # or: ollama pull gpt-oss:20b
OLLAMA_CONTEXT_LENGTH=32768 ollama serve           # tool calls need a 16k-32k context
```

Point opencode at Ollama in `opencode.json` (Ollama can also write this for
you, see its opencode integration docs), then open opencode in the repo and
run `notes-setup-agent`:

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

**Known limits.** Grading and nuanced feedback (`notes-grade`) and
teacher-style judgment are clearly weaker than on a frontier model: take their
output as a draft. Long multi-step skills (`notes-teach`) and large contexts
degrade earlier. When that matters, a paid model is worth it.

**Plan B**: [Goose](https://github.com/block/goose) (Apache-2.0), if opencode
stops fitting.

## Files

```
README.md            The introduction.
notes, notes.cmd     Launcher: `./notes` (or `./notes app`) starts the app, `./notes setup` sets it up; `notes` on Windows.
LICENSE              MIT.
AGENTS.md            Entry point for any agent: where the skills are and how to map tools.
agent/
    skills/          The skills below. Single source, for any agent.
    agents/          researcher (verifies before teaching) and one teacher-<slug> per topic (personal, ignored).
docs/manual.md       This file.
app/
    server/server.py Local server. Lists files, builds and saves the notebooks.
    server/text.py   HTML <-> Markdown conversion. `python3 app/server/text.py` self-tests.
    views/           Pages: notes.html (notebook), exam.html (exam simulator, every question type), settings.html.
    scripts/         Shared JS: theme.js (color themes, settings), shell.js (waybar, explorer, statusline), viz.js (Mermaid, KaTeX).
    styles/style.css Shared visual system. Tokens and color themes.
    tests/           Self-checks, one per area: `python3 app/tests/test_<name>.py`.
    tools/migrate_names.py Renames old Spanish class names in topics/*/notes/*.md. Idempotent.
    vendor/          Mermaid 11.17.2 and KaTeX 0.16.11 with their fonts, Inter 4.1 and
                     JetBrains Mono 2.304 (OFL), to work offline.
    Design.md        The visual system: tokens, components, do's and don'ts.
topics/<slug>/
    topic.json         Title, subtitle, type, area, goals, reason, language, routine, sources_mode, links.
    learning.md        Mission, Glossary and Record. The memory of /notes-teach.
    notes/NN-*.md      One section per file. Real Markdown.
    notes/img/         Pasted images, as separate files.
    resources/         PDFs, handouts, anything you want at hand.
    exams/<slug>/
        exam.json      Questions: multiple choice, open, oral or practical.
        attempts/      One .json (answers) and one .md (grading) per attempt.
    exercises/<slug>/
        prompt.md      Applied task: produce an artifact, not an answer.
        attempts/      The submitted artifact and its grading .md.
    progress/
        status.md      Where I am today in this topic.
        log.md         History: reading, exams, exercises, reviews.
topics/review/       Created by /notes-review. One dated exam per review.
```

The frontends read the filesystem: any `<slug>/exam.json` you put in
`exams/` shows up in the list on its own, and the notebook sections come from
the `.md` files. There's no index to maintain by hand.

## The visual system

`app/Design.md` is the source. The app imitates a tiling desktop in a tab:
a waybar on top (navigation and tools), an explorer on the left with every
topic and its index, the content as a vim buffer in the middle (line numbers,
`~` at the end) and a statusline at the bottom (mode, path, saved, zoom, width).
JetBrains Mono everywhere, flat surfaces, no shadows. Headings are told apart
by ANSI color, not by size.

There are six color themes in the waybar picker: `hypr` (navy, the dark default),
`light`, `e-ink` (dark monochrome), `sakura`, `forest` and `amber crt`. Each one
is a block of 20 tokens in `style.css`. To add one, copy a block and add its key
to `THEMES` in `theme.js`. Components only read tokens: change them there, not
in individual rules.

The notebook's reading font picker (mono / serif / inter) applies only to the
body of the note. To read in your own typeface, upload a `.woff2`, `.ttf` or
`.otf` file from `/settings`: it is stored in `fonts/` at the repo root
(git-ignored, like `topics/`) and appears in both font pickers, offline. The
name is saved lowercase with dashes for spaces (`My Font.ttf` → `my-font.ttf`);
the extension must already be lowercase. A font with the same name is refused
instead of overwritten. Anything that isn't a font, or bigger than 20 MB, is
rejected.

## Diagrams and formulas

In the notebook, the ⌗ and Σ buttons insert a diagram block (Mermaid) or a
formula block (LaTeX). Click it to edit the source and it redraws itself.

The block is atomic: you don't type inside it. Its source text is what counts; the
drawing is discarded on save, so the `.md` keeps a clean fence:

    ```mermaid
    graph TD
      A[Packet] --> B[Reliable stream]
    ```

That means the file also renders on GitHub and in Obsidian, and you can write
the fence by hand in the `.md` without opening the app. `exam.html` renders the
same fences inside the question, the options and the explanation.

Mermaid and KaTeX ship in `app/vendor/`, so diagrams and formulas work without
internet. Inline math in the middle of a line isn't supported: blocks only.

## How it's used

The entry point is `/notes-session`: it surveys the state of every topic
(overdue reviews, ungraded attempts, topics without exercises) and asks what
you want to do. For a new topic, `/notes-init` interviews you, creates the
filesystem above and runs a level check.

Inside a topic, the loop is preparation → practice → feedback → iteration:

1. **Preparation** — I read with `resources/` and the `links` in `topic.json`,
   take notes in **notes.html**, or `/notes-summarize` condenses a text I
   already understand. When something doesn't sink in by reading,
   `/notes-teach` builds it from scratch (see below).
2. **Practice** — `/notes-exam` builds an exam (`exams/<slug>/`) to answer
   questions about the topic; `/notes-exercises` builds an exercise
   (`exercises/<slug>/`) to produce something with it — code, an ADR,
   a critique. I sit the exam in **exam.html**.
3. **Feedback** — `/notes-grade` grades the attempt, exam or exercise, against
   the rubric or the prompt, and updates `learning.md` and `progress/`.
4. **Iteration** — `/notes-review` builds a spaced, interleaved review
   (Leitner cards) so that what you understood doesn't fade away.

## Topics

A **topic** is any study source, not just a book. The `type` field in
`topic.json` says which: `book`, `certification`, `documentation`, `course`
or `practice`. The type changes two things: the label you see in the lists and
how `notes-exam` writes the questions (a certification exam mimics the real
exam format, a documentation one asks when to use what).

```json
{
  "title": "AWS Certified Cloud Practitioner",
  "subtitle": "CLF-C02 · 65 questions in 90 min · pass with 700 of 1000",
  "type": "certification",
  "area": "cloud",
  "order": 3,
  "goals": ["Pick the right service by trade-offs, not by the name I know."],
  "reason": "I need the certification for the role.",
  "language": { "source": "en", "notes": "es", "exams": "es" },
  "routine": { "cadence": "1 domain per week", "session": "~30 min" },
  "end_date": "YYYY-MM-DD",
  "sources_mode": "both",
  "links": [
    { "title": "Exam guide", "url": "https://docs.aws.amazon.com/..." },
    { "title": "My study guide", "path": "~/Books/clf-c02-guide.pdf" }
  ]
}
```

`area` groups related topics (for example several software architecture
books) as context and tone. The teacher agent is per **topic**, not per area:
`notes-init` offers to generate `agent/agents/teacher-<slug>.md` when you add
a new topic, with a persona designed for that specific topic (a literature
book calls for a literature teacher, a cert calls for an instructor for that
cert); `notes-session` offers to generate it for topics that don't have one yet.
`links` are the declared sources: a `url` (official docs, a course) or a `path`
to a file anywhere on disk; `resources/` are local files inside the topic (the
book's PDF, a handout) and always count as sources. All show up together above
the notebook's index. `notes-init` offers to copy an external `path` into
`resources/`; a missing path only produces a warning. `sources_mode` (`web`,
`local` or `both`) is where the agent looks things up; `notes-init` defaults it
from the Profile (`both` for Online, `local` for Offline), and with no
connection it's local regardless, with a note on what wasn't verified on the web.

### Language

`language` sets the default language of each output, separately:

- `source` — the language of the material, so `notes-summarize` doesn't assume
  it has to translate.
- `notes` — notes, summaries and lessons (`notes-summarize`, `notes-teach`).
- `exams` — exams, exercises and grading feedback (`notes-exam`,
  `notes-exercises`, `notes-review`, `notes-grade`).

They're defaults, not locks: ask for a different language on any single request
("give me the exam in English", "explain this in Spanish") and that output
follows your request. The agent chats with you in whatever language you write in.

To add a topic: `/notes-init` interviews you and creates `topics/<slug>/` with
`topic.json` and the `notes/`, `exams/`, `exercises/`, `resources/`
and `progress/` folders. It shows up in the lists on its own.

## Notebook

**One notebook per topic.** You don't create notes by hand: every **Heading 1**
you write *is* a section, and it's saved as its own `.md` in
`topics/<slug>/notes/`. Deleting the heading deletes the file. Renaming it
renames the file. The file order (`01-`, `02-`…) is the document order.

- The notebook opens with the topic's title, subtitle and index. All three
  are edited in place; the index builds itself from the headings you write.
- **Automatic numbering**: h1 → 1, 2, 3; h2 → 1.1, 1.2; h3 → 1.1.1. It's CSS,
  not saved in the file, so it never gets out of sync.
- Clicking an index entry takes you to the section.
- **Typing shortcuts**: `/h1` … `/h6` at the start of a line turn it into a
  heading; `/p` goes back to paragraph; `/list` or a `- ` followed by a space
  starts a list. The toolbar dropdown does the same if you prefer the mouse.
- Highlight / underline / strikethrough with color: pick the color in the toolbar
  and then the action. The palette is the `COLORS` array at the top of the
  script in `app/views/notes.html`.
- **Comments**: only on text that's already highlighted, underlined or struck
  through. Click the mark and a menu opens with the six colors, the comment
  field and the button to remove the mark. A commented mark carries a `°`; the
  comment shows in a bubble on hover.
- **References**: the button opens a dropdown with every section in the
  index, numbered and indented by level. If you had text selected, that text
  becomes the link; otherwise the section title is inserted. You can also type
  `[[Section name]]` and it converts when you close the bracket. On hover it
  pulls up the content of the referenced section.
- **Image**: goes into the text flow, centered, wherever the cursor is.
  You can also paste it (⌘V, works for screenshots) or drop it on the
  document. Clicking the image opens a width control, from 20% to 100%.
  On save, the image is written as a file in `notes/img/` and the `.md`
  keeps only the reference: `<img src="img/ae738e6a.png">`. The name is the
  content hash, so pasting the same screenshot twice doesn't duplicate the
  file, and images that are no longer referenced are deleted on their own.
- **Margin note**: floats wherever you leave it, in the right margin, at
  50% opacity until you hover over it. Drag it by the `⠿`. If you paste an
  image inside, you get a floating image.
- **Reading font**: Serif (Charter), Inter or JetBrains Mono, in the toolbar.
  It's remembered. All three work offline: Inter and JetBrains Mono ship in
  `app/vendor/`.
- **Light / dark mode** in the toolbar, for the whole interface.
- **Dictation**: click the microphone or `⌃M` (Control, not Command: macOS uses
  `⌘M` to minimize), speak, and do the same to finish. The text goes where the
  cursor is. Whisper transcribes locally, detecting the language when none is
  given, with no internet once `./notes setup` downloaded the model.
  - **Model**: `voice_model` in `/settings` wins, then the `NOTES_VOICE_MODEL`
    environment variable, then the engine default: `turbo` on the GPU on Apple
    Silicon, `small` on CPU. Setup writes `voice_model`: `turbo` for Auto and
    Online, what the hardware handles for Offline (`small` or `base` on a modest
    CPU, `turbo` on a fast one) or a model you already have. The `/settings`
    dropdown offers the sizes (`tiny` to `large-v3`), which work on both
    engines; its **download** key saves the selected size to `models/` and sets
    `voice_model` to that folder. A size already in `models/` is used from
    there; otherwise Online fetches it on first use and Offline only looks in
    the Hugging Face cache (`local_files_only`). For a model folder you already
    have (MLX for mlx-whisper, CTranslate2 for faster-whisper), type its path in
    **model path** and press **use path**: it is used as-is, never downloaded.
  - **Fallback**: with no engine (started without `uv`) or no model (a skipped
    Setup, Offline with a size that isn't on disk) the microphone
    doesn't break: the status tells you to use the OS dictation instead, which
    types into the notebook like a keyboard.
    - macOS: system dictation, press `Fn` twice (System Settings → Keyboard →
      Dictation).
    - Windows: voice typing, `Win+H`.
    - Linux: [Speech Note](https://github.com/mkiol/dsnote), offline:
      `flatpak install flathub net.mkiol.SpeechNote` (Arch: `yay -S dsnote`).
      On Wayland it needs `ydotool` to type into other windows.
- Saves on its own, 0.9 s after each change. The status shows in the toolbar.

### What's inside a `.md`

Plain Markdown (`#`, `-`, `**`, `*`, `~~`) plus inline HTML for what
Markdown lacks: colored highlights, comments, margin notes and blank lines
(`<br>`, because Markdown can't represent one). It's valid HTML inside
Markdown, so the files open fine in Obsidian or any editor.

`python3 app/server/text.py` checks that the HTML↔MD round trip doesn't lose anything
or move anything around.

## Topic order

`topic.json` has an `order` field. It rules both lists, notes and exams.
A topic without `order` goes at the end, sorted by title. The title carries
no number: the number is what sorts, not what you read.

```json
{ "title": "Fundamentals of Software Architecture", "subtitle": "…", "order": 1 }
```

It's edited by hand; the editor doesn't overwrite it on save.

## Why there are no folders per block

Blocks are reading order, not file location. A topic is a topic; grouping
folders by block forces you to move them whenever the order changes.
The grouping lives in a `progress/roadmap.md` inside whichever topic acts as the hub.

## Skills

They live in `agent/skills/`. They trigger on their own when the request fits,
or you call them by name (`/name` in Claude Code). For another agent, see
`/notes-setup-agent`. They all write to this project's folders, not to the chat.

| Skill | What for | Leaves |
|---|---|---|
| `/notes-setup-agent` | Set up the repo for your agent (Claude Code, Codex, Gemini, Cline…) | Symlinks or native files, in `.git/info/exclude` |
| `/notes-session` | Entry point: what's missing across topics, what to do today | Hands off to the right skill |
| `/notes-init` | Add a new topic | Full `topics/<slug>/`, `learning.md` with the Mission |
| `/notes-teach` | Really understand something from scratch | A lesson in `topics/<slug>/notes/` |
| `/notes-summarize` | Condense a text you already understand, in the topic's notes language | New sections in an existing note |
| `/notes-exam` | Turn material into gradable questions | `topics/<slug>/exams/<slug>/exam.json` |
| `/notes-exercises` | Force you to produce an artifact, not to answer | `topics/<slug>/exercises/<slug>/prompt.md` |
| `/notes-grade` | Grade an exam or exercise attempt | The feedback `.md` next to the attempt, `learning.md`, `progress/` |
| `/notes-review` | Keep what you understood from fading | `topics/review/exams/YYYY-MM-DD/exam.json` |

Plus the **researcher** subagent (`agent/agents/`), which isn't called by hand:
`notes-teach` fires it to verify a fact before stating it and to survey a topic
before planning.

### `/notes-teach` — the one worth knowing

It comes from [amosblomqvist's system](https://github.com/amosblomqvist/learn),
adapted to this project. The core idea: the brain doesn't lock in a fact it
isn't sure is safe to lock in. If something deeper might contradict it later,
it hedges and the fact never lands. Hence the two principles:

1. **Unconditional truths first** — what's accepted as is, with no caveats.
   It sticks instantly and gives solid ground to build on.
2. **"How could I have discovered this myself?"** — nothing appears out of
   nowhere. Every step is motivated, 3Blue1Brown style. A fact that feels
   arbitrary doesn't stick.

The goal isn't to recite: it's for the fact to be *derivable* from things you
already accept. That holds on its own; what's memorized rots.

Three phases, always, scaling the size and never the shape:

1. **Probe.** It asks graded questions until it finds the edge of what you
   know — bounded on both sides: something you get right and something you get
   wrong. If you get everything right, the questions were easy and it goes up.
   Then it asks you, open-ended, what exactly you want to understand.
2. **Plan.** It shows you the plan as a dependency graph: unconditional truths
   at the roots, your goal at the destination. **It stops and waits for your
   go-ahead** — a wrong root is cheap to fix here and expensive halfway
   through the lesson.
3. **Teach.** Node by node: motivate → establish → connect → check. Each
   node is confirmed with a question before anything is built on top of it.

```
/notes-teach coupling and cohesion
```

At the end the lesson is written to `topics/<slug>/notes/`, with the
dependency graph as a `mermaid` fence, and it offers to move on to `notes-exam`
or `notes-exercises`.

Two things worth knowing:

- **It's slow on purpose.** The probe phase can take ten questions. That's
  the work, not the preamble: without knowing where your edge is there's no
  way to teach inside it.
- **Caveman mode turns off while it teaches.** Compressed prose is for
  answering queries, not for building a dependency graph.

Edit `agent/skills/notes-teach/SKILL.md` if you want it to teach differently:
it's written for one person, and that person is you.

### `learning.md` — each topic's memory

`/notes-teach` keeps in `topics/<slug>/learning.md` what it knows about you
**as a student**, and reads it before probing. Without it every session starts
from zero. Three parts:

- **Mission** — why you're studying the topic, concretely. It anchors every
  decision: what to teach next, what to cut. If it's vague, the first thing it
  does is question it.
- **Glossary** — a term goes in **only once you can use it**, not when it was
  explained to you. That makes it both canonical vocabulary and a progress signal.
- **Record** — numbered entries on what was understood, what you already knew,
  and above all **which misconception was corrected**. Those last ones are the
  most valuable: they predict where you'll trip in neighboring topics, and
  they're the highest-yield review material.

An entry isn't written because a topic "was covered". Covering isn't learning:
it takes evidence.

### `/notes-review` — fluency isn't retention

Answering correctly at the end of the lesson measures **fluency**: recalling it
now, with the topic fresh. What matters is **retention**: recalling it in three
weeks. From the inside they feel the same, and that's the trap.

`/notes-review` builds an exam with desirable difficulty, using Leitner cards:

- **Cards** — every question you've answered is a card, in a *fast*, *medium*
  or *slow* box. A correct answer moves it up a box; a miss sends it all the
  way back to fast. Three correct answers in a row in the slow box retire the card.
- **Weakness** — what you missed weighs more, and the misconceptions in
  `learning.md` always go in.
- **Interleaving** — it mixes topics in the same session. A review of a single
  chapter isn't a review, it's retaking the exam.
- **Recall, not recognition** — it rewrites the questions. A question seen
  word for word measures whether you remember the exam, not the concept.

```
/notes-review
```

Each review is a dated folder in `topics/review/exams/`; old ones stay as a
record of what you were forgetting. **The spacing depends on `notes-grade`
leaving its row in each topic's `progress/log.md`** — without it, the skill is blind.

### Where they come from

`/notes-teach` comes from [amosblomqvist's](https://github.com/amosblomqvist/learn) system
(the dependency graph, the unconditional truths, probing for the edge).
Per-topic memory, the Mission, the Glossary and `/notes-review` come from
[Matt Pocock's](https://github.com/mattpocock) `teach` skill, adapted: his version
assumes the whole directory is a teaching workspace with lessons as loose HTML,
which here the notebook and the exams already cover.

## Exam format

An exam is a folder, `topics/<slug>/exams/<slug>/`, with `exam.json`
inside. Before writing questions, `/notes-exam` asks which types to include
(you may not have a microphone, or may not want to record oral answers) — it
never assumes all of them. Each question has a `type` (default `multiple_choice`
if missing):

```json
{
  "title": "FoSA — Ch 1",
  "questions": [
    {
      "type": "multiple_choice",
      "q": "Question?",
      "options": ["A", "B", "C", "D"],
      "answer": 2,
      "explanation": "Why C and why not the others."
    },
    {
      "type": "open",
      "q": "Explain when a topic is preferable to a queue and why.",
      "rubric": ["Mentions extensibility/coupling", "Gives a decision criterion, not just pros/cons"]
    }
  ]
}
```

`answer` is a 0-based index, and `multiple_choice` questions are shuffled and
auto-graded in the client. `open`, `oral` and `practical` have no `answer`:
they have a `rubric`, and there's no way to auto-grade them in the browser.
`oral` records by voice (same mechanism as the notebook's dictation) and
transcribes before saving.

When you finish, `exam.html` saves the whole attempt with `POST /api/attempt` to
`exams/<slug>/attempts/<date>.json`. If the exam had non-MC questions,
run `/notes-grade` on that attempt: it checks each rubric point, writes
`attempts/<date>.md` with the feedback and updates `learning.md` and
`progress/`. The same skill grades `/notes-exercises` exercises against their
`prompt.md` instead of a rubric.
