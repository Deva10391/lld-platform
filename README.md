# LLD Practice Platform (MVP)
 
## Problem
 
LLD practice has no quick, repeatable feedback on a written design.
 
## Solution
 
Pick one of 5 seeded problems (Parking Lot, Elevator System, Library Management, Vending Machine, Ride-Sharing Matching), submit a text design, and get 0–5 scores with a comment per rubric dimension. A deterministic evaluator scores structure, edge-case coverage and requirement coverage. An LLM evaluator (Anthropic API) scores responsibility design, coupling/cohesion, abstraction/patterns, extensibility and explanation quality. If the LLM call fails, the attempt is saved as `PARTIAL` with deterministic scores and can be re-evaluated via the retry endpoint.
 
## Speciality
 
- Evaluation split by what is objectively checkable vs. what needs judgment.
- Attempt lifecycle (PENDING → EVALUATING → COMPLETED / PARTIAL / FAILED) makes failures a normal state, not an exception.
- `Evaluator` interface + `CompositeEvaluator` facade: new formats or evaluators plug in without touching routes.
- Per-user attempt history.
## Simplified Working
 
You write your design, the app checks the checkable parts by rules and the judgment parts by an AI reviewer, and keeps every attempt.
 
## Utilities
 
- FastAPI — API
- SQLAlchemy + SQLite — storage
- Anthropic API — judgment scoring
- pytest — tests
## Run it
 
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
 
Open
```
frontend/index.html
```
directly in a browser (it calls `http://localhost:8000`).
 
## Test
 
```bash
python -m pytest tests/ -v
```
 
## API
| Endpoint | Purpose |
|---|---|
| `GET /problems` | List seeded problems |
| `POST /attempts` | Start an attempt `{user_id, problem_id}` |
| `POST /attempts/{id}/submit` | Submit design text, triggers evaluation |
| `POST /attempts/{id}/retry` | Re-evaluate if AI eval failed/partial |
| `GET /attempts/{id}` | Get attempt + result |
| `GET /users/{user_id}/history` | Past attempts for a learner |
 
See `DESIGN_NOTE.md` for architecture, `RESEARCH_NOTE.md` for problem research, `AI_USAGE.md` for AI-assisted decisions.
 
## Limitations (by design, MVP)
- Text submissions only (no code/diagram parsing yet — extensible via `SubmissionFormat`).
- Synchronous evaluation, no auth, no distributed queue — see DESIGN_NOTE "Trade-offs."