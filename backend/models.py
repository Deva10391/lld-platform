"""
Core domain model.

Problem        -> what the learner practices
Attempt        -> one practice session (has a lifecycle/status)
Submission     -> the artifact the learner produced for an attempt
                  (format is a field, not a hardcoded shape -> new formats
                  like CODE or DIAGRAM can be added without touching Attempt)
EvaluationResult -> stored feedback for an attempt, tagged by which
                  evaluator produced it, so the learner sees provenance.
"""
import enum
import datetime as dt
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON
)
from sqlalchemy.orm import relationship
from database import Base


class AttemptStatus(str, enum.Enum):
    PENDING = "PENDING"
    EVALUATING = "EVALUATING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"      # deterministic-only fallback after LLM failure
    FAILED = "FAILED"        # nothing usable produced; learner can retry


class SubmissionFormat(str, enum.Enum):
    TEXT_DESIGN = "TEXT_DESIGN"   # only format supported in this MVP
    # CODE, DIAGRAM etc. can be added later without schema changes


class Problem(Base):
    __tablename__ = "problems"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(String, default="MEDIUM")
    tags = Column(String, default="")  # comma separated, kept simple on purpose

    attempts = relationship("Attempt", back_populates="problem")


class Attempt(Base):
    __tablename__ = "attempts"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False)
    status = Column(Enum(AttemptStatus), default=AttemptStatus.PENDING)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    error_message = Column(Text, nullable=True)  # set when FAILED, shown to learner

    problem = relationship("Problem", back_populates="attempts")
    submission = relationship("Submission", back_populates="attempt", uselist=False)
    result = relationship("EvaluationResult", back_populates="attempt", uselist=False)


class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True)
    attempt_id = Column(Integer, ForeignKey("attempts.id"), nullable=False, unique=True)
    format = Column(Enum(SubmissionFormat), default=SubmissionFormat.TEXT_DESIGN)
    content = Column(Text, nullable=False)
    submitted_at = Column(DateTime, default=dt.datetime.utcnow)

    attempt = relationship("Attempt", back_populates="submission")


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"
    id = Column(Integer, primary_key=True)
    attempt_id = Column(Integer, ForeignKey("attempts.id"), nullable=False, unique=True)
    dimension_scores = Column(JSON, nullable=False)   # {dimension: score 0-5}
    overall_score = Column(Integer, nullable=False)   # 0-100
    comments = Column(JSON, nullable=False)           # {dimension: comment string}
    evaluated_by = Column(String, nullable=False)     # "deterministic" | "deterministic+llm"
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    attempt = relationship("Attempt", back_populates="result")
