"""
LLM provider health checks — background workers and on-demand checks.
Extracted from LLMOrchestrator._health_check_worker / _perform_health_checks.
"""

import time

import requests

from .models import LLMProvider


def perform_health_checks(providers: dict[str, LLMProvider]) -> None:
    """Perform health checks on all providers."""
    for provider in providers.values():
        if provider.health_check_endpoint:
            try:
                response = requests.get(provider.health_check_endpoint, timeout=5)
                if response.status_code != 200:
                    print(f"⚠️  Provider {provider.provider_id} health check failed: HTTP {response.status_code}")
            except Exception as e:
                print(f"⚠️  Provider {provider.provider_id} health check error: {e}")


def health_check_worker(orchestrator) -> None:
    """Background worker for health checks.

    Args:
        orchestrator: LLMOrchestrator instance (duck-typed for .running, .config, .providers).
    """
    while orchestrator.running:
        try:
            time.sleep(orchestrator.config["health_check_interval"])
            perform_health_checks(orchestrator.providers)
        except Exception as e:
            print(f"❌ Health check worker error: {e}")
