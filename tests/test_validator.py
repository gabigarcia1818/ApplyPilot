from applypilot.scoring.validator import validate_json_fields


def _resume_data(skills):
    return {
        "title": "Software Engineer",
        "summary": "Engineer with backend experience.",
        "skills": {"Frameworks": skills},
        "experience": [
            {"header": "Software Engineer at Brightwave Logistics", "bullets": ["Built APIs."]},
        ],
        "projects": [{"header": "API Service", "bullets": ["Built API endpoints."]}],
        "education": "Example University",
    }


def test_allowed_watchlist_skill_is_not_flagged_as_fabricated():
    profile = {
        "skills_boundary": {"frameworks": ["Django"]},
        "resume_facts": {
            "preserved_companies": ["Brightwave Logistics"],
            "preserved_school": "Example University",
        },
    }

    result = validate_json_fields(_resume_data("Django"), profile)

    assert result["passed"]
    assert result["errors"] == []


def test_watchlist_skill_not_in_profile_is_still_rejected():
    profile = {
        "skills_boundary": {"frameworks": ["FastAPI"]},
        "resume_facts": {
            "preserved_companies": ["Brightwave Logistics"],
            "preserved_school": "Example University",
        },
    }

    result = validate_json_fields(_resume_data("Django"), profile)

    assert not result["passed"]
    assert "Fabricated skill: 'django'" in result["errors"]
