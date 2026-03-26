"""Instance manager CLI — _build_parser + _dispatch pattern."""

import json
import argparse

from .._utils import cli_main

from .models import InstanceType, InstanceConfig
from .manager import InstanceManager


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="llx Instance Manager")
    parser.add_argument(
        "command",
        choices=["create", "start", "stop", "remove", "list", "status", "metrics", "health", "cleanup"],
    )
    parser.add_argument("--instance-id", help="Instance ID")
    parser.add_argument("--type", choices=["vscode", "ai_tools", "llm_proxy"], help="Instance type")
    parser.add_argument("--account", help="Account name")
    parser.add_argument("--provider", help="Provider name")
    parser.add_argument("--port", type=int, help="Port number")
    parser.add_argument("--image", help="Docker image")
    parser.add_argument("--auto-start", action="store_true", help="Auto start instance")
    parser.add_argument("--auto-restart", action="store_true", help="Auto restart instance")
    return parser


def _dispatch(args: argparse.Namespace, mgr: InstanceManager) -> bool:
    handlers = {
        "create": _cmd_create,
        "start": _cmd_start,
        "stop": _cmd_stop,
        "remove": _cmd_remove,
        "list": _cmd_list,
        "status": _cmd_status,
        "metrics": _cmd_metrics,
        "health": _cmd_health,
        "cleanup": _cmd_cleanup,
    }
    handler = handlers.get(args.command)
    if handler:
        return handler(args, mgr)
    return False


def _cmd_create(args, mgr: InstanceManager) -> bool:
    if not args.instance_id or not args.type:
        print("❌ --instance-id and --type required for create")
        return False
    config = InstanceConfig(
        instance_id=args.instance_id,
        instance_type=InstanceType(args.type),
        account=args.account or "default",
        provider=args.provider or "default",
        port=args.port or 0,
        image=args.image or "default",
        auto_start=args.auto_start,
        auto_restart=args.auto_restart,
    )
    success = mgr.create_instance(config)
    if success and config.auto_start:
        mgr.start_instance(config.instance_id)
    if success:
        mgr.save_instances()
    return success


def _cmd_start(args, mgr: InstanceManager) -> bool:
    if not args.instance_id:
        print("❌ --instance-id required for start")
        return False
    success = mgr.start_instance(args.instance_id)
    if success:
        mgr.save_instances()
    return success


def _cmd_stop(args, mgr: InstanceManager) -> bool:
    if not args.instance_id:
        print("❌ --instance-id required for stop")
        return False
    success = mgr.stop_instance(args.instance_id)
    if success:
        mgr.save_instances()
    return success


def _cmd_remove(args, mgr: InstanceManager) -> bool:
    if not args.instance_id:
        print("❌ --instance-id required for remove")
        return False
    success = mgr.remove_instance(args.instance_id)
    if success:
        mgr.save_instances()
    return success


def _cmd_list(args, mgr: InstanceManager) -> bool:
    instance_type = InstanceType(args.type) if args.type else None
    instances = mgr.list_instances(instance_type)
    print(f"📋 Instances ({len(instances)}):")
    for inst in instances:
        print(f"  • {inst['instance_id']}: {inst['status']} ({inst['type']}, port {inst['port']})")
    return True


def _cmd_status(args, mgr: InstanceManager) -> bool:
    if args.instance_id:
        status = mgr.get_instance_status(args.instance_id)
        if status:
            print(json.dumps(status, indent=2))
            return True
        print(f"❌ Instance {args.instance_id} not found")
        return False
    mgr.print_status_summary()
    return True


def _cmd_metrics(args, mgr: InstanceManager) -> bool:
    if not args.instance_id:
        print("❌ --instance-id required for metrics")
        return False
    metrics = mgr.get_instance_metrics(args.instance_id)
    if metrics:
        print(json.dumps(metrics, indent=2))
        return True
    print(f"❌ Could not get metrics for {args.instance_id}")
    return False


def _cmd_health(args, mgr: InstanceManager) -> bool:
    results = mgr.health_check_all()
    print(json.dumps(results, indent=2))
    return True


def _cmd_cleanup(args, mgr: InstanceManager) -> bool:
    mgr.save_instances()
    print("✅ Cleanup completed")
    return True


def main():
    cli_main(_build_parser, _dispatch, InstanceManager)


if __name__ == "__main__":
    main()
