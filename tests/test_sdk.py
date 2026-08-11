"""SDK test suite — tests the publicly installed kestrel-workflows package.

These tests use HTTP mocks via respx and verify the SDK behavior
as a customer would experience it after `pip install kestrel-workflows`.

Run::

    pip install kestrel-workflows  # install the public package
    pip install pytest respx pytest-asyncio
    pytest tests -v

Sections:
    TestAuth                — client construction
    TestHttpErrorMapping    — 401/404/409/5xx → typed exceptions
    TestWorkflowActivationValidation — save allowed, activate blocked when fields missing
    TestWorkflowsCRUD       — list/get/create/update/delete/activate/pause/duplicate
    TestWorkflowsExtras     — generate, request, stats, catalog, integrations, suggestions, test
    TestExecutions          — get, cancel, wait
    TestApprovals           — list_pending, approve, reject (incl. extra server fields)
    TestRequests            — list (unfiltered + filtered), approve, reject
    TestAsyncClient         — async surface parity
    TestBuilderDSL          — Trigger, Action, Condition, Approval, Workflow.build()
    TestNullTolerance       — server-returned null is coerced to default
"""

from __future__ import annotations

import asyncio
import importlib
import os
from typing import Any

import httpx
import pytest
import respx

import kestrel

# Optionally enforce running against the installed (PyPI) package — useful when
# release engineering wants to validate the published wheel. Off by default so
# editable installs (`pip install -e .[dev]`) — the standard dev workflow —
# don't have to fight the test runner.
if os.environ.get("KESTREL_REQUIRE_INSTALLED") == "1":
    _pkg_path = str(importlib.util.find_spec("kestrel").origin)
    assert "site-packages" in _pkg_path or "dist-packages" in _pkg_path, (
        f"KESTREL_REQUIRE_INSTALLED=1 but kestrel resolves to local source: {_pkg_path}\n"
        f"Install the public package with: pip install kestrel-workflows"
    )

from kestrel import (
    AsyncKestrelClient,
    AuthError,
    ConflictError,
    KestrelClient,
    KestrelError,
    NotFoundError,
    ServerError,
    ValidationError,
)
from kestrel.workflows import Action, Approval, Condition, ForEach, PollUntil, Trigger, Workflow

SERVER = "https://test.usekestrel.ai"
API_KEY = "kestrel_sk_test"


@pytest.fixture
def client():
    c = KestrelClient(server=SERVER, api_key=API_KEY)
    yield c
    c.close()


@pytest.fixture
def workflow_payload():
    return {
        "id": "wf-1",
        "tenant_id": "t-1",
        "name": "Test",
        "description": "",
        "status": "active",
        "definition": {"nodes": [], "edges": []},
        "trigger_config": {"source": "kubernetes"},
        "nl_prompt": "",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }


# ---------------------------------------------------------------------------
# Auth + HTTP error mapping
# ---------------------------------------------------------------------------


class TestAuth:
    def test_api_key_sets_bearer_header(self):
        c = KestrelClient(server=SERVER, api_key="abc")
        assert c._http.headers["Authorization"] == "Bearer abc"
        c.close()

    def test_session_token_sets_session_header(self):
        c = KestrelClient(server=SERVER, session_token="sess")
        assert c._http.headers["X-Session-Token"] == "sess"
        c.close()

    def test_no_credentials_raises(self):
        with pytest.raises(AuthError):
            KestrelClient(server=SERVER)

    def test_trailing_slash_in_server_is_stripped(self):
        c = KestrelClient(server=SERVER + "/", api_key="abc")
        assert str(c._http.base_url).rstrip("/") == SERVER
        c.close()


class TestHttpErrorMapping:
    @respx.mock
    def test_401_raises_auth_error(self, client):
        respx.get(f"{SERVER}/api/workflows").mock(httpx.Response(401, text="bad token"))
        with pytest.raises(AuthError):
            client.workflows.list()

    @respx.mock
    def test_404_raises_not_found(self, client):
        respx.get(f"{SERVER}/api/workflows/missing").mock(httpx.Response(404, text="nope"))
        with pytest.raises(NotFoundError):
            client.workflows.get("missing")

    @respx.mock
    def test_409_raises_conflict(self, client):
        respx.post(f"{SERVER}/api/workflows").mock(httpx.Response(409, text="dup"))
        with pytest.raises(ConflictError):
            client.workflows.create(name="dup")

    @respx.mock
    def test_500_raises_server_error(self, client):
        respx.get(f"{SERVER}/api/workflows").mock(httpx.Response(500, text="boom"))
        with pytest.raises(ServerError):
            client.workflows.list()

    @respx.mock
    def test_400_raises_kestrel_error(self, client):
        respx.get(f"{SERVER}/api/workflows").mock(httpx.Response(400, text="bad"))
        with pytest.raises(KestrelError):
            client.workflows.list()

    @respx.mock
    def test_empty_body_returns_none(self, client):
        respx.post(f"{SERVER}/api/workflows/wf-1/activate").mock(httpx.Response(204, text=""))
        assert client.workflows.activate("wf-1") is None


# ---------------------------------------------------------------------------
# Workflow activation validation (save allowed, activate blocked if missing fields)
# ---------------------------------------------------------------------------


class TestWorkflowActivationValidation:
    """Tests that workflows with missing required fields can be saved but not activated."""

    MISSING_FIELDS_RESPONSE = {
        "error": "Workflow has missing required fields",
        "missing_fields": [
            {"node_id": "action-1", "node_label": "Generate Manifest", "field_name": "name", "field_label": "Resource Name"},
        ],
        "message": 'Node "Generate Manifest": required field "Resource Name" is not set',
    }

    INCOMPLETE_DEFINITION = {
        "nodes": [
            {"id": "trigger-1", "type": "trigger", "data": {"source": "kubernetes"}},
            {
                "id": "action-1", "type": "action",
                "data": {
                    "action": "kestrel-generate-k8s-manifest",
                    "label": "Generate Manifest",
                    "integration": "kestrel",
                    "config": {"resource_type": "Deployment"},
                },
            },
        ],
        "edges": [{"id": "e1", "source": "trigger-1", "target": "action-1"}],
    }

    COMPLETE_DEFINITION = {
        "nodes": [
            {"id": "trigger-1", "type": "trigger", "data": {"source": "kubernetes"}},
            {
                "id": "action-1", "type": "action",
                "data": {
                    "action": "kestrel-generate-k8s-manifest",
                    "label": "Generate Manifest",
                    "integration": "kestrel",
                    "config": {"resource_type": "Deployment", "name": "my-app"},
                },
            },
        ],
        "edges": [{"id": "e1", "source": "trigger-1", "target": "action-1"}],
    }

    @respx.mock
    def test_save_allowed_with_missing_fields(self, client):
        """Creating (saving) a workflow with missing required fields should succeed."""
        respx.post(f"{SERVER}/api/workflows").mock(
            httpx.Response(201, json={
                "id": "wf-incomplete", "name": "Incomplete WF", "status": "draft",
                "definition": self.INCOMPLETE_DEFINITION,
                "trigger_config": {"source": "kubernetes"},
            })
        )
        wf = client.workflows.create(
            name="Incomplete WF",
            definition=self.INCOMPLETE_DEFINITION,
            trigger_config={"source": "kubernetes"},
        )
        assert wf.id == "wf-incomplete"
        assert wf.status == "draft"

    @respx.mock
    def test_activate_blocked_with_missing_fields(self, client):
        """Activating a workflow with missing required fields should raise ValidationError."""
        respx.post(f"{SERVER}/api/workflows/wf-incomplete/activate").mock(
            httpx.Response(400, json=self.MISSING_FIELDS_RESPONSE)
        )
        with pytest.raises(ValidationError) as exc_info:
            client.workflows.activate("wf-incomplete")

        err = exc_info.value
        assert err.status_code == 400
        assert len(err.missing_fields) == 1
        assert err.missing_fields[0]["field_name"] == "name"
        assert err.missing_fields[0]["node_label"] == "Generate Manifest"
        assert "Resource Name" in str(err)

    @respx.mock
    def test_save_allowed_with_complete_fields(self, client):
        """Creating a workflow with all required fields populated should succeed."""
        respx.post(f"{SERVER}/api/workflows").mock(
            httpx.Response(201, json={
                "id": "wf-complete", "name": "Complete WF", "status": "draft",
                "definition": self.COMPLETE_DEFINITION,
                "trigger_config": {"source": "kubernetes"},
            })
        )
        wf = client.workflows.create(
            name="Complete WF",
            definition=self.COMPLETE_DEFINITION,
            trigger_config={"source": "kubernetes"},
        )
        assert wf.id == "wf-complete"

    @respx.mock
    def test_activate_allowed_with_complete_fields(self, client):
        """Activating a workflow with all required fields should succeed."""
        respx.post(f"{SERVER}/api/workflows/wf-complete/activate").mock(
            httpx.Response(200, json={"status": "active"})
        )
        client.workflows.activate("wf-complete")

    @respx.mock
    def test_deploy_with_activate_raises_validation_error_for_incomplete(self, client):
        """deploy(wf, activate=True) should raise ValidationError if fields are missing."""
        respx.post(f"{SERVER}/api/workflows").mock(
            httpx.Response(201, json={
                "id": "wf-inc", "name": "Inc", "status": "draft",
                "definition": self.INCOMPLETE_DEFINITION,
                "trigger_config": {"source": "kubernetes"},
            })
        )
        respx.post(f"{SERVER}/api/workflows/wf-inc/activate").mock(
            httpx.Response(400, json=self.MISSING_FIELDS_RESPONSE)
        )

        wf_builder = (
            Workflow("Inc")
            .trigger(Trigger.k8s_pod_status())
            .then(Action("kestrel", "kestrel-generate-k8s-manifest")
                  .resource_type("Deployment"))
        )
        with pytest.raises(ValidationError) as exc_info:
            client.workflows.deploy(wf_builder, activate=True)
        assert exc_info.value.missing_fields[0]["field_name"] == "name"

    @respx.mock
    def test_deploy_with_activate_succeeds_for_complete(self, client):
        """deploy(wf, activate=True) should succeed when all fields are present."""
        respx.post(f"{SERVER}/api/workflows").mock(
            httpx.Response(201, json={
                "id": "wf-ok", "name": "OK", "status": "draft",
                "definition": self.COMPLETE_DEFINITION,
                "trigger_config": {"source": "kubernetes"},
            })
        )
        respx.post(f"{SERVER}/api/workflows/wf-ok/activate").mock(
            httpx.Response(200, json={"status": "active"})
        )

        wf_builder = (
            Workflow("OK")
            .trigger(Trigger.k8s_pod_status())
            .then(Action("kestrel", "kestrel-generate-k8s-manifest")
                  .resource_type("Deployment").name("my-app"))
        )
        created = client.workflows.deploy(wf_builder, activate=True)
        assert created.status == "active"

    @respx.mock
    def test_validation_error_multiple_missing_fields(self, client):
        """ValidationError should expose all missing fields when multiple are empty."""
        multi_missing = {
            "error": "Workflow has missing required fields",
            "missing_fields": [
                {"node_id": "action-1", "node_label": "Gen Manifest", "field_name": "resource_type", "field_label": "Resource Type"},
                {"node_id": "action-1", "node_label": "Gen Manifest", "field_name": "name", "field_label": "Resource Name"},
            ],
            "message": "The following required fields are not set:\n  - Node \"Gen Manifest\": \"Resource Type\"\n  - Node \"Gen Manifest\": \"Resource Name\"\n",
        }
        respx.post(f"{SERVER}/api/workflows/wf-x/activate").mock(
            httpx.Response(400, json=multi_missing)
        )
        with pytest.raises(ValidationError) as exc_info:
            client.workflows.activate("wf-x")
        assert len(exc_info.value.missing_fields) == 2


# ---------------------------------------------------------------------------
# Workflows CRUD
# ---------------------------------------------------------------------------


class TestWorkflowsCRUD:
    @respx.mock
    def test_list(self, client, workflow_payload):
        respx.get(f"{SERVER}/api/workflows").mock(httpx.Response(200, json=[workflow_payload]))
        wfs = client.workflows.list()
        assert len(wfs) == 1 and wfs[0].id == "wf-1"

    @respx.mock
    def test_list_with_status_filter_passes_query_param(self, client):
        route = respx.get(f"{SERVER}/api/workflows").mock(httpx.Response(200, json=[]))
        client.workflows.list(status="active")
        assert "status=active" in str(route.calls[0].request.url)

    @respx.mock
    def test_get(self, client, workflow_payload):
        respx.get(f"{SERVER}/api/workflows/wf-1").mock(httpx.Response(200, json=workflow_payload))
        wf = client.workflows.get("wf-1")
        assert wf.id == "wf-1"

    @respx.mock
    def test_create(self, client, workflow_payload):
        respx.post(f"{SERVER}/api/workflows").mock(httpx.Response(201, json=workflow_payload))
        wf = client.workflows.create(name="Test", definition={}, trigger_config={})
        assert wf.id == "wf-1"

    @respx.mock
    def test_update_round_trips_existing_state(self, client, workflow_payload):
        respx.get(f"{SERVER}/api/workflows/wf-1").mock(httpx.Response(200, json=workflow_payload))
        updated = {**workflow_payload, "description": "new"}
        put_route = respx.put(f"{SERVER}/api/workflows/wf-1").mock(httpx.Response(200, json=updated))
        out = client.workflows.update("wf-1", description="new")
        assert out.description == "new"
        body = put_route.calls[0].request.content.decode()
        assert "Test" in body  # original name preserved

    @respx.mock
    def test_delete(self, client):
        respx.delete(f"{SERVER}/api/workflows/wf-1").mock(httpx.Response(204, text=""))
        client.workflows.delete("wf-1")

    @respx.mock
    def test_activate_pause(self, client):
        respx.post(f"{SERVER}/api/workflows/wf-1/activate").mock(httpx.Response(200, json={}))
        respx.post(f"{SERVER}/api/workflows/wf-1/pause").mock(httpx.Response(200, json={}))
        client.workflows.activate("wf-1")
        client.workflows.pause("wf-1")

    @respx.mock
    def test_duplicate(self, client, workflow_payload):
        dup = {**workflow_payload, "id": "wf-2"}
        respx.post(f"{SERVER}/api/workflows/wf-1/duplicate").mock(httpx.Response(200, json=dup))
        out = client.workflows.duplicate("wf-1", name="copy")
        assert out.id == "wf-2"


# ---------------------------------------------------------------------------
# Workflows: extras (generate, request, stats, catalog, integrations, ...)
# ---------------------------------------------------------------------------


class TestWorkflowsExtras:
    @respx.mock
    def test_generate(self, client):
        respx.post(f"{SERVER}/api/workflows/generate").mock(
            httpx.Response(200, json={
                "success": True, "name": "Auto", "description": "",
                "definition": {"nodes": [{"id": "trigger-1", "type": "trigger"}], "edges": []},
                "trigger_config": {"source": "kubernetes"},
                "explanation": "ok",
            })
        )
        res = client.workflows.generate("when pod crashes, alert me")
        assert res.success and res.name == "Auto"

    @respx.mock
    def test_request(self, client):
        respx.post(f"{SERVER}/api/workflow-requests/submit").mock(
            httpx.Response(200, json={"status": "no_workflow", "request_id": "req-1"})
        )
        res = client.workflows.request("restart api-server")
        assert res.request_id == "req-1"

    @respx.mock
    def test_request_confirm(self, client):
        respx.post(f"{SERVER}/api/workflow-requests/req-1/confirm").mock(
            httpx.Response(200, json={"id": "req-1", "status": "no_workflow", "summary": "Filed for the platform team."})
        )
        res = client.workflows.request_confirm("req-1", True)
        assert res.id == "req-1" and res.status == "no_workflow"

    @respx.mock
    def test_request_confirm_dismiss(self, client):
        respx.post(f"{SERVER}/api/workflow-requests/req-2/confirm").mock(
            httpx.Response(200, json={"id": "req-2", "status": "dismissed", "summary": "Dismissed."})
        )
        res = client.workflows.request_confirm("req-2", False)
        assert res.status == "dismissed"

    @respx.mock
    def test_stats(self, client):
        respx.get(f"{SERVER}/api/workflows/stats").mock(
            httpx.Response(200, json={"total_workflows": 3, "active_workflows": 1})
        )
        s = client.workflows.stats()
        assert s.total_workflows == 3

    @respx.mock
    def test_catalog_basic(self, client):
        respx.get(f"{SERVER}/api/workflows/catalog").mock(
            httpx.Response(200, json={"signals": [], "actions": [], "integrations": []})
        )
        cat = client.workflows.catalog()
        assert cat.signals == [] and cat.actions == [] and cat.integrations == []

    @respx.mock
    def test_catalog_full_fields(self, client):
        """Catalog exposes custom_blocks, slack_channels, slack_users, trigger_variables."""
        respx.get(f"{SERVER}/api/workflows/catalog").mock(
            httpx.Response(200, json={
                "signals": [], "actions": [], "integrations": [],
                "custom_blocks": [{"id": "cb-1", "name": "Custom"}],
                "slack_channels": [{"id": "C1", "name": "general"}],
                "slack_users": [{"id": "U1", "name": "alice"}],
                "trigger_variables": {"k8s.pod_status": ["incident.title"]},
            })
        )
        cat = client.workflows.catalog()
        assert cat.custom_blocks[0]["id"] == "cb-1"
        assert cat.slack_channels[0]["id"] == "C1"
        assert cat.slack_users[0]["id"] == "U1"
        assert cat.trigger_variables == {"k8s.pod_status": ["incident.title"]}

    @respx.mock
    def test_integrations(self, client):
        respx.get(f"{SERVER}/api/workflows/integrations/status").mock(
            httpx.Response(200, json=[{"id": "slack", "name": "Slack", "connected": True}])
        )
        ints = client.workflows.integrations()
        assert ints[0].connected is True

    @respx.mock
    def test_suggestions(self, client):
        respx.get(f"{SERVER}/api/workflows/suggestions").mock(httpx.Response(200, json=[]))
        assert client.workflows.suggestions() == []

    @respx.mock
    def test_test_execution(self, client):
        respx.post(f"{SERVER}/api/workflows/wf-1/test").mock(
            httpx.Response(200, json={"id": "exec-1", "status": "running"})
        )
        ex = client.workflows.test("wf-1")
        assert ex.id == "exec-1"

    @respx.mock
    def test_executions_list(self, client):
        respx.get(f"{SERVER}/api/workflows/wf-1/executions").mock(
            httpx.Response(200, json={"executions": [], "total": 0, "page": 1, "page_size": 20})
        )
        ex_list = client.workflows.executions("wf-1")
        assert ex_list.total == 0


# ---------------------------------------------------------------------------
# Executions
# ---------------------------------------------------------------------------


class TestExecutions:
    @respx.mock
    def test_get(self, client):
        respx.get(f"{SERVER}/api/workflow-executions/exec-1").mock(
            httpx.Response(200, json={"id": "exec-1", "status": "completed"})
        )
        ex = client.executions.get("exec-1")
        assert ex.status == "completed"

    @respx.mock
    def test_cancel(self, client):
        respx.post(f"{SERVER}/api/workflow-executions/exec-1/cancel").mock(
            httpx.Response(200, json={"status": "cancelled"})
        )
        client.executions.cancel("exec-1")

    @respx.mock
    def test_cancel_unknown_raises_not_found(self, client):
        """Server now returns 404 for unknown execution IDs (was bug #6)."""
        respx.post(f"{SERVER}/api/workflow-executions/missing/cancel").mock(
            httpx.Response(404, text="Execution not found")
        )
        with pytest.raises(NotFoundError):
            client.executions.cancel("missing")

    @respx.mock
    def test_wait_completes(self, client):
        respx.get(f"{SERVER}/api/workflow-executions/exec-1").mock(
            httpx.Response(200, json={"id": "exec-1", "status": "completed"})
        )
        ex = client.executions.wait("exec-1", poll_interval=0.01, timeout=2.0)
        assert ex.status == "completed"

    @respx.mock
    def test_wait_times_out(self, client):
        respx.get(f"{SERVER}/api/workflow-executions/exec-1").mock(
            httpx.Response(200, json={"id": "exec-1", "status": "running"})
        )
        with pytest.raises(TimeoutError):
            client.executions.wait("exec-1", poll_interval=0.01, timeout=0.1)


# ---------------------------------------------------------------------------
# Approvals
# ---------------------------------------------------------------------------


class TestApprovals:
    @respx.mock
    def test_list_pending_basic(self, client):
        respx.get(f"{SERVER}/api/workflow-approvals/pending").mock(
            httpx.Response(200, json=[{"id": "a-1"}])
        )
        out = client.approvals.list_pending()
        assert out[0].id == "a-1"

    @respx.mock
    def test_list_pending_full_fields(self, client):
        """Approval exposes approval_responses, approval_rules, slack_channel_id, slack_message_ts."""
        respx.get(f"{SERVER}/api/workflow-approvals/pending").mock(
            httpx.Response(200, json=[{
                "id": "a-1", "status": "pending",
                "approval_responses": [{"user": "u1", "decision": "approve"}],
                "approval_rules": [{"entries": [{"type": "user", "id": "u1"}]}],
                "slack_channel_id": "C123",
                "slack_message_ts": "1700000000.000",
            }])
        )
        a = client.approvals.list_pending()[0]
        assert a.approval_responses == [{"user": "u1", "decision": "approve"}]
        assert a.approval_rules == [{"entries": [{"type": "user", "id": "u1"}]}]
        assert a.slack_channel_id == "C123"
        assert a.slack_message_ts == "1700000000.000"

    @respx.mock
    def test_approve(self, client):
        respx.post(f"{SERVER}/api/workflow-approvals/a-1/approve").mock(httpx.Response(204, text=""))
        client.approvals.approve("a-1", justification="lgtm")

    @respx.mock
    def test_reject(self, client):
        respx.post(f"{SERVER}/api/workflow-approvals/a-1/reject").mock(httpx.Response(204, text=""))
        client.approvals.reject("a-1")


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class TestRequests:
    @respx.mock
    def test_list_unfiltered_returns_all(self, client):
        """list() returns *all* statuses, including pending/executing/completed/failed."""
        respx.get(f"{SERVER}/api/workflow-requests").mock(
            httpx.Response(200, json={"requests": [
                {"id": "r-1", "status": "no_workflow"},
                {"id": "r-2", "status": "completed"},
                {"id": "r-3", "status": "pending"},
                {"id": "r-4", "status": "executing"},
                {"id": "r-5", "status": "failed"},
            ]})
        )
        out = client.requests.list()
        assert len(out) == 5
        assert {r.status for r in out} == {"no_workflow", "completed", "pending", "executing", "failed"}

    @respx.mock
    def test_list_with_status_filter(self, client):
        respx.get(f"{SERVER}/api/workflow-requests").mock(
            httpx.Response(200, json={"requests": [
                {"id": "r-1", "status": "no_workflow"},
                {"id": "r-2", "status": "completed"},
            ]})
        )
        out = client.requests.list(status="completed")
        assert len(out) == 1 and out[0].status == "completed"

    @respx.mock
    def test_list_handles_bare_array(self, client):
        """Some server versions return a bare list instead of {"requests": [...]}."""
        respx.get(f"{SERVER}/api/workflow-requests").mock(
            httpx.Response(200, json=[{"id": "r-1", "status": "no_workflow"}])
        )
        out = client.requests.list()
        assert len(out) == 1

    @respx.mock
    def test_approve(self, client):
        respx.post(f"{SERVER}/api/workflow-requests/r-1/approve").mock(httpx.Response(204, text=""))
        client.requests.approve("r-1")

    @respx.mock
    def test_reject(self, client):
        respx.post(f"{SERVER}/api/workflow-requests/r-1/reject").mock(httpx.Response(204, text=""))
        client.requests.reject("r-1")


# ---------------------------------------------------------------------------
# Async client — verifies the async surface mirrors sync
# ---------------------------------------------------------------------------


class TestAsyncClient:
    @pytest.mark.asyncio
    @respx.mock
    async def test_async_list(self):
        respx.get(f"{SERVER}/api/workflows").mock(httpx.Response(200, json=[]))
        async with AsyncKestrelClient(server=SERVER, api_key=API_KEY) as c:
            out = await c.workflows.list()
            assert out == []

    @pytest.mark.asyncio
    @respx.mock
    async def test_async_requests_list_unfiltered(self):
        respx.get(f"{SERVER}/api/workflow-requests").mock(
            httpx.Response(200, json={"requests": [
                {"id": "r-1", "status": "no_workflow"},
                {"id": "r-2", "status": "completed"},
            ]})
        )
        async with AsyncKestrelClient(server=SERVER, api_key=API_KEY) as c:
            out = await c.requests.list()
            assert len(out) == 2


# ---------------------------------------------------------------------------
# Builder DSL — pure offline, no HTTP
# ---------------------------------------------------------------------------


class TestBuilderDSL:
    def test_simple_trigger_and_action(self):
        wf = (
            Workflow("simple")
            .trigger(Trigger.k8s_pod_status().reasons("CrashLoopBackOff"))
            .then(Action.kestrel_trigger_rca())
        )
        d, t = wf.build()
        assert len(d["nodes"]) == 2
        assert len(d["edges"]) == 1
        assert t["source"] == "kubernetes"

    def test_trigger_filters_compose(self):
        t = Trigger.k8s_pod_status().reasons("OOM").cluster("c1").namespace("ns1")
        wf = Workflow("x").trigger(t)
        _, tc = wf.build()
        assert tc["source"] == "kubernetes"
        f = tc["signals"][0]["filters"]
        assert f["reasons"] == ["OOM"]
        assert f["cluster_ids"] == ["c1"]
        assert f["namespaces"] == ["ns1"]

    def test_rollouts_and_flux_actions(self):
        """Argo Rollouts and Flux CD factories emit the right integration,
        action IDs, and config keys."""
        promote = Action.rollouts_promote().cluster_id("c1").rollout_name("my-app").ns("prod").full()
        assert promote._integration == "argo-rollouts"
        assert promote._action == "rollouts-promote"
        assert promote._config["cluster_id"] == "c1"
        assert promote._config["rollout_name"] == "my-app"
        assert promote._config["namespace"] == "prod"
        assert promote._config["full"] is True

        undo = Action.rollouts_undo().rollout_name("my-app").revision(3)
        assert undo._action == "rollouts-undo"
        assert undo._config["revision"] == 3

        wait = Action.rollouts_wait_healthy().rollout_name("my-app").wait_timeout_seconds(120)
        assert wait._config["wait_timeout_seconds"] == 120

        reconcile = (
            Action.flux_reconcile()
            .cluster_id("c1")
            .resource_kind("HelmRelease")
            .resource_name("podinfo")
            .ns("flux-system")
            .with_source()
        )
        assert reconcile._integration == "fluxcd"
        assert reconcile._action == "flux-reconcile"
        assert reconcile._config["resource_kind"] == "HelmRelease"
        assert reconcile._config["resource_name"] == "podinfo"
        assert reconcile._config["with_source"] is True

        for factory, action_id in [
            (Action.rollouts_abort, "rollouts-abort"),
            (Action.rollouts_retry, "rollouts-retry"),
            (Action.rollouts_pause, "rollouts-pause"),
            (Action.rollouts_resume, "rollouts-resume"),
            (Action.rollouts_restart, "rollouts-restart"),
            (Action.rollouts_get_status, "rollouts-get-status"),
            (Action.flux_suspend, "flux-suspend"),
            (Action.flux_resume, "flux-resume"),
            (Action.flux_get_status, "flux-get-status"),
            (Action.flux_wait_ready, "flux-wait-ready"),
            (Action.flux_get_events, "flux-get-events"),
        ]:
            assert factory()._action == action_id

    def test_rollouts_and_flux_request_triggers(self):
        _, t = Workflow("r").trigger(Trigger.request_argo_rollouts()).build()
        assert t["source"] == "request"
        assert t["signals"][0]["filters"]["request_categories"] == ["argo-rollouts"]

        _, t = Workflow("f").trigger(Trigger.request_fluxcd()).build()
        assert t["signals"][0]["filters"]["request_categories"] == ["fluxcd"]

    def test_karpenter_actions(self):
        """Karpenter factories emit the right integration, action IDs, and
        config keys."""
        scale = (
            Action.karpenter_scale_nodepool()
            .cluster_id("c1")
            .nodepool_name("default")
            .cpu_limit("200")
            .memory_limit("400Gi")
        )
        assert scale._integration == "karpenter"
        assert scale._action == "karpenter-scale-nodepool"
        assert scale._config["cluster_id"] == "c1"
        assert scale._config["nodepool_name"] == "default"
        assert scale._config["cpu_limit"] == "200"
        assert scale._config["memory_limit"] == "400Gi"

        disruption = (
            Action.karpenter_set_disruption()
            .nodepool_name("default")
            .consolidation_policy("WhenEmpty")
            .consolidate_after("5m")
        )
        assert disruption._action == "karpenter-set-disruption"
        assert disruption._config["consolidation_policy"] == "WhenEmpty"
        assert disruption._config["consolidate_after"] == "5m"

        apply = Action.karpenter_apply_nodepool().nodepool_spec("apiVersion: karpenter.sh/v1\nkind: NodePool")
        assert apply._action == "karpenter-apply-nodepool"
        assert apply._config["nodepool_spec"].startswith("apiVersion: karpenter.sh/v1")

        delete = Action.karpenter_delete_nodeclaim().nodeclaim_name("default-abc12")
        assert delete._action == "karpenter-delete-nodeclaim"
        assert delete._config["nodeclaim_name"] == "default-abc12"

        for factory, action_id in [
            (Action.karpenter_list_nodepools, "karpenter-list-nodepools"),
            (Action.karpenter_get_nodepool_status, "karpenter-get-nodepool-status"),
            (Action.karpenter_list_nodeclaims, "karpenter-list-nodeclaims"),
        ]:
            action = factory()
            assert action._integration == "karpenter"
            assert action._action == action_id

    def test_karpenter_triggers(self):
        _, t = Workflow("k").trigger(Trigger.request_karpenter()).build()
        assert t["source"] == "request"
        assert t["signals"][0]["filters"]["request_categories"] == ["karpenter"]

        for factory, signal_type in [
            (Trigger.karpenter_node_provisioning_failed, "nodeclaim.provisioning_failed"),
            (Trigger.karpenter_node_interrupted, "node.interrupted"),
            (Trigger.karpenter_nodepool_limit_reached, "nodepool.limit_reached"),
            (Trigger.karpenter_any, "any"),
        ]:
            _, t = Workflow("k").trigger(factory().cluster("c1")).build()
            assert t["source"] == "karpenter"
            assert t["signals"][0]["signal_type"] == signal_type
            assert t["signals"][0]["filters"]["cluster_ids"] == ["c1"]

    def test_kyverno_actions(self):
        """Kyverno factories emit the right integration, action IDs, and
        config keys."""
        enforcement = (
            Action.kyverno_set_enforcement()
            .cluster_id("c1")
            .policy_name("disallow-privileged-containers")
            .enforcement_action("Enforce")
        )
        assert enforcement._integration == "kyverno"
        assert enforcement._action == "kyverno-set-enforcement"
        assert enforcement._config["cluster_id"] == "c1"
        assert enforcement._config["policy_name"] == "disallow-privileged-containers"
        assert enforcement._config["enforcement_action"] == "Enforce"

        violations = (
            Action.kyverno_list_violations()
            .cluster_id("c1")
            .ns("payments")
            .policy_filter("require-labels")
            .severity("high")
            .result_filter("fail,warn,error")
            .max_results(50)
        )
        assert violations._action == "kyverno-list-violations"
        assert violations._config["namespace"] == "payments"
        assert violations._config["policy"] == "require-labels"
        assert violations._config["severity"] == "high"
        assert violations._config["result"] == "fail,warn,error"
        assert violations._config["max_results"] == 50

        apply = Action.kyverno_apply_policy().cluster_id("c1").policy_spec(
            "apiVersion: kyverno.io/v1\nkind: ClusterPolicy"
        )
        assert apply._action == "kyverno-apply-policy"
        assert apply._config["policy_spec"].startswith("apiVersion: kyverno.io/v1")

        delete = Action.kyverno_delete_policy().cluster_id("c1").policy_name("require-labels").ns("payments")
        assert delete._action == "kyverno-delete-policy"
        assert delete._config["policy_name"] == "require-labels"
        assert delete._config["namespace"] == "payments"

        investigate = (
            Action.kyverno_investigate()
            .cluster_id("c1")
            .query("why was this deployment blocked?")
            .max_iterations(5)
        )
        assert investigate._action == "kyverno-investigate"
        assert investigate._integration == "kyverno"
        assert investigate._config["cluster_id"] == "c1"
        assert investigate._config["query"] == "why was this deployment blocked?"
        assert investigate._config["max_iterations"] == 5

        for factory, action_id in [
            (Action.kyverno_list_policies, "kyverno-list-policies"),
            (Action.kyverno_get_policy, "kyverno-get-policy"),
        ]:
            action = factory()
            assert action._integration == "kyverno"
            assert action._action == action_id

    def test_kyverno_triggers(self):
        _, t = Workflow("k").trigger(Trigger.request_kyverno()).build()
        assert t["source"] == "request"
        assert t["signals"][0]["filters"]["request_categories"] == ["kyverno"]

        for factory, signal_type in [
            (Trigger.kyverno_policy_violation, "policy.violation"),
            (Trigger.kyverno_admission_blocked, "policy.admission_blocked"),
            (Trigger.kyverno_any, "any"),
        ]:
            _, t = (
                Workflow("k")
                .trigger(
                    factory()
                    .cluster("c1")
                    .namespace("payments")
                    .kyverno_policies("disallow-privileged-containers")
                    .kyverno_severities("critical", "high")
                )
                .build()
            )
            assert t["source"] == "kyverno"
            assert t["signals"][0]["signal_type"] == signal_type
            filters = t["signals"][0]["filters"]
            assert filters["cluster_ids"] == ["c1"]
            assert filters["namespaces"] == ["payments"]
            assert filters["kyverno_policies"] == ["disallow-privileged-containers"]
            assert filters["kyverno_severities"] == ["critical", "high"]

    def test_trivy_actions(self):
        """Trivy factories emit the right integration, action IDs, and
        config keys."""
        vulns = (
            Action.trivy_list_vulnerabilities()
            .cluster_id("c1")
            .ns("payments")
            .workload("deployment/nginx")
            .severity("critical,high")
            .fixed_only()
            .max_results(50)
        )
        assert vulns._integration == "trivy"
        assert vulns._action == "trivy-list-vulnerabilities"
        assert vulns._config["cluster_id"] == "c1"
        assert vulns._config["namespace"] == "payments"
        assert vulns._config["workload"] == "deployment/nginx"
        assert vulns._config["severity"] == "critical,high"
        assert vulns._config["fixed_only"] is True
        assert vulns._config["max_results"] == 50

        report = (
            Action.trivy_get_vulnerability_report()
            .cluster_id("c1")
            .ns("payments")
            .workload("deployment/nginx")
        )
        assert report._action == "trivy-get-vulnerability-report"
        assert report._config["workload"] == "deployment/nginx"
        assert report._config["namespace"] == "payments"

        misconfigs = (
            Action.trivy_list_misconfigurations()
            .cluster_id("c1")
            .resource_kind("Deployment")
            .report_kind("config-audit")
        )
        assert misconfigs._action == "trivy-list-misconfigurations"
        assert misconfigs._config["resource_kind"] == "Deployment"
        assert misconfigs._config["report_kind"] == "config-audit"

        compliance = Action.trivy_get_compliance_report().cluster_id("c1").report_name("cis")
        assert compliance._action == "trivy-get-compliance-report"
        assert compliance._config["report_name"] == "cis"

        rescan = Action.trivy_rescan_workload().cluster_id("c1").ns("payments").workload("nginx")
        assert rescan._action == "trivy-rescan-workload"
        assert rescan._config["workload"] == "nginx"
        assert rescan._config["namespace"] == "payments"

        investigate = (
            Action.trivy_investigate()
            .cluster_id("c1")
            .query("which workloads ship critical CVEs with fixes available?")
            .max_iterations(5)
        )
        assert investigate._action == "trivy-investigate"
        assert investigate._integration == "trivy"
        assert investigate._config["query"].startswith("which workloads")
        assert investigate._config["max_iterations"] == 5

        secrets = Action.trivy_list_exposed_secrets().cluster_id("c1")
        assert secrets._integration == "trivy"
        assert secrets._action == "trivy-list-exposed-secrets"

    def test_trivy_triggers(self):
        _, t = Workflow("t").trigger(Trigger.request_trivy()).build()
        assert t["source"] == "request"
        assert t["signals"][0]["filters"]["request_categories"] == ["trivy"]

        for factory, signal_type in [
            (Trigger.trivy_vulnerability_detected, "vulnerability.detected"),
            (Trigger.trivy_exposed_secret_detected, "secret.exposed"),
            (Trigger.trivy_config_audit_failed, "configaudit.failed"),
            (Trigger.trivy_compliance_failed, "compliance.failed"),
            (Trigger.trivy_any, "any"),
        ]:
            _, t = (
                Workflow("t")
                .trigger(
                    factory()
                    .cluster("c1")
                    .namespace("payments")
                    .trivy_severities("critical", "high")
                    .trivy_resource_kinds("Deployment")
                )
                .build()
            )
            assert t["source"] == "trivy"
            assert t["signals"][0]["signal_type"] == signal_type
            filters = t["signals"][0]["filters"]
            assert filters["cluster_ids"] == ["c1"]
            assert filters["namespaces"] == ["payments"]
            assert filters["trivy_severities"] == ["critical", "high"]
            assert filters["trivy_resource_kinds"] == ["Deployment"]

    def test_terraform_actions(self):
        """Terraform Cloud factories emit the right integration, action IDs,
        and config keys."""
        create = (
            Action.terraform_create_run()
            .workspace("prod-vpc")
            .run_message("Queued by Kestrel")
            .auto_apply()
        )
        assert create._integration == "terraform"
        assert create._action == "terraform-create-run"
        assert create._config["workspace"] == "prod-vpc"
        assert create._config["message"] == "Queued by Kestrel"
        assert create._config["auto_apply"] is True

        apply = Action.terraform_apply_run().workspace("prod-vpc").run_id("run-abc").comment("ok")
        assert apply._action == "terraform-apply-run"
        assert apply._config["run_id"] == "run-abc"
        assert apply._config["comment"] == "ok"

        setvar = (
            Action.terraform_set_variable()
            .workspace("prod-vpc")
            .key("instance_count")
            .value("3")
            .category("terraform")
            .hcl(False)
            .sensitive()
        )
        assert setvar._action == "terraform-set-variable"
        assert setvar._config["key"] == "instance_count"
        assert setvar._config["value"] == "3"
        assert setvar._config["category"] == "terraform"
        assert setvar._config["hcl"] is False
        assert setvar._config["sensitive"] is True

        wait = Action.terraform_wait_for_run().workspace("w").run_id("run-1").timeout_minutes(30)
        assert wait._action == "terraform-wait-for-run"
        assert wait._config["timeout_minutes"] == 30

        lock = Action.terraform_lock_workspace().workspace("w").reason("freeze")
        assert lock._config["reason"] == "freeze"

        investigate = Action.terraform_investigate().query("why?").workspace("w").max_iterations(5)
        assert investigate._action == "terraform-investigate"
        assert investigate._config["query"] == "why?"
        assert investigate._config["max_iterations"] == 5

        for factory, action_id in [
            (Action.terraform_list_workspaces, "terraform-list-workspaces"),
            (Action.terraform_get_workspace, "terraform-get-workspace"),
            (Action.terraform_unlock_workspace, "terraform-unlock-workspace"),
            (Action.terraform_force_unlock_workspace, "terraform-force-unlock-workspace"),
            (Action.terraform_list_runs, "terraform-list-runs"),
            (Action.terraform_get_run, "terraform-get-run"),
            (Action.terraform_create_destroy_run, "terraform-create-destroy-run"),
            (Action.terraform_discard_run, "terraform-discard-run"),
            (Action.terraform_cancel_run, "terraform-cancel-run"),
            (Action.terraform_get_state_outputs, "terraform-get-state-outputs"),
            (Action.terraform_list_variables, "terraform-list-variables"),
            (Action.terraform_get_drift, "terraform-get-drift"),
        ]:
            assert factory()._action == action_id

    def test_terraform_triggers(self):
        t = (
            Trigger.terraform_run_errored()
            .terraform_workspaces("prod-vpc", "prod-eks")
            .terraform_run_statuses("errored")
        )
        _, tc = Workflow("t").trigger(t).build()
        assert tc["source"] == "terraform"
        f = tc["signals"][0]["filters"]
        assert f["terraform_event_types"] == ["run:errored"]
        assert f["terraform_workspaces"] == ["prod-vpc", "prod-eks"]
        assert f["terraform_run_statuses"] == ["errored"]

        for factory, event in [
            (Trigger.terraform_run_created, "run:created"),
            (Trigger.terraform_run_needs_attention, "run:needs_attention"),
            (Trigger.terraform_run_completed, "run:completed"),
            (Trigger.terraform_drift_detected, "assessment:drifted"),
            (Trigger.terraform_check_failed, "assessment:check_failure"),
        ]:
            trig = factory()
            assert trig._filters["terraform_event_types"] == [event]

        _, tc = Workflow("any").trigger(Trigger.terraform_any()).build()
        assert tc["source"] == "terraform"

        _, tc = Workflow("req").trigger(Trigger.request_terraform()).build()
        assert tc["source"] == "request"
        assert tc["signals"][0]["filters"]["request_categories"] == ["terraform"]

    def test_pulumi_actions(self):
        """Pulumi Cloud factories emit the right integration, action IDs, and
        config keys."""
        run = (
            Action.pulumi_run_deployment()
            .stack("my-project/prod")
            .operation("update")
        )
        assert run._integration == "pulumi"
        assert run._action == "pulumi-run-deployment"
        assert run._config["stack"] == "my-project/prod"
        assert run._config["operation"] == "update"

        wait = (
            Action.pulumi_wait_for_deployment()
            .stack("{{signal.stack}}")
            .deployment_id("{{step_outputs.action-1.deployment_id}}")
            .timeout_minutes(45)
            .poll_interval_seconds(20)
        )
        assert wait._action == "pulumi-wait-for-deployment"
        assert wait._config["deployment_id"] == "{{step_outputs.action-1.deployment_id}}"
        assert wait._config["timeout_minutes"] == 45
        assert wait._config["poll_interval_seconds"] == 20

        upd = Action.pulumi_get_update().stack("p/s").update_version("42")
        assert upd._action == "pulumi-get-update"
        assert upd._config["version"] == "42"

        tag = (
            Action.pulumi_set_stack_tag()
            .stack("p/s")
            .tag_name("kestrel:quarantined")
            .tag_value("true")
        )
        assert tag._action == "pulumi-set-stack-tag"
        assert tag._config["tag_name"] == "kestrel:quarantined"
        assert tag._config["tag_value"] == "true"

        investigate = Action.pulumi_investigate().query("why did the update fail?").stack("p/s").max_iterations(5)
        assert investigate._action == "pulumi-investigate"
        assert investigate._config["query"] == "why did the update fail?"
        assert investigate._config["max_iterations"] == 5

        for factory, action_id in [
            (Action.pulumi_list_stacks, "pulumi-list-stacks"),
            (Action.pulumi_get_stack, "pulumi-get-stack"),
            (Action.pulumi_list_updates, "pulumi-list-updates"),
            (Action.pulumi_get_deployment, "pulumi-get-deployment"),
            (Action.pulumi_cancel_deployment, "pulumi-cancel-deployment"),
            (Action.pulumi_pause_deployments, "pulumi-pause-deployments"),
            (Action.pulumi_resume_deployments, "pulumi-resume-deployments"),
            (Action.pulumi_get_stack_outputs, "pulumi-get-stack-outputs"),
            (Action.pulumi_get_drift, "pulumi-get-drift"),
            (Action.pulumi_delete_stack_tag, "pulumi-delete-stack-tag"),
        ]:
            assert factory()._action == action_id

    def test_pulumi_triggers(self):
        t = (
            Trigger.pulumi_update_failed()
            .pulumi_stacks("my-project/prod")
            .pulumi_projects("my-project")
        )
        _, tc = Workflow("p").trigger(t).build()
        assert tc["source"] == "pulumi"
        f = tc["signals"][0]["filters"]
        assert f["pulumi_event_types"] == ["update_failed"]
        assert f["pulumi_stacks"] == ["my-project/prod"]
        assert f["pulumi_projects"] == ["my-project"]

        for factory, event in [
            (Trigger.pulumi_update_succeeded, "update_succeeded"),
            (Trigger.pulumi_preview_failed, "preview_failed"),
            (Trigger.pulumi_destroy_succeeded, "destroy_succeeded"),
            (Trigger.pulumi_deployment_started, "deployment_started"),
            (Trigger.pulumi_deployment_succeeded, "deployment_succeeded"),
            (Trigger.pulumi_deployment_failed, "deployment_failed"),
            (Trigger.pulumi_drift_detected, "drift_detected"),
            (Trigger.pulumi_policy_violation, "policy_violation_mandatory"),
            (Trigger.pulumi_stack_created, "stack_created"),
            (Trigger.pulumi_stack_deleted, "stack_deleted"),
        ]:
            trig = factory()
            assert trig._filters["pulumi_event_types"] == [event]

        _, tc = Workflow("any").trigger(Trigger.pulumi_any()).build()
        assert tc["source"] == "pulumi"

        _, tc = Workflow("req").trigger(Trigger.request_pulumi()).build()
        assert tc["source"] == "request"
        assert tc["signals"][0]["filters"]["request_categories"] == ["pulumi"]

    def test_vault_actions(self):
        """Vault factories emit the right integration, action IDs, and
        config keys."""
        read = (
            Action.vault_read_secret()
            .mount("secret/")
            .path("app/prod/db")
            .secret_key("password")
            .secret_version(3)
        )
        assert read._integration == "vault"
        assert read._action == "vault-read-secret"
        assert read._config["mount"] == "secret/"
        assert read._config["path"] == "app/prod/db"
        assert read._config["key"] == "password"
        assert read._config["version"] == 3

        write = (
            Action.vault_write_secret()
            .mount("secret/")
            .path("app/prod/db")
            .secret_data('{"password": "{{step_outputs.action-1.value}}"}')
        )
        assert write._action == "vault-write-secret"
        assert write._config["data"] == '{"password": "{{step_outputs.action-1.value}}"}'

        delete = Action.vault_delete_secret().mount("secret/").path("app/old").destroy()
        assert delete._action == "vault-delete-secret"
        assert delete._config["destroy"] is True

        rotate = Action.vault_rotate_static_role().mount("database/").role("app-db")
        assert rotate._action == "vault-rotate-static-role"
        assert rotate._config["role"] == "app-db"

        policy = (
            Action.vault_write_policy()
            .name("app-read")
            .policy_hcl('path "secret/data/app/*" {\n  capabilities = ["read"]\n}')
        )
        assert policy._action == "vault-write-policy"
        assert policy._config["name"] == "app-read"
        assert "capabilities" in policy._config["policy"]

        renew = Action.vault_renew_lease().lease_id("database/creds/app/abc").increment(3600)
        assert renew._action == "vault-renew-lease"
        assert renew._config["lease_id"] == "database/creds/app/abc"
        assert renew._config["increment"] == 3600

        revoke_tok = Action.vault_revoke_token_accessor().accessor("hmac.abc123")
        assert revoke_tok._action == "vault-revoke-token-accessor"
        assert revoke_tok._config["accessor"] == "hmac.abc123"

        investigate = (
            Action.vault_investigate()
            .query("why is this secret stale?")
            .mount("secret/")
            .max_iterations(5)
        )
        assert investigate._action == "vault-investigate"
        assert investigate._config["query"] == "why is this secret stale?"
        assert investigate._config["max_iterations"] == 5

        for factory, action_id in [
            (Action.vault_list_secrets, "vault-list-secrets"),
            (Action.vault_get_secret_metadata, "vault-get-secret-metadata"),
            (Action.vault_list_mounts, "vault-list-mounts"),
            (Action.vault_list_policies, "vault-list-policies"),
            (Action.vault_read_policy, "vault-read-policy"),
            (Action.vault_list_auth_methods, "vault-list-auth-methods"),
            (Action.vault_list_leases, "vault-list-leases"),
            (Action.vault_revoke_lease, "vault-revoke-lease"),
            (Action.vault_get_health, "vault-get-health"),
            (Action.vault_list_token_accessors, "vault-list-token-accessors"),
        ]:
            assert factory()._action == action_id
            assert factory()._integration == "vault"

    def test_vault_triggers(self):
        t = (
            Trigger.vault_secret_stale()
            .vault_mounts("secret/")
            .vault_secret_paths("app/prod")
            .vault_secret_max_age_days(60)
            .vault_poll_interval("15m")
        )
        _, tc = Workflow("v").trigger(t).build()
        assert tc["source"] == "vault"
        f = tc["signals"][0]["filters"]
        assert f["vault_event_types"] == ["secret.stale"]
        assert f["vault_mounts"] == ["secret/"]
        assert f["vault_secret_paths"] == ["app/prod"]
        assert f["vault_secret_max_age_days"] == 60
        assert f["vault_poll_interval"] == "15m"

        for factory, event in [
            (Trigger.vault_sealed, "seal.sealed"),
            (Trigger.vault_unsealed, "seal.unsealed"),
            (Trigger.vault_health_degraded, "health.degraded"),
            (Trigger.vault_secret_version_created, "secret.version_created"),
            (Trigger.vault_policy_created, "policy.created"),
            (Trigger.vault_policy_deleted, "policy.deleted"),
            (Trigger.vault_auth_method_enabled, "auth_method.enabled"),
            (Trigger.vault_auth_method_disabled, "auth_method.disabled"),
        ]:
            trig = factory()
            assert trig._filters["vault_event_types"] == [event]

        _, tc = Workflow("any").trigger(Trigger.vault_any()).build()
        assert tc["source"] == "vault"

        _, tc = Workflow("req").trigger(Trigger.request_vault()).build()
        assert tc["source"] == "request"
        assert tc["signals"][0]["filters"]["request_categories"] == ["vault"]

    def test_infisical_actions(self):
        """Infisical factories emit the right integration, action IDs, and
        config keys."""
        get = (
            Action.infisical_get_secret()
            .infisical_project("backend")
            .environment("prod")
            .secret_path("/api")
            .secret_key("DB_PASSWORD")
        )
        assert get._integration == "infisical"
        assert get._action == "infisical-get-secret"
        assert get._config["project"] == "backend"
        assert get._config["environment"] == "prod"
        assert get._config["secret_path"] == "/api"
        assert get._config["key"] == "DB_PASSWORD"

        create = (
            Action.infisical_create_secret()
            .infisical_project("backend")
            .environment("prod")
            .secret_key("API_KEY")
            .secret_value("{{step_outputs.action-1.value}}")
            .comment("rotated by Kestrel")
        )
        assert create._action == "infisical-create-secret"
        assert create._config["value"] == "{{step_outputs.action-1.value}}"
        assert create._config["comment"] == "rotated by Kestrel"

        folder = (
            Action.infisical_create_folder()
            .infisical_project("backend")
            .environment("prod")
            .path("/")
            .name("payments")
        )
        assert folder._action == "infisical-create-folder"
        assert folder._config["name"] == "payments"

        sync = Action.infisical_trigger_secret_sync().sync_id("{{signal.sync_id}}")
        assert sync._action == "infisical-trigger-secret-sync"
        assert sync._config["sync_id"] == "{{signal.sync_id}}"

        audit = (
            Action.infisical_get_audit_logs()
            .infisical_project("{{signal.project_id}}")
            .event_type("delete-secret")
            .limit(100)
        )
        assert audit._action == "infisical-get-audit-logs"
        assert audit._config["event_type"] == "delete-secret"
        assert audit._config["limit"] == 100

        investigate = (
            Action.infisical_investigate()
            .query("which syncs are failing?")
            .max_iterations(5)
        )
        assert investigate._action == "infisical-investigate"
        assert investigate._config["query"] == "which syncs are failing?"

        for factory, action_id in [
            (Action.infisical_update_secret, "infisical-update-secret"),
            (Action.infisical_delete_secret, "infisical-delete-secret"),
            (Action.infisical_list_secrets, "infisical-list-secrets"),
            (Action.infisical_list_projects, "infisical-list-projects"),
            (Action.infisical_list_environments, "infisical-list-environments"),
            (Action.infisical_list_folders, "infisical-list-folders"),
            (Action.infisical_list_secret_syncs, "infisical-list-secret-syncs"),
            (Action.infisical_list_approval_requests, "infisical-list-approval-requests"),
            (Action.infisical_list_identities, "infisical-list-identities"),
        ]:
            assert factory()._action == action_id
            assert factory()._integration == "infisical"

    def test_infisical_triggers(self):
        t = (
            Trigger.infisical_secret_updated()
            .infisical_projects("proj-id-1")
            .infisical_environments("prod")
            .infisical_secret_paths("/backend")
            .infisical_poll_interval("1m")
        )
        _, tc = Workflow("i").trigger(t).build()
        assert tc["source"] == "infisical"
        f = tc["signals"][0]["filters"]
        assert f["infisical_event_types"] == ["secret.updated"]
        assert f["infisical_project_ids"] == ["proj-id-1"]
        assert f["infisical_environments"] == ["prod"]
        assert f["infisical_secret_paths"] == ["/backend"]
        assert f["infisical_poll_interval"] == "1m"

        for factory, event in [
            (Trigger.infisical_secret_created, "secret.created"),
            (Trigger.infisical_secret_deleted, "secret.deleted"),
            (Trigger.infisical_approval_requested, "approval.requested"),
            (Trigger.infisical_secret_sync_failed, "sync.failed"),
            (Trigger.infisical_identity_created, "identity.created"),
        ]:
            trig = factory()
            assert trig._filters["infisical_event_types"] == [event]

        _, tc = Workflow("any").trigger(Trigger.infisical_any()).build()
        assert tc["source"] == "infisical"

        _, tc = Workflow("req").trigger(Trigger.request_infisical()).build()
        assert tc["source"] == "request"
        assert tc["signals"][0]["filters"]["request_categories"] == ["infisical"]

    def test_jenkins_actions_serialize(self):
        """Jenkins factories emit the right integration, action IDs, and
        config keys."""
        trigger = (
            Action.jenkins_trigger_build()
            .job("platform/deploy-api")
            .parameters("ENV=staging\nVERSION={{step_outputs.action-1.tag}}")
        )
        assert trigger._integration == "jenkins"
        assert trigger._action == "jenkins-trigger-build"
        assert trigger._config["job"] == "platform/deploy-api"
        assert "ENV=staging" in trigger._config["parameters"]

        wait = (
            Action.jenkins_wait_for_build()
            .job("platform/deploy-api")
            .build_number("{{signal.build_number}}")
            .timeout_minutes(45)
            .poll_interval_seconds(20)
        )
        assert wait._action == "jenkins-wait-for-build"
        assert wait._config["build_number"] == "{{signal.build_number}}"
        assert wait._config["timeout_minutes"] == 45
        assert wait._config["poll_interval_seconds"] == 20

        log = Action.jenkins_get_console_log().job("j").max_lines(500)
        assert log._action == "jenkins-get-console-log"
        assert log._config["max_lines"] == 500

        investigate = Action.jenkins_investigate().query("why did the build fail?").job("j").max_iterations(5)
        assert investigate._action == "jenkins-investigate"
        assert investigate._config["query"] == "why did the build fail?"
        assert investigate._config["max_iterations"] == 5

        for factory, action_id in [
            (Action.jenkins_get_build_status, "jenkins-get-build-status"),
            (Action.jenkins_stop_build, "jenkins-stop-build"),
        ]:
            assert factory()._action == action_id

    def test_jenkins_triggers(self):
        t = (
            Trigger.jenkins_build_failed()
            .jenkins_jobs("platform/deploy-api", "nightly")
        )
        _, tc = Workflow("j").trigger(t).build()
        assert tc["source"] == "jenkins"
        f = tc["signals"][0]["filters"]
        assert f["jenkins_event_types"] == ["build.completed"]
        assert f["jenkins_build_statuses"] == ["FAILURE"]
        assert f["jenkins_jobs"] == ["platform/deploy-api", "nightly"]

        for factory, event, statuses in [
            (Trigger.jenkins_build_unstable, "build.completed", ["UNSTABLE"]),
            (Trigger.jenkins_build_succeeded, "build.completed", ["SUCCESS"]),
            (Trigger.jenkins_build_completed, "build.completed", ["*"]),
        ]:
            trig = factory()
            assert trig._filters["jenkins_event_types"] == [event]
            assert trig._filters["jenkins_build_statuses"] == statuses

        started = Trigger.jenkins_build_started()
        assert started._filters["jenkins_event_types"] == ["build.started"]
        assert "jenkins_build_statuses" not in started._filters

        _, tc = Workflow("any").trigger(Trigger.jenkins_any()).build()
        assert tc["source"] == "jenkins"

        _, tc = Workflow("req").trigger(Trigger.request_jenkins()).build()
        assert tc["source"] == "request"
        assert tc["signals"][0]["filters"]["request_categories"] == ["jenkins"]

    def test_circleci_actions_serialize(self):
        """CircleCI factories emit the right integration, action IDs, and
        config keys."""
        trigger = (
            Action.circleci_trigger_pipeline()
            .project_slug("gh/org/repo")
            .branch("main")
            .parameters("deploy_env=staging")
        )
        assert trigger._integration == "circleci"
        assert trigger._action == "circleci-trigger-pipeline"
        assert trigger._config["project_slug"] == "gh/org/repo"
        assert trigger._config["branch"] == "main"

        tag_trigger = Action.circleci_trigger_pipeline().project_slug("gh/org/repo").tag("v1.2.3")
        assert tag_trigger._config["tag"] == "v1.2.3"

        wait = (
            Action.circleci_wait_for_pipeline()
            .project_slug("gh/org/repo")
            .pipeline_id("{{signal.pipeline_id}}")
            .timeout_minutes(45)
        )
        assert wait._action == "circleci-wait-for-pipeline"
        assert wait._config["pipeline_id"] == "{{signal.pipeline_id}}"
        assert wait._config["timeout_minutes"] == 45

        rerun = Action.circleci_rerun_workflow().workflow_id("{{signal.workflow_id}}").from_failed()
        assert rerun._action == "circleci-rerun-workflow"
        assert rerun._config["workflow_id"] == "{{signal.workflow_id}}"
        assert rerun._config["from_failed"] is True

        approve = Action.circleci_approve_job().workflow_id("wf-1").job_name("hold-deploy")
        assert approve._action == "circleci-approve-job"
        assert approve._config["job_name"] == "hold-deploy"

        tests = Action.circleci_get_job_tests().project_slug("gh/org/repo").job_number("{{signal.job_number}}")
        assert tests._action == "circleci-get-job-tests"
        assert tests._config["job_number"] == "{{signal.job_number}}"

        investigate = Action.circleci_investigate().query("why?").project_slug("gh/org/repo").max_iterations(5)
        assert investigate._action == "circleci-investigate"
        assert investigate._config["max_iterations"] == 5

        for factory, action_id in [
            (Action.circleci_get_workflow_status, "circleci-get-workflow-status"),
            (Action.circleci_cancel_workflow, "circleci-cancel-workflow"),
        ]:
            assert factory()._action == action_id

    def test_circleci_triggers(self):
        t = (
            Trigger.circleci_workflow_failed()
            .circleci_projects("gh/org/repo")
            .circleci_branches("main", "release/*")
        )
        _, tc = Workflow("c").trigger(t).build()
        assert tc["source"] == "circleci"
        f = tc["signals"][0]["filters"]
        assert f["circleci_event_types"] == ["workflow-completed"]
        assert f["circleci_statuses"] == ["failed", "error"]
        assert f["circleci_projects"] == ["gh/org/repo"]
        assert f["circleci_branches"] == ["main", "release/*"]

        for factory, event, statuses in [
            (Trigger.circleci_workflow_succeeded, "workflow-completed", ["success"]),
            (Trigger.circleci_workflow_completed, "workflow-completed", ["*"]),
            (Trigger.circleci_job_failed, "job-completed", ["failed"]),
        ]:
            trig = factory()
            assert trig._filters["circleci_event_types"] == [event]
            assert trig._filters["circleci_statuses"] == statuses

        _, tc = Workflow("any").trigger(Trigger.circleci_any()).build()
        assert tc["source"] == "circleci"

        _, tc = Workflow("req").trigger(Trigger.request_circleci()).build()
        assert tc["source"] == "request"
        assert tc["signals"][0]["filters"]["request_categories"] == ["circleci"]

    def test_sonarcloud_actions_serialize(self):
        """SonarCloud factories emit the right integration, action IDs, and
        config keys."""
        gate = Action.sonarcloud_get_quality_gate().sonar_project("my-org_api").branch("main")
        assert gate._integration == "sonarcloud"
        assert gate._action == "sonarcloud-get-quality-gate"
        assert gate._config["project"] == "my-org_api"
        assert gate._config["branch"] == "main"

        issues = (
            Action.sonarcloud_list_issues()
            .sonar_project("{{signal.project_key}}")
            .issue_types("VULNERABILITY", "BUG")
            .severities("BLOCKER", "CRITICAL")
            .new_code_only()
            .max_results(100)
        )
        assert issues._action == "sonarcloud-list-issues"
        assert issues._config["project"] == "{{signal.project_key}}"
        assert issues._config["types"] == ["VULNERABILITY", "BUG"]
        assert issues._config["severities"] == ["BLOCKER", "CRITICAL"]
        assert issues._config["new_code_only"] is True
        assert issues._config["max_results"] == 100

        hotspots = Action.sonarcloud_list_hotspots().sonar_project("my-org_api").hotspot_status("TO_REVIEW")
        assert hotspots._action == "sonarcloud-list-hotspots"
        assert hotspots._config["hotspot_status"] == "TO_REVIEW"

        measures = Action.sonarcloud_get_measures().sonar_project("my-org_api").metric_keys("bugs,coverage")
        assert measures._action == "sonarcloud-get-measures"
        assert measures._config["metric_keys"] == "bugs,coverage"

    def test_sonarcloud_triage_actions_serialize(self):
        """SonarCloud triage (write) factories emit the right action IDs and
        config keys."""
        transition = Action.sonarcloud_transition_issue().issue_key("{{item.key}}").transition("falsepositive")
        assert transition._integration == "sonarcloud"
        assert transition._action == "sonarcloud-transition-issue"
        assert transition._config["issue_key"] == "{{item.key}}"
        assert transition._config["transition"] == "falsepositive"

        assign = Action.sonarcloud_assign_issue().issue_key("ISSUE-1").assignee("alice")
        assert assign._action == "sonarcloud-assign-issue"
        assert assign._config["issue_key"] == "ISSUE-1"
        assert assign._config["assignee"] == "alice"

        comment = Action.sonarcloud_comment_issue().issue_key("ISSUE-1").comment("Triaged by Kestrel")
        assert comment._action == "sonarcloud-comment-issue"
        assert comment._config["comment"] == "Triaged by Kestrel"

        review = (
            Action.sonarcloud_review_hotspot()
            .hotspot_key("{{item.key}}")
            .hotspot_status("REVIEWED")
            .hotspot_resolution("SAFE")
            .comment("Reviewed via workflow")
        )
        assert review._action == "sonarcloud-review-hotspot"
        assert review._config["hotspot_key"] == "{{item.key}}"
        assert review._config["hotspot_status"] == "REVIEWED"
        assert review._config["resolution"] == "SAFE"
        assert review._config["comment"] == "Reviewed via workflow"

        investigate = (
            Action.sonarcloud_investigate()
            .query("why did the quality gate fail?")
            .max_iterations(5)
        )
        assert investigate._action == "sonarcloud-investigate"
        assert investigate._integration == "sonarcloud"
        assert investigate._config["query"] == "why did the quality gate fail?"
        assert investigate._config["max_iterations"] == 5

    def test_sonarcloud_triggers(self):
        t = (
            Trigger.sonarcloud_quality_gate_failed()
            .sonarcloud_projects("my-org_api")
            .sonarcloud_branches("main")
        )
        _, tc = Workflow("s").trigger(t).build()
        assert tc["source"] == "sonarcloud"
        f = tc["signals"][0]["filters"]
        assert f["sonarcloud_event_types"] == ["analysis.completed"]
        assert f["sonarcloud_quality_gate_statuses"] == ["ERROR"]
        assert f["sonarcloud_projects"] == ["my-org_api"]
        assert f["sonarcloud_branches"] == ["main"]

        for factory, event, statuses in [
            (Trigger.sonarcloud_quality_gate_passed, "analysis.completed", ["OK"]),
            (Trigger.sonarcloud_analysis_completed, "analysis.completed", ["*"]),
        ]:
            trig = factory()
            assert trig._filters["sonarcloud_event_types"] == [event]
            assert trig._filters["sonarcloud_quality_gate_statuses"] == statuses

        failed = Trigger.sonarcloud_analysis_failed()
        assert failed._filters["sonarcloud_event_types"] == ["analysis.failed"]
        assert "sonarcloud_quality_gate_statuses" not in failed._filters

        _, tc = Workflow("any").trigger(Trigger.sonarcloud_any()).build()
        assert tc["source"] == "sonarcloud"

        _, tc = Workflow("req").trigger(Trigger.request_sonarcloud()).build()
        assert tc["source"] == "request"
        assert tc["signals"][0]["filters"]["request_categories"] == ["sonarcloud"]

    def test_okta_actions_serialize(self):
        """Okta factories emit the right integration, action IDs, and config
        keys."""
        get_user = Action.okta_get_user().okta_user("{{signal.target_user}}")
        assert get_user._integration == "okta"
        assert get_user._action == "okta-get-user"
        assert get_user._config["user"] == "{{signal.target_user}}"

        users = (
            Action.okta_list_users()
            .query("alice")
            .okta_user_status("LOCKED_OUT")
            .max_results(100)
        )
        assert users._action == "okta-list-users"
        assert users._config["query"] == "alice"
        assert users._config["user_status"] == "LOCKED_OUT"
        assert users._config["max_results"] == 100

        log = (
            Action.okta_query_system_log()
            .okta_event_types("user.account.lock,user.session.start")
            .search("{{signal.target_user}}")
            .since_hours(48)
            .max_results(200)
        )
        assert log._action == "okta-query-system-log"
        assert log._config["event_types"] == "user.account.lock,user.session.start"
        assert log._config["search"] == "{{signal.target_user}}"
        assert log._config["since_hours"] == 48
        assert log._config["max_results"] == 200

        groups = Action.okta_list_user_groups().okta_user("alice@example.com")
        assert groups._action == "okta-list-user-groups"
        assert groups._config["user"] == "alice@example.com"

        members = Action.okta_list_group_members().okta_group("Okta Administrators").max_results(50)
        assert members._action == "okta-list-group-members"
        assert members._config["group"] == "Okta Administrators"
        assert members._config["max_results"] == 50

    def test_okta_response_actions_serialize(self):
        """Okta response (write) factories emit the right action IDs and
        config keys."""
        for factory, action_id in [
            (Action.okta_suspend_user, "okta-suspend-user"),
            (Action.okta_unsuspend_user, "okta-unsuspend-user"),
            (Action.okta_unlock_user, "okta-unlock-user"),
            (Action.okta_deactivate_user, "okta-deactivate-user"),
            (Action.okta_expire_password, "okta-expire-password"),
            (Action.okta_reset_mfa, "okta-reset-mfa"),
        ]:
            a = factory().okta_user("{{signal.target_user}}")
            assert a._integration == "okta"
            assert a._action == action_id
            assert a._config["user"] == "{{signal.target_user}}"

        clear = Action.okta_clear_sessions().okta_user("alice").revoke_oauth_tokens()
        assert clear._action == "okta-clear-sessions"
        assert clear._config["user"] == "alice"
        assert clear._config["revoke_oauth_tokens"] is True

        add = Action.okta_add_user_to_group().okta_user("alice").okta_group("Quarantine")
        assert add._action == "okta-add-user-to-group"
        assert add._config["user"] == "alice"
        assert add._config["group"] == "Quarantine"

        remove = Action.okta_remove_user_from_group().okta_user("{{signal.target_user}}").okta_group("{{signal.target_group}}")
        assert remove._action == "okta-remove-user-from-group"
        assert remove._config["group"] == "{{signal.target_group}}"

        investigate = (
            Action.okta_investigate()
            .query("is this account lockout suspicious?")
            .max_iterations(5)
        )
        assert investigate._action == "okta-investigate"
        assert investigate._integration == "okta"
        assert investigate._config["query"] == "is this account lockout suspicious?"
        assert investigate._config["max_iterations"] == 5

    def test_okta_triggers(self):
        t = (
            Trigger.okta_group_membership_changed("Okta Administrators")
            .okta_actors("admin@example.com")
            .okta_outcomes("SUCCESS")
            .okta_poll_interval("1m")
        )
        _, tc = Workflow("o").trigger(t).build()
        assert tc["source"] == "okta"
        f = tc["signals"][0]["filters"]
        assert f["okta_event_types"] == ["group.user_membership.add", "group.user_membership.remove"]
        assert f["okta_target_groups"] == ["Okta Administrators"]
        assert f["okta_actors"] == ["admin@example.com"]
        assert f["okta_outcomes"] == ["SUCCESS"]
        assert f["okta_poll_interval"] == "1m"

        for factory, events in [
            (Trigger.okta_user_locked_out, ["user.account.lock"]),
            (Trigger.okta_suspicious_activity, ["user.account.report_suspicious_activity_by_enduser", "security.threat.detected"]),
            (Trigger.okta_admin_privilege_granted, ["user.account.privilege.grant"]),
            (Trigger.okta_mfa_factor_changed, ["user.mfa.factor.deactivate", "user.mfa.factor.reset_all"]),
            (Trigger.okta_user_created, ["user.lifecycle.create"]),
            (Trigger.okta_user_deactivated, ["user.lifecycle.deactivate", "user.lifecycle.suspend"]),
            (Trigger.okta_app_assignment_changed, ["application.user_membership.add", "application.user_membership.remove"]),
        ]:
            trig = factory()
            assert trig._filters["okta_event_types"] == events

        locked = Trigger.okta_user_locked_out().okta_target_users("alice@example.com")
        assert locked._filters["okta_target_users"] == ["alice@example.com"]

        _, tc = Workflow("any").trigger(Trigger.okta_any()).build()
        assert tc["source"] == "okta"

        _, tc = Workflow("req").trigger(Trigger.request_okta()).build()
        assert tc["source"] == "request"
        assert tc["signals"][0]["filters"]["request_categories"] == ["okta"]

    def test_databricks_triggers(self):
        t = (
            Trigger.databricks_job_run_failed("42")
            .databricks_poll_interval("1m")
        )
        _, tc = Workflow("d").trigger(t).build()
        assert tc["source"] == "databricks"
        f = tc["signals"][0]["filters"]
        assert f["databricks_event_types"] == ["job_run.failed"]
        assert f["databricks_job_ids"] == ["42"]
        assert f["databricks_poll_interval"] == "1m"

        for factory, events in [
            (Trigger.databricks_job_run_failed, ["job_run.failed"]),
            (Trigger.databricks_job_run_succeeded, ["job_run.succeeded"]),
            (Trigger.databricks_cluster_terminated, ["cluster.terminated_unexpectedly"]),
            (Trigger.databricks_pipeline_update_failed, ["pipeline.update_failed"]),
        ]:
            trig = factory()
            assert trig._filters["databricks_event_types"] == events

        long_running = Trigger.databricks_job_run_long_running(90)
        assert long_running._filters["databricks_event_types"] == ["job_run.long_running"]
        assert long_running._filters["databricks_min_duration_minutes"] == 90

        scoped = Trigger.databricks_pipeline_update_failed("p-1", "p-2")
        assert scoped._filters["databricks_pipeline_ids"] == ["p-1", "p-2"]

        _, tc = Workflow("any").trigger(Trigger.databricks_any()).build()
        assert tc["source"] == "databricks"

        _, tc = Workflow("req").trigger(Trigger.request_databricks()).build()
        assert tc["source"] == "request"
        assert tc["signals"][0]["filters"]["request_categories"] == ["databricks"]

    def test_databricks_actions_serialize(self):
        """Databricks factories emit the right integration, action IDs, and
        config keys."""
        repair = Action.databricks_repair_run().databricks_run("{{signal.run_id}}")
        assert repair._integration == "databricks"
        assert repair._action == "databricks-repair-run"
        assert repair._config["run_id"] == "{{signal.run_id}}"

        run = Action.databricks_run_job().databricks_job("42")
        assert run._action == "databricks-run-job"
        assert run._config["job_id"] == "42"

        sql = (
            Action.databricks_execute_sql()
            .databricks_warehouse("wh-1")
            .databricks_statement("SELECT count(*) FROM t")
        )
        assert sql._action == "databricks-execute-sql"
        assert sql._config["warehouse_id"] == "wh-1"
        assert sql._config["statement"] == "SELECT count(*) FROM t"

        restart = Action.databricks_restart_cluster().databricks_cluster("{{signal.cluster_id}}")
        assert restart._action == "databricks-restart-cluster"
        assert restart._config["cluster_id"] == "{{signal.cluster_id}}"

        update = Action.databricks_start_pipeline_update().databricks_pipeline("p-1")
        assert update._action == "databricks-start-pipeline-update"
        assert update._config["pipeline_id"] == "p-1"

        investigate = Action.databricks_investigate().config("query", "why did the run fail?")
        assert investigate._action == "databricks-investigate"
        assert investigate._config["query"] == "why did the run fail?"

    def test_gcp_triggers(self):
        """Every GCP trigger factory sets source "gcp" and pins exactly the
        event type it names."""
        t = (
            Trigger.gcp_cost_anomaly()
            .gcp_projects("my-project")
            .gcp_min_cost_impact(250)
            .gcp_poll_interval("6h")
        )
        _, tc = Workflow("g").trigger(t).build()
        assert tc["source"] == "gcp"
        assert tc["signals"][0]["signal_type"] == "cost_anomaly"
        f = tc["signals"][0]["filters"]
        assert f["gcp_connection_ids"] == ["my-project"]
        assert f["gcp_min_cost_impact"] == 250
        assert f["gcp_poll_interval"] == "6h"

        # Each factory pins its own event type, so a copy-paste slip between
        # the 23 factories is caught here rather than at runtime.
        for factory, events in [
            (Trigger.gcp_cost_anomaly, ["cost_anomaly"]),
            (Trigger.gcp_budget_alert, ["budget_alert"]),
            (Trigger.gcp_forecast_overrun, ["forecast_overrun"]),
            (Trigger.gcp_spend_spike, ["spend_spike"]),
            (Trigger.gcp_idle_resource, ["idle_resource"]),
            (Trigger.gcp_instance_preempted, ["instance.preempted"]),
            (
                Trigger.gcp_instance_terminated_abnormally,
                ["instance.terminated_abnormally"],
            ),
            (Trigger.gcp_mig_unhealthy, ["mig.unhealthy"]),
            (Trigger.gcp_nodepool_degraded, ["nodepool.degraded"]),
            (Trigger.gcp_cloudrun_revision_failed, ["cloudrun.revision_failed"]),
            (Trigger.gcp_monitoring_alert_fired, ["monitoring.alert_fired"]),
            (Trigger.gcp_logging_error_pattern, ["logging.error_pattern"]),
            (Trigger.gcp_build_failed, ["build.failed"]),
            (Trigger.gcp_scc_finding, ["scc.finding"]),
            (Trigger.gcp_iam_policy_change, ["iam.policy_change"]),
            (Trigger.gcp_service_account_key_stale, ["sa_key.stale"]),
            (Trigger.gcp_public_bucket, ["storage.public_access"]),
            (Trigger.gcp_public_iam_binding, ["iam.public_binding"]),
            (Trigger.gcp_bigquery_job_failed, ["bigquery.job_failed"]),
            (Trigger.gcp_bigquery_expensive_query, ["bigquery.expensive_query"]),
            (Trigger.gcp_cloudsql_unhealthy, ["cloudsql.unhealthy"]),
            (Trigger.gcp_pubsub_backlog, ["pubsub.backlog"]),
            (Trigger.gcp_dataflow_job_failed, ["dataflow.job_failed"]),
        ]:
            trig = factory()
            assert trig._signal_type == events[0], factory.__name__

        # gcp_any() matches every GCP event rather than pinning one.
        _, tc = Workflow("any").trigger(Trigger.gcp_any()).build()
        assert tc["source"] == "gcp"
        assert tc["signals"][0]["signal_type"] == "any"

    def test_gcp_trigger_scoping_filters(self):
        """Scoping helpers write the filter keys the server's SignalFilter
        expects. A rename on either side would break matching silently."""
        t = (
            Trigger.gcp_mig_unhealthy()
            .gcp_projects("proj-a", "proj-b")
            .gcp_regions("us-central1")
            .gcp_zones("us-central1-a")
            .gcp_instance_groups("mig-1")
            .gcp_unhealthy_threshold(3)
        )
        f = t._filters
        assert f["gcp_connection_ids"] == ["proj-a", "proj-b"]
        assert f["gcp_regions"] == ["us-central1"]
        assert f["gcp_zones"] == ["us-central1-a"]
        assert f["gcp_instance_groups"] == ["mig-1"]
        assert f["gcp_unhealthy_threshold"] == 3

        ops = (
            Trigger.gcp_nodepool_degraded()
            .gcp_clusters("prod")
            .gcp_node_pools("default-pool")
            .gcp_min_duration_minutes(15)
        )
        assert ops._filters["gcp_clusters"] == ["prod"]
        assert ops._filters["gcp_node_pools"] == ["default-pool"]
        assert ops._filters["gcp_min_duration_minutes"] == 15

        # gcp_services filters the billing/monitoring service name, while
        # gcp_cloudrun_services scopes Cloud Run events to service names. These
        # are different filter keys and must not collide.
        billing = Trigger.gcp_cost_anomaly().gcp_services("Compute Engine")
        assert billing._filters["gcp_service_names"] == ["Compute Engine"]
        run = Trigger.gcp_cloudrun_revision_failed().gcp_cloudrun_services("checkout")
        assert run._filters["gcp_services"] == ["checkout"]

        logs = (
            Trigger.gcp_logging_error_pattern()
            .gcp_log_filter('resource.type="cloud_run_revision"')
            .gcp_log_severity("ERROR")
            .gcp_min_error_count(20)
        )
        assert logs._filters["gcp_log_filter"] == 'resource.type="cloud_run_revision"'
        assert logs._filters["gcp_log_severity"] == "ERROR"
        assert logs._filters["gcp_min_error_count"] == 20

        sec = (
            Trigger.gcp_scc_finding()
            .gcp_finding_categories("PUBLIC_BUCKET_ACL")
            .gcp_severities("critical", "high")
        )
        assert sec._filters["gcp_finding_categories"] == ["PUBLIC_BUCKET_ACL"]
        assert sec._filters["gcp_severities"] == ["critical", "high"]

        keys = (
            Trigger.gcp_service_account_key_stale()
            .gcp_service_accounts("sa@proj.iam.gserviceaccount.com")
            .gcp_max_key_age_days(30)
        )
        assert keys._filters["gcp_service_accounts"] == [
            "sa@proj.iam.gserviceaccount.com"
        ]
        assert keys._filters["gcp_max_key_age_days"] == 30

        data = Trigger.gcp_pubsub_backlog().gcp_subscriptions("orders-sub")
        assert data._filters["gcp_subscriptions"] == ["orders-sub"]

        idle = (
            Trigger.gcp_idle_resource()
            .gcp_idle_resource_types("disk", "address")
            .gcp_min_monthly_savings(50)
        )
        assert idle._filters["gcp_idle_resource_types"] == ["disk", "address"]
        assert idle._filters["gcp_min_monthly_savings"] == 50

        budget = Trigger.gcp_budget_alert().gcp_budget_threshold_percent(90)
        assert budget._filters["gcp_budget_threshold_percent"] == 90
        spike = Trigger.gcp_spend_spike().gcp_spike_percent(60)
        assert spike._filters["gcp_spike_percent"] == 60

    def test_gcp_actions_serialize(self):
        """GCP factories emit the right integration, action IDs, and config
        keys, including template variables passed through from a trigger."""
        # The four GCP integrations are distinct, so a block registered under
        # one must not report another.
        query = (
            Action.gcp_query_billing()
            .config("gcp_project", "my-project")
            .config("days", 30)
        )
        assert query._integration == "gcp-cost"
        assert query._action == "gcp-query-billing"
        assert query._config["gcp_project"] == "my-project"

        stop = (
            Action.gcp_stop_instances()
            .config("gcp_project", "my-project")
            .config("zone", "us-central1-a")
            .config("instance_names", "{{step_outputs.action-1.instance_names}}")
        )
        assert stop._integration == "gcp-cost"
        assert stop._action == "gcp-stop-instances"
        assert stop._config["zone"] == "us-central1-a"
        # Template variables must survive untouched so the engine can resolve
        # them at execution time.
        assert (
            stop._config["instance_names"]
            == "{{step_outputs.action-1.instance_names}}"
        )

        rollback = (
            Action.gcp_rollback_cloudrun()
            .config("gcp_project", "my-project")
            .config("region", "us-central1")
            .config("service_name", "{{signal.cloudrun_service}}")
        )
        assert rollback._integration == "gcp"
        assert rollback._action == "gcp-rollback-cloudrun"
        assert rollback._config["service_name"] == "{{signal.cloudrun_service}}"

        binding = (
            Action.gcp_remove_iam_binding()
            .config("gcp_project", "my-project")
            .config("member", "user:contractor@example.com")
            .config("role", "roles/owner")
        )
        assert binding._integration == "gcp-security"
        assert binding._action == "gcp-remove-iam-binding"
        assert binding._config["role"] == "roles/owner"

        bq = (
            Action.gcp_run_bigquery_query()
            .config("gcp_project", "my-project")
            .config("query", "SELECT 1")
        )
        assert bq._integration == "gcp-data"
        assert bq._action == "gcp-run-bigquery-query"
        assert bq._config["query"] == "SELECT 1"

    def test_gcp_workflow_round_trip(self):
        """A GCP trigger feeding a GCP action serializes into the shape the
        server expects, with the trigger's outputs referenced by the action."""
        wf = (
            Workflow("cloud-run-rollback")
            .trigger(
                Trigger.gcp_cloudrun_revision_failed()
                .gcp_projects("my-project")
                .gcp_cloudrun_services("checkout")
            )
            .then(
                Action.gcp_get_cloudrun_service()
                .config("gcp_project", "my-project")
                .config("region", "us-central1")
                .config("service_name", "{{signal.cloudrun_service}}")
            )
        )
        dag, tc = wf.build()
        assert tc["source"] == "gcp"
        assert tc["signals"][0]["filters"]["gcp_services"] == ["checkout"]

        # Node 0 is the trigger, node 1 the action it feeds.
        trigger_node, step = dag["nodes"][0], dag["nodes"][1]
        assert trigger_node["type"] == "trigger"
        assert trigger_node["data"]["source"] == "gcp"
        assert trigger_node["data"]["signal_type"] == "cloudrun.revision_failed"

        assert step["type"] == "action"
        assert step["data"]["integration"] == "gcp"
        assert step["data"]["action"] == "gcp-get-cloudrun-service"
        assert (
            step["data"]["config"]["service_name"] == "{{signal.cloudrun_service}}"
        )
        # The trigger must actually be wired to the action.
        assert any(
            e["source"] == trigger_node["id"] and e["target"] == step["id"]
            for e in dag["edges"]
        )

    def test_condition_branching(self):
        wf = (
            Workflow("cond")
            .trigger(Trigger.k8s_pod_status())
            .then(Condition.equals("rca_result.bug", "true"))
            .on_true(Action.slack_send_message().channel("dev"))
            .on_false(Action.slack_send_message().channel("infra"))
        )
        d, _ = wf.build()
        labels = {e.get("label") for e in d["edges"]}
        assert {"true", "false"} <= labels

    def test_approval_branching(self):
        wf = (
            Workflow("appr")
            .trigger(Trigger.k8s_rollout_status())
            .then(Approval.slack("#approvals").message("ok?"))
            .on_approved(Action.kestrel_apply_yaml_fix())
            .on_rejected(Action.slack_send_message().channel("ops"))
        )
        d, _ = wf.build()
        labels = {e.get("label") for e in d["edges"]}
        assert {"approved", "rejected"} <= labels

    def test_refine_approval_node(self):
        """Approval.refine() emits a self-looping refine_approval node with
        the approval-refine-rca action + max_rounds, and supports approved/
        rejected branching like a normal approval gate."""
        wf = (
            Workflow("refine")
            .trigger(Trigger.k8s_rollout_status())
            .then(Action.kestrel_trigger_rca())
            .then(Action.kestrel_generate_runbook())
            .then(Approval.refine().max_rounds(3).message("Review"))
            .on_approved(Action.kestrel_apply_yaml_fix())
            .on_rejected(Action.slack_send_message().channel("ops"))
        )
        d, _ = wf.build()

        runbook = next(n for n in d["nodes"] if n["data"].get("action") == "kestrel-generate-runbook")
        assert runbook["type"] == "action"

        gate = next(n for n in d["nodes"] if n["type"] == "refine_approval")
        assert gate["data"]["action"] == "approval-refine-rca"
        assert gate["data"]["max_rounds"] == 3
        assert gate["data"]["approval_type"] == "manual"

        labels = {e.get("label") for e in d["edges"]}
        assert {"approved", "rejected"} <= labels

    def test_refine_approval_defaults_and_slack(self):
        manual = Approval.refine()._to_node("approval-1")
        assert manual.to_dict()["data"]["max_rounds"] == 5

        slack = Approval.refine("slack").channel("#oncall")._to_node("approval-2")
        data = slack.to_dict()["data"]
        assert data["approval_type"] == "slack"
        assert data["config"]["channel"] == "#oncall"
        assert slack.to_dict()["type"] == "refine_approval"

    def test_poll_until_node(self):
        """PollUntil emits a self-looping loop node with the embedded action,
        exit condition, interval/timeout, and met/timeout branching."""
        wf = (
            Workflow("poll")
            .trigger(Trigger.request_general())
            .then(Action.daytona_create_sandbox())
            .then(
                PollUntil(
                    Action.daytona_get_sandbox().config("sandbox_id", "{{step_outputs.action-1.sandbox_id}}"),
                    Condition.not_equals("state", "started"),
                )
                .every(seconds=45)
                .timeout(minutes=30)
                .label("Poll until stopped")
            )
            .on_met(Action.slack_send_message().channel("dev"))
            .on_timeout(Action.slack_send_message().channel("dev"))
        )
        d, _ = wf.build()

        loop = next(n for n in d["nodes"] if n["type"] == "loop")
        assert loop["id"] == "loop-1"
        assert loop["data"]["integration"] == "daytona"
        assert loop["data"]["action"] == "daytona-get-sandbox"
        assert loop["data"]["config"]["sandbox_id"] == "{{step_outputs.action-1.sandbox_id}}"
        assert loop["data"]["condition"] == {
            "field": "state",
            "operator": "not_equals",
            "value": "started",
        }
        assert loop["data"]["interval_seconds"] == 45
        assert loop["data"]["timeout_minutes"] == 30
        assert loop["data"]["label"] == "Poll until stopped"

        labels = {e.get("label") for e in d["edges"]}
        assert {"met", "timeout"} <= labels

    def test_poll_until_defaults(self):
        node = PollUntil(
            Action.daytona_get_sandbox(),
            Condition.equals("state", "stopped"),
        )._to_node("loop-1")
        data = node.to_dict()["data"]
        assert data["interval_seconds"] == 60
        assert data["timeout_minutes"] == 60
        assert data["condition"]["operator"] == "equals"
        # Single-value conditions omit "values" (legacy payload shape).
        assert "values" not in data["condition"]

    def test_poll_until_multi_value_condition(self):
        """Condition factories accept multiple values; the payload carries
        them in "values" (ANY-match for equals, NONE-match for not_equals)."""
        node = PollUntil(
            Action.daytona_get_sandbox(),
            Condition.equals("sandbox_state", "stopped", "error"),
        )._to_node("loop-1")
        cond = node.to_dict()["data"]["condition"]
        assert cond["operator"] == "equals"
        assert cond["values"] == ["stopped", "error"]

    def test_condition_node_multi_value(self):
        node = Condition.not_equals("state", "started", "starting")._to_node("condition-1")
        data = node.to_dict()["data"]
        assert data["operator"] == "not_equals"
        assert data["values"] == ["started", "starting"]

    def test_for_each_node(self):
        """ForEach emits a for_each node with the embedded per-item action,
        items_path, fan-out settings, and ordinary successor edges."""
        wf = (
            Workflow("fanout")
            .trigger(Trigger.request_general())
            .then(Action("kestrel", "kestrel-execute-script").config("script", "print('x')"))
            .then(
                ForEach(
                    "{{step_outputs.action-1.outputs.new_findings}}",
                    Action.jira_create_ticket()
                    .config("project_key", "SEC")
                    .config("title_template", "[Audit] {{item.title}}"),
                )
                .max_items(50)
                .continue_on_error()
                .label("Ticket per finding")
            )
            .then(Action.slack_send_message().channel("security"))
        )
        d, _ = wf.build()

        fe = next(n for n in d["nodes"] if n["type"] == "for_each")
        assert fe["id"] == "foreach-1"
        assert fe["data"]["integration"] == "jira"
        assert fe["data"]["action"] == "jira-create-ticket"
        assert fe["data"]["items_path"] == "{{step_outputs.action-1.outputs.new_findings}}"
        assert fe["data"]["config"]["title_template"] == "[Audit] {{item.title}}"
        assert fe["data"]["max_items"] == 50
        assert fe["data"]["continue_on_error"] is True
        assert fe["data"]["label"] == "Ticket per finding"

        # Successor wired via a plain (unlabelled) edge from the for_each node.
        succ = next(e for e in d["edges"] if e["source"] == "foreach-1")
        assert succ["target"] == "action-2"
        assert not succ.get("label")

    def test_for_each_defaults(self):
        node = ForEach(
            "{{step_outputs.action-1.outputs.items}}",
            Action.slack_send_message().channel("dev"),
        )._to_node("foreach-1")
        data = node.to_dict()["data"]
        # Server-side defaults apply; the payload omits unset optionals.
        assert "max_items" not in data
        assert "continue_on_error" not in data
        assert "condition" not in data
        assert data["items_path"] == "{{step_outputs.action-1.outputs.items}}"

    def test_parallel_via_also(self):
        wf = (
            Workflow("para")
            .trigger(Trigger.k8s_pod_status())
            .then(Action.kestrel_trigger_rca())
            .also(Action.slack_send_message().channel("incidents"))
        )
        d, _ = wf.build()
        assert len(d["nodes"]) == 3

    def test_linear_actions_serialize(self):
        wf = (
            Workflow("linear")
            .trigger(Trigger.k8s_pod_status().reasons("CrashLoopBackOff"))
            .then(
                Action.linear_create_issue()
                .team("ENG")
                .title("{{incident.title}}")
                .body("{{rca_result.root_cause}}")
                .priority("High")
                .labels("bug, infra")
                .project_name("Reliability")
                .label("Create Linear Issue")
            )
            .then(
                Action.linear_update_issue()
                .issue_identifier("{{step_outputs.action-1.issue_identifier}}")
                .status("In Progress")
            )
        )
        d, _ = wf.build()
        action_nodes = [n for n in d["nodes"] if n["type"] == "action"]
        assert len(action_nodes) == 2

        create = action_nodes[0]["data"]
        assert create["integration"] == "linear"
        assert create["action"] == "linear-create-issue"
        assert create["config"]["team_key"] == "ENG"
        assert create["config"]["title_template"] == "{{incident.title}}"
        assert create["config"]["priority"] == "High"
        assert create["config"]["labels"] == "bug, infra"
        assert create["config"]["project"] == "Reliability"
        assert create["label"] == "Create Linear Issue"

        update = action_nodes[1]["data"]
        assert update["action"] == "linear-update-issue"
        assert update["config"]["issue_identifier"] == "{{step_outputs.action-1.issue_identifier}}"
        assert update["config"]["status"] == "In Progress"

    def test_linear_search_and_comment_factories(self):
        search = Action.linear_search_issues().query("db timeout").team("ENG").limit(5)
        node = search._to_node("action-1").to_dict()
        assert node["data"]["integration"] == "linear"
        assert node["data"]["action"] == "linear-search-issues"
        assert node["data"]["config"] == {"query": "db timeout", "team_key": "ENG", "limit": 5}

        comment = Action.linear_add_comment().issue_identifier("ENG-123").body("update")
        node = comment._to_node("action-2").to_dict()
        assert node["data"]["action"] == "linear-add-comment"
        assert node["data"]["config"] == {"issue_identifier": "ENG-123", "body_template": "update"}

    def test_railway_actions_serialize(self):
        wf = (
            Workflow("railway")
            .trigger(Trigger.railway_deployment_failed())
            .then(
                Action.railway_get_deployment_logs()
                .config("deployment_id", "{{signal.deployment_id}}")
                .label("Get Railway Logs")
            )
            .then(
                Action.railway_redeploy()
                .config("service_id", "{{signal.service_id}}")
                .config("environment_id", "{{signal.environment_id}}")
            )
        )
        d, _ = wf.build()
        action_nodes = [n for n in d["nodes"] if n["type"] == "action"]
        assert len(action_nodes) == 2

        logs = action_nodes[0]["data"]
        assert logs["integration"] == "railway"
        assert logs["action"] == "railway-get-deployment-logs"
        assert logs["config"]["deployment_id"] == "{{signal.deployment_id}}"
        assert logs["label"] == "Get Railway Logs"

        redeploy = action_nodes[1]["data"]
        assert redeploy["action"] == "railway-redeploy"
        assert redeploy["config"]["service_id"] == "{{signal.service_id}}"
        assert redeploy["config"]["environment_id"] == "{{signal.environment_id}}"

    def test_railway_factory_methods(self):
        cases = {
            "railway-get-deployment": Action.railway_get_deployment(),
            "railway-get-deployment-logs": Action.railway_get_deployment_logs(),
            "railway-rollback": Action.railway_rollback(),
            "railway-redeploy": Action.railway_redeploy(),
            "railway-restart": Action.railway_restart(),
            "railway-list-deployments": Action.railway_list_deployments(),
            "railway-set-variables": Action.railway_set_variables(),
            "railway-investigate": Action.railway_investigate(),
        }
        for action_id, action in cases.items():
            node = action._to_node("action-1").to_dict()
            assert node["data"]["integration"] == "railway"
            assert node["data"]["action"] == action_id

    def test_flyio_actions_serialize(self):
        wf = (
            Workflow("flyio")
            .trigger(
                Trigger.flyio_machine_crashed()
                .fly_apps("my-app")
                .fly_poll_interval("5m")
            )
            .then(
                Action.flyio_get_machine_events()
                .app_name("{{signal.app_name}}")
                .machine_id("{{signal.machine_id}}")
                .label("Get Machine Events")
            )
            .then(
                Action.flyio_restart_machine()
                .app_name("{{signal.app_name}}")
                .machine_id("{{signal.machine_id}}")
            )
        )
        d, tc = wf.build()
        action_nodes = [n for n in d["nodes"] if n["type"] == "action"]
        assert len(action_nodes) == 2

        events = action_nodes[0]["data"]
        assert events["integration"] == "flyio"
        assert events["action"] == "flyio-get-machine-events"
        assert events["config"]["app_name"] == "{{signal.app_name}}"
        assert events["config"]["machine_id"] == "{{signal.machine_id}}"
        assert events["label"] == "Get Machine Events"

        restart = action_nodes[1]["data"]
        assert restart["action"] == "flyio-restart-machine"
        assert restart["config"]["machine_id"] == "{{signal.machine_id}}"

        assert tc["source"] == "flyio"
        assert tc["signals"][0]["filters"]["fly_app_names"] == ["my-app"]
        assert tc["signals"][0]["filters"]["fly_poll_interval"] == "5m"
        assert tc["signals"][0]["filters"]["fly_event_types"] == ["machine.crashed"]

    def test_flyio_factory_methods(self):
        cases = {
            "flyio-restart-machine": Action.flyio_restart_machine(),
            "flyio-start-machine": Action.flyio_start_machine(),
            "flyio-stop-machine": Action.flyio_stop_machine(),
            "flyio-suspend-machine": Action.flyio_suspend_machine(),
            "flyio-cordon-machine": Action.flyio_cordon_machine(),
            "flyio-uncordon-machine": Action.flyio_uncordon_machine(),
            "flyio-get-machine": Action.flyio_get_machine(),
            "flyio-get-machine-events": Action.flyio_get_machine_events(),
            "flyio-list-machines": Action.flyio_list_machines(),
            "flyio-set-secrets": Action.flyio_set_secrets(),
            "flyio-investigate": Action.flyio_investigate(),
        }
        for action_id, action in cases.items():
            node = action._to_node("action-1").to_dict()
            assert node["data"]["integration"] == "flyio"
            assert node["data"]["action"] == action_id

    def test_flyio_trigger_factory_methods(self):
        cases = {
            "machine.crashed": Trigger.flyio_machine_crashed(),
            "machine.stopped": Trigger.flyio_machine_stopped(),
            "machine.started": Trigger.flyio_machine_started(),
            "app.down": Trigger.flyio_app_down(),
            "any": Trigger.flyio_any(),
        }
        for signal_type, trig in cases.items():
            wf = Workflow("t").trigger(trig).then(Action.flyio_get_machine())
            _, tc = wf.build()
            assert tc["source"] == "flyio"
            assert tc["signals"][0]["signal_type"] == signal_type

    def test_nebius_actions_serialize(self):
        wf = (
            Workflow("nebius")
            .trigger(
                Trigger.nebius_gpu_error()
                .nebius_projects("project-abc")
                .nebius_poll_interval("5m")
            )
            .then(
                Action.nebius_investigate()
                .config("query", "Analyze the GPU error")
                .label("Investigate Nebius")
            )
            .then(
                Action.nebius_scale_node_group()
                .cluster_id("{{signal.cluster_id}}")
                .node_group_id("{{signal.node_group_id}}")
                .size(3)
            )
        )
        d, tc = wf.build()
        action_nodes = [n for n in d["nodes"] if n["type"] == "action"]
        assert len(action_nodes) == 2

        investigate = action_nodes[0]["data"]
        assert investigate["integration"] == "nebius"
        assert investigate["action"] == "nebius-investigate"
        assert investigate["config"]["query"] == "Analyze the GPU error"
        assert investigate["label"] == "Investigate Nebius"

        scale = action_nodes[1]["data"]
        assert scale["action"] == "nebius-scale-node-group"
        assert scale["config"]["cluster_id"] == "{{signal.cluster_id}}"
        assert scale["config"]["node_group_id"] == "{{signal.node_group_id}}"
        assert scale["config"]["size"] == 3

        assert tc["source"] == "nebius"
        assert tc["signals"][0]["filters"]["nebius_project_ids"] == ["project-abc"]
        assert tc["signals"][0]["filters"]["nebius_poll_interval"] == "5m"
        assert tc["signals"][0]["filters"]["nebius_event_types"] == ["node.gpu_error"]

    def test_nebius_factory_methods(self):
        cases = {
            "nebius-get-instance": Action.nebius_get_instance(),
            "nebius-start-instance": Action.nebius_start_instance(),
            "nebius-stop-instance": Action.nebius_stop_instance(),
            "nebius-restart-instance": Action.nebius_restart_instance(),
            "nebius-list-instances": Action.nebius_list_instances(),
            "nebius-list-clusters": Action.nebius_list_clusters(),
            "nebius-list-node-groups": Action.nebius_list_node_groups(),
            "nebius-scale-node-group": Action.nebius_scale_node_group(),
            "nebius-create-instance": Action.nebius_create_instance(),
            "nebius-delete-instance": Action.nebius_delete_instance(),
            "nebius-create-node-group": Action.nebius_create_node_group(),
            "nebius-delete-node-group": Action.nebius_delete_node_group(),
            "nebius-investigate": Action.nebius_investigate(),
        }
        for action_id, action in cases.items():
            node = action._to_node("action-1").to_dict()
            assert node["data"]["integration"] == "nebius"
            assert node["data"]["action"] == action_id

    def test_nebius_provisioning_actions_serialize(self):
        wf = (
            Workflow("nebius-provision")
            .trigger(Trigger.nebius_any())
            .then(
                Action.nebius_create_instance()
                .project_id("project-abc")
                .name("gpu-box")
                .platform("gpu-h100-sxm")
                .preset("1gpu-16vcpu-200gb")
                .subnet_id("subnet-1")
                .config("image_family", "ubuntu22.04-cuda12")
                .config("boot_disk_gb", 200)
                .config("ssh_public_key", "ssh-ed25519 AAAA dev@host")
            )
            .then(
                Action.nebius_delete_instance()
                .project_id("project-abc")
                .instance_id("{{step_outputs.action-1.instance_id}}")
                .config("delete_boot_disk", True)
            )
            .then(
                Action.nebius_create_node_group()
                .cluster_id("cluster-1")
                .name("gpu-pool")
                .platform("gpu-h200-sxm")
                .preset("1gpu-16vcpu-200gb")
                .config("node_count", 2)
            )
            .then(
                Action.nebius_delete_node_group()
                .cluster_id("cluster-1")
                .node_group_id("{{step_outputs.action-3.node_group_id}}")
            )
        )
        d, tc = wf.build()
        action_nodes = [n for n in d["nodes"] if n["type"] == "action"]
        assert len(action_nodes) == 4

        create = action_nodes[0]["data"]
        assert create["action"] == "nebius-create-instance"
        assert create["config"]["project_id"] == "project-abc"
        assert create["config"]["name"] == "gpu-box"
        assert create["config"]["platform"] == "gpu-h100-sxm"
        assert create["config"]["preset"] == "1gpu-16vcpu-200gb"
        assert create["config"]["subnet_id"] == "subnet-1"
        assert create["config"]["image_family"] == "ubuntu22.04-cuda12"
        assert create["config"]["boot_disk_gb"] == 200
        assert create["config"]["ssh_public_key"] == "ssh-ed25519 AAAA dev@host"

        delete = action_nodes[1]["data"]
        assert delete["action"] == "nebius-delete-instance"
        assert delete["config"]["instance_id"] == "{{step_outputs.action-1.instance_id}}"
        assert delete["config"]["delete_boot_disk"] is True

        create_ng = action_nodes[2]["data"]
        assert create_ng["action"] == "nebius-create-node-group"
        assert create_ng["config"]["cluster_id"] == "cluster-1"
        assert create_ng["config"]["name"] == "gpu-pool"
        assert create_ng["config"]["platform"] == "gpu-h200-sxm"
        assert create_ng["config"]["node_count"] == 2

        delete_ng = action_nodes[3]["data"]
        assert delete_ng["action"] == "nebius-delete-node-group"
        assert delete_ng["config"]["node_group_id"] == "{{step_outputs.action-3.node_group_id}}"

        assert tc["source"] == "nebius"

    def test_nebius_trigger_factory_methods(self):
        cases = {
            "node.gpu_error": Trigger.nebius_gpu_error(),
            "node.maintenance_scheduled": Trigger.nebius_maintenance_scheduled(),
            "node.not_ready": Trigger.nebius_node_not_ready(),
            "instance.stopped": Trigger.nebius_instance_stopped(),
            "any": Trigger.nebius_any(),
        }
        for signal_type, trig in cases.items():
            wf = Workflow("t").trigger(trig).then(Action.nebius_get_instance())
            _, tc = wf.build()
            assert tc["source"] == "nebius"
            assert tc["signals"][0]["signal_type"] == signal_type

    def test_daytona_actions_serialize(self):
        wf = (
            Workflow("daytona")
            .trigger(
                Trigger.daytona_sandbox_error()
                .daytona_sandboxes("sandbox-abc")
            )
            .then(Action.daytona_get_sandbox())
            .then(Action.daytona_investigate())
        )
        d, tc = wf.build()
        node_map = {n["data"].get("action"): n["data"] for n in d["nodes"] if n["data"].get("integration") == "daytona"}
        assert node_map["daytona-get-sandbox"]["integration"] == "daytona"
        assert node_map["daytona-investigate"]["action"] == "daytona-investigate"
        assert tc["source"] == "daytona"
        assert tc["signals"][0]["filters"]["daytona_sandbox_ids"] == ["sandbox-abc"]
        assert tc["signals"][0]["filters"]["daytona_event_types"] == ["sandbox.error"]

    def test_daytona_factory_methods(self):
        cases = {
            "daytona-list-sandboxes": Action.daytona_list_sandboxes(),
            "daytona-create-sandbox": Action.daytona_create_sandbox(),
            "daytona-get-sandbox": Action.daytona_get_sandbox(),
            "daytona-start-sandbox": Action.daytona_start_sandbox(),
            "daytona-stop-sandbox": Action.daytona_stop_sandbox(),
            "daytona-archive-sandbox": Action.daytona_archive_sandbox(),
            "daytona-delete-sandbox": Action.daytona_delete_sandbox(),
            "daytona-run-command": Action.daytona_run_command(),
            "daytona-set-auto-stop": Action.daytona_set_auto_stop(),
            "daytona-list-snapshots": Action.daytona_list_snapshots(),
            "daytona-create-snapshot": Action.daytona_create_snapshot(),
            "daytona-delete-snapshot": Action.daytona_delete_snapshot(),
            "daytona-list-volumes": Action.daytona_list_volumes(),
            "daytona-get-volume": Action.daytona_get_volume(),
            "daytona-create-volume": Action.daytona_create_volume(),
            "daytona-delete-volume": Action.daytona_delete_volume(),
            "daytona-investigate": Action.daytona_investigate(),
        }
        for action_id, action in cases.items():
            node = action._to_node("action-1").to_dict()
            assert node["data"]["integration"] == "daytona"
            assert node["data"]["action"] == action_id

    def test_daytona_trigger_factory_methods(self):
        cases = {
            "sandbox.created": Trigger.daytona_sandbox_created(),
            "sandbox.stopped": Trigger.daytona_sandbox_stopped(),
            "sandbox.error": Trigger.daytona_sandbox_error(),
            "sandbox.archived": Trigger.daytona_sandbox_archived(),
            "snapshot.build_failed": Trigger.daytona_snapshot_build_failed(),
            "volume.error": Trigger.daytona_volume_error(),
            "any": Trigger.daytona_any(),
        }
        for signal_type, trig in cases.items():
            wf = Workflow("t").trigger(trig).then(Action.daytona_get_sandbox())
            _, tc = wf.build()
            assert tc["source"] == "daytona"
            assert tc["signals"][0]["signal_type"] == signal_type

    def test_build_without_trigger_raises(self):
        with pytest.raises(ValueError):
            Workflow("no trigger").build()

    def test_cooldown_settings(self):
        wf = Workflow("cd").trigger(Trigger.k8s_pod_status()).cooldown(hours=2, minutes=30)
        _, tc = wf.build()
        assert tc["cooldown_hours"] == 2
        assert tc["cooldown_minutes"] == 30

    def test_no_cooldown(self):
        wf = Workflow("cd").trigger(Trigger.k8s_pod_status()).cooldown()
        _, tc = wf.build()
        assert tc["no_cooldown"] is True


# ---------------------------------------------------------------------------
# Null tolerance — server may return null for fields with default_factory
# ---------------------------------------------------------------------------


class TestNullTolerance:
    @respx.mock
    def test_workflow_request_suggested_workflow_null(self, client):
        respx.get(f"{SERVER}/api/workflow-requests").mock(
            httpx.Response(200, json={"requests": [
                {"id": "r-1", "status": "no_workflow", "suggested_workflow": None}
            ]})
        )
        out = client.requests.list()
        assert out[0].suggested_workflow == {}

    @respx.mock
    def test_workflow_definition_null(self, client):
        respx.get(f"{SERVER}/api/workflows/wf-1").mock(
            httpx.Response(200, json={
                "id": "wf-1", "name": "x", "status": "draft",
                "definition": None, "trigger_config": None,
            })
        )
        wf = client.workflows.get("wf-1")
        assert wf.definition == {}
        assert wf.trigger_config == {}

    @respx.mock
    def test_execution_trigger_signal_null(self, client):
        respx.get(f"{SERVER}/api/workflow-executions/exec-1").mock(
            httpx.Response(200, json={
                "id": "exec-1", "status": "running",
                "trigger_signal": None, "step_results": None,
            })
        )
        ex = client.executions.get("exec-1")
        assert ex.trigger_signal == {}
        assert ex.step_results == []

    @respx.mock
    def test_approval_context_null(self, client):
        respx.get(f"{SERVER}/api/workflow-approvals/pending").mock(
            httpx.Response(200, json=[{"id": "a-1", "context": None,
                                       "approval_responses": None, "approval_rules": None}])
        )
        a = client.approvals.list_pending()[0]
        assert a.context == {}
        assert a.approval_responses == []
        assert a.approval_rules == []

    @respx.mock
    def test_catalog_extra_fields_null(self, client):
        respx.get(f"{SERVER}/api/workflows/catalog").mock(
            httpx.Response(200, json={
                "signals": [], "actions": [], "integrations": [],
                "custom_blocks": None, "slack_channels": None,
                "slack_users": None, "trigger_variables": None,
            })
        )
        cat = client.workflows.catalog()
        assert cat.custom_blocks == []
        assert cat.slack_channels == []
        assert cat.slack_users == []
        assert cat.trigger_variables == {}
