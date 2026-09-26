# 独学 SLP — Design & Brand Reference
> 独学 (*dokugaku*) means self-study. SLP is a terminal-style study tool: a waybar on top, a file explorer on the left, a vim buffer in the middle, a statusline at the bottom. One person, one topic, and a quiet screen.

**Themes:** `sumi` 墨 (dark, default when the OS is dark) · `kami` 紙 (light, default when the OS is light) · `seed` (dark, generated from one color the user picks)

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
| 静寂 | **seijaku** | Calm | Chrome lives in two bars. The content between them stays silent. No toasts, no motion beyond 120ms color fades (the recording pulse is the one exception, and only without reduced motion) |

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
│ [独] (1 notes)(2 exams)(3 cards)(4 project)(5 settings) Wed Sep 23 [theme▾]│
├──────────────┬──────────────────────────────────────────────────────┤
│┌ explorer ┐  │   notes ~/topics ❯ ls -l                             │
││ ⌄ topic-a/2│  │   # TOPIC                    TYPE    SECT  RES       │
││  1 Intro   │  │   01 Fundamentals of …       book       2    1       │
││ ⌄ topic-b/4│  │ ~                                                    │
│└───────────┘  │ ~                                                    │
├──────────────┴──────────────────────────────────────────────────────┤
│ NORMAL ~/notes/topics      🔍 − 100% +  ↔ − 960px +  utf-8[unix]  All │
└─────────────────────────────────────────────────────────────────────┘
```

- The page scrolls as a document. The waybar is `position: sticky`, the explorer is sticky under it, and the statusline is `position: fixed`. There is no inner scroll container. The notes editor positions margin cards and menus against `scrollY`, so keep it that way.
- The content column is centered in the panel: `max-width: calc(var(--width) + 2 * var(--gutter))`, with symmetric gutter padding. `--width` is set from the statusline (default 960px, shared by every page).
- The content zoom (statusline 🔍) applies CSS `zoom` to `#app` only. Chrome, explorer and bars never zoom. Any code that mixes `clientX/Y` with `offsetLeft/Top` inside `#app` must divide by the zoom (see card drag in `notes.html`).
- The session control sits in the statusline on pages with a topic in context (`?topic=` or an exam being sat): `▶ session` starts one, `● 00:42 ■` (red, hours:minutes since start) stops it. It re-reads `/api/session/<slug>` every 30s, because any save in the topic opens a session behind the scenes and 30 idle minutes close it.
- Below 900px the explorer hides, the clock hides, and workspace labels collapse to numbers. Below 1280px margin cards stop floating and sit inline.

## Color

The brand is ink on paper: **sumi 墨** `#0c0c0c` and **kami 紙** `#e6e6e6`, with the grey ramp between them. Brand material uses only this ramp and never takes a hue. In the app, `sumi` is the ramp as below and `kami` is the same ramp inverted; the optional `seed` theme is the one place a hue enters (see Seed theme).

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

The short names (`--bg`, `--ink`, `--muted`, `--line`, `--accent`, `--good`, `--bad`) are aliases kept so page-level CSS stays short. `viz.js` reads the ramp for Mermaid (resolved to `rgb()` first, so generated colors work too), so diagrams follow the theme and repaint on the `theme-changed` event.

### Themes

| Key | Character | Carbon | Paper | Accent |
|---|---|---|---|---|
| `sumi` | Ink. Monochrome dark; every ANSI hue is a grey | `#141414` | `#e6e6e6` | `#d4d4d4` |
| `kami` | Paper. The sumi ramp inverted; logos use `filter: invert(1)` via `--logo` | `#e6e6e6` | `#0c0c0c` | `#1b1b1b` |
| `seed` | One color. The ramp tinted with the seed hue, accent = the seed, real ANSI hues | L .19 | L .94 | L .8 |

Theme selection lives in `theme.js`. The saved `theme` is `""` (auto), `sumi`, `kami` or `seed`. `theme.js` always writes the *effective* theme to `data-theme` on `<html>`: auto resolves to `kami` or `sumi` from `prefers-color-scheme` and follows OS changes live through a `matchMedia` listener. Unknown saved keys (old themes) behave as auto. The waybar selector and the settings page share `THEME_CHOICES` (`auto`, `sumi`, `kami`, `seed`). The choice persists in `settings.json` at the repo root through `/api/settings`; `localStorage.settings` only caches it so the first paint has the right theme. `kami` sets `color-scheme: light`.

### Seed theme

`seed` is built from one color, `theme_seed` in `settings.json` (`#rrggbb`, picked with the native color input in settings; picking it also switches the theme to `seed`). `theme.js` sets it as `--seed` on `<html>`; the `:root[data-theme="seed"]` block derives every token with CSS relative color syntax (`oklch(from var(--seed) L c h)`):
- The ramp keeps the seed's hue with its chroma cut to 4-15%, at fixed lightness steps (void .15 → paper .94), so contrast is the same as sumi whatever the seed.
- The accent is the seed at lightness .8 with chroma capped at .15, so `--on-accent` (void) stays readable on it.
- The seven ANSI hues are fixed oklch colors at lightness .72-.84, independent of the seed.
It is a dark theme only. Browsers without relative color syntax (Chrome < 119, Safari < 16.4, Firefox < 128) cannot render it.

Highlight colors for marks (`PALETTE` in `notes.html`) are fixed hexes stored in the `.md` (`--c:#d8c06a`), so they look the same in every theme and in Obsidian, and the swatches show those real colors. Old notes that stored `var(--ansi-x, #hex)` are converted to the plain hex when opened.

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
- **Left:** the 独 mark (`assets/mark.png`, 20px, inverted on light themes), then the workspace module: pill links `1 notes` / `2 exams` / `3 cards` / `4 project` / `5 settings`. The mark links to `project`. The active one is filled with accent and `--on-accent` text.
- **Center:** clock, bold `--color-chalk`, `Wed Sep 23   16:30`, 24h, updated every 15s. No decoration.
- **Right:** tool modules, then the theme `<select>` (`auto`, `sumi`, `kami`, `seed`). Each module is a `--color-graphite` rounded rect (radius 8px, 30px tall) holding 24px-tall borderless buttons (radius 6px, so they nest inside the module) that hover to `--color-iron`. Pressed buttons fill with accent. Color swatches are 12px circles; the pressed one gets a 1.5px outline ring.
- Tools overflow by horizontal scroll with no scrollbar. They never wrap.

### Explorer
Sticky left column, 18rem wide, inside a 1px `--color-slate` frame with an inverted `explorer` title notch (paper background, carbon text) sitting on the top border, like a TUI panel.
- The tree is built from native `<details open>` per topic. The summary is `slug/` in `--ansi-blue` with a count on the right and a `›`/`⌄` marker. The current topic's summary is filled with accent.
- **Notes, current topic:** a `resources/` subfolder (files with size on the right, web links with `↗`, local `path` sources marked `local` and opened through `/api/source`, and a `+ add` row that uploads files to `resources/` or adds a link or path to `topic.json`), then `notes/` with the live, foldable heading index.
- **Notes, other topics:** their h1 sections as `?topic=slug#id` links, so you can jump between projects without going back to the index.
- **Exams:** each topic lists its exam files. The open exam is `--ansi-yellow`.
- Long names truncate with an ellipsis; the full name is in `title`.

### Content panel
- **Prompt line** above the content: `notes ~/path ❯ command`. Host in green bold, path in blue, `❯` in magenta. It says what the view is (`ls -l`, `nvim notes/`, `exam exam.json`, `exam --check`).
- **Line-number gutter:** every top-level block and every list item gets a CSS counter in `--color-slate`, right-aligned in the left gutter. Figures and margin cards are skipped.
- **`~` filler:** eight tildes after the content, like an empty vim buffer. This is the product's *ma*; never replace it with content.
- **Empty state:** when there are no topics, the stacked lockup (200px, 90% opacity) sits centered above the `slp-init` hint, followed by the tildes.

### htop table
The topic index for notes, exams and cards. The header row is `--ansi-cyan` with `--on-accent` uppercase labels. Rows are 13px. On hover the whole row fills with accent and all text turns `--on-accent`. Zero counts use `--color-steel`. The topic type uses magenta. Exams hang under their topic as `└─` rows.

### Statusline
Fixed, 24px, `--color-void`, 12px text. Left to right:
- **Mode block:** `NORMAL` (yellow) or `INSERT` (green), bold `--on-accent` text. Notes switch on editor focus. Exams show `INSERT` once any option is picked, then `PASS` or `FAIL` after grading. Cards show `INSERT` while a card is revealed.
- **Path** in `--color-chalk`.
- **Right cluster:** save or progress status, zoom control (magnifier, `−`, numeric %, `+`; 50–250, step 10), width control (`↔`, `−`, numeric px, `+`; 320–2400, step 40), `utf-8[unix]` on `--color-iron`, and scroll position (`Top` / `N%` / `Bottom` / `All`) on green.
- Zoom and width persist in `localStorage` (`zoom`, `width`), shared by every page.

### Keys (htop function-key buttons)
Buttons are `<kbd>` + label pairs: the key on `--color-void`, the label filled with `--ansi-cyan`, or with accent and bold for the primary action. There is no radius. The key label is a real shortcut: `⏎` triggers the primary key, `Esc` goes back (asking first when answers would be lost). Exams add `R` (record, again to stop) and `T` (answer in writing) on oral questions; cards use `Space` flip, `1` again, `2` good, `A` study all.

### Exam
- Question number `[01]` in orange, then the statement.
- Options render as `( )` / `(•)` text: the native radio is visually hidden but stays focusable. The selected option label turns bold paper.
- Grading shows an htop meter, `Score[|||||||     ]70%`, 40 cells, green at 70% or more and red below. Each option then gets `✓` (green), `✕` + strikethrough (red), or `·` (grey). Explanations are prefixed `//`.

### Cards
- `cards.html` (the `3 cards` workspace): htop index of topics with `CARDS`, `DUE` and `UNSURE`; `?topic=<slug>` opens the deck. Cards live in `cards/cards.json`: the agent writes them (`slp-cards`), or you do, by hand, in the app. The app never derives them on its own.
- Due cards only by default. The card is a literal card: a centered `--color-graphite` tile (14px radius, 520px max) with the question and `NN / MM`; `Space Reveal` sits under it. On hover it lifts (translate + shadow, the one place with a shadow; off under reduced motion). Clicking it or `Space` reveals: the app blurs behind a full-screen layer and the card flips (rotateY, 0.5s) to its back: the question small, the answer, the `// H1 › H2` note link. Three choices under it: `1 Don't know` (back to the end of the deck), `2 Knew it`, `3 Unsure` (sets `flagged: true` in `cards.json` and counts as don't know without repeating it; `/slp-session` goes over flagged cards with the agent). `Esc` or a click outside puts the card back face down. Focus goes to the layer, never to a choice, so a stray `Space` can't grade. Only the first rating per card is saved, in one batch at the end (and on `pagehide`), to `cards/reviews.jsonl`.
- Actions live in the waybar tools, like the notes toolbar: `new N`, `edit E`, `list L` (pick a card, edit or delete it), `skip S` (next card without revealing), `delete D`, `study all A`, `back Esc`.
- Scheduling is Leitner, derived by the server from `reviews.jsonl`: box = consecutive goods since the last again (max 3), due after 0 / 1 / 3 / 7 days.
- The form is a modal `<dialog class="card-form">` from `cardForm()` in `shell.js`: front, back, and an optional note with the topic's `H1 › H2` headings as suggestions; `⌘⏎` saves, `Esc` cancels. Manual cards get `"by": "user"`.
- In notes, the flashcard tool in the waybar opens the same form with the selection as the back and the caret's `H1 › H2` as the note.
- Empty states: `no cards yet — press N to write one, or ask your agent: /slp-cards`, or `nothing due · next in X` with `A` to study all.

### Note document
- Lists: `- ` markers for `ul` (`· ` nested), decimals for `ol`, markers in orange. Bold is paper, italic is yellow.
- The block selector in the waybar always reflects the block under the caret: `paragraph`, `heading 1` … `heading 6`, `list`, `numbered list`. Picking a value converts the current line in place. From inside a list item, picking a paragraph or heading lifts that line out and splits the list around it. Picking the other list type converts the whole list.
- Typed shortcuts at the start of a line: `/h1`…`/h6`, `/p`, `/list`, `/ol`, `- `, `* `, `1. `.
- Marks: background, underline or strikethrough in the chosen swatch color. A comment adds a `°` in accent.
- Margin cards: a TUI panel like the explorer. `--bg` fill, 1px frame in the card's own color, and a bold `note` / `figure` title cut into the top border in that color; the title is the drag grip. `✕` sits on the right of the border and shows on hover. 55% opacity until hovered.
- Names written into the note HTML stay as they were so saved `.md` files keep rendering: `mk`, `mk-highlight`, `mk-underline`, `mk-strike`, `data-comment`, `card`, `card-body`, `inline`, `ref`, `viz`, `data-kind`, `src`, `view`, `data-x`/`data-y` and the inline `--c`. Renaming any of them needs a migration of every note.
- Floating menus, tooltips and reference previews share the `.float` surface in `style.css`: `--color-void` with a 1px `--color-slate` border, no radius. They close on outside click, `Esc` and scroll.
- Pasted, dropped or picked images are uploaded once (`POST /api/topic/<slug>/img`) and inserted by URL; the note never holds base64.
- Paste is plain text; rich HTML from other apps is dropped.
- Autosave is debounced (900ms), serialized, and sends the `stamp` from the last load or save. A 409 (notes changed on disk) stops saving, keeps your version in `localStorage` and offers `reload`; after the reload the statusline offers `restore` or `discard`.

### Brand touchpoints
- **Favicon:** `mark.png`. **Tab titles:** `独学 · <page>` (`独学 · <topic or exam title>` once one is open), set by `mountShell`, which also adds `assets/favicon.svg` (the mark on sumi).
- **README:** horizontal lockup on `#0c0c0c` as the header, tagline below in fog.
- **Social / slides:** e-ink ramp only, JetBrains Mono, one kanji at most per surface.

## Shape and depth

- Radius: 0 for content and every plain button (cards, menus, keys, tables, form controls); 8px for waybar modules (`--radius-mod`) and 6px for the buttons inside them (`--radius-in`); full pills only for workspaces and color swatches.
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
| `style.css` | Tokens, the sumi, kami and seed blocks, and shared components (waybar, explorer, tables, statusline, keys, `.float`, `.recording`, viz) |
| `theme.js` | `THEMES`/`THEME_CHOICES`, settings load/save (`settings`, `saveSettings()`), applies the effective theme, seed and reading font, `themeSelector()`, `pickTheme()`; `api()` (throws with `status` and `data`), `esc()`, `clean()` (sanitizes note HTML into a fragment), `optionTags()` |
| `shell.js` | `mountShell(page)` injects waybar (with the 独 mark), explorer, panel and statusline; runs the clock, scroll position, zoom, width and the session control. Returns `{ app, tree, tools, path, mode }`. Helpers: `key()`, `promptLine()`, `folder()`, `offline()`, `noTopicsRow()`, `hotkey()` (the dictation shortcut from `dictation_key`), `placeNear()`, `dropMenu()`/`dropdown()`, `cardForm()`/`deleteCard()` |
| `notes.html` | Editor-specific styles and logic: tools, tree index, document |
| `exam.html` | Exam styles and logic: tree of exams, questions, meter |
| `cards.html` | Flashcards: topic index with due counts, deck session, ratings batch |
| `project.html` | The `/project` page: what SLP is, quick start, how it works, AI teacher, your topics, the principles |
| `settings.html` | The `/settings` page: profile, theme, seed color, ui font, dictation shortcut, voice model, font upload |
| `viz.js` | Mermaid and KaTeX; the Mermaid theme is built from the ramp tokens |
| `assets/` | `lockup-horizontal.png`, `lockup-stacked.png`, `mark.png` (white on transparent) |
