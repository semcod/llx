"""Utility for creating remove command handlers."""

from typing import Callable, Any, Optional, TypeVar
from ..cli_utils import cmd_remove_wrapper

T = TypeVar('T')


def create_remove_handler(
    id_attr: str,
    id_label: str,
    remove_func: Callable[[T, str], bool],
    save_func: Optional[Callable[[T], None]] = None
) -> Callable[[Any, T], bool]:
    """Create a remove command handler function.
    
    Args:
        id_attr: Attribute name for ID (e.g., 'session_id', 'instance_id')
        id_label: Human-readable label (e.g., 'Session', 'Instance')
        remove_func: Function that takes (manager, id) and removes the item
        save_func: Optional function that takes (manager) and saves state
        
    Returns:
        A function that can be used as a command handler
    """
    def handler(args: Any, mgr: T) -> bool:
        return cmd_remove_wrapper(
            args,
            id_attr=id_attr,
            id_label=id_label,
            remove_func=lambda item_id: remove_func(mgr, item_id),
            save_func=lambda: save_func(mgr) if save_func else None
        )
    
    return handler
