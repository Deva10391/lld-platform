import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient
from evaluators import DeterministicEvaluator, CompositeEvaluator, Evaluator, EvalOutcome

import main
from main import app

client = TestClient(app)


# ---------- Deterministic evaluator (pure logic, no mocks needed) ----------

def test_deterministic_scores_edge_cases_and_structure():
    ev = DeterministicEvaluator()
    content = "class ParkingLot { } class Spot { } handles invalid ticket and concurrent entry, null checks."
    out = ev.evaluate("Parking Lot", "parking lot spot ticket concurrent invalid", content)
    assert out.dimension_scores["structure_presence"] >= 2
    assert out.dimension_scores["testability_edge_cases"] >= 4
    assert out.source == "deterministic"


def test_deterministic_low_score_on_thin_submission():
    ev = DeterministicEvaluator()
    out = ev.evaluate("Parking Lot", "parking lot spot ticket fee floor", "not much here")
    assert out.dimension_scores["structure_presence"] == 0
    assert out.dimension_scores["requirement_understanding"] == 0


# ---------- Composite evaluator: success and failure fallback ----------

class FakeLLMOk(Evaluator):
    def evaluate(self, title, desc, content):
        return EvalOutcome(
            dimension_scores={"responsibility_design": 4, "coupling_cohesion": 3},
            comments={"responsibility_design": "clear", "coupling_cohesion": "ok"},
            source="llm",
        )


class FakeLLMFails(Evaluator):
    def evaluate(self, title, desc, content):
        raise RuntimeError("simulated API outage")


def test_composite_merges_deterministic_and_llm_on_success():
    comp = CompositeEvaluator(llm=FakeLLMOk())
    out = comp.run("Parking Lot", "parking lot spot ticket", "class ParkingLot { } handles invalid ticket")
    assert out["evaluated_by"] == "deterministic+llm"
    assert "responsibility_design" in out["dimension_scores"]
    assert out["llm_failed_reason"] is None


def test_composite_falls_back_to_deterministic_when_llm_fails():
    comp = CompositeEvaluator(llm=FakeLLMFails())
    out = comp.run("Parking Lot", "parking lot spot ticket", "class ParkingLot { } handles invalid ticket")
    assert out["evaluated_by"] == "deterministic"
    assert out["llm_failed_reason"] is not None
    assert "responsibility_design" not in out["dimension_scores"]  # llm-only dim absent, no fake data


# ---------- API integration (uses in-memory-equivalent sqlite file, patched evaluator) ----------

@pytest.fixture(autouse=True)
def patch_evaluator_to_fake(monkeypatch):
    monkeypatch.setattr(main, "evaluator", CompositeEvaluator(llm=FakeLLMOk()))
    yield


def test_list_problems_seeded():
    res = client.get("/problems")
    assert res.status_code == 200
    assert len(res.json()) >= 5


def test_full_attempt_flow_completed():
    user = "test-user-flow"
    problem_id = client.get("/problems").json()[0]["id"]
    attempt = client.post("/attempts", json={"user_id": user, "problem_id": problem_id}).json()

    res = client.post(f"/attempts/{attempt['id']}/submit",
                       json={"content": "class ParkingLot { } handles invalid ticket and concurrent entry"})
    body = res.json()
    assert res.status_code == 200
    assert body["status"] == "COMPLETED"
    assert body["result"]["overall_score"] > 0

    history = client.get(f"/users/{user}/history").json()
    assert any(a["id"] == attempt["id"] for a in history)


def test_submission_too_short_is_rejected():
    problem_id = client.get("/problems").json()[0]["id"]
    attempt = client.post("/attempts", json={"user_id": "u2", "problem_id": problem_id}).json()
    res = client.post(f"/attempts/{attempt['id']}/submit", json={"content": "short"})
    assert res.status_code == 422


def test_double_submit_rejected():
    problem_id = client.get("/problems").json()[0]["id"]
    attempt = client.post("/attempts", json={"user_id": "u3", "problem_id": problem_id}).json()
    client.post(f"/attempts/{attempt['id']}/submit", json={"content": "class Spot { } handles invalid case here"})
    res = client.post(f"/attempts/{attempt['id']}/submit", json={"content": "second try text goes here now"})
    assert res.status_code == 400


def test_retry_after_llm_failure_recovers(monkeypatch):
    monkeypatch.setattr(main, "evaluator", CompositeEvaluator(llm=FakeLLMFails()))
    problem_id = client.get("/problems").json()[0]["id"]
    attempt = client.post("/attempts", json={"user_id": "u4", "problem_id": problem_id}).json()
    res = client.post(f"/attempts/{attempt['id']}/submit",
                       json={"content": "class ParkingLot { } handles invalid ticket case"})
    assert res.json()["status"] == "PARTIAL"

    # LLM recovers, learner retries
    monkeypatch.setattr(main, "evaluator", CompositeEvaluator(llm=FakeLLMOk()))
    res = client.post(f"/attempts/{attempt['id']}/retry")
    assert res.json()["status"] == "COMPLETED"


def test_unknown_problem_404():
    res = client.post("/attempts", json={"user_id": "u5", "problem_id": 99999})
    assert res.status_code == 404
