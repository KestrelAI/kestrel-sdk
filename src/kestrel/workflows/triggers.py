"""Trigger builder for workflow definitions."""

from __future__ import annotations

from typing import Any

from .types import _Node


class Trigger:
    """Builds a workflow trigger node with typed filter methods.

    Use the static factory methods to create a trigger for a specific source
    and signal type, then chain filter methods to narrow the scope::

        trigger = (
            Trigger.k8s_pod_status()
            .filter(reasons=["CrashLoopBackOff"])
            .cluster("my-cluster-id")
            .namespace("default")
        )
    """

    def __init__(self, source: str, signal_type: str = "any") -> None:
        self._source = source
        self._signal_type = signal_type
        self._filters: dict[str, Any] = {}
        self._label: str = ""

    # -- Generic -----------------------------------------------------------

    def label(self, text: str) -> Trigger:
        self._label = text
        return self

    def filter(self, **kwargs: Any) -> Trigger:
        """Set arbitrary filter keys (generic escape hatch)."""
        self._filters.update(kwargs)
        return self

    # -- Kubernetes filters ------------------------------------------------

    def cluster(self, *ids: str) -> Trigger:
        self._filters["cluster_ids"] = list(ids)
        return self

    def namespace(self, *names: str) -> Trigger:
        self._filters["namespaces"] = list(names)
        return self

    def workload(self, *names: str) -> Trigger:
        self._filters["workload_names"] = list(names)
        return self

    def reasons(self, *r: str) -> Trigger:
        self._filters["reasons"] = list(r)
        return self

    def conditions(self, *c: str) -> Trigger:
        self._filters["conditions"] = list(c)
        return self

    def phases(self, *p: str) -> Trigger:
        self._filters["phases"] = list(p)
        return self

    def resource_kinds(self, *kinds: str) -> Trigger:
        self._filters["resource_kinds"] = list(kinds)
        return self

    def restart_threshold(self, n: int) -> Trigger:
        self._filters["restart_count_threshold"] = n
        return self

    def terminated_reasons(self, *r: str) -> Trigger:
        self._filters["terminated_reasons"] = list(r)
        return self

    # -- AWS filters -------------------------------------------------------

    def aws_connection(self, *ids: str) -> Trigger:
        self._filters["aws_connection_ids"] = list(ids)
        return self

    def service_names(self, *s: str) -> Trigger:
        self._filters["service_names"] = list(s)
        return self

    def incident_types(self, *t: str) -> Trigger:
        self._filters["incident_types"] = list(t)
        return self

    def severities(self, *s: str) -> Trigger:
        self._filters["severities"] = list(s)
        return self

    def regions(self, *r: str) -> Trigger:
        self._filters["regions"] = list(r)
        return self

    # -- PagerDuty filters -------------------------------------------------

    def pd_services(self, *ids: str) -> Trigger:
        self._filters["pd_service_ids"] = list(ids)
        return self

    def pd_urgencies(self, *u: str) -> Trigger:
        self._filters["pd_urgencies"] = list(u)
        return self

    # -- PostHog filters ---------------------------------------------------

    def posthog_events(self, *types: str) -> Trigger:
        self._filters["posthog_event_types"] = list(types)
        return self

    def min_rage_clicks(self, n: int) -> Trigger:
        self._filters["min_rage_clicks"] = n
        return self

    # -- Vercel filters ----------------------------------------------------

    def vercel_events(self, *types: str) -> Trigger:
        self._filters["vercel_event_types"] = list(types)
        return self

    # -- Railway filters ---------------------------------------------------

    def railway_events(self, *types: str) -> Trigger:
        self._filters["railway_event_types"] = list(types)
        return self

    def railway_projects(self, *project_ids: str) -> Trigger:
        self._filters["railway_project_ids"] = list(project_ids)
        return self

    def railway_environments(self, *environment_names: str) -> Trigger:
        self._filters["railway_environment_names"] = list(environment_names)
        return self

    # -- Fly.io filters ----------------------------------------------------

    def fly_events(self, *types: str) -> Trigger:
        self._filters["fly_event_types"] = list(types)
        return self

    def fly_apps(self, *app_names: str) -> Trigger:
        self._filters["fly_app_names"] = list(app_names)
        return self

    def fly_regions(self, *regions: str) -> Trigger:
        self._filters["fly_regions"] = list(regions)
        return self

    def fly_poll_interval(self, interval: str) -> Trigger:
        """Set the Fly polling cadence, e.g. "1m", "5m", "15m", "30m"."""
        self._filters["fly_poll_interval"] = interval
        return self

    # -- Nebius filters ----------------------------------------------------

    def nebius_events(self, *types: str) -> Trigger:
        self._filters["nebius_event_types"] = list(types)
        return self

    def nebius_projects(self, *project_ids: str) -> Trigger:
        self._filters["nebius_project_ids"] = list(project_ids)
        return self

    def nebius_clusters(self, *cluster_ids: str) -> Trigger:
        self._filters["nebius_cluster_ids"] = list(cluster_ids)
        return self

    def nebius_poll_interval(self, interval: str) -> Trigger:
        """Set the Nebius polling cadence, e.g. "1m", "5m", "15m", "30m"."""
        self._filters["nebius_poll_interval"] = interval
        return self

    # -- Daytona filters ---------------------------------------------------

    def daytona_events(self, *types: str) -> Trigger:
        self._filters["daytona_event_types"] = list(types)
        return self

    def daytona_sandboxes(self, *sandbox_ids: str) -> Trigger:
        self._filters["daytona_sandbox_ids"] = list(sandbox_ids)
        return self

    # -- Supabase filters --------------------------------------------------

    def supabase_events(self, *types: str) -> Trigger:
        self._filters["supabase_event_types"] = list(types)
        return self

    def supabase_projects(self, *project_refs: str) -> Trigger:
        self._filters["supabase_project_refs"] = list(project_refs)
        return self

    def supabase_tables(self, *tables: str) -> Trigger:
        self._filters["supabase_tables"] = list(tables)
        return self

    def supabase_poll_interval(self, interval: str) -> Trigger:
        """Set the poll cadence for control-plane Supabase triggers (one of
        "1m", "5m", "15m", "30m")."""
        self._filters["supabase_poll_interval"] = interval
        return self

    # -- PlanetScale filters ------------------------------------------------

    def planetscale_events(self, *types: str) -> Trigger:
        self._filters["planetscale_event_types"] = list(types)
        return self

    def planetscale_databases(self, *databases: str) -> Trigger:
        self._filters["planetscale_databases"] = list(databases)
        return self

    def planetscale_branches(self, *branches: str) -> Trigger:
        self._filters["planetscale_branches"] = list(branches)
        return self

    def planetscale_poll_interval(self, interval: str) -> Trigger:
        """Set the poll cadence for the poll-based PlanetScale backup triggers
        (one of "1m", "5m", "15m", "30m")."""
        self._filters["planetscale_poll_interval"] = interval
        return self

    # -- Neon filters ------------------------------------------------------

    def neon_events(self, *types: str) -> Trigger:
        self._filters["neon_event_types"] = list(types)
        return self

    def neon_projects(self, *project_ids: str) -> Trigger:
        self._filters["neon_project_ids"] = list(project_ids)
        return self

    def neon_branches(self, *branch_ids: str) -> Trigger:
        self._filters["neon_branch_ids"] = list(branch_ids)
        return self

    def neon_usage_threshold(self, percent: int) -> Trigger:
        self._filters["neon_usage_threshold_percent"] = percent
        return self

    def neon_poll_interval(self, interval: str) -> Trigger:
        """Set the poll cadence for the poll-based Neon triggers (one of "1m",
        "5m", "15m", "30m"). Neon has no control-plane webhooks."""
        self._filters["neon_poll_interval"] = interval
        return self

    # -- ClickHouse filters ------------------------------------------------

    def clickhouse_events(self, *types: str) -> Trigger:
        self._filters["clickhouse_event_types"] = list(types)
        return self

    def clickhouse_services(self, *service_ids: str) -> Trigger:
        self._filters["clickhouse_service_ids"] = list(service_ids)
        return self

    def clickhouse_error_threshold(self, count: int) -> Trigger:
        """Set the number of new failed queries/inserts per poll window at or
        above which a query.error_spike trigger fires (default 10)."""
        self._filters["clickhouse_error_threshold"] = count
        return self

    def clickhouse_usage_threshold(self, percent: int, budget_chc: float) -> Trigger:
        """Fire usage.threshold when month-to-date spend crosses percent of the
        monthly budget (in ClickHouse Credits)."""
        self._filters["clickhouse_usage_threshold_percent"] = percent
        self._filters["clickhouse_usage_budget_chc"] = budget_chc
        return self

    def clickhouse_poll_interval(self, interval: str) -> Trigger:
        """Set the poll cadence for the poll-based ClickHouse triggers (one of
        "1m", "5m", "15m", "30m"). ClickHouse Cloud has no control-plane
        webhooks."""
        self._filters["clickhouse_poll_interval"] = interval
        return self

    # -- Request filters ---------------------------------------------------

    def request_categories(self, *c: str) -> Trigger:
        self._filters["request_categories"] = list(c)
        return self

    def request_keywords(self, *k: str) -> Trigger:
        self._filters["request_keywords"] = list(k)
        return self

    # -- GitHub filters ----------------------------------------------------

    def repos(self, *repos: str) -> Trigger:
        self._filters["github_repos"] = list(repos)
        return self

    def branches(self, *branches: str) -> Trigger:
        self._filters["github_branches"] = list(branches)
        return self

    def workflow_names(self, *names: str) -> Trigger:
        self._filters["github_workflow_names"] = list(names)
        return self

    # -- Datadog filters ---------------------------------------------------

    def monitor_names(self, *names: str) -> Trigger:
        self._filters["datadog_monitor_names"] = list(names)
        return self

    def monitor_ids(self, *ids: str) -> Trigger:
        self._filters["datadog_monitor_ids"] = list(ids)
        return self

    def alert_transitions(self, *transitions: str) -> Trigger:
        self._filters["datadog_alert_transitions"] = list(transitions)
        return self

    def datadog_tags(self, *tags: str) -> Trigger:
        self._filters["datadog_tags"] = list(tags)
        return self

    # ======================================================================
    # Factory methods — Kubernetes
    # ======================================================================

    @staticmethod
    def k8s_pod_status() -> Trigger:
        return Trigger("kubernetes", "pod_status")

    @staticmethod
    def k8s_rollout_status() -> Trigger:
        return Trigger("kubernetes", "rollout_status")

    @staticmethod
    def k8s_node_condition() -> Trigger:
        return Trigger("kubernetes", "node_condition")

    @staticmethod
    def k8s_any() -> Trigger:
        return Trigger("kubernetes", "any")

    # ======================================================================
    # Factory methods — AWS
    # ======================================================================

    @staticmethod
    def aws_cloudtrail() -> Trigger:
        return Trigger("aws", "cloudtrail")

    @staticmethod
    def aws_security_hub() -> Trigger:
        return Trigger("aws", "security_hub")

    @staticmethod
    def aws_cloudwatch_metric() -> Trigger:
        return Trigger("aws", "cloudwatch_metric")

    @staticmethod
    def aws_cloudwatch_log() -> Trigger:
        return Trigger("aws", "cloudwatch_log")

    @staticmethod
    def aws_config_rule() -> Trigger:
        return Trigger("aws", "config_rule")

    @staticmethod
    def aws_service_health() -> Trigger:
        return Trigger("aws", "service_health")

    @staticmethod
    def aws_cost_anomaly() -> Trigger:
        return Trigger("aws", "cost_anomaly")

    @staticmethod
    def aws_budget_alert() -> Trigger:
        return Trigger("aws", "budget_alert")

    @staticmethod
    def aws_any() -> Trigger:
        return Trigger("aws", "any")

    # ======================================================================
    # Factory methods — PagerDuty
    # ======================================================================

    @staticmethod
    def pagerduty_triggered() -> Trigger:
        return Trigger("pagerduty", "incident.triggered")

    @staticmethod
    def pagerduty_acknowledged() -> Trigger:
        return Trigger("pagerduty", "incident.acknowledged")

    @staticmethod
    def pagerduty_resolved() -> Trigger:
        return Trigger("pagerduty", "incident.resolved")

    @staticmethod
    def pagerduty_any() -> Trigger:
        return Trigger("pagerduty", "any")

    # ======================================================================
    # Factory methods — PostHog
    # ======================================================================

    @staticmethod
    def posthog_exception() -> Trigger:
        return Trigger("posthog", "$exception")

    @staticmethod
    def posthog_rage_click() -> Trigger:
        return Trigger("posthog", "$rageclick")

    @staticmethod
    def posthog_log_entry() -> Trigger:
        return Trigger("posthog", "$log_entry")

    @staticmethod
    def posthog_log_alert() -> Trigger:
        return Trigger("posthog", "log_alert")

    @staticmethod
    def posthog_any() -> Trigger:
        return Trigger("posthog", "any")

    # ======================================================================
    # Factory methods — Vercel
    # ======================================================================

    @staticmethod
    def vercel_deployment_failed() -> Trigger:
        return Trigger("vercel", "deployment.error")

    @staticmethod
    def vercel_deployment_ready() -> Trigger:
        return Trigger("vercel", "deployment.succeeded")

    @staticmethod
    def vercel_deployment_created() -> Trigger:
        return Trigger("vercel", "deployment.created")

    @staticmethod
    def vercel_checks_failed() -> Trigger:
        return Trigger("vercel", "deployment.checks.failed")

    @staticmethod
    def vercel_rollback() -> Trigger:
        return Trigger("vercel", "deployment.rollback")

    @staticmethod
    def vercel_firewall_attack() -> Trigger:
        return Trigger("vercel", "firewall.attack")

    @staticmethod
    def vercel_any() -> Trigger:
        return Trigger("vercel", "any")

    # ======================================================================
    # Factory methods — Railway
    # ======================================================================

    @staticmethod
    def railway_deployment_failed() -> Trigger:
        return Trigger("railway", "Deployment.failed").railway_events("Deployment.failed")

    @staticmethod
    def railway_deployment_crashed() -> Trigger:
        return Trigger("railway", "Deployment.crashed").railway_events("Deployment.crashed")

    @staticmethod
    def railway_deployment_succeeded() -> Trigger:
        return Trigger("railway", "Deployment.success").railway_events("Deployment.success")

    @staticmethod
    def railway_volume_alert() -> Trigger:
        return Trigger("railway", "alert").railway_events("VolumeAlert")

    @staticmethod
    def railway_resource_alert() -> Trigger:
        return Trigger("railway", "alert").railway_events("MonitorAlert")

    @staticmethod
    def railway_any() -> Trigger:
        return Trigger("railway", "any")

    # ======================================================================
    # Factory methods — Fly.io
    # ======================================================================

    @staticmethod
    def flyio_machine_crashed() -> Trigger:
        return Trigger("flyio", "machine.crashed").fly_events("machine.crashed")

    @staticmethod
    def flyio_machine_stopped() -> Trigger:
        return Trigger("flyio", "machine.stopped").fly_events("machine.stopped")

    @staticmethod
    def flyio_machine_started() -> Trigger:
        return Trigger("flyio", "machine.started").fly_events("machine.started")

    @staticmethod
    def flyio_app_down() -> Trigger:
        return Trigger("flyio", "app.down").fly_events("app.down")

    @staticmethod
    def flyio_any() -> Trigger:
        return Trigger("flyio", "any")

    # ======================================================================
    # Factory methods — Nebius
    # ======================================================================

    @staticmethod
    def nebius_gpu_error() -> Trigger:
        return Trigger("nebius", "node.gpu_error").nebius_events("node.gpu_error")

    @staticmethod
    def nebius_maintenance_scheduled() -> Trigger:
        return Trigger("nebius", "node.maintenance_scheduled").nebius_events("node.maintenance_scheduled")

    @staticmethod
    def nebius_node_not_ready() -> Trigger:
        return Trigger("nebius", "node.not_ready").nebius_events("node.not_ready")

    @staticmethod
    def nebius_instance_stopped() -> Trigger:
        return Trigger("nebius", "instance.stopped").nebius_events("instance.stopped")

    @staticmethod
    def nebius_any() -> Trigger:
        return Trigger("nebius", "any")

    # ======================================================================
    # Factory methods — Daytona
    # ======================================================================

    @staticmethod
    def daytona_sandbox_created() -> Trigger:
        return Trigger("daytona", "sandbox.created").daytona_events("sandbox.created")

    @staticmethod
    def daytona_sandbox_stopped() -> Trigger:
        return Trigger("daytona", "sandbox.stopped").daytona_events("sandbox.stopped")

    @staticmethod
    def daytona_sandbox_error() -> Trigger:
        return Trigger("daytona", "sandbox.error").daytona_events("sandbox.error")

    @staticmethod
    def daytona_sandbox_archived() -> Trigger:
        return Trigger("daytona", "sandbox.archived").daytona_events("sandbox.archived")

    @staticmethod
    def daytona_snapshot_build_failed() -> Trigger:
        return Trigger("daytona", "snapshot.build_failed").daytona_events("snapshot.build_failed")

    @staticmethod
    def daytona_volume_error() -> Trigger:
        return Trigger("daytona", "volume.error").daytona_events("volume.error")

    @staticmethod
    def daytona_any() -> Trigger:
        return Trigger("daytona", "any")

    # ======================================================================
    # Factory methods — Supabase
    # ======================================================================

    @staticmethod
    def supabase_project_health_degraded() -> Trigger:
        return Trigger("supabase", "project.health_degraded").supabase_events("project.health_degraded")

    @staticmethod
    def supabase_backup_failed() -> Trigger:
        return Trigger("supabase", "backup.failed").supabase_events("backup.failed")

    @staticmethod
    def supabase_replica_unhealthy() -> Trigger:
        return Trigger("supabase", "replica.unhealthy").supabase_events("replica.unhealthy")

    @staticmethod
    def supabase_usage_threshold() -> Trigger:
        return Trigger("supabase", "usage.threshold").supabase_events("usage.threshold")

    @staticmethod
    def supabase_branch_created() -> Trigger:
        return Trigger("supabase", "branch.created").supabase_events("branch.created")

    @staticmethod
    def supabase_branch_merge_failed() -> Trigger:
        return Trigger("supabase", "branch.merge_failed").supabase_events("branch.merge_failed")

    @staticmethod
    def supabase_db_row_event() -> Trigger:
        return Trigger("supabase", "db.row_event").supabase_events("db.row_event")

    @staticmethod
    def supabase_any() -> Trigger:
        return Trigger("supabase", "any")

    # ======================================================================
    # Factory methods — PlanetScale
    # ======================================================================

    @staticmethod
    def planetscale_deploy_request_opened() -> Trigger:
        return Trigger("planetscale", "deploy_request.opened").planetscale_events("deploy_request.opened")

    @staticmethod
    def planetscale_deploy_request_queued() -> Trigger:
        return Trigger("planetscale", "deploy_request.queued").planetscale_events("deploy_request.queued")

    @staticmethod
    def planetscale_deploy_request_in_progress() -> Trigger:
        return Trigger("planetscale", "deploy_request.in_progress").planetscale_events("deploy_request.in_progress")

    @staticmethod
    def planetscale_deploy_request_schema_applied() -> Trigger:
        return Trigger("planetscale", "deploy_request.schema_applied").planetscale_events("deploy_request.schema_applied")

    @staticmethod
    def planetscale_deploy_request_errored() -> Trigger:
        return Trigger("planetscale", "deploy_request.errored").planetscale_events("deploy_request.errored")

    @staticmethod
    def planetscale_deploy_request_reverted() -> Trigger:
        return Trigger("planetscale", "deploy_request.reverted").planetscale_events("deploy_request.reverted")

    @staticmethod
    def planetscale_deploy_request_closed() -> Trigger:
        return Trigger("planetscale", "deploy_request.closed").planetscale_events("deploy_request.closed")

    @staticmethod
    def planetscale_branch_ready() -> Trigger:
        return Trigger("planetscale", "branch.ready").planetscale_events("branch.ready")

    @staticmethod
    def planetscale_branch_anomaly() -> Trigger:
        return Trigger("planetscale", "branch.anomaly").planetscale_events("branch.anomaly")

    @staticmethod
    def planetscale_branch_primary_promoted() -> Trigger:
        return Trigger("planetscale", "branch.primary_promoted").planetscale_events("branch.primary_promoted")

    @staticmethod
    def planetscale_branch_sleeping() -> Trigger:
        return Trigger("planetscale", "branch.sleeping").planetscale_events("branch.sleeping")

    @staticmethod
    def planetscale_storage_threshold() -> Trigger:
        return Trigger("planetscale", "cluster.storage").planetscale_events("cluster.storage", "keyspace.storage")

    @staticmethod
    def planetscale_backup_completed() -> Trigger:
        return Trigger("planetscale", "backup.completed").planetscale_events("backup.completed")

    @staticmethod
    def planetscale_backup_failed() -> Trigger:
        return Trigger("planetscale", "backup.failed").planetscale_events("backup.failed")

    @staticmethod
    def planetscale_any() -> Trigger:
        return Trigger("planetscale", "any")

    # ======================================================================
    # Factory methods — Neon
    # ======================================================================

    @staticmethod
    def neon_branch_created() -> Trigger:
        return Trigger("neon", "branch.created").neon_events("branch.created")

    @staticmethod
    def neon_branch_ready() -> Trigger:
        return Trigger("neon", "branch.ready").neon_events("branch.ready")

    @staticmethod
    def neon_operation_failed() -> Trigger:
        return Trigger("neon", "operation.failed").neon_events("operation.failed")

    @staticmethod
    def neon_compute_suspended() -> Trigger:
        return Trigger("neon", "compute.suspended").neon_events("compute.suspended")

    @staticmethod
    def neon_compute_active() -> Trigger:
        return Trigger("neon", "compute.active").neon_events("compute.active")

    @staticmethod
    def neon_usage_threshold() -> Trigger:
        return Trigger("neon", "usage.threshold").neon_events("usage.threshold")

    @staticmethod
    def neon_any() -> Trigger:
        return Trigger("neon", "any")

    # ======================================================================
    # Factory methods — ClickHouse
    # ======================================================================

    @staticmethod
    def clickhouse_service_state_changed() -> Trigger:
        return Trigger("clickhouse", "service.state_changed").clickhouse_events("service.state_changed")

    @staticmethod
    def clickhouse_service_idle() -> Trigger:
        return Trigger("clickhouse", "service.idle").clickhouse_events("service.idle")

    @staticmethod
    def clickhouse_service_scaled() -> Trigger:
        return Trigger("clickhouse", "service.scaled").clickhouse_events("service.scaled")

    @staticmethod
    def clickhouse_version_changed() -> Trigger:
        return Trigger("clickhouse", "service.version_changed").clickhouse_events("service.version_changed")

    @staticmethod
    def clickhouse_backup_completed() -> Trigger:
        return Trigger("clickhouse", "backup.completed").clickhouse_events("backup.completed")

    @staticmethod
    def clickhouse_backup_failed() -> Trigger:
        return Trigger("clickhouse", "backup.failed").clickhouse_events("backup.failed")

    @staticmethod
    def clickhouse_query_error_spike() -> Trigger:
        return Trigger("clickhouse", "query.error_spike").clickhouse_events("query.error_spike")

    @staticmethod
    def clickhouse_clickpipe_failed() -> Trigger:
        return Trigger("clickhouse", "clickpipe.failed").clickhouse_events("clickpipe.failed")

    @staticmethod
    def clickhouse_usage_threshold_crossed() -> Trigger:
        return Trigger("clickhouse", "usage.threshold").clickhouse_events("usage.threshold")

    @staticmethod
    def clickhouse_any() -> Trigger:
        return Trigger("clickhouse", "any")

    # ======================================================================
    # Factory methods — Request (Slack /kestrel-workflow)
    # ======================================================================

    @staticmethod
    def request_kubernetes() -> Trigger:
        return Trigger("request", "any").config(request_categories=["k8s"])

    @staticmethod
    def request_cloud() -> Trigger:
        return Trigger("request", "any").config(request_categories=["cloud"])

    @staticmethod
    def request_cloudflare() -> Trigger:
        return Trigger("request", "any").config(request_categories=["cloudflare"])

    @staticmethod
    def request_pagerduty() -> Trigger:
        return Trigger("request", "any").config(request_categories=["pagerduty"])

    @staticmethod
    def request_datadog() -> Trigger:
        return Trigger("request", "any").config(request_categories=["datadog"])

    @staticmethod
    def request_argocd() -> Trigger:
        return Trigger("request", "any").config(request_categories=["argocd"])

    @staticmethod
    def request_github() -> Trigger:
        return Trigger("request", "any").config(request_categories=["github"])

    @staticmethod
    def request_gitlab() -> Trigger:
        return Trigger("request", "any").config(request_categories=["gitlab"])

    @staticmethod
    def request_helm() -> Trigger:
        return Trigger("request", "any").config(request_categories=["helm"])

    @staticmethod
    def request_vercel() -> Trigger:
        return Trigger("request", "any").config(request_categories=["vercel"])

    @staticmethod
    def request_general() -> Trigger:
        return Trigger("request", "any").config(request_categories=["general"])

    # ======================================================================
    # Factory methods — Custom Webhook
    # ======================================================================

    @staticmethod
    def custom_webhook(signal_type: str = "any") -> Trigger:
        return Trigger("custom_webhook", signal_type)

    # ======================================================================
    # Factory methods — GitHub
    # ======================================================================

    @staticmethod
    def github_pr_opened() -> Trigger:
        return Trigger("github", "pull_request.opened")

    @staticmethod
    def github_pr_merged() -> Trigger:
        return Trigger("github", "pull_request.merged")

    @staticmethod
    def github_action_completed() -> Trigger:
        return Trigger("github", "workflow_run.completed")

    @staticmethod
    def github_action_failed() -> Trigger:
        return Trigger("github", "workflow_run.failed")

    @staticmethod
    def github_push() -> Trigger:
        """Triggers when new commits are pushed to a branch."""
        return Trigger("github", "push")

    @staticmethod
    def github_any() -> Trigger:
        return Trigger("github", "any")

    # ======================================================================
    # Factory methods — Datadog
    # ======================================================================

    @staticmethod
    def datadog_monitor_alert() -> Trigger:
        return Trigger("datadog", "monitor.alert")

    @staticmethod
    def datadog_monitor_warn() -> Trigger:
        return Trigger("datadog", "monitor.warn")

    @staticmethod
    def datadog_monitor_recovered() -> Trigger:
        return Trigger("datadog", "monitor.recovered")

    @staticmethod
    def datadog_monitor_no_data() -> Trigger:
        return Trigger("datadog", "monitor.no_data")

    @staticmethod
    def datadog_monitor_any() -> Trigger:
        return Trigger("datadog", "any")

    # ======================================================================
    # Internal serialisation
    # ======================================================================

    def _to_node(self, node_id: str) -> _Node:
        data: dict[str, Any] = {
            "source": self._source,
            "signal_type": self._signal_type,
            "signal_filter": self._filters,
        }
        if self._label:
            data["label"] = self._label
        return _Node(id=node_id, type="trigger", data=data)

    def _to_trigger_config(self, *, cooldown_hours: int = 0, cooldown_minutes: int = 0,
                           no_cooldown: bool = False, max_concurrent: int = 3) -> dict[str, Any]:
        cfg: dict[str, Any] = {
            "source": self._source,
            "signals": [{"signal_type": self._signal_type, "filters": self._filters}],
            "max_concurrent_executions": max_concurrent,
        }
        if no_cooldown:
            cfg["cooldown_hours"] = 0
            cfg["cooldown_minutes"] = 0
            cfg["no_cooldown"] = True
        else:
            if cooldown_hours:
                cfg["cooldown_hours"] = cooldown_hours
            if cooldown_minutes:
                cfg["cooldown_minutes"] = cooldown_minutes
        return cfg
