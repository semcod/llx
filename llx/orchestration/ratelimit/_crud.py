"""CRUD helpers for managing rate limit configurations."""

from .models import LimitType, RateLimitConfig, RateLimitState


def create_default_limits(self):
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
        existed = key in self.limits or key in self.states
        self.limits.pop(key, None)
        self.states.pop(key, None)
        if existed:
            print(f"✅ Removed rate limit for {provider}:{account}")
        return existed
