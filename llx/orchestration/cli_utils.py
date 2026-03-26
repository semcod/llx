"""Shared CLI utilities for LLX orchestration commands."""

from typing import Callable, Any, Optional


def cmd_remove_wrapper(
    args: Any,
    id_attr: str,
    id_label: str,
    remove_func: Callable[[str], bool],
    save_func: Optional[Callable[[], None]] = None
) -> bool:
    """Generic wrapper for remove commands.
    
    Args:
        args: CLI arguments
        id_attr: Attribute name for ID (e.g., 'session_id', 'instance_id')
        id_label: Human-readable label (e.g., 'Session', 'Instance')
        remove_func: Function to call to remove the item
        save_func: Optional function to save state after removal
        
    Returns:
        True if successful, False otherwise
    """
    item_id = getattr(args, id_attr, None)
    
    if not item_id:
        print(f"❌ --{id_attr.replace('_', '-')} required for remove")
        return False
    
    success = remove_func(item_id)
    
    if success:
        print(f"✅ {id_label} '{item_id}' removed successfully")
        if save_func:
            save_func()
    else:
        print(f"❌ Failed to remove {id_label.lower()} '{item_id}'")
    
    return success


def cmd_status_wrapper(
    args: Any,
    id_attr: str,
    id_label: str,
    status_func: Callable[[str], dict]
) -> bool:
    """Generic wrapper for status commands.
    
    Args:
        args: CLI arguments
        id_attr: Attribute name for ID
        id_label: Human-readable label
        status_func: Function to get status
        
    Returns:
        True if successful, False otherwise
    """
    item_id = getattr(args, id_attr, None)
    
    if not item_id:
        print(f"❌ --{id_attr.replace('_', '-')} required for status")
        return False
    
    try:
        status = status_func(item_id)
        print(f"📊 {id_label} '{item_id}' status:")
        for key, value in status.items():
            print(f"  • {key}: {value}")
        return True
    except Exception as e:
        print(f"❌ Failed to get status: {e}")
        return False


def cmd_list_wrapper(
    items: list,
    title: str,
    formatter: Optional[Callable[[Any], str]] = None
) -> bool:
    """Generic wrapper for list commands.
    
    Args:
        items: List of items to display
        title: Title for the list
        formatter: Optional function to format each item
        
    Returns:
        True always
    """
    print(f"📋 {title} ({len(items)}):")
    
    if not items:
        print("  (none)")
        return True
    
    for item in items:
        if formatter:
            print(f"  • {formatter(item)}")
        else:
            print(f"  • {item}")
    
    return True


def cmd_cleanup_wrapper(
    cleanup_func: Callable[[], int],
    item_label: str = "items"
) -> bool:
    """Generic wrapper for cleanup commands.
    
    Args:
        cleanup_func: Function that performs cleanup and returns count
        item_label: Label for cleaned items
        
    Returns:
        True always
    """
    count = cleanup_func()
    print(f"🧹 Clean up complete: {count} {item_label} removed")
    return True
