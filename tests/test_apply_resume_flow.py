import json

from applypilot import config
from applypilot.apply import launcher, prompt
from applypilot.database import init_db


def test_score_five_tailored_resume_reaches_apply_prompt(tmp_path, monkeypatch):
    tailored_dir = tmp_path / "tailored"
    tailored_dir.mkdir()
    resume_txt = tailored_dir / "Example_Engineer.txt"
    resume_txt.write_text("Tailored resume content", encoding="utf-8")
    resume_txt.with_suffix(".pdf").write_bytes(b"test pdf")

    conn = init_db(tmp_path / "apply.db")
    job_url = "https://example.test/jobs/engineer"
    conn.execute(
        "INSERT INTO jobs "
        "(url, title, site, application_url, tailored_resume_path, fit_score, full_description) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            job_url,
            "Engineer",
            "Example",
            "https://example.test/apply",
            str(resume_txt),
            5,
            "Job description",
        ),
    )
    conn.commit()

    apply_dir = tmp_path / "apply-workers"
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    worker_dir = tmp_path / "worker"
    worker_dir.mkdir()

    monkeypatch.setattr(launcher, "get_connection", lambda: conn)
    monkeypatch.setattr(launcher, "_load_blocked", lambda: (set(), []))
    monkeypatch.setattr(config, "is_manual_ats", lambda url: False)
    monkeypatch.setattr(config, "APP_DIR", tmp_path)
    monkeypatch.setattr(config, "APPLY_WORKER_DIR", apply_dir)
    monkeypatch.setattr(config, "LOG_DIR", log_dir)
    monkeypatch.setattr(
        config,
        "load_profile",
        lambda: {"personal": {"full_name": "Test User", "email": "test@example.test"}},
    )
    monkeypatch.setattr(config, "load_search_config", lambda: {})
    monkeypatch.setattr(config, "load_blocked_sso", lambda: [])
    monkeypatch.setattr(launcher, "reset_worker_dir", lambda worker_id: worker_dir)

    monkeypatch.setattr(prompt, "_build_profile_summary", lambda profile: "Test profile")
    monkeypatch.setattr(prompt, "_build_location_check", lambda profile, search: "Location rules")
    monkeypatch.setattr(prompt, "_build_salary_section", lambda profile: "Salary rules")
    monkeypatch.setattr(prompt, "_build_screening_section", lambda profile: "Screening rules")
    monkeypatch.setattr(prompt, "_build_hard_rules", lambda profile: "Hard rules")
    monkeypatch.setattr(prompt, "_build_captcha_section", lambda: "Captcha rules")

    class FakeInput:
        def __init__(self):
            self.value = ""

        def write(self, text):
            self.value += text

        def close(self):
            pass

    class FakeProcess:
        def __init__(self):
            self.stdin = FakeInput()
            self.stdout = iter([
                json.dumps({"type": "result", "result": "RESULT:APPLIED", "usage": {}}),
            ])
            self.returncode = 0

        def wait(self, timeout=None):
            return self.returncode

        def poll(self):
            return self.returncode

    process = FakeProcess()
    monkeypatch.setattr(launcher.subprocess, "Popen", lambda *args, **kwargs: process)

    job = launcher.acquire_job()

    assert job is not None
    assert job["fit_score"] == 5
    assert job["tailored_resume_path"] == str(resume_txt)

    result, _ = launcher.run_job(job, port=0, dry_run=True)

    assert result == "applied"
    assert "Tailored resume content" in process.stdin.value
    assert (apply_dir / "current" / "Test_User_Resume.pdf").exists()
    conn.close()
