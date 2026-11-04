from applypilot.scoring import tailor


def test_tailor_resume_reports_exhausted_json_retries(monkeypatch):
    class InvalidJsonClient:
        def chat(self, messages, max_tokens, temperature):
            return "not JSON"

    monkeypatch.setattr(tailor, "get_client", lambda: InvalidJsonClient())

    text, report = tailor.tailor_resume(
        "Original resume",
        {"title": "Engineer", "site": "Example", "full_description": ""},
        {},
        max_retries=1,
    )

    assert text == ""
    assert report["status"] == "failed_json"
    assert report["attempts"] == 2
    assert len(report["errors"]) == 2


def test_run_tailoring_does_not_save_empty_resume(tmp_path, monkeypatch):
    class FakeConnection:
        def __init__(self):
            self.executed = []

        def execute(self, query, params):
            self.executed.append((query, params))

        def commit(self):
            pass

    resume_path = tmp_path / "resume.txt"
    resume_path.write_text("Original resume", encoding="utf-8")
    output_dir = tmp_path / "tailored"
    connection = FakeConnection()
    job = {
        "url": "https://example.test/job",
        "title": "Engineer",
        "site": "Example",
        "full_description": "Description",
    }

    monkeypatch.setattr(tailor, "RESUME_PATH", resume_path)
    monkeypatch.setattr(tailor, "TAILORED_DIR", output_dir)
    monkeypatch.setattr(tailor, "load_profile", lambda: {})
    monkeypatch.setattr(tailor, "get_connection", lambda: connection)
    monkeypatch.setattr(tailor, "get_jobs_by_stage", lambda **kwargs: [job])
    monkeypatch.setattr(
        tailor,
        "tailor_resume",
        lambda *args, **kwargs: (
            "",
            {"status": "failed_json", "attempts": 4},
        ),
    )

    result = tailor.run_tailoring()

    assert result["approved"] == 0
    assert result["failed"] == 1
    assert result["errors"] == 0
    assert list(output_dir.iterdir()) == []
    assert len(connection.executed) == 1
    assert "tailor_attempts" in connection.executed[0][0]
    assert "tailored_resume_path=?" not in connection.executed[0][0]
