"""Routing engine CLI — _build_parser + _dispatch pattern."""

import json
import argparse

from .._utils import cli_main

from .models import RoutingStrategy, ResourceType, RequestPriority, RoutingRequest
from .engine import RoutingEngine


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="llx Routing Engine")
    parser.add_argument(
        "command",
        choices=["route", "status", "metrics", "optimize", "cleanup"],
    )
    parser.add_argument("--request-id", help="Request ID")
    parser.add_argument(
        "--resource-type",
        choices=["llm", "vscode", "ai_tools"],
        help="Resource type",
    )
    parser.add_argument("--provider", help="Provider name")
    parser.add_argument("--account", help="Account name")
    parser.add_argument("--model", help="Model name")
    parser.add_argument(
        "--strategy",
        choices=[s.value for s in RoutingStrategy],
        help="Routing strategy",
    )
    parser.add_argument(
        "--priority",
        choices=["urgent", "high", "normal", "low", "background"],
        help="Request priority",
    )
    return parser


def _dispatch(args: argparse.Namespace, engine: RoutingEngine) -> bool:
    handlers = {
        "route": _cmd_route,
        "status": _cmd_status,
        "metrics": _cmd_metrics,
        "optimize": _cmd_optimize,
        "cleanup": _cmd_cleanup,
    }
    handler = handlers.get(args.command)
    if handler:
        return handler(args, engine)
    return False


def _cmd_route(args, engine: RoutingEngine) -> bool:
    if not args.request_id or not args.resource_type:
        print("❌ --request-id and --resource-type required for route")
        return False

    request = RoutingRequest(
        request_id=args.request_id,
        resource_type=ResourceType(args.resource_type),
        provider=args.provider,
        account=args.account,
        model=args.model,
        priority=RequestPriority(args.priority) if args.priority else RequestPriority.NORMAL,
        strategy=RoutingStrategy(args.strategy) if args.strategy else None,
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
            "reasoning": decision.reasoning,
        }, indent=2))
        return True
    print("❌ Routing failed")
    return False


def _cmd_status(args, engine: RoutingEngine) -> bool:
    status = engine.get_routing_status()
    print(json.dumps(status, indent=2))
    return True


def _cmd_metrics(args, engine: RoutingEngine) -> bool:
    engine.print_status_summary()
    return True


def _cmd_optimize(args, engine: RoutingEngine) -> bool:
    engine._optimize_routing()
    print("✅ Optimization completed")
    return True


def _cmd_cleanup(args, engine: RoutingEngine) -> bool:
    engine.save_config()
    print("✅ Cleanup completed")
    return True


def main():
    cli_main(_build_parser, _dispatch, RoutingEngine)


if __name__ == "__main__":
    main()
