"""Compatibility helpers for the optional `nfo` dependency.

When `nfo` is installed, this module re-exports the real objects. When it is
missing, it provides lightweight stdlib fallbacks so `llx.prellm` remains
importable in the default dev/test environment.
"""

from __future__ import annotations

import inspect
import logging
import sys
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable

try:  # pragma: no cover - exercised indirectly when nfo is installed
    from nfo.configure import configure
    from nfo.decorators import catch, log_call
    from nfo.logger import Logger
    from nfo.sinks import MarkdownSink
    from nfo.terminal import TerminalSink
except ImportError:  # pragma: no cover - fallback is covered by tests
    Logger = logging.Logger

    @dataclass
    class TerminalSink:
        format: str = "markdown"
        stream: Any = sys.stderr
        show_args: bool = True
        show_return: bool = True
        show_duration: bool = True
        show_traceback: bool = True

    @dataclass
    class MarkdownSink:
        file_path: str = ""

    def _wrap_callable(func: Callable[..., Any]) -> Callable[..., Any]:
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                return await func(*args, **kwargs)

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return sync_wrapper

    def catch(func: Callable[..., Any]) -> Callable[..., Any]:
        return _wrap_callable(func)

    def log_call(func: Callable[..., Any]) -> Callable[..., Any]:
        return _wrap_callable(func)

    def _coerce_level(level: str | int) -> int:
        if isinstance(level, int):
            return level
        return getattr(logging, str(level).upper(), logging.INFO)

    def configure(
        name: str = "prellm",
        level: str | int = "INFO",
        sinks: list[Any] | tuple[Any, ...] | None = None,
        bridge_stdlib: bool = True,
        propagate_stdlib: bool = False,
        env_prefix: str | None = None,
        version: str | None = None,
        force: bool = False,
        **kwargs: Any,
    ) -> Logger:
        logger = logging.getLogger(name)
        logger.setLevel(_coerce_level(level))
        logger.propagate = propagate_stdlib

        if force:
            for handler in list(logger.handlers):
                logger.removeHandler(handler)

        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        has_handlers = False

        for sink in sinks or ():
            if isinstance(sink, MarkdownSink) and sink.file_path:
                handler = logging.FileHandler(sink.file_path, encoding="utf-8")
                handler.setFormatter(formatter)
                logger.addHandler(handler)
                has_handlers = True
            elif isinstance(sink, TerminalSink):
                stream = getattr(sink, "stream", None) or sys.stderr
                handler = logging.StreamHandler(stream)
                handler.setFormatter(formatter)
                logger.addHandler(handler)
                has_handlers = True

        if not has_handlers:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger


__all__ = [
    "Logger",
    "MarkdownSink",
    "TerminalSink",
    "catch",
    "configure",
    "log_call",
]
