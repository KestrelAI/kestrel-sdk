"""Kestrel Python SDK — programmatic access to Kestrel Workflows."""

from .client import KestrelClient
from .async_client import AsyncKestrelClient
from .exceptions import AuthError, ConflictError, KestrelError, NotFoundError, ServerError
from .models import (
    Approval,
    Catalog,
    Execution,
    ExecutionList,
    GenerateResult,
    IntegrationStatus,
    RequestResult,
    SuggestedWorkflow,
    Workflow,
    WorkflowRequest,
    WorkflowStats,
)

__all__ = [
    "KestrelClient",
    "AsyncKestrelClient",
    "KestrelError",
    "AuthError",
    "NotFoundError",
    "ConflictError",
    "ServerError",
    "Workflow",
    "GenerateResult",
    "WorkflowStats",
    "Execution",
    "ExecutionList",
    "Approval",
    "WorkflowRequest",
    "RequestResult",
    "SuggestedWorkflow",
    "Catalog",
    "IntegrationStatus",
]
