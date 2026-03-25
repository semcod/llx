"""
Routing Engine for llx Orchestration
Intelligent routing of requests to optimal LLM and VS Code instances.
"""

import os
import sys
import json
import time
import threading
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import requests
import random

from .session_manager import SessionManager, SessionType, SessionStatus
from .instance_manager import InstanceManager, InstanceType, InstanceStatus
from .rate_limiter import RateLimiter, LimitType
from .queue_manager import QueueManager, RequestPriority


class RoutingStrategy(Enum):
    """Routing strategies."""
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    PRIORITY_BASED = "priority_based"
    COST_OPTIMIZED = "cost_optimized"
    PERFORMANCE_OPTIMIZED = "performance_optimized"
    AVAILABILITY_FIRST = "availability_first"


class ResourceType(Enum):
    """Types of resources to route to."""
    LLM = "llm"
    VSCODE = "vscode"
    AI_TOOLS = "ai_tools"


@dataclass
class RoutingRequest:
    """A request to be routed."""
    request_id: str
    resource_type: ResourceType
    provider: Optional[str]
    account: Optional[str]
    model: Optional[str]
    priority: RequestPriority
    strategy: RoutingStrategy
    requirements: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutingDecision:
    """A routing decision."""
    request_id: str
    resource_type: ResourceType
    selected_resource: str
    provider: str
    account: str
    model: str
    strategy_used: RoutingStrategy
    confidence: float
    estimated_wait_time: float
    estimated_cost: float
    reasoning: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutingMetrics:
    """Metrics for routing performance."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_routing_time: float = 0.0
    resource_utilization: Dict[str, float] = field(default_factory=dict)
    strategy_performance: Dict[str, Dict[str, float]] = field(default_factory=dict)
    provider_performance: Dict[str, Dict[str, float]] = field(default_factory=dict)


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
                RoutingStrategy.ROUND_ROBIN
            ],
            "max_routing_time": 5.0,  # seconds
            "confidence_threshold": 0.7,
            "cost_weights": {
                "anthropic": 1.0,
                "openai": 0.8,
                "google": 0.6,
                "openrouter": 0.4,
                "ollama": 0.1
            },
            "performance_weights": {
                "anthropic": 0.9,
                "openai": 0.8,
                "google": 0.7,
                "openrouter": 0.6,
                "ollama": 0.5
            }
        }
        
        # Metrics
        self.metrics = RoutingMetrics()
        self.lock = threading.RLock()
        
        # Load configuration
        self.load_config()
        
        # Start background tasks
        self.start_background_tasks()
    
    def load_config(self) -> bool:
        """Load routing configuration."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                self.routing_config.update(data.get("routing", {}))
                print(f"✅ Loaded routing configuration")
                return True
            else:
                print("📝 Using default routing configuration")
                return True
                
        except Exception as e:
            print(f"❌ Error loading routing config: {e}")
            return False
    
    def save_config(self) -> bool:
        """Save routing configuration."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "routing": self.routing_config,
                "metrics": {
                    "total_requests": self.metrics.total_requests,
                    "successful_requests": self.metrics.successful_requests,
                    "failed_requests": self.metrics.failed_requests,
                    "average_routing_time": self.metrics.average_routing_time,
                    "resource_utilization": self.metrics.resource_utilization,
                    "strategy_performance": self.metrics.strategy_performance,
                    "provider_performance": self.metrics.provider_performance
                }
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving routing config: {e}")
            return False
    
    def route_request(self, request: RoutingRequest) -> Optional[RoutingDecision]:
        """Route a request to the optimal resource."""
        start_time = time.time()
        
        try:
            with self.lock:
                self.metrics.total_requests += 1
            
            # Get candidates
            candidates = self._get_candidates(request)
            
            if not candidates:
                return self._create_no_resources_decision(request)
            
            # Apply routing strategy
            decision = self._apply_routing_strategy(request, candidates)
            
            if not decision:
                return self._create_routing_failed_decision(request)
            
            # Validate decision
            if not self._validate_decision(decision):
                return self._create_validation_failed_decision(request)
            
            # Update metrics
            routing_time = time.time() - start_time
            self._update_routing_metrics(decision, routing_time, True)
            
            print(f"✅ Routed request {request.request_id} to {decision.selected_resource}")
            return decision
            
        except Exception as e:
            print(f"❌ Routing error for request {request.request_id}: {e}")
            
            # Update metrics
            routing_time = time.time() - start_time
            self._update_routing_metrics(None, routing_time, False)
            
            return None
    
    def _get_candidates(self, request: RoutingRequest) -> List[Dict[str, Any]]:
        """Get candidate resources for routing."""
        candidates = []
        
        if request.resource_type == ResourceType.LLM:
            candidates = self._get_llm_candidates(request)
        elif request.resource_type == ResourceType.VSCODE:
            candidates = self._get_vscode_candidates(request)
        elif request.resource_type == ResourceType.AI_TOOLS:
            candidates = self._get_ai_tools_candidates(request)
        
        # Filter by constraints
        candidates = self._filter_candidates(candidates, request.constraints)
        
        # Filter by rate limits
        candidates = self._filter_by_rate_limits(candidates, request)
        
        return candidates
    
    def _get_llm_candidates(self, request: RoutingRequest) -> List[Dict[str, Any]]:
        """Get LLM candidates."""
        candidates = []
        
        # Get available sessions
        session_type = SessionType.LLM
        available_sessions = self.session_manager.list_sessions(session_type, SessionStatus.IDLE)
        
        for session in available_sessions:
            # Check if session matches requirements
            if request.provider and session["provider"] != request.provider:
                continue
            
            if request.account and session["account"] != request.account:
                continue
            
            if request.model and session["model"] != request.model:
                continue
            
            # Get rate limit status
            rate_limit_status = self.rate_limiter.get_status(session["provider"], session["account"])
            provider_account_key = f"{session['provider']}:{session['account']}"
            
            if provider_account_key in rate_limit_status:
                status = rate_limit_status[provider_account_key]
                if status["status"] == "rate_limited":
                    continue
            
            # Calculate score
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
                "performance": self._get_provider_performance(session["provider"])
            })
        
        return candidates
    
    def _get_vscode_candidates(self, request: RoutingRequest) -> List[Dict[str, Any]]:
        """Get VS Code candidates."""
        candidates = []
        
        # Get available instances
        instance_type = InstanceType.VSCODE
        available_instances = self.instance_manager.list_instances(instance_type, InstanceStatus.RUNNING)
        
        for instance in available_instances:
            # Check if instance matches requirements
            if request.provider and instance["provider"] != request.provider:
                continue
            
            if request.account and instance["account"] != request.account:
                continue
            
            # Calculate score
            score = self._calculate_vscode_score(instance, request)
            
            candidates.append({
                "resource_id": instance["instance_id"],
                "type": "instance",
                "provider": instance["provider"],
                "account": instance["account"],
                "model": instance.get("image", "vscode"),
                "score": score,
                "utilization": instance.get("cpu_usage", 0),
                "estimated_wait_time": 0,  # VS Code instances are usually available immediately
                "cost_per_hour": self._get_vscode_cost_per_hour(instance["provider"]),
                "performance": instance.get("health_status", "unknown")
            })
        
        return candidates
    
    def _get_ai_tools_candidates(self, request: RoutingRequest) -> List[Dict[str, Any]]:
        """Get AI tools candidates."""
        candidates = []
        
        # Get available instances
        instance_type = InstanceType.AI_TOOLS
        available_instances = self.instance_manager.list_instances(instance_type, InstanceStatus.RUNNING)
        
        for instance in available_instances:
            # Check if instance matches requirements
            if request.provider and instance["provider"] != request.provider:
                continue
            
            if request.account and instance["account"] != request.account:
                continue
            
            # Calculate score
            score = self._calculate_ai_tools_score(instance, request)
            
            candidates.append({
                "resource_id": instance["instance_id"],
                "type": "instance",
                "provider": instance["provider"],
                "account": instance["account"],
                "model": instance.get("image", "ai-tools"),
                "score": score,
                "utilization": instance.get("cpu_usage", 0),
                "estimated_wait_time": 0,
                "cost_per_hour": self._get_ai_tools_cost_per_hour(instance["provider"]),
                "performance": instance.get("health_status", "unknown")
            })
        
        return candidates
    
    def _filter_candidates(self, candidates: List[Dict[str, Any]], constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter candidates based on constraints."""
        filtered = []
        
        for candidate in candidates:
            # Check cost constraints
            max_cost = constraints.get("max_cost")
            if max_cost:
                cost_key = "cost_per_token" if candidate["type"] == "session" else "cost_per_hour"
                if candidate.get(cost_key, float('inf')) > max_cost:
                    continue
            
            # Check performance constraints
            min_performance = constraints.get("min_performance")
            if min_performance and candidate.get("performance", 0) < min_performance:
                continue
            
            # Check utilization constraints
            max_utilization = constraints.get("max_utilization")
            if max_utilization and candidate.get("utilization", 0) > max_utilization:
                continue
            
            # Check wait time constraints
            max_wait_time = constraints.get("max_wait_time")
            if max_wait_time and candidate.get("estimated_wait_time", 0) > max_wait_time:
                continue
            
            filtered.append(candidate)
        
        return filtered
    
    def _filter_by_rate_limits(self, candidates: List[Dict[str, Any]], request: RoutingRequest) -> List[Dict[str, Any]]:
        """Filter candidates by rate limits."""
        filtered = []
        
        for candidate in candidates:
            if candidate["type"] == "session":
                # Check rate limit for LLM sessions
                allowed, _ = self.rate_limiter.check_rate_limit(
                    candidate["provider"],
                    candidate["account"],
                    LimitType.REQUESTS_PER_HOUR
                )
                
                if allowed:
                    filtered.append(candidate)
            else:
                # VS Code and AI tools instances typically don't have rate limits
                filtered.append(candidate)
        
        return filtered
    
    def _apply_routing_strategy(self, request: RoutingRequest, candidates: List[Dict[str, Any]]) -> Optional[RoutingDecision]:
        """Apply routing strategy to select best candidate."""
        if not candidates:
            return None
        
        # Try primary strategy
        strategy = request.strategy or self.routing_config["default_strategy"]
        decision = self._apply_strategy(request, candidates, strategy)
        
        if decision and decision.confidence >= self.routing_config["confidence_threshold"]:
            return decision
        
        # Try fallback strategies
        for fallback_strategy in self.routing_config["fallback_strategies"]:
            decision = self._apply_strategy(request, candidates, fallback_strategy)
            if decision and decision.confidence >= self.routing_config["confidence_threshold"] * 0.8:
                return decision
        
        # If no strategy meets threshold, return best available
        if candidates:
            best_candidate = max(candidates, key=lambda x: x["score"])
            return self._create_decision_from_candidate(request, best_candidate, strategy, 0.5)
        
        return None
    
    def _apply_strategy(self, request: RoutingRequest, candidates: List[Dict[str, Any]], strategy: RoutingStrategy) -> Optional[RoutingDecision]:
        """Apply a specific routing strategy."""
        if strategy == RoutingStrategy.ROUND_ROBIN:
            return self._round_robin_strategy(request, candidates)
        elif strategy == RoutingStrategy.LEAST_LOADED:
            return self._least_loaded_strategy(request, candidates)
        elif strategy == RoutingStrategy.PRIORITY_BASED:
            return self._priority_based_strategy(request, candidates)
        elif strategy == RoutingStrategy.COST_OPTIMIZED:
            return self._cost_optimized_strategy(request, candidates)
        elif strategy == RoutingStrategy.PERFORMANCE_OPTIMIZED:
            return self._performance_optimized_strategy(request, candidates)
        elif strategy == RoutingStrategy.AVAILABILITY_FIRST:
            return self._availability_first_strategy(request, candidates)
        else:
            return None
    
    def _round_robin_strategy(self, request: RoutingRequest, candidates: List[Dict[str, Any]]) -> Optional[RoutingDecision]:
        """Round-robin routing strategy."""
        if not candidates:
            return None
        
        # Simple round-robin based on request ID hash
        index = hash(request.request_id) % len(candidates)
        selected = candidates[index]
        
        confidence = 0.7  # Medium confidence for round-robin
        reasoning = ["Round-robin selection", f"Selected index {index} of {len(candidates)} candidates"]
        
        return self._create_decision_from_candidate(request, selected, RoutingStrategy.ROUND_ROBIN, confidence, reasoning)
    
    def _least_loaded_strategy(self, request: RoutingRequest, candidates: List[Dict[str, Any]]) -> Optional[RoutingDecision]:
        """Least-loaded routing strategy."""
        if not candidates:
            return None
        
        # Sort by utilization (lowest first)
        sorted_candidates = sorted(candidates, key=lambda x: x["utilization"])
        selected = sorted_candidates[0]
        
        confidence = 0.8  # High confidence for least-loaded
        reasoning = [f"Least-loaded selection", f"Utilization: {selected['utilization']:.1f}%"]
        
        return self._create_decision_from_candidate(request, selected, RoutingStrategy.LEAST_LOADED, confidence, reasoning)
    
    def _priority_based_strategy(self, request: RoutingRequest, candidates: List[Dict[str, Any]]) -> Optional[RoutingDecision]:
        """Priority-based routing strategy."""
        if not candidates:
            return None
        
        # Sort by score (highest first)
        sorted_candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)
        selected = sorted_candidates[0]
        
        confidence = 0.9  # Very high confidence for priority-based
        reasoning = [f"Priority-based selection", f"Score: {selected['score']:.2f}"]
        
        return self._create_decision_from_candidate(request, selected, RoutingStrategy.PRIORITY_BASED, confidence, reasoning)
    
    def _cost_optimized_strategy(self, request: RoutingRequest, candidates: List[Dict[str, Any]]) -> Optional[RoutingDecision]:
        """Cost-optimized routing strategy."""
        if not candidates:
            return None
        
        # Sort by cost (lowest first)
        cost_key = "cost_per_token" if candidates[0]["type"] == "session" else "cost_per_hour"
        sorted_candidates = sorted(candidates, key=lambda x: x.get(cost_key, float('inf')))
        selected = sorted_candidates[0]
        
        confidence = 0.8  # High confidence for cost-optimized
        reasoning = [f"Cost-optimized selection", f"Cost: {selected.get(cost_key, 'unknown')}"]
        
        return self._create_decision_from_candidate(request, selected, RoutingStrategy.COST_OPTIMIZED, confidence, reasoning)
    
    def _performance_optimized_strategy(self, request: RoutingRequest, candidates: List[Dict[str, Any]]) -> Optional[RoutingDecision]:
        """Performance-optimized routing strategy."""
        if not candidates:
            return None
        
        # Sort by performance (highest first)
        sorted_candidates = sorted(candidates, key=lambda x: x.get("performance", 0), reverse=True)
        selected = sorted_candidates[0]
        
        confidence = 0.85  # High confidence for performance-optimized
        reasoning = [f"Performance-optimized selection", f"Performance: {selected.get('performance', 'unknown')}"]
        
        return self._create_decision_from_candidate(request, selected, RoutingStrategy.PERFORMANCE_OPTIMIZED, confidence, reasoning)
    
    def _availability_first_strategy(self, request: RoutingRequest, candidates: List[Dict[str, Any]]) -> Optional[RoutingDecision]:
        """Availability-first routing strategy."""
        if not candidates:
            return None
        
        # Sort by wait time (lowest first)
        sorted_candidates = sorted(candidates, key=lambda x: x.get("estimated_wait_time", 0))
        selected = sorted_candidates[0]
        
        confidence = 0.9  # Very high confidence for availability-first
        reasoning = [f"Availability-first selection", f"Wait time: {selected.get('estimated_wait_time', 0)}s"]
        
        return self._create_decision_from_candidate(request, selected, RoutingStrategy.AVAILABILITY_FIRST, confidence, reasoning)
    
    def _create_decision_from_candidate(self, request: RoutingRequest, candidate: Dict[str, Any], strategy: RoutingStrategy, confidence: float, reasoning: List[str] = None) -> RoutingDecision:
        """Create routing decision from candidate."""
        if reasoning is None:
            reasoning = [f"Selected {candidate['resource_id']}"]
        
        # Calculate estimated cost
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
                "score": candidate.get("score", 0)
            }
        )
    
    def _validate_decision(self, decision: RoutingDecision) -> bool:
        """Validate routing decision."""
        # Check if resource is still available
        if decision.resource_type == ResourceType.LLM:
            session = self.session_manager.get_session_status(decision.selected_resource)
            if not session or session["status"] != "idle":
                return False
        elif decision.resource_type in [ResourceType.VSCODE, ResourceType.AI_TOOLS]:
            instance = self.instance_manager.get_instance_status(decision.selected_resource)
            if not instance or instance["status"] != "running":
                return False
        
        # Check rate limits
        if decision.resource_type == ResourceType.LLM:
            allowed, _ = self.rate_limiter.check_rate_limit(decision.provider, decision.account)
            if not allowed:
                return False
        
        return True
    
    def _create_no_resources_decision(self, request: RoutingRequest) -> RoutingDecision:
        """Create decision when no resources are available."""
        return RoutingDecision(
            request_id=request.request_id,
            resource_type=request.resource_type,
            selected_resource="",
            provider="",
            account="",
            model="",
            strategy_used=request.strategy or self.routing_config["default_strategy"],
            confidence=0.0,
            estimated_wait_time=float('inf'),
            estimated_cost=0.0,
            reasoning=["No available resources"],
            metadata={"error": "no_resources"}
        )
    
    def _create_routing_failed_decision(self, request: RoutingRequest) -> RoutingDecision:
        """Create decision when routing failed."""
        return RoutingDecision(
            request_id=request.request_id,
            resource_type=request.resource_type,
            selected_resource="",
            provider="",
            account="",
            model="",
            strategy_used=request.strategy or self.routing_config["default_strategy"],
            confidence=0.0,
            estimated_wait_time=float('inf'),
            estimated_cost=0.0,
            reasoning=["Routing failed"],
            metadata={"error": "routing_failed"}
        )
    
    def _create_validation_failed_decision(self, request: RoutingRequest) -> RoutingDecision:
        """Create decision when validation failed."""
        return RoutingDecision(
            request_id=request.request_id,
            resource_type=request.resource_type,
            selected_resource="",
            provider="",
            account="",
            model="",
            strategy_used=request.strategy or self.routing_config["default_strategy"],
            confidence=0.0,
            estimated_wait_time=float('inf'),
            estimated_cost=0.0,
            reasoning=["Validation failed"],
            metadata={"error": "validation_failed"}
        )
    
    def _calculate_llm_score(self, session: Dict[str, Any], request: RoutingRequest) -> float:
        """Calculate score for LLM session."""
        score = 0.0
        
        # Base score from utilization (lower utilization = higher score)
        utilization = session.get("utilization", 0)
        score += (100 - utilization) * 0.3
        
        # Provider preference
        provider_weight = self.routing_config["cost_weights"].get(session["provider"], 0.5)
        score += provider_weight * 20
        
        # Performance weight
        performance_weight = self.routing_config["performance_weights"].get(session["provider"], 0.5)
        score += performance_weight * 20
        
        # Wait time penalty
        wait_time = session.get("time_until_available", 0)
        score -= min(wait_time, 300) * 0.1  # Max 30 point penalty
        
        # Error penalty
        errors = session.get("errors_count", 0)
        score -= errors * 5
        
        return max(0, score)
    
    def _calculate_vscode_score(self, instance: Dict[str, Any], request: RoutingRequest) -> float:
        """Calculate score for VS Code instance."""
        score = 0.0
        
        # Base score from CPU utilization
        cpu_usage = instance.get("cpu_usage", 0)
        score += (100 - cpu_usage) * 0.4
        
        # Memory usage
        memory_usage = instance.get("memory_usage", 0)
        score += (100 - memory_usage) * 0.3
        
        # Health status
        health = instance.get("health_status", "unknown")
        if health == "healthy":
            score += 30
        elif health == "unknown":
            score += 10
        else:
            score -= 10
        
        # Error penalty
        errors = instance.get("error_count", 0)
        score -= errors * 5
        
        return max(0, score)
    
    def _calculate_ai_tools_score(self, instance: Dict[str, Any], request: RoutingRequest) -> float:
        """Calculate score for AI tools instance."""
        # Similar to VS Code scoring
        return self._calculate_vscode_score(instance, request)
    
    def _get_cost_per_token(self, provider: str, model: str) -> float:
        """Get cost per token for provider/model."""
        # Simplified cost model
        costs = {
            "anthropic": {"claude-3-sonnet": 0.015, "claude-3-haiku": 0.0025},
            "openai": {"gpt-4": 0.03, "gpt-3.5-turbo": 0.002},
            "google": {"gemini-pro": 0.0025},
            "openrouter": {"mixtral": 0.0015},
            "ollama": {"qwen2.5-coder:7b": 0.0}  # Free for local models
        }
        
        return costs.get(provider, {}).get(model, 0.01)
    
    def _get_vscode_cost_per_hour(self, provider: str) -> float:
        """Get cost per hour for VS Code instance."""
        # Simplified cost model
        costs = {
            "default": 0.05,
            "premium": 0.15,
            "enterprise": 0.50
        }
        
        return costs.get(provider, 0.05)
    
    def _get_ai_tools_cost_per_hour(self, provider: str) -> float:
        """Get cost per hour for AI tools instance."""
        # Similar to VS Code
        return self._get_vscode_cost_per_hour(provider)
    
    def _get_provider_performance(self, provider: str) -> float:
        """Get performance score for provider."""
        return self.routing_config["performance_weights"].get(provider, 0.5)
    
    def _update_routing_metrics(self, decision: Optional[RoutingDecision], routing_time: float, success: bool):
        """Update routing metrics."""
        with self.lock:
            if success:
                self.metrics.successful_requests += 1
            else:
                self.metrics.failed_requests += 1
            
            # Update average routing time
            total_requests = self.metrics.successful_requests + self.metrics.failed_requests
            self.metrics.average_routing_time = (
                (self.metrics.average_routing_time * (total_requests - 1) + routing_time) / total_requests
            )
            
            # Update strategy performance
            if decision:
                strategy = decision.strategy_used.value
                if strategy not in self.metrics.strategy_performance:
                    self.metrics.strategy_performance[strategy] = {"success": 0, "total": 0}
                
                self.metrics.strategy_performance[strategy]["total"] += 1
                if success:
                    self.metrics.strategy_performance[strategy]["success"] += 1
                
                # Update provider performance
                provider = decision.provider
                if provider not in self.metrics.provider_performance:
                    self.metrics.provider_performance[provider] = {"success": 0, "total": 0}
                
                self.metrics.provider_performance[provider]["total"] += 1
                if success:
                    self.metrics.provider_performance[provider]["success"] += 1
    
    def start_background_tasks(self):
        """Start background tasks for metrics and optimization."""
        # Metrics collection thread
        metrics_thread = threading.Thread(target=self._metrics_worker, daemon=True)
        metrics_thread.start()
        
        # Optimization thread
        optimization_thread = threading.Thread(target=self._optimization_worker, daemon=True)
        optimization_thread.start()
    
    def _metrics_worker(self):
        """Background worker for metrics collection."""
        while True:
            try:
                time.sleep(60)  # Every minute
                
                # Collect metrics from all managers
                self._collect_system_metrics()
                
                # Save configuration periodically
                if time.time() % 300 < 60:  # Every 5 minutes
                    self.save_config()
                
            except Exception as e:
                print(f"❌ Metrics worker error: {e}")
    
    def _optimization_worker(self):
        """Background worker for system optimization."""
        while True:
            try:
                time.sleep(300)  # Every 5 minutes
                
                # Optimize routing based on metrics
                self._optimize_routing()
                
            except Exception as e:
                print(f"❌ Optimization worker error: {e}")
    
    def _collect_system_metrics(self):
        """Collect system metrics from all managers."""
        # Update resource utilization
        for provider, account in [(s["provider"], s["account"]) for s in self.session_manager.list_sessions()]:
            key = f"{provider}:{account}"
            # This would be updated with actual utilization metrics
            self.metrics.resource_utilization[key] = 0.0
    
    def _optimize_routing(self):
        """Optimize routing based on collected metrics."""
        # Adjust strategy weights based on performance
        for strategy, performance in self.metrics.strategy_performance.items():
            if performance["total"] > 10:  # Only adjust with sufficient data
                success_rate = performance["success"] / performance["total"]
                
                # Boost successful strategies
                if success_rate > 0.9:
                    print(f"📈 Strategy {strategy} performing well ({success_rate:.1%})")
                elif success_rate < 0.7:
                    print(f"📉 Strategy {strategy} performing poorly ({success_rate:.1%})")
    
    def get_routing_status(self) -> Dict[str, Any]:
        """Get comprehensive routing status."""
        return {
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "success_rate": (self.metrics.successful_requests / self.metrics.total_requests * 100) if self.metrics.total_requests > 0 else 0,
            "average_routing_time": self.metrics.average_routing_time,
            "default_strategy": self.routing_config["default_strategy"],
            "strategy_performance": self.metrics.strategy_performance,
            "provider_performance": self.metrics.provider_performance,
            "resource_utilization": self.metrics.resource_utilization
        }
    
    def print_status_summary(self):
        """Print comprehensive status summary."""
        print("🧭 Routing Engine Status")
        print("=======================")
        
        # Overall metrics
        status = self.get_routing_status()
        
        print(f"📊 Total Requests: {status['total_requests']}")
        print(f"✅ Successful: {status['successful_requests']}")
        print(f"❌ Failed: {status['failed_requests']}")
        print(f"📈 Success Rate: {status['success_rate']:.1f}%")
        print(f"⏱️  Avg Routing Time: {status['average_routing_time']:.3f}s")
        print(f"🎯 Default Strategy: {status['default_strategy']}")
        
        # Strategy performance
        if status["strategy_performance"]:
            print(f"\n📊 Strategy Performance:")
            for strategy, perf in status["strategy_performance"].items():
                success_rate = perf["success"] / perf["total"] * 100 if perf["total"] > 0 else 0
                print(f"  • {strategy}: {success_rate:.1f}% ({perf['success']}/{perf['total']})")
        
        # Provider performance
        if status["provider_performance"]:
            print(f"\n🏢 Provider Performance:")
            for provider, perf in status["provider_performance"].items():
                success_rate = perf["success"] / perf["total"] * 100 if perf["total"] > 0 else 0
                print(f"  • {provider}: {success_rate:.1f}% ({perf['success']}/{perf['total']})")
        
        print()


# CLI interface
def main():
    """CLI interface for routing engine."""
    import argparse
    
    parser = argparse.ArgumentParser(description="llx Routing Engine")
    parser.add_argument("command", choices=[
        "route", "status", "metrics", "optimize", "cleanup"
    ])
    parser.add_argument("--request-id", help="Request ID")
    parser.add_argument("--resource-type", choices=["llm", "vscode", "ai_tools"], help="Resource type")
    parser.add_argument("--provider", help="Provider name")
    parser.add_argument("--account", help="Account name")
    parser.add_argument("--model", help="Model name")
    parser.add_argument("--strategy", choices=["round_robin", "least_loaded", "priority_based", "cost_optimized", "performance_optimized", "availability_first"], help="Routing strategy")
    parser.add_argument("--priority", choices=["urgent", "high", "normal", "low", "background"], help="Request priority")
    
    args = parser.parse_args()
    
    engine = RoutingEngine()
    
    try:
        if args.command == "route":
            if not args.request_id or not args.resource_type:
                print("❌ --request-id and --resource-type required for route")
                sys.exit(1)
            
            request = RoutingRequest(
                request_id=args.request_id,
                resource_type=ResourceType(args.resource_type),
                provider=args.provider,
                account=args.account,
                model=args.model,
                priority=RequestPriority(args.priority) if args.priority else RequestPriority.NORMAL,
                strategy=RoutingStrategy(args.strategy) if args.strategy else None
            )
            
            decision = engine.route_request(request)
            if decision:
                print(json.dumps({
                    "request_id": decision.request_id,
                    "selected_resource": decision.selected_resource,
                    "provider": decision.provider,
                    "account": decision.account,
                    "model": decision.model,
                    "strategy": decision.strategy_used.value,
                    "confidence": decision.confidence,
                    "estimated_wait_time": decision.estimated_wait_time,
                    "estimated_cost": decision.estimated_cost,
                    "reasoning": decision.reasoning
                }, indent=2))
            else:
                print("❌ Routing failed")
                sys.exit(1)
        
        elif args.command == "status":
            status = engine.get_routing_status()
            print(json.dumps(status, indent=2))
        
        elif args.command == "metrics":
            engine.print_status_summary()
        
        elif args.command == "optimize":
            engine._optimize_routing()
            print("✅ Optimization completed")
        
        elif args.command == "cleanup":
            engine.save_config()
            print("✅ Cleanup completed")
        
        sys.exit(0)
    
    finally:
        # Cleanup
        pass


if __name__ == "__main__":
    main()
