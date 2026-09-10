# AI Usage

1. **Evaluator split (deterministic vs. LLM)** — AI suggested scoring all 8 rubric dimensions via LLM only. Rejected: kept 3 objective dimensions (structure, edge-cases, requirement coverage) as regex/keyword-based deterministic checks. Reason: they don't need judgment, and a guaranteed non-AI floor means an attempt is never left with zero feedback if the LLM is down.

2. **Failure handling** — AI initially proposed a background job queue (Celery/Redis) for resilience. Rejected as over-engineering for a 2-day monolith per the assignment's own "keep this practical" guidance. Accepted instead: synchronous call wrapped in try/except with a `PARTIAL` status and a `/retry` endpoint — same practical outcome, no infra.

3. **Submission format** — AI suggested supporting text + diagram (Mermaid) + code from day one. Rejected: narrowed to text-only for MVP (smallest format that proves design reasoning), but accepted AI's suggestion to make `format` an enum field on `Submission` now so adding formats later needs no schema migration.

4. **Seed problems** — Asked AI to draft descriptions for 5 problems; accepted 4 largely as-is, rewrote Elevator's description to add "maintenance/out-of-service mode" so it forces an edge-case discussion (the deterministic evaluator's edge-case scoring becomes meaningful for it).

5. **Frontend** — Accepted AI-generated single-file HTML/JS as-is (no framework) since it's not graded on UI polish; asked for and rejected an AI suggestion to add localStorage-based "save draft" since it wasn't needed for the practice loop and added complexity.
