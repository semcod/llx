"""Utility for creating simple command handlers with argument validation."""

from typing import Callable, Any, TypeVar
import argparse

T = TypeVar('T')


def create_simple_handler(
    arg_name: str,
    arg_label: str,
    manager_method: Callable[[T, str], bool]
) -> Callable[[argparse.Namespace, T], bool]:
    """Create a simple command handler that validates one argument and calls a manager method.
    
    Args:
        arg_name: Name of the required argument (e.g., 'extension', 'model', 'tier')
        arg_label: Human-readable label for error messages (e.g., 'extension', 'model', 'tier')
        manager_method: Method on the manager that takes the argument value
        
    Returns:
        A function that can be used as a command handler
    """
    def handler(args: argparse.Namespace, manager: T) -> bool:
        value = getattr(args, arg_name, None)
        if not value:
            print(f"❌ --{arg_name.replace('_', '-')} required for {arg_label}")
            return False
        return manager_method(manager, value)
    
    return handler
