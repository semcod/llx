"""
LLM Orchestrator — core routing and provider management.
Extracted from the monolithic llm_orchestrator.py.
"""

import json
import time
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

import requests

from .._utils import load_json, save_json
from ..session.manager import SessionManager
from ..ratelimit.limiter import RateLimiter
from ..ratelimit.models import LimitType
from ..routing.engine import RoutingEngine
from ..routing.models import (
    ResourceType,
    RoutingRequest,
    RequestPriority,
    RoutingStrategy,
)

from .models import (
    LLMProviderType,
    ModelCapability,
    LLMModel,
    LLMProvider,
    LLMRequest,
    LLMResponse,
)
from .executors import execute_request, messages_to_prompt
from .health import perform_health_checks, health_check_worker


class LLMOrchestrator:
    """Orchestrates multiple LLM providers and models with intelligent routing."""

    def __init__(self, config_file: str = None):
        self.project_root = Path.cwd()
        self.config_file = config_file or self.project_root / "orchestration" / "llm.json"

        # Initialize managers
        self.session_manager = SessionManager()
        self.rate_limiter = RateLimiter()
        self.routing_engine = RoutingEngine()

        # LLM specific data
        self.providers: Dict[str, LLMProvider] = {}
        self.active_requests: Dict[str, LLMRequest] = {}
        self.request_history: List[LLMResponse] = []
        self.model_cache: Dict[str, LLMModel] = {}

        # Configuration
        self.config = {
            "default_timeout": 30,
            "max_concurrent_requests": 50,
            "request_history_size": 1000,
            "health_check_interval": 60,
            "auto_retry": True,
            "cost_tracking": True,
            "performance_tracking": True,
        }

        # State
        self.running = False
        self.lock = threading.RLock()

        # Load configuration
        self.load_config()

        # Start orchestrator
        self.start()

    # ── Config persistence ──────────────────────────────────

    def load_config(self) -> bool:
        """Load LLM orchestration configuration."""
        try:
            data = load_json(self.config_file, "LLM config")
            if data is not None:

                self.config.update(data.get("config", {}))

                for provider_data in data.get("providers", []):
                    provider = LLMProvider(
                        provider_id=provider_data["provider_id"],
                        provider_type=LLMProviderType(provider_data["provider_type"]),
                        name=provider_data["name"],
                        api_base=provider_data.get("api_base"),
                        auth_method=provider_data["auth_method"],
                        auth_config=provider_data.get("auth_config", {}),
                        rate_limits=provider_data.get("rate_limits", {}),
                        retry_config=provider_data.get("retry_config", {}),
                        health_check_endpoint=provider_data.get("health_check_endpoint"),
                        metadata=provider_data.get("metadata", {}),
                    )

                    for model_data in provider_data.get("models", {}):
                        model = LLMModel(
                            model_id=model_data["model_id"],
                            provider=provider.provider_type,
                            name=model_data["name"],
                            display_name=model_data["display_name"],
                            capabilities=[
                                ModelCapability(cap)
                                for cap in model_data.get("capabilities", [])
                            ],
                            context_window=model_data.get("context_window", 4096),
                            max_tokens=model_data.get("max_tokens", 1000),
                            cost_per_1k_input=model_data.get("cost_per_1k_input", 0.0),
                            cost_per_1k_output=model_data.get("cost_per_1k_output", 0.0),
                            average_latency_ms=model_data.get("average_latency_ms", 1000.0),
                            quality_score=model_data.get("quality_score", 0.5),
                            reliability_score=model_data.get("reliability_score", 0.5),
                            metadata=model_data.get("metadata", {}),
                        )
                        provider.models[model.model_id] = model
                        self.model_cache[model.model_id] = model

                    self.providers[provider.provider_id] = provider

                print(
                    f"✅ Loaded LLM orchestration config: "
                    f"{len(self.providers)} providers, {len(self.model_cache)} models"
                )
                return True
            else:
                print("📝 No existing LLM config found, starting fresh")
                self._create_default_config()
                return True

        except Exception as e:
            print(f"❌ Error loading LLM config: {e}")
            return False

    def save_config(self) -> bool:
        """Save LLM orchestration configuration."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            data: Dict[str, Any] = {"config": self.config, "providers": []}

            for provider in self.providers.values():
                provider_data = {
                    "provider_id": provider.provider_id,
                    "provider_type": provider.provider_type.value,
                    "name": provider.name,
                    "api_base": provider.api_base,
                    "auth_method": provider.auth_method,
                    "auth_config": provider.auth_config,
                    "rate_limits": provider.rate_limits,
                    "retry_config": provider.retry_config,
                    "health_check_endpoint": provider.health_check_endpoint,
                    "metadata": provider.metadata,
                    "models": {},
                }

                for model in provider.models.values():
                    provider_data["models"][model.model_id] = {
                        "model_id": model.model_id,
                        "name": model.name,
                        "display_name": model.display_name,
                        "capabilities": [cap.value for cap in model.capabilities],
                        "context_window": model.context_window,
                        "max_tokens": model.max_tokens,
                        "cost_per_1k_input": model.cost_per_1k_input,
                        "cost_per_1k_output": model.cost_per_1k_output,
                        "average_latency_ms": model.average_latency_ms,
                        "quality_score": model.quality_score,
                        "reliability_score": model.reliability_score,
                        "metadata": model.metadata,
                    }

                data["providers"].append(provider_data)

            return save_json(self.config_file, data, "LLM config")

        except Exception as e:
            print(f"❌ Error saving LLM config: {e}")
            return False

    def _create_default_config(self):
        """Create default LLM configuration."""
        ollama_provider = LLMProvider(
            provider_id="ollama-local",
            provider_type=LLMProviderType.OLLAMA,
            name="Local Ollama",
            api_base="http://localhost:11434",
            auth_method="none",
            rate_limits={"requests_per_hour": 1000, "tokens_per_hour": 1000000},
            health_check_endpoint="http://localhost:11434/api/tags",
        )

        ollama_models = {
            "qwen2.5-coder:7b": LLMModel(
                model_id="qwen2.5-coder:7b",
                provider=LLMProviderType.OLLAMA,
                name="qwen2.5-coder:7b",
                display_name="Qwen2.5 Coder 7B",
                capabilities=[
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.REASONING,
                    ModelCapability.CHAT,
                ],
                context_window=32768,
                max_tokens=4096,
                cost_per_1k_input=0.0,
                cost_per_1k_output=0.0,
                average_latency_ms=2000.0,
                quality_score=0.8,
                reliability_score=0.9,
            ),
            "phi3:3.8b": LLMModel(
                model_id="phi3:3.8b",
                provider=LLMProviderType.OLLAMA,
                name="phi3:3.8b",
                display_name="Phi3 3.8B",
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.REASONING,
                    ModelCapability.CHAT,
                ],
                context_window=4096,
                max_tokens=2048,
                cost_per_1k_input=0.0,
                cost_per_1k_output=0.0,
                average_latency_ms=1500.0,
                quality_score=0.7,
                reliability_score=0.8,
            ),
        }

        ollama_provider.models = ollama_models
        self.providers[ollama_provider.provider_id] = ollama_provider

        for model in ollama_models.values():
            self.model_cache[model.model_id] = model

        print("✅ Created default LLM configuration")

    # ── Lifecycle ───────────────────────────────────────────

    def start(self):
        """Start the LLM orchestrator."""
        with self.lock:
            if self.running:
                return
            self.running = True
            self._start_background_tasks()
            perform_health_checks(self.providers)
            print("✅ Started LLM orchestrator")

    def stop(self):
        """Stop the LLM orchestrator."""
        with self.lock:
            self.running = False
            for request_id in list(self.active_requests.keys()):
                self.cancel_request(request_id)
            print("✅ Stopped LLM orchestrator")

    # ── Provider / model management ─────────────────────────

    def add_provider(self, provider: LLMProvider) -> bool:
        """Add a new LLM provider."""
        with self.lock:
            if provider.provider_id in self.providers:
                print(f"⚠️  Provider {provider.provider_id} already exists")
                return False
            self.providers[provider.provider_id] = provider
            for model in provider.models.values():
                self.model_cache[model.model_id] = model
            print(f"✅ Added provider: {provider.provider_id}")
            return True

    def remove_provider(self, provider_id: str) -> bool:
        """Remove an LLM provider."""
        with self.lock:
            if provider_id not in self.providers:
                print(f"❌ Provider {provider_id} not found")
                return False
            provider = self.providers[provider_id]
            for model_id in provider.models.keys():
                if model_id in self.model_cache:
                    del self.model_cache[model_id]
            del self.providers[provider_id]
            print(f"✅ Removed provider: {provider_id}")
            return True

    def add_model(self, provider_id: str, model: LLMModel) -> bool:
        """Add a model to a provider."""
        with self.lock:
            if provider_id not in self.providers:
                print(f"❌ Provider {provider_id} not found")
                return False
            provider = self.providers[provider_id]
            provider.models[model.model_id] = model
            self.model_cache[model.model_id] = model
            print(f"✅ Added model {model.model_id} to provider {provider_id}")
            return True

    # ── Request execution ───────────────────────────────────

    def complete_request(self, request: LLMRequest) -> Optional[LLMResponse]:
        """Complete an LLM request with intelligent routing."""
        try:
            with self.lock:
                self.active_requests[request.request_id] = request

            routing_decision = self._route_request(request)
            if not routing_decision:
                return self._create_failed_response(request, "No suitable provider/model found")

            allowed, reason = self.rate_limiter.check_rate_limit(
                routing_decision["provider"],
                "default",
                LimitType.REQUESTS_PER_HOUR,
            )
            if not allowed:
                return self._create_failed_response(request, f"Rate limited: {reason}")

            response = self._execute_request(request, routing_decision)

            self.rate_limiter.record_request(
                routing_decision["provider"],
                "default",
                LimitType.REQUESTS_PER_HOUR,
                response.total_tokens,
                response.success,
            )

            self._add_to_history(response)
            return response

        except Exception as e:
            print(f"❌ Error completing request {request.request_id}: {e}")
            return self._create_failed_response(request, str(e))
        finally:
            with self.lock:
                self.active_requests.pop(request.request_id, None)

    def cancel_request(self, request_id: str) -> bool:
        """Cancel an active request."""
        with self.lock:
            if request_id not in self.active_requests:
                return False
            del self.active_requests[request_id]
            print(f"✅ Cancelled request {request_id}")
            return True

    def _route_request(self, request: LLMRequest) -> Optional[Dict[str, Any]]:
        """Route request to best provider/model."""
        routing_request = RoutingRequest(
            request_id=request.request_id,
            resource_type=ResourceType.LLM,
            provider=request.provider,
            account="default",
            model=request.model,
            priority=request.priority or RequestPriority.NORMAL,
            strategy=RoutingStrategy.AVAILABILITY_FIRST,
            requirements={
                "estimated_tokens": request.max_tokens,
                "capabilities": self._get_required_capabilities(request),
            },
            constraints={"max_cost": 0.1, "max_wait_time": request.timeout_seconds},
        )
        decision = self.routing_engine.route_request(routing_request)
        if not decision:
            return None
        return {
            "provider": decision.provider,
            "model": decision.model,
            "resource_id": decision.selected_resource,
            "confidence": decision.confidence,
            "estimated_wait_time": decision.estimated_wait_time,
            "estimated_cost": decision.estimated_cost,
        }

    def _execute_request(
        self, request: LLMRequest, routing_decision: Dict[str, Any]
    ) -> LLMResponse:
        """Execute LLM request via the appropriate provider executor."""
        provider_id = routing_decision["provider"]
        model_id = routing_decision["model"]
        provider = self.providers.get(provider_id)
        if not provider:
            return self._create_failed_response(request, f"Provider {provider_id} not found")
        model = provider.models.get(model_id)
        if not model:
            return self._create_failed_response(request, f"Model {model_id} not found")

        start_time = time.time()
        try:
            response = execute_request(request, provider, model)
            response.latency_ms = (time.time() - start_time) * 1000
            return response
        except Exception as e:
            return self._create_failed_response(request, str(e))

    def _get_required_capabilities(self, request: LLMRequest) -> List[str]:
        """Get required capabilities for request."""
        capabilities = []
        content = " ".join([msg.get("content", "") for msg in request.messages])
        if any(kw in content.lower() for kw in ["code", "function", "class", "algorithm"]):
            capabilities.append("code_generation")
        if any(kw in content.lower() for kw in ["why", "how", "explain", "reason"]):
            capabilities.append("reasoning")
        capabilities.append("chat")
        return capabilities

    @staticmethod
    def _create_failed_response(request: LLMRequest, error: str) -> LLMResponse:
        """Create a failed response."""
        return LLMResponse(
            request_id=request.request_id,
            provider="",
            model="",
            content="",
            finish_reason="error",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            latency_ms=0,
            cost=0.0,
            success=False,
            error=error,
        )

    def _add_to_history(self, response: LLMResponse):
        """Add response to history."""
        with self.lock:
            self.request_history.append(response)
            max_size = self.config["request_history_size"]
            if len(self.request_history) > max_size:
                self.request_history = self.request_history[-max_size:]

    # ── Query methods ───────────────────────────────────────

    def get_provider_status(self, provider_id: str = None) -> Dict[str, Any]:
        """Get status of LLM providers."""
        with self.lock:
            if provider_id:
                if provider_id not in self.providers:
                    return {}
                return self._get_single_provider_status(self.providers[provider_id])
            return self._get_all_provider_status()

    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model."""
        if model_id not in self.model_cache:
            return None
        model = self.model_cache[model_id]
        return {
            "model_id": model.model_id,
            "provider": model.provider.value,
            "name": model.name,
            "display_name": model.display_name,
            "capabilities": [cap.value for cap in model.capabilities],
            "context_window": model.context_window,
            "max_tokens": model.max_tokens,
            "cost_per_1k_input": model.cost_per_1k_input,
            "cost_per_1k_output": model.cost_per_1k_output,
            "average_latency_ms": model.average_latency_ms,
            "quality_score": model.quality_score,
            "reliability_score": model.reliability_score,
        }

    def list_models(
        self, provider_id: str = None, capability: ModelCapability = None
    ) -> List[Dict[str, Any]]:
        """List available models."""
        models = []
        for model in self.model_cache.values():
            if provider_id and model.provider.value != provider_id:
                continue
            if capability and capability not in model.capabilities:
                continue
            models.append(self.get_model_info(model.model_id))
        return models

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        with self.lock:
            total = len(self.request_history)
            successful = len([r for r in self.request_history if r.success])
            failed = total - successful
            total_cost = sum(r.cost for r in self.request_history)
            total_tokens = sum(r.total_tokens for r in self.request_history)

            provider_stats: Dict[str, Any] = {}
            model_stats: Dict[str, Any] = {}

            for resp in self.request_history:
                # Provider breakdown
                ps = provider_stats.setdefault(
                    resp.provider, {"requests": 0, "successful": 0, "cost": 0.0, "tokens": 0}
                )
                ps["requests"] += 1
                if resp.success:
                    ps["successful"] += 1
                ps["cost"] += resp.cost
                ps["tokens"] += resp.total_tokens

                # Model breakdown
                ms = model_stats.setdefault(
                    resp.model, {"requests": 0, "successful": 0, "average_latency": 0.0}
                )
                ms["requests"] += 1
                if resp.success:
                    ms["successful"] += 1
                if ms["requests"] > 0:
                    ms["average_latency"] = (
                        ms["average_latency"] * (ms["requests"] - 1) + resp.latency_ms
                    ) / ms["requests"]

            return {
                "total_requests": total,
                "successful_requests": successful,
                "failed_requests": failed,
                "success_rate": (successful / total * 100) if total > 0 else 0,
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "provider_stats": provider_stats,
                "model_stats": model_stats,
            }

    # ── Status helpers ──────────────────────────────────────

    def _get_single_provider_status(self, provider: LLMProvider) -> Dict[str, Any]:
        """Get status of a single provider."""
        health_status = "unknown"
        last_check = None
        if provider.health_check_endpoint:
            try:
                response = requests.get(provider.health_check_endpoint, timeout=5)
                health_status = "healthy" if response.status_code == 200 else "unhealthy"
                last_check = datetime.now().isoformat()
            except Exception:
                health_status = "error"
                last_check = datetime.now().isoformat()

        provider_requests = [r for r in self.request_history if r.provider == provider.provider_id]
        successful_requests = len([r for r in provider_requests if r.success])

        return {
            "provider_id": provider.provider_id,
            "provider_type": provider.provider_type.value,
            "name": provider.name,
            "api_base": provider.api_base,
            "health_status": health_status,
            "last_health_check": last_check,
            "models_count": len(provider.models),
            "total_requests": len(provider_requests),
            "successful_requests": successful_requests,
            "success_rate": (
                successful_requests / len(provider_requests) * 100
            )
            if provider_requests
            else 0,
            "rate_limits": provider.rate_limits,
        }

    def _get_all_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers."""
        status: Dict[str, Any] = {
            "total_providers": len(self.providers),
            "healthy_providers": 0,
            "unhealthy_providers": 0,
            "providers": {},
        }
        for provider in self.providers.values():
            ps = self._get_single_provider_status(provider)
            status["providers"][provider.provider_id] = ps
            if ps["health_status"] == "healthy":
                status["healthy_providers"] += 1
            elif ps["health_status"] in ("unhealthy", "error"):
                status["unhealthy_providers"] += 1
        return status

    # ── Background tasks ────────────────────────────────────

    def _start_background_tasks(self):
        """Start background tasks."""
        threading.Thread(target=health_check_worker, args=(self,), daemon=True).start()
        threading.Thread(target=self._config_save_worker, daemon=True).start()

    def _config_save_worker(self):
        """Background worker for configuration saving."""
        while self.running:
            try:
                time.sleep(300)
                self.save_config()
            except Exception as e:
                print(f"❌ Config save worker error: {e}")

    # ── Print summary ───────────────────────────────────────

    def print_status_summary(self):
        """Print comprehensive status summary."""
        print("🤖 LLM Orchestrator Status")
        print("==========================")

        self._print_usage_stats()
        self._print_provider_status()
        self._print_model_summary()
        print()
    
    def _print_usage_stats(self):
        """Print usage statistics."""
        usage_stats = self.get_usage_stats()
        print(f"📊 Total Requests: {usage_stats['total_requests']}")
        print(f"✅ Successful: {usage_stats['successful_requests']}")
        print(f"❌ Failed: {usage_stats['failed_requests']}")
        print(f"📈 Success Rate: {usage_stats['success_rate']:.1f}%")
        print(f"💰 Total Cost: ${usage_stats['total_cost']:.4f}")
        print(f"🔤 Total Tokens: {usage_stats['total_tokens']}")
    
    def _print_provider_status(self):
        """Print provider status information."""
        provider_status = self.get_provider_status()
        
        print(f"\n🏢 Providers ({provider_status['total_providers']}):")
        print(f"  🟢 Healthy: {provider_status['healthy_providers']}")
        print(f"  🔴 Unhealthy: {provider_status['unhealthy_providers']}")
        
        for pid, st in provider_status["providers"].items():
            print(
                f"  • {pid}: {st['health_status']} "
                f"({st['success_rate']:.1f}% success, {st['models_count']} models)"
            )
    
    def _print_model_summary(self):
        """Print model capability summary."""
        print(f"\n🤖 Models ({len(self.model_cache)}):")
        capability_counts: Dict[str, int] = {}
        for model in self.model_cache.values():
            for cap in model.capabilities:
                capability_counts[cap.value] = capability_counts.get(cap.value, 0) + 1
        for cap_name, count in capability_counts.items():
            print(f"  • {cap_name}: {count} models")
