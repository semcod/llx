"""CLI handlers for llx config manager."""

import argparse
import json
import sys
from typing import Callable

from .manager import ConfigManager
from llx.tools._utils import cli_main
from llx.tools.utils._cmd_uninstall_extension import create_simple_handler


# Type alias for command handler
CmdHandler = Callable[[argparse.Namespace, ConfigManager], bool]


def _cmd_load(args: argparse.Namespace, manager: ConfigManager) -> bool:
    if not args.type:
        print("❌ --type required for load")
        return False
    config = manager.load_config(args.type)
    if config:
        print(json.dumps(config, indent=2))
        return True
    return False


def _cmd_save(args: argparse.Namespace, manager: ConfigManager) -> bool:
    if not args.type:
        print("❌ --type required for save")
        return False
    try:
        config_data = json.loads(sys.stdin.read())
        return manager.save_config(args.type, config_data)
    except Exception:
        print("❌ Invalid JSON configuration")
        return False


def _cmd_create_env(args: argparse.Namespace, manager: ConfigManager) -> bool:
    return manager.create_default_env(args.overwrite)


def _cmd_update_env(args: argparse.Namespace, manager: ConfigManager) -> bool:
    if not args.key or not args.value:
        print("❌ --key and --value required for update-env")
        return False
    return manager.update_env_var(args.key, args.value)


def _cmd_get_env(args: argparse.Namespace, manager: ConfigManager) -> bool:
    if not args.key:
        print("❌ --key required for get-env")
        return False
    value = manager.get_env_var(args.key)
    if value is not None:
        print(value)
        return True
    print(f"❌ Environment variable {args.key} not found")
    return False


def _cmd_validate(args: argparse.Namespace, manager: ConfigManager) -> bool:
    issues = manager.validate_env_config()
    docker_issues = manager.validate_docker_configs()
    total = sum(len(v) for v in issues.values()) + sum(len(v) for v in docker_issues.values())
    if total > 0:
        print(f"❌ Found {total} configuration issues")
        return False
    print("✅ Configuration is valid")
    return True


def _cmd_list_models(args: argparse.Namespace, manager: ConfigManager) -> bool:
    manager.list_models()
    return True


def _cmd_add_model(args: argparse.Namespace, manager: ConfigManager) -> bool:
    if not args.tier:
        print("❌ --tier required for add-model")
        return False
    try:
        model_config = json.loads(sys.stdin.read())
        return manager.add_model(args.tier, model_config)
    except Exception:
        print("❌ Invalid model configuration")
        return False


# Create remove model handler
_cmd_remove_model = create_simple_handler(
    arg_name="tier",
    arg_label="remove-model",
    manager_method=lambda mgr, tier: mgr.remove_model(tier)
)


def _cmd_backup(args: argparse.Namespace, manager: ConfigManager) -> bool:
    return manager.backup_configs(args.backup_dir)


# Create restore handler
_cmd_restore = create_simple_handler(
    arg_name="backup_dir",
    arg_label="restore",
    manager_method=lambda mgr, dir: mgr.restore_configs(dir)
)


def _cmd_docker_env(args: argparse.Namespace, manager: ConfigManager) -> bool:
    return manager.generate_docker_env_file(args.env)


# Create create profile handler
_cmd_create_profile = create_simple_handler(
    arg_name="profile",
    arg_label="create-profile",
    manager_method=lambda mgr, profile: mgr.create_profile(profile)
)


# Create load profile handler
_cmd_load_profile = create_simple_handler(
    arg_name="profile",
    arg_label="load-profile",
    manager_method=lambda mgr, profile: mgr.load_profile(profile)
)


def _cmd_list_profiles(args: argparse.Namespace, manager: ConfigManager) -> bool:
    profiles = manager.list_profiles()
    if profiles:
        print("📋 Available Profiles:")
        for profile in profiles:
            print(f"  • {profile}")
    else:
        print("No profiles found")
    return True


def _cmd_summary(args: argparse.Namespace, manager: ConfigManager) -> bool:
    manager.print_config_summary()
    return True


# Command registry: maps command names to handler functions
_COMMAND_HANDLERS: dict[str, CmdHandler] = {
    "load": _cmd_load,
    "save": _cmd_save,
    "create-env": _cmd_create_env,
    "update-env": _cmd_update_env,
    "get-env": _cmd_get_env,
    "validate": _cmd_validate,
    "list-models": _cmd_list_models,
    "add-model": _cmd_add_model,
    "remove-model": _cmd_remove_model,
    "backup": _cmd_backup,
    "restore": _cmd_restore,
    "docker-env": _cmd_docker_env,
    "create-profile": _cmd_create_profile,
    "load-profile": _cmd_load_profile,
    "list-profiles": _cmd_list_profiles,
    "summary": _cmd_summary,
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="llx Config Manager")
    parser.add_argument("command", choices=list(_COMMAND_HANDLERS.keys()))
    parser.add_argument("--type", help="Configuration type")
    parser.add_argument("--key", help="Environment variable key")
    parser.add_argument("--value", help="Environment variable value")
    parser.add_argument("--tier", help="Model tier")
    parser.add_argument("--env", default="dev", help="Docker environment")
    parser.add_argument("--profile", help="Profile name")
    parser.add_argument("--backup-dir", help="Backup directory")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    return parser


def _dispatch(args: argparse.Namespace, manager: ConfigManager) -> bool:
    """Dispatch command to appropriate handler using registry pattern.
    
    CC reduced from 36 to ~3 by using handler registry instead of if-elif chain.
    """
    handler = _COMMAND_HANDLERS.get(args.command)
    if handler:
        return handler(args, manager)
    return False


def main():
    """CLI entry point for config manager."""
    cli_main(_build_parser, _dispatch, ConfigManager)


if __name__ == "__main__":
    main()
