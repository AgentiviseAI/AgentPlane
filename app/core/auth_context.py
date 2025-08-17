"""
Authentication context module for storing current user information
across the request lifecycle using contextvars
"""
from contextvars import ContextVar
from typing import Optional
from uuid import UUID

# Context variables to store the current user ID, organization ID, and access token
current_user_id: ContextVar[Optional[str]] = ContextVar('current_user_id', default=None)
current_organization_id: ContextVar[Optional[str]] = ContextVar('current_organization_id', default=None)
current_access_token: ContextVar[Optional[str]] = ContextVar('current_access_token', default=None)

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

def set_current_access_token(access_token: str) -> None:
    """Set the current access token in the context"""
    current_access_token.set(access_token)

def get_current_access_token() -> Optional[str]:
    """Get the current access token from the context"""
    return current_access_token.get()

def set_current_auth_context(user_id: UUID, organization_id: UUID, access_token: str = None) -> None:
    """Set user ID, organization ID, and optionally access token in the context"""
    set_current_user_id(user_id)
    set_current_organization_id(organization_id)
    if access_token:
        set_current_access_token(access_token)

def clear_current_user_id() -> None:
    """Clear the current user ID from the context"""
    current_user_id.set(None)

def clear_current_organization_id() -> None:
    """Clear the current organization ID from the context"""
    current_organization_id.set(None)

def clear_current_access_token() -> None:
    """Clear the current access token from the context"""
    current_access_token.set(None)

def clear_auth_context() -> None:
    """Clear user ID, organization ID, and access token from the context"""
    clear_current_user_id()
    clear_current_organization_id()
    clear_current_access_token()
