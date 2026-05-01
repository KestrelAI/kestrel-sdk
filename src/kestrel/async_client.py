"""Async Kestrel client — mirrors KestrelClient with async/await."""

from __future__ import annotations

from typing import Any

import httpx

from .auth import Config, load_config
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


class _AsyncWorkflowsNamespace:
    def __init__(self, client: AsyncKestrelClient):
        self._c = client

    async def list(self, *, status: str | None = None) -> list[Workflow]:
        params = {}
        if status:
            params["status"] = status
        data = await self._c._get("/api/workflows", params=params)
        return [Workflow.model_validate(w) for w in data]

    async def get(self, workflow_id: str) -> Workflow:
        return Workflow.model_validate(await self._c._get(f"/api/workflows/{workflow_id}"))

    async def create(self, *, name: str, description: str = "", definition: dict[str, Any] | None = None,
                     trigger_config: dict[str, Any] | None = None, nl_prompt: str = "",
                     alert_config: dict[str, Any] | None = None) -> Workflow:
        body: dict[str, Any] = {"name": name, "description": description}
        if definition is not None:
            body["definition"] = definition
        if trigger_config is not None:
            body["trigger_config"] = trigger_config
        if nl_prompt:
            body["nl_prompt"] = nl_prompt
        if alert_config is not None:
            body["alert_config"] = alert_config
        return Workflow.model_validate(await self._c._post("/api/workflows", json=body))

    async def update(self, workflow_id: str, *, name: str | None = None, description: str | None = None,
                     definition: dict[str, Any] | None = None, trigger_config: dict[str, Any] | None = None,
                     nl_prompt: str | None = None) -> Workflow:
        current = await self.get(workflow_id)
        body: dict[str, Any] = {
            "name": name if name is not None else current.name,
            "description": description if description is not None else current.description,
            "definition": definition if definition is not None else current.definition,
            "trigger_config": trigger_config if trigger_config is not None else current.trigger_config,
            "nl_prompt": nl_prompt if nl_prompt is not None else current.nl_prompt,
        }
        return Workflow.model_validate(await self._c._put(f"/api/workflows/{workflow_id}", json=body))

    async def delete(self, workflow_id: str) -> None:
        await self._c._delete(f"/api/workflows/{workflow_id}")

    async def activate(self, workflow_id: str) -> None:
        await self._c._post(f"/api/workflows/{workflow_id}/activate")

    async def pause(self, workflow_id: str) -> None:
        await self._c._post(f"/api/workflows/{workflow_id}/pause")

    async def duplicate(self, workflow_id: str, *, name: str = "") -> Workflow:
        return Workflow.model_validate(
            await self._c._post(f"/api/workflows/{workflow_id}/duplicate", json={"name": name})
        )

    async def deploy(self, workflow: Any, *, activate: bool = False) -> Workflow:
        """Create a workflow from a builder and optionally activate it."""
        definition, trigger_config = workflow.build()
        body: dict[str, Any] = {
            "name": workflow._name,
            "description": workflow._description,
            "definition": definition,
            "trigger_config": trigger_config,
        }
        if workflow._alert_config:
            body["alert_config"] = workflow._alert_config
        created = Workflow.model_validate(await self._c._post("/api/workflows", json=body))
        if activate:
            await self.activate(created.id)
            created.status = "active"
        return created

    async def test(self, workflow_id: str) -> Execution:
        return Execution.model_validate(await self._c._post(f"/api/workflows/{workflow_id}/test"))

    async def generate(self, prompt: str) -> GenerateResult:
        return GenerateResult.model_validate(
            await self._c._post("/api/workflows/generate", json={"prompt": prompt})
        )

    async def stats(self) -> WorkflowStats:
        return WorkflowStats.model_validate(await self._c._get("/api/workflows/stats"))

    async def executions(self, workflow_id: str, *, page: int = 1, page_size: int = 20) -> ExecutionList:
        return ExecutionList.model_validate(
            await self._c._get(f"/api/workflows/{workflow_id}/executions",
                               params={"page": str(page), "page_size": str(page_size)})
        )

    async def catalog(self) -> Catalog:
        return Catalog.model_validate(await self._c._get("/api/workflows/catalog"))

    async def integrations(self) -> list[IntegrationStatus]:
        data = await self._c._get("/api/workflows/integrations/status")
        return [IntegrationStatus.model_validate(i) for i in data]

    async def suggestions(self) -> list[SuggestedWorkflow]:
        data = await self._c._get("/api/workflows/suggestions")
        return [SuggestedWorkflow.model_validate(s) for s in data]


class _AsyncExecutionsNamespace:
    def __init__(self, client: AsyncKestrelClient):
        self._c = client

    async def get(self, execution_id: str) -> Execution:
        return Execution.model_validate(
            await self._c._get(f"/api/workflow-executions/{execution_id}")
        )

    async def cancel(self, execution_id: str) -> None:
        await self._c._post(f"/api/workflow-executions/{execution_id}/cancel")

    async def wait(self, execution_id: str, *, poll_interval: float = 2.0, timeout: float = 300.0) -> Execution:
        """Poll until execution completes, fails, or times out."""
        import asyncio
        import time
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            ex = await self.get(execution_id)
            if ex.status in ("completed", "failed", "cancelled"):
                return ex
            await asyncio.sleep(poll_interval)
        raise TimeoutError(f"Execution {execution_id} did not complete within {timeout}s")


class _AsyncApprovalsNamespace:
    def __init__(self, client: AsyncKestrelClient):
        self._c = client

    async def list_pending(self) -> list[Approval]:
        data = await self._c._get("/api/workflow-approvals/pending")
        return [Approval.model_validate(a) for a in data]

    async def approve(self, approval_id: str, *, justification: str | None = None) -> None:
        body = {"justification": justification} if justification else None
        await self._c._post(f"/api/workflow-approvals/{approval_id}/approve", json=body)

    async def reject(self, approval_id: str) -> None:
        await self._c._post(f"/api/workflow-approvals/{approval_id}/reject")


class _AsyncRequestsNamespace:
    def __init__(self, client: AsyncKestrelClient):
        self._c = client

    async def list(self) -> list[WorkflowRequest]:
        data = await self._c._get("/api/workflow-requests")
        items = data.get("requests", []) if isinstance(data, dict) else data
        results = [WorkflowRequest.model_validate(r) for r in items]
        return [r for r in results if r.status in ("no_workflow", "approved", "rejected")]

    async def approve(self, request_id: str) -> None:
        await self._c._post(f"/api/workflow-requests/{request_id}/approve")

    async def reject(self, request_id: str) -> None:
        await self._c._post(f"/api/workflow-requests/{request_id}/reject")


class AsyncKestrelClient:
    """Async entry point for the Kestrel Python SDK.

    Usage::

        async with AsyncKestrelClient(api_key="kestrel_sk_...") as client:
            workflows = await client.workflows.list()
            execution = await client.workflows.test(workflows[0].id)
            result = await client.executions.wait(execution.id)
    """

    DEFAULT_SERVER = "https://platform.usekestrel.ai"

    def __init__(
        self,
        server: str = DEFAULT_SERVER,
        *,
        api_key: str | None = None,
        session_token: str | None = None,
        timeout: float = 120.0,
    ):
        if api_key is None and session_token is None:
            raise AuthError("Provide either api_key or session_token.")

        server = server.rstrip("/")
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if api_key is not None:
            headers["Authorization"] = f"Bearer {api_key}"
        else:
            assert session_token is not None
            headers["X-Session-Token"] = session_token

        self._config = Config(server_url=server, session_token=session_token or "")
        self._http = httpx.AsyncClient(base_url=server, headers=headers, timeout=timeout)
        self.workflows = _AsyncWorkflowsNamespace(self)
        self.executions = _AsyncExecutionsNamespace(self)
        self.approvals = _AsyncApprovalsNamespace(self)
        self.requests = _AsyncRequestsNamespace(self)

    @classmethod
    def from_config(cls) -> AsyncKestrelClient:
        cfg = load_config()
        if not cfg.is_logged_in:
            raise AuthError("Not logged in. Run `kestrel login` or use AsyncKestrelClient(api_key=...).")
        return cls(server=cfg.server_url, session_token=cfg.session_token)

    async def close(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> AsyncKestrelClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def _get(self, path: str, *, params: dict[str, str] | None = None) -> Any:
        return self._handle(await self._http.get(path, params=params))

    async def _post(self, path: str, *, json: Any = None) -> Any:
        return self._handle(await self._http.post(path, json=json))

    async def _put(self, path: str, *, json: Any = None) -> Any:
        return self._handle(await self._http.put(path, json=json))

    async def _delete(self, path: str) -> Any:
        return self._handle(await self._http.delete(path))

    @staticmethod
    def _handle(resp: httpx.Response) -> Any:
        if resp.status_code == 401:
            raise AuthError("Session expired or invalid. Re-authenticate.", status_code=401)
        if resp.status_code == 404:
            raise NotFoundError(resp.text[:200], status_code=404)
        if resp.status_code == 409:
            raise ConflictError(resp.text[:200], status_code=409)
        if resp.status_code >= 500:
            raise ServerError(resp.text[:200], status_code=resp.status_code)
        if resp.status_code >= 400:
            raise KestrelError(resp.text[:200], status_code=resp.status_code)
        if not resp.text:
            return None
        return resp.json()
