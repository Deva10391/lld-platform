# LLD Practice Platform (MVP)

Practice LLD problems (Parking Lot, Elevator, etc.), submit a text design, get rubric + AI feedback, track attempt history.

## Run it

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Open `frontend/index.html` directly in a browser (it calls `http://localhost:8000`).

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
