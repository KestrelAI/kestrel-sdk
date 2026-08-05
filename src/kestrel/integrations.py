"""Integration registry and connect/test/disconnect namespaces.

Mirrors the Kestrel CLI's integration registry so SDK users (and agents)
can connect any integration programmatically:

    client.integrations.list()
    client.integrations.setup_help("cloudflare")   # where to create credentials
    client.integrations.connect("cloudflare", api_token="...", account_id="...")
    client.integrations.post_connect_hint("cloudflare")  # e.g. webhook setup
    client.integrations.set_webhook_secret("vercel", "whsec_...")  # paste vendor secret
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
    # Where to create the credentials this integration needs (mirrors the
    # platform UI and `kestrel integrations connect <name> --help`).
    setup_help: str = ""
    # Extra hint for after a successful connect (e.g. webhook setup).
    # `{server}` is a placeholder for your Kestrel server URL.
    post_connect_hint: str = ""
    # Endpoint that saves vendor-generated webhook signing secret(s) after
    # connect (PlanetScale, Vercel, Railway, Supabase). Enables
    # ``client.integrations.set_webhook_secret(name, secret)``.
    webhook_secret_path: str = ""


def _token(key: str, name: str, description: str, *fields: IntegrationField,
           setup_help: str = "", post_connect_hint: str = "",
           webhook_secret_path: str = "") -> IntegrationSpec:
    return IntegrationSpec(
        key=key, name=name, kind="token", description=description,
        connect_path=f"/api/integrations/{key}/connect",
        disconnect_path=f"/api/integrations/{key}/disconnect",
        test_path=f"/api/integrations/{key}/test",
        fields=fields,
        setup_help=setup_help,
        post_connect_hint=post_connect_hint,
        webhook_secret_path=webhook_secret_path,
    )


def _knowledge(key: str, name: str, description: str, *fields: IntegrationField,
               setup_help: str = "") -> IntegrationSpec:
    return IntegrationSpec(
        key=key, name=name, kind="knowledge", description=description,
        source_type=key, fields=fields, setup_help=setup_help,
    )


REGISTRY: tuple[IntegrationSpec, ...] = (
    # OAuth / browser flows
    IntegrationSpec(key="github", name="GitHub", kind="oauth",
                    description="Pull request automation and CI/CD triggers (GitHub App install)",
                    setup_help="Connecting GitHub installs the Kestrel GitHub App. connect() returns an install URL — open it in your browser, pick the org/repos to grant, and approve."),
    IntegrationSpec(key="gitlab", name="GitLab", kind="oauth",
                    description="Merge request automation and pipeline triggers (OAuth)",
                    setup_help="Connecting GitLab uses an OAuth flow. connect() returns an authorization URL — open it in your browser and approve access."),
    IntegrationSpec(key="slack", name="Slack", kind="oauth",
                    description="Incident alerts, approvals, and AI responses in Slack (app install)",
                    setup_help="Connecting Slack installs the Kestrel Slack app. connect() returns an install URL — open it in your browser, pick the workspace, and approve."),
    # Cluster / cloud (multi-step; use the CLI)
    IntegrationSpec(key="kubernetes", name="Kubernetes", kind="cluster",
                    description="Onboard a cluster via the Kestrel operator (use the kestrel CLI)",
                    setup_help="Use the Kestrel CLI: `kestrel integrations connect kubernetes` mints an operator token, writes a Helm values file, and prints the 'helm install' command to run against your cluster."),
    IntegrationSpec(key="aws", name="AWS", kind="cloud",
                    description="Connect an AWS account via IAM role (use the kestrel CLI)",
                    setup_help="Use the Kestrel CLI: `kestrel integrations connect aws` runs a two-step IAM role flow (bootstrap with an External ID, then verify with --role-arn). No long-lived AWS keys are stored."),
    IntegrationSpec(key="oci", name="Oracle Cloud (OCI)", kind="cloud",
                    description="Connect an OCI tenancy with API-key auth (use the kestrel CLI)",
                    setup_help="Use the Kestrel CLI: `kestrel integrations connect oci`. API key: OCI Console -> Profile -> My profile -> API keys -> Add API key. Download the private key (PEM) and note the fingerprint, tenancy OCID, and user OCID."),
    # Token integrations
    _token("cloudflare", "Cloudflare", "Zones, Workers, DNS, WAF, and tunnels",
           IntegrationField("api_token", "Cloudflare API token", required=True, secret=True),
           IntegrationField("account_id", "Cloudflare account ID", required=True),
           setup_help=(
               "API token: Cloudflare dashboard -> My Profile -> API Tokens -> Create Token -> Custom Token. "
               "Grant: Zone (DNS Edit, Zone Settings Edit, Zone Read, Analytics Read, Firewall Services "
               "Edit, Health Checks Edit) and Account (Workers Scripts Edit, Workers KV Storage Edit, "
               "Account Analytics Read, Account Settings Read). Scope Account Resources to your account. "
               "Account ID: in the dashboard URL — dash.cloudflare.com/<account-id>/home."
           ),
           post_connect_hint=(
               "To receive alerts, add a webhook in Cloudflare: Manage account -> Notifications -> "
               "Destinations -> Webhooks -> Create, with URL {server}/api/webhooks/cloudflare and the "
               "webhook_secret returned by connect(), then route notifications to it."
           )),
    _token("nebius", "Nebius", "Nebius AI Cloud resources and jobs",
           IntegrationField("credentials", "Service account authorized-key JSON document", required=True, secret=True),
           IntegrationField("region", "Nebius region"),
           setup_help=(
               "Authorized key: Nebius console -> Administration -> IAM -> Service accounts -> your account -> "
               "Keys tab -> Authorized keys (NOT Access keys) -> Upload authorized key. "
               "Or via CLI: nebius iam auth-public-key generate --service-account-id <id> --output authorized-key.json. "
               "Pass the full authorized-key JSON document as the credentials value."
           )),
    _token("jenkins", "Jenkins", "Jenkins builds and job status",
           IntegrationField("base_url", "Jenkins URL", required=True),
           IntegrationField("username", "Jenkins username", required=True),
           IntegrationField("api_token", "Jenkins API token", required=True, secret=True),
           setup_help=(
               "API token: Jenkins -> your user (top right) -> Security -> API Token -> Add new token. "
               "The user needs permission to read jobs and trigger builds. Auth is username + token (HTTP Basic). "
               "The Jenkins URL must be reachable from the Kestrel server."
           ),
           post_connect_hint=(
               "Optional: to receive build events, add a webhook via the Notification plugin (job -> Configure -> "
               "Job Notifications) posting JSON to {server}/api/webhooks/jenkins with the webhook_secret "
               "returned by connect() in the X-Kestrel-Webhook-Secret header."
           )),
    _token("circleci", "CircleCI", "CircleCI workflow and job events",
           IntegrationField("api_token", "CircleCI personal API token", required=True, secret=True),
           IntegrationField("org_slug", "Organization slug (e.g. gh/my-org)"),
           setup_help=(
               "API token: CircleCI -> User Settings -> Personal API Tokens -> Create New Token. "
               "Org slug (optional): Organization Settings -> Overview (e.g. gh/my-org)."
           ),
           post_connect_hint=(
               "To receive workflow/job events, add a webhook per project: Project Settings -> Webhooks -> "
               "Add Webhook with URL {server}/api/webhooks/circleci, the webhook_secret returned by connect(), "
               "and the Workflow Completed + Job Completed events."
           )),
    _token("terraform", "Terraform Cloud", "Terraform Cloud runs and plan/apply events",
           IntegrationField("api_token", "Terraform Cloud API token", required=True, secret=True),
           IntegrationField("organization", "Terraform Cloud organization", required=True),
           IntegrationField("base_url", "Base URL (default https://app.terraform.io)"),
           setup_help=(
               "API token: Terraform Cloud -> Organization Settings -> API Tokens -> Team Tokens (recommended), "
               "or a user token under Account Settings -> Tokens. "
               "Organization: the name in your URL — app.terraform.io/app/<organization>."
           ),
           post_connect_hint=(
               "To receive run events, add a notification per workspace: workspace -> Settings -> Notifications -> "
               "Create a Notification -> Webhook, URL {server}/api/webhooks/terraform, the notification_token "
               "returned by connect(), and select the run events. Repeat for each workspace."
           )),
    _token("pulumi", "Pulumi Cloud", "Pulumi stack updates and deployment events",
           IntegrationField("api_token", "Pulumi access token", required=True, secret=True),
           IntegrationField("organization", "Pulumi organization", required=True),
           IntegrationField("base_url", "Base URL (default https://api.pulumi.com)"),
           setup_help=(
               "Access token: Pulumi Cloud -> Organization Settings -> Access Tokens (recommended), "
               "or a personal token under Personal Settings -> Access Tokens (pul-...). "
               "Organization: the name in your URL — app.pulumi.com/<organization>."
           ),
           post_connect_hint=(
               "To receive stack/deployment events, add a webhook: org Settings -> Integrations -> Webhooks -> "
               "Add webhook (destination: Webhook), payload URL {server}/api/webhooks/pulumi, the "
               "webhook_secret returned by connect(), and check all trigger groups."
           )),
    _token("argocd", "Argo CD", "Argo CD application sync status",
           IntegrationField("server_url", "Argo CD server URL", required=True),
           IntegrationField("api_token", "Argo CD API token", required=True, secret=True),
           setup_help=(
               "API token: generate one in Argo CD -> Settings -> Accounts -> Generate New Token. "
               "The Argo CD server URL must be reachable from the Kestrel server."
           )),
    _token("vercel", "Vercel", "Vercel deployments and rollbacks",
           IntegrationField("api_token", "Vercel API token", required=True, secret=True),
           IntegrationField("team_id", "Vercel team ID"),
           setup_help=(
               "API token: Vercel -> your avatar -> Account Settings -> Tokens. Scope it to your team for "
               "team-level access. Team ID (optional, team_...): Vercel -> Settings -> General; leave blank "
               "for personal accounts."
           ),
           post_connect_hint=(
               "To receive deployment events, add a webhook in Vercel: Settings -> Webhooks -> Create Webhook "
               "with URL {server}/api/webhooks/vercel and the deployment/alert events, then save the signing "
               "secret (shown once) with set_webhook_secret('vercel', secret)."
           ),
           webhook_secret_path="/api/integrations/vercel/webhook-secret"),
    _token("railway", "Railway", "Railway services and deployments",
           IntegrationField("api_token", "Railway API token", required=True, secret=True),
           setup_help=(
               "API token: railway.com/account/tokens (Account Settings -> Tokens). Leave the Workspace "
               "dropdown at \"No workspace\" to mint an account-scoped token that can read your projects, "
               "services, deployments, and logs."
           ),
           post_connect_hint=(
               "To receive deployment events, choose a secret and save it with "
               "set_webhook_secret('railway', secret), then add a webhook per project: Project -> Settings -> "
               "Webhooks with URL {server}/api/webhooks/railway?secret=<your-secret> (Railway doesn't sign webhooks)."
           ),
           webhook_secret_path="/api/integrations/railway/webhook-secret"),
    _token("flyio", "Fly.io", "Fly.io apps, machines, and deployments",
           IntegrationField("api_token", "Fly.io API token", required=True, secret=True),
           IntegrationField("org_slug", "Fly.io organization slug"),
           setup_help=(
               "API token: run 'fly tokens create org' (or create a token in the Fly.io dashboard) with "
               "read access to your organization. "
               "Org slug: find with 'fly orgs list' — use the slug, not the display name (default: personal). "
               "No webhooks needed — Kestrel polls the Fly Machines API."
           )),
    _token("beam", "Beam", "Beam serverless GPU workloads",
           IntegrationField("api_token", "Beam API token", required=True, secret=True),
           IntegrationField("gateway_base_url", "Gateway base URL"),
           setup_help=(
               "API token: Beam dashboard -> Settings -> API Keys & Workspace ID -> Create Key. "
               "Or via CLI: pip install beam-client && beam config create kestrel, then copy the token "
               "from ~/.beam/config.ini. Permissions: Full Access, or Restricted with Read+Write+Delete "
               "on Deployments, Containers, Tasks, Machines and Read on Images, Volumes, Logs. "
               "No webhooks needed — Kestrel polls the Beam API."
           )),
    _token("daytona", "Daytona", "Daytona sandboxes and dev environments",
           IntegrationField("api_key", "Daytona API key", required=True, secret=True),
           IntegrationField("webhook_secret", "Webhook signing secret", required=True, secret=True),
           IntegrationField("api_url", "Daytona API URL"),
           setup_help=(
               "API key: Daytona dashboard -> API Keys -> Create API Key (shown once). Permissions: Full "
               "Access, or Read+Write+Delete on Sandboxes and Snapshots plus Read on Volumes. "
               "Webhook secret (required): Daytona dashboard -> Webhooks -> Enable webhooks -> Create "
               "Endpoint with your Kestrel webhook URL ({server}/api/webhooks/daytona) and all sandbox/"
               "snapshot/volume events, then open the endpoint and copy its Signing Secret (whsec_...)."
           )),
    _token("supabase", "Supabase", "Supabase projects, database health, and auth events",
           IntegrationField("access_token", "Supabase access token", required=True, secret=True),
           IntegrationField("webhook_secret", "Webhook signing secret", secret=True),
           IntegrationField("api_url", "Supabase API URL"),
           setup_help=(
               "Access token: Supabase dashboard -> Account -> Access Tokens -> Generate new token (sbp_...). "
               "Kestrel polls the Management API for project health, backups, replicas, and branches."
           ),
           post_connect_hint=(
               "Optional: for row-level DB events, add a Database Webhook per project (Integrations -> "
               "Database Webhooks) posting to {server}/api/webhooks/supabase with your secret in the "
               "X-Supabase-Webhook-Secret header, then save it with set_webhook_secret('supabase', secret)."
           ),
           webhook_secret_path="/api/integrations/supabase/webhook-secret"),
    _token("planetscale", "PlanetScale", "PlanetScale branches, deploy requests, and database events",
           IntegrationField("token_id", "Service token ID", required=True),
           IntegrationField("token", "Service token", required=True, secret=True),
           IntegrationField("organization", "PlanetScale organization", required=True),
           IntegrationField("webhook_secret", "Webhook signing secret", secret=True),
           setup_help=(
               "Service token: app.planetscale.com -> Settings -> Service tokens -> New service token "
               "(or 'pscale service-token create'). You get a token ID + token (pscale_tkn_...). "
               "Permissions: org-level read_databases (required), plus branch/deploy-request/backup "
               "permissions on the databases you want Kestrel to manage."
           ),
           post_connect_hint=(
               "To receive branch/deploy events, add a webhook per database: Settings -> Webhooks -> "
               "Add webhook with URL {server}/api/webhooks/planetscale. PlanetScale shows a unique signing "
               "secret per webhook — save each with set_webhook_secret('planetscale', secret)."
           ),
           webhook_secret_path="/api/integrations/planetscale/webhook-secret"),
    _token("neon", "Neon", "Neon Postgres projects, branches, and compute",
           IntegrationField("api_key", "Neon API key", required=True, secret=True),
           IntegrationField("org_id", "Neon organization ID (auto-detected for keys with a single org; required if the key can see multiple)"),
           IntegrationField("api_url", "Neon API URL"),
           setup_help=(
               "API key: Neon Console (console.neon.tech) -> Account settings -> API keys -> Create new "
               "API key (napi_..., shown once). Personal or organization keys both work. "
               "Org ID (org-...): auto-detected when the key sees one org; for multiple orgs find it in "
               "the Console URL (console.neon.tech/app/org-.../projects) or Organization settings. "
               "No webhooks needed — Kestrel polls the Neon API."
           )),
    _token("clickhouse", "ClickHouse", "ClickHouse Cloud services and query performance",
           IntegrationField("key_id", "ClickHouse API key ID", required=True),
           IntegrationField("key_secret", "ClickHouse API key secret", required=True, secret=True),
           IntegrationField("org_id", "ClickHouse organization ID"),
           IntegrationField("api_url", "ClickHouse API URL"),
           setup_help=(
               "API key: ClickHouse Cloud console (console.clickhouse.cloud) -> click your organization "
               "name (bottom left) -> API keys -> New API key. Assign the Admin role (Developer keys are "
               "read-only). Key ID and secret are shown once. Org ID is auto-detected from the key. "
               "No webhooks needed — Kestrel polls the ClickHouse Cloud API."
           )),
    _token("posthog", "PostHog", "PostHog product analytics, feature flags, and errors",
           IntegrationField("api_key", "PostHog personal API key", required=True, secret=True),
           IntegrationField("project_id", "PostHog project ID", required=True),
           IntegrationField("host", "PostHog host (default https://us.posthog.com)"),
           setup_help=(
               "Personal API key: PostHog -> Settings -> Personal API Keys (phx_...). Required scopes: "
               "project:read, session_recording:write, query:read, error_tracking:read. "
               "Project ID: PostHog -> Settings. Host: us.posthog.com / eu.posthog.com / self-hosted."
           ),
           post_connect_hint=(
               "To receive events (exceptions, rage clicks), add a destination: PostHog -> Data -> "
               "Destinations -> New Destination -> HTTP Webhook posting to {server}/api/webhooks/posthog."
           )),
    _token("pagerduty", "PagerDuty", "Incident routing and on-call alerting",
           IntegrationField("api_token", "PagerDuty REST API token", required=True, secret=True),
           IntegrationField("webhook_secret", "Webhook signing secret", required=True, secret=True),
           setup_help=(
               "API token: PagerDuty -> your user icon -> My Profile -> User Settings -> Create API User "
               "Token. Must be a USER-level token — account-level API Access Keys will not work. "
               "Webhook secret (required): PagerDuty -> Integrations -> Generic Webhooks (V3) -> New "
               "Webhook with your Kestrel webhook URL ({server}/api/webhooks/pagerduty), Scope Type = "
               "Account, subscribed to incident events; copy the signing secret it shows."
           )),
    _token("vault", "HashiCorp Vault", "Vault KV secrets, policies, leases, and rotation",
           IntegrationField("address", "Vault address (https://vault.example.com:8200)", required=True),
           IntegrationField("token", "Vault token", required=True, secret=True),
           IntegrationField("namespace", "Vault namespace (Enterprise/HCP; e.g. admin)"),
           setup_help=(
               "Token: create a periodic, renewable token bound to a dedicated Kestrel policy, e.g. "
               "`vault token create -policy=kestrel -period=768h`. Grant the policy read/list on "
               "sys/health, sys/mounts, sys/policies/acl, sys/auth, and the KV metadata/ paths you want "
               "monitored, plus write only where workflows need it. Namespace (Enterprise/HCP only): "
               "HCP Vault uses 'admin'; leave blank for OSS Vault. No webhooks needed — Kestrel polls "
               "the Vault API (secret values are never read by triggers)."
           )),
    _token("infisical", "Infisical", "Infisical secrets, approvals, and secret syncs",
           IntegrationField("client_id", "Machine Identity client ID", required=True),
           IntegrationField("client_secret", "Machine Identity client secret", required=True, secret=True),
           IntegrationField("site_url", "Site URL (default https://app.infisical.com)"),
           setup_help=(
               "Machine Identity: Infisical -> Organization -> Access Control -> Machine Identities -> "
               "Create identity, then add it to the projects you want to automate. Open its Universal "
               "Auth method and copy the Client ID (not the identity's ID) and create a Client Secret. "
               "Site URL: leave blank for Infisical "
               "Cloud US; use "
               "https://eu.infisical.com for EU Cloud or your own URL for self-hosted. No webhooks "
               "needed — Kestrel polls the Infisical audit log and project APIs (secret-change triggers "
               "need a paid plan for audit log access; secret values are never read by triggers)."
           )),
    _token("sonarcloud", "SonarCloud", "SonarCloud code quality gates, issues, and security hotspots",
           IntegrationField("organization", "SonarCloud organization key", required=True),
           IntegrationField("api_token", "SonarCloud API token", required=True, secret=True),
           setup_help=(
               "API token: sonarcloud.io -> your avatar -> My Account -> Access Tokens -> Generate Token. "
               "Organization key: sonarcloud.io -> your organization -> the key in the URL "
               "(sonarcloud.io/organizations/<key>) or Administration -> Organization settings."
           ),
           post_connect_hint=(
               "To receive analysis events, add a webhook in SonarCloud: open your organization and select "
               "Webhooks in the left sidebar (for a single project: Administration -> Webhooks), then Create, "
               "with URL {server}/api/webhooks/sonarcloud and the "
               "webhook_secret returned by connect() (SonarCloud signs deliveries with it via the "
               "X-Sonar-Webhook-HMAC-SHA256 header)."
           )),
    _token("okta", "Okta", "Okta identity security: users, groups, sessions, and System Log triggers",
           IntegrationField("org_url", "Okta org URL (https://your-org.okta.com)", required=True),
           IntegrationField("api_token", "Okta API token (SSWS)", required=True, secret=True),
           setup_help=(
               "API token (SSWS): Okta Admin Console -> Security -> API -> Tokens -> Create token. "
               "Org URL: your Okta domain, e.g. https://your-org.okta.com (shown in the Admin Console "
               "header). The token inherits the permissions of the admin who created it; a read-only "
               "admin token works for triggers and read blocks, while lifecycle/session blocks need a "
               "super admin or org admin token. No webhooks needed — Kestrel polls the Okta System Log "
               "for security events."
           )),
    _token("databricks", "Databricks", "Databricks jobs, clusters, DLT pipelines, and SQL warehouses",
           IntegrationField("workspace_url", "Databricks workspace URL (https://dbc-xxx.cloud.databricks.com)", required=True),
           IntegrationField("api_token", "Databricks personal access token", required=True, secret=True),
           setup_help=(
               "Personal access token: your workspace -> Settings -> Developer -> Access tokens -> "
               "Generate new token. Under Scope choose 'Other APIs' and select the jobs, clusters, "
               "pipelines, sql, and query-history API scopes (avoid 'all APIs'). A service-principal "
               "token is recommended for production. "
               "Workspace URL: the workspace base URL from the browser address bar, e.g. "
               "https://dbc-a1b2c3d4-e5f6.cloud.databricks.com (Azure: https://adb-xxxx.azuredatabricks.net). "
               "No webhooks needed — Kestrel polls the Databricks REST API for job-run, cluster, and "
               "DLT pipeline events."
           )),
    # Knowledge sources
    _knowledge("confluence", "Confluence", "Confluence runbooks and docs for AI context",
               IntegrationField("base_url", "Atlassian site URL", required=True),
               IntegrationField("api_key", "Atlassian account email", required=True),
               IntegrationField("api_token", "Atlassian API token", required=True, secret=True),
               setup_help=(
                   "API token: id.atlassian.com/manage-profile/security/api-tokens -> Create API token. "
                   "Auth is your Atlassian account email + the token (Basic auth)."
               )),
    _knowledge("jira", "Jira", "Jira issues for incident context and ticket creation",
               IntegrationField("base_url", "Atlassian site URL", required=True),
               IntegrationField("api_key", "Atlassian account email", required=True),
               IntegrationField("api_token", "Atlassian API token", required=True, secret=True),
               setup_help=(
                   "API token: id.atlassian.com/manage-profile/security/api-tokens -> Create API token. "
                   "Auth is your Atlassian account email + the token (Basic auth)."
               )),
    _knowledge("linear", "Linear", "Linear issues for incident context and ticket creation",
               IntegrationField("api_key", "Linear API key", required=True, secret=True),
               setup_help=(
                   "API key: linear.app/settings/account/security -> Personal API keys -> New API Key. "
                   "Personal keys inherit your permissions — consider a service account for production."
               )),
    _knowledge("notion", "Notion", "Notion pages and runbooks for AI context",
               IntegrationField("api_token", "Notion integration token", required=True, secret=True),
               setup_help=(
                   "Integration token: notion.so/my-integrations -> New integration -> select workspace -> "
                   "copy the Internal Integration Secret. Then share each page/database you want searchable "
                   "with the integration (Notion pages are not visible to integrations by default)."
               )),
    _knowledge("glean", "Glean", "Company-wide knowledge search via Glean",
               IntegrationField("api_key", "Glean API key", required=True, secret=True),
               IntegrationField("base_url", "Glean instance URL"),
               setup_help=(
                   "API key: Glean Admin Console -> API -> API Keys -> Create API Key with the search:read "
                   "scope. API access requires an Enterprise plan — ask your Glean administrator to enable it."
               )),
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


def _expand_server(text: str, server_url: str) -> str:
    return text.replace("{server}", server_url or "<your-kestrel-server>")


def _webhook_secret_request(name: str, secret: str) -> tuple[str, dict[str, Any]]:
    """Validate and build the request for saving a vendor-generated webhook secret."""
    spec = get_spec(name)
    if not spec.webhook_secret_path:
        supported = ", ".join(sorted(s.key for s in REGISTRY if s.webhook_secret_path))
        raise KestrelError(
            f"{spec.name} does not take a pasted webhook secret — supported: {supported}"
        )
    if not secret or not secret.strip():
        raise ValidationError(
            f"webhook secret is required for {spec.name}", missing_fields=["secret"]
        )
    return spec.webhook_secret_path, {"webhook_secret": secret.strip()}


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

    def setup_help(self, name: str) -> str:
        """Where to create the credentials an integration needs.

        Mirrors the setup instructions shown in the Kestrel platform UI and
        by ``kestrel integrations connect <name> --help``. ``{server}``
        placeholders are expanded to this client's server URL.
        """
        spec = get_spec(name)
        return _expand_server(spec.setup_help, self._c._config.server_url)

    def post_connect_hint(self, name: str) -> str:
        """Follow-up steps after connecting (e.g. webhook setup), or ''."""
        spec = get_spec(name)
        return _expand_server(spec.post_connect_hint, self._c._config.server_url)

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

    def set_webhook_secret(self, name: str, secret: str) -> dict[str, Any]:
        """Save a vendor-generated webhook signing secret after connect.

        Supported for integrations where the third party generates the secret
        (Vercel, Railway, PlanetScale, Supabase). The stored API token is kept
        as-is. For PlanetScale (one secret per database webhook), call once
        per secret — new secrets are merged with the ones already stored.
        """
        path, body = _webhook_secret_request(name, secret)
        return self._c._post(path, json=body) or {"status": "saved"}

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

    def setup_help(self, name: str) -> str:
        """Where to create the credentials an integration needs."""
        spec = get_spec(name)
        return _expand_server(spec.setup_help, self._c._config.server_url)

    def post_connect_hint(self, name: str) -> str:
        """Follow-up steps after connecting (e.g. webhook setup), or ''."""
        spec = get_spec(name)
        return _expand_server(spec.post_connect_hint, self._c._config.server_url)

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

    async def set_webhook_secret(self, name: str, secret: str) -> dict[str, Any]:
        """Save a vendor-generated webhook signing secret after connect."""
        path, body = _webhook_secret_request(name, secret)
        return await self._c._post(path, json=body) or {"status": "saved"}

    async def _find_knowledge_source(self, spec: IntegrationSpec) -> dict[str, Any]:
        data = await self._c._get("/api/tribal-knowledge/sources")
        for src in data.get("sources", []):
            if src.get("source_type") == spec.source_type:
                return src
        raise KestrelError(f"No {spec.name} source is connected")
