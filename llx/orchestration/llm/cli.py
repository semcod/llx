"""
LLM orchestrator CLI — split from monolithic main().
Entry point: main() with _build_parser() + _dispatch() pattern.
"""

import json
import argparse

from .._utils import cli_main

from .models import LLMProviderType, ModelCapability, LLMProvider
from .orchestrator import LLMOrchestrator


def _build_parser() -> argparse.ArgumentParser:
    """Build argument parser for LLM orchestrator CLI.  CC ≤ 5."""
    parser = argparse.ArgumentParser(description="llx LLM Orchestrator")
    parser.add_argument(
        "command",
        choices=[
            "add-provider", "remove-provider", "list-providers",
            "add-model", "list-models", "model-info",
            "complete", "cancel", "status", "usage", "cleanup",
        ],
    )
    parser.add_argument("--provider-id", help="Provider ID")
    parser.add_argument("--model-id", help="Model ID")
    parser.add_argument("--request-id", help="Request ID")
    parser.add_argument(
        "--type",
        choices=["openai", "anthropic", "google", "openrouter", "ollama", "local", "custom"],
        help="Provider type",
    )
    parser.add_argument("--name", help="Provider name")
    parser.add_argument("--api-base", help="API base URL")
    parser.add_argument(
        "--capability",
        choices=[c.value for c in ModelCapability],
        help="Model capability",
    )
    return parser


def _dispatch(args: argparse.Namespace, orchestrator: LLMOrchestrator) -> bool:
    """Dispatch CLI command.  CC ≤ 10."""
    handlers = {
        "add-provider": _cmd_add_provider,
        "remove-provider": _cmd_remove_provider,
        "list-providers": _cmd_list_providers,
        "list-models": _cmd_list_models,
        "model-info": _cmd_model_info,
        "complete": _cmd_complete,
        "cancel": _cmd_cancel,
        "status": _cmd_status,
        "usage": _cmd_usage,
        "cleanup": _cmd_cleanup,
    }
    handler = handlers.get(args.command)
    if handler:
        return handler(args, orchestrator)
    print(f"❌ Unknown command: {args.command}")
    return False


# ── Individual command handlers ─────────────────────────────

def _cmd_add_provider(args, orch: LLMOrchestrator) -> bool:
    if not args.provider_id or not args.type or not args.name:
        print("❌ --provider-id, --type, and --name required for add-provider")
        return False
    provider = LLMProvider(
        provider_id=args.provider_id,
        provider_type=LLMProviderType(args.type),
        name=args.name,
        api_base=getattr(args, "api_base", None),
        auth_method="api_key",
    )
    success = orch.add_provider(provider)
    if success:
        orch.save_config()
    return success


def _cmd_remove_provider(args, orch: LLMOrchestrator) -> bool:
    if not args.provider_id:
        print("❌ --provider-id required for remove-provider")
        return False
    success = orch.remove_provider(args.provider_id)
    if success:
        orch.save_config()
    return success


def _cmd_list_providers(args, orch: LLMOrchestrator) -> bool:
    status = orch.get_provider_status()
    for pid, ps in status["providers"].items():
        print(f"  • {pid}: {ps['health_status']} ({ps['models_count']} models)")
    return True


def _cmd_list_models(args, orch: LLMOrchestrator) -> bool:
    capability = ModelCapability(args.capability) if args.capability else None
    models = orch.list_models(args.provider_id, capability)
    for model in models:
        print(f"  • {model['model_id']}: {model['display_name']} ({model['provider']})")
    return True


def _cmd_model_info(args, orch: LLMOrchestrator) -> bool:
    if not args.model_id:
        print("❌ --model-id required for model-info")
        return False
    info = orch.get_model_info(args.model_id)
    if info:
        print(json.dumps(info, indent=2))
        return True
    print(f"❌ Model {args.model_id} not found")
    return False


def _cmd_complete(args, orch: LLMOrchestrator) -> bool:
    print("❌ Complete command requires request data (not implemented in CLI)")
    return False


def _cmd_cancel(args, orch: LLMOrchestrator) -> bool:
    if not args.request_id:
        print("❌ --request-id required for cancel")
        return False
    return orch.cancel_request(args.request_id)


def _cmd_status(args, orch: LLMOrchestrator) -> bool:
    orch.print_status_summary()
    return True


def _cmd_usage(args, orch: LLMOrchestrator) -> bool:
    stats = orch.get_usage_stats()
    print(json.dumps(stats, indent=2))
    return True


def _cmd_cleanup(args, orch: LLMOrchestrator) -> bool:
    orch.save_config()
    print("✅ Cleanup completed")
    return True


def main():
    """CLI entry point.  CC ≤ 3."""
    cli_main(_build_parser, _dispatch, LLMOrchestrator, cleanup=lambda o: o.stop())


if __name__ == "__main__":
    main()
