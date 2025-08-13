"""
FastAPI service dependencies
"""
from fastapi import Depends
from app.core.di_container import get_container
from app.services import WorkflowService, LLMService


def get_workflow_service() -> WorkflowService:
    """FastAPI dependency to get the WorkflowService"""
    container = get_container()
    return container.workflow_service


def get_llm_service() -> LLMService:
    """FastAPI dependency to get the LLMService"""
    container = get_container()
    return container.llm_service

