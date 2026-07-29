"""Action builder for workflow definitions.

Each static factory method returns an ``Action`` pre-configured with the
correct integration and action ID.  Chain config convenience methods to set
action-specific parameters::

    action = (
        Action.jira_create_ticket()
        .project("KAN")
        .title("{{incident.title}}")
        .priority("High")
        .label("Create Jira Ticket")
    )
"""

from __future__ import annotations

from typing import Any, Union

from .types import _Node

# A numeric config value that may be a literal number or a template string
# (e.g. "{{request.replicas}}"). The server resolves template strings to numbers
# at execution time, so numeric setters accept both.
Number = Union[int, float, str]


class Action:
    """Workflow action node builder."""

    def __init__(self, integration: str, action: str) -> None:
        self._integration = integration
        self._action = action
        self._config: dict[str, Any] = {}
        self._label: str = ""

    # -- Generic helpers ---------------------------------------------------

    def label(self, text: str) -> Action:
        self._label = text
        return self

    def config(self, key: str, value: Any) -> Action:
        """Set an arbitrary config key (generic escape hatch)."""
        self._config[key] = value
        return self

    # -- Shared convenience methods (used by many actions) -----------------

    def title(self, template: str) -> Action:
        return self.config("title_template", template)

    def body(self, template: str) -> Action:
        return self.config("body_template", template)

    def message(self, template: str) -> Action:
        return self.config("message_template", template)

    def channel(self, ch: str) -> Action:
        return self.config("channel", ch)

    def repo(self, name: str) -> Action:
        return self.config("repo", name)

    def project(self, key: str) -> Action:
        return self.config("project_key", key)

    def query(self, q: str) -> Action:
        return self.config("query", q)

    def cluster_id(self, cid: str) -> Action:
        return self.config("cluster_id", cid)

    # -- Kestrel -----------------------------------------------------------

    def include_metrics(self, v: bool = True) -> Action:
        return self.config("include_metrics", v)

    def include_logs(self, v: bool = True) -> Action:
        return self.config("include_logs", v)

    def include_tribal_knowledge(self, v: bool = True) -> Action:
        return self.config("include_tribal_knowledge", v)

    def dry_run_first(self, v: bool = True) -> Action:
        return self.config("dry_run_first", v)

    def duration(self, n: Number) -> Action:
        return self.config("duration", n)

    def unit(self, u: str) -> Action:
        return self.config("unit", u)

    def operation(self, op: str) -> Action:
        return self.config("operation", op)

    def resource_type(self, rt: str) -> Action:
        return self.config("resource_type", rt)

    def name(self, n: str) -> Action:
        return self.config("name", n)

    def ns(self, namespace: str) -> Action:
        return self.config("namespace", namespace)

    def additional_spec(self, spec: str) -> Action:
        return self.config("additional_spec", spec)

    def gitops_repo(self, r: str) -> Action:
        return self.config("gitops_repo", r)

    def gitops_root_path(self, p: str) -> Action:
        return self.config("gitops_root_path", p)

    def git_provider(self, gp: str) -> Action:
        return self.config("git_provider", gp)

    def base_path(self, bp: str) -> Action:
        return self.config("base_path", bp)

    def branch_prefix(self, bp: str) -> Action:
        return self.config("branch_prefix", bp)

    def chart_name(self, cn: str) -> Action:
        return self.config("chart_name", cn)

    def parameters(self, p: str) -> Action:
        return self.config("parameters", p)

    def cloud_service(self, *svcs: str) -> Action:
        return self.config("cloud_service", list(svcs))

    def output_format(self, f: str) -> Action:
        return self.config("output_format", f)

    def region(self, r: str) -> Action:
        return self.config("region", r)

    def resource_spec(self, spec: str) -> Action:
        return self.config("resource_spec", spec)

    def require_approval(self, v: bool = True) -> Action:
        return self.config("require_approval", v)

    def max_iterations(self, n: Number) -> Action:
        return self.config("max_iterations", n)

    def workload_name(self, wn: str) -> Action:
        return self.config("workload_name", wn)

    def analysis_type(self, at: str) -> Action:
        return self.config("analysis_type", at)

    def context(self, c: str) -> Action:
        return self.config("context", c)

    # -- Slack -------------------------------------------------------------

    def dm_user(self, user_id: str) -> Action:
        return self.config("dm_user_id", user_id)

    def mention_users(self, *user_ids: str) -> Action:
        return self.config("mention_user_ids", ",".join(user_ids))

    def include_rca(self, v: bool = True) -> Action:
        return self.config("include_rca", v)

    def include_fixes(self, v: bool = True) -> Action:
        return self.config("include_fixes", v)

    def prompt_message(self, msg: str) -> Action:
        return self.config("prompt_message", msg)

    # -- Jira --------------------------------------------------------------

    def issue_type(self, it: str) -> Action:
        return self.config("issue_type", it)

    def priority(self, p: str) -> Action:
        return self.config("priority", p)

    def assignee(self, a: str) -> Action:
        return self.config("assignee", a)

    def ticket_key(self, key: str) -> Action:
        return self.config("ticket_key", key)

    def status(self, s: str) -> Action:
        return self.config("status", s)

    # -- Linear --------------------------------------------------------------

    def team(self, key: str) -> Action:
        return self.config("team_key", key)

    def issue_identifier(self, identifier: str) -> Action:
        return self.config("issue_identifier", identifier)

    def project_name(self, name: str) -> Action:
        return self.config("project", name)

    def limit(self, n: Number) -> Action:
        return self.config("limit", n)

    # -- Confluence --------------------------------------------------------

    def space_key(self, sk: str) -> Action:
        return self.config("space_key", sk)

    def parent_page_id(self, pid: str) -> Action:
        return self.config("parent_page_id", pid)

    def page_id(self, pid: str) -> Action:
        return self.config("page_id", pid)

    def section(self, s: str) -> Action:
        return self.config("section", s)

    def content(self, template: str) -> Action:
        return self.config("content_template", template)

    # -- GitHub / GitLab ---------------------------------------------------

    def labels(self, l: str) -> Action:
        return self.config("labels", l)

    def workflow_file(self, wf: str) -> Action:
        return self.config("workflow_file", wf)

    def ref(self, r: str) -> Action:
        return self.config("ref", r)

    def inputs(self, kv: dict[str, str]) -> Action:
        return self.config("inputs", kv)

    def timeout_minutes(self, n: Number) -> Action:
        return self.config("timeout_minutes", n)

    def poll_interval_seconds(self, n: Number) -> Action:
        return self.config("poll_interval_seconds", n)

    def path(self, p: str) -> Action:
        return self.config("path", p)

    def max_turns(self, n: Number) -> Action:
        return self.config("max_turns", n)

    # -- Datadog -----------------------------------------------------------

    def timeframe(self, tf: str) -> Action:
        return self.config("timeframe", tf)

    def monitor_type(self, mt: str) -> Action:
        return self.config("type", mt)

    def critical_threshold(self, v: Number) -> Action:
        return self.config("critical_threshold", v)

    def warning_threshold(self, v: Number) -> Action:
        return self.config("warning_threshold", v)

    def alert_type(self, at: str) -> Action:
        return self.config("alert_type", at)

    def tags(self, t: str) -> Action:
        return self.config("tags", t)

    def text(self, template: str) -> Action:
        return self.config("text_template", template)

    def scope(self, s: str) -> Action:
        return self.config("scope", s)

    def duration_minutes(self, n: Number) -> Action:
        return self.config("duration_minutes", n)

    def monitor_id(self, mid: str) -> Action:
        return self.config("monitor_id", mid)

    # -- PagerDuty ---------------------------------------------------------

    def service(self, s: str) -> Action:
        return self.config("service", s)

    def severity(self, s: str) -> Action:
        return self.config("severity", s)

    def resolution_note(self, note: str) -> Action:
        return self.config("resolution_note", note)

    def escalation_policy(self, ep: str) -> Action:
        return self.config("escalation_policy_id", ep)

    # -- ArgoCD ------------------------------------------------------------

    def app_name(self, name: str) -> Action:
        return self.config("app_name", name)

    # -- Argo Rollouts -----------------------------------------------------

    def rollout_name(self, name: str) -> Action:
        return self.config("rollout_name", name)

    def full(self, v: bool = True) -> Action:
        return self.config("full", v)

    def revision(self, n: Number) -> Action:
        return self.config("revision", n)

    # -- Flux CD -----------------------------------------------------------

    def resource_kind(self, kind: str) -> Action:
        return self.config("resource_kind", kind)

    def resource_name(self, name: str) -> Action:
        return self.config("resource_name", name)

    def with_source(self, v: bool = True) -> Action:
        return self.config("with_source", v)

    # -- Karpenter ---------------------------------------------------------

    def nodepool_name(self, name: str) -> Action:
        return self.config("nodepool_name", name)

    def nodeclaim_name(self, name: str) -> Action:
        return self.config("nodeclaim_name", name)

    def cpu_limit(self, limit: str) -> Action:
        return self.config("cpu_limit", limit)

    def memory_limit(self, limit: str) -> Action:
        return self.config("memory_limit", limit)

    def consolidation_policy(self, policy: str) -> Action:
        return self.config("consolidation_policy", policy)

    def consolidate_after(self, duration: str) -> Action:
        return self.config("consolidate_after", duration)

    def nodepool_spec(self, manifest: str) -> Action:
        return self.config("nodepool_spec", manifest)

    # -- Kyverno -------------------------------------------------------------
    # cluster_id() / ns() / severity() / max_results() are shared helpers.

    def policy_name(self, name: str) -> Action:
        """The Kyverno ClusterPolicy (or namespaced Policy) to operate on."""
        return self.config("policy_name", name)

    def policy_filter(self, name: str) -> Action:
        """Limit violation listing to results produced by one policy."""
        return self.config("policy", name)

    def result_filter(self, result: str) -> Action:
        """Which PolicyReport results to include ("fail", "warn", "error",
        "fail,warn,error", or "all")."""
        return self.config("result", result)

    def enforcement_action(self, action: str) -> Action:
        """"Enforce" (block at admission) or "Audit" (report only)."""
        return self.config("enforcement_action", action)

    def policy_spec(self, manifest: str) -> Action:
        """Full ClusterPolicy/Policy manifest (YAML or JSON)."""
        return self.config("policy_spec", manifest)

    # -- Trivy ---------------------------------------------------------------
    # cluster_id() / ns() / severity() / resource_kind() / max_results() are
    # shared helpers.

    def workload(self, w: str) -> Action:
        """The scanned workload — accepts "kind/name" (e.g. deployment/nginx)
        or just the workload name."""
        return self.config("workload", w)

    def fixed_only(self, v: bool = True) -> Action:
        """Only include CVEs that have a fixed version available."""
        return self.config("fixed_only", v)

    def report_kind(self, kind: str) -> Action:
        """Which trivy-operator report kinds to aggregate ("config-audit",
        "rbac-assessment", "infra-assessment", or "all")."""
        return self.config("report_kind", kind)

    def report_name(self, name: str) -> Action:
        """The ClusterComplianceReport to read (e.g. "cis", "nsa",
        "pss-baseline", "pss-restricted")."""
        return self.config("report_name", name)

    # -- Fly.io ------------------------------------------------------------

    def machine_id(self, mid: str) -> Action:
        return self.config("machine_id", mid)

    def prune(self, v: bool = True) -> Action:
        return self.config("prune", v)

    def wait_timeout_seconds(self, n: Number) -> Action:
        return self.config("wait_timeout_seconds", n)

    # -- AWS Cost ----------------------------------------------------------

    def aws_account(self, acct: str) -> Action:
        return self.config("aws_account", acct)

    def granularity(self, g: str) -> Action:
        return self.config("granularity", g)

    def time_range(self, tr: str) -> Action:
        return self.config("time_range", tr)

    def group_by(self, gb: str) -> Action:
        return self.config("group_by", gb)

    def filter_service(self, s: str) -> Action:
        return self.config("filter_service", s)

    def lookback_days(self, n: Number) -> Action:
        return self.config("lookback_days", n)

    def min_impact(self, n: Number) -> Action:
        return self.config("min_impact", n)

    def forecast_days(self, d: str) -> Action:
        return self.config("forecast_days", d)

    def budget_name(self, bn: str) -> Action:
        return self.config("budget_name", bn)

    # -- PostHog -----------------------------------------------------------

    def session_ids(self, ids: str) -> Action:
        return self.config("session_ids", ids)

    def session_id(self, sid: str) -> Action:
        return self.config("session_id", sid)

    def focus_area(self, fa: str) -> Action:
        return self.config("focus_area", fa)

    def limit(self, n: Number) -> Action:
        return self.config("limit", n)

    def date_from(self, d: str) -> Action:
        return self.config("date_from", d)

    def issue_id(self, iid: str) -> Action:
        return self.config("issue_id", iid)

    # -- Vercel ------------------------------------------------------------

    def deployment_id(self, did: str) -> Action:
        return self.config("deployment_id", did)

    def project_id(self, pid: str) -> Action:
        return self.config("project_id", pid)

    def state(self, s: str) -> Action:
        return self.config("state", s)

    def target(self, t: str) -> Action:
        return self.config("target", t)

    # -- Nebius ------------------------------------------------------------

    def instance_id(self, iid: str) -> Action:
        return self.config("instance_id", iid)

    def cluster_id(self, cid: str) -> Action:
        return self.config("cluster_id", cid)

    def node_group_id(self, ngid: str) -> Action:
        return self.config("node_group_id", ngid)

    def platform(self, p: str) -> Action:
        """Nebius compute platform, e.g. "gpu-h100-sxm" or "cpu-d3" (availability varies by project region)."""
        return self.config("platform", p)

    def preset(self, p: str) -> Action:
        """Nebius resource preset, e.g. "1gpu-16vcpu-200gb" or "4vcpu-16gb"."""
        return self.config("preset", p)

    def subnet_id(self, sid: str) -> Action:
        return self.config("subnet_id", sid)

    # -- Daytona -----------------------------------------------------------

    def sandbox_id(self, sid: str) -> Action:
        return self.config("sandbox_id", sid)

    def size(self, n: Number) -> Action:
        return self.config("size", n)

    # -- Terraform Cloud -----------------------------------------------------

    def workspace(self, w: str) -> Action:
        return self.config("workspace", w)

    def run_id(self, rid: str) -> Action:
        return self.config("run_id", rid)

    def run_message(self, template: str) -> Action:
        """Run message shown in Terraform Cloud (config key "message")."""
        return self.config("message", template)

    def auto_apply(self, v: bool = True) -> Action:
        return self.config("auto_apply", v)

    def comment(self, c: str) -> Action:
        return self.config("comment", c)

    def reason(self, r: str) -> Action:
        return self.config("reason", r)

    def key(self, k: str) -> Action:
        return self.config("key", k)

    def value(self, v: str) -> Action:
        return self.config("value", v)

    def category(self, c: str) -> Action:
        """Variable category: "terraform" or "env"."""
        return self.config("category", c)

    def hcl(self, v: bool = True) -> Action:
        return self.config("hcl", v)

    def sensitive(self, v: bool = True) -> Action:
        return self.config("sensitive", v)

    # -- Pulumi Cloud ----------------------------------------------------------
    # (operation and deployment_id helpers are shared with other integrations
    # above; they set the same config keys Pulumi actions expect.)

    def stack(self, s: str) -> Action:
        """Pulumi stack reference in project/stack format (e.g.
        "my-project/prod"). Defaults to "{{signal.stack}}" when triggered by
        a Pulumi Cloud event."""
        return self.config("stack", s)

    def update_version(self, v: str) -> Action:
        """Pulumi update version number (blank for the latest update)."""
        return self.config("version", v)

    def tag_name(self, name: str) -> Action:
        return self.config("tag_name", name)

    def tag_value(self, value: str) -> Action:
        return self.config("tag_value", value)

    # -- HashiCorp Vault -------------------------------------------------------
    # (key, value, path, name, limit helpers are shared with other
    # integrations above; they set the same config keys Vault actions expect.)

    def mount(self, m: str) -> Action:
        """Secrets engine mount (e.g. "secret/" for KV v2, "database/" for
        the database engine)."""
        return self.config("mount", m)

    def secret_version(self, v: Number) -> Action:
        """Specific KV v2 secret version to read (blank for the latest)."""
        return self.config("version", v)

    def secret_data(self, json_data: str) -> Action:
        """JSON object of key/value pairs to store, e.g.
        '{"password": "{{step_outputs.action-1.value}}"}'."""
        return self.config("data", json_data)

    def destroy(self, v: bool = True) -> Action:
        """Permanently destroy all versions instead of a soft-delete."""
        return self.config("destroy", v)

    def role(self, r: str) -> Action:
        """Vault database static role name."""
        return self.config("role", r)

    def policy_hcl(self, hcl: str) -> Action:
        """HCL policy document for vault_write_policy."""
        return self.config("policy", hcl)

    def lease_prefix(self, p: str) -> Action:
        return self.config("prefix", p)

    def lease_id(self, lid: str) -> Action:
        return self.config("lease_id", lid)

    def increment(self, seconds: Number) -> Action:
        """Requested TTL extension in seconds for vault_renew_lease."""
        return self.config("increment", seconds)

    def accessor(self, a: str) -> Action:
        """Token accessor for vault_revoke_token_accessor."""
        return self.config("accessor", a)

    # -- Infisical -------------------------------------------------------------
    # (project sets "project" via infisical_project below because the shared
    # .project() helper sets "project_key" for Jira.)

    def infisical_project(self, p: str) -> Action:
        """Infisical project (name or ID)."""
        return self.config("project", p)

    def environment(self, env: str) -> Action:
        """Infisical environment slug (e.g. "dev", "staging", "prod")."""
        return self.config("environment", env)

    def secret_path(self, p: str) -> Action:
        """Infisical folder path (e.g. "/backend"). Defaults to "/"."""
        return self.config("secret_path", p)

    def secret_key(self, k: str) -> Action:
        """Infisical secret name (e.g. "DB_PASSWORD")."""
        return self.config("key", k)

    def secret_value(self, v: str) -> Action:
        """Infisical secret value; can reference previous step outputs."""
        return self.config("value", v)

    def sync_id(self, sid: str) -> Action:
        """Infisical secret sync to trigger (defaults to "{{signal.sync_id}}")."""
        return self.config("sync_id", sid)

    def event_type(self, et: str) -> Action:
        """Audit-log event type filter (e.g. "create-secret")."""
        return self.config("event_type", et)

    # -- Jenkins -------------------------------------------------------------

    def job(self, j: str) -> Action:
        """Jenkins job full name (folder-nested jobs use a path like
        "platform/deploy-api")."""
        return self.config("job", j)

    def build_number(self, b: str) -> Action:
        """Build number (or blank for the last build). Accepts templates like
        "{{signal.build_number}}"."""
        return self.config("build_number", b)

    def max_lines(self, n: Number) -> Action:
        return self.config("max_lines", n)

    # -- CircleCI ------------------------------------------------------------

    def project_slug(self, slug: str) -> Action:
        """CircleCI project slug like "gh/org/repo"."""
        return self.config("project_slug", slug)

    def pipeline_id(self, pid: str) -> Action:
        return self.config("pipeline_id", pid)

    def workflow_id(self, wid: str) -> Action:
        return self.config("workflow_id", wid)

    def branch(self, b: str) -> Action:
        return self.config("branch", b)

    def tag(self, t: str) -> Action:
        return self.config("tag", t)

    def job_number(self, jn: str) -> Action:
        return self.config("job_number", jn)

    def job_name(self, jn: str) -> Action:
        return self.config("job_name", jn)

    # -- SonarCloud ----------------------------------------------------------

    def sonar_project(self, key: str) -> Action:
        """SonarCloud project key (e.g. "my-org_my-repo"). Defaults to
        "{{signal.project_key}}" from a SonarCloud trigger when unset."""
        return self.config("project", key)

    def issue_types(self, *types: str) -> Action:
        """Restrict listed issues to types: VULNERABILITY, BUG, CODE_SMELL."""
        return self.config("types", list(types))

    def severities(self, *severities: str) -> Action:
        """Restrict listed issues to severities: BLOCKER, CRITICAL, MAJOR,
        MINOR, INFO."""
        return self.config("severities", list(severities))

    def max_results(self, n: Number) -> Action:
        return self.config("max_results", n)

    def hotspot_status(self, status: str) -> Action:
        """Restrict listed hotspots by review status: TO_REVIEW or REVIEWED."""
        return self.config("hotspot_status", status)

    def metric_keys(self, keys: str) -> Action:
        """Comma-separated SonarCloud metric keys (e.g.
        "bugs,vulnerabilities,coverage")."""
        return self.config("metric_keys", keys)

    def new_code_only(self, v: bool = True) -> Action:
        """Only issues introduced in the new code period (since the leak
        period) — ideal after a quality gate failure."""
        return self.config("new_code_only", v)

    def issue_key(self, key: str) -> Action:
        """SonarCloud issue key to act on (transition / assign / comment)."""
        return self.config("issue_key", key)

    def transition(self, t: str) -> Action:
        """Issue workflow transition: confirm, unconfirm, reopen, resolve,
        falsepositive, or wontfix."""
        return self.config("transition", t)

    def hotspot_key(self, key: str) -> Action:
        """SonarCloud security hotspot key to review."""
        return self.config("hotspot_key", key)

    def hotspot_resolution(self, resolution: str) -> Action:
        """Hotspot review outcome when marking REVIEWED: SAFE, FIXED, or
        ACKNOWLEDGED."""
        return self.config("resolution", resolution)

    # -- Okta ----------------------------------------------------------------

    def okta_user(self, user: str) -> Action:
        """Okta user (login, email, or ID). Defaults to
        "{{signal.target_user}}" from an Okta trigger when unset."""
        return self.config("user", user)

    def okta_group(self, group: str) -> Action:
        """Okta group (name or ID)."""
        return self.config("group", group)

    def okta_user_status(self, status: str) -> Action:
        """Restrict listed users by lifecycle status (ACTIVE, LOCKED_OUT,
        SUSPENDED, PASSWORD_EXPIRED, PROVISIONED, DEPROVISIONED)."""
        return self.config("user_status", status)

    def okta_event_types(self, types: str) -> Action:
        """Comma-separated Okta System Log event types to query (e.g.
        "user.account.lock,user.session.start")."""
        return self.config("event_types", types)

    def search(self, keyword: str) -> Action:
        """Free-text keyword filter (Okta System Log queries: matches actor,
        target, IP, etc.)."""
        return self.config("search", keyword)

    def since_hours(self, n: Number) -> Action:
        """How many hours of Okta System Log history to query (up to 168)."""
        return self.config("since_hours", n)

    def revoke_oauth_tokens(self, v: bool = True) -> Action:
        """Also revoke the user's OIDC/OAuth access and refresh tokens when
        clearing sessions."""
        return self.config("revoke_oauth_tokens", v)

    def from_failed(self, v: bool = True) -> Action:
        return self.config("from_failed", v)

    # ======================================================================
    # Factory methods — Kestrel
    # ======================================================================

    @staticmethod
    def kestrel_trigger_rca() -> Action:
        return Action("kestrel", "kestrel-trigger-rca")

    @staticmethod
    def kestrel_apply_yaml_fix() -> Action:
        return Action("kestrel", "kestrel-apply-yaml-fix")

    @staticmethod
    def kestrel_find_causal_prs() -> Action:
        return Action("kestrel", "kestrel-find-causal-prs")

    @staticmethod
    def kestrel_trigger_cloud_rca() -> Action:
        return Action("kestrel", "kestrel-trigger-cloud-rca")

    @staticmethod
    def kestrel_generate_runbook() -> Action:
        """Distill the upstream RCA + fixes into a reusable, generalized runbook
        document (Markdown + HTML). Requires an upstream RCA step
        (``kestrel_trigger_rca`` or ``kestrel_trigger_cloud_rca``). Outputs
        ``runbook``, ``runbook_markdown`` and ``runbook_html`` into the context;
        feed ``runbook_html`` to ``confluence_publish_runbook`` to publish."""
        return Action("kestrel", "kestrel-generate-runbook")

    @staticmethod
    def kestrel_wait() -> Action:
        return Action("kestrel", "kestrel-wait")

    @staticmethod
    def kubectl_execute(command: str = "", cluster_id: str = "") -> Action:
        a = Action("kestrel", "kestrel-kubectl-execute")
        if command:
            a = a.config(command=command)
        if cluster_id:
            a = a.config(cluster_id=cluster_id)
        return a

    @staticmethod
    def generate_kubectl_command(query: str = "", cluster_id: str = "") -> Action:
        """AI generates a kubectl command from natural language. Pipe output to kubectl_execute."""
        a = Action("kestrel", "kestrel-generate-kubectl-command")
        if query:
            a = a.config(query=query)
        if cluster_id:
            a = a.config(cluster_id=cluster_id)
        return a

    @staticmethod
    def kestrel_generate_k8s_manifest() -> Action:
        return Action("kestrel", "kestrel-generate-k8s-manifest")

    @staticmethod
    def kestrel_apply_k8s_manifest() -> Action:
        return Action("kestrel", "kestrel-apply-k8s-manifest")

    @staticmethod
    def kestrel_create_gitops_pr() -> Action:
        return Action("kestrel", "kestrel-create-gitops-pr")

    @staticmethod
    def kestrel_generate_helm_values() -> Action:
        return Action("kestrel", "kestrel-generate-helm-values")

    @staticmethod
    def kestrel_generate_cloud_resource() -> Action:
        return Action("kestrel", "kestrel-generate-cloud-resource")

    @staticmethod
    def kestrel_execute_cloud_cli() -> Action:
        return Action("kestrel", "kestrel-execute-cloud-cli")

    @staticmethod
    def kestrel_create_iac_pr() -> Action:
        return Action("kestrel", "kestrel-create-iac-pr")

    @staticmethod
    def kestrel_investigate_cloud() -> Action:
        return Action("kestrel", "kestrel-investigate-cloud")

    @staticmethod
    def kestrel_investigate_k8s() -> Action:
        return Action("kestrel", "kestrel-investigate-k8s")

    @staticmethod
    def kestrel_find_service_deps() -> Action:
        return Action("kestrel", "kestrel-find-service-deps")

    @staticmethod
    def kestrel_analyze_costs() -> Action:
        return Action("kestrel", "kestrel-analyze-costs")

    # ======================================================================
    # Factory methods — GitHub
    # ======================================================================

    @staticmethod
    def github_create_pr() -> Action:
        return Action("github", "github-create-pr")

    @staticmethod
    def github_create_issue() -> Action:
        return Action("github", "github-create-issue")

    @staticmethod
    def github_trigger_workflow() -> Action:
        return Action("github", "github-trigger-workflow")

    @staticmethod
    def github_wait_for_run() -> Action:
        return Action("github", "github-wait-for-run")

    @staticmethod
    def github_get_run_status() -> Action:
        return Action("github", "github-get-run-status")

    @staticmethod
    def github_read_file() -> Action:
        return Action("github", "github-read-file")

    @staticmethod
    def github_search_code() -> Action:
        return Action("github", "github-search-code")

    @staticmethod
    def github_investigate_code() -> Action:
        return Action("github", "github-investigate-code")

    @staticmethod
    def github_analyze_push() -> Action:
        """Analyze a git push to determine affected services/components."""
        return Action("github", "github-analyze-push")

    @staticmethod
    def github_generate_code_fix() -> Action:
        return Action("github", "github-generate-code-fix")

    @staticmethod
    def github_wait_pr_approval() -> Action:
        return Action("github", "github-wait-pr-approval")

    @staticmethod
    def github_wait_pr_merge() -> Action:
        return Action("github", "github-wait-pr-merge")

    @staticmethod
    def github_investigate_action_failure() -> Action:
        return Action("github", "github-investigate-action-failure")

    # ======================================================================
    # Factory methods — GitLab
    # ======================================================================

    @staticmethod
    def gitlab_create_mr() -> Action:
        return Action("gitlab", "gitlab-create-mr")

    @staticmethod
    def gitlab_create_issue() -> Action:
        return Action("gitlab", "gitlab-create-issue")

    @staticmethod
    def gitlab_trigger_pipeline() -> Action:
        return Action("gitlab", "gitlab-trigger-pipeline")

    @staticmethod
    def gitlab_wait_for_pipeline() -> Action:
        return Action("gitlab", "gitlab-wait-for-pipeline")

    @staticmethod
    def gitlab_get_pipeline_status() -> Action:
        return Action("gitlab", "gitlab-get-pipeline-status")

    @staticmethod
    def gitlab_wait_mr_approval() -> Action:
        return Action("gitlab", "gitlab-wait-mr-approval")

    @staticmethod
    def gitlab_wait_mr_merge() -> Action:
        return Action("gitlab", "gitlab-wait-mr-merge")

    # ======================================================================
    # Factory methods — Slack
    # ======================================================================

    @staticmethod
    def slack_send_message() -> Action:
        return Action("slack", "slack-send-message")

    @staticmethod
    def slack_update_message() -> Action:
        return Action("slack", "slack-update-message")

    @staticmethod
    def slack_request_justification() -> Action:
        return Action("slack", "slack-request-justification")

    # ======================================================================
    # Factory methods — Confluence
    # ======================================================================

    @staticmethod
    def confluence_publish_rca() -> Action:
        return Action("confluence", "confluence-publish-rca")

    @staticmethod
    def confluence_publish_postmortem() -> Action:
        return Action("confluence", "confluence-publish-postmortem")

    @staticmethod
    def confluence_publish_runbook() -> Action:
        return Action("confluence", "confluence-publish-runbook")

    @staticmethod
    def confluence_update_page() -> Action:
        return Action("confluence", "confluence-update-page")

    # ======================================================================
    # Factory methods — Jira
    # ======================================================================

    @staticmethod
    def jira_create_ticket() -> Action:
        return Action("jira", "jira-create-ticket")

    @staticmethod
    def jira_add_comment() -> Action:
        return Action("jira", "jira-add-comment")

    @staticmethod
    def jira_transition_ticket() -> Action:
        return Action("jira", "jira-transition-ticket")

    # ======================================================================
    # Factory methods — Linear
    # ======================================================================

    @staticmethod
    def linear_create_issue() -> Action:
        return Action("linear", "linear-create-issue")

    @staticmethod
    def linear_add_comment() -> Action:
        return Action("linear", "linear-add-comment")

    @staticmethod
    def linear_update_issue() -> Action:
        return Action("linear", "linear-update-issue")

    @staticmethod
    def linear_search_issues() -> Action:
        return Action("linear", "linear-search-issues")

    # ======================================================================
    # Factory methods — Datadog
    # ======================================================================

    @staticmethod
    def datadog_query_metrics() -> Action:
        return Action("datadog", "datadog-query-metrics")

    @staticmethod
    def datadog_create_monitor() -> Action:
        return Action("datadog", "datadog-create-monitor")

    @staticmethod
    def datadog_send_event() -> Action:
        return Action("datadog", "datadog-send-event")

    @staticmethod
    def datadog_mute_monitor() -> Action:
        return Action("datadog", "datadog-mute-monitor")

    # ======================================================================
    # Factory methods — PagerDuty
    # ======================================================================

    @staticmethod
    def pagerduty_create_alert() -> Action:
        return Action("pagerduty", "pagerduty-create-alert")

    @staticmethod
    def pagerduty_acknowledge_alert() -> Action:
        return Action("pagerduty", "pagerduty-acknowledge-alert")

    @staticmethod
    def pagerduty_add_note() -> Action:
        return Action("pagerduty", "pagerduty-add-note")

    @staticmethod
    def pagerduty_resolve_alert() -> Action:
        return Action("pagerduty", "pagerduty-resolve-alert")

    @staticmethod
    def pagerduty_escalate() -> Action:
        return Action("pagerduty", "pagerduty-escalate")

    # ======================================================================
    # Factory methods — ArgoCD
    # ======================================================================

    @staticmethod
    def argocd_sync() -> Action:
        return Action("argocd", "argocd-sync")

    @staticmethod
    def argocd_wait_sync() -> Action:
        return Action("argocd", "argocd-wait-sync")

    @staticmethod
    def argocd_get_status() -> Action:
        return Action("argocd", "argocd-get-status")

    @staticmethod
    def argocd_rollback() -> Action:
        return Action("argocd", "argocd-rollback")

    @staticmethod
    def argocd_find_app() -> Action:
        return Action("argocd", "argocd-find-app")

    # ======================================================================
    # Factory methods — Argo Rollouts
    # ======================================================================

    @staticmethod
    def rollouts_promote() -> Action:
        return Action("argo-rollouts", "rollouts-promote")

    @staticmethod
    def rollouts_abort() -> Action:
        return Action("argo-rollouts", "rollouts-abort")

    @staticmethod
    def rollouts_retry() -> Action:
        return Action("argo-rollouts", "rollouts-retry")

    @staticmethod
    def rollouts_undo() -> Action:
        return Action("argo-rollouts", "rollouts-undo")

    @staticmethod
    def rollouts_pause() -> Action:
        return Action("argo-rollouts", "rollouts-pause")

    @staticmethod
    def rollouts_resume() -> Action:
        return Action("argo-rollouts", "rollouts-resume")

    @staticmethod
    def rollouts_restart() -> Action:
        return Action("argo-rollouts", "rollouts-restart")

    @staticmethod
    def rollouts_get_status() -> Action:
        return Action("argo-rollouts", "rollouts-get-status")

    @staticmethod
    def rollouts_wait_healthy() -> Action:
        return Action("argo-rollouts", "rollouts-wait-healthy")

    # ======================================================================
    # Factory methods — Flux CD
    # ======================================================================

    @staticmethod
    def flux_reconcile() -> Action:
        return Action("fluxcd", "flux-reconcile")

    @staticmethod
    def flux_suspend() -> Action:
        return Action("fluxcd", "flux-suspend")

    @staticmethod
    def flux_resume() -> Action:
        return Action("fluxcd", "flux-resume")

    @staticmethod
    def flux_get_status() -> Action:
        return Action("fluxcd", "flux-get-status")

    @staticmethod
    def flux_wait_ready() -> Action:
        return Action("fluxcd", "flux-wait-ready")

    @staticmethod
    def flux_get_events() -> Action:
        return Action("fluxcd", "flux-get-events")

    # ======================================================================
    # Factory methods — Karpenter
    # ======================================================================

    @staticmethod
    def karpenter_list_nodepools() -> Action:
        return Action("karpenter", "karpenter-list-nodepools")

    @staticmethod
    def karpenter_get_nodepool_status() -> Action:
        return Action("karpenter", "karpenter-get-nodepool-status")

    @staticmethod
    def karpenter_list_nodeclaims() -> Action:
        return Action("karpenter", "karpenter-list-nodeclaims")

    @staticmethod
    def karpenter_scale_nodepool() -> Action:
        return Action("karpenter", "karpenter-scale-nodepool")

    @staticmethod
    def karpenter_set_disruption() -> Action:
        return Action("karpenter", "karpenter-set-disruption")

    @staticmethod
    def karpenter_apply_nodepool() -> Action:
        return Action("karpenter", "karpenter-apply-nodepool")

    @staticmethod
    def karpenter_delete_nodeclaim() -> Action:
        return Action("karpenter", "karpenter-delete-nodeclaim")

    # ======================================================================
    # Factory methods — Kyverno
    # ======================================================================

    @staticmethod
    def kyverno_list_policies() -> Action:
        return Action("kyverno", "kyverno-list-policies")

    @staticmethod
    def kyverno_get_policy() -> Action:
        return Action("kyverno", "kyverno-get-policy")

    @staticmethod
    def kyverno_list_violations() -> Action:
        return Action("kyverno", "kyverno-list-violations")

    @staticmethod
    def kyverno_set_enforcement() -> Action:
        return Action("kyverno", "kyverno-set-enforcement")

    @staticmethod
    def kyverno_apply_policy() -> Action:
        return Action("kyverno", "kyverno-apply-policy")

    @staticmethod
    def kyverno_delete_policy() -> Action:
        return Action("kyverno", "kyverno-delete-policy")

    @staticmethod
    def kyverno_investigate() -> Action:
        """AI investigation of Kyverno policies and violations (read-only)."""
        return Action("kyverno", "kyverno-investigate")

    # ======================================================================
    # Factory methods — Trivy
    # ======================================================================

    @staticmethod
    def trivy_list_vulnerabilities() -> Action:
        return Action("trivy", "trivy-list-vulnerabilities")

    @staticmethod
    def trivy_get_vulnerability_report() -> Action:
        return Action("trivy", "trivy-get-vulnerability-report")

    @staticmethod
    def trivy_list_exposed_secrets() -> Action:
        return Action("trivy", "trivy-list-exposed-secrets")

    @staticmethod
    def trivy_list_misconfigurations() -> Action:
        return Action("trivy", "trivy-list-misconfigurations")

    @staticmethod
    def trivy_get_compliance_report() -> Action:
        return Action("trivy", "trivy-get-compliance-report")

    @staticmethod
    def trivy_rescan_workload() -> Action:
        """Force trivy-operator to rescan a workload by deleting its
        VulnerabilityReports."""
        return Action("trivy", "trivy-rescan-workload")

    @staticmethod
    def trivy_investigate() -> Action:
        """AI investigation of Trivy scan results (read-only)."""
        return Action("trivy", "trivy-investigate")

    # ======================================================================
    # Factory methods — Helm
    # ======================================================================

    @staticmethod
    def helm_upgrade() -> Action:
        return Action("helm", "helm-upgrade")

    @staticmethod
    def helm_install() -> Action:
        return Action("helm", "helm-install")

    @staticmethod
    def helm_rollback() -> Action:
        return Action("helm", "helm-rollback")

    @staticmethod
    def helm_uninstall() -> Action:
        return Action("helm", "helm-uninstall")

    @staticmethod
    def helm_status() -> Action:
        return Action("helm", "helm-status")

    # ======================================================================
    # Factory methods — AWS Cost
    # ======================================================================

    @staticmethod
    def aws_query_cost_explorer() -> Action:
        return Action("aws-cost", "aws-query-cost-explorer")

    @staticmethod
    def aws_get_cost_anomalies() -> Action:
        return Action("aws-cost", "aws-get-cost-anomalies")

    @staticmethod
    def aws_get_cost_forecast() -> Action:
        return Action("aws-cost", "aws-get-cost-forecast")

    @staticmethod
    def aws_get_budget_status() -> Action:
        return Action("aws-cost", "aws-get-budget-status")

    @staticmethod
    def aws_get_rightsizing_recommendations() -> Action:
        """EC2 rightsizing recommendations from Cost Explorer with monthly savings."""
        return Action("aws-cost", "aws-get-rightsizing-recommendations")

    @staticmethod
    def aws_get_savings_plans_recommendations() -> Action:
        """Savings Plans purchase recommendations from Cost Explorer."""
        return Action("aws-cost", "aws-get-savings-plans-recommendations")

    @staticmethod
    def aws_get_reservation_recommendations() -> Action:
        """Reserved Instance purchase recommendations (EC2, RDS, ElastiCache, OpenSearch, Redshift)."""
        return Action("aws-cost", "aws-get-reservation-recommendations")

    @staticmethod
    def aws_get_commitment_utilization() -> Action:
        """Savings Plans and Reserved Instance utilization / unused commitment."""
        return Action("aws-cost", "aws-get-commitment-utilization")

    @staticmethod
    def aws_compare_cost_periods() -> Action:
        """Compare spend between two consecutive periods and find top cost movers."""
        return Action("aws-cost", "aws-compare-cost-periods")

    @staticmethod
    def aws_find_idle_resources() -> Action:
        """Scan for unattached EBS volumes, unassociated Elastic IPs, low-CPU EC2 instances, and old snapshots."""
        return Action("aws-cost", "aws-find-idle-resources")

    @staticmethod
    def aws_get_compute_optimizer_recommendations() -> Action:
        """AWS Compute Optimizer recommendations (EC2, ASG, EBS, Lambda)."""
        return Action("aws-cost", "aws-get-compute-optimizer-recommendations")

    @staticmethod
    def aws_get_trusted_advisor_cost_checks() -> Action:
        """Trusted Advisor cost optimization checks (Business/Enterprise support required)."""
        return Action("aws-cost", "aws-get-trusted-advisor-cost-checks")

    # -- AWS Cost remediation (destructive — place behind an Approval block) --

    @staticmethod
    def aws_stop_ec2_instances() -> Action:
        """Stop running EC2 instances. Instances tagged kestrel:protected are skipped."""
        return Action("aws-cost", "aws-stop-ec2-instances")

    @staticmethod
    def aws_delete_unattached_ebs_volumes() -> Action:
        """Delete unattached ('available') EBS volumes, optionally snapshotting first."""
        return Action("aws-cost", "aws-delete-unattached-ebs-volumes")

    @staticmethod
    def aws_release_elastic_ips() -> Action:
        """Release unassociated Elastic IP addresses."""
        return Action("aws-cost", "aws-release-elastic-ips")

    @staticmethod
    def aws_delete_old_snapshots() -> Action:
        """Delete EBS snapshots older than a threshold (AMI-referenced snapshots skipped)."""
        return Action("aws-cost", "aws-delete-old-snapshots")

    # ======================================================================
    # Factory methods — PostHog
    # ======================================================================

    @staticmethod
    def posthog_get_session_summary() -> Action:
        return Action("posthog", "posthog-get-session-summary")

    @staticmethod
    def posthog_get_session_recording() -> Action:
        return Action("posthog", "posthog-get-session-recording")

    @staticmethod
    def posthog_query_events() -> Action:
        return Action("posthog", "posthog-query-events")

    @staticmethod
    def posthog_list_session_recordings() -> Action:
        return Action("posthog", "posthog-list-session-recordings")

    @staticmethod
    def posthog_get_error_issue() -> Action:
        return Action("posthog", "posthog-get-error-issue")

    # ======================================================================
    # Factory methods — Vercel
    # ======================================================================

    @staticmethod
    def vercel_get_deployment() -> Action:
        return Action("vercel", "vercel-get-deployment")

    @staticmethod
    def vercel_get_build_logs() -> Action:
        return Action("vercel", "vercel-get-build-logs")

    @staticmethod
    def vercel_rollback() -> Action:
        return Action("vercel", "vercel-rollback")

    @staticmethod
    def vercel_promote() -> Action:
        return Action("vercel", "vercel-promote")

    @staticmethod
    def vercel_list_deployments() -> Action:
        return Action("vercel", "vercel-list-deployments")

    @staticmethod
    def vercel_investigate() -> Action:
        return Action("vercel", "vercel-investigate")

    # ======================================================================
    # Factory methods — Railway
    # ======================================================================

    @staticmethod
    def railway_get_deployment() -> Action:
        return Action("railway", "railway-get-deployment")

    @staticmethod
    def railway_get_deployment_logs() -> Action:
        return Action("railway", "railway-get-deployment-logs")

    @staticmethod
    def railway_rollback() -> Action:
        return Action("railway", "railway-rollback")

    @staticmethod
    def railway_redeploy() -> Action:
        return Action("railway", "railway-redeploy")

    @staticmethod
    def railway_restart() -> Action:
        return Action("railway", "railway-restart")

    @staticmethod
    def railway_list_deployments() -> Action:
        return Action("railway", "railway-list-deployments")

    @staticmethod
    def railway_set_variables() -> Action:
        return Action("railway", "railway-set-variables")

    @staticmethod
    def railway_investigate() -> Action:
        return Action("railway", "railway-investigate")

    # ======================================================================
    # Factory methods — Fly.io
    # ======================================================================

    @staticmethod
    def flyio_restart_machine() -> Action:
        return Action("flyio", "flyio-restart-machine")

    @staticmethod
    def flyio_start_machine() -> Action:
        return Action("flyio", "flyio-start-machine")

    @staticmethod
    def flyio_stop_machine() -> Action:
        return Action("flyio", "flyio-stop-machine")

    @staticmethod
    def flyio_suspend_machine() -> Action:
        return Action("flyio", "flyio-suspend-machine")

    @staticmethod
    def flyio_cordon_machine() -> Action:
        return Action("flyio", "flyio-cordon-machine")

    @staticmethod
    def flyio_uncordon_machine() -> Action:
        return Action("flyio", "flyio-uncordon-machine")

    @staticmethod
    def flyio_get_machine() -> Action:
        return Action("flyio", "flyio-get-machine")

    @staticmethod
    def flyio_get_machine_events() -> Action:
        return Action("flyio", "flyio-get-machine-events")

    @staticmethod
    def flyio_list_machines() -> Action:
        return Action("flyio", "flyio-list-machines")

    @staticmethod
    def flyio_set_secrets() -> Action:
        return Action("flyio", "flyio-set-secrets")

    @staticmethod
    def flyio_investigate() -> Action:
        return Action("flyio", "flyio-investigate")

    # ======================================================================
    # Factory methods — Nebius
    # ======================================================================

    @staticmethod
    def nebius_get_instance() -> Action:
        return Action("nebius", "nebius-get-instance")

    @staticmethod
    def nebius_start_instance() -> Action:
        return Action("nebius", "nebius-start-instance")

    @staticmethod
    def nebius_stop_instance() -> Action:
        return Action("nebius", "nebius-stop-instance")

    @staticmethod
    def nebius_restart_instance() -> Action:
        return Action("nebius", "nebius-restart-instance")

    @staticmethod
    def nebius_list_instances() -> Action:
        return Action("nebius", "nebius-list-instances")

    @staticmethod
    def nebius_list_clusters() -> Action:
        return Action("nebius", "nebius-list-clusters")

    @staticmethod
    def nebius_list_node_groups() -> Action:
        return Action("nebius", "nebius-list-node-groups")

    @staticmethod
    def nebius_scale_node_group() -> Action:
        return Action("nebius", "nebius-scale-node-group")

    @staticmethod
    def nebius_create_instance() -> Action:
        return Action("nebius", "nebius-create-instance")

    @staticmethod
    def nebius_delete_instance() -> Action:
        return Action("nebius", "nebius-delete-instance")

    @staticmethod
    def nebius_create_node_group() -> Action:
        return Action("nebius", "nebius-create-node-group")

    @staticmethod
    def nebius_delete_node_group() -> Action:
        return Action("nebius", "nebius-delete-node-group")

    @staticmethod
    def nebius_investigate() -> Action:
        return Action("nebius", "nebius-investigate")

    # ======================================================================
    # Factory methods — Daytona
    # ======================================================================

    @staticmethod
    def daytona_list_sandboxes() -> Action:
        return Action("daytona", "daytona-list-sandboxes")

    @staticmethod
    def daytona_create_sandbox() -> Action:
        return Action("daytona", "daytona-create-sandbox")

    @staticmethod
    def daytona_get_sandbox() -> Action:
        return Action("daytona", "daytona-get-sandbox")

    @staticmethod
    def daytona_start_sandbox() -> Action:
        return Action("daytona", "daytona-start-sandbox")

    @staticmethod
    def daytona_stop_sandbox() -> Action:
        return Action("daytona", "daytona-stop-sandbox")

    @staticmethod
    def daytona_archive_sandbox() -> Action:
        return Action("daytona", "daytona-archive-sandbox")

    @staticmethod
    def daytona_delete_sandbox() -> Action:
        return Action("daytona", "daytona-delete-sandbox")

    @staticmethod
    def daytona_run_command() -> Action:
        return Action("daytona", "daytona-run-command")

    @staticmethod
    def daytona_set_auto_stop() -> Action:
        return Action("daytona", "daytona-set-auto-stop")

    @staticmethod
    def daytona_list_snapshots() -> Action:
        return Action("daytona", "daytona-list-snapshots")

    @staticmethod
    def daytona_create_snapshot() -> Action:
        return Action("daytona", "daytona-create-snapshot")

    @staticmethod
    def daytona_delete_snapshot() -> Action:
        return Action("daytona", "daytona-delete-snapshot")

    @staticmethod
    def daytona_list_volumes() -> Action:
        return Action("daytona", "daytona-list-volumes")

    @staticmethod
    def daytona_get_volume() -> Action:
        return Action("daytona", "daytona-get-volume")

    @staticmethod
    def daytona_create_volume() -> Action:
        return Action("daytona", "daytona-create-volume")

    @staticmethod
    def daytona_delete_volume() -> Action:
        return Action("daytona", "daytona-delete-volume")

    @staticmethod
    def daytona_investigate() -> Action:
        return Action("daytona", "daytona-investigate")

    # ======================================================================
    # Factory methods — Supabase
    # ======================================================================

    @staticmethod
    def supabase_list_projects() -> Action:
        return Action("supabase", "supabase-list-projects")

    @staticmethod
    def supabase_get_project() -> Action:
        return Action("supabase", "supabase-get-project")

    @staticmethod
    def supabase_get_project_health() -> Action:
        return Action("supabase", "supabase-get-project-health")

    @staticmethod
    def supabase_pause_project() -> Action:
        return Action("supabase", "supabase-pause-project")

    @staticmethod
    def supabase_restore_project() -> Action:
        return Action("supabase", "supabase-restore-project")

    @staticmethod
    def supabase_list_branches() -> Action:
        return Action("supabase", "supabase-list-branches")

    @staticmethod
    def supabase_create_branch() -> Action:
        return Action("supabase", "supabase-create-branch")

    @staticmethod
    def supabase_get_branch() -> Action:
        return Action("supabase", "supabase-get-branch")

    @staticmethod
    def supabase_merge_branch() -> Action:
        return Action("supabase", "supabase-merge-branch")

    @staticmethod
    def supabase_reset_branch() -> Action:
        return Action("supabase", "supabase-reset-branch")

    @staticmethod
    def supabase_delete_branch() -> Action:
        return Action("supabase", "supabase-delete-branch")

    @staticmethod
    def supabase_list_backups() -> Action:
        return Action("supabase", "supabase-list-backups")

    @staticmethod
    def supabase_create_restore_point() -> Action:
        return Action("supabase", "supabase-create-restore-point")

    @staticmethod
    def supabase_restore_pitr() -> Action:
        return Action("supabase", "supabase-restore-pitr")

    @staticmethod
    def supabase_setup_read_replica() -> Action:
        return Action("supabase", "supabase-setup-read-replica")

    @staticmethod
    def supabase_remove_read_replica() -> Action:
        return Action("supabase", "supabase-remove-read-replica")

    @staticmethod
    def supabase_get_network_restrictions() -> Action:
        return Action("supabase", "supabase-get-network-restrictions")

    @staticmethod
    def supabase_update_network_restrictions() -> Action:
        return Action("supabase", "supabase-update-network-restrictions")

    @staticmethod
    def supabase_list_api_keys() -> Action:
        return Action("supabase", "supabase-list-api-keys")

    @staticmethod
    def supabase_investigate() -> Action:
        return Action("supabase", "supabase-investigate")

    # ======================================================================
    # Factory methods — PlanetScale
    # ======================================================================

    @staticmethod
    def planetscale_list_databases() -> Action:
        return Action("planetscale", "planetscale-list-databases")

    @staticmethod
    def planetscale_get_database() -> Action:
        return Action("planetscale", "planetscale-get-database")

    @staticmethod
    def planetscale_list_branches() -> Action:
        return Action("planetscale", "planetscale-list-branches")

    @staticmethod
    def planetscale_get_branch() -> Action:
        return Action("planetscale", "planetscale-get-branch")

    @staticmethod
    def planetscale_create_branch() -> Action:
        return Action("planetscale", "planetscale-create-branch")

    @staticmethod
    def planetscale_delete_branch() -> Action:
        return Action("planetscale", "planetscale-delete-branch")

    @staticmethod
    def planetscale_promote_branch() -> Action:
        return Action("planetscale", "planetscale-promote-branch")

    @staticmethod
    def planetscale_set_safe_migrations() -> Action:
        return Action("planetscale", "planetscale-set-safe-migrations")

    @staticmethod
    def planetscale_list_deploy_requests() -> Action:
        return Action("planetscale", "planetscale-list-deploy-requests")

    @staticmethod
    def planetscale_get_deploy_request() -> Action:
        return Action("planetscale", "planetscale-get-deploy-request")

    @staticmethod
    def planetscale_create_deploy_request() -> Action:
        return Action("planetscale", "planetscale-create-deploy-request")

    @staticmethod
    def planetscale_deploy_deploy_request() -> Action:
        return Action("planetscale", "planetscale-deploy-deploy-request")

    @staticmethod
    def planetscale_revert_deploy_request() -> Action:
        return Action("planetscale", "planetscale-revert-deploy-request")

    @staticmethod
    def planetscale_close_deploy_request() -> Action:
        return Action("planetscale", "planetscale-close-deploy-request")

    @staticmethod
    def planetscale_approve_deploy_request() -> Action:
        return Action("planetscale", "planetscale-approve-deploy-request")

    @staticmethod
    def planetscale_list_backups() -> Action:
        return Action("planetscale", "planetscale-list-backups")

    @staticmethod
    def planetscale_create_backup() -> Action:
        return Action("planetscale", "planetscale-create-backup")

    @staticmethod
    def planetscale_list_passwords() -> Action:
        return Action("planetscale", "planetscale-list-passwords")

    @staticmethod
    def planetscale_create_password() -> Action:
        return Action("planetscale", "planetscale-create-password")

    @staticmethod
    def planetscale_delete_password() -> Action:
        return Action("planetscale", "planetscale-delete-password")

    @staticmethod
    def planetscale_investigate() -> Action:
        return Action("planetscale", "planetscale-investigate")

    # ======================================================================
    # Factory methods — Neon
    # ======================================================================

    @staticmethod
    def neon_list_projects() -> Action:
        return Action("neon", "neon-list-projects")

    @staticmethod
    def neon_get_project() -> Action:
        return Action("neon", "neon-get-project")

    @staticmethod
    def neon_list_branches() -> Action:
        return Action("neon", "neon-list-branches")

    @staticmethod
    def neon_get_branch() -> Action:
        return Action("neon", "neon-get-branch")

    @staticmethod
    def neon_create_branch() -> Action:
        return Action("neon", "neon-create-branch")

    @staticmethod
    def neon_delete_branch() -> Action:
        return Action("neon", "neon-delete-branch")

    @staticmethod
    def neon_reset_branch() -> Action:
        return Action("neon", "neon-reset-branch")

    @staticmethod
    def neon_restore_branch() -> Action:
        return Action("neon", "neon-restore-branch")

    @staticmethod
    def neon_list_endpoints() -> Action:
        return Action("neon", "neon-list-endpoints")

    @staticmethod
    def neon_create_endpoint() -> Action:
        return Action("neon", "neon-create-endpoint")

    @staticmethod
    def neon_delete_endpoint() -> Action:
        return Action("neon", "neon-delete-endpoint")

    @staticmethod
    def neon_suspend_compute() -> Action:
        return Action("neon", "neon-suspend-compute")

    @staticmethod
    def neon_start_compute() -> Action:
        return Action("neon", "neon-start-compute")

    @staticmethod
    def neon_set_autoscaling() -> Action:
        return Action("neon", "neon-set-autoscaling")

    @staticmethod
    def neon_rotate_credentials() -> Action:
        return Action("neon", "neon-rotate-credentials")

    @staticmethod
    def neon_get_connection_uri() -> Action:
        return Action("neon", "neon-get-connection-uri")

    @staticmethod
    def neon_investigate() -> Action:
        return Action("neon", "neon-investigate")

    # ======================================================================
    # Factory methods — ClickHouse
    # ======================================================================

    @staticmethod
    def clickhouse_list_services() -> Action:
        return Action("clickhouse", "clickhouse-list-services")

    @staticmethod
    def clickhouse_get_service() -> Action:
        return Action("clickhouse", "clickhouse-get-service")

    @staticmethod
    def clickhouse_create_service() -> Action:
        return Action("clickhouse", "clickhouse-create-service")

    @staticmethod
    def clickhouse_start_service() -> Action:
        return Action("clickhouse", "clickhouse-start-service")

    @staticmethod
    def clickhouse_stop_service() -> Action:
        return Action("clickhouse", "clickhouse-stop-service")

    @staticmethod
    def clickhouse_update_autoscaling() -> Action:
        return Action("clickhouse", "clickhouse-update-autoscaling")

    @staticmethod
    def clickhouse_update_ip_access() -> Action:
        return Action("clickhouse", "clickhouse-update-ip-access")

    @staticmethod
    def clickhouse_list_backups() -> Action:
        return Action("clickhouse", "clickhouse-list-backups")

    @staticmethod
    def clickhouse_get_backup() -> Action:
        return Action("clickhouse", "clickhouse-get-backup")

    @staticmethod
    def clickhouse_update_backup_config() -> Action:
        return Action("clickhouse", "clickhouse-update-backup-config")

    @staticmethod
    def clickhouse_restore_backup() -> Action:
        return Action("clickhouse", "clickhouse-restore-backup")

    @staticmethod
    def clickhouse_delete_service() -> Action:
        return Action("clickhouse", "clickhouse-delete-service")

    @staticmethod
    def clickhouse_list_api_keys() -> Action:
        return Action("clickhouse", "clickhouse-list-api-keys")

    @staticmethod
    def clickhouse_get_service_metrics() -> Action:
        return Action("clickhouse", "clickhouse-get-service-metrics")

    @staticmethod
    def clickhouse_get_usage_cost() -> Action:
        return Action("clickhouse", "clickhouse-get-usage-cost")

    @staticmethod
    def clickhouse_list_clickpipes() -> Action:
        return Action("clickhouse", "clickhouse-list-clickpipes")

    @staticmethod
    def clickhouse_get_clickpipe() -> Action:
        return Action("clickhouse", "clickhouse-get-clickpipe")

    @staticmethod
    def clickhouse_start_clickpipe() -> Action:
        return Action("clickhouse", "clickhouse-start-clickpipe")

    @staticmethod
    def clickhouse_stop_clickpipe() -> Action:
        return Action("clickhouse", "clickhouse-stop-clickpipe")

    @staticmethod
    def clickhouse_resync_clickpipe() -> Action:
        return Action("clickhouse", "clickhouse-resync-clickpipe")

    @staticmethod
    def clickhouse_scale_clickpipe() -> Action:
        return Action("clickhouse", "clickhouse-scale-clickpipe")

    @staticmethod
    def clickhouse_get_scaling_schedule() -> Action:
        return Action("clickhouse", "clickhouse-get-scaling-schedule")

    @staticmethod
    def clickhouse_set_scaling_schedule() -> Action:
        return Action("clickhouse", "clickhouse-set-scaling-schedule")

    @staticmethod
    def clickhouse_clear_scaling_schedule() -> Action:
        return Action("clickhouse", "clickhouse-clear-scaling-schedule")

    @staticmethod
    def clickhouse_get_upgrade_window() -> Action:
        return Action("clickhouse", "clickhouse-get-upgrade-window")

    @staticmethod
    def clickhouse_set_upgrade_window() -> Action:
        return Action("clickhouse", "clickhouse-set-upgrade-window")

    @staticmethod
    def clickhouse_clear_upgrade_window() -> Action:
        return Action("clickhouse", "clickhouse-clear-upgrade-window")

    @staticmethod
    def clickhouse_get_settings() -> Action:
        return Action("clickhouse", "clickhouse-get-settings")

    @staticmethod
    def clickhouse_update_setting() -> Action:
        return Action("clickhouse", "clickhouse-update-setting")

    @staticmethod
    def clickhouse_reset_setting() -> Action:
        return Action("clickhouse", "clickhouse-reset-setting")

    @staticmethod
    def clickhouse_get_query_endpoint() -> Action:
        return Action("clickhouse", "clickhouse-get-query-endpoint")

    @staticmethod
    def clickhouse_upsert_query_endpoint() -> Action:
        return Action("clickhouse", "clickhouse-upsert-query-endpoint")

    @staticmethod
    def clickhouse_delete_query_endpoint() -> Action:
        return Action("clickhouse", "clickhouse-delete-query-endpoint")

    @staticmethod
    def clickhouse_list_members() -> Action:
        return Action("clickhouse", "clickhouse-list-members")

    @staticmethod
    def clickhouse_remove_member() -> Action:
        return Action("clickhouse", "clickhouse-remove-member")

    @staticmethod
    def clickhouse_list_roles() -> Action:
        return Action("clickhouse", "clickhouse-list-roles")

    @staticmethod
    def clickhouse_list_activity() -> Action:
        return Action("clickhouse", "clickhouse-list-activity")

    @staticmethod
    def clickhouse_investigate() -> Action:
        return Action("clickhouse", "clickhouse-investigate")

    # ======================================================================
    # Factory methods — Terraform Cloud
    # ======================================================================

    @staticmethod
    def terraform_list_workspaces() -> Action:
        return Action("terraform", "terraform-list-workspaces")

    @staticmethod
    def terraform_get_workspace() -> Action:
        return Action("terraform", "terraform-get-workspace")

    @staticmethod
    def terraform_lock_workspace() -> Action:
        return Action("terraform", "terraform-lock-workspace")

    @staticmethod
    def terraform_unlock_workspace() -> Action:
        return Action("terraform", "terraform-unlock-workspace")

    @staticmethod
    def terraform_force_unlock_workspace() -> Action:
        return Action("terraform", "terraform-force-unlock-workspace")

    @staticmethod
    def terraform_list_runs() -> Action:
        return Action("terraform", "terraform-list-runs")

    @staticmethod
    def terraform_get_run() -> Action:
        return Action("terraform", "terraform-get-run")

    @staticmethod
    def terraform_create_run() -> Action:
        """Queue a plan (and optionally auto-apply) on a workspace."""
        return Action("terraform", "terraform-create-run")

    @staticmethod
    def terraform_create_destroy_run() -> Action:
        return Action("terraform", "terraform-create-destroy-run")

    @staticmethod
    def terraform_apply_run() -> Action:
        """Confirm and apply a run awaiting confirmation."""
        return Action("terraform", "terraform-apply-run")

    @staticmethod
    def terraform_discard_run() -> Action:
        return Action("terraform", "terraform-discard-run")

    @staticmethod
    def terraform_cancel_run() -> Action:
        return Action("terraform", "terraform-cancel-run")

    @staticmethod
    def terraform_wait_for_run() -> Action:
        """Poll a run until it reaches a terminal or attention state."""
        return Action("terraform", "terraform-wait-for-run")

    @staticmethod
    def terraform_get_state_outputs() -> Action:
        return Action("terraform", "terraform-get-state-outputs")

    @staticmethod
    def terraform_list_variables() -> Action:
        return Action("terraform", "terraform-list-variables")

    @staticmethod
    def terraform_set_variable() -> Action:
        return Action("terraform", "terraform-set-variable")

    @staticmethod
    def terraform_get_drift() -> Action:
        return Action("terraform", "terraform-get-drift")

    @staticmethod
    def terraform_investigate() -> Action:
        return Action("terraform", "terraform-investigate")

    # ======================================================================
    # Factory methods — Pulumi Cloud
    # ======================================================================

    @staticmethod
    def pulumi_list_stacks() -> Action:
        return Action("pulumi", "pulumi-list-stacks")

    @staticmethod
    def pulumi_get_stack() -> Action:
        return Action("pulumi", "pulumi-get-stack")

    @staticmethod
    def pulumi_list_updates() -> Action:
        return Action("pulumi", "pulumi-list-updates")

    @staticmethod
    def pulumi_get_update() -> Action:
        return Action("pulumi", "pulumi-get-update")

    @staticmethod
    def pulumi_run_deployment() -> Action:
        """Start a Pulumi Deployments run (update, preview, refresh, destroy,
        detect-drift, or remediate-drift) on a stack. Gate destructive
        operations behind an approval."""
        return Action("pulumi", "pulumi-run-deployment")

    @staticmethod
    def pulumi_get_deployment() -> Action:
        return Action("pulumi", "pulumi-get-deployment")

    @staticmethod
    def pulumi_wait_for_deployment() -> Action:
        """Wait for a Pulumi deployment to reach a terminal state."""
        return Action("pulumi", "pulumi-wait-for-deployment")

    @staticmethod
    def pulumi_cancel_deployment() -> Action:
        return Action("pulumi", "pulumi-cancel-deployment")

    @staticmethod
    def pulumi_pause_deployments() -> Action:
        """Pause a stack's deployment queue (e.g. during an incident)."""
        return Action("pulumi", "pulumi-pause-deployments")

    @staticmethod
    def pulumi_resume_deployments() -> Action:
        return Action("pulumi", "pulumi-resume-deployments")

    @staticmethod
    def pulumi_get_stack_outputs() -> Action:
        return Action("pulumi", "pulumi-get-stack-outputs")

    @staticmethod
    def pulumi_get_drift() -> Action:
        return Action("pulumi", "pulumi-get-drift")

    @staticmethod
    def pulumi_set_stack_tag() -> Action:
        return Action("pulumi", "pulumi-set-stack-tag")

    @staticmethod
    def pulumi_delete_stack_tag() -> Action:
        return Action("pulumi", "pulumi-delete-stack-tag")

    @staticmethod
    def pulumi_investigate() -> Action:
        return Action("pulumi", "pulumi-investigate")

    # ======================================================================
    # Factory methods — HashiCorp Vault
    # ======================================================================

    @staticmethod
    def vault_read_secret() -> Action:
        """Read a KV v2 secret. The 'value' output is sensitive: it is
        redacted in run history but can be templated into downstream steps."""
        return Action("vault", "vault-read-secret")

    @staticmethod
    def vault_write_secret() -> Action:
        """Create or update a KV v2 secret (creates a new version).
        Provide the data with .secret_data('{"key": "value"}')."""
        return Action("vault", "vault-write-secret")

    @staticmethod
    def vault_delete_secret() -> Action:
        """Soft-delete the latest version of a KV v2 secret (or destroy all
        versions with .destroy()). Gate behind an approval."""
        return Action("vault", "vault-delete-secret")

    @staticmethod
    def vault_list_secrets() -> Action:
        return Action("vault", "vault-list-secrets")

    @staticmethod
    def vault_get_secret_metadata() -> Action:
        """Fetch version and age metadata for a secret without reading its value."""
        return Action("vault", "vault-get-secret-metadata")

    @staticmethod
    def vault_rotate_static_role() -> Action:
        """Rotate the credentials of a database static role."""
        return Action("vault", "vault-rotate-static-role")

    @staticmethod
    def vault_list_mounts() -> Action:
        return Action("vault", "vault-list-mounts")

    @staticmethod
    def vault_list_policies() -> Action:
        return Action("vault", "vault-list-policies")

    @staticmethod
    def vault_read_policy() -> Action:
        return Action("vault", "vault-read-policy")

    @staticmethod
    def vault_write_policy() -> Action:
        """Create or update an ACL policy from HCL (.policy_hcl())."""
        return Action("vault", "vault-write-policy")

    @staticmethod
    def vault_list_auth_methods() -> Action:
        return Action("vault", "vault-list-auth-methods")

    @staticmethod
    def vault_list_leases() -> Action:
        return Action("vault", "vault-list-leases")

    @staticmethod
    def vault_revoke_lease() -> Action:
        """Revoke a dynamic-credential lease immediately."""
        return Action("vault", "vault-revoke-lease")

    @staticmethod
    def vault_renew_lease() -> Action:
        return Action("vault", "vault-renew-lease")

    @staticmethod
    def vault_get_health() -> Action:
        """Check seal/init status and server version."""
        return Action("vault", "vault-get-health")

    @staticmethod
    def vault_list_token_accessors() -> Action:
        return Action("vault", "vault-list-token-accessors")

    @staticmethod
    def vault_revoke_token_accessor() -> Action:
        """Revoke a token by accessor (e.g. during credential-leak response)."""
        return Action("vault", "vault-revoke-token-accessor")

    @staticmethod
    def vault_investigate() -> Action:
        """AI investigation of Vault state (read-only; never reads secret values)."""
        return Action("vault", "vault-investigate")

    # ======================================================================
    # Factory methods — Infisical
    # ======================================================================

    @staticmethod
    def infisical_get_secret() -> Action:
        """Read a secret. The 'value' output is sensitive: it is redacted in
        run history but can be templated into downstream steps."""
        return Action("infisical", "infisical-get-secret")

    @staticmethod
    def infisical_create_secret() -> Action:
        return Action("infisical", "infisical-create-secret")

    @staticmethod
    def infisical_update_secret() -> Action:
        return Action("infisical", "infisical-update-secret")

    @staticmethod
    def infisical_delete_secret() -> Action:
        """Delete a secret. Gate behind an approval."""
        return Action("infisical", "infisical-delete-secret")

    @staticmethod
    def infisical_list_secrets() -> Action:
        """List secret key names (never values) in a project/environment/path."""
        return Action("infisical", "infisical-list-secrets")

    @staticmethod
    def infisical_list_projects() -> Action:
        return Action("infisical", "infisical-list-projects")

    @staticmethod
    def infisical_list_environments() -> Action:
        return Action("infisical", "infisical-list-environments")

    @staticmethod
    def infisical_list_folders() -> Action:
        return Action("infisical", "infisical-list-folders")

    @staticmethod
    def infisical_create_folder() -> Action:
        return Action("infisical", "infisical-create-folder")

    @staticmethod
    def infisical_list_secret_syncs() -> Action:
        return Action("infisical", "infisical-list-secret-syncs")

    @staticmethod
    def infisical_trigger_secret_sync() -> Action:
        """Manually trigger a secret sync (e.g. to retry after a failure)."""
        return Action("infisical", "infisical-trigger-secret-sync")

    @staticmethod
    def infisical_list_approval_requests() -> Action:
        return Action("infisical", "infisical-list-approval-requests")

    @staticmethod
    def infisical_get_audit_logs() -> Action:
        return Action("infisical", "infisical-get-audit-logs")

    @staticmethod
    def infisical_list_identities() -> Action:
        return Action("infisical", "infisical-list-identities")

    @staticmethod
    def infisical_investigate() -> Action:
        """AI investigation of Infisical state (read-only; never reads secret values)."""
        return Action("infisical", "infisical-investigate")

    # ======================================================================
    # Factory methods — Jenkins
    # ======================================================================

    @staticmethod
    def jenkins_trigger_build() -> Action:
        """Trigger a Jenkins job build, optionally with build parameters."""
        return Action("jenkins", "jenkins-trigger-build")

    @staticmethod
    def jenkins_wait_for_build() -> Action:
        """Wait for a Jenkins build to complete and return its result."""
        return Action("jenkins", "jenkins-wait-for-build")

    @staticmethod
    def jenkins_get_build_status() -> Action:
        return Action("jenkins", "jenkins-get-build-status")

    @staticmethod
    def jenkins_stop_build() -> Action:
        """Abort a running Jenkins build."""
        return Action("jenkins", "jenkins-stop-build")

    @staticmethod
    def jenkins_get_console_log() -> Action:
        return Action("jenkins", "jenkins-get-console-log")

    @staticmethod
    def jenkins_investigate() -> Action:
        return Action("jenkins", "jenkins-investigate")

    # ======================================================================
    # Factory methods — CircleCI
    # ======================================================================

    @staticmethod
    def circleci_trigger_pipeline() -> Action:
        """Trigger a CircleCI pipeline on a branch or tag."""
        return Action("circleci", "circleci-trigger-pipeline")

    @staticmethod
    def circleci_wait_for_pipeline() -> Action:
        """Wait for a CircleCI pipeline's workflows to complete."""
        return Action("circleci", "circleci-wait-for-pipeline")

    @staticmethod
    def circleci_get_workflow_status() -> Action:
        return Action("circleci", "circleci-get-workflow-status")

    @staticmethod
    def circleci_rerun_workflow() -> Action:
        """Rerun a CircleCI workflow, optionally only its failed jobs."""
        return Action("circleci", "circleci-rerun-workflow")

    @staticmethod
    def circleci_cancel_workflow() -> Action:
        """Cancel a running CircleCI workflow."""
        return Action("circleci", "circleci-cancel-workflow")

    @staticmethod
    def circleci_approve_job() -> Action:
        """Approve an on-hold approval job so a gated workflow can proceed."""
        return Action("circleci", "circleci-approve-job")

    @staticmethod
    def circleci_get_job_tests() -> Action:
        return Action("circleci", "circleci-get-job-tests")

    @staticmethod
    def circleci_investigate() -> Action:
        return Action("circleci", "circleci-investigate")

    # ======================================================================
    # Factory methods — SonarCloud
    # ======================================================================

    @staticmethod
    def sonarcloud_get_quality_gate() -> Action:
        """Fetch a project's quality gate status with failing conditions."""
        return Action("sonarcloud", "sonarcloud-get-quality-gate")

    @staticmethod
    def sonarcloud_list_issues() -> Action:
        """List open issues (bugs, vulnerabilities, code smells) on a project."""
        return Action("sonarcloud", "sonarcloud-list-issues")

    @staticmethod
    def sonarcloud_list_hotspots() -> Action:
        """List security hotspots awaiting review on a project."""
        return Action("sonarcloud", "sonarcloud-list-hotspots")

    @staticmethod
    def sonarcloud_get_measures() -> Action:
        """Fetch project metric values (bugs, coverage, duplication, ...)."""
        return Action("sonarcloud", "sonarcloud-get-measures")

    @staticmethod
    def sonarcloud_transition_issue() -> Action:
        """Apply an issue workflow transition (confirm, resolve, reopen,
        falsepositive, wontfix)."""
        return Action("sonarcloud", "sonarcloud-transition-issue")

    @staticmethod
    def sonarcloud_assign_issue() -> Action:
        """Assign a SonarCloud issue to a user (empty assignee unassigns)."""
        return Action("sonarcloud", "sonarcloud-assign-issue")

    @staticmethod
    def sonarcloud_comment_issue() -> Action:
        """Add a comment to a SonarCloud issue."""
        return Action("sonarcloud", "sonarcloud-comment-issue")

    @staticmethod
    def sonarcloud_review_hotspot() -> Action:
        """Change a security hotspot's review status (SAFE / FIXED /
        ACKNOWLEDGED, or back TO_REVIEW)."""
        return Action("sonarcloud", "sonarcloud-review-hotspot")

    @staticmethod
    def sonarcloud_investigate() -> Action:
        """AI investigation of SonarCloud quality gates, issues, hotspots,
        and metrics (read-only)."""
        return Action("sonarcloud", "sonarcloud-investigate")

    # ======================================================================
    # Factory methods — Okta
    # ======================================================================

    @staticmethod
    def okta_get_user() -> Action:
        """Fetch an Okta user's profile and status. Config: user (defaults
        to {{signal.target_user}})."""
        return Action("okta", "okta-get-user")

    @staticmethod
    def okta_list_users() -> Action:
        """Search Okta users by name/email prefix and/or lifecycle status.
        Config: query, user_status, max_results."""
        return Action("okta", "okta-list-users")

    @staticmethod
    def okta_query_system_log() -> Action:
        """Query the Okta System Log for recent security events. Config:
        event_types, search, since_hours, max_results."""
        return Action("okta", "okta-query-system-log")

    @staticmethod
    def okta_list_user_groups() -> Action:
        """List the groups an Okta user belongs to. Config: user."""
        return Action("okta", "okta-list-user-groups")

    @staticmethod
    def okta_list_group_members() -> Action:
        """List the users in an Okta group. Config: group, max_results."""
        return Action("okta", "okta-list-group-members")

    @staticmethod
    def okta_suspend_user() -> Action:
        """Suspend an Okta user (reversible; keeps assignments). Config: user."""
        return Action("okta", "okta-suspend-user")

    @staticmethod
    def okta_unsuspend_user() -> Action:
        """Return a suspended Okta user to ACTIVE. Config: user."""
        return Action("okta", "okta-unsuspend-user")

    @staticmethod
    def okta_unlock_user() -> Action:
        """Unlock a LOCKED_OUT Okta user. Config: user."""
        return Action("okta", "okta-unlock-user")

    @staticmethod
    def okta_deactivate_user() -> Action:
        """Deactivate an Okta user (DEPROVISIONED; not simply reversible).
        Config: user."""
        return Action("okta", "okta-deactivate-user")

    @staticmethod
    def okta_clear_sessions() -> Action:
        """Revoke all of a user's active Okta sessions. Config: user,
        revoke_oauth_tokens."""
        return Action("okta", "okta-clear-sessions")

    @staticmethod
    def okta_expire_password() -> Action:
        """Expire an Okta user's password (must reset at next sign-in).
        Config: user."""
        return Action("okta", "okta-expire-password")

    @staticmethod
    def okta_reset_mfa() -> Action:
        """Reset all of a user's enrolled MFA factors. Config: user."""
        return Action("okta", "okta-reset-mfa")

    @staticmethod
    def okta_add_user_to_group() -> Action:
        """Add an Okta user to a group. Config: user, group."""
        return Action("okta", "okta-add-user-to-group")

    @staticmethod
    def okta_remove_user_from_group() -> Action:
        """Remove an Okta user from a group. Config: user, group."""
        return Action("okta", "okta-remove-user-from-group")

    @staticmethod
    def okta_investigate() -> Action:
        """AI investigation of Okta users, groups, MFA factors, and System
        Log activity (read-only)."""
        return Action("okta", "okta-investigate")

    # ======================================================================
    # Internal serialisation
    # ======================================================================

    def _to_node(self, node_id: str) -> _Node:
        data: dict[str, Any] = {
            "integration": self._integration,
            "action": self._action,
            "config": self._config,
        }
        if self._label:
            data["label"] = self._label
        return _Node(id=node_id, type="action", data=data)
