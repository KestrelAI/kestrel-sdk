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

from typing import Any

from .types import _Node


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

    def duration(self, n: int) -> Action:
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

    def max_iterations(self, n: int) -> Action:
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

    def limit(self, n: int) -> Action:
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

    def timeout_minutes(self, n: int) -> Action:
        return self.config("timeout_minutes", n)

    def poll_interval_seconds(self, n: int) -> Action:
        return self.config("poll_interval_seconds", n)

    def path(self, p: str) -> Action:
        return self.config("path", p)

    def max_turns(self, n: int) -> Action:
        return self.config("max_turns", n)

    # -- Datadog -----------------------------------------------------------

    def timeframe(self, tf: str) -> Action:
        return self.config("timeframe", tf)

    def monitor_type(self, mt: str) -> Action:
        return self.config("type", mt)

    def critical_threshold(self, v: float) -> Action:
        return self.config("critical_threshold", v)

    def warning_threshold(self, v: float) -> Action:
        return self.config("warning_threshold", v)

    def alert_type(self, at: str) -> Action:
        return self.config("alert_type", at)

    def tags(self, t: str) -> Action:
        return self.config("tags", t)

    def text(self, template: str) -> Action:
        return self.config("text_template", template)

    def scope(self, s: str) -> Action:
        return self.config("scope", s)

    def duration_minutes(self, n: int) -> Action:
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

    # -- Fly.io ------------------------------------------------------------

    def machine_id(self, mid: str) -> Action:
        return self.config("machine_id", mid)

    def prune(self, v: bool = True) -> Action:
        return self.config("prune", v)

    def wait_timeout_seconds(self, n: int) -> Action:
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

    def lookback_days(self, n: int) -> Action:
        return self.config("lookback_days", n)

    def min_impact(self, n: float) -> Action:
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

    def limit(self, n: int) -> Action:
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

    def size(self, n: int) -> Action:
        return self.config("size", n)

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
    def nebius_investigate() -> Action:
        return Action("nebius", "nebius-investigate")

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
