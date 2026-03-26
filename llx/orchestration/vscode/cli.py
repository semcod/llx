"""VS Code orchestrator CLI — _build_parser + _dispatch pattern."""

import json
import argparse

from .._utils import cli_main
from ..cli_utils import cmd_remove_wrapper
from ..utils._cmd_remove import create_remove_handler
from ..utils._cmd_status import create_status_handler
from ..utils._cmd_cleanup import create_cleanup_handler

from .models import VSCodeAccountType, VSCodeAccount, VSCodeInstanceConfig
from .orchestrator import VSCodeOrchestrator


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="llx VS Code Orchestrator")
    parser.add_argument(
        "command",
        choices=[
            "add-account", "remove-account", "list-accounts",
            "create", "remove", "start", "stop",
            "list", "sessions", "status", "cleanup",
        ],
    )
    parser.add_argument("--account-id", help="Account ID")
    parser.add_argument("--instance-id", help="Instance ID")
    parser.add_argument("--session-id", help="Session ID")
    parser.add_argument("--name", help="Account name")
    parser.add_argument("--email", help="Account email")
    parser.add_argument(
        "--account-type",
        choices=[t.value for t in VSCodeAccountType],
        help="Account type",
    )
    parser.add_argument("--auth-method", default="password", help="Auth method")
    parser.add_argument("--port", type=int, default=0, help="Port number")
    parser.add_argument("--workspace", help="Workspace path")
    parser.add_argument("--auto-start-browser", action="store_true", help="Auto start browser")
    return parser


def _dispatch(args: argparse.Namespace, orch: VSCodeOrchestrator) -> bool:
    handlers = {
        "add-account": _cmd_add_account,
        "remove-account": _cmd_remove_account,
        "list-accounts": _cmd_list_accounts,
        "create": _cmd_create,
        "remove": _cmd_remove,
        "start": _cmd_start,
        "stop": _cmd_stop,
        "list": _cmd_list,
        "sessions": _cmd_sessions,
        "status": _cmd_status,
        "cleanup": _cmd_cleanup,
    }
    handler = handlers.get(args.command)
    if handler:
        return handler(args, orch)
    return False


def _cmd_add_account(args, orch: VSCodeOrchestrator) -> bool:
    if not args.account_id or not args.name:
        print("❌ --account-id and --name required for add-account")
        return False
    account = VSCodeAccount(
        account_id=args.account_id,
        account_type=VSCodeAccountType(args.account_type or "local"),
        name=args.name,
        email=args.email,
        auth_method=args.auth_method,
    )
    success = orch.add_account(account)
    if success:
        orch.save_config()
    return success


# Create remove handlers
_cmd_remove_account = create_remove_handler(
    id_attr="account_id",
    id_label="Account",
    remove_func=lambda orch, id: orch.remove_account(id),
    save_func=lambda orch: orch.save_config()
)

_cmd_remove = create_remove_handler(
    id_attr="instance_id",
    id_label="Instance",
    remove_func=lambda orch, id: orch.remove_instance(id),
    save_func=lambda orch: orch.save_config()
)


def _cmd_list_accounts(args, orch: VSCodeOrchestrator) -> bool:
    accounts = orch.list_accounts()
    print(f"📋 Accounts ({len(accounts)}):")
    for a in accounts:
        print(f"  • {a['account_id']}: {a['name']} ({a['account_type']}, {a['active_sessions']} sessions)")
    return True


def _cmd_create(args, orch: VSCodeOrchestrator) -> bool:
    if not args.instance_id or not args.account_id:
        print("❌ --instance-id and --account-id required for create")
        return False
    config = VSCodeInstanceConfig(
        instance_id=args.instance_id,
        account_id=args.account_id,
        port=args.port,
        workspace_path=args.workspace or ".",
        auto_start_browser=args.auto_start_browser,
    )
    success = orch.create_instance(config)
    if success:
        orch.save_config()
    return success


def _cmd_start(args, orch: VSCodeOrchestrator) -> bool:
    if not args.instance_id:
        print("❌ --instance-id required for start")
        return False
    session_id = orch.start_instance(args.instance_id)
    if session_id:
        orch.save_config()
        print(f"Session ID: {session_id}")
        return True
    return False


def _cmd_stop(args, orch: VSCodeOrchestrator) -> bool:
    if args.session_id:
        success = orch.end_session(args.session_id)
    elif args.instance_id:
        success = orch.remove_instance(args.instance_id)
    else:
        print("❌ --session-id or --instance-id required for stop")
        return False
    if success:
        orch.save_config()
    return success


def _cmd_list(args, orch: VSCodeOrchestrator) -> bool:
    instances = orch.list_instances(args.account_id)
    print(f"📋 Instances ({len(instances)}):")
    for inst in instances:
        print(f"  • {inst['instance_id']}: {inst['status']} (port {inst['port']}, {inst['active_sessions']} sessions)")
    return True


def _cmd_sessions(args, orch: VSCodeOrchestrator) -> bool:
    sessions = orch.list_sessions(args.account_id)
    print(f"📋 Sessions ({len(sessions)}):")
    for s in sessions:
        if s:
            print(f"  • {s['session_id']}: {s['instance_id']} ({s['session_duration_minutes']:.1f} min)")
    return True


# Create status handler
_cmd_status = create_status_handler(
    id_attr='session_id',
    entity_label='Session',
    get_status_func=lambda orch, id: orch.get_session_status(id),
    print_summary_func=lambda orch: orch.print_status_summary()
)


# Create cleanup handler
_cmd_cleanup = create_cleanup_handler(
    save_func=lambda orch: orch.save_config()
)


def main():
    cli_main(_build_parser, _dispatch, VSCodeOrchestrator, cleanup=lambda o: o.stop())


if __name__ == "__main__":
    main()
