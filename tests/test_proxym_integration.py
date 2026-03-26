"""Tests for proxym integration module.

Tests ProxymClient, tier mapping, header generation, and LlxClient
metrics-aware routing — all without requiring a running proxym server.
"""

import pytest
from unittest.mock import patch, MagicMock

from llx.analysis.collector import ProjectMetrics
from llx.routing.selector import ModelTier


class TestTierMapping:
    """Verify llx ModelTier → proxym TaskTier mapping."""

    def test_free_maps_to_trivial(self):
        from llx.integrations.proxym import _tier_to_proxym
        assert _tier_to_proxym(ModelTier.FREE) == "trivial"

    def test_local_maps_to_operational(self):
        from llx.integrations.proxym import _tier_to_proxym
        assert _tier_to_proxym(ModelTier.LOCAL) == "operational"

    def test_cheap_maps_to_operational(self):
        from llx.integrations.proxym import _tier_to_proxym
        assert _tier_to_proxym(ModelTier.CHEAP) == "operational"

    def test_balanced_maps_to_standard(self):
        from llx.integrations.proxym import _tier_to_proxym
        assert _tier_to_proxym(ModelTier.BALANCED) == "standard"

    def test_premium_maps_to_complex(self):
        from llx.integrations.proxym import _tier_to_proxym
        assert _tier_to_proxym(ModelTier.PREMIUM) == "complex"


class TestHeaderGeneration:
    """Verify X-Llx-* headers built from ProjectMetrics."""

    def test_empty_metrics_no_headers(self):
        from llx.integrations.proxym import _build_llx_headers
        headers = _build_llx_headers(None, None)
        assert headers == {}

    def test_tier_only_sets_task_tier(self):
        from llx.integrations.proxym import _build_llx_headers
        headers = _build_llx_headers(None, ModelTier.BALANCED)
        assert headers == {"X-Task-Tier": "standard"}

    def test_metrics_generate_headers(self):
        from llx.integrations.proxym import _build_llx_headers
        m = ProjectMetrics(
            total_files=50, total_lines=10000, avg_cc=5.5, max_cc=30,
            god_modules=3, dependency_cycles=1,
        )
        headers = _build_llx_headers(m, ModelTier.PREMIUM)
        assert headers["X-Task-Tier"] == "complex"
        assert headers["X-Llx-Files"] == "50"
        assert headers["X-Llx-Lines"] == "10000"
        assert headers["X-Llx-Avg-Cc"] == "5.5"
        assert headers["X-Llx-Max-Cc"] == "30"
        assert headers["X-Llx-God-Modules"] == "3"
        assert headers["X-Llx-Dep-Cycles"] == "1"
        assert "X-Llx-Complexity" in headers
        assert "X-Llx-Scale" in headers

    def test_no_god_modules_omits_header(self):
        from llx.integrations.proxym import _build_llx_headers
        m = ProjectMetrics(total_files=5, total_lines=500, avg_cc=2.0, max_cc=5)
        headers = _build_llx_headers(m, ModelTier.CHEAP)
        assert "X-Llx-God-Modules" not in headers
        assert "X-Llx-Dep-Cycles" not in headers


class TestProxymClientStructure:
    """Test ProxymClient initialization and data models."""

    def test_client_default_url(self):
        from llx.integrations.proxym import ProxymClient
        client = ProxymClient()
        assert client.base_url == "http://localhost:4000"
        client.close()

    def test_client_custom_url(self):
        from llx.integrations.proxym import ProxymClient
        client = ProxymClient(base_url="http://custom:8080")
        assert client.base_url == "http://custom:8080"
        client.close()

    def test_status_unreachable(self):
        from llx.integrations.proxym import ProxymClient
        client = ProxymClient(base_url="http://localhost:59999")
        status = client.status()
        assert status.available is False
        assert status.error is not None
        client.close()

    def test_is_available_unreachable(self):
        from llx.integrations.proxym import ProxymClient
        client = ProxymClient(base_url="http://localhost:59999")
        assert client.is_available() is False
        client.close()

    def test_proxym_status_dataclass(self):
        from llx.integrations.proxym import ProxymStatus
        s = ProxymStatus(available=True, url="http://localhost:4000", version="0.1.119", models_count=19)
        assert s.available
        assert s.version == "0.1.119"
        assert s.models_count == 19

    def test_proxym_response_dataclass(self):
        from llx.integrations.proxym import ProxymResponse
        r = ProxymResponse(
            content="Hello", model="claude-sonnet",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        )
        assert r.content == "Hello"
        assert r.prompt_tokens == 10
        assert r.completion_tokens == 20
        assert r.total_tokens == 30

    def test_proxym_response_no_usage(self):
        from llx.integrations.proxym import ProxymResponse
        r = ProxymResponse(content="", model="test")
        assert r.prompt_tokens == 0
        assert r.total_tokens == 0


class TestLlxClientMetrics:
    """Test LlxClient metrics header integration."""

    def test_metrics_headers_generated(self):
        from llx.routing.client import LlxClient
        m = ProjectMetrics(
            total_files=100, total_lines=30000,
            avg_cc=6.0, max_cc=50, critical_count=10,
            god_modules=5, max_fan_out=25, dependency_cycles=2,
        )
        headers = LlxClient._metrics_headers(m)
        assert "X-Task-Tier" in headers
        assert headers["X-Llx-Files"] == "100"
        assert headers["X-Llx-Lines"] == "30000"

    def test_chat_accepts_metrics_param(self):
        """Verify the chat() signature accepts metrics parameter."""
        import inspect
        from llx.routing.client import LlxClient
        sig = inspect.signature(LlxClient.chat)
        assert "metrics" in sig.parameters


class TestListModelsUnavailable:
    """Test list_models when proxym is down."""

    def test_list_models_returns_empty(self):
        from llx.integrations.proxym import ProxymClient
        client = ProxymClient(base_url="http://localhost:59999")
        models = client.list_models()
        assert models == []
        client.close()
