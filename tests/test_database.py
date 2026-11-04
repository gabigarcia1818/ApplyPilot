from applypilot.database import get_jobs_by_stage, get_stats, init_db


def test_default_tailoring_threshold_includes_moderate_scores(tmp_path):
    conn = init_db(tmp_path / "test.db")
    conn.executemany(
        "INSERT INTO jobs (url, fit_score, full_description) VALUES (?, ?, ?)",
        [
            ("https://example.test/moderate", 5, "Description"),
            ("https://example.test/weak", 4, "Description"),
        ],
    )
    conn.commit()

    pending = get_jobs_by_stage(conn=conn, stage="pending_tailor")

    assert [job["url"] for job in pending] == ["https://example.test/moderate"]
    assert get_stats(conn)["untailored_eligible"] == 1
    conn.close()
