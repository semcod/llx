"""Utility for creating cleanup command handlers."""

from typing import Callable, Any, TypeVar

T = TypeVar('T')


def create_cleanup_handler(
    save_func: Callable[[T], None]
) -> Callable[[Any, T], bool]:
    """Create a cleanup command handler that saves state and prints completion.
    
    Args:
        save_func: Function that takes (manager) and saves state
        
    Returns:
        A function that can be used as a command handler
    """
    def handler(args: Any, manager: T) -> bool:
        save_func(manager)
        print("✅ Cleanup completed")
        return True
    
    return handler
