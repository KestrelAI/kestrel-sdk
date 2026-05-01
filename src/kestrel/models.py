from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class Workflow(BaseModel):
    id: str
    tenant_id: str = ""
    name: str
    description: str = ""
    status: str
    definition: dict[str, Any] = Field(default_factory=dict)
    trigger_config: dict[str, Any] = Field(default_factory=dict)
    nl_prompt: str = ""
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    last_triggered_at: Optional[str] = None
    trigger_count: int = 0


class GenerateResult(BaseModel):
    success: bool = True
    name: str = ""
    description: str = ""
    definition: dict[str, Any] = Field(default_factory=dict)
    trigger_config: dict[str, Any] = Field(default_factory=dict)
    explanation: str = ""
    error: Optional[str] = None


class WorkflowStats(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    total_workflows: int = 0
    active_workflows: int = 0
    total_executions: int = 0
    status_breakdown: dict[str, int] = Field(default_factory=dict)
    daily_executions: list[DailyExecutionCount] = Field(default_factory=list)


class DailyExecutionCount(BaseModel):
    date: str = ""
    completed: int = 0
    failed: int = 0
    running: int = 0
    waiting: int = 0


# Fix forward reference
WorkflowStats.model_rebuild()


class Execution(BaseModel):
    id: str
    workflow_id: str = ""
    tenant_id: str = ""
    incident_id: str = ""
    trigger_signal: dict[str, Any] = Field(default_factory=dict)
    status: str = ""
    started_at: str = ""
    completed_at: Optional[str] = None
    step_results: Optional[list[Any]] = Field(default_factory=list)
    error_message: str = ""
    current_step_id: str = ""


class ExecutionList(BaseModel):
    executions: list[Execution] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


class Approval(BaseModel):
    id: str
    execution_id: str = ""
    tenant_id: str = ""
    step_id: str = ""
    approval_type: str = ""
    status: str = ""
    requested_at: str = ""
    responded_at: Optional[str] = None
    responded_by: Optional[str] = None
    pr_url: str = ""
    expires_at: Optional[str] = None
    context: dict[str, Any] = Field(default_factory=dict)


class WorkflowRequest(BaseModel):
    model_config = {"populate_by_name": True}

    id: str
    tenant_id: str = ""
    requester_slack_user_id: str = Field(default="", alias="requester_slack_user_id")
    requester_name: str = ""
    source: str = ""
    prompt: str = ""
    category: str = ""
    matched_workflow_id: Optional[str] = None
    execution_id: Optional[str] = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    missing_parameters: list[Any] = Field(default_factory=list)
    suggested_workflow: dict[str, Any] = Field(default_factory=dict)
    status: str = ""
    created_at: str = ""
    updated_at: str = ""


class RequestResult(BaseModel):
    status: str = ""
    request_id: str = ""
    workflow_name: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
    missing_parameters: list[str] = Field(default_factory=list)
    extracted_parameters: dict[str, Any] = Field(default_factory=dict)
    explanation: str = ""
    category: str = ""
    request_url: str = ""
    error: str = ""


class SuggestedWorkflow(BaseModel):
    id: str = ""
    tenant_id: str = ""
    name: str = ""
    description: str = ""
    definition: dict[str, Any] = Field(default_factory=dict)
    nl_prompt: str = ""
    created_at: str = ""


class SignalTemplate(BaseModel):
    id: str
    source: str = ""
    name: str = ""
    description: str = ""
    category: str = ""
    signal_type: str = ""


class ActionTemplate(BaseModel):
    id: str
    integration: str = ""
    name: str = ""
    description: str = ""
    category: str = ""


class IntegrationMeta(BaseModel):
    id: str
    name: str = ""


class Catalog(BaseModel):
    signals: list[SignalTemplate] = Field(default_factory=list)
    actions: list[ActionTemplate] = Field(default_factory=list)
    integrations: list[IntegrationMeta] = Field(default_factory=list)


class IntegrationStatus(BaseModel):
    id: str
    name: str = ""
    connected: bool = False
