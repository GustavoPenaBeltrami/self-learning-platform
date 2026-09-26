# Sources

How every skill and agent finds, uses and arbitrates study material.

## What counts as a source

- Every file in `topics/<slug>/resources/`, declared or not. Files the user uploads in the app land here. Never edit them.
- Each entry of `topic.json` `links`: `{title, url}` or `{title, path}` (a file anywhere on disk; `~` is allowed).
- A `path` that doesn't exist: say so in one line and continue with the rest. Never stop for it.
- The topic's `wiki/` is compiled from these; it is a map, not a source. Cite the source behind it.

## Where to look: `sources_mode`

| `sources_mode` | Look in |
|---|---|
| `local` | `resources/` and `path` entries only |
| `web` | the web (`WebSearch`, `WebFetch`) and `url` entries |
| `both` (default, also when missing) | local first, then the web |

With `local`, or with no connection, verify only against local sources and say plainly "not verified on the web" for any claim you couldn't check there. Never state a fact from memory to fill the gap.

Order of trust: the topic's own material, then official docs, specifications and primary sources, then everything else.

## Citing

Every claim that came from a source carries it: a link for URLs, the file name for local files. In the wiki, a footnote keyed by `sources[].id` ([formats.md](formats.md#wiki)).

## When sources disagree

Pick one; never hand the conflict to the learner in the chat.

1. An existing `Source choice` entry on the same claim in the `learning.md` Record decides it. Follow it.
2. Otherwise the topic's own material (`links`, `resources/`) wins, **unless it is outdated for the Mission** (a certification that tests the current version of a service).
3. Teach, grade or write the chosen version with confidence and cite it.
4. Record the choice in the Record, exactly:

```md
### 0004 — 2026-09-25 — Source choice: S3 read-after-write consistency
Taught: strong for every write, from [AWS docs](https://aws.amazon.com/s3/consistency/).
Not taught: eventual for overwrites, from `resources/course-2019.pdf`.
Why: topic material outdated for the Mission (the exam tests the current service).
```

Graders grade against the taught version: a student never loses points for learning what they were taught.

## Verifying

Doubt a fact, name, date, formula or definition even slightly: verify it before saying or writing it, with the `researcher` agent (`agent/agents/researcher.md`). Its verdicts: `correct`, `correct (local only)`, `incorrect`, `unverifiable`. If the check changes what you were going to say, say so openly.
