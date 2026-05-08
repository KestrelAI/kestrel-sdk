"""SDK test suite — pure HTTP mocks via respx.

Run::

    cd sdk
    pip install -e '.[dev]'
    pytest tests -v

Sections:
    TestAuth                — client construction
    TestHttpErrorMapping    — 401/404/409/5xx → typed exceptions
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
from typing import Any

import httpx
import pytest
import respx

from kestrel import (
    AsyncKestrelClient,
    AuthError,
    ConflictError,
    KestrelClient,
    KestrelError,
    NotFoundError,
    ServerError,
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

    def test_parallel_via_also(self):
        wf = (
            Workflow("para")
            .trigger(Trigger.k8s_pod_status())
            .then(Action.kestrel_trigger_rca())
            .also(Action.slack_send_message().channel("incidents"))
        )
        d, _ = wf.build()
        assert len(d["nodes"]) == 3

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
