"""_nfo_compat — Compatibility layer for nfo logging.

Falls back to stdlib logging and no-op decorators when `nfo` is unavailable.
This keeps llx.prellm importable without optional nfo dependency.
"""

from __future__ import annotations

import functools
import io
import logging
import sys
from pathlib import Path
from typing import Any, Callable, Optional, Protocol, TextIO, TypeVar, Union

F = TypeVar("F", bound=Callable[..., Any])

# Try to import nfo, fall back to stdlib
try:
    from nfo import log_call as _nfo_log_call
    from nfo import configure as _nfo_configure
    from nfo import Logger as _nfo_Logger
    from nfo import MarkdownSink as _nfo_MarkdownSink
    from nfo import TerminalSink as _nfo_TerminalSink
    NFO_AVAILABLE = True
except ImportError:
    NFO_AVAILABLE = False
    _nfo_log_call = None
    _nfo_configure = None
    _nfo_Logger = None
    _nfo_MarkdownSink = None
    _nfo_TerminalSink = None


# ============================================================
# Fallback Logger Implementation
# ============================================================

class _FallbackLogger:
    """Fallback logger using stdlib logging."""
    
    def __init__(self, name: str = "prellm", level: int = logging.INFO):
        self.name = name
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        # Add a handler if none exists
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stderr)
            handler.setLevel(level)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
    
    def debug(self, msg: str, **kwargs: Any) -> None:
        self._logger.debug(msg)
    
    def info(self, msg: str, **kwargs: Any) -> None:
        self._logger.info(msg)
    
    def warning(self, msg: str, **kwargs: Any) -> None:
        self._logger.warning(msg)
    
    def error(self, msg: str, **kwargs: Any) -> None:
        self._logger.error(msg)
    
    def critical(self, msg: str, **kwargs: Any) -> None:
        self._logger.critical(msg)
    
    def exception(self, msg: str, **kwargs: Any) -> None:
        self._logger.exception(msg)


# ============================================================
# Fallback Sink Classes
# ============================================================

class _FallbackTerminalSink:
    """Fallback terminal sink using stdlib logging."""
    
    def __init__(
        self,
        format: str = "markdown",
        stream: TextIO = sys.stderr,
        show_args: bool = True,
        show_return: bool = True,
        show_duration: bool = True,
        show_traceback: bool = True,
    ):
        self.format = format
        self.stream = stream
        self.show_args = show_args
        self.show_return = show_return
        self.show_duration = show_duration
        self.show_traceback = show_traceback


class _FallbackMarkdownSink:
    """Fallback markdown sink that writes to a file."""
    
    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        # Ensure parent directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)


# ============================================================
# Configure Function
# ============================================================

def configure(
    name: str = "prellm",
    level: str = "INFO",
    sinks: Optional[list[Any]] = None,
    bridge_stdlib: bool = True,
    propagate_stdlib: bool = False,
    env_prefix: str = "PRELLM_NFO_",
    version: str = "unknown",
    force: bool = False,
    **kwargs: Any,
) -> Any:
    """Configure logging.
    
    Uses nfo.configure if available, otherwise sets up stdlib logging.
    """
    if NFO_AVAILABLE and _nfo_configure is not None:
        return _nfo_configure(
            name=name,
            level=level,
            sinks=sinks,
            bridge_stdlib=bridge_stdlib,
            propagate_stdlib=propagate_stdlib,
            env_prefix=env_prefix,
            version=version,
            force=force,
            **kwargs,
        )
    
    # Fallback: return stdlib-based logger
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    log_level = level_map.get(level.upper(), logging.INFO)
    return _FallbackLogger(name, log_level)


# ============================================================
# log_call Decorator
# ============================================================

import asyncio


def log_call(func: F) -> F:
    """Decorator that logs function calls.
    
    Uses nfo.log_call if available, otherwise falls back to stdlib logging.
    """
    if NFO_AVAILABLE and _nfo_log_call is not None:
        return _nfo_log_call(func)
    
    # Fallback: stdlib logging decorator
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger = logging.getLogger(func.__module__)
        logger.debug(f"Calling {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.warning(f"{func.__name__} failed: {e}")
            raise
    
    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        logger = logging.getLogger(func.__module__)
        logger.debug(f"Calling {func.__name__} (async)")
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.warning(f"{func.__name__} failed: {e}")
            raise
    
    # Return appropriate wrapper based on whether function is async
    if asyncio.iscoroutinefunction(func):
        return async_wrapper  # type: ignore[return-value]
    return wrapper  # type: ignore[return-value]


# ============================================================
# Type aliases for exports
# ============================================================

if NFO_AVAILABLE:
    Logger = _nfo_Logger
    TerminalSink = _nfo_TerminalSink
    MarkdownSink = _nfo_MarkdownSink
else:
    Logger = _FallbackLogger
    TerminalSink = _FallbackTerminalSink
    MarkdownSink = _FallbackMarkdownSink


# Export for use in other modules
__all__ = [
    "log_call",
    "configure",
    "Logger",
    "TerminalSink",
    "MarkdownSink",
    "NFO_AVAILABLE",
]
