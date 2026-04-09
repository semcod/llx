"""Persistence helpers for rate limiter configuration and state."""

import json
from datetime import datetime
from typing import Any, Dict

from .models import LimitType, RateLimitConfig, RateLimitState
from .._utils import save_json


def load_limits_from_file(self) -> bool:
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


def save_limits_to_file(self) -> bool:
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
