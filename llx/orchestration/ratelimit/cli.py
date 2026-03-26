"""Rate limiter CLI — _build_parser + _dispatch pattern."""

import json
import argparse

from .._utils import cli_main

from .models import LimitType, RateLimitConfig
from .limiter import RateLimiter


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="llx Rate Limiter")
    parser.add_argument(
        "command",
        choices=["add", "remove", "check", "record", "release", "status", "available", "cleanup"],
    )
    parser.add_argument("--provider", help="Provider name")
    parser.add_argument("--account", help="Account name")
    parser.add_argument(
        "--type",
        choices=[lt.value for lt in LimitType],
        help="Limit type",
    )
    parser.add_argument("--limit", type=int, help="Rate limit value")
    parser.add_argument("--tokens", type=int, default=0, help="Number of tokens")
    parser.add_argument("--cooldown", type=int, default=60, help="Cooldown minutes")
    parser.add_argument("--success", action="store_true", help="Request was successful")
    return parser


def _dispatch(args: argparse.Namespace, limiter: RateLimiter) -> bool:
    handlers = {
        "add": _cmd_add,
        "remove": _cmd_remove,
        "check": _cmd_check,
        "record": _cmd_record,
        "release": _cmd_release,
        "status": _cmd_status,
        "available": _cmd_available,
        "cleanup": _cmd_cleanup,
    }
    handler = handlers.get(args.command)
    if handler:
        return handler(args, limiter)
    return False


def _cmd_add(args, limiter: RateLimiter) -> bool:
    if not args.provider or not args.account:
        print("❌ --provider and --account required for add")
        return False
    limits = {}
    if args.type and args.limit:
        limits[LimitType(args.type)] = args.limit
    config = RateLimitConfig(
        provider=args.provider,
        account=args.account,
        limits=limits,
        cooldown_minutes=args.cooldown,
    )
    success = limiter.add_limit(config)
    if success:
        limiter.save_limits()
    return success


def _cmd_remove(args, limiter: RateLimiter) -> bool:
    if not args.provider or not args.account:
        print("❌ --provider and --account required for remove")
        return False
    success = limiter.remove_limit(args.provider, args.account)
    if success:
        limiter.save_limits()
    return success


def _cmd_check(args, limiter: RateLimiter) -> bool:
    if not args.provider or not args.account:
        print("❌ --provider and --account required for check")
        return False
    request_type = LimitType(args.type) if args.type else LimitType.REQUESTS_PER_HOUR
    allowed, reason = limiter.check_rate_limit(args.provider, args.account, request_type, args.tokens)
    if allowed:
        print("✅ Request allowed")
    else:
        print(f"❌ Request denied: {reason}")
    return allowed


def _cmd_record(args, limiter: RateLimiter) -> bool:
    if not args.provider or not args.account:
        print("❌ --provider and --account required for record")
        return False
    request_type = LimitType(args.type) if args.type else LimitType.REQUESTS_PER_HOUR
    return limiter.record_request(args.provider, args.account, request_type, args.tokens, args.success)


def _cmd_release(args, limiter: RateLimiter) -> bool:
    if not args.provider or not args.account:
        print("❌ --provider and --account required for release")
        return False
    return limiter.release_request(args.provider, args.account)


def _cmd_status(args, limiter: RateLimiter) -> bool:
    status = limiter.get_status(args.provider, args.account)
    print(json.dumps(status, indent=2))
    return True


def _cmd_available(args, limiter: RateLimiter) -> bool:
    request_type = LimitType(args.type) if args.type else LimitType.REQUESTS_PER_HOUR
    available = limiter.get_available_providers(request_type)
    print(f"📋 Available Providers ({len(available)}):")
    for p in available:
        print(f"  • {p['provider']}:{p['account']} (score: {p['score']:.1f}, utilization: {p['utilization']:.1f}%)")
    return True


def _cmd_cleanup(args, limiter: RateLimiter) -> bool:
    limiter._cleanup_expired_penalties()
    limiter.save_limits()
    print("✅ Cleanup completed")
    return True


def main():
    cli_main(_build_parser, _dispatch, RateLimiter)


if __name__ == "__main__":
    main()
