"""
Thin dispatcher CLI for llx orchestration system.
Replaces the monolithic orchestrator_cli.py (1264L) with delegation to sub-package CLIs.
"""

import sys
import time
import json
import argparse
from pathlib import Path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="llx-orchestrator",
        description="llx Orchestration System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  llx-orchestrator status                    # Show system status
  llx-orchestrator health                    # Check system health
  llx-orchestrator llm complete --prompt "Hello"
  llx-orchestrator vscode list
  llx-orchestrator session list
  llx-orchestrator instance list
  llx-orchestrator queue status
  llx-orchestrator rate-limit status
  llx-orchestrator routing status

For sub-command help:
  llx-orchestrator <component> --help
        """,
    )

    sub = parser.add_subparsers(dest="component", title="Components", metavar="COMPONENT")

    # Top-level system commands
    sub.add_parser("status", help="Show system-wide status")
    sub.add_parser("health", help="Check system health")

    mon = sub.add_parser("monitor", help="Monitor system metrics")
    mon.add_argument("--interval", type=int, default=30, help="Interval in seconds")
    mon.add_argument("--duration", type=int, default=300, help="Duration in seconds")

    # Component sub-commands — each delegates to its own CLI module
    sub.add_parser("llm", help="LLM orchestration")
    sub.add_parser("vscode", help="VS Code orchestration")
    sub.add_parser("session", help="Session management")
    sub.add_parser("instance", help="Instance management")
    sub.add_parser("queue", help="Queue management")
    sub.add_parser("rate-limit", help="Rate limiting")
    sub.add_parser("routing", help="Request routing")

    return parser


def _handle_status():
    """Print status summary for every sub-system."""
    from . import (
        SessionManager, InstanceManager, RateLimiter,
        QueueManager, RoutingEngine, VSCodeOrchestrator, LLMOrchestrator,
    )

    print("📊 llx Orchestration System Status")
    print("=================================\n")

    managers = [
        ("Sessions", SessionManager),
        ("Instances", InstanceManager),
        ("Rate Limits", RateLimiter),
        ("Queues", QueueManager),
        ("Routing", RoutingEngine),
        ("VS Code", VSCodeOrchestrator),
        ("LLM", LLMOrchestrator),
    ]

    for label, cls in managers:
        try:
            mgr = cls()
            if hasattr(mgr, "print_status_summary"):
                mgr.print_status_summary()
        except Exception as e:
            print(f"❌ {label}: {e}\n")


def _handle_health():
    """Run health checks across all components."""
    from .instances import InstanceManager

    print("🏥 System Health Check")
    print("====================\n")

    try:
        mgr = InstanceManager()
        results = mgr.health_check_all()
        print(json.dumps(results, indent=2))
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    return True


def _handle_monitor(interval: int, duration: int):
    """Monitor system metrics."""
    from .session import SessionManager
    from .instances import InstanceManager
    from .queue import QueueManager

    print(f"🔍 Monitoring system (interval: {interval}s, duration: {duration}s)")
    print("=" * 50)

    sm = SessionManager()
    im = InstanceManager()
    qm = QueueManager()

    start = time.time()
    try:
        while time.time() - start < duration:
            ts = time.strftime("%H:%M:%S")
            print(
                f"\r{ts} | Sessions: {len(sm.session_states)} "
                f"| Instances: {len(im.instances)} "
                f"| Queues: {len(qm.queues)}",
                end="", flush=True,
            )
            time.sleep(interval)
    except KeyboardInterrupt:
        pass
    print("\n✅ Monitoring completed")


def _delegate_to_subpackage(component: str, argv: list):
    """Forward remaining argv to the sub-package's CLI main()."""
    _CLI_MODULES = {
        "llm": "llx.orchestration.llm.cli",
        "vscode": "llx.orchestration.vscode.cli",
        "session": "llx.orchestration.session.cli",
        "instance": "llx.orchestration.instances.cli",
        "queue": "llx.orchestration.queue.cli",
        "rate-limit": "llx.orchestration.ratelimit.cli",
        "routing": "llx.orchestration.routing.cli",
    }

    mod_name = _CLI_MODULES.get(component)
    if not mod_name:
        print(f"❌ Unknown component: {component}")
        return False

    import importlib
    mod = importlib.import_module(mod_name)

    # Replace sys.argv so the sub-package's argparse sees only its own args
    old_argv = sys.argv
    sys.argv = [f"llx-orchestrator {component}"] + argv
    try:
        mod.main()
    except SystemExit as e:
        return e.code == 0
    finally:
        sys.argv = old_argv
    return True


def main():
    # Pre-parse: find the component, pass the rest to sub-package CLI
    parser = _build_parser()

    # If no args or --help, show top-level help
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        parser.print_help()
        sys.exit(1)

    component = sys.argv[1]

    if component == "status":
        _handle_status()
    elif component == "health":
        _handle_health()
    elif component == "monitor":
        args = parser.parse_args()
        _handle_monitor(args.interval, args.duration)
    elif component in ("llm", "vscode", "session", "instance", "queue", "rate-limit", "routing"):
        # Everything after the component name goes to the sub-package CLI
        remaining = sys.argv[2:]
        success = _delegate_to_subpackage(component, remaining)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
