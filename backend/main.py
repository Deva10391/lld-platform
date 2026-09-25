from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import Base, engine, get_db
import models
from models import Attempt, Submission, EvaluationResult, Problem, AttemptStatus
import schemas
from seed_data import seed
from evaluators import CompositeEvaluator

Base.metadata.create_all(bind=engine)
app = FastAPI(title="LLD Practice Platform")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

evaluator = CompositeEvaluator()

# Seed at import time (not just on startup event) so both `uvicorn main:app`
# and TestClient(app) without a lifespan context see the seeded problems.
_seed_db = next(get_db())
seed(_seed_db)
_seed_db.close()


@app.get("/problems", response_model=list[schemas.ProblemOut])
def list_problems(db: Session = Depends(get_db)):
    return db.query(Problem).all()


@app.get("/problems/{problem_id}", response_model=schemas.ProblemOut)
def get_problem(problem_id: int, db: Session = Depends(get_db)):
    p = db.query(Problem).get(problem_id)
    if not p:
        raise HTTPException(404, "problem not found")
    return p


@app.post("/attempts", response_model=schemas.AttemptOut)
def start_attempt(body: schemas.AttemptCreate, db: Session = Depends(get_db)):
    print(body.problem_id)
    if not db.query(Problem).get(body.problem_id):
        raise HTTPException(404, "problem not found")
    attempt = Attempt(user_id=body.user_id, problem_id=body.problem_id, status=AttemptStatus.PENDING)
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    attempt_json = {
        column.name: getattr(attempt, column.name)
        for column in attempt.__table__.columns
    }
    print(attempt_json)
    return attempt_json


def _run_evaluation(db: Session, attempt: Attempt, content: str):
    """Shared by submit and retry. Never leaves an attempt without a clear status."""
    attempt.status = AttemptStatus.EVALUATING
    db.commit()
    try:
        out = evaluator.run(attempt.problem.title, attempt.problem.description, content)
    except Exception as e:  # deterministic evaluator itself failing = genuine failure
        attempt.status = AttemptStatus.FAILED
        attempt.error_message = str(e)
        db.commit()
        return

    if attempt.result:
        db.delete(attempt.result)
        db.flush()

    result = EvaluationResult(
        attempt_id=attempt.id,
        dimension_scores=out["dimension_scores"],
        overall_score=out["overall_score"],
        comments=out["comments"],
        evaluated_by=out["evaluated_by"],
    )
    db.add(result)
    attempt.status = AttemptStatus.COMPLETED if out["evaluated_by"] == "deterministic+llm" else AttemptStatus.PARTIAL
    attempt.error_message = out["llm_failed_reason"]
    db.commit()


@app.post("/attempts/{attempt_id}/submit", response_model=schemas.AttemptOut)
def submit_attempt(attempt_id: int, body: schemas.SubmissionCreate, db: Session = Depends(get_db)):
    attempt = db.query(Attempt).get(attempt_id)
    if not attempt:
        raise HTTPException(404, "attempt not found")
    if attempt.submission:
        raise HTTPException(400, "attempt already submitted; use /retry to re-evaluate")
    if len(body.content.strip()) < 10:
        raise HTTPException(422, "submission is too short to evaluate")

    db.add(Submission(attempt_id=attempt.id, content=body.content))
    db.commit()
    db.refresh(attempt)

    _run_evaluation(db, attempt, body.content)
    db.refresh(attempt)
    return attempt


@app.post("/attempts/{attempt_id}/retry", response_model=schemas.AttemptOut)
def retry_attempt(attempt_id: int, db: Session = Depends(get_db)):
    attempt = db.query(Attempt).get(attempt_id)
    if not attempt or not attempt.submission:
        raise HTTPException(404, "attempt or submission not found")
    if attempt.status == AttemptStatus.COMPLETED:
        raise HTTPException(400, "attempt already completed")

    _run_evaluation(db, attempt, attempt.submission.content)
    db.refresh(attempt)
    return attempt


@app.get("/attempts/{attempt_id}", response_model=schemas.AttemptOut)
def get_attempt(attempt_id: int, db: Session = Depends(get_db)):
    attempt = db.query(Attempt).get(attempt_id)
    if not attempt:
        raise HTTPException(404, "attempt not found")
    return attempt


@app.get("/users/{user_id}/history", response_model=list[schemas.AttemptOut])
def user_history(user_id: str, db: Session = Depends(get_db)):
    return (
        db.query(Attempt)
        .filter(Attempt.user_id == user_id)
        .order_by(Attempt.created_at.desc())
        .all()
    )
