"""
Authentication context module for storing current user information
across the request lifecycle using contextvars
"""
from contextvars import ContextVar
from typing import Optional
from uuid import UUID

# Context variables to store the current user ID and organization ID
current_user_id: ContextVar[Optional[str]] = ContextVar('current_user_id', default=None)
current_organization_id: ContextVar[Optional[str]] = ContextVar('current_organization_id', default=None)

def set_current_user_id(user_id: UUID) -> None:
    """Set the current user ID in the context"""
    current_user_id.set(str(user_id))

def get_current_user_id() -> Optional[str]:
    """Get the current user ID from the context"""
    return current_user_id.get()

def set_current_organization_id(organization_id: UUID) -> None:
    """Set the current organization ID in the context"""
    current_organization_id.set(str(organization_id))

def get_current_organization_id() -> Optional[str]:
    """Get the current organization ID from the context"""
    return current_organization_id.get()

def set_current_auth_context(user_id: UUID, organization_id: UUID) -> None:
    """Set both user ID and organization ID in the context"""
    set_current_user_id(user_id)
    set_current_organization_id(organization_id)

def clear_current_user_id() -> None:
    """Clear the current user ID from the context"""
    current_user_id.set(None)

def clear_current_organization_id() -> None:
    """Clear the current organization ID from the context"""
    current_organization_id.set(None)

def clear_auth_context() -> None:
    """Clear both user ID and organization ID from the context"""
    clear_current_user_id()
    clear_current_organization_id()
