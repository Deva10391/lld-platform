# Research Note

## Learner problem
Practicing LLD [Low-Level Design: class/interface/responsibility-level design, as opposed to HLD which is system/infra-level] is hard because:
- No compiler/test-runner tells you if a design is "correct" — multiple valid designs exist.
- Self-assessment is unreliable; learners don't know their own blind spots (coupling, missing edge cases).
- No memory of past attempts → same mistakes repeat.

## Existing approaches looked at
- **LeetCode/HackerRank-style judges**: great for algorithms, useless for LLD — no single correct output to diff against.
- **Educative/Grokking LLD courses**: teach patterns via reading, but give no personalized feedback on a learner's own submission.
- **GitHub "LLD practice" repos** (community solutions): show one reference solution per problem — implicitly treats it as "the" answer, discouraging valid alternatives.
- **Generic AI chat (ask ChatGPT to review my design)**: gives feedback but no rubric consistency, no history, no structured comparison across attempts.

## Gaps identified
1. No tool separates **objective** checks (did you even define classes? mention edge cases?) from **subjective** judgment (is your abstraction appropriate?).
2. No tool tracks **attempt history** so a learner sees if they're repeating the same weakness.
3. Reference-solution-only tools punish valid alternative designs.
4. Nothing has a resilience story for "AI evaluation is slow/down."

## Product direction
A rubric-based platform: deterministic checks for objective evidence (structure, edge-case mentions, requirement coverage) + LLM judgment for design-quality dimensions (cohesion, abstraction, extensibility, explanation) — never a single reference-solution diff. Every attempt is stored so learners see growth over time.
