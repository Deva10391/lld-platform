# Design Note

## MVP scope
5 seeded problems, one submission format (TEXT_DESIGN), one evaluation flow (deterministic + LLM composite), feedback with per-dimension scores + comments, full attempt history. Monolith: FastAPI + SQLite.

## User flow
Pick problem → start attempt → submit text design → see rubric feedback (or retry if AI evaluation failed) → check history anytime.

## Key classes/interfaces (`backend/`)
- `Problem`, `Attempt`, `Submission`, `EvaluationResult` — ORM domain models. `Attempt` owns a `status` [state field driving the lifecycle] so partial/failed states are first-class, not exceptions.
- `Evaluator` (ABC) — interface with one method `evaluate(problem_title, problem_description, content) -> EvalOutcome`. Any new evaluation approach implements this and nothing else changes.
- `DeterministicEvaluator` — rule-based (regex/keyword) checks. Cannot fail, always returns a result — the guaranteed floor of feedback.
- `LLMEvaluator` — calls Anthropic API for judgment dimensions; raises on failure instead of guessing.
- `CompositeEvaluator` — the only evaluator `main.py` talks to (Facade [interface hiding subsystem complexity]). Merges both, decides `evaluated_by` and fallback policy.

## Evaluation approach
Rubric dimensions split by what's checkable objectively vs. needs judgment:

| Deterministic | LLM (judgment) |
|---|---|
| structure_presence | responsibility_design |
| testability_edge_cases | coupling_cohesion |
| requirement_understanding | abstraction_patterns, extensibility, explanation_quality |

No single reference solution — feedback is evidence-based comments per dimension, not a diff.

## Failure/slowness handling
Kept practical, no queues/workers:
- `Attempt.status`: PENDING → EVALUATING → COMPLETED / PARTIAL / FAILED.
- LLM call wrapped in try/except inside `CompositeEvaluator.run` → on failure, attempt still gets deterministic scores (`PARTIAL`), never blank.
- `POST /attempts/{id}/retry` re-runs evaluation on the same stored submission — no re-typing needed.
- Deterministic evaluator failing (should be rare — pure logic) → `FAILED` with `error_message`, retryable.

## Extensibility (accommodating another format/approach later)
- New submission format (CODE, DIAGRAM): add enum value to `SubmissionFormat`, no schema change to `Attempt`/`EvaluationResult`.
- New evaluation approach (e.g. static analysis for CODE, different LLM provider): implement `Evaluator`, pass into `CompositeEvaluator(deterministic=..., llm=...)` — swap without touching `main.py` routes.
- Rubric dimensions are dict-keyed, not hardcoded columns → adding a dimension is a code change in one evaluator, not a migration.

## Trade-offs (MVP scope, 2 days)
- One submission format only (text) — smallest format proven sufficient for evidence per the assignment guide; code/diagram deferred.
- Synchronous evaluation (no background queue) — acceptable at this scale; `EVALUATING` status + retry endpoint models the practical failure case without distributed-systems overhead.
- No auth — `user_id` is a free-text field, sufficient to demo history per learner.
