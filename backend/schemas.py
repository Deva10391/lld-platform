from pydantic import BaseModel
from typing import Optional, Dict


class ProblemOut(BaseModel):
    id: int
    title: str
    description: str
    difficulty: str
    tags: str

    class Config:
        from_attributes = True


class AttemptCreate(BaseModel):
    user_id: str
    problem_id: int


class SubmissionCreate(BaseModel):
    content: str


class EvaluationOut(BaseModel):
    dimension_scores: Dict[str, int]
    overall_score: int
    comments: Dict[str, str]
    evaluated_by: str

    class Config:
        from_attributes = True


class AttemptOut(BaseModel):
    id: int
    user_id: str
    problem_id: int
    status: str
    error_message: Optional[str] = None
    result: Optional[EvaluationOut] = None

    class Config:
        from_attributes = True
