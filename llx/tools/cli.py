"""
Thin dispatcher CLI for llx tools.
Replaces the monolithic LLXToolsCLI class (783L) with delegation to each manager's CLI.
"""

import sys
import importlib
import argparse


_CLI_MODULES = {
    "docker": "llx.tools.docker_manager",
    "ai-tools": "llx.tools.ai_tools_manager",
    "vscode": "llx.tools.vscode_manager",
    "models": "llx.tools.model_manager",
    "config": "llx.tools.config_manager",
    "health": "llx.tools.health_checker",
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="llx-tools",
        description="llx Ecosystem Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  llx-tools start                          # Start dev environment (docker)
  llx-tools status                         # Show system status (docker)
  llx-tools health check                   # Run health check
  llx-tools models list                    # List Ollama models
  llx-tools config summary                 # Show config summary
  llx-tools ai-tools shell                 # Access AI tools shell
  llx-tools vscode quick-start             # VS Code quick start

For sub-command help:
  llx-tools <component> --help
        """,
    )

    sub = parser.add_subparsers(dest="component", title="Components", metavar="COMPONENT")

    # Convenience top-level aliases that delegate to docker_manager
    start_p = sub.add_parser("start", help="Start llx environment")
    start_p.add_argument("--env", default="dev", choices=["dev", "prod", "full"])
    start_p.add_argument("--service", help="Specific service")

    stop_p = sub.add_parser("stop", help="Stop llx environment")
    stop_p.add_argument("--env", default="dev", choices=["dev", "prod", "full"])
    stop_p.add_argument("--service", help="Specific service")

    status_p = sub.add_parser("status", help="Show system status")
    status_p.add_argument("--env", default="dev", choices=["dev", "prod", "full"])

    # Component sub-commands
    for name in _CLI_MODULES:
        sub.add_parser(name, help=f"{name} management")

    return parser


def _delegate(component: str, argv: list) -> bool:
    """Forward remaining argv to the component's main()."""
    mod_name = _CLI_MODULES.get(component)
    if not mod_name:
        print(f"❌ Unknown component: {component}")
        return False

    mod = importlib.import_module(mod_name)

    old_argv = sys.argv
    sys.argv = [f"llx-tools {component}"] + argv
    try:
        mod.main()
    except SystemExit as e:
        return e.code == 0
    finally:
        sys.argv = old_argv
    return True


def _handle_start(args):
    """Convenience: llx-tools start → docker start."""
    extra = ["start", f"--env={args.env}"]
    if args.service:
        extra += [f"--service={args.service}"]
    return _delegate("docker", extra)


def _handle_stop(args):
    """Convenience: llx-tools stop → docker stop."""
    extra = ["stop", f"--env={args.env}"]
    if args.service:
        extra += [f"--service={args.service}"]
    return _delegate("docker", extra)


def _handle_status(args):
    """Convenience: llx-tools status → docker status."""
    return _delegate("docker", ["status", f"--env={args.env}"])


def main():
    parser = _build_parser()

    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        parser.print_help()
        sys.exit(1)

    component = sys.argv[1]

    # Top-level convenience aliases
    if component == "start":
        args = parser.parse_args()
        success = _handle_start(args)
    elif component == "stop":
        args = parser.parse_args()
        success = _handle_stop(args)
    elif component == "status":
        args = parser.parse_args()
        success = _handle_status(args)
    elif component in _CLI_MODULES:
        remaining = sys.argv[2:]
        success = _delegate(component, remaining)
    else:
        parser.print_help()
        sys.exit(1)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
