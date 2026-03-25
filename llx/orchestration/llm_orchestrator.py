"""
LLM Orchestrator for llx Orchestration
Manages multiple LLM providers and models with intelligent routing and load balancing.
"""

import os
import sys
import json
import time
import uuid
import threading
import subprocess
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import requests

from .session_manager import SessionManager, SessionType, SessionStatus
from .rate_limiter import RateLimiter, LimitType
from .routing_engine import RoutingEngine, ResourceType, RoutingRequest, RequestPriority


class LLMProviderType(Enum):
    """Types of LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    LOCAL = "local"
    CUSTOM = "custom"


class ModelCapability(Enum):
    """Model capabilities."""
    CODE_GENERATION = "code_generation"
    TEXT_GENERATION = "text_generation"
    REASONING = "reasoning"
    MATH = "math"
    MULTIMODAL = "multimodal"
    FUNCTION_CALLING = "function_calling"
    CHAT = "chat"
    COMPLETION = "completion"


@dataclass
class LLMModel:
    """LLM model configuration."""
    model_id: str
    provider: LLMProviderType
    name: str
    display_name: str
    capabilities: List[ModelCapability]
    context_window: int
    max_tokens: int
    cost_per_1k_input: float
    cost_per_1k_output: float
    average_latency_ms: float
    quality_score: float  # 0.0-1.0
    reliability_score: float  # 0.0-1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMProvider:
    """LLM provider configuration."""
    provider_id: str
    provider_type: LLMProviderType
    name: str
    api_base: Optional[str]
    auth_method: str  # "api_key", "oauth", "none"
    auth_config: Dict[str, Any] = field(default_factory=dict)
    models: Dict[str, LLMModel] = field(default_factory=dict)
    rate_limits: Dict[str, int] = field(default_factory=dict)
    retry_config: Dict[str, Any] = field(default_factory=dict)
    health_check_endpoint: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMRequest:
    """LLM request."""
    request_id: str
    provider: str
    model: str
    messages: List[Dict[str, Any]]
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stream: bool = False
    priority: RequestPriority = RequestPriority.NORMAL
    timeout_seconds: int = 30
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """LLM response."""
    request_id: str
    provider: str
    model: str
    content: str
    finish_reason: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    cost: float
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


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
            "performance_tracking": True
        }
        
        # State
        self.running = False
        self.lock = threading.RLock()
        
        # Load configuration
        self.load_config()
        
        # Start orchestrator
        self.start()
    
    def load_config(self) -> bool:
        """Load LLM orchestration configuration."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                # Load configuration
                self.config.update(data.get("config", {}))
                
                # Load providers
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
                        metadata=provider_data.get("metadata", {})
                    )
                    
                    # Load models
                    for model_data in provider_data.get("models", {}):
                        model = LLMModel(
                            model_id=model_data["model_id"],
                            provider=provider.provider_type,
                            name=model_data["name"],
                            display_name=model_data["display_name"],
                            capabilities=[ModelCapability(cap) for cap in model_data.get("capabilities", [])],
                            context_window=model_data.get("context_window", 4096),
                            max_tokens=model_data.get("max_tokens", 1000),
                            cost_per_1k_input=model_data.get("cost_per_1k_input", 0.0),
                            cost_per_1k_output=model_data.get("cost_per_1k_output", 0.0),
                            average_latency_ms=model_data.get("average_latency_ms", 1000.0),
                            quality_score=model_data.get("quality_score", 0.5),
                            reliability_score=model_data.get("reliability_score", 0.5),
                            metadata=model_data.get("metadata", {})
                        )
                        provider.models[model.model_id] = model
                        self.model_cache[model.model_id] = model
                    
                    self.providers[provider.provider_id] = provider
                
                print(f"✅ Loaded LLM orchestration config: {len(self.providers)} providers, {len(self.model_cache)} models")
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
            
            data = {
                "config": self.config,
                "providers": []
            }
            
            # Save providers
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
                    "models": {}
                }
                
                # Save models
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
                        "metadata": model.metadata
                    }
                
                data["providers"].append(provider_data)
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving LLM config: {e}")
            return False
    
    def _create_default_config(self):
        """Create default LLM configuration."""
        # Create Ollama provider
        ollama_provider = LLMProvider(
            provider_id="ollama-local",
            provider_type=LLMProviderType.OLLAMA,
            name="Local Ollama",
            api_base="http://localhost:11434",
            auth_method="none",
            rate_limits={
                "requests_per_hour": 1000,
                "tokens_per_hour": 1000000
            },
            health_check_endpoint="http://localhost:11434/api/tags"
        )
        
        # Add common Ollama models
        ollama_models = {
            "qwen2.5-coder:7b": LLMModel(
                model_id="qwen2.5-coder:7b",
                provider=LLMProviderType.OLLAMA,
                name="qwen2.5-coder:7b",
                display_name="Qwen2.5 Coder 7B",
                capabilities=[ModelCapability.CODE_GENERATION, ModelCapability.REASONING, ModelCapability.CHAT],
                context_window=32768,
                max_tokens=4096,
                cost_per_1k_input=0.0,
                cost_per_1k_output=0.0,
                average_latency_ms=2000.0,
                quality_score=0.8,
                reliability_score=0.9
            ),
            "phi3:3.8b": LLMModel(
                model_id="phi3:3.8b",
                provider=LLMProviderType.OLLAMA,
                name="phi3:3.8b",
                display_name="Phi3 3.8B",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.REASONING, ModelCapability.CHAT],
                context_window=4096,
                max_tokens=2048,
                cost_per_1k_input=0.0,
                cost_per_1k_output=0.0,
                average_latency_ms=1500.0,
                quality_score=0.7,
                reliability_score=0.8
            )
        }
        
        ollama_provider.models = ollama_models
        self.providers[ollama_provider.provider_id] = ollama_provider
        
        # Update model cache
        for model in ollama_models.values():
            self.model_cache[model.model_id] = model
        
        print("✅ Created default LLM configuration")
    
    def start(self):
        """Start the LLM orchestrator."""
        with self.lock:
            if self.running:
                return
            
            self.running = True
            
            # Start background tasks
            self._start_background_tasks()
            
            # Perform initial health checks
            self._perform_health_checks()
            
            print(f"✅ Started LLM orchestrator")
    
    def stop(self):
        """Stop the LLM orchestrator."""
        with self.lock:
            self.running = False
            
            # Cancel active requests
            for request_id in list(self.active_requests.keys()):
                self.cancel_request(request_id)
            
            print(f"✅ Stopped LLM orchestrator")
    
    def add_provider(self, provider: LLMProvider) -> bool:
        """Add a new LLM provider."""
        with self.lock:
            if provider.provider_id in self.providers:
                print(f"⚠️  Provider {provider.provider_id} already exists")
                return False
            
            self.providers[provider.provider_id] = provider
            
            # Update model cache
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
            
            # Remove from model cache
            for model_id in provider.models.keys():
                if model_id in self.model_cache:
                    del self.model_cache[model_id]
            
            # Remove provider
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
    
    def complete_request(self, request: LLMRequest) -> Optional[LLMResponse]:
        """Complete an LLM request with intelligent routing."""
        start_time = time.time()
        
        try:
            with self.lock:
                self.active_requests[request.request_id] = request
            
            # Route request to best provider/model
            routing_decision = self._route_request(request)
            
            if not routing_decision:
                return self._create_failed_response(request, "No suitable provider/model found")
            
            # Check rate limits
            allowed, reason = self.rate_limiter.check_rate_limit(
                routing_decision.provider,
                "default",  # Could be enhanced with account support
                LimitType.REQUESTS_PER_HOUR
            )
            
            if not allowed:
                return self._create_failed_response(request, f"Rate limited: {reason}")
            
            # Execute request
            response = self._execute_request(request, routing_decision)
            
            # Record request in rate limiter
            self.rate_limiter.record_request(
                routing_decision.provider,
                "default",
                LimitType.REQUESTS_PER_HOUR,
                response.total_tokens,
                response.success
            )
            
            # Add to history
            self._add_to_history(response)
            
            return response
            
        except Exception as e:
            print(f"❌ Error completing request {request.request_id}: {e}")
            return self._create_failed_response(request, str(e))
        finally:
            with self.lock:
                if request.request_id in self.active_requests:
                    del self.active_requests[request.request_id]
    
    def _route_request(self, request: LLMRequest) -> Optional[Dict[str, Any]]:
        """Route request to best provider/model."""
        # Create routing request
        routing_request = RoutingRequest(
            request_id=request.request_id,
            resource_type=ResourceType.LLM,
            provider=request.provider,
            account="default",
            model=request.model,
            priority=request.priority,
            strategy=RoutingStrategy.AVAILABILITY_FIRST,
            requirements={
                "estimated_tokens": request.max_tokens,
                "capabilities": self._get_required_capabilities(request)
            },
            constraints={
                "max_cost": 0.1,  # Could be configurable
                "max_wait_time": request.timeout_seconds
            }
        )
        
        # Get routing decision
        decision = self.routing_engine.route_request(routing_request)
        
        if not decision:
            return None
        
        return {
            "provider": decision.provider,
            "model": decision.model,
            "resource_id": decision.selected_resource,
            "confidence": decision.confidence,
            "estimated_wait_time": decision.estimated_wait_time,
            "estimated_cost": decision.estimated_cost
        }
    
    def _execute_request(self, request: LLMRequest, routing_decision: Dict[str, Any]) -> LLMResponse:
        """Execute LLM request."""
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
            # Execute based on provider type
            if provider.provider_type == LLMProviderType.OLLAMA:
                response = self._execute_ollama_request(request, provider, model)
            elif provider.provider_type == LLMProviderType.OPENAI:
                response = self._execute_openai_request(request, provider, model)
            elif provider.provider_type == LLMProviderType.ANTHROPIC:
                response = self._execute_anthropic_request(request, provider, model)
            else:
                response = self._execute_generic_request(request, provider, model)
            
            # Calculate latency
            response.latency_ms = (time.time() - start_time) * 1000
            
            return response
            
        except Exception as e:
            return self._create_failed_response(request, str(e))
    
    def _execute_ollama_request(self, request: LLMRequest, provider: LLMProvider, model: LLMModel) -> LLMResponse:
        """Execute Ollama request."""
        api_base = provider.api_base or "http://localhost:11434"
        url = f"{api_base}/api/generate"
        
        payload = {
            "model": model.name,
            "prompt": self._messages_to_prompt(request.messages),
            "stream": request.stream,
            "options": {
                "temperature": request.temperature,
                "top_p": request.top_p,
                "num_predict": request.max_tokens
            }
        }
        
        response = requests.post(url, json=payload, timeout=request.timeout_seconds)
        
        if response.status_code != 200:
            return self._create_failed_response(request, f"HTTP {response.status_code}: {response.text}")
        
        data = response.json()
        
        # Calculate tokens (approximate)
        prompt_tokens = len(payload["prompt"].split()) * 1.3  # Rough estimate
        completion_tokens = len(data.get("response", "").split()) * 1.3
        total_tokens = int(prompt_tokens + completion_tokens)
        
        # Calculate cost
        cost = (prompt_tokens / 1000 * model.cost_per_1k_input) + (completion_tokens / 1000 * model.cost_per_1k_output)
        
        return LLMResponse(
            request_id=request.request_id,
            provider=provider.provider_id,
            model=model.model_id,
            content=data.get("response", ""),
            finish_reason=data.get("done_reason", "stop"),
            prompt_tokens=int(prompt_tokens),
            completion_tokens=int(completion_tokens),
            total_tokens=total_tokens,
            latency_ms=0,  # Will be set by caller
            cost=cost,
            success=True
        )
    
    def _execute_openai_request(self, request: LLMRequest, provider: LLMProvider, model: LLMModel) -> LLMResponse:
        """Execute OpenAI request."""
        api_base = provider.api_base or "https://api.openai.com/v1"
        url = f"{api_base}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {provider.auth_config.get('api_key')}"
        }
        
        payload = {
            "model": model.name,
            "messages": request.messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "frequency_penalty": request.frequency_penalty,
            "presence_penalty": request.presence_penalty,
            "stream": request.stream
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=request.timeout_seconds)
        
        if response.status_code != 200:
            return self._create_failed_response(request, f"HTTP {response.status_code}: {response.text}")
        
        data = response.json()
        
        choice = data["choices"][0]
        usage = data.get("usage", {})
        
        # Calculate cost
        cost = (usage.get("prompt_tokens", 0) / 1000 * model.cost_per_1k_input) + \
               (usage.get("completion_tokens", 0) / 1000 * model.cost_per_1k_output)
        
        return LLMResponse(
            request_id=request.request_id,
            provider=provider.provider_id,
            model=model.model_id,
            content=choice.get("message", {}).get("content", ""),
            finish_reason=choice.get("finish_reason", "stop"),
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            latency_ms=0,  # Will be set by caller
            cost=cost,
            success=True
        )
    
    def _execute_anthropic_request(self, request: LLMRequest, provider: LLMProvider, model: LLMModel) -> LLMResponse:
        """Execute Anthropic request."""
        api_base = provider.api_base or "https://api.anthropic.com/v1"
        url = f"{api_base}/messages"
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": provider.auth_config.get('api_key'),
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": model.name,
            "messages": request.messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=request.timeout_seconds)
        
        if response.status_code != 200:
            return self._create_failed_response(request, f"HTTP {response.status_code}: {response.text}")
        
        data = response.json()
        
        usage = data.get("usage", {})
        
        # Calculate cost
        cost = (usage.get("input_tokens", 0) / 1000 * model.cost_per_1k_input) + \
               (usage.get("output_tokens", 0) / 1000 * model.cost_per_1k_output)
        
        return LLMResponse(
            request_id=request.request_id,
            provider=provider.provider_id,
            model=model.model_id,
            content=data.get("content", [{}])[0].get("text", ""),
            finish_reason=data.get("stop_reason", "stop"),
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            latency_ms=0,  # Will be set by caller
            cost=cost,
            success=True
        )
    
    def _execute_generic_request(self, request: LLMRequest, provider: LLMProvider, model: LLMModel) -> LLMResponse:
        """Execute generic request (fallback)."""
        # This would implement a generic OpenAI-compatible API
        return self._execute_openai_request(request, provider, model)
    
    def _messages_to_prompt(self, messages: List[Dict[str, Any]]) -> str:
        """Convert messages to prompt for non-chat models."""
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts)
    
    def _get_required_capabilities(self, request: LLMRequest) -> List[str]:
        """Get required capabilities for request."""
        capabilities = []
        
        # Check if request requires code generation
        content = " ".join([msg.get("content", "") for msg in request.messages])
        if any(keyword in content.lower() for keyword in ["code", "function", "class", "algorithm"]):
            capabilities.append("code_generation")
        
        # Check if request requires reasoning
        if any(keyword in content.lower() for keyword in ["why", "how", "explain", "reason"]):
            capabilities.append("reasoning")
        
        # Default to chat capability
        capabilities.append("chat")
        
        return capabilities
    
    def _create_failed_response(self, request: LLMRequest, error: str) -> LLMResponse:
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
            error=error
        )
    
    def _add_to_history(self, response: LLMResponse):
        """Add response to history."""
        with self.lock:
            self.request_history.append(response)
            
            # Trim history if needed
            if len(self.request_history) > self.config["request_history_size"]:
                self.request_history = self.request_history[-self.config["request_history_size"]:]
    
    def cancel_request(self, request_id: str) -> bool:
        """Cancel an active request."""
        with self.lock:
            if request_id not in self.active_requests:
                return False
            
            # Remove from active requests
            del self.active_requests[request_id]
            
            print(f"✅ Cancelled request {request_id}")
            return True
    
    def get_provider_status(self, provider_id: str = None) -> Dict[str, Any]:
        """Get status of LLM providers."""
        with self.lock:
            if provider_id:
                if provider_id not in self.providers:
                    return {}
                
                provider = self.providers[provider_id]
                return self._get_single_provider_status(provider)
            else:
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
            "reliability_score": model.reliability_score
        }
    
    def list_models(self, provider_id: str = None, capability: ModelCapability = None) -> List[Dict[str, Any]]:
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
            total_requests = len(self.request_history)
            successful_requests = len([r for r in self.request_history if r.success])
            failed_requests = total_requests - successful_requests
            
            total_cost = sum(r.cost for r in self.request_history)
            total_tokens = sum(r.total_tokens for r in self.request_history)
            
            # Provider breakdown
            provider_stats = {}
            for response in self.request_history:
                if response.provider not in provider_stats:
                    provider_stats[response.provider] = {
                        "requests": 0,
                        "successful": 0,
                        "cost": 0.0,
                        "tokens": 0
                    }
                
                stats = provider_stats[response.provider]
                stats["requests"] += 1
                if response.success:
                    stats["successful"] += 1
                stats["cost"] += response.cost
                stats["tokens"] += response.total_tokens
            
            # Model breakdown
            model_stats = {}
            for response in self.request_history:
                if response.model not in model_stats:
                    model_stats[response.model] = {
                        "requests": 0,
                        "successful": 0,
                        "average_latency": 0.0
                    }
                
                stats = model_stats[response.model]
                stats["requests"] += 1
                if response.success:
                    stats["successful"] += 1
                
                # Update average latency
                if stats["requests"] > 0:
                    stats["average_latency"] = (
                        (stats["average_latency"] * (stats["requests"] - 1) + response.latency_ms) /
                        stats["requests"]
                    )
            
            return {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "provider_stats": provider_stats,
                "model_stats": model_stats
            }
    
    def _get_single_provider_status(self, provider: LLMProvider) -> Dict[str, Any]:
        """Get status of a single provider."""
        # Perform health check
        health_status = "unknown"
        last_check = None
        
        if provider.health_check_endpoint:
            try:
                response = requests.get(provider.health_check_endpoint, timeout=5)
                health_status = "healthy" if response.status_code == 200 else "unhealthy"
                last_check = datetime.now().isoformat()
            except:
                health_status = "error"
                last_check = datetime.now().isoformat()
        
        # Calculate usage stats
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
            "success_rate": (successful_requests / len(provider_requests) * 100) if provider_requests else 0,
            "rate_limits": provider.rate_limits
        }
    
    def _get_all_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers."""
        status = {
            "total_providers": len(self.providers),
            "healthy_providers": 0,
            "unhealthy_providers": 0,
            "providers": {}
        }
        
        for provider in self.providers.values():
            provider_status = self._get_single_provider_status(provider)
            status["providers"][provider.provider_id] = provider_status
            
            if provider_status["health_status"] == "healthy":
                status["healthy_providers"] += 1
            elif provider_status["health_status"] in ["unhealthy", "error"]:
                status["unhealthy_providers"] += 1
        
        return status
    
    def _start_background_tasks(self):
        """Start background tasks."""
        # Health check thread
        health_thread = threading.Thread(target=self._health_check_worker, daemon=True)
        health_thread.start()
        
        # Config save thread
        save_thread = threading.Thread(target=self._config_save_worker, daemon=True)
        save_thread.start()
    
    def _health_check_worker(self):
        """Background worker for health checks."""
        while self.running:
            try:
                time.sleep(self.config["health_check_interval"])
                self._perform_health_checks()
            except Exception as e:
                print(f"❌ Health check worker error: {e}")
    
    def _config_save_worker(self):
        """Background worker for configuration saving."""
        while self.running:
            try:
                time.sleep(300)  # Every 5 minutes
                self.save_config()
            except Exception as e:
                print(f"❌ Config save worker error: {e}")
    
    def _perform_health_checks(self):
        """Perform health checks on all providers."""
        for provider in self.providers.values():
            if provider.health_check_endpoint:
                try:
                    response = requests.get(provider.health_check_endpoint, timeout=5)
                    if response.status_code != 200:
                        print(f"⚠️  Provider {provider.provider_id} health check failed: HTTP {response.status_code}")
                except Exception as e:
                    print(f"⚠️  Provider {provider.provider_id} health check error: {e}")
    
    def print_status_summary(self):
        """Print comprehensive status summary."""
        print("🤖 LLM Orchestrator Status")
        print("==========================")
        
        # Overall stats
        usage_stats = self.get_usage_stats()
        provider_status = self.get_provider_status()
        
        print(f"📊 Total Requests: {usage_stats['total_requests']}")
        print(f"✅ Successful: {usage_stats['successful_requests']}")
        print(f"❌ Failed: {usage_stats['failed_requests']}")
        print(f"📈 Success Rate: {usage_stats['success_rate']:.1f}%")
        print(f"💰 Total Cost: ${usage_stats['total_cost']:.4f}")
        print(f"🔤 Total Tokens: {usage_stats['total_tokens']}")
        
        # Provider breakdown
        print(f"\n🏢 Providers ({provider_status['total_providers']}):")
        print(f"  🟢 Healthy: {provider_status['healthy_providers']}")
        print(f"  🔴 Unhealthy: {provider_status['unhealthy_providers']}")
        
        for provider_id, status in provider_status["providers"].items():
            print(f"  • {provider_id}: {status['health_status']} ({status['success_rate']:.1f}% success, {status['models_count']} models)")
        
        # Model breakdown
        print(f"\n🤖 Models ({len(self.model_cache)}):")
        capability_counts = {}
        for model in self.model_cache.values():
            for capability in model.capabilities:
                capability_counts[capability.value] = capability_counts.get(capability.value, 0) + 1
        
        for capability, count in capability_counts.items():
            print(f"  • {capability}: {count} models")
        
        print()


# CLI interface
def main():
    """CLI interface for LLM orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="llx LLM Orchestrator")
    parser.add_argument("command", choices=[
        "add-provider", "remove-provider", "list-providers",
        "add-model", "list-models", "model-info",
        "complete", "cancel", "status", "usage", "cleanup"
    ])
    parser.add_argument("--provider-id", help="Provider ID")
    parser.add_argument("--model-id", help="Model ID")
    parser.add_argument("--request-id", help="Request ID")
    parser.add_argument("--type", choices=["openai", "anthropic", "google", "openrouter", "ollama", "local", "custom"], help="Provider type")
    parser.add_argument("--name", help="Provider name")
    api_base = parser.add_argument("--api-base", help="API base URL")
    parser.add_argument("--capability", choices=["code_generation", "text_generation", "reasoning", "math", "multimodal", "function_calling", "chat", "completion"], help="Model capability")
    
    args = parser.parse_args()
    
    orchestrator = LLMOrchestrator()
    
    try:
        if args.command == "add-provider":
            if not args.provider_id or not args.type or not args.name:
                print("❌ --provider-id, --type, and --name required for add-provider")
                sys.exit(1)
            
            provider = LLMProvider(
                provider_id=args.provider_id,
                provider_type=LLMProviderType(args.type),
                name=args.name,
                api_base=getattr(args, 'api_base', None),
                auth_method="api_key"
            )
            
            success = orchestrator.add_provider(provider)
            if success:
                orchestrator.save_config()
        
        elif args.command == "remove-provider":
            if not args.provider_id:
                print("❌ --provider-id required for remove-provider")
                sys.exit(1)
            
            success = orchestrator.remove_provider(args.provider_id)
            if success:
                orchestrator.save_config()
        
        elif args.command == "list-providers":
            status = orchestrator.get_provider_status()
            for provider_id, provider_status in status["providers"].items():
                print(f"  • {provider_id}: {provider_status['health_status']} ({provider_status['models_count']} models)")
        
        elif args.command == "list-models":
            capability = ModelCapability(args.capability) if args.capability else None
            models = orchestrator.list_models(args.provider_id, capability)
            
            for model in models:
                print(f"  • {model['model_id']}: {model['display_name']} ({model['provider']})")
        
        elif args.command == "model-info":
            if not args.model_id:
                print("❌ --model-id required for model-info")
                sys.exit(1)
            
            model_info = orchestrator.get_model_info(args.model_id)
            if model_info:
                print(json.dumps(model_info, indent=2))
            else:
                print(f"❌ Model {args.model_id} not found")
                sys.exit(1)
        
        elif args.command == "complete":
            # This would require a more complex CLI interface for creating requests
            print("❌ Complete command requires request data (not implemented in CLI)")
        
        elif args.command == "cancel":
            if not args.request_id:
                print("❌ --request-id required for cancel")
                sys.exit(1)
            
            success = orchestrator.cancel_request(args.request_id)
        
        elif args.command == "status":
            orchestrator.print_status_summary()
        
        elif args.command == "usage":
            stats = orchestrator.get_usage_stats()
            print(json.dumps(stats, indent=2))
        
        elif args.command == "cleanup":
            orchestrator.save_config()
            print("✅ Cleanup completed")
        
        sys.exit(0 if success else 1)
    
    finally:
        orchestrator.stop()


if __name__ == "__main__":
    main()
