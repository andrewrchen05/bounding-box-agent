"""
Request context management for tracking requests across the system.
"""
import uuid
from contextvars import ContextVar
from typing import Optional

# Context variable to store the current request ID
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


def generate_request_id() -> str:
    """
    Generate a new unique request ID.
    
    Returns:
        A UUID-based request ID string
    """
    return str(uuid.uuid4())


def set_request_id(request_id: str) -> None:
    """
    Set the current request ID in the context.
    
    Args:
        request_id: The request ID to set
    """
    request_id_var.set(request_id)


def get_request_id() -> Optional[str]:
    """
    Get the current request ID from the context.
    
    Returns:
        The current request ID, or None if not set
    """
    return request_id_var.get()


def clear_request_id() -> None:
    """
    Clear the current request ID from the context.
    """
    request_id_var.set(None)
