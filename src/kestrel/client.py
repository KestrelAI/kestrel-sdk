from __future__ import annotations

from typing import Any

import httpx

from .auth import Config, load_config, save_config
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


class _WorkflowsNamespace:
    """Workflow CRUD, generation, stats, catalog, and integrations."""

    def __init__(self, client: KestrelClient):
        self._c = client

    def list(self, *, status: str | None = None) -> list[Workflow]:
        params = {}
        if status:
            params["status"] = status
        data = self._c._get("/api/workflows", params=params)
        return [Workflow.model_validate(w) for w in data]

    def get(self, workflow_id: str) -> Workflow:
        return Workflow.model_validate(self._c._get(f"/api/workflows/{workflow_id}"))

    def create(
        self,
        *,
        name: str,
        description: str = "",
        definition: dict[str, Any] | None = None,
        trigger_config: dict[str, Any] | None = None,
        nl_prompt: str = "",
    ) -> Workflow:
        body: dict[str, Any] = {"name": name, "description": description}
        if definition is not None:
            body["definition"] = definition
        if trigger_config is not None:
            body["trigger_config"] = trigger_config
        if nl_prompt:
            body["nl_prompt"] = nl_prompt
        return Workflow.model_validate(self._c._post("/api/workflows", json=body))

    def update(
        self,
        workflow_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        definition: dict[str, Any] | None = None,
        trigger_config: dict[str, Any] | None = None,
        nl_prompt: str | None = None,
    ) -> Workflow:
        current = self.get(workflow_id)
        body: dict[str, Any] = {
            "name": name if name is not None else current.name,
            "description": description if description is not None else current.description,
            "definition": definition if definition is not None else current.definition,
            "trigger_config": trigger_config if trigger_config is not None else current.trigger_config,
            "nl_prompt": nl_prompt if nl_prompt is not None else current.nl_prompt,
        }
        return Workflow.model_validate(
            self._c._put(f"/api/workflows/{workflow_id}", json=body)
        )

    def delete(self, workflow_id: str) -> None:
        self._c._delete(f"/api/workflows/{workflow_id}")

    def activate(self, workflow_id: str) -> None:
        self._c._post(f"/api/workflows/{workflow_id}/activate")

    def pause(self, workflow_id: str) -> None:
        self._c._post(f"/api/workflows/{workflow_id}/pause")

    def duplicate(self, workflow_id: str, *, name: str = "") -> Workflow:
        return Workflow.model_validate(
            self._c._post(f"/api/workflows/{workflow_id}/duplicate", json={"name": name})
        )

    def deploy(
        self,
        workflow: Any,
        *,
        activate: bool = False,
    ) -> Workflow:
        """Create a workflow from a builder and optionally activate it.

        ``workflow`` should be a :class:`kestrel.workflows.Workflow` builder
        instance.  Its :meth:`build` method is called to compile the definition
        and trigger config dicts that the server expects.

        Example::

            from kestrel.workflows import Workflow as WF, Trigger, Action

            wf = (
                WF("Pod Crash RCA")
                .trigger(Trigger.k8s_pod_status().reasons("CrashLoopBackOff"))
                .then(Action.kestrel_trigger_rca())
            )
            created = client.workflows.deploy(wf, activate=True)
        """
        definition, trigger_config = workflow.build()
        body: dict[str, Any] = {
            "name": workflow._name,
            "description": workflow._description,
            "definition": definition,
            "trigger_config": trigger_config,
        }
        if workflow._alert_config:
            body["alert_config"] = workflow._alert_config
        created = Workflow.model_validate(self._c._post("/api/workflows", json=body))
        if activate:
            self.activate(created.id)
            created.status = "active"
        return created

    def test(self, workflow_id: str) -> Execution:
        return Execution.model_validate(
            self._c._post(f"/api/workflows/{workflow_id}/test")
        )

    def generate(self, prompt: str) -> GenerateResult:
        data = self._c._post("/api/workflows/generate", json={"prompt": prompt})
        return GenerateResult.model_validate(data)

    def request(self, prompt: str, *, requester_name: str | None = None) -> RequestResult:
        name = requester_name or self._c._config.email or "python-sdk"
        data = self._c._post(
            "/api/workflow-requests",
            json={"prompt": prompt, "source": "sdk", "requester_name": name},
        )
        return RequestResult.model_validate(data)

    def stats(self) -> WorkflowStats:
        return WorkflowStats.model_validate(self._c._get("/api/workflows/stats"))

    def executions(
        self, workflow_id: str, *, page: int = 1, page_size: int = 20
    ) -> ExecutionList:
        data = self._c._get(
            f"/api/workflows/{workflow_id}/executions",
            params={"page": str(page), "page_size": str(page_size)},
        )
        return ExecutionList.model_validate(data)

    def catalog(self) -> Catalog:
        return Catalog.model_validate(self._c._get("/api/workflows/catalog"))

    def integrations(self) -> list[IntegrationStatus]:
        data = self._c._get("/api/workflows/integrations/status")
        return [IntegrationStatus.model_validate(i) for i in data]

    def suggestions(self) -> list[SuggestedWorkflow]:
        data = self._c._get("/api/workflows/suggestions")
        return [SuggestedWorkflow.model_validate(s) for s in data]


class _ExecutionsNamespace:
    """Execution detail and cancellation."""

    def __init__(self, client: KestrelClient):
        self._c = client

    def get(self, execution_id: str) -> Execution:
        return Execution.model_validate(
            self._c._get(f"/api/workflow-executions/{execution_id}")
        )

    def cancel(self, execution_id: str) -> None:
        self._c._post(f"/api/workflow-executions/{execution_id}/cancel")

    def wait(self, execution_id: str, *, poll_interval: float = 2.0, timeout: float = 300.0) -> Execution:
        """Poll until execution completes, fails, or times out."""
        import time
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            ex = self.get(execution_id)
            if ex.status in ("completed", "failed", "cancelled"):
                return ex
            time.sleep(poll_interval)
        raise TimeoutError(f"Execution {execution_id} did not complete within {timeout}s")


class _ApprovalsNamespace:
    """Approval gate management."""

    def __init__(self, client: KestrelClient):
        self._c = client

    def list_pending(self) -> list[Approval]:
        data = self._c._get("/api/workflow-approvals/pending")
        return [Approval.model_validate(a) for a in data]

    def approve(self, approval_id: str, *, justification: str | None = None) -> None:
        body = {"justification": justification} if justification else None
        self._c._post(f"/api/workflow-approvals/{approval_id}/approve", json=body)

    def reject(self, approval_id: str) -> None:
        self._c._post(f"/api/workflow-approvals/{approval_id}/reject")


class _RequestsNamespace:
    """Unmatched workflow request management."""

    def __init__(self, client: KestrelClient):
        self._c = client

    def list(self) -> list[WorkflowRequest]:
        data = self._c._get("/api/workflow-requests")
        items = data.get("requests", []) if isinstance(data, dict) else data
        results = [WorkflowRequest.model_validate(r) for r in items]
        return [r for r in results if r.status in ("no_workflow", "approved", "rejected")]

    def approve(self, request_id: str) -> None:
        self._c._post(f"/api/workflow-requests/{request_id}/approve")

    def reject(self, request_id: str) -> None:
        self._c._post(f"/api/workflow-requests/{request_id}/reject")


class KestrelClient:
    """Main entry point for the Kestrel Python SDK.

    Usage::

        # API key auth (recommended for programmatic access)
        client = KestrelClient(api_key="kestrel_sk_...")

        # From existing CLI login
        client = KestrelClient.from_config()

        # Login with credentials (defaults to production server)
        client = KestrelClient.login(email="...", password="...")

        # Direct session token (defaults to production server)
        client = KestrelClient(session_token="...")
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
            self._config = Config(server_url=server, session_token="")
        else:
            assert session_token is not None
            headers["X-Session-Token"] = session_token
            self._config = Config(server_url=server, session_token=session_token)

        self._http = httpx.Client(base_url=server, headers=headers, timeout=timeout)
        self.workflows = _WorkflowsNamespace(self)
        self.executions = _ExecutionsNamespace(self)
        self.approvals = _ApprovalsNamespace(self)
        self.requests = _RequestsNamespace(self)

    @classmethod
    def from_config(cls) -> KestrelClient:
        cfg = load_config()
        if not cfg.is_logged_in:
            raise AuthError("Not logged in. Run `kestrel login` or use KestrelClient.login().")
        return cls(server=cfg.server_url, session_token=cfg.session_token)

    @classmethod
    def login(
        cls,
        *,
        server: str = DEFAULT_SERVER,
        email: str,
        password: str,
        save: bool = True,
    ) -> KestrelClient:
        server = server.rstrip("/")
        resp = httpx.post(
            f"{server}/api/login",
            json={"email": email, "password": password},
            timeout=30.0,
        )
        if resp.status_code >= 400:
            raise AuthError(f"Login failed: {resp.text[:200]}", status_code=resp.status_code)
        data = resp.json()
        if data.get("requires_2fa"):
            raise AuthError("Account requires 2FA. Log in via the web UI or CLI first.")
        token = data["session_token"]
        if save:
            save_config(Config(
                server_url=server,
                session_token=token,
                user_id=data.get("user_id", ""),
                email=email,
            ))
        return cls(server=server, session_token=token)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> KestrelClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    # --- HTTP helpers ---

    def _get(self, path: str, *, params: dict[str, str] | None = None) -> Any:
        return self._handle(self._http.get(path, params=params))

    def _post(self, path: str, *, json: Any = None) -> Any:
        return self._handle(self._http.post(path, json=json))

    def _put(self, path: str, *, json: Any = None) -> Any:
        return self._handle(self._http.put(path, json=json))

    def _delete(self, path: str) -> Any:
        return self._handle(self._http.delete(path))

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
