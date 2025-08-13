"""
Authentication context module for storing current user information
across the request lifecycle using contextvars
"""
from contextvars import ContextVar
from typing import Optional
from uuid import UUID

# Context variable to store the current user ID
current_user_id: ContextVar[Optional[str]] = ContextVar('current_user_id', default=None)

def set_current_user_id(user_id: UUID) -> None:
    """Set the current user ID in the context"""
    current_user_id.set(str(user_id))

def get_current_user_id() -> Optional[str]:
    """Get the current user ID from the context"""
    return current_user_id.get()

def clear_current_user_id() -> None:
    """Clear the current user ID from the context"""
    current_user_id.set(None)
