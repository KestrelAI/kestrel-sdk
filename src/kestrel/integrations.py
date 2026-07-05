"""Integration registry and connect/test/disconnect namespaces.

Mirrors the Kestrel CLI's integration registry so SDK users (and agents)
can connect any integration programmatically:

    client.integrations.list()
    client.integrations.connect("cloudflare", api_token="...", account_id="...")
    client.integrations.test("cloudflare")
    client.integrations.disconnect("cloudflare")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .exceptions import KestrelError, ValidationError
from .models import IntegrationStatus


@dataclass(frozen=True)
class IntegrationField:
    """One credential/config input for a token or knowledge integration."""

    name: str  # JSON body field name (e.g. "api_token")
    usage: str
    required: bool = False
    secret: bool = False


@dataclass(frozen=True)
class IntegrationSpec:
    """Describes how one integration is connected."""

    key: str
    name: str
    kind: str  # token | oauth | cluster | cloud | knowledge
    description: str
    connect_path: str = ""
    disconnect_path: str = ""
    test_path: str = ""
    fields: tuple[IntegrationField, ...] = field(default_factory=tuple)
    source_type: str = ""  # knowledge integrations only


def _token(key: str, name: str, description: str, *fields: IntegrationField) -> IntegrationSpec:
    return IntegrationSpec(
        key=key, name=name, kind="token", description=description,
        connect_path=f"/api/integrations/{key}/connect",
        disconnect_path=f"/api/integrations/{key}/disconnect",
        test_path=f"/api/integrations/{key}/test",
        fields=fields,
    )


def _knowledge(key: str, name: str, description: str, *fields: IntegrationField) -> IntegrationSpec:
    return IntegrationSpec(
        key=key, name=name, kind="knowledge", description=description,
        source_type=key, fields=fields,
    )


REGISTRY: tuple[IntegrationSpec, ...] = (
    # OAuth / browser flows
    IntegrationSpec(key="github", name="GitHub", kind="oauth",
                    description="Pull request automation and CI/CD triggers (GitHub App install)"),
    IntegrationSpec(key="gitlab", name="GitLab", kind="oauth",
                    description="Merge request automation and pipeline triggers (OAuth)"),
    IntegrationSpec(key="slack", name="Slack", kind="oauth",
                    description="Incident alerts, approvals, and AI responses in Slack (app install)"),
    # Cluster / cloud (multi-step; use the CLI)
    IntegrationSpec(key="kubernetes", name="Kubernetes", kind="cluster",
                    description="Onboard a cluster via the Kestrel operator (use the kestrel CLI)"),
    IntegrationSpec(key="aws", name="AWS", kind="cloud",
                    description="Connect an AWS account via IAM role (use the kestrel CLI)"),
    IntegrationSpec(key="oci", name="Oracle Cloud (OCI)", kind="cloud",
                    description="Connect an OCI tenancy with API-key auth (use the kestrel CLI)"),
    # Token integrations
    _token("cloudflare", "Cloudflare", "Zones, Workers, DNS, WAF, and tunnels",
           IntegrationField("api_token", "Cloudflare API token", required=True, secret=True),
           IntegrationField("account_id", "Cloudflare account ID", required=True)),
    _token("nebius", "Nebius", "Nebius AI Cloud resources and jobs",
           IntegrationField("credentials", "Service account authorized-key JSON document", required=True, secret=True),
           IntegrationField("region", "Nebius region")),
    _token("jenkins", "Jenkins", "Jenkins builds and job status",
           IntegrationField("base_url", "Jenkins URL", required=True),
           IntegrationField("username", "Jenkins username", required=True),
           IntegrationField("api_token", "Jenkins API token", required=True, secret=True)),
    _token("circleci", "CircleCI", "CircleCI workflow and job events",
           IntegrationField("api_token", "CircleCI personal API token", required=True, secret=True),
           IntegrationField("org_slug", "Organization slug (e.g. gh/my-org)")),
    _token("terraform", "Terraform Cloud", "Terraform Cloud runs and plan/apply events",
           IntegrationField("api_token", "Terraform Cloud API token", required=True, secret=True),
           IntegrationField("organization", "Terraform Cloud organization", required=True),
           IntegrationField("base_url", "Base URL (default https://app.terraform.io)")),
    _token("pulumi", "Pulumi Cloud", "Pulumi stack updates and deployment events",
           IntegrationField("api_token", "Pulumi access token", required=True, secret=True),
           IntegrationField("organization", "Pulumi organization", required=True),
           IntegrationField("base_url", "Base URL (default https://api.pulumi.com)")),
    _token("argocd", "Argo CD", "Argo CD application sync status",
           IntegrationField("server_url", "Argo CD server URL", required=True),
           IntegrationField("api_token", "Argo CD API token", required=True, secret=True)),
    _token("vercel", "Vercel", "Vercel deployments and rollbacks",
           IntegrationField("api_token", "Vercel API token", required=True, secret=True),
           IntegrationField("team_id", "Vercel team ID")),
    _token("railway", "Railway", "Railway services and deployments",
           IntegrationField("api_token", "Railway API token", required=True, secret=True)),
    _token("flyio", "Fly.io", "Fly.io apps, machines, and deployments",
           IntegrationField("api_token", "Fly.io API token", required=True, secret=True),
           IntegrationField("org_slug", "Fly.io organization slug")),
    _token("beam", "Beam", "Beam serverless GPU workloads",
           IntegrationField("api_token", "Beam API token", required=True, secret=True),
           IntegrationField("gateway_base_url", "Gateway base URL")),
    _token("daytona", "Daytona", "Daytona sandboxes and dev environments",
           IntegrationField("api_key", "Daytona API key", required=True, secret=True),
           IntegrationField("webhook_secret", "Webhook signing secret", required=True, secret=True),
           IntegrationField("api_url", "Daytona API URL")),
    _token("supabase", "Supabase", "Supabase projects, database health, and auth events",
           IntegrationField("access_token", "Supabase access token", required=True, secret=True),
           IntegrationField("webhook_secret", "Webhook signing secret", secret=True),
           IntegrationField("api_url", "Supabase API URL")),
    _token("planetscale", "PlanetScale", "PlanetScale branches, deploy requests, and database events",
           IntegrationField("token_id", "Service token ID", required=True),
           IntegrationField("token", "Service token", required=True, secret=True),
           IntegrationField("organization", "PlanetScale organization", required=True),
           IntegrationField("webhook_secret", "Webhook signing secret", secret=True)),
    _token("neon", "Neon", "Neon Postgres projects, branches, and compute",
           IntegrationField("api_key", "Neon API key", required=True, secret=True),
           IntegrationField("org_id", "Neon organization ID"),
           IntegrationField("api_url", "Neon API URL")),
    _token("clickhouse", "ClickHouse", "ClickHouse Cloud services and query performance",
           IntegrationField("key_id", "ClickHouse API key ID", required=True),
           IntegrationField("key_secret", "ClickHouse API key secret", required=True, secret=True),
           IntegrationField("org_id", "ClickHouse organization ID"),
           IntegrationField("api_url", "ClickHouse API URL")),
    _token("posthog", "PostHog", "PostHog product analytics, feature flags, and errors",
           IntegrationField("api_key", "PostHog personal API key", required=True, secret=True),
           IntegrationField("project_id", "PostHog project ID", required=True),
           IntegrationField("host", "PostHog host (default https://us.posthog.com)")),
    _token("pagerduty", "PagerDuty", "Incident routing and on-call alerting",
           IntegrationField("api_token", "PagerDuty REST API token", required=True, secret=True),
           IntegrationField("webhook_secret", "Webhook signing secret", required=True, secret=True)),
    # Knowledge sources
    _knowledge("confluence", "Confluence", "Confluence runbooks and docs for AI context",
               IntegrationField("base_url", "Atlassian site URL", required=True),
               IntegrationField("api_key", "Atlassian account email", required=True),
               IntegrationField("api_token", "Atlassian API token", required=True, secret=True)),
    _knowledge("jira", "Jira", "Jira issues for incident context and ticket creation",
               IntegrationField("base_url", "Atlassian site URL", required=True),
               IntegrationField("api_key", "Atlassian account email", required=True),
               IntegrationField("api_token", "Atlassian API token", required=True, secret=True)),
    _knowledge("linear", "Linear", "Linear issues for incident context and ticket creation",
               IntegrationField("api_key", "Linear API key", required=True, secret=True)),
    _knowledge("notion", "Notion", "Notion pages and runbooks for AI context",
               IntegrationField("api_token", "Notion integration token", required=True, secret=True)),
    _knowledge("glean", "Glean", "Company-wide knowledge search via Glean",
               IntegrationField("api_key", "Glean API key", required=True, secret=True),
               IntegrationField("base_url", "Glean instance URL")),
)

_BY_KEY = {spec.key: spec for spec in REGISTRY}


def get_spec(key: str) -> IntegrationSpec:
    spec = _BY_KEY.get(key.lower())
    if spec is None:
        available = ", ".join(sorted(_BY_KEY))
        raise KestrelError(f"Unknown integration {key!r} — available: {available}")
    return spec


def _validate_credentials(spec: IntegrationSpec, credentials: dict[str, Any]) -> dict[str, Any]:
    """Check required fields and drop unknown/empty ones."""
    known = {f.name for f in spec.fields}
    unknown = sorted(set(credentials) - known)
    if unknown:
        raise ValidationError(
            f"Unknown credential fields for {spec.name}: {', '.join(unknown)} — "
            f"expected: {', '.join(sorted(known))}",
            missing_fields=[],
        )
    missing = [f.name for f in spec.fields if f.required and not credentials.get(f.name)]
    if missing:
        raise ValidationError(
            f"Missing required credentials for {spec.name}: {', '.join(missing)}",
            missing_fields=missing,
        )
    return {k: v for k, v in credentials.items() if v not in (None, "")}


def _knowledge_body(spec: IntegrationSpec, credentials: dict[str, Any]) -> dict[str, Any]:
    body = _validate_credentials(spec, credentials)
    body["source_type"] = spec.source_type
    body["name"] = spec.name
    body["enabled"] = True
    return body


_OAUTH_ENDPOINTS = {
    "github": ("/api/tenant/github/connect", "installation_url"),
    "gitlab": ("/api/tenant/gitlab/connect", "authorization_url"),
    "slack": ("/api/integrations/slack/install-url", "install_url"),
}

_CLI_ONLY_MSG = (
    "{name} uses a multi-step flow — connect it with the Kestrel CLI: "
    "kestrel integrations connect {key} --help"
)


class IntegrationsNamespace:
    """Sync integration management."""

    def __init__(self, client: Any):
        self._c = client

    def list(self) -> list[IntegrationStatus]:
        """List every integration with its connection status."""
        data = self._c._get("/api/workflows/integrations/status")
        return [IntegrationStatus.model_validate(i) for i in data]

    def specs(self) -> list[IntegrationSpec]:
        """Return the full integration registry (credential requirements etc.)."""
        return list(REGISTRY)

    def connect(self, name: str, **credentials: Any) -> dict[str, Any] | str:
        """Connect an integration.

        Token/knowledge integrations take credential kwargs (see
        :meth:`specs` for required fields per integration). OAuth
        integrations return the authorization URL to open in a browser.
        """
        spec = get_spec(name)
        if spec.kind == "token":
            body = _validate_credentials(spec, credentials)
            return self._c._post(spec.connect_path, json=body) or {"status": "connected"}
        if spec.kind == "knowledge":
            data = self._c._post("/api/tribal-knowledge/sources", json=_knowledge_body(spec, credentials))
            return data or {"status": "connected"}
        if spec.kind == "oauth":
            path, url_field = _OAUTH_ENDPOINTS[spec.key]
            data = self._c._get(path)
            return data[url_field]
        raise KestrelError(_CLI_ONLY_MSG.format(name=spec.name, key=spec.key))

    def test(self, name: str) -> dict[str, Any]:
        """Test a connected integration's credentials."""
        spec = get_spec(name)
        if spec.kind == "token":
            if not spec.test_path:
                raise KestrelError(f"{spec.name} does not support connection tests")
            return self._c._post(spec.test_path) or {}
        if spec.kind == "knowledge":
            src = self._find_knowledge_source(spec)
            return self._c._post(f"/api/tribal-knowledge/sources/{src['id']}/test") or {}
        raise KestrelError(f"{spec.name} does not support tests — check status with integrations.list()")

    def disconnect(self, name: str) -> None:
        """Disconnect a token integration or knowledge source."""
        spec = get_spec(name)
        if spec.kind == "token":
            self._c._post(spec.disconnect_path)
            return
        if spec.kind == "knowledge":
            src = self._find_knowledge_source(spec)
            self._c._delete(f"/api/tribal-knowledge/sources/{src['id']}")
            return
        raise KestrelError(f"{spec.name} must be disconnected in the Kestrel UI")

    def _find_knowledge_source(self, spec: IntegrationSpec) -> dict[str, Any]:
        data = self._c._get("/api/tribal-knowledge/sources")
        for src in data.get("sources", []):
            if src.get("source_type") == spec.source_type:
                return src
        raise KestrelError(f"No {spec.name} source is connected")


class AsyncIntegrationsNamespace:
    """Async integration management — mirrors :class:`IntegrationsNamespace`."""

    def __init__(self, client: Any):
        self._c = client

    async def list(self) -> list[IntegrationStatus]:
        data = await self._c._get("/api/workflows/integrations/status")
        return [IntegrationStatus.model_validate(i) for i in data]

    def specs(self) -> list[IntegrationSpec]:
        return list(REGISTRY)

    async def connect(self, name: str, **credentials: Any) -> dict[str, Any] | str:
        spec = get_spec(name)
        if spec.kind == "token":
            body = _validate_credentials(spec, credentials)
            return await self._c._post(spec.connect_path, json=body) or {"status": "connected"}
        if spec.kind == "knowledge":
            data = await self._c._post("/api/tribal-knowledge/sources", json=_knowledge_body(spec, credentials))
            return data or {"status": "connected"}
        if spec.kind == "oauth":
            path, url_field = _OAUTH_ENDPOINTS[spec.key]
            data = await self._c._get(path)
            return data[url_field]
        raise KestrelError(_CLI_ONLY_MSG.format(name=spec.name, key=spec.key))

    async def test(self, name: str) -> dict[str, Any]:
        spec = get_spec(name)
        if spec.kind == "token":
            if not spec.test_path:
                raise KestrelError(f"{spec.name} does not support connection tests")
            return await self._c._post(spec.test_path) or {}
        if spec.kind == "knowledge":
            src = await self._find_knowledge_source(spec)
            return await self._c._post(f"/api/tribal-knowledge/sources/{src['id']}/test") or {}
        raise KestrelError(f"{spec.name} does not support tests — check status with integrations.list()")

    async def disconnect(self, name: str) -> None:
        spec = get_spec(name)
        if spec.kind == "token":
            await self._c._post(spec.disconnect_path)
            return
        if spec.kind == "knowledge":
            src = await self._find_knowledge_source(spec)
            await self._c._delete(f"/api/tribal-knowledge/sources/{src['id']}")
            return
        raise KestrelError(f"{spec.name} must be disconnected in the Kestrel UI")

    async def _find_knowledge_source(self, spec: IntegrationSpec) -> dict[str, Any]:
        data = await self._c._get("/api/tribal-knowledge/sources")
        for src in data.get("sources", []):
            if src.get("source_type") == spec.source_type:
                return src
        raise KestrelError(f"No {spec.name} source is connected")
