"""
Shared utilities for tools sub-package.
Eliminates repeated CLI boilerplate across managers.
"""

import sys
from typing import Callable, Optional


def cli_main(
    build_parser: Callable,
    dispatch: Callable,
    factory: Callable,
    cleanup: Optional[Callable] = None,
) -> None:
    """Generic CLI entry point.

    Parameters
    ----------
    build_parser : callable returning argparse.ArgumentParser
    dispatch : callable(args, instance) -> bool
    factory : callable() -> manager instance
    cleanup : optional callable(instance) called in finally block
    """
    parser = build_parser()
    args = parser.parse_args()
    instance = factory()
    try:
        success = dispatch(args, instance)
    finally:
        if cleanup:
            cleanup(instance)
    sys.exit(0 if success else 1)
