---
name: notes-summarize
description: Summarizes a text (pasted, attached, or from the topic's resources/) and appends it to a note in topics/*/notes/*.md, in the topic's configured notes language unless the user asks for another. Use when the user says "summarize this", "/notes-summarize", "add this summary to the note", or pastes/attaches a fragment of a book/article to condense.
---

# Summarize

Summarizes technical text and appends it to an existing notes file (`topics/<topic>/notes/*.md`), following the same format those notes already use.

## Required data (ask together if missing)

1. **Source**: where the text comes from —
   - **pasted**: it comes in the message.
   - **attached**: a PDF/image the user attached — read it with `Read`.
   - **`resources/`**: a file already saved in `topics/<topic>/resources/` — ask which one if they don't say.
   - **local path**: a `path` source from the topic's `topic.json` `links`. If the file doesn't exist, say so in one line and ask for another source.
2. **Destination**: which topic and which file in `notes/` (e.g. `topics/example/notes/01-methods-and-codes.md`). If the user is already working on a note in the conversation, use that one without asking again.
3. **Summary level** (if they don't say, use `medium`):
   - **compact**: very compact, just bullets with the key idea of each concept. No elaboration, no examples unless essential.
   - **medium** (default): shorter than the original but with enough explanation to understand the concept without reading the source text. Includes the most important examples.
   - **extensive**: developed, close to full study notes. Keeps nuances, most of the examples and the original's distinctions, but it's still a summary (not a translation).
4. **Output language**: an explicit request from the user ("summarize it in English") wins; otherwise default to `language.notes` from `topic.json`. If the topic has no `language` set, ask once (and not again in the same session).

If you already have the data (from the conversation context or because the user gave it), don't ask: summarize directly.

## Before writing

Look at how the destination note is structured (and if needed, `app/server/text.py` / `app/server/server.py` to understand the general convention of `topics/*/notes/`):

- Each `.md` in `notes/` starts with a `# ` (h1, the note's title) — that h1 is what the editor uses to split the file into sections when saving from the UI. Don't add a second h1.
- Topics within the note go as `##`; subtopics, as `###`.
- Lists with `- ` (dash + space), one idea per item.
- Normal paragraphs for prose explanation.
- Raw HTML (`<img>`, `<mark>`, etc.) is left as is if it already exists in the note; don't invent new markup.
- A ```` ```mermaid ```` or ```` ```math ```` fence is rendered in `notes.html`. Use it only if the
  original text describes a structure or a formula that is better understood
  drawn, never as decoration.

## Summary rules

- Write in the output language (above), naturally, in study-notes style — not a literal translation, explain the idea.
- Important technical terms are kept in their original language if it differs from the output language (with their explanation if needed), e.g. *technical breadth*, *trade-off*, *coupling*.
- Don't add information that isn't in the original text.
- Don't add a conclusion or repeat concepts already stated.
- If the text has examples, keep the most important ones (more at the `extensive` level, fewer at `compact`).
- If part of the text is already covered in the note (redundant with something summarized before), don't duplicate it: integrate it or say you're merging it instead of repeating it.

## How to add it

Append the summary at the **end** of the destination file, as new section(s) (`##`/`###` depending on the level of detail of the text given — a text with its own subheadings in another language gets its own translated subheadings). Use Edit (append at the end of the file), don't rewrite what's already there unless the user explicitly asks to restructure an existing part.

## After writing

Report in 1-2 lines which heading(s) were added and in which file. Don't repeat the full summary in the chat if it's already written in the file.
