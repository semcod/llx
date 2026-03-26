"""Session manager CLI — _build_parser + _dispatch pattern."""

import json
import argparse

from .._utils import cli_main
from ..cli_utils import cmd_list_wrapper, cmd_cleanup_wrapper
from ..utils._cmd_remove import create_remove_handler
from ..utils._cmd_status import create_status_handler

from .models import SessionType, SessionConfig
from .manager import SessionManager


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="llx Session Manager")
    parser.add_argument(
        "command",
        choices=["create", "remove", "list", "status", "queue", "cleanup"],
    )
    parser.add_argument("--session-id", help="Session ID")
    parser.add_argument("--type", choices=["llm", "vscode", "ai_tools"], help="Session type")
    parser.add_argument("--provider", help="Provider name")
    parser.add_argument("--model", help="Model name")
    parser.add_argument("--account", help="Account name")
    parser.add_argument("--max-requests", type=int, default=100, help="Max requests per hour")
    parser.add_argument("--max-tokens", type=int, default=100000, help="Max tokens per hour")
    parser.add_argument("--cooldown", type=int, default=60, help="Cooldown minutes")
    parser.add_argument("--priority", type=int, default=1, help="Priority (1=high)")
    return parser


def _dispatch(args: argparse.Namespace, mgr: SessionManager) -> bool:
    handlers = {
        "create": _cmd_create,
        "remove": _cmd_remove,
        "list": _cmd_list,
        "status": _cmd_status,
        "queue": _cmd_queue,
        "cleanup": _cmd_cleanup,
    }
    handler = handlers.get(args.command)
    if handler:
        return handler(args, mgr)
    return False


def _cmd_create(args, mgr: SessionManager) -> bool:
    if not args.session_id or not args.type or not args.provider:
        print("❌ --session-id, --type, and --provider required for create")
        return False
    config = SessionConfig(
        session_id=args.session_id,
        session_type=SessionType(args.type),
        provider=args.provider,
        model=args.model or "default",
        account=args.account or "default",
        max_requests_per_hour=args.max_requests,
        max_tokens_per_hour=args.max_tokens,
        cooldown_minutes=args.cooldown,
        priority=args.priority,
    )
    success = mgr.create_session(config)
    if success:
        mgr.save_sessions()
    return success


# Create remove handler
_cmd_remove = create_remove_handler(
    id_attr='session_id',
    id_label='Session',
    remove_func=lambda mgr, id: mgr.remove_session(id),
    save_func=lambda mgr: mgr.save_sessions()
)


def _cmd_list(args, mgr: SessionManager) -> bool:
    session_type = SessionType(args.type) if args.type else None
    sessions = mgr.list_sessions(session_type)
    print(f"📋 Sessions ({len(sessions)}):")
    for s in sessions:
        print(f"  • {s['session_id']}: {s['status']} ({s['type']})")
    return True


# Create status handler
_cmd_status = create_status_handler(
    id_attr='session_id',
    entity_label='Session',
    get_status_func=lambda mgr, id: mgr.get_session_status(id),
    print_summary_func=lambda mgr: mgr.print_status_summary()
)


def _cmd_queue(args, mgr: SessionManager) -> bool:
    status = mgr.get_queue_status()
    print(json.dumps(status, indent=2))
    return True


def _cmd_cleanup(args, mgr: SessionManager) -> bool:
    mgr._cleanup_expired_limits()
    mgr.save_sessions()
    print("✅ Cleanup completed")
    return True


def main():
    cli_main(_build_parser, _dispatch, SessionManager)


if __name__ == "__main__":
    main()
