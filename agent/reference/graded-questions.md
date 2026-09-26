# Graded questions

Rules for any question with a correct answer: in the chat (`slp-teach`, `slp-quiz`, `slp-init`) or in an `exam.json` (`slp-exam`, `slp-quiz`).

## In the chat

- Ask with `AskUserQuestion`: one question, the options, nothing else.
- **Grade in the very next message**, before anything else: ✓/✗, which option was correct, and what confusion the chosen option represents. The grading is the part that teaches. Never move on with a question left ungraded.
- A question with no correct answer (goals, preferences) is asked the same way and not graded.
- Offer an "I don't know" option when locating a level: it is a distinct, honest signal, recorded as a miss.

## Building the options

Balance comes from construction, not from an audit at the end.

1. **Every option is a bare statement.** No "because" in any option. The number one tell is the correct option carrying its reasoning and ending up longer. All reasoning goes in the grading or `explanation`.
2. **Write the correct statement first, then mutate it into each distractor.** Take a real confusion or a near neighbor and write what someone holding it would claim, with the same skeleton, length, grain and register.
3. Each distractor is a mistake the learner could genuinely make (so the pick is diagnostic) and unambiguously wrong: tempting, not tricky.
4. **No asymmetric bold.** Bold nothing, or the parallel term in every option.

If you can guess the answer by reading the set cold, you skipped 1 or 2: regenerate the set, don't patch it.

## Quality rules (exam files)

- `multiple_choice` has exactly 4 options and one correct `answer` (0-3). Spread `answer` across 0-3 over the exam.
- Forbidden: "all of the above", "none of the above", "A and C", double negatives.
- One question tests one idea.
- `explanation` says why the correct one is correct **and** what confusion each distractor represents. A single generic line is badly written.
- Everything comes from the source material ([sources.md](sources.md)). If something is needed and isn't there, don't invent it: flag it to the user.

## Rubrics (`open`, `oral`, `practical`)

3 to 5 short points, each checkable ✓/✗ by reading the answer: a concrete concept or criterion ("mentions the wiretap problem"), never "understands the topic". Not a model answer: a rubric lets paraphrase pass. Touching the word without the concept doesn't.

## Locating the edge of what they know

A mapping job, not a sample. Used by `slp-teach` phase 1a and `slp-quiz`.

- Skip what the `learning.md` Record already shows as floor. Do probe recorded misconceptions: neighboring topics are where they come back.
- A thread's edge is located only when **bounded on both sides**: a floor (answered correctly at that level) and a ceiling (missed, or "I don't know").
- **All correct means the questions were easy.** Go up sharply until something breaks.
- **Binary search**: after a hit raise the difficulty hard; after a miss come back down to pin it.
- A wrong answer is a coordinate, not a cue to start teaching. Probe around it: slip, isolated gap, or systematic misconception? A misconception held with confidence has to be measured and evicted.
- Map every thread the goal depends on, and none it doesn't.
- Done when you can say, per thread, what they have and where it runs out.
