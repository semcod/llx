"""
Config Manager for llx - backward-compatible facade.

All implementations moved to llx.tools.config subpackage.
"""

from llx.tools.config.manager import ConfigManager
from llx.tools.config.cli import main

__all__ = ["ConfigManager", "main"]

# Backward compatibility re-exports
# ConfigManager class is now in llx.tools.config.manager
# CLI main() is now in llx.tools.config.cli
