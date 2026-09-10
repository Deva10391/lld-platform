"""
Evaluation is split by what benefits from determinism vs. judgment
(per the assignment's design question):

  DETERMINISTIC dims  -> cheap, instant, reproducible, no false confidence needed
    requirement_understanding, testability_edge_cases, structure_presence

  JUDGMENT dims (LLM)  -> no single correct answer, needs reasoning
    responsibility_design, coupling_cohesion, abstraction_patterns,
    extensibility, explanation_quality

Evaluator is an abstract interface so a new evaluation approach (e.g. a
static-analysis evaluator for CODE submissions, or a different LLM) can be
added by implementing one method -> Open/Closed.

CompositeEvaluator orchestrates both and is the ONLY thing main.py calls,
so main.py never needs to know how many evaluators exist or how they combine.
"""
from abc import ABC, abstractmethod
import json
import os
import re
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class EvalOutcome:
    dimension_scores: Dict[str, int] = field(default_factory=dict)  # 0-5 each
    comments: Dict[str, str] = field(default_factory=dict)
    source: str = "unknown"


class Evaluator(ABC):
    """Interface every evaluation strategy must satisfy."""

    @abstractmethod
    def evaluate(self, problem_title: str, problem_description: str, content: str) -> EvalOutcome:
        ...


class DeterministicEvaluator(Evaluator):
    """
    Rule-based checks on the submitted text. No AI call, cannot fail,
    always returns a result. This is the guaranteed floor of every
    evaluation, so an attempt is never left with zero feedback.
    """

    CLASS_PATTERN = re.compile(r"\bclass\b", re.IGNORECASE)
    EDGE_CASE_KEYWORDS = ["edge case", "invalid", "concurrent", "null", "empty", "fail", "error", "limit"]
    RESPONSIBILITY_KEYWORDS = ["responsib", "single responsibility", "encapsulat"]

    def evaluate(self, problem_title, problem_description, content):
        text = content.lower()
        word_count = len(content.split())

        class_mentions = len(self.CLASS_PATTERN.findall(content))
        structure_score = min(5, class_mentions)  # 1 point per distinct class up to 5

        edge_hits = sum(1 for kw in self.EDGE_CASE_KEYWORDS if kw in text)
        edge_score = min(5, edge_hits * 2)

        req_terms = [t for t in re.findall(r"[a-zA-Z]{4,}", problem_description.lower())]
        req_terms = list(dict.fromkeys(req_terms))[:15]  # first 15 unique domain-ish words
        req_hits = sum(1 for t in req_terms if t in text)
        req_score = min(5, round((req_hits / max(1, len(req_terms))) * 5))

        length_note = "" if word_count >= 80 else " Submission is short; add more detail."

        return EvalOutcome(
            dimension_scores={
                "structure_presence": structure_score,
                "testability_edge_cases": edge_score,
                "requirement_understanding": req_score,
            },
            comments={
                "structure_presence": f"Found {class_mentions} class mention(s).{length_note}",
                "testability_edge_cases": f"Found {edge_hits} edge-case keyword(s) (null/invalid/concurrent/etc).",
                "requirement_understanding": f"Covered {req_hits}/{len(req_terms)} key problem terms.",
            },
            source="deterministic",
        )


class LLMEvaluator(Evaluator):
    """
    Calls Anthropic's API to score judgment-heavy dimensions.
    If ANTHROPIC_API_KEY is not set (or the call fails), raises so the
    CompositeEvaluator can decide the fallback -- this class does not
    silently degrade, it fails loudly and lets the orchestrator handle it.
    """

    DIMENSIONS = [
        "responsibility_design", "coupling_cohesion",
        "abstraction_patterns", "extensibility", "explanation_quality",
    ]

    def evaluate(self, problem_title, problem_description, content):
        import anthropic  # imported lazily so the app runs without the package during tests

        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
        prompt = f"""You are grading a Low-Level-Design (LLD) practice submission.
Problem: {problem_title}
Problem description: {problem_description}

Candidate's design submission:
---
{content}
---

Score these dimensions from 0-5 (0=missing/poor, 5=excellent), each with a
one-sentence comment pointing to specific evidence in the submission:
{", ".join(self.DIMENSIONS)}

Respond with ONLY valid JSON, no markdown fences, shaped as:
{{"scores": {{"dim": int, ...}}, "comments": {{"dim": "text", ...}}}}"""

        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        raw = raw.strip().strip("`").replace("json\n", "", 1) if raw.strip().startswith("```") else raw
        parsed = json.loads(raw)

        return EvalOutcome(
            dimension_scores={k: int(v) for k, v in parsed["scores"].items()},
            comments=parsed["comments"],
            source="llm",
        )


class CompositeEvaluator:
    """
    Orchestrates deterministic + LLM evaluators, merges scores into one
    result, and defines the fail-handling policy:

      LLM succeeds -> evaluated_by = "deterministic+llm"
      LLM fails    -> evaluated_by = "deterministic"  (PARTIAL, not FAILED --
                       the learner still gets useful, if narrower, feedback)
      deterministic itself never fails (no external calls, pure logic)
    """

    def __init__(self, deterministic: Evaluator = None, llm: Evaluator = None):
        self.deterministic = deterministic or DeterministicEvaluator()
        self.llm = llm or LLMEvaluator()

    def run(self, problem_title: str, problem_description: str, content: str):
        det = self.deterministic.evaluate(problem_title, problem_description, content)
        scores = dict(det.dimension_scores)
        comments = dict(det.comments)
        evaluated_by = "deterministic"
        llm_failed_reason = None

        try:
            llm_out = self.llm.evaluate(problem_title, problem_description, content)
            scores.update(llm_out.dimension_scores)
            comments.update(llm_out.comments)
            evaluated_by = "deterministic+llm"
        except Exception as e:  # noqa: BLE001 - any LLM/network failure falls back
            llm_failed_reason = str(e)

        max_possible = len(scores) * 5
        overall = round((sum(scores.values()) / max_possible) * 100) if scores else 0

        return {
            "dimension_scores": scores,
            "comments": comments,
            "overall_score": overall,
            "evaluated_by": evaluated_by,
            "llm_failed_reason": llm_failed_reason,
        }
