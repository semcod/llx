"""
Routing Engine — intelligent request routing to optimal resources.
Extracted from the monolithic routing_engine.py.
"""

import time
import threading
from typing import Dict, List, Optional, Any
from pathlib import Path

from .._utils import load_json, save_json

from .models import (
    RoutingStrategy,
    ResourceType,
    RoutingRequest,
    RoutingDecision,
    RoutingMetrics,
)
from ..session.manager import SessionManager
from ..session.models import SessionType, SessionStatus
from ..instances.manager import InstanceManager
from ..instances.models import InstanceType, InstanceStatus
from ..ratelimit.limiter import RateLimiter
from ..ratelimit.models import LimitType
from ..queue.manager import QueueManager


class RoutingEngine:
    """Intelligent routing engine for LLM and VS Code requests."""

    def __init__(self, config_file: str = None):
        self.project_root = Path.cwd()
        self.config_file = config_file or self.project_root / "orchestration" / "routing.json"

        # Initialize managers
        self.session_manager = SessionManager()
        self.instance_manager = InstanceManager()
        self.rate_limiter = RateLimiter()
        self.queue_manager = QueueManager()

        # Routing configuration
        self.routing_config = {
            "default_strategy": RoutingStrategy.AVAILABILITY_FIRST,
            "fallback_strategies": [
                RoutingStrategy.LEAST_LOADED,
                RoutingStrategy.ROUND_ROBIN,
            ],
            "max_routing_time": 5.0,
            "confidence_threshold": 0.7,
            "cost_weights": {
                "anthropic": 1.0,
                "openai": 0.8,
                "google": 0.6,
                "openrouter": 0.4,
                "ollama": 0.1,
            },
            "performance_weights": {
                "anthropic": 0.9,
                "openai": 0.8,
                "google": 0.7,
                "openrouter": 0.6,
                "ollama": 0.5,
            },
        }

        self.metrics = RoutingMetrics()
        self.lock = threading.RLock()

        self.load_config()
        self.start_background_tasks()

    # ── Config persistence ──────────────────────────────────

    def load_config(self) -> bool:
        """Load routing configuration."""
        data = load_json(self.config_file, "routing config")
        if data is not None:
            self.routing_config.update(data.get("routing", {}))
            print("✅ Loaded routing configuration")
        else:
            print("📝 Using default routing configuration")
        return True

    def save_config(self) -> bool:
        """Save routing configuration."""
        data = {
            "routing": self.routing_config,
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "average_routing_time": self.metrics.average_routing_time,
                "resource_utilization": self.metrics.resource_utilization,
                "strategy_performance": self.metrics.strategy_performance,
                "provider_performance": self.metrics.provider_performance,
            },
        }
        return save_json(self.config_file, data, "routing config")

    # ── Main routing ────────────────────────────────────────

    def route_request(self, request: RoutingRequest) -> Optional[RoutingDecision]:
        """Route a request to the optimal resource."""
        start_time = time.time()

        try:
            with self.lock:
                self.metrics.total_requests += 1

            candidates = self._get_candidates(request)
            if not candidates:
                return self._create_no_resources_decision(request)

            decision = self._apply_routing_strategy(request, candidates)
            if not decision:
                return self._create_routing_failed_decision(request)

            if not self._validate_decision(decision):
                return self._create_validation_failed_decision(request)

            routing_time = time.time() - start_time
            self._update_routing_metrics(decision, routing_time, True)

            print(f"✅ Routed request {request.request_id} to {decision.selected_resource}")
            return decision

        except Exception as e:
            print(f"❌ Routing error for request {request.request_id}: {e}")
            routing_time = time.time() - start_time
            self._update_routing_metrics(None, routing_time, False)
            return None

    # ── Candidate gathering ─────────────────────────────────

    def _get_candidates(self, request: RoutingRequest) -> List[Dict[str, Any]]:
        """Get candidate resources for routing."""
        if request.resource_type == ResourceType.LLM:
            candidates = self._get_llm_candidates(request)
        elif request.resource_type == ResourceType.VSCODE:
            candidates = self._get_vscode_candidates(request)
        elif request.resource_type == ResourceType.AI_TOOLS:
            candidates = self._get_ai_tools_candidates(request)
        else:
            candidates = []

        candidates = self._filter_candidates(candidates, request.constraints)
        candidates = self._filter_by_rate_limits(candidates, request)
        return candidates

    def _get_llm_candidates(self, request: RoutingRequest) -> List[Dict[str, Any]]:
        """Get LLM candidates."""
        candidates = []
        available_sessions = self.session_manager.list_sessions(
            SessionType.LLM, SessionStatus.IDLE
        )

        for session in available_sessions:
            if request.provider and session["provider"] != request.provider:
                continue
            if request.account and session["account"] != request.account:
                continue
            if request.model and session["model"] != request.model:
                continue

            status = self.rate_limiter.get_status(session["provider"], session["account"])
            key = f"{session['provider']}:{session['account']}"
            if key in status and status[key]["status"] == "rate_limited":
                continue

            score = self._calculate_llm_score(session, request)
            candidates.append({
                "resource_id": session["session_id"],
                "type": "session",
                "provider": session["provider"],
                "account": session["account"],
                "model": session["model"],
                "score": score,
                "utilization": session.get("utilization", 0),
                "estimated_wait_time": session.get("time_until_available", 0),
                "cost_per_token": self._get_cost_per_token(session["provider"], session["model"]),
                "performance": self._get_provider_performance(session["provider"]),
            })
        return candidates

    def _get_vscode_candidates(self, request: RoutingRequest) -> List[Dict[str, Any]]:
        """Get VS Code candidates."""
        candidates = []
        available = self.instance_manager.list_instances(
            InstanceType.VSCODE, InstanceStatus.RUNNING
        )

        for inst in available:
            if request.provider and inst["provider"] != request.provider:
                continue
            if request.account and inst["account"] != request.account:
                continue

            score = self._calculate_vscode_score(inst, request)
            candidates.append({
                "resource_id": inst["instance_id"],
                "type": "instance",
                "provider": inst["provider"],
                "account": inst["account"],
                "model": inst.get("image", "vscode"),
                "score": score,
                "utilization": inst.get("cpu_usage", 0),
                "estimated_wait_time": 0,
                "cost_per_hour": self._get_vscode_cost_per_hour(inst["provider"]),
                "performance": inst.get("health_status", "unknown"),
            })
        return candidates

    def _get_ai_tools_candidates(self, request: RoutingRequest) -> List[Dict[str, Any]]:
        """Get AI tools candidates."""
        candidates = []
        available = self.instance_manager.list_instances(
            InstanceType.AI_TOOLS, InstanceStatus.RUNNING
        )

        for inst in available:
            if request.provider and inst["provider"] != request.provider:
                continue
            if request.account and inst["account"] != request.account:
                continue

            score = self._calculate_ai_tools_score(inst, request)
            candidates.append({
                "resource_id": inst["instance_id"],
                "type": "instance",
                "provider": inst["provider"],
                "account": inst["account"],
                "model": inst.get("image", "ai-tools"),
                "score": score,
                "utilization": inst.get("cpu_usage", 0),
                "estimated_wait_time": 0,
                "cost_per_hour": self._get_ai_tools_cost_per_hour(inst["provider"]),
                "performance": inst.get("health_status", "unknown"),
            })
        return candidates

    # ── Filtering ───────────────────────────────────────────

    def _filter_candidates(
        self, candidates: List[Dict[str, Any]], constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Filter candidates based on constraints."""
        filtered = []
        for c in candidates:
            max_cost = constraints.get("max_cost")
            if max_cost:
                cost_key = "cost_per_token" if c["type"] == "session" else "cost_per_hour"
                if c.get(cost_key, float("inf")) > max_cost:
                    continue
            min_perf = constraints.get("min_performance")
            if min_perf and c.get("performance", 0) < min_perf:
                continue
            max_util = constraints.get("max_utilization")
            if max_util and c.get("utilization", 0) > max_util:
                continue
            max_wait = constraints.get("max_wait_time")
            if max_wait and c.get("estimated_wait_time", 0) > max_wait:
                continue
            filtered.append(c)
        return filtered

    def _filter_by_rate_limits(
        self, candidates: List[Dict[str, Any]], request: RoutingRequest
    ) -> List[Dict[str, Any]]:
        """Filter candidates by rate limits."""
        filtered = []
        for c in candidates:
            if c["type"] == "session":
                allowed, _ = self.rate_limiter.check_rate_limit(
                    c["provider"], c["account"], LimitType.REQUESTS_PER_HOUR
                )
                if allowed:
                    filtered.append(c)
            else:
                filtered.append(c)
        return filtered

    # ── Strategy application ────────────────────────────────

    def _apply_routing_strategy(
        self, request: RoutingRequest, candidates: List[Dict[str, Any]]
    ) -> Optional[RoutingDecision]:
        """Apply routing strategy to select best candidate."""
        if not candidates:
            return None

        strategy = request.strategy or self.routing_config["default_strategy"]
        decision = self._apply_strategy(request, candidates, strategy)

        if decision and decision.confidence >= self.routing_config["confidence_threshold"]:
            return decision

        for fallback in self.routing_config["fallback_strategies"]:
            decision = self._apply_strategy(request, candidates, fallback)
            if decision and decision.confidence >= self.routing_config["confidence_threshold"] * 0.8:
                return decision

        if candidates:
            best = max(candidates, key=lambda x: x["score"])
            return self._create_decision_from_candidate(request, best, strategy, 0.5)

        return None

    def _apply_strategy(
        self,
        request: RoutingRequest,
        candidates: List[Dict[str, Any]],
        strategy: RoutingStrategy,
    ) -> Optional[RoutingDecision]:
        """Apply a specific routing strategy."""
        _STRATEGIES = {
            RoutingStrategy.ROUND_ROBIN: self._round_robin_strategy,
            RoutingStrategy.LEAST_LOADED: self._least_loaded_strategy,
            RoutingStrategy.PRIORITY_BASED: self._priority_based_strategy,
            RoutingStrategy.COST_OPTIMIZED: self._cost_optimized_strategy,
            RoutingStrategy.PERFORMANCE_OPTIMIZED: self._performance_optimized_strategy,
            RoutingStrategy.AVAILABILITY_FIRST: self._availability_first_strategy,
        }
        handler = _STRATEGIES.get(strategy)
        if handler:
            return handler(request, candidates)
        return None

    def _round_robin_strategy(self, request, candidates):
        if not candidates:
            return None
        index = hash(request.request_id) % len(candidates)
        selected = candidates[index]
        return self._create_decision_from_candidate(
            request, selected, RoutingStrategy.ROUND_ROBIN, 0.7,
            ["Round-robin selection", f"Selected index {index} of {len(candidates)} candidates"],
        )

    def _least_loaded_strategy(self, request, candidates):
        if not candidates:
            return None
        selected = sorted(candidates, key=lambda x: x["utilization"])[0]
        return self._create_decision_from_candidate(
            request, selected, RoutingStrategy.LEAST_LOADED, 0.8,
            ["Least-loaded selection", f"Utilization: {selected['utilization']:.1f}%"],
        )

    def _priority_based_strategy(self, request, candidates):
        if not candidates:
            return None
        selected = sorted(candidates, key=lambda x: x["score"], reverse=True)[0]
        return self._create_decision_from_candidate(
            request, selected, RoutingStrategy.PRIORITY_BASED, 0.9,
            ["Priority-based selection", f"Score: {selected['score']:.2f}"],
        )

    def _cost_optimized_strategy(self, request, candidates):
        if not candidates:
            return None
        cost_key = "cost_per_token" if candidates[0]["type"] == "session" else "cost_per_hour"
        selected = sorted(candidates, key=lambda x: x.get(cost_key, float("inf")))[0]
        return self._create_decision_from_candidate(
            request, selected, RoutingStrategy.COST_OPTIMIZED, 0.8,
            ["Cost-optimized selection", f"Cost: {selected.get(cost_key, 'unknown')}"],
        )

    def _performance_optimized_strategy(self, request, candidates):
        if not candidates:
            return None
        selected = sorted(candidates, key=lambda x: x.get("performance", 0), reverse=True)[0]
        return self._create_decision_from_candidate(
            request, selected, RoutingStrategy.PERFORMANCE_OPTIMIZED, 0.85,
            ["Performance-optimized selection", f"Performance: {selected.get('performance', 'unknown')}"],
        )

    def _availability_first_strategy(self, request, candidates):
        if not candidates:
            return None
        selected = sorted(candidates, key=lambda x: x.get("estimated_wait_time", 0))[0]
        return self._create_decision_from_candidate(
            request, selected, RoutingStrategy.AVAILABILITY_FIRST, 0.9,
            ["Availability-first selection", f"Wait time: {selected.get('estimated_wait_time', 0)}s"],
        )

    # ── Decision helpers ────────────────────────────────────

    def _create_decision_from_candidate(
        self,
        request: RoutingRequest,
        candidate: Dict[str, Any],
        strategy: RoutingStrategy,
        confidence: float,
        reasoning: List[str] = None,
    ) -> RoutingDecision:
        if reasoning is None:
            reasoning = [f"Selected {candidate['resource_id']}"]

        estimated_cost = 0.0
        if candidate["type"] == "session":
            estimated_cost = candidate.get("cost_per_token", 0) * request.requirements.get("estimated_tokens", 1000)
        else:
            estimated_cost = candidate.get("cost_per_hour", 0) * request.requirements.get("estimated_hours", 1)

        return RoutingDecision(
            request_id=request.request_id,
            resource_type=request.resource_type,
            selected_resource=candidate["resource_id"],
            provider=candidate["provider"],
            account=candidate["account"],
            model=candidate["model"],
            strategy_used=strategy,
            confidence=confidence,
            estimated_wait_time=candidate.get("estimated_wait_time", 0),
            estimated_cost=estimated_cost,
            reasoning=reasoning,
            metadata={
                "candidate_type": candidate["type"],
                "utilization": candidate.get("utilization", 0),
                "score": candidate.get("score", 0),
            },
        )

    def _validate_decision(self, decision: RoutingDecision) -> bool:
        """Validate routing decision."""
        if decision.resource_type == ResourceType.LLM:
            session = self.session_manager.get_session_status(decision.selected_resource)
            if not session or session["status"] != "idle":
                return False
        elif decision.resource_type in (ResourceType.VSCODE, ResourceType.AI_TOOLS):
            instance = self.instance_manager.get_instance_status(decision.selected_resource)
            if not instance or instance["status"] != "running":
                return False

        if decision.resource_type == ResourceType.LLM:
            allowed, _ = self.rate_limiter.check_rate_limit(decision.provider, decision.account)
            if not allowed:
                return False
        return True

    def _create_no_resources_decision(self, request: RoutingRequest) -> RoutingDecision:
        return RoutingDecision(
            request_id=request.request_id,
            resource_type=request.resource_type,
            selected_resource="", provider="", account="", model="",
            strategy_used=request.strategy or self.routing_config["default_strategy"],
            confidence=0.0, estimated_wait_time=float("inf"), estimated_cost=0.0,
            reasoning=["No available resources"],
            metadata={"error": "no_resources"},
        )

    def _create_routing_failed_decision(self, request: RoutingRequest) -> RoutingDecision:
        return RoutingDecision(
            request_id=request.request_id,
            resource_type=request.resource_type,
            selected_resource="", provider="", account="", model="",
            strategy_used=request.strategy or self.routing_config["default_strategy"],
            confidence=0.0, estimated_wait_time=float("inf"), estimated_cost=0.0,
            reasoning=["Routing failed"],
            metadata={"error": "routing_failed"},
        )

    def _create_validation_failed_decision(self, request: RoutingRequest) -> RoutingDecision:
        return RoutingDecision(
            request_id=request.request_id,
            resource_type=request.resource_type,
            selected_resource="", provider="", account="", model="",
            strategy_used=request.strategy or self.routing_config["default_strategy"],
            confidence=0.0, estimated_wait_time=float("inf"), estimated_cost=0.0,
            reasoning=["Validation failed"],
            metadata={"error": "validation_failed"},
        )

    # ── Scoring ─────────────────────────────────────────────

    def _calculate_llm_score(self, session: Dict[str, Any], request: RoutingRequest) -> float:
        score = 0.0
        utilization = session.get("utilization", 0)
        score += (100 - utilization) * 0.3
        score += self.routing_config["cost_weights"].get(session["provider"], 0.5) * 20
        score += self.routing_config["performance_weights"].get(session["provider"], 0.5) * 20
        score -= min(session.get("time_until_available", 0), 300) * 0.1
        score -= session.get("errors_count", 0) * 5
        return max(0, score)

    def _calculate_vscode_score(self, instance: Dict[str, Any], request: RoutingRequest) -> float:
        score = 0.0
        score += (100 - instance.get("cpu_usage", 0)) * 0.4
        score += (100 - instance.get("memory_usage", 0)) * 0.3
        health = instance.get("health_status", "unknown")
        if health == "healthy":
            score += 30
        elif health == "unknown":
            score += 10
        else:
            score -= 10
        score -= instance.get("error_count", 0) * 5
        return max(0, score)

    def _calculate_ai_tools_score(self, instance: Dict[str, Any], request: RoutingRequest) -> float:
        return self._calculate_vscode_score(instance, request)

    def _get_cost_per_token(self, provider: str, model: str) -> float:
        costs = {
            "anthropic": {"claude-3-sonnet": 0.015, "claude-3-haiku": 0.0025},
            "openai": {"gpt-4": 0.03, "gpt-3.5-turbo": 0.002},
            "google": {"gemini-pro": 0.0025},
            "openrouter": {"mixtral": 0.0015},
            "ollama": {"qwen2.5-coder:7b": 0.0},
        }
        return costs.get(provider, {}).get(model, 0.01)

    def _get_vscode_cost_per_hour(self, provider: str) -> float:
        return {"default": 0.05, "premium": 0.15, "enterprise": 0.50}.get(provider, 0.05)

    def _get_ai_tools_cost_per_hour(self, provider: str) -> float:
        return self._get_vscode_cost_per_hour(provider)

    def _get_provider_performance(self, provider: str) -> float:
        return self.routing_config["performance_weights"].get(provider, 0.5)

    # ── Metrics ─────────────────────────────────────────────

    def _update_routing_metrics(
        self, decision: Optional[RoutingDecision], routing_time: float, success: bool
    ):
        with self.lock:
            if success:
                self.metrics.successful_requests += 1
            else:
                self.metrics.failed_requests += 1

            total = self.metrics.successful_requests + self.metrics.failed_requests
            self.metrics.average_routing_time = (
                (self.metrics.average_routing_time * (total - 1) + routing_time) / total
            )

            if decision:
                strategy = decision.strategy_used.value
                if strategy not in self.metrics.strategy_performance:
                    self.metrics.strategy_performance[strategy] = {"success": 0, "total": 0}
                self.metrics.strategy_performance[strategy]["total"] += 1
                if success:
                    self.metrics.strategy_performance[strategy]["success"] += 1

                provider = decision.provider
                if provider not in self.metrics.provider_performance:
                    self.metrics.provider_performance[provider] = {"success": 0, "total": 0}
                self.metrics.provider_performance[provider]["total"] += 1
                if success:
                    self.metrics.provider_performance[provider]["success"] += 1

    # ── Background tasks ────────────────────────────────────

    def start_background_tasks(self):
        """Start background tasks for metrics and optimization."""
        threading.Thread(target=self._metrics_worker, daemon=True).start()
        threading.Thread(target=self._optimization_worker, daemon=True).start()

    def _metrics_worker(self):
        while True:
            try:
                time.sleep(60)
                self._collect_system_metrics()
                if time.time() % 300 < 60:
                    self.save_config()
            except Exception as e:
                print(f"❌ Metrics worker error: {e}")

    def _optimization_worker(self):
        while True:
            try:
                time.sleep(300)
                self._optimize_routing()
            except Exception as e:
                print(f"❌ Optimization worker error: {e}")

    def _collect_system_metrics(self):
        for provider, account in [
            (s["provider"], s["account"]) for s in self.session_manager.list_sessions()
        ]:
            key = f"{provider}:{account}"
            self.metrics.resource_utilization[key] = 0.0

    def _optimize_routing(self):
        for strategy, performance in self.metrics.strategy_performance.items():
            if performance["total"] > 10:
                success_rate = performance["success"] / performance["total"]
                if success_rate > 0.9:
                    print(f"📈 Strategy {strategy} performing well ({success_rate:.1%})")
                elif success_rate < 0.7:
                    print(f"📉 Strategy {strategy} performing poorly ({success_rate:.1%})")

    # ── Status / summary ────────────────────────────────────

    def get_routing_status(self) -> Dict[str, Any]:
        """Get comprehensive routing status."""
        return {
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "success_rate": (
                (self.metrics.successful_requests / self.metrics.total_requests * 100)
                if self.metrics.total_requests > 0
                else 0
            ),
            "average_routing_time": self.metrics.average_routing_time,
            "default_strategy": self.routing_config["default_strategy"],
            "strategy_performance": self.metrics.strategy_performance,
            "provider_performance": self.metrics.provider_performance,
            "resource_utilization": self.metrics.resource_utilization,
        }

    def print_status_summary(self):
        """Print comprehensive status summary."""
        print("🧭 Routing Engine Status")
        print("=======================")

        status = self.get_routing_status()
        print(f"📊 Total Requests: {status['total_requests']}")
        print(f"✅ Successful: {status['successful_requests']}")
        print(f"❌ Failed: {status['failed_requests']}")
        print(f"📈 Success Rate: {status['success_rate']:.1f}%")
        print(f"⏱️  Avg Routing Time: {status['average_routing_time']:.3f}s")
        print(f"🎯 Default Strategy: {status['default_strategy']}")

        if status["strategy_performance"]:
            print("\n📊 Strategy Performance:")
            for strategy, perf in status["strategy_performance"].items():
                sr = perf["success"] / perf["total"] * 100 if perf["total"] > 0 else 0
                print(f"  • {strategy}: {sr:.1f}% ({perf['success']}/{perf['total']})")

        if status["provider_performance"]:
            print("\n🏢 Provider Performance:")
            for provider, perf in status["provider_performance"].items():
                sr = perf["success"] / perf["total"] * 100 if perf["total"] > 0 else 0
                print(f"  • {provider}: {sr:.1f}% ({perf['success']}/{perf['total']})")

        print()
