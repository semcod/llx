"""
Rate Limiter for llx Orchestration
Manages rate limiting and cooldown periods for LLM providers and accounts.
"""

import os
import sys
import json
import time
import threading
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class LimitType(Enum):
    """Types of rate limits."""
    REQUESTS_PER_HOUR = "requests_per_hour"
    TOKENS_PER_HOUR = "tokens_per_hour"
    REQUESTS_PER_MINUTE = "requests_per_minute"
    CONCURRENT_REQUESTS = "concurrent_requests"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    provider: str
    account: str
    limits: Dict[LimitType, int] = field(default_factory=dict)
    cooldown_minutes: int = 60
    penalty_multiplier: float = 1.5
    max_penalties: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RateLimitState:
    """Current state of rate limiting."""
    provider: str
    account: str
    current_usage: Dict[LimitType, int] = field(default_factory=dict)
    last_reset_times: Dict[LimitType, datetime] = field(default_factory=dict)
    cooldown_until: Optional[datetime] = None
    penalty_count: int = 0
    last_request_time: Optional[datetime] = None
    concurrent_requests: int = 0
    total_requests: int = 0
    rejected_requests: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class RateLimiter:
    """Manages rate limiting for multiple providers and accounts."""
    
    def __init__(self, config_file: str = None):
        self.project_root = Path.cwd()
        self.config_file = config_file or self.project_root / "orchestration" / "rate_limits.json"
        self.limits: Dict[str, RateLimitConfig] = {}
        self.states: Dict[str, RateLimitState] = {}
        self.lock = threading.RLock()
        
        # Default limits for common providers
        self.default_limits = {
            "anthropic": {
                "requests_per_hour": 50,
                "tokens_per_hour": 100000,
                "requests_per_minute": 5,
                "concurrent_requests": 3
            },
            "openai": {
                "requests_per_hour": 100,
                "tokens_per_hour": 200000,
                "requests_per_minute": 10,
                "concurrent_requests": 5
            },
            "google": {
                "requests_per_hour": 60,
                "tokens_per_hour": 150000,
                "requests_per_minute": 8,
                "concurrent_requests": 4
            },
            "openrouter": {
                "requests_per_hour": 200,
                "tokens_per_hour": 500000,
                "requests_per_minute": 20,
                "concurrent_requests": 10
            },
            "ollama": {
                "requests_per_hour": 1000,
                "tokens_per_hour": 1000000,
                "requests_per_minute": 60,
                "concurrent_requests": 20
            }
        }
        
        # Load existing configuration
        self.load_limits()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()
    
    def load_limits(self) -> bool:
        """Load rate limits from configuration file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                # Load rate limit configurations
                for limit_data in data.get("limits", []):
                    config = RateLimitConfig(
                        provider=limit_data["provider"],
                        account=limit_data["account"],
                        limits={
                            LimitType(k): v for k, v in limit_data.get("limits", {}).items()
                        },
                        cooldown_minutes=limit_data.get("cooldown_minutes", 60),
                        penalty_multiplier=limit_data.get("penalty_multiplier", 1.5),
                        max_penalties=limit_data.get("max_penalties", 3),
                        metadata=limit_data.get("metadata", {})
                    )
                    key = f"{config.provider}:{config.account}"
                    self.limits[key] = config
                    
                    # Load or create state
                    state_data = data.get("states", {}).get(key, {})
                    state = RateLimitState(
                        provider=config.provider,
                        account=config.account,
                        current_usage={
                            LimitType(k): v for k, v in state_data.get("current_usage", {}).items()
                        },
                        last_reset_times={
                            LimitType(k): datetime.fromisoformat(v) for k, v in state_data.get("last_reset_times", {}).items()
                        },
                        cooldown_until=datetime.fromisoformat(state_data["cooldown_until"]) if state_data.get("cooldown_until") else None,
                        penalty_count=state_data.get("penalty_count", 0),
                        last_request_time=datetime.fromisoformat(state_data["last_request_time"]) if state_data.get("last_request_time") else None,
                        concurrent_requests=state_data.get("concurrent_requests", 0),
                        total_requests=state_data.get("total_requests", 0),
                        rejected_requests=state_data.get("rejected_requests", 0),
                        metadata=state_data.get("metadata", {})
                    )
                    self.states[key] = state
                
                print(f"✅ Loaded rate limits for {len(self.limits)} provider-account combinations")
                return True
            else:
                print("📝 No existing rate limits found, starting with defaults")
                self._create_default_limits()
                return True
                
        except Exception as e:
            print(f"❌ Error loading rate limits: {e}")
            return False
    
    def save_limits(self) -> bool:
        """Save rate limits to configuration file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "limits": [],
                "states": {}
            }
            
            # Save rate limit configurations
            for config in self.limits.values():
                data["limits"].append({
                    "provider": config.provider,
                    "account": config.account,
                    "limits": {k.value: v for k, v in config.limits.items()},
                    "cooldown_minutes": config.cooldown_minutes,
                    "penalty_multiplier": config.penalty_multiplier,
                    "max_penalties": config.max_penalties,
                    "metadata": config.metadata
                })
            
            # Save states
            for state in self.states.values():
                key = f"{state.provider}:{state.account}"
                data["states"][key] = {
                    "current_usage": {k.value: v for k, v in state.current_usage.items()},
                    "last_reset_times": {k.value: v.isoformat() for k, v in state.last_reset_times.items()},
                    "cooldown_until": state.cooldown_until.isoformat() if state.cooldown_until else None,
                    "penalty_count": state.penalty_count,
                    "last_request_time": state.last_request_time.isoformat() if state.last_request_time else None,
                    "concurrent_requests": state.concurrent_requests,
                    "total_requests": state.total_requests,
                    "rejected_requests": state.rejected_requests,
                    "metadata": state.metadata
                }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving rate limits: {e}")
            return False
    
    def _create_default_limits(self):
        """Create default rate limits for common providers."""
        for provider, limits in self.default_limits.items():
            config = RateLimitConfig(
                provider=provider,
                account="default",
                limits={LimitType(k): v for k, v in limits.items()}
            )
            key = f"{config.provider}:{config.account}"
            self.limits[key] = config
            
            # Create initial state
            self.states[key] = RateLimitState(
                provider=provider,
                account="default"
            )
    
    def add_limit(self, config: RateLimitConfig) -> bool:
        """Add or update a rate limit configuration."""
        with self.lock:
            key = f"{config.provider}:{config.account}"
            self.limits[key] = config
            
            # Create state if not exists
            if key not in self.states:
                self.states[key] = RateLimitState(
                    provider=config.provider,
                    account=config.account
                )
            
            print(f"✅ Added rate limit for {config.provider}:{config.account}")
            return True
    
    def remove_limit(self, provider: str, account: str) -> bool:
        """Remove a rate limit configuration."""
        with self.lock:
            key = f"{provider}:{account}"
            
            if key not in self.limits:
                print(f"❌ Rate limit not found for {provider}:{account}")
                return False
            
            del self.limits[key]
            del self.states[key]
            
            print(f"✅ Removed rate limit for {provider}:{account}")
            return True
    
    def check_rate_limit(self, provider: str, account: str, request_type: LimitType = LimitType.REQUESTS_PER_HOUR, tokens: int = 0) -> Tuple[bool, Optional[str]]:
        """Check if a request is allowed under rate limits."""
        with self.lock:
            key = f"{provider}:{account}"
            
            if key not in self.limits:
                # Use default limits if not configured
                if provider in self.default_limits:
                    config = RateLimitConfig(
                        provider=provider,
                        account=account,
                        limits={LimitType(k): v for k, v in self.default_limits[provider].items()}
                    )
                    self.limits[key] = config
                    self.states[key] = RateLimitState(provider=provider, account=account)
                else:
                    return False, f"No rate limit configuration for {provider}:{account}"
            
            config = self.limits[key]
            state = self.states[key]
            now = datetime.now()
            
            # Check cooldown
            if state.cooldown_until and state.cooldown_until > now:
                remaining_time = (state.cooldown_until - now).total_seconds()
                return False, f"Rate limited (cooldown). Available in {remaining_time:.0f} seconds"
            
            # Check concurrent request limit
            if request_type == LimitType.CONCURRENT_REQUESTS:
                if state.concurrent_requests >= config.limits.get(LimitType.CONCURRENT_REQUESTS, 1):
                    return False, "Concurrent request limit exceeded"
                return True, None
            
            # Reset counters if needed
            self._reset_counters_if_needed(key, now)
            
            # Check specific limit
            if request_type in config.limits:
                limit = config.limits[request_type]
                usage = state.current_usage.get(request_type, 0)
                
                if request_type == LimitType.TOKENS_PER_HOUR:
                    usage += tokens
                
                if usage >= limit:
                    # Apply penalty
                    self._apply_penalty(key)
                    return False, f"{request_type.value} limit exceeded ({limit})"
            
            return True, None
    
    def record_request(self, provider: str, account: str, request_type: LimitType = LimitType.REQUESTS_PER_HOUR, tokens: int = 0, success: bool = True) -> bool:
        """Record a request for rate limiting."""
        with self.lock:
            key = f"{provider}:{account}"
            
            if key not in self.states:
                return False
            
            state = self.states[key]
            now = datetime.now()
            
            # Update counters
            if request_type == LimitType.CONCURRENT_REQUESTS:
                if success:
                    state.concurrent_requests += 1
            else:
                state.current_usage[request_type] = state.current_usage.get(request_type, 0) + 1
                
                if request_type == LimitType.TOKENS_PER_HOUR:
                    state.current_usage[request_type] += tokens - 1  # tokens already added in check_rate_limit
            
            state.last_request_time = now
            state.total_requests += 1
            
            if not success:
                state.rejected_requests += 1
            
            return True
    
    def release_request(self, provider: str, account: str) -> bool:
        """Release a concurrent request."""
        with self.lock:
            key = f"{provider}:{account}"
            
            if key not in self.states:
                return False
            
            state = self.states[key]
            if state.concurrent_requests > 0:
                state.concurrent_requests -= 1
            
            return True
    
    def get_status(self, provider: str = None, account: str = None) -> Dict[str, Any]:
        """Get rate limiting status."""
        with self.lock:
            now = datetime.now()
            results = {}
            
            for key, config in self.limits.items():
                p, a = key.split(":", 1)
                
                if provider and p != provider:
                    continue
                
                if account and a != account:
                    continue
                
                state = self.states[key]
                
                # Calculate utilization
                utilization = {}
                for limit_type, limit in config.limits.items():
                    usage = state.current_usage.get(limit_type, 0)
                    utilization[limit_type.value] = {
                        "used": usage,
                        "limit": limit,
                        "percentage": (usage / limit * 100) if limit > 0 else 0,
                        "remaining": max(0, limit - usage)
                    }
                
                # Calculate time until reset
                next_reset_times = {}
                for limit_type in config.limits.keys():
                    if limit_type in state.last_reset_times:
                        next_reset = state.last_reset_times[limit_type] + timedelta(hours=1)
                        if next_reset > now:
                            next_reset_times[limit_type.value] = (next_reset - now).total_seconds()
                        else:
                            next_reset_times[limit_type.value] = 0
                
                results[key] = {
                    "provider": p,
                    "account": a,
                    "status": "rate_limited" if (state.cooldown_until and state.cooldown_until > now) else "available",
                    "cooldown_until": state.cooldown_until.isoformat() if state.cooldown_until else None,
                    "penalty_count": state.penalty_count,
                    "concurrent_requests": state.concurrent_requests,
                    "total_requests": state.total_requests,
                    "rejected_requests": state.rejected_requests,
                    "utilization": utilization,
                    "next_reset_times": next_reset_times,
                    "last_request_time": state.last_request_time.isoformat() if state.last_request_time else None
                }
            
            return results
    
    def get_available_providers(self, request_type: LimitType = LimitType.REQUESTS_PER_HOUR) -> List[Dict[str, Any]]:
        """Get list of available providers sorted by availability."""
        with self.lock:
            available = []
            
            for key, config in self.limits.items():
                provider, account = key.split(":", 1)
                state = self.states[key]
                
                # Check if provider is available
                allowed, reason = self.check_rate_limit(provider, account, request_type)
                
                if allowed:
                    # Calculate score for sorting
                    score = 0
                    
                    # Lower utilization = higher score
                    if request_type in config.limits:
                        limit = config.limits[request_type]
                        usage = state.current_usage.get(request_type, 0)
                        utilization = (usage / limit) if limit > 0 else 0
                        score = 100 - (utilization * 100)
                    
                    # Lower penalty count = higher score
                    score -= (state.penalty_count * 10)
                    
                    available.append({
                        "provider": provider,
                        "account": account,
                        "score": score,
                        "utilization": utilization if request_type in config.limits else 0,
                        "penalty_count": state.penalty_count,
                        "concurrent_requests": state.concurrent_requests
                    })
            
            # Sort by score (highest first)
            available.sort(key=lambda x: x["score"], reverse=True)
            
            return available
    
    def _reset_counters_if_needed(self, key: str, now: datetime):
        """Reset counters if time period has passed."""
        state = self.states[key]
        config = self.limits[key]
        
        for limit_type in config.limits.keys():
            if limit_type in [LimitType.REQUESTS_PER_HOUR, LimitType.TOKENS_PER_HOUR]:
                if limit_type not in state.last_reset_times:
                    state.last_reset_times[limit_type] = now
                    state.current_usage[limit_type] = 0
                else:
                    last_reset = state.last_reset_times[limit_type]
                    if now - last_reset >= timedelta(hours=1):
                        state.last_reset_times[limit_type] = now
                        state.current_usage[limit_type] = 0
            
            elif limit_type == LimitType.REQUESTS_PER_MINUTE:
                if limit_type not in state.last_reset_times:
                    state.last_reset_times[limit_type] = now
                    state.current_usage[limit_type] = 0
                else:
                    last_reset = state.last_reset_times[limit_type]
                    if now - last_reset >= timedelta(minutes=1):
                        state.last_reset_times[limit_type] = now
                        state.current_usage[limit_type] = 0
    
    def _apply_penalty(self, key: str):
        """Apply penalty for rate limit violation."""
        state = self.states[key]
        config = self.limits[key]
        
        state.penalty_count += 1
        
        # Apply cooldown
        cooldown_minutes = int(config.cooldown_minutes * (config.penalty_multiplier ** state.penalty_count))
        state.cooldown_until = datetime.now() + timedelta(minutes=cooldown_minutes)
        
        # Reset some usage
        for limit_type in config.limits.keys():
            if limit_type in [LimitType.REQUESTS_PER_HOUR, LimitType.TOKENS_PER_HOUR]:
                state.current_usage[limit_type] = int(state.current_usage.get(limit_type, 0) * 0.8)  # Reduce by 20%
        
        print(f"⚠️  Applied penalty to {key}: {cooldown_minutes} minutes cooldown")
    
    def _cleanup_worker(self):
        """Background worker for cleanup tasks."""
        while True:
            try:
                time.sleep(60)  # Run every minute
                self._cleanup_expired_penalties()
                self._save_state_if_needed()
                
            except Exception as e:
                print(f"❌ Rate limiter cleanup error: {e}")
    
    def _cleanup_expired_penalties(self):
        """Clean up expired penalties."""
        with self.lock:
            now = datetime.now()
            
            for state in self.states.values():
                if state.cooldown_until and state.cooldown_until <= now:
                    state.cooldown_until = None
                    state.penalty_count = 0
                    print(f"✅ Penalty expired for {state.provider}:{state.account}")
    
    def _save_state_if_needed(self):
        """Save state if needed."""
        # Save every 5 minutes
        if time.time() % 300 < 60:
            self.save_limits()
    
    def print_status_summary(self):
        """Print comprehensive status summary."""
        print("⏱️  Rate Limiter Status")
        print("=====================")
        
        # Overall stats
        total_configs = len(self.limits)
        rate_limited = sum(1 for state in self.states.values() if state.cooldown_until and state.cooldown_until > datetime.now())
        
        print(f"📊 Total Configurations: {total_configs}")
        print(f"⏰ Rate Limited: {rate_limited}")
        print(f"📈 Total Requests: {sum(state.total_requests for state in self.states.values())}")
        print(f"❌ Rejected Requests: {sum(state.rejected_requests for state in self.states.values())}")
        
        # Provider breakdown
        provider_stats = {}
        for key, state in self.states.items():
            provider = key.split(":")[0]
            if provider not in provider_stats:
                provider_stats[provider] = {"requests": 0, "rejected": 0, "penalties": 0}
            
            provider_stats[provider]["requests"] += state.total_requests
            provider_stats[provider]["rejected"] += state.rejected_requests
            provider_stats[provider]["penalties"] += state.penalty_count
        
        print(f"\n📊 Provider Statistics:")
        for provider, stats in provider_stats.items():
            rejection_rate = (stats["rejected"] / stats["requests"] * 100) if stats["requests"] > 0 else 0
            print(f"  • {provider}: {stats['requests']} requests, {rejection_rate:.1f}% rejected, {stats['penalties']} penalties")
        
        # Rate limited providers
        rate_limited_providers = []
        for key, state in self.states.items():
            if state.cooldown_until and state.cooldown_until > datetime.now():
                provider, account = key.split(":", 1)
                time_left = (state.cooldown_until - datetime.now()).total_seconds()
                rate_limited_providers.append((provider, account, time_left))
        
        if rate_limited_providers:
            print(f"\n⏰ Rate Limited Providers:")
            for provider, account, time_left in rate_limited_providers:
                print(f"  • {provider}:{account} - {time_left:.0f}s")
        
        print()


# CLI interface
def main():
    """CLI interface for rate limiter."""
    import argparse
    
    parser = argparse.ArgumentParser(description="llx Rate Limiter")
    parser.add_argument("command", choices=[
        "add", "remove", "check", "record", "release", "status", "available", "cleanup"
    ])
    parser.add_argument("--provider", help="Provider name")
    parser.add_argument("--account", help="Account name")
    parser.add_argument("--type", choices=["requests_per_hour", "tokens_per_hour", "requests_per_minute", "concurrent_requests"], help="Limit type")
    parser.add_argument("--limit", type=int, help="Rate limit value")
    parser.add_argument("--tokens", type=int, default=0, help="Number of tokens")
    parser.add_argument("--cooldown", type=int, default=60, help="Cooldown minutes")
    parser.add_argument("--success", action="store_true", help="Request was successful")
    
    args = parser.parse_args()
    
    limiter = RateLimiter()
    
    if args.command == "add":
        if not args.provider or not args.account:
            print("❌ --provider and --account required for add")
            sys.exit(1)
        
        limits = {}
        if args.type and args.limit:
            limits[LimitType(args.type)] = args.limit
        
        config = RateLimitConfig(
            provider=args.provider,
            account=args.account,
            limits=limits,
            cooldown_minutes=args.cooldown
        )
        
        success = limiter.add_limit(config)
        if success:
            limiter.save_limits()
    
    elif args.command == "remove":
        if not args.provider or not args.account:
            print("❌ --provider and --account required for remove")
            sys.exit(1)
        
        success = limiter.remove_limit(args.provider, args.account)
        if success:
            limiter.save_limits()
    
    elif args.command == "check":
        if not args.provider or not args.account:
            print("❌ --provider and --account required for check")
            sys.exit(1)
        
        request_type = LimitType(args.type) if args.type else LimitType.REQUESTS_PER_HOUR
        allowed, reason = limiter.check_rate_limit(args.provider, args.account, request_type, args.tokens)
        
        if allowed:
            print("✅ Request allowed")
        else:
            print(f"❌ Request denied: {reason}")
    
    elif args.command == "record":
        if not args.provider or not args.account:
            print("❌ --provider and --account required for record")
            sys.exit(1)
        
        request_type = LimitType(args.type) if args.type else LimitType.REQUESTS_PER_HOUR
        success = limiter.record_request(args.provider, args.account, request_type, args.tokens, args.success)
    
    elif args.command == "release":
        if not args.provider or not args.account:
            print("❌ --provider and --account required for release")
            sys.exit(1)
        
        success = limiter.release_request(args.provider, args.account)
    
    elif args.command == "status":
        status = limiter.get_status(args.provider, args.account)
        print(json.dumps(status, indent=2))
    
    elif args.command == "available":
        request_type = LimitType(args.type) if args.type else LimitType.REQUESTS_PER_HOUR
        available = limiter.get_available_providers(request_type)
        
        print(f"📋 Available Providers ({len(available)}):")
        for provider in available:
            print(f"  • {provider['provider']}:{provider['account']} (score: {provider['score']:.1f}, utilization: {provider['utilization']:.1f}%)")
    
    elif args.command == "cleanup":
        limiter._cleanup_expired_penalties()
        limiter.save_limits()
        print("✅ Cleanup completed")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
