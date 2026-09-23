# 独学 SLP — Design & Brand Reference
> 独学 (*dokugaku*) means self-study. SLP is a terminal-style study tool: a waybar on top, a file explorer on the left, a vim buffer in the middle, a statusline at the bottom. One person, one topic, and a quiet screen.

**Themes:** `sumi` 墨 (dark, default when the OS is dark) · `kami` 紙 (light, default when the OS is light)

## Identity

**Name:** SLP · Self Learning Platform. Written `SLP` in prose and `slp` in code, commands and paths (`/slp-init`, `uv run slp`).
**Mark:** 独学. 独 *doku* means "by oneself", 学 *gaku* means "learning". The single 独 is the short mark.
**Tagline:** An agent-powered hub for self-learners.

The references are a Hyprland desktop with vanilla waybar, nvim with a NERDTree-style panel, htop and neofetch. The Japanese side is limited to the mark and a few ideas about restraint. It is not a theme and it never decorates the UI.

## Principles

Four Japanese design ideas describe what the product already does. Use them to settle decisions.

| | Idea | Meaning | Rule in SLP |
|---|---|---|---|
| 簡素 | **kanso** | Simplicity | One typeface. No shadows, no gradients, no radius on content. Remove before adding |
| 間 | **ma** | Empty space is part of the design | The `~` filler, generous gutters, clear space around the mark. Don't fill empty areas |
| 渋い | **shibui** | Understated beauty | Hierarchy comes from lightness and color, not size. Headings stay near body size |
| 静寂 | **seijaku** | Calm | Chrome lives in two bars. The content between them stays silent. No toasts, no motion beyond 120ms color fades |

## Logo

| Asset | File | Use |
|---|---|---|
| Horizontal lockup | `assets/lockup-horizontal.png` | README header, splash, slides, social banners |
| Stacked lockup | `assets/lockup-stacked.png` | Square and portrait formats, the empty topic list |
| Mark 独 | `assets/mark.png` | Favicon, waybar, avatar |

- The PNGs are white on transparent. On light surfaces, invert them to black (`filter: invert(1)`). Never place them on a mid-grey or on a photo.
- **Clear space:** ¼ of the mark's height on every side.
- **Minimum width:** mark 16px, stacked 96px, horizontal 180px. Below that, use the mark alone.
- The lettering is artwork. Never retype it, recolor it, stretch, rotate, crop or add shadow or glow.

## Voice

SLP talks like a good terminal: lowercase, short, exact. It says what happened and what to do next, then goes quiet.

- Lowercase labels. Commands and paths as names (`ls -l`, `exam --check`, `~/notes/topics`).
- One fact per line. No exclamation marks, no praise, no emoji in the UI.
- State is a glyph plus a word: `✓ correct`, `✕ wrong`, `NORMAL`, `INSERT`, `PASS`, `FAIL`.

| Write | Not |
|---|---|
| `saved` | Your note was saved successfully! |
| `Score 70% · pass` | Great job, you passed! |
| `no topics yet: ask your agent to "create a new topic" (slp-init)` | Looks like you haven't added anything yet |

## Layout

```
┌ waybar ─────────────────────────────────────────────────────────────┐
│ [独] (1 notes)(2 exams)(3 settings)   Wed Sep 23  16:30   [tools][theme▾] │
├──────────────┬──────────────────────────────────────────────────────┤
│┌ explorer ┐  │   notes ~/topics ❯ ls -l                             │
││ ⌄ topic-a/2│  │   # TOPIC                    TYPE    SECT  RES       │
││  1 Intro   │  │   01 Fundamentals of …       book       2    1       │
││ ⌄ topic-b/4│  │ ~                                                    │
│└───────────┘  │ ~                                                    │
├──────────────┴──────────────────────────────────────────────────────┤
│ NORMAL ~/notes/topics      🔍 − 100% +  ↔ − 736px +  utf-8[unix]  All │
└─────────────────────────────────────────────────────────────────────┘
```

- The page scrolls as a document. The waybar is `position: sticky`, the explorer is sticky under it, and the statusline is `position: fixed`. There is no inner scroll container. The notes editor positions margin cards and menus against `scrollY`, so keep it that way.
- The content column is centered in the panel: `max-width: calc(var(--width) + 2 * var(--gutter))`, with symmetric gutter padding. `--width` is set from the statusline (defaults: 736px for notes, 960px for exams).
- The content zoom (statusline 🔍) applies CSS `zoom` to `#app` only. Chrome, explorer and bars never zoom. Any code that mixes `clientX/Y` with `offsetLeft/Top` inside `#app` must divide by the zoom (see card drag in `notes.html`).
- Below 900px the explorer hides, the clock hides, and workspace labels collapse to numbers. Below 1280px margin cards stop floating and sit inline.

## Color

The brand is ink on paper: **sumi 墨** `#0c0c0c` and **kami 紙** `#e6e6e6`, with the grey ramp between them. The app and brand material use only this ramp and never take a hue. `sumi` is the ramp as below; `kami` is the same ramp inverted.

| Step | sumi hex | Token |
|---|---|---|
| void (sumi) | `#0c0c0c` | `--color-void` |
| carbon | `#141414` | `--color-carbon` |
| graphite | `#1b1b1b` | `--color-graphite` |
| iron | `#262626` | `--color-iron` |
| slate | `#383838` | `--color-slate` |
| pewter | `#4e4e4e` | `--color-pewter` |
| steel | `#676767` | `--color-steel` |
| ash | `#828282` | `--color-ash` |
| fog | `#a3a3a3` | `--color-fog` |
| chalk | `#cacaca` | `--color-chalk` |
| paper (kami) | `#e6e6e6` | `--color-paper` |
| accent | `#d4d4d4` | `--color-accent` |

### Tokens

Each theme defines the same 20 tokens: an 11-step neutral ramp, an accent, seven ANSI hues and `--on-accent`. Components only read tokens, so a new theme is one CSS block.

| Token | Role |
|---|---|
| `--color-void` | Waybar, statusline, floating menus. The darkest surface |
| `--color-carbon` | Page background (`--bg`) |
| `--color-graphite` | Waybar modules, cards, hover rows |
| `--color-iron` | Hairlines (`--line`), control fills, hover inside modules |
| `--color-slate` | Explorer frame, line numbers, `~` filler, empty placeholders |
| `--color-pewter` … `--color-ash` | Intermediate steps, rarely used directly |
| `--color-steel` | Heading counters, `//` and `#` prefixes, zero counts |
| `--color-fog` | Secondary text (`--muted`) |
| `--color-chalk` | Tree items, clock, statusline modules |
| `--color-paper` | Primary text (`--ink`) |
| `--color-accent` | Active workspace, selected tree node, hovered table row, links, refs, focus rings |
| `--ansi-red` | Failure: wrong answer, save error, recording mic (`--bad`) |
| `--ansi-green` | Success: correct answer, INSERT mode, caret, h3 (`--good`) |
| `--ansi-yellow` | NORMAL mode, italics, h4, current exam in the tree |
| `--ansi-blue` | h1, folder names in the tree |
| `--ansi-magenta` | Topic type (`book`, `certification`), prompt `❯`, h5 |
| `--ansi-cyan` | h2, htop table header, secondary keys, tree subfolders |
| `--ansi-orange` | List markers, `[01]` question numbers, inline `code` |
| `--on-accent` | Text on any filled accent/ANSI background |

The short names (`--bg`, `--card`, `--ink`, `--muted`, `--line`, `--accent`, `--good`, `--bad`, `--veil`) are aliases kept so page-level CSS stays short. `viz.js` reads the ramp for Mermaid, so diagrams follow the theme.

### Themes

| Key | Character | Carbon | Paper | Accent |
|---|---|---|---|---|
| `sumi` | Ink. Monochrome dark; every ANSI hue is a grey | `#141414` | `#e6e6e6` | `#d4d4d4` |
| `kami` | Paper. The sumi ramp inverted; logos use `filter: invert(1)` via `--logo` | `#e6e6e6` | `#0c0c0c` | `#1b1b1b` |

Theme selection lives in `theme.js`. `data-theme` on `<html>` picks the block; with no value, the page follows `prefers-color-scheme` (`sumi` or `kami`). Unknown saved keys (old themes) fall back to that. The choice persists in `settings.json` at the repo root through `/api/settings`; `localStorage.settings` only caches it so the first paint has the right theme. `kami` sets `color-scheme: light`. There are no other themes: the identity is ink and paper.

Highlight colors for marks (`COLORS` in `notes.html`) are fixed hexes stored in the `.md`, so they don't change with the theme.

## Typography

**JetBrains Mono** 400 and 700 for everything: chrome, body, headings, tables, buttons, and brand material.
**Noto Sans JP** 700/900 only for kanji in brand material (the name gloss, section marks, a single character on a cover). Never for UI text. In the app it ships as `app/vendor/noto-sans-jp/`, subset to the brand kanji (独学簡素間渋い静寂墨紙, ~3KB per weight), used through `--kanji` on the project page only. New kanji need a new subset.

The note body has a reader-font switch (`mono` default, `serif`, `inter`) that only affects `.doc` text. Headings stay mono. It is saved in `settings.json` like the theme.

| Role | Size | Notes |
|---|---|---|
| Chrome (waybar, tree, tables) | 13px | |
| Statusline, counts, captions | 12px | |
| Body | 14px / 1.71 | 15px when the reader font is serif or inter |
| Page title (`.cover h1`, exam title) | 22px bold | The only "big" text |
| Note h1 / h2 / h3–h5 | 17 / 15 / 14px bold | Colored blue / cyan / green / yellow / magenta |

Headings are numbered by CSS counters (`1.`, `1.1`, `1.1.1`) and the numbers are not saved to the `.md`.

## Components

### Waybar
`--color-void` bar, 44px tall, three columns (`1fr auto 1fr`).
- **Left:** the 独 mark (`assets/mark.png`, 20px, inverted on light themes), then the workspace module: pill links `1 notes` / `2 exams` / `3 project` / `4 settings`. The mark links to `project`. The active one is filled with accent and `--on-accent` text.
- **Center:** clock, bold `--color-chalk`, `Wed Sep 23   16:30`, 24h, updated every 15s. No decoration.
- **Right:** tool modules, then the theme `<select>`. Each module is a `--color-graphite` rounded rect (radius 8px, 30px tall) holding 24px-tall borderless buttons that hover to `--color-iron`. Pressed buttons fill with accent. Color swatches are 12px circles; the pressed one gets a 1.5px outline ring.
- Tools overflow by horizontal scroll with no scrollbar. They never wrap.

### Explorer
Sticky left column, 18rem wide, inside a 1px `--color-slate` frame with an inverted `explorer` title notch (paper background, carbon text) sitting on the top border, like a TUI panel.
- The tree is built from native `<details open>` per topic. The summary is `slug/` in `--ansi-blue` with a count on the right and a `›`/`⌄` marker. The current topic's summary is filled with accent.
- **Notes, current topic:** a `resources/` subfolder (files with size on the right, links with `↗`), then `notes/` with the live, foldable heading index.
- **Notes, other topics:** their h1 sections as `?topic=slug#id` links, so you can jump between projects without going back to the index.
- **Exams:** each topic lists its exam files. The open exam is `--ansi-yellow`.
- Long names truncate with an ellipsis; the full name is in `title`.

### Content panel
- **Prompt line** above the content: `notes ~/path ❯ command`. Host in green bold, path in blue, `❯` in magenta. It says what the view is (`ls -l`, `nvim notes/`, `exam exam.json`, `exam --check`).
- **Line-number gutter:** every top-level block and every list item gets a CSS counter in `--color-slate`, right-aligned in the left gutter. Figures and margin cards are skipped.
- **`~` filler:** eight tildes after the content, like an empty vim buffer. This is the product's *ma*; never replace it with content.
- **Empty state:** when there are no topics, the stacked lockup (200px, 90% opacity) sits centered above the `slp-init` hint, followed by the tildes.

### htop table
The topic index for both pages. The header row is `--ansi-cyan` with `--on-accent` uppercase labels. Rows are 13px. On hover the whole row fills with accent and all text turns `--on-accent`. Zero counts use `--color-steel`. The topic type uses magenta. Exams hang under their topic as `└─` rows.

### Statusline
Fixed, 24px, `--color-void`, 12px text. Left to right:
- **Mode block:** `NORMAL` (yellow) or `INSERT` (green), bold `--on-accent` text. Notes switch on editor focus. Exams show `INSERT` once any option is picked, then `PASS` or `FAIL` after grading.
- **Path** in `--color-chalk`.
- **Right cluster:** save or progress status, zoom control (magnifier, `−`, numeric %, `+`; 50–250, step 10), width control (`↔`, `−`, numeric px, `+`; 320–2400, step 40), `utf-8[unix]` on `--color-iron`, and scroll position (`Top` / `N%` / `Bottom` / `All`) on green.
- Zoom and width persist in `localStorage` (`zoom`, `width-notes`, `width-exams`).

### Keys (htop function-key buttons)
Buttons are `<kbd>` + label pairs: the key on `--color-void`, the label filled with `--ansi-cyan`, or with accent and bold for the primary action. There is no radius. The key label is a real shortcut: `⏎` triggers the primary key, `Esc` goes back.

### Exam
- Question number `[01]` in orange, then the statement.
- Options render as `( )` / `(•)` text: the native radio is visually hidden but stays focusable. The selected option label turns bold paper.
- Grading shows an htop meter, `Score[|||||||     ]70%`, 40 cells, green at 70% or more and red below. Each option then gets `✓` (green), `✕` + strikethrough (red), or `·` (grey). Explanations are prefixed `//`.

### Note document
- Lists: `- ` markers for `ul` (`· ` nested), decimals for `ol`, markers in orange. Bold is paper, italic is yellow.
- The block selector in the waybar always reflects the block under the caret: `paragraph`, `heading 1` … `heading 6`, `list`, `numbered list`. Picking a value converts the current line in place. From inside a list item, picking a paragraph or heading lifts that line out and splits the list around it. Picking the other list type converts the whole list.
- Typed shortcuts at the start of a line: `/h1`…`/h6`, `/p`, `/list`, `/ol`, `- `, `* `, `1. `.
- Marks: background, underline or strikethrough in the chosen swatch color. A comment adds a `°` in accent.
- Margin cards: a TUI panel like the explorer. `--bg` fill, 1px frame in the card's own color, and a bold `note` / `figure` title cut into the top border in that color; the title is the drag grip. `✕` sits on the right of the border and shows on hover. 55% opacity until hovered.
- Names written into the note HTML stay as they were so saved `.md` files keep rendering: `mk`, `mk-highlight`, `mk-underline`, `mk-strike`, `data-comment`, `card`, `card-body`, `inline`, `ref`, `viz`, `data-kind`, `src`, `view`, `data-x`/`data-y` and the inline `--c`. Renaming any of them needs a migration of every note (see `app/tools/migrate_names.py`).
- Floating menus, tooltips and reference previews: `--color-void` with a 1px `--color-slate` border, no radius.

### Brand touchpoints
- **Favicon:** `mark.png`. **Tab titles:** `独学 · <page>`, set by `mountShell`, which also adds `assets/favicon.svg` (the mark on sumi).
- **README:** horizontal lockup on `#0c0c0c` as the header, tagline below in fog.
- **Social / slides:** e-ink ramp only, JetBrains Mono, one kanji at most per surface.

## Shape and depth

- Radius: 0 for content (cards, menus, keys, tables); 8px for waybar modules; full pills only for workspaces and color swatches.
- No shadows anywhere. Depth is the step between `void`, `carbon` and `graphite`.
- Borders are 1px hairlines. Dashed only between exam questions.

## Do

- Read colors through tokens only. A hex in a component rule breaks every theme but one.
- Say state with ANSI color and a glyph together (`✓`/`✕`, `NORMAL`/`INSERT`), so e-ink, where hues are grey, still reads.
- Keep headings mono and near body size. Tell levels apart by color and counter.
- Put navigation and tools in the waybar, and view and state controls in the statusline.
- Label buttons like terminal keys, and make the shortcut real.
- Leave empty space empty.

## Don't

- Don't add shadows, gradients, or large type.
- Don't add radius to content surfaces.
- Don't make the panel its own scroll container.
- Don't store theme-dependent colors in the `.md`.
- Don't use accent fills for anything but the current selection or the primary action.
- Don't use kanji as UI labels or decoration. 独学 is the mark, nothing more.
- Don't recolor or retype the logo.

## Files

| File | Owns |
|---|---|
| `style.css` | Tokens, the sumi and kami blocks, and shared components (waybar, explorer, tables, statusline, keys, viz) |
| `theme.js` | Theme list, settings load/save (`settings`, `saveSettings()`), applies theme and reading font, `themeSelector()` markup, `pickTheme()` |
| `shell.js` | `mountShell(page)` injects waybar (with the 独 mark), explorer, panel and statusline; runs the clock, scroll position, zoom and width. Returns `{ app, tree, tools, path, mode }` |
| `notes.html` | Editor-specific styles and logic: tools, tree index, document |
| `exam.html` | Exam styles and logic: tree of exams, questions, meter |
| `project.html` | The `/project` page: what SLP is, the three windows, the loop, the pieces, the principles |
| `settings.html` | The `/settings` page: profile, theme and reading font |
| `viz.js` | Mermaid and KaTeX; the Mermaid theme is built from the ramp tokens |
| `assets/` | `lockup-horizontal.png`, `lockup-stacked.png`, `mark.png` (white on transparent) |
