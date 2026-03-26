"""Utility for creating status command handlers."""

from typing import Callable, Any, TypeVar
import json

T = TypeVar('T')


def create_status_handler(
    id_attr: str,
    entity_label: str,
    get_status_func: Callable[[T, str], dict],
    print_summary_func: Callable[[T], None]
) -> Callable[[Any, T], bool]:
    """Create a status command handler that shows specific status or summary.
    
    Args:
        id_attr: Attribute name for ID (e.g., 'session_id', 'instance_id')
        entity_label: Label for error messages (e.g., 'Session', 'Instance')
        get_status_func: Function that takes (manager, id) and returns status dict
        print_summary_func: Function that takes (manager) and prints summary
        
    Returns:
        A function that can be used as a command handler
    """
    def handler(args: Any, manager: T) -> bool:
        entity_id = getattr(args, id_attr, None)
        
        if entity_id:
            status = get_status_func(manager, entity_id)
            if status:
                print(json.dumps(status, indent=2))
                return True
            print(f"❌ {entity_label} {entity_id} not found")
            return False
        
        print_summary_func(manager)
        return True
    
    return handler
