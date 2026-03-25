"""Tests for llx core functionality.

Includes scenarios from real projects:
- code2llm: 113 files, 21K lines, CC̄=4.6, max CC=65
- preLLM: 31 files, 8.9K lines, CC̄=5.0, max CC=28, 3 god modules
- vallm: 56 files, 8.6K lines, CC̄=3.5, max CC=42
"""

import pytest
from llx.analysis.collector import ProjectMetrics, _extract_cc_value, _apply_analysis_yaml, _apply_evolution_yaml
from llx.routing.selector import ModelTier, select_model, check_context_fit, select_with_context_check
from llx.config import LlxConfig, TierThresholds


class TestProjectMetrics:
    def test_complexity_score_zero(self):
        assert ProjectMetrics().complexity_score == 0.0

    def test_complexity_score_high(self):
        m = ProjectMetrics(avg_cc=8.0, max_cc=65, critical_count=12, god_modules=5, dependency_cycles=3)
        assert m.complexity_score > 80

    def test_scale_score_small(self):
        m = ProjectMetrics(total_files=2, total_lines=100, total_functions=5)
        assert m.scale_score < 10

    def test_scale_score_large(self):
        m = ProjectMetrics(total_files=200, total_lines=50000, total_functions=800, max_fan_out=30)
        assert m.scale_score > 80


class TestModelSelection:
    def test_trivial_gets_free(self):
        m = ProjectMetrics(total_files=1, total_lines=50, total_functions=2)
        assert select_model(m).tier == ModelTier.FREE

    def test_small_gets_cheap(self):
        m = ProjectMetrics(total_files=5, total_lines=800, total_functions=20)
        assert select_model(m).tier == ModelTier.CHEAP

    def test_medium_gets_balanced(self):
        m = ProjectMetrics(total_files=25, total_lines=8000, total_functions=100, avg_cc=4.5, max_fan_out=12)
        assert select_model(m).tier == ModelTier.BALANCED

    def test_large_gets_premium(self):
        m = ProjectMetrics(
            total_files=100, total_lines=30000, total_functions=500,
            avg_cc=7.0, max_cc=40, max_fan_out=35, dependency_cycles=2, critical_count=15,
        )
        assert select_model(m).tier == ModelTier.PREMIUM

    def test_local_override(self):
        m = ProjectMetrics(total_files=100, total_lines=30000, avg_cc=7.0)
        assert select_model(m, prefer_local=True).tier == ModelTier.LOCAL

    def test_max_tier_caps(self):
        m = ProjectMetrics(
            total_files=100, total_lines=30000, avg_cc=7.0,
            max_fan_out=35, dependency_cycles=2, critical_count=15,
        )
        assert select_model(m, max_tier=ModelTier.BALANCED).tier == ModelTier.BALANCED

    def test_refactor_hint_upgrades(self):
        m = ProjectMetrics(total_files=30, total_lines=10000, avg_cc=5.0, max_fan_out=15)
        result = select_model(m, task_hint="refactor")
        assert result.tier in (ModelTier.BALANCED, ModelTier.PREMIUM)

    def test_quick_fix_downgrades(self):
        m = ProjectMetrics(total_files=30, total_lines=10000, avg_cc=5.0, max_fan_out=15)
        result = select_model(m, task_hint="quick_fix")
        assert result.tier in (ModelTier.CHEAP, ModelTier.BALANCED)

    def test_has_reasons(self):
        m = ProjectMetrics(total_files=50, total_lines=20000, avg_cc=6.0)
        assert len(select_model(m).reasons) > 0

    def test_has_scores(self):
        m = ProjectMetrics(total_files=10, total_lines=2000)
        scores = select_model(m).scores
        assert "complexity" in scores and "scale" in scores and "coupling" in scores


class TestContextFit:
    def test_small_fits(self):
        m = ProjectMetrics(estimated_context_tokens=1000)
        from llx.config import ModelConfig
        model = ModelConfig(name="t", provider="t", model_id="t", max_context=32_000)
        assert check_context_fit(m, model)

    def test_huge_exceeds(self):
        m = ProjectMetrics(estimated_context_tokens=500_000)
        from llx.config import ModelConfig
        model = ModelConfig(name="t", provider="t", model_id="t", max_context=32_000)
        assert not check_context_fit(m, model)

    def test_context_auto_upgrade(self):
        m = ProjectMetrics(
            total_files=5, total_lines=800,
            estimated_context_tokens=500_000,  # huge context
        )
        result = select_with_context_check(m)
        # Should upgrade from cheap/free to something with larger context
        assert result.model.max_context >= 200_000


class TestConfig:
    def test_default_tiers(self):
        config = LlxConfig()
        assert all(t in config.models for t in ["premium", "balanced", "cheap", "free", "local"])


class TestHelpers:
    def test_extract_cc_value(self):
        assert _extract_cc_value("query CC=27 (limit:15)") == 27
        assert _extract_cc_value("main CC=30 (limit:15)") == 30
        assert _extract_cc_value("no cc here") is None


# ---------------------------------------------------------------------------
# Real project scenarios
# ---------------------------------------------------------------------------

class TestCode2LLMProject:
    """code2llm: 113 files, 21K lines, CC̄=4.6, max CC=65."""

    def test_selects_premium(self):
        m = ProjectMetrics(
            total_files=113, total_lines=21128, total_functions=918,
            avg_cc=4.6, max_cc=65, critical_count=12,
            god_modules=5, max_fan_out=45, hotspot_count=5,
        )
        result = select_model(m)
        assert result.tier == ModelTier.PREMIUM


class TestPreLLMProject:
    """preLLM: 31 files, 8.9K lines, CC̄=5.0, max CC=28, 3 god modules, 1 cycle."""

    def test_selects_balanced_or_premium(self):
        m = ProjectMetrics(
            total_files=31, total_lines=8900, total_functions=310,
            avg_cc=5.0, max_cc=28, critical_count=10,
            god_modules=3, max_fan_out=30, dependency_cycles=1,
        )
        result = select_model(m)
        # preLLM has high CC and god modules → at least balanced, likely premium
        assert result.tier in (ModelTier.BALANCED, ModelTier.PREMIUM)

    def test_analysis_yaml_parsing(self):
        """Test parsing the actual preLLM analysis.toon.yaml structure."""
        data = {
            "header": {
                "files": 31, "lines": 8900, "functions": 310,
                "avg_cc": 5.0, "critical_count": 10, "cycles": 1,
            },
            "health": {
                "issues": [
                    {"severity": "yellow", "code": "CC", "message": "main CC=30 (limit:15)"},
                    {"severity": "yellow", "code": "CC", "message": "query CC=27 (limit:15)"},
                    {"severity": "yellow", "code": "CC", "message": "to_stdout CC=28 (limit:15)"},
                ]
            },
        }
        m = ProjectMetrics()
        _apply_analysis_yaml(data, m)
        assert m.total_files == 31
        assert m.total_lines == 8900
        assert m.avg_cc == 5.0
        assert m.max_cc == 30  # from main CC=30
        assert m.dependency_cycles == 1

    def test_evolution_yaml_parsing(self):
        """Test parsing the preLLM evolution.toon.yaml structure."""
        data = {
            "stats": {
                "total_funcs": 248, "total_files": 24,
                "avg_cc": 5.1, "max_cc": 28,
            },
            "metrics_target": {
                "god_modules": {"current": 3, "target": 0},
                "max_cc": {"current": 28, "target": 14},
            },
            "refactoring": {
                "actions": [
                    {"action": "SPLIT-FUNC", "target": "query", "cc": 27, "fan_out": 30},
                    {"action": "SPLIT", "target": "prellm/cli.py", "reason": "999L"},
                ],
            },
        }
        m = ProjectMetrics()
        _apply_evolution_yaml(data, m)
        assert m.god_modules == 3
        assert m.max_cc == 28
        assert m.max_fan_out == 30
        assert m.total_functions == 248


class TestVallmProject:
    """vallm: 56 files, 8604 lines, CC̄=3.5, max CC=42."""

    def test_selects_balanced(self):
        m = ProjectMetrics(
            total_files=56, total_lines=8604, total_functions=91,
            avg_cc=3.5, max_cc=42, critical_count=3,
        )
        result = select_model(m)
        assert result.tier in (ModelTier.BALANCED, ModelTier.PREMIUM)


class TestSingleScript:
    def test_selects_free(self):
        m = ProjectMetrics(total_files=1, total_lines=80, total_functions=3, avg_cc=2.0)
        assert select_model(m).tier == ModelTier.FREE
