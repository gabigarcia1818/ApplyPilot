from typer.testing import CliRunner

from applypilot import cli, config, database


def test_apply_without_tailored_resumes_exits_with_message(monkeypatch, tmp_path):
    class EmptyConnection:
        def execute(self, query):
            return self

        def fetchone(self):
            return (0,)

    profile_path = tmp_path / "profile.yaml"
    profile_path.touch()
    tier_checks = []

    monkeypatch.setattr(cli, "_bootstrap", lambda: None)
    monkeypatch.setattr(config, "check_tier", lambda tier, feature: tier_checks.append((tier, feature)))
    monkeypatch.setattr(config, "PROFILE_PATH", profile_path)
    monkeypatch.setattr(database, "get_connection", lambda: EmptyConnection())

    result = CliRunner().invoke(cli.app, ["apply"])

    assert result.exit_code == 1
    assert "No resumes available to apply." in result.output
    assert "applypilot run score tailor" in result.output
    assert "Traceback" not in result.output
    assert "Launching Auto-Apply" not in result.output
    assert tier_checks == []
