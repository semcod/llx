import copy

from llx.planfile.generate_strategy import _normalize_strategy_data


def test_normalize_strategy_data_converts_string_quality_gates():
    raw = {
        "name": "Refactor Strategy",
        "project_type": "python",
        "domain": "software",
        "goal": {
            "short": "Improve maintainability",
            "quality": ["Reduce complexity"],
            "delivery": ["Ship safely"],
            "metrics": ["Avg CC < 5"],
        },
        "sprints": [
            {
                "id": "sprint-2",
                "name": "Sprint 2",
                "objectives": "Reduce complexity",
                "tasks": [],
                "task_patterns": ["Extract helper function"],
            }
        ],
        "quality_gates": [
            "Average CC < 5",
            {"name": "Coverage gate", "criteria": "Test coverage >= 80%"},
        ],
    }

    normalized = _normalize_strategy_data(copy.deepcopy(raw))

    assert normalized["sprints"][0]["id"] == 2
    assert normalized["sprints"][0]["objectives"] == ["Reduce complexity"]
    assert normalized["sprints"][0]["tasks"][0]["name"] == "Extract helper function"
    assert normalized["quality_gates"][0]["name"] == "Average CC < 5"
    assert normalized["quality_gates"][0]["criteria"] == ["Average CC < 5"]
    assert normalized["quality_gates"][1]["criteria"] == ["Test coverage >= 80%"]
    assert normalized["quality_gates"][1]["required"] is True
