import json
from unittest.mock import patch

import httpx
import pytest
import respx

from kestrel import KestrelClient, AsyncKestrelClient, Workflow, WorkflowStats, Approval, AuthError


SERVER = "https://test.usekestrel.ai"
TOKEN = "test-session-token"


@pytest.fixture
def client():
    c = KestrelClient(server=SERVER, session_token=TOKEN)
    yield c
    c.close()


class TestWorkflowCRUD:
    @respx.mock
    def test_list_workflows(self, client: KestrelClient):
        respx.get(f"{SERVER}/api/workflows").mock(
            return_value=httpx.Response(200, json=[
                {"id": "wf-1", "name": "Test WF", "status": "active"},
            ])
        )
        wfs = client.workflows.list()
        assert len(wfs) == 1
        assert wfs[0].name == "Test WF"
        assert isinstance(wfs[0], Workflow)

    @respx.mock
    def test_list_workflows_with_status(self, client: KestrelClient):
        route = respx.get(f"{SERVER}/api/workflows").mock(
            return_value=httpx.Response(200, json=[])
        )
        client.workflows.list(status="active")
        assert "status=active" in str(route.calls[0].request.url)

    @respx.mock
    def test_get_workflow(self, client: KestrelClient):
        respx.get(f"{SERVER}/api/workflows/wf-1").mock(
            return_value=httpx.Response(200, json={
                "id": "wf-1", "name": "My WF", "status": "draft",
                "definition": {"nodes": [], "edges": []},
                "trigger_config": {"source": "kubernetes"},
            })
        )
        wf = client.workflows.get("wf-1")
        assert wf.id == "wf-1"
        assert wf.trigger_config["source"] == "kubernetes"

    @respx.mock
    def test_create_workflow(self, client: KestrelClient):
        respx.post(f"{SERVER}/api/workflows").mock(
            return_value=httpx.Response(201, json={
                "id": "wf-new", "name": "New WF", "status": "draft",
            })
        )
        wf = client.workflows.create(
            name="New WF",
            definition={"nodes": [], "edges": []},
            trigger_config={"source": "kubernetes"},
        )
        assert wf.id == "wf-new"

    @respx.mock
    def test_delete_workflow(self, client: KestrelClient):
        respx.delete(f"{SERVER}/api/workflows/wf-1").mock(
            return_value=httpx.Response(200, text="")
        )
        client.workflows.delete("wf-1")

    @respx.mock
    def test_activate_workflow(self, client: KestrelClient):
        respx.post(f"{SERVER}/api/workflows/wf-1/activate").mock(
            return_value=httpx.Response(200, json={"status": "active"})
        )
        client.workflows.activate("wf-1")

    @respx.mock
    def test_pause_workflow(self, client: KestrelClient):
        respx.post(f"{SERVER}/api/workflows/wf-1/pause").mock(
            return_value=httpx.Response(200, json={"status": "paused"})
        )
        client.workflows.pause("wf-1")


class TestGenerate:
    @respx.mock
    def test_generate_workflow(self, client: KestrelClient):
        respx.post(f"{SERVER}/api/workflows/generate").mock(
            return_value=httpx.Response(200, json={
                "success": True,
                "name": "Auto RCA",
                "description": "Runs RCA on crashloop",
                "definition": {"nodes": [{"id": "t1", "type": "trigger"}], "edges": []},
                "trigger_config": {"source": "kubernetes"},
                "explanation": "This workflow triggers on pod crashloops.",
            })
        )
        result = client.workflows.generate("When a pod crashloops, run RCA")
        assert result.success
        assert result.name == "Auto RCA"
        assert len(result.definition["nodes"]) == 1


class TestStats:
    @respx.mock
    def test_get_stats(self, client: KestrelClient):
        respx.get(f"{SERVER}/api/workflows/stats").mock(
            return_value=httpx.Response(200, json={
                "total_workflows": 5,
                "active_workflows": 3,
                "total_executions": 42,
                "status_breakdown": {"completed": 30, "failed": 12},
                "daily_executions": [],
            })
        )
        stats = client.workflows.stats()
        assert stats.total_workflows == 5
        assert stats.status_breakdown["failed"] == 12


class TestApprovals:
    @respx.mock
    def test_list_pending(self, client: KestrelClient):
        respx.get(f"{SERVER}/api/workflow-approvals/pending").mock(
            return_value=httpx.Response(200, json=[
                {"id": "ap-1", "approval_type": "manual", "status": "pending"},
                {"id": "ap-2", "approval_type": "justification", "status": "pending"},
            ])
        )
        approvals = client.approvals.list_pending()
        assert len(approvals) == 2
        assert approvals[1].approval_type == "justification"

    @respx.mock
    def test_approve_with_justification(self, client: KestrelClient):
        route = respx.post(f"{SERVER}/api/workflow-approvals/ap-2/approve").mock(
            return_value=httpx.Response(200, json={"status": "approved"})
        )
        client.approvals.approve("ap-2", justification="Emergency fix")
        body = json.loads(route.calls[0].request.content)
        assert body["justification"] == "Emergency fix"

    @respx.mock
    def test_reject(self, client: KestrelClient):
        respx.post(f"{SERVER}/api/workflow-approvals/ap-1/reject").mock(
            return_value=httpx.Response(200, json={"status": "rejected"})
        )
        client.approvals.reject("ap-1")


class TestRequests:
    @respx.mock
    def test_list_returns_all_statuses(self, client: KestrelClient):
        respx.get(f"{SERVER}/api/workflow-requests").mock(
            return_value=httpx.Response(200, json={
                "requests": [
                    {"id": "r-1", "status": "no_workflow", "prompt": "create vpc"},
                    {"id": "r-2", "status": "executing", "prompt": "create cm"},
                    {"id": "r-3", "status": "rejected", "prompt": "bad request"},
                ],
                "total": 3,
            })
        )
        reqs = client.requests.list()
        assert len(reqs) == 3

    @respx.mock
    def test_list_with_status_filter(self, client: KestrelClient):
        respx.get(f"{SERVER}/api/workflow-requests").mock(
            return_value=httpx.Response(200, json={
                "requests": [
                    {"id": "r-1", "status": "no_workflow", "prompt": "create vpc"},
                    {"id": "r-2", "status": "executing", "prompt": "create cm"},
                ],
                "total": 2,
            })
        )
        reqs = client.requests.list(status="no_workflow")
        assert len(reqs) == 1 and reqs[0].id == "r-1"


class TestAuth:
    def test_missing_config(self):
        with patch("kestrel.client.load_config") as mock_load:
            mock_load.return_value = type("C", (), {"is_logged_in": False})()
            with pytest.raises(AuthError, match="Not logged in"):
                KestrelClient.from_config()

    def _write_config(self, tmp_path, monkeypatch, **fields):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"server_url": SERVER, "session_token": "", **fields}))
        monkeypatch.setattr("kestrel.auth._CONFIG_PATH", path)

    def test_from_config_with_api_key(self, tmp_path, monkeypatch):
        # `kestrel auth kestrel_sk_...` writes api_key and an empty session_token
        self._write_config(tmp_path, monkeypatch, api_key="kestrel_sk_test")
        client = KestrelClient.from_config()
        assert client._http.headers["Authorization"] == "Bearer kestrel_sk_test"
        assert "X-Session-Token" not in client._http.headers

    def test_async_from_config_with_api_key(self, tmp_path, monkeypatch):
        self._write_config(tmp_path, monkeypatch, api_key="kestrel_sk_test")
        client = AsyncKestrelClient.from_config()
        assert client._http.headers["Authorization"] == "Bearer kestrel_sk_test"

    def test_from_config_with_session_token(self, tmp_path, monkeypatch):
        self._write_config(tmp_path, monkeypatch, session_token="tok-123")
        client = KestrelClient.from_config()
        assert client._http.headers["X-Session-Token"] == "tok-123"
        assert "Authorization" not in client._http.headers

    @respx.mock
    def test_auth_error_on_401(self, client: KestrelClient):
        respx.get(f"{SERVER}/api/workflows").mock(
            return_value=httpx.Response(401, text="Unauthorized")
        )
        with pytest.raises(AuthError):
            client.workflows.list()
