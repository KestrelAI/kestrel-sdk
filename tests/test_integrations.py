import httpx
import pytest
import respx

from kestrel import KestrelClient, AsyncKestrelClient, KestrelError, ValidationError, IntegrationStatus
from kestrel.integrations import REGISTRY, get_spec


SERVER = "https://test.usekestrel.ai"
TOKEN = "test-session-token"


@pytest.fixture
def client():
    c = KestrelClient(server=SERVER, session_token=TOKEN)
    yield c
    c.close()


class TestRegistry:
    def test_keys_unique(self):
        keys = [s.key for s in REGISTRY]
        assert len(keys) == len(set(keys))

    def test_token_specs_have_paths(self):
        for spec in REGISTRY:
            if spec.kind == "token":
                assert spec.connect_path.startswith("/api/integrations/"), spec.key
                assert spec.disconnect_path, spec.key
                assert any(f.required for f in spec.fields), spec.key

    def test_knowledge_specs_have_source_type(self):
        for spec in REGISTRY:
            if spec.kind == "knowledge":
                assert spec.source_type, spec.key
                assert spec.fields, spec.key

    def test_get_spec_unknown(self):
        with pytest.raises(KestrelError, match="Unknown integration"):
            get_spec("does-not-exist")

    def test_get_spec_case_insensitive(self):
        assert get_spec("Cloudflare").key == "cloudflare"

    def test_all_specs_have_setup_help(self):
        # Parity with the CLI: every integration explains where to create
        # its credentials (or how to run the multi-step flow).
        for spec in REGISTRY:
            assert spec.setup_help, spec.key

    def test_webhook_hints_use_server_placeholder(self):
        for spec in REGISTRY:
            if "/api/webhooks/" in spec.post_connect_hint:
                assert "{server}/api/webhooks/" in spec.post_connect_hint, spec.key


class TestSetupHelp:
    def test_setup_help_expands_server(self, client: KestrelClient):
        hint = client.integrations.setup_help("daytona")
        assert f"{SERVER}/api/webhooks/daytona" in hint
        assert "{server}" not in hint

    def test_post_connect_hint_expands_server(self, client: KestrelClient):
        hint = client.integrations.post_connect_hint("cloudflare")
        assert f"{SERVER}/api/webhooks/cloudflare" in hint
        assert "{server}" not in hint

    def test_post_connect_hint_empty_when_none(self, client: KestrelClient):
        assert client.integrations.post_connect_hint("argocd") == ""

    def test_setup_help_unknown(self, client: KestrelClient):
        with pytest.raises(KestrelError, match="Unknown integration"):
            client.integrations.setup_help("does-not-exist")


class TestListIntegrations:
    @respx.mock
    def test_list(self, client: KestrelClient):
        respx.get(f"{SERVER}/api/workflows/integrations/status").mock(
            return_value=httpx.Response(200, json=[
                {"id": "cloudflare", "name": "Cloudflare", "connected": True},
                {"id": "github", "name": "GitHub", "connected": False},
            ])
        )
        statuses = client.integrations.list()
        assert len(statuses) == 2
        assert isinstance(statuses[0], IntegrationStatus)
        assert statuses[0].connected is True

    def test_specs(self, client: KestrelClient):
        specs = client.integrations.specs()
        assert any(s.key == "pagerduty" for s in specs)


class TestConnectToken:
    @respx.mock
    def test_connect_cloudflare(self, client: KestrelClient):
        route = respx.post(f"{SERVER}/api/integrations/cloudflare/connect").mock(
            return_value=httpx.Response(200, json={"status": "connected"})
        )
        result = client.integrations.connect("cloudflare", api_token="tok", account_id="acc")
        assert result == {"status": "connected"}
        assert route.called
        import json
        body = json.loads(route.calls[0].request.content)
        assert body == {"api_token": "tok", "account_id": "acc"}

    def test_connect_missing_required(self, client: KestrelClient):
        with pytest.raises(ValidationError) as exc:
            client.integrations.connect("cloudflare", api_token="tok")
        assert "account_id" in str(exc.value)

    def test_connect_unknown_field(self, client: KestrelClient):
        with pytest.raises(ValidationError, match="Unknown credential fields"):
            client.integrations.connect("cloudflare", api_token="t", account_id="a", bogus="x")

    def test_connect_cli_only(self, client: KestrelClient):
        with pytest.raises(KestrelError, match="kestrel integrations connect kubernetes"):
            client.integrations.connect("kubernetes")


class TestConnectOAuth:
    @respx.mock
    def test_connect_github_returns_url(self, client: KestrelClient):
        respx.get(f"{SERVER}/api/tenant/github/connect").mock(
            return_value=httpx.Response(200, json={"installation_url": "https://github.com/apps/x/installations/new"})
        )
        url = client.integrations.connect("github")
        assert url.startswith("https://github.com/")

    @respx.mock
    def test_connect_slack_returns_url(self, client: KestrelClient):
        respx.get(f"{SERVER}/api/integrations/slack/install-url").mock(
            return_value=httpx.Response(200, json={"install_url": "https://slack.com/oauth/v2/authorize?x=1"})
        )
        url = client.integrations.connect("slack")
        assert "slack.com" in url


class TestConnectKnowledge:
    @respx.mock
    def test_connect_linear(self, client: KestrelClient):
        route = respx.post(f"{SERVER}/api/tribal-knowledge/sources").mock(
            return_value=httpx.Response(200, json={"message": "ok", "source": {"id": "src-1"}})
        )
        client.integrations.connect("linear", api_key="lin_xxx")
        import json
        body = json.loads(route.calls[0].request.content)
        assert body["source_type"] == "linear"
        assert body["enabled"] is True
        assert body["api_key"] == "lin_xxx"


class TestTestAndDisconnect:
    @respx.mock
    def test_test_token(self, client: KestrelClient):
        respx.post(f"{SERVER}/api/integrations/vercel/test").mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        assert client.integrations.test("vercel") == {"success": True}

    @respx.mock
    def test_test_knowledge(self, client: KestrelClient):
        respx.get(f"{SERVER}/api/tribal-knowledge/sources").mock(
            return_value=httpx.Response(200, json={"sources": [{"id": "src-9", "source_type": "notion"}]})
        )
        respx.post(f"{SERVER}/api/tribal-knowledge/sources/src-9/test").mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        assert client.integrations.test("notion") == {"success": True}

    @respx.mock
    def test_test_knowledge_not_connected(self, client: KestrelClient):
        respx.get(f"{SERVER}/api/tribal-knowledge/sources").mock(
            return_value=httpx.Response(200, json={"sources": []})
        )
        with pytest.raises(KestrelError, match="No Notion source"):
            client.integrations.test("notion")

    @respx.mock
    def test_disconnect_token(self, client: KestrelClient):
        route = respx.post(f"{SERVER}/api/integrations/railway/disconnect").mock(
            return_value=httpx.Response(200, json={})
        )
        client.integrations.disconnect("railway")
        assert route.called

    @respx.mock
    def test_disconnect_knowledge(self, client: KestrelClient):
        respx.get(f"{SERVER}/api/tribal-knowledge/sources").mock(
            return_value=httpx.Response(200, json={"sources": [{"id": "src-2", "source_type": "jira"}]})
        )
        route = respx.delete(f"{SERVER}/api/tribal-knowledge/sources/src-2").mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        client.integrations.disconnect("jira")
        assert route.called

    def test_disconnect_oauth_rejected(self, client: KestrelClient):
        with pytest.raises(KestrelError, match="Kestrel UI"):
            client.integrations.disconnect("slack")


class TestSetWebhookSecret:
    def test_registry_paths(self):
        supported = {s.key for s in REGISTRY if s.webhook_secret_path}
        assert supported == {"vercel", "railway", "planetscale", "supabase"}
        for spec in REGISTRY:
            if spec.webhook_secret_path:
                assert spec.webhook_secret_path == f"/api/integrations/{spec.key}/webhook-secret"
                # The post-connect hint should tell users how to save the secret.
                assert "set_webhook_secret" in spec.post_connect_hint, spec.key

    @respx.mock
    def test_set_webhook_secret_vercel(self, client: KestrelClient):
        route = respx.post(f"{SERVER}/api/integrations/vercel/webhook-secret").mock(
            return_value=httpx.Response(200, json={"status": "saved"})
        )
        result = client.integrations.set_webhook_secret("vercel", "whsec_123")
        assert result == {"status": "saved"}
        import json
        body = json.loads(route.calls[0].request.content)
        assert body == {"webhook_secret": "whsec_123"}

    @respx.mock
    def test_set_webhook_secret_planetscale_merges(self, client: KestrelClient):
        respx.post(f"{SERVER}/api/integrations/planetscale/webhook-secret").mock(
            return_value=httpx.Response(200, json={"status": "saved", "webhook_secret_count": 2})
        )
        result = client.integrations.set_webhook_secret("planetscale", "pscale_wh_abc")
        assert result["webhook_secret_count"] == 2

    def test_set_webhook_secret_strips_whitespace(self, client: KestrelClient):
        with respx.mock:
            route = respx.post(f"{SERVER}/api/integrations/supabase/webhook-secret").mock(
                return_value=httpx.Response(200, json={"status": "saved"})
            )
            client.integrations.set_webhook_secret("supabase", "  secret  \n")
            import json
            body = json.loads(route.calls[0].request.content)
            assert body == {"webhook_secret": "secret"}

    def test_set_webhook_secret_unsupported(self, client: KestrelClient):
        with pytest.raises(KestrelError, match="does not take a pasted webhook secret"):
            client.integrations.set_webhook_secret("cloudflare", "s")

    def test_set_webhook_secret_empty(self, client: KestrelClient):
        with pytest.raises(ValidationError, match="webhook secret is required"):
            client.integrations.set_webhook_secret("vercel", "   ")

    def test_set_webhook_secret_unknown(self, client: KestrelClient):
        with pytest.raises(KestrelError, match="Unknown integration"):
            client.integrations.set_webhook_secret("does-not-exist", "s")


class TestAsyncIntegrations:
    @respx.mock
    @pytest.mark.asyncio
    async def test_async_connect(self):
        respx.post(f"{SERVER}/api/integrations/cloudflare/connect").mock(
            return_value=httpx.Response(200, json={"status": "connected"})
        )
        async with AsyncKestrelClient(server=SERVER, session_token=TOKEN) as c:
            result = await c.integrations.connect("cloudflare", api_token="t", account_id="a")
            assert result == {"status": "connected"}

    @respx.mock
    @pytest.mark.asyncio
    async def test_async_list(self):
        respx.get(f"{SERVER}/api/workflows/integrations/status").mock(
            return_value=httpx.Response(200, json=[{"id": "aws", "name": "AWS", "connected": False}])
        )
        async with AsyncKestrelClient(server=SERVER, session_token=TOKEN) as c:
            statuses = await c.integrations.list()
            assert statuses[0].id == "aws"

    @pytest.mark.asyncio
    async def test_async_setup_help(self):
        async with AsyncKestrelClient(server=SERVER, session_token=TOKEN) as c:
            hint = c.integrations.setup_help("pagerduty")
            assert f"{SERVER}/api/webhooks/pagerduty" in hint
            assert c.integrations.post_connect_hint("railway")

    @respx.mock
    @pytest.mark.asyncio
    async def test_async_set_webhook_secret(self):
        respx.post(f"{SERVER}/api/integrations/railway/webhook-secret").mock(
            return_value=httpx.Response(200, json={"status": "saved"})
        )
        async with AsyncKestrelClient(server=SERVER, session_token=TOKEN) as c:
            result = await c.integrations.set_webhook_secret("railway", "my-secret")
            assert result == {"status": "saved"}

    @pytest.mark.asyncio
    async def test_async_set_webhook_secret_unsupported(self):
        async with AsyncKestrelClient(server=SERVER, session_token=TOKEN) as c:
            with pytest.raises(KestrelError, match="does not take a pasted webhook secret"):
                await c.integrations.set_webhook_secret("jenkins", "s")
