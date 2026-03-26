"""LiteLLM proxy management.

Generates proxy config and can start/stop the proxy process.
"""

from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

import yaml

from llx.config import LlxConfig


def generate_proxy_config(config: LlxConfig, output_path: Path | None = None) -> str:
    """Generate a LiteLLM proxy config YAML.

    Args:
        config: LlxConfig with model definitions.
        output_path: Where to write the config file. If None, returns string only.

    Returns:
        YAML config string.
    """
    model_list = []
    for tier_name, model in config.models.items():
        entry: dict[str, Any] = {
            "model_name": tier_name,
            "litellm_params": {
                "model": model.model_id,
            },
        }
        if model.provider == "ollama":
            entry["litellm_params"]["api_base"] = "http://localhost:11434"
        elif model.provider == "openrouter":
            entry["litellm_params"]["api_base"] = "https://openrouter.ai/api/v1"

        model_list.append(entry)

    proxy_config: dict[str, Any] = {
        "model_list": model_list,
        "litellm_settings": {
            "drop_params": True,
            "set_verbose": config.verbose,
        },
        "general_settings": {
            "master_key": config.proxy.master_key,
        },
    }

    if config.proxy.redis_url:
        proxy_config["litellm_settings"]["cache"] = True
        proxy_config["litellm_settings"]["cache_params"] = {
            "type": "redis",
            "url": config.proxy.redis_url,
        }

    if config.proxy.budget_limit:
        proxy_config["general_settings"]["max_budget"] = config.proxy.budget_limit

    yaml_str = yaml.dump(proxy_config, default_flow_style=False, sort_keys=False)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(yaml_str, encoding="utf-8")

    return yaml_str


def start_proxy(
    config: LlxConfig,
    *,
    config_path: Path | None = None,
    background: bool = True,
) -> subprocess.Popen | None:
    """Start LiteLLM proxy server.

    Args:
        config: LlxConfig with proxy settings.
        config_path: Path to proxy config YAML. Generated if not provided.
        background: Run in background (returns Popen) or foreground (blocks).

    Returns:
        Popen process if background=True, None if foreground.
    """
    if not shutil.which("litellm"):
        raise RuntimeError(
            "litellm CLI not found. Install with: pip install codr[litellm]"
        )

    # Generate config file if needed
    if config_path is None:
        config_path = Path.home() / ".codr" / "proxy_config.yaml"
        generate_proxy_config(config, config_path)

    cmd = [
        "litellm",
        "--config", str(config_path),
        "--host", config.proxy.host,
        "--port", str(config.proxy.port),
    ]

    if background:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Wait briefly and check if it started
        time.sleep(2)
        if proc.poll() is not None:
            raise RuntimeError(f"Proxy failed to start (exit code {proc.returncode})")
        return proc

    # Foreground — blocks until killed
    subprocess.run(cmd)
    return None


def check_proxy(base_url: str = "http://localhost:4000") -> bool:
    """Check if LiteLLM proxy is running."""
    try:
        import httpx
        resp = httpx.get(f"{base_url}/health", timeout=3.0)
        return resp.status_code == 200
    except Exception:
        return False
