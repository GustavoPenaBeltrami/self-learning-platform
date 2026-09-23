# The agent resolves source conflicts itself, without flagging them

When a topic's sources disagree (say the learner's PDF is the 2nd edition and the web describes the 3rd), the agent picks one and teaches it with confidence instead of telling the learner the sources are inconsistent: judging sources is part of what a teacher brings, and hedging in front of a learner erodes trust in the lesson. The topic's own material wins unless it is outdated with respect to the topic's Mission (for example, a certification that tests the current version). The agent still cites the source it used, and records the choice in the topic's `learning.md`, so later exams and grading stay consistent with what was taught.

## Considered Options

- **Flag the discrepancy in the chat** and let the learner decide: transparent, but it hands the learner a judgment they are studying precisely because they can't make it yet.
- **Decide without citing**: confident, but breaks the rule that every claim in a lesson carries its source, and leaves grading with no trace of which version was taught.
