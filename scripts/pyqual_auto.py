#!/usr/bin/env python3
"""Auto-mechanism for pyqual model switching and fix stage forcing.

Usage:
    # Change model and run pyqual
    python scripts/pyqual_auto.py --model openrouter/openai/gpt-5-mini
    
    # Force fix stage by lowering quality gates
    python scripts/pyqual_auto.py --model gpt-5-mini --force-fix
    
    # Dry run to see what would happen
    python scripts/pyqual_auto.py --model gpt-5-mini --force-fix --dry-run
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


def load_pyqual_config(path: Path) -> dict[str, Any]:
    """Load pyqual.yaml configuration."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_pyqual_config(path: Path, config: dict[str, Any]) -> None:
    """Save pyqual.yaml configuration."""
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def set_env_file(workdir: Path, model: str) -> str | None:
    """Set LLM_MODEL in .env file."""
    env_path = workdir / ".env"
    old_model = None
    
    if env_path.exists():
        content = env_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        new_lines = []
        found = False
        
        for line in lines:
            if line.startswith("LLM_MODEL="):
                old_model = line.split("=", 1)[1].strip().strip('"\'')
                new_lines.append(f'LLM_MODEL={model}')
                found = True
            else:
                new_lines.append(line)
        
        if not found:
            new_lines.append(f'LLM_MODEL={model}')
        
        env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    else:
        env_path.write_text(f'LLM_MODEL={model}\n', encoding="utf-8")
    
    return old_model


def restore_env_file(workdir: Path, old_model: str | None) -> None:
    """Restore original LLM_MODEL in .env file."""
    if old_model is None:
        return
    
    env_path = workdir / ".env"
    if env_path.exists():
        content = env_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        new_lines = []
        
        for line in lines:
            if line.startswith("LLM_MODEL="):
                new_lines.append(f'LLM_MODEL={old_model}')
            else:
                new_lines.append(line)
        
        env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def backup_config(path: Path) -> Path:
    """Create timestamped backup of config."""
    from datetime import datetime
    backup_name = f"{path.stem}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}{path.suffix}"
    backup_path = path.parent / backup_name
    backup_path.write_text(path.read_text(), encoding="utf-8")
    return backup_path


def set_model(config: dict[str, Any], model: str) -> dict[str, Any]:
    """Set LLM_MODEL in pyqual config."""
    if "pipeline" not in config:
        config["pipeline"] = {}
    if "env" not in config["pipeline"]:
        config["pipeline"]["env"] = {}
    
    old_model = config["pipeline"]["env"].get("LLM_MODEL", "<not set>")
    config["pipeline"]["env"]["LLM_MODEL"] = model
    return config, old_model


def force_fix_stage(config: dict[str, Any]) -> dict[str, Any]:
    """
    Modify quality gates to force fix stage.
    Lowers thresholds so current metrics fail.
    """
    metrics = config["pipeline"].get("metrics", {})
    
    # Store original values
    original = {
        "coverage_min": metrics.get("coverage_min", 15),
        "vallm_pass_min": metrics.get("vallm_pass_min", 50),
        "cc_max": metrics.get("cc_max", 15),
    }
    
    # Lower thresholds to force failure
    # Current: coverage ~17%, vallm ~53%, cc ~3.7
    # We set them high enough to fail
    metrics["coverage_min"] = 50  # Will fail (current ~17%)
    metrics["vallm_pass_min"] = 90  # Will fail (current ~53%)
    metrics["cc_max"] = 2  # Will fail (current ~3.7)
    
    config["pipeline"]["metrics"] = metrics
    return config, original


def restore_metrics(config: dict[str, Any], original: dict[str, Any]) -> dict[str, Any]:
    """Restore original metric thresholds."""
    metrics = config["pipeline"].get("metrics", {})
    metrics.update(original)
    config["pipeline"]["metrics"] = metrics
    return config


def run_pyqual(workdir: Path, dry_run: bool = False, verbose: bool = False) -> int:
    """Run pyqual command."""
    cmd = ["pyqual", "run"]
    if dry_run:
        cmd.append("--dry-run")
    if verbose:
        cmd.append("--verbose")
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=workdir)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Auto-mechanism for pyqual model switching and fix stage forcing"
    )
    parser.add_argument(
        "--model", "-m",
        required=True,
        help="LLM model to use (e.g., openrouter/openai/gpt-5-mini)"
    )
    parser.add_argument(
        "--force-fix", "-f",
        action="store_true",
        help="Force fix stage by lowering quality gates"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Dry run (don't actually run pyqual)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--workdir", "-w",
        type=Path,
        default=Path("."),
        help="Working directory (default: .)"
    )
    parser.add_argument(
        "--no-restore",
        action="store_true",
        help="Don't restore original config after run"
    )
    
    args = parser.parse_args()
    workdir = args.workdir.resolve()
    config_path = workdir / "pyqual.yaml"
    
    if not config_path.exists():
        print(f"Error: {config_path} not found", file=sys.stderr)
        return 1
    
    # Load and backup config
    print(f"Loading config from {config_path}")
    config = load_pyqual_config(config_path)
    backup_path = backup_config(config_path)
    print(f"Backup created: {backup_path}")
    
    # Set model in both pyqual.yaml and .env
    config, old_model_yaml = set_model(config, args.model)
    old_model_env = set_env_file(workdir, args.model)
    old_model = old_model_env or old_model_yaml
    print(f"Model changed: {old_model or '<default>'} -> {args.model}")
    
    original_metrics = None
    if args.force_fix:
        config, original_metrics = force_fix_stage(config)
        print("Quality gates lowered to force fix stage:")
        print(f"  coverage_min: 50 (was {original_metrics['coverage_min']})")
        print(f"  vallm_pass_min: 90 (was {original_metrics['vallm_pass_min']})")
        print(f"  cc_max: 2 (was {original_metrics['cc_max']})")
    
    # Save modified config
    save_pyqual_config(config_path, config)
    print(f"Config saved to {config_path}")
    
    if args.dry_run:
        print("\n[Dry run - not executing pyqual]")
        print("Modified config:")
        print(yaml.dump(config, default_flow_style=False))
        return 0
    
    # Run pyqual
    print("\n" + "=" * 60)
    print("Running pyqual...")
    print("=" * 60)
    rc = run_pyqual(workdir, dry_run=False, verbose=args.verbose)
    
    # Restore config
    if not args.no_restore:
        if original_metrics:
            config = load_pyqual_config(config_path)
            config = restore_metrics(config, original_metrics)
        
        # Restore from backup
        config_path.write_text(backup_path.read_text(), encoding="utf-8")
        print(f"\nConfig restored from {backup_path}")
        
        # Cleanup backup
        backup_path.unlink()
        print(f"Backup removed: {backup_path}")
        
        # Restore .env
        restore_env_file(workdir, old_model_env)
        print(f".env restored")
    
    return rc


if __name__ == "__main__":
    sys.exit(main())
