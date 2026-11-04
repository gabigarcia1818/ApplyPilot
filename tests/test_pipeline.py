from applypilot import pipeline
from applypilot.scoring import tailor


def test_tailor_stage_reports_no_work(monkeypatch):
    monkeypatch.setattr(
        tailor,
        "run_tailoring",
        lambda **kwargs: {"approved": 0, "failed": 0, "errors": 0, "elapsed": 0.0},
    )

    result = pipeline._run_tailor()

    assert result["status"] == "no work"
    assert result["elapsed"] == 0.0


def test_tailor_stage_reports_failed_jobs(monkeypatch):
    monkeypatch.setattr(
        tailor,
        "run_tailoring",
        lambda **kwargs: {"approved": 0, "failed": 2, "errors": 0, "elapsed": 1.0},
    )

    result = pipeline._run_tailor()

    assert result["status"] == "failed"
    assert result["failed"] == 2
