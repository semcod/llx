"""Config package for llx tools.

Backward-compatible re-exports from llx.tools.config_manager.
"""

from llx.tools.config.manager import ConfigManager
from llx.tools.config.cli import main

__all__ = ["ConfigManager", "main"]
