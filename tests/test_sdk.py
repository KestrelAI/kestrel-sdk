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
from kestrel.workflows import Action, Approval, Condition, Trigger, Workflow

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
        respx.post(f"{SERVER}/api/workflow-requests").mock(
            httpx.Response(200, json={"status": "no_workflow", "request_id": "req-1"})
        )
        res = client.workflows.request("restart api-server")
        assert res.request_id == "req-1"

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
            "nebius-investigate": Action.nebius_investigate(),
        }
        for action_id, action in cases.items():
            node = action._to_node("action-1").to_dict()
            assert node["data"]["integration"] == "nebius"
            assert node["data"]["action"] == action_id

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
