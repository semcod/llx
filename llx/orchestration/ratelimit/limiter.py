"""
Rate Limiter — core rate limiting logic.
Extracted from the monolithic rate_limiter.py.
"""

import json
import time
import threading
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path

from .models import LimitType, RateLimitConfig, RateLimitState
from .._utils import save_json


class RateLimiter:
    """Manages rate limiting for multiple providers and accounts."""

    def __init__(self, config_file: str = None):
        self.project_root = Path.cwd()
        self.config_file = config_file or self.project_root / "orchestration" / "rate_limits.json"
        self.limits: Dict[str, RateLimitConfig] = {}
        self.states: Dict[str, RateLimitState] = {}
        self.lock = threading.RLock()

        self.default_limits = {
            "anthropic": {
                "requests_per_hour": 50, "tokens_per_hour": 100000,
                "requests_per_minute": 5, "concurrent_requests": 3,
            },
            "openai": {
                "requests_per_hour": 100, "tokens_per_hour": 200000,
                "requests_per_minute": 10, "concurrent_requests": 5,
            },
            "google": {
                "requests_per_hour": 60, "tokens_per_hour": 150000,
                "requests_per_minute": 8, "concurrent_requests": 4,
            },
            "openrouter": {
                "requests_per_hour": 200, "tokens_per_hour": 500000,
                "requests_per_minute": 20, "concurrent_requests": 10,
            },
            "ollama": {
                "requests_per_hour": 1000, "tokens_per_hour": 1000000,
                "requests_per_minute": 60, "concurrent_requests": 20,
            },
        }

        self.load_limits()

        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()

    # ── Config persistence ──────────────────────────────────

    def load_limits(self) -> bool:
        """Load rate limits from configuration file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    data = json.load(f)

                for limit_data in data.get("limits", []):
                    config = RateLimitConfig(
                        provider=limit_data["provider"],
                        account=limit_data["account"],
                        limits={LimitType(k): v for k, v in limit_data.get("limits", {}).items()},
                        cooldown_minutes=limit_data.get("cooldown_minutes", 60),
                        penalty_multiplier=limit_data.get("penalty_multiplier", 1.5),
                        max_penalties=limit_data.get("max_penalties", 3),
                        metadata=limit_data.get("metadata", {}),
                    )
                    key = f"{config.provider}:{config.account}"
                    self.limits[key] = config

                    state_data = data.get("states", {}).get(key, {})
                    state = RateLimitState(
                        provider=config.provider,
                        account=config.account,
                        current_usage={
                            LimitType(k): v for k, v in state_data.get("current_usage", {}).items()
                        },
                        last_reset_times={
                            LimitType(k): datetime.fromisoformat(v)
                            for k, v in state_data.get("last_reset_times", {}).items()
                        },
                        cooldown_until=(
                            datetime.fromisoformat(state_data["cooldown_until"])
                            if state_data.get("cooldown_until")
                            else None
                        ),
                        penalty_count=state_data.get("penalty_count", 0),
                        last_request_time=(
                            datetime.fromisoformat(state_data["last_request_time"])
                            if state_data.get("last_request_time")
                            else None
                        ),
                        concurrent_requests=state_data.get("concurrent_requests", 0),
                        total_requests=state_data.get("total_requests", 0),
                        rejected_requests=state_data.get("rejected_requests", 0),
                        metadata=state_data.get("metadata", {}),
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
            data: Dict[str, Any] = {"limits": [], "states": {}}

            for config in self.limits.values():
                data["limits"].append({
                    "provider": config.provider,
                    "account": config.account,
                    "limits": {k.value: v for k, v in config.limits.items()},
                    "cooldown_minutes": config.cooldown_minutes,
                    "penalty_multiplier": config.penalty_multiplier,
                    "max_penalties": config.max_penalties,
                    "metadata": config.metadata,
                })

            for state in self.states.values():
                key = f"{state.provider}:{state.account}"
                data["states"][key] = {
                    "current_usage": {k.value: v for k, v in state.current_usage.items()},
                    "last_reset_times": {
                        k.value: v.isoformat() for k, v in state.last_reset_times.items()
                    },
                    "cooldown_until": (
                        state.cooldown_until.isoformat() if state.cooldown_until else None
                    ),
                    "penalty_count": state.penalty_count,
                    "last_request_time": (
                        state.last_request_time.isoformat() if state.last_request_time else None
                    ),
                    "concurrent_requests": state.concurrent_requests,
                    "total_requests": state.total_requests,
                    "rejected_requests": state.rejected_requests,
                    "metadata": state.metadata,
                }

            return save_json(self.config_file, data, "rate limits")

        except Exception as e:
            print(f"❌ Error saving rate limits: {e}")
            return False

    def _create_default_limits(self):
        """Create default rate limits for common providers."""
        for provider, limits in self.default_limits.items():
            config = RateLimitConfig(
                provider=provider,
                account="default",
                limits={LimitType(k): v for k, v in limits.items()},
            )
            key = f"{config.provider}:{config.account}"
            self.limits[key] = config
            self.states[key] = RateLimitState(provider=provider, account="default")

    # ── Limit CRUD ──────────────────────────────────────────

    def add_limit(self, config: RateLimitConfig) -> bool:
        """Add or update a rate limit configuration."""
        with self.lock:
            key = f"{config.provider}:{config.account}"
            self.limits[key] = config
            if key not in self.states:
                self.states[key] = RateLimitState(
                    provider=config.provider, account=config.account
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

    # ── Rate check / record ─────────────────────────────────

    def check_rate_limit(
        self,
        provider: str,
        account: str,
        request_type: LimitType = LimitType.REQUESTS_PER_HOUR,
        tokens: int = 0,
    ) -> Tuple[bool, Optional[str]]:
        """Check if a request is allowed under rate limits."""
        with self.lock:
            key = f"{provider}:{account}"

            if key not in self.limits:
                if provider in self.default_limits:
                    config = RateLimitConfig(
                        provider=provider,
                        account=account,
                        limits={LimitType(k): v for k, v in self.default_limits[provider].items()},
                    )
                    self.limits[key] = config
                    self.states[key] = RateLimitState(provider=provider, account=account)
                else:
                    return False, f"No rate limit configuration for {provider}:{account}"

            config = self.limits[key]
            state = self.states[key]
            now = datetime.now()

            if state.cooldown_until and state.cooldown_until > now:
                remaining = (state.cooldown_until - now).total_seconds()
                return False, f"Rate limited (cooldown). Available in {remaining:.0f} seconds"

            if request_type == LimitType.CONCURRENT_REQUESTS:
                if state.concurrent_requests >= config.limits.get(LimitType.CONCURRENT_REQUESTS, 1):
                    return False, "Concurrent request limit exceeded"
                return True, None

            self._reset_counters_if_needed(key, now)

            if request_type in config.limits:
                limit = config.limits[request_type]
                usage = state.current_usage.get(request_type, 0)
                if request_type == LimitType.TOKENS_PER_HOUR:
                    usage += tokens
                if usage >= limit:
                    self._apply_penalty(key)
                    return False, f"{request_type.value} limit exceeded ({limit})"

            return True, None

    def record_request(
        self,
        provider: str,
        account: str,
        request_type: LimitType = LimitType.REQUESTS_PER_HOUR,
        tokens: int = 0,
        success: bool = True,
    ) -> bool:
        """Record a request for rate limiting."""
        with self.lock:
            key = f"{provider}:{account}"
            if key not in self.states:
                return False

            state = self.states[key]
            now = datetime.now()

            if request_type == LimitType.CONCURRENT_REQUESTS:
                if success:
                    state.concurrent_requests += 1
            else:
                state.current_usage[request_type] = state.current_usage.get(request_type, 0) + 1
                if request_type == LimitType.TOKENS_PER_HOUR:
                    state.current_usage[request_type] += tokens - 1

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

    # ── Query methods ───────────────────────────────────────

    def get_status(self, provider: str = None, account: str = None) -> Dict[str, Any]:
        """Get rate limiting status."""
        with self.lock:
            now = datetime.now()
            results: Dict[str, Any] = {}

            for key, config in self.limits.items():
                p, a = key.split(":", 1)
                if provider and p != provider:
                    continue
                if account and a != account:
                    continue

                state = self.states[key]

                utilization: Dict[str, Any] = {}
                for limit_type, limit in config.limits.items():
                    usage = state.current_usage.get(limit_type, 0)
                    utilization[limit_type.value] = {
                        "used": usage,
                        "limit": limit,
                        "percentage": (usage / limit * 100) if limit > 0 else 0,
                        "remaining": max(0, limit - usage),
                    }

                next_reset_times: Dict[str, float] = {}
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
                    "status": (
                        "rate_limited"
                        if (state.cooldown_until and state.cooldown_until > now)
                        else "available"
                    ),
                    "cooldown_until": (
                        state.cooldown_until.isoformat() if state.cooldown_until else None
                    ),
                    "penalty_count": state.penalty_count,
                    "concurrent_requests": state.concurrent_requests,
                    "total_requests": state.total_requests,
                    "rejected_requests": state.rejected_requests,
                    "utilization": utilization,
                    "next_reset_times": next_reset_times,
                    "last_request_time": (
                        state.last_request_time.isoformat() if state.last_request_time else None
                    ),
                }

            return results

    def get_available_providers(
        self, request_type: LimitType = LimitType.REQUESTS_PER_HOUR
    ) -> List[Dict[str, Any]]:
        """Get list of available providers sorted by availability."""
        with self.lock:
            available = []

            for key, config in self.limits.items():
                provider, account = key.split(":", 1)
                state = self.states[key]

                allowed, _ = self.check_rate_limit(provider, account, request_type)
                if not allowed:
                    continue

                utilization = 0.0
                if request_type in config.limits:
                    limit = config.limits[request_type]
                    usage = state.current_usage.get(request_type, 0)
                    utilization = (usage / limit) if limit > 0 else 0

                score = 100 - (utilization * 100) - (state.penalty_count * 10)

                available.append({
                    "provider": provider,
                    "account": account,
                    "score": score,
                    "utilization": utilization,
                    "penalty_count": state.penalty_count,
                    "concurrent_requests": state.concurrent_requests,
                })

            available.sort(key=lambda x: x["score"], reverse=True)
            return available

    # ── Internal helpers ────────────────────────────────────

    def _reset_counters_if_needed(self, key: str, now: datetime):
        """Reset counters if time period has passed."""
        state = self.states[key]
        config = self.limits[key]

        for limit_type in config.limits.keys():
            if limit_type in (LimitType.REQUESTS_PER_HOUR, LimitType.TOKENS_PER_HOUR):
                if limit_type not in state.last_reset_times:
                    state.last_reset_times[limit_type] = now
                    state.current_usage[limit_type] = 0
                else:
                    if now - state.last_reset_times[limit_type] >= timedelta(hours=1):
                        state.last_reset_times[limit_type] = now
                        state.current_usage[limit_type] = 0
            elif limit_type == LimitType.REQUESTS_PER_MINUTE:
                if limit_type not in state.last_reset_times:
                    state.last_reset_times[limit_type] = now
                    state.current_usage[limit_type] = 0
                else:
                    if now - state.last_reset_times[limit_type] >= timedelta(minutes=1):
                        state.last_reset_times[limit_type] = now
                        state.current_usage[limit_type] = 0

    def _apply_penalty(self, key: str):
        """Apply penalty for rate limit violation."""
        state = self.states[key]
        config = self.limits[key]

        state.penalty_count += 1
        cooldown_minutes = int(
            config.cooldown_minutes * (config.penalty_multiplier ** state.penalty_count)
        )
        state.cooldown_until = datetime.now() + timedelta(minutes=cooldown_minutes)

        for limit_type in config.limits.keys():
            if limit_type in (LimitType.REQUESTS_PER_HOUR, LimitType.TOKENS_PER_HOUR):
                state.current_usage[limit_type] = int(
                    state.current_usage.get(limit_type, 0) * 0.8
                )

        print(f"⚠️  Applied penalty to {key}: {cooldown_minutes} minutes cooldown")

    # ── Background tasks ────────────────────────────────────

    def _cleanup_worker(self):
        """Background worker for cleanup tasks."""
        while True:
            try:
                time.sleep(60)
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
        if time.time() % 300 < 60:
            self.save_limits()

    # ── Print summary ───────────────────────────────────────

    def print_status_summary(self):
        """Print comprehensive status summary."""
        print("⏱️  Rate Limiter Status")
        print("=====================")

        total_configs = len(self.limits)
        rate_limited = sum(
            1
            for state in self.states.values()
            if state.cooldown_until and state.cooldown_until > datetime.now()
        )

        print(f"📊 Total Configurations: {total_configs}")
        print(f"⏰ Rate Limited: {rate_limited}")
        print(f"📈 Total Requests: {sum(s.total_requests for s in self.states.values())}")
        print(f"❌ Rejected Requests: {sum(s.rejected_requests for s in self.states.values())}")

        provider_stats: Dict[str, Dict[str, int]] = {}
        for key, state in self.states.items():
            provider = key.split(":")[0]
            ps = provider_stats.setdefault(
                provider, {"requests": 0, "rejected": 0, "penalties": 0}
            )
            ps["requests"] += state.total_requests
            ps["rejected"] += state.rejected_requests
            ps["penalties"] += state.penalty_count

        print("\n📊 Provider Statistics:")
        for provider, stats in provider_stats.items():
            rejection_rate = (
                (stats["rejected"] / stats["requests"] * 100) if stats["requests"] > 0 else 0
            )
            print(
                f"  • {provider}: {stats['requests']} requests, "
                f"{rejection_rate:.1f}% rejected, {stats['penalties']} penalties"
            )

        rate_limited_providers = []
        for key, state in self.states.items():
            if state.cooldown_until and state.cooldown_until > datetime.now():
                provider, account = key.split(":", 1)
                time_left = (state.cooldown_until - datetime.now()).total_seconds()
                rate_limited_providers.append((provider, account, time_left))

        if rate_limited_providers:
            print("\n⏰ Rate Limited Providers:")
            for provider, account, time_left in rate_limited_providers:
                print(f"  • {provider}:{account} - {time_left:.0f}s")

        print()
