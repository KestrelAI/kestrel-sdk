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

    def clickhouse_parts_threshold(self, count: int) -> Trigger:
        """Set the max part-count-for-partition at or above which a
        service.too_many_parts trigger fires (default 3000)."""
        self._filters["clickhouse_parts_threshold"] = count
        return self

    def clickhouse_concurrency_threshold(self, count: int) -> Trigger:
        """Set the concurrent running query count at or above which a
        service.high_query_concurrency trigger fires (default 1000)."""
        self._filters["clickhouse_concurrency_threshold"] = count
        return self

    def clickhouse_poll_interval(self, interval: str) -> Trigger:
        """Set the poll cadence for the poll-based ClickHouse triggers (one of
        "1m", "5m", "15m", "30m"). ClickHouse Cloud has no control-plane
        webhooks."""
        self._filters["clickhouse_poll_interval"] = interval
        return self

    # -- Terraform Cloud filters ---------------------------------------------

    def terraform_events(self, *types: str) -> Trigger:
        self._filters["terraform_event_types"] = list(types)
        return self

    def terraform_workspaces(self, *workspaces: str) -> Trigger:
        self._filters["terraform_workspaces"] = list(workspaces)
        return self

    def terraform_run_statuses(self, *statuses: str) -> Trigger:
        self._filters["terraform_run_statuses"] = list(statuses)
        return self

    # -- Pulumi Cloud filters --------------------------------------------------

    def pulumi_events(self, *types: str) -> Trigger:
        self._filters["pulumi_event_types"] = list(types)
        return self

    def pulumi_stacks(self, *stacks: str) -> Trigger:
        """Restrict to specific stacks by project/stack reference (or bare stack name)."""
        self._filters["pulumi_stacks"] = list(stacks)
        return self

    def pulumi_projects(self, *projects: str) -> Trigger:
        self._filters["pulumi_projects"] = list(projects)
        return self

    # -- HashiCorp Vault filters -------------------------------------------

    def vault_events(self, *types: str) -> Trigger:
        self._filters["vault_event_types"] = list(types)
        return self

    def vault_mounts(self, *mounts: str) -> Trigger:
        """Restrict secret events to specific KV v2 mounts (e.g. "secret/")."""
        self._filters["vault_mounts"] = list(mounts)
        return self

    def vault_secret_paths(self, *paths: str) -> Trigger:
        """Restrict secret events to path prefixes within the mount (e.g. "app/prod")."""
        self._filters["vault_secret_paths"] = list(paths)
        return self

    def vault_secret_max_age_days(self, days: int) -> Trigger:
        """Age threshold (days) for the secret.stale trigger. Defaults to 90."""
        self._filters["vault_secret_max_age_days"] = days
        return self

    def vault_poll_interval(self, interval: str) -> Trigger:
        """Set the poll cadence for the poll-based Vault triggers (one of "1m",
        "5m", "15m", "30m"). Vault has no outbound webhooks; only secret
        metadata is polled — never values."""
        self._filters["vault_poll_interval"] = interval
        return self

    # -- Infisical filters ---------------------------------------------------

    def infisical_events(self, *types: str) -> Trigger:
        self._filters["infisical_event_types"] = list(types)
        return self

    def infisical_projects(self, *project_ids: str) -> Trigger:
        self._filters["infisical_project_ids"] = list(project_ids)
        return self

    def infisical_environments(self, *environments: str) -> Trigger:
        """Restrict secret events to environment slugs (e.g. "prod")."""
        self._filters["infisical_environments"] = list(environments)
        return self

    def infisical_secret_paths(self, *paths: str) -> Trigger:
        """Restrict secret events to folder path prefixes (e.g. "/backend")."""
        self._filters["infisical_secret_paths"] = list(paths)
        return self

    def infisical_poll_interval(self, interval: str) -> Trigger:
        """Set the poll cadence for the poll-based Infisical triggers (one of
        "1m", "5m", "15m", "30m"). Secret values are never read."""
        self._filters["infisical_poll_interval"] = interval
        return self

    # -- Jenkins filters -----------------------------------------------------

    def jenkins_events(self, *types: str) -> Trigger:
        self._filters["jenkins_event_types"] = list(types)
        return self

    def jenkins_jobs(self, *jobs: str) -> Trigger:
        """Scope to Jenkins job full names (folder-nested jobs use a path like
        "platform/deploy-api"; ["*"] for all)."""
        self._filters["jenkins_jobs"] = list(jobs)
        return self

    def jenkins_build_statuses(self, *statuses: str) -> Trigger:
        """Restrict build.completed triggers by result (SUCCESS, FAILURE,
        UNSTABLE, ABORTED; ["*"] for any)."""
        self._filters["jenkins_build_statuses"] = list(statuses)
        return self

    # -- CircleCI filters ------------------------------------------------------

    def circleci_events(self, *types: str) -> Trigger:
        self._filters["circleci_event_types"] = list(types)
        return self

    def circleci_projects(self, *slugs: str) -> Trigger:
        """Scope to CircleCI project slugs like "gh/org/repo" (["*"] for all)."""
        self._filters["circleci_projects"] = list(slugs)
        return self

    def circleci_branches(self, *branches: str) -> Trigger:
        self._filters["circleci_branches"] = list(branches)
        return self

    def circleci_statuses(self, *statuses: str) -> Trigger:
        """Restrict by workflow/job status (success, failed, error, canceled,
        unauthorized; ["*"] for any)."""
        self._filters["circleci_statuses"] = list(statuses)
        return self

    # -- SonarCloud filters --------------------------------------------------

    def sonarcloud_events(self, *types: str) -> Trigger:
        """Restrict to SonarCloud webhook event types ("analysis.completed",
        "analysis.failed"; ["*"] for all)."""
        self._filters["sonarcloud_event_types"] = list(types)
        return self

    def sonarcloud_projects(self, *keys: str) -> Trigger:
        """Scope to SonarCloud project keys (["*"] for all)."""
        self._filters["sonarcloud_projects"] = list(keys)
        return self

    def sonarcloud_quality_gate_statuses(self, *statuses: str) -> Trigger:
        """Restrict analysis.completed triggers by quality gate result (OK,
        ERROR, NONE; ["*"] for any)."""
        self._filters["sonarcloud_quality_gate_statuses"] = list(statuses)
        return self

    def sonarcloud_branches(self, *branches: str) -> Trigger:
        self._filters["sonarcloud_branches"] = list(branches)
        return self

    # -- Okta filters --------------------------------------------------------

    def okta_events(self, *types: str) -> Trigger:
        """Restrict to Okta System Log event types (e.g. "user.account.lock",
        "group.user_membership.add"; ["*"] for all the trigger detects)."""
        self._filters["okta_event_types"] = list(types)
        return self

    def okta_target_users(self, *users: str) -> Trigger:
        """Scope to events about specific users by login/email (["*"] for all)."""
        self._filters["okta_target_users"] = list(users)
        return self

    def okta_actors(self, *actors: str) -> Trigger:
        """Scope to events performed by specific admins/users by login/email
        (["*"] for any actor)."""
        self._filters["okta_actors"] = list(actors)
        return self

    def okta_target_groups(self, *groups: str) -> Trigger:
        """For group membership events, scope to specific group names
        (e.g. "Okta Administrators"; ["*"] for any group)."""
        self._filters["okta_target_groups"] = list(groups)
        return self

    def okta_outcomes(self, *outcomes: str) -> Trigger:
        """Restrict by event outcome (SUCCESS, FAILURE; ["*"] for both)."""
        self._filters["okta_outcomes"] = list(outcomes)
        return self

    def okta_poll_interval(self, interval: str) -> Trigger:
        """How often Kestrel tails the Okta System Log ("1m", "5m", "15m", "30m")."""
        self._filters["okta_poll_interval"] = interval
        return self

    # -- Kyverno filters -----------------------------------------------------
    # Cluster/namespace scoping uses the generic .cluster() / .namespace()
    # helpers since Kyverno signals ride the Kubernetes event pipeline.

    def kyverno_policies(self, *policies: str) -> Trigger:
        """Scope to violations produced by specific Kyverno policy names
        (e.g. "disallow-privileged-containers"; ["*"] for all)."""
        self._filters["kyverno_policies"] = list(policies)
        return self

    def kyverno_severities(self, *severities: str) -> Trigger:
        """Restrict by violation severity as annotated on the policy
        (critical, high, medium, low, info; ["*"] for any)."""
        self._filters["kyverno_severities"] = list(severities)
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

    # -- Schedule filters ----------------------------------------------------

    def schedule_interval(self, interval: str) -> Trigger:
        """Set the recurring cadence: "hourly", "daily", "weekly", or "monthly"."""
        self._filters["schedule_interval"] = interval
        return self

    def schedule_time(self, hhmm_utc: str) -> Trigger:
        """Set the HH:MM (24h, UTC) fire time for daily/weekly/monthly schedules."""
        self._filters["schedule_time_utc"] = hhmm_utc
        return self

    def schedule_day_of_week(self, day: int) -> Trigger:
        """Set the weekday for weekly schedules (0=Sunday ... 6=Saturday)."""
        self._filters["schedule_day_of_week"] = day
        return self

    def schedule_day_of_month(self, day: int) -> Trigger:
        """Set the day of month (1-28) for monthly schedules."""
        self._filters["schedule_day_of_month"] = day
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
    def aws_forecast_overrun() -> Trigger:
        """Month-end cost forecast exceeds last month's spend by >20%."""
        return Trigger("aws", "forecast_overrun")

    @staticmethod
    def aws_spend_spike() -> Trigger:
        """Yesterday's spend exceeds the trailing 7-day average."""
        return Trigger("aws", "spend_spike")

    @staticmethod
    def aws_idle_resource() -> Trigger:
        """Daily idle-resource scan found unattached volumes, unassociated EIPs, or idle instances."""
        return Trigger("aws", "idle_resource")

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
    # Factory methods — Karpenter
    # ======================================================================

    @staticmethod
    def karpenter_node_provisioning_failed() -> Trigger:
        return Trigger("karpenter", "nodeclaim.provisioning_failed")

    @staticmethod
    def karpenter_node_interrupted() -> Trigger:
        return Trigger("karpenter", "node.interrupted")

    @staticmethod
    def karpenter_nodepool_limit_reached() -> Trigger:
        return Trigger("karpenter", "nodepool.limit_reached")

    @staticmethod
    def karpenter_any() -> Trigger:
        return Trigger("karpenter", "any")

    # ======================================================================
    # Factory methods — Kyverno
    # ======================================================================

    @staticmethod
    def kyverno_policy_violation() -> Trigger:
        """A Kyverno PolicyReport recorded a new fail/warn/error result
        (Audit-mode violation on a live resource)."""
        return Trigger("kyverno", "policy.violation")

    @staticmethod
    def kyverno_admission_blocked() -> Trigger:
        """A Kyverno Enforce-mode policy blocked a resource at admission."""
        return Trigger("kyverno", "policy.admission_blocked")

    @staticmethod
    def kyverno_any() -> Trigger:
        return Trigger("kyverno", "any")

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
    def clickhouse_too_many_parts() -> Trigger:
        return Trigger("clickhouse", "service.too_many_parts").clickhouse_events("service.too_many_parts")

    @staticmethod
    def clickhouse_high_query_concurrency() -> Trigger:
        return Trigger("clickhouse", "service.high_query_concurrency").clickhouse_events("service.high_query_concurrency")

    @staticmethod
    def clickhouse_any() -> Trigger:
        return Trigger("clickhouse", "any")

    # ======================================================================
    # Factory methods — Terraform Cloud
    # ======================================================================

    @staticmethod
    def terraform_run_created() -> Trigger:
        return Trigger("terraform", "run:created").terraform_events("run:created")

    @staticmethod
    def terraform_run_needs_attention() -> Trigger:
        """A plan finished and the run is awaiting confirmation/approval."""
        return Trigger("terraform", "run:needs_attention").terraform_events("run:needs_attention")

    @staticmethod
    def terraform_run_completed() -> Trigger:
        return Trigger("terraform", "run:completed").terraform_events("run:completed")

    @staticmethod
    def terraform_run_errored() -> Trigger:
        return Trigger("terraform", "run:errored").terraform_events("run:errored")

    @staticmethod
    def terraform_drift_detected() -> Trigger:
        """A health assessment detected drift between state and real infrastructure."""
        return Trigger("terraform", "assessment:drifted").terraform_events("assessment:drifted")

    @staticmethod
    def terraform_check_failed() -> Trigger:
        return Trigger("terraform", "assessment:check_failure").terraform_events("assessment:check_failure")

    @staticmethod
    def terraform_any() -> Trigger:
        return Trigger("terraform", "any")

    # ======================================================================
    # Factory methods — Pulumi Cloud
    # ======================================================================

    @staticmethod
    def pulumi_update_succeeded() -> Trigger:
        return Trigger("pulumi", "update_succeeded").pulumi_events("update_succeeded")

    @staticmethod
    def pulumi_update_failed() -> Trigger:
        return Trigger("pulumi", "update_failed").pulumi_events("update_failed")

    @staticmethod
    def pulumi_preview_failed() -> Trigger:
        return Trigger("pulumi", "preview_failed").pulumi_events("preview_failed")

    @staticmethod
    def pulumi_destroy_succeeded() -> Trigger:
        return Trigger("pulumi", "destroy_succeeded").pulumi_events("destroy_succeeded")

    @staticmethod
    def pulumi_deployment_started() -> Trigger:
        return Trigger("pulumi", "deployment_started").pulumi_events("deployment_started")

    @staticmethod
    def pulumi_deployment_succeeded() -> Trigger:
        return Trigger("pulumi", "deployment_succeeded").pulumi_events("deployment_succeeded")

    @staticmethod
    def pulumi_deployment_failed() -> Trigger:
        return Trigger("pulumi", "deployment_failed").pulumi_events("deployment_failed")

    @staticmethod
    def pulumi_drift_detected() -> Trigger:
        """A scheduled drift run detected drift between the stack's state and real infrastructure."""
        return Trigger("pulumi", "drift_detected").pulumi_events("drift_detected")

    @staticmethod
    def pulumi_policy_violation() -> Trigger:
        """A mandatory policy pack blocked an update."""
        return Trigger("pulumi", "policy_violation_mandatory").pulumi_events("policy_violation_mandatory")

    @staticmethod
    def pulumi_stack_created() -> Trigger:
        return Trigger("pulumi", "stack_created").pulumi_events("stack_created")

    @staticmethod
    def pulumi_stack_deleted() -> Trigger:
        return Trigger("pulumi", "stack_deleted").pulumi_events("stack_deleted")

    @staticmethod
    def pulumi_any() -> Trigger:
        return Trigger("pulumi", "any")

    # ======================================================================
    # Factory methods — HashiCorp Vault (all poll-based; Vault has no
    # outbound webhooks. Secret values are never read — only KV metadata.)
    # ======================================================================

    @staticmethod
    def vault_sealed() -> Trigger:
        """Vault sealed — secrets are unavailable until it is unsealed."""
        return Trigger("vault", "seal.sealed").vault_events("seal.sealed")

    @staticmethod
    def vault_unsealed() -> Trigger:
        return Trigger("vault", "seal.unsealed").vault_events("seal.unsealed")

    @staticmethod
    def vault_health_degraded() -> Trigger:
        """Vault became unreachable or reported an unhealthy status."""
        return Trigger("vault", "health.degraded").vault_events("health.degraded")

    @staticmethod
    def vault_secret_version_created() -> Trigger:
        """A KV v2 secret got a new version (metadata only — values are never read)."""
        return Trigger("vault", "secret.version_created").vault_events("secret.version_created")

    @staticmethod
    def vault_secret_stale() -> Trigger:
        """A secret's latest version exceeded the rotation age threshold
        (set with .vault_secret_max_age_days(), default 90)."""
        return Trigger("vault", "secret.stale").vault_events("secret.stale")

    @staticmethod
    def vault_policy_created() -> Trigger:
        return Trigger("vault", "policy.created").vault_events("policy.created")

    @staticmethod
    def vault_policy_deleted() -> Trigger:
        return Trigger("vault", "policy.deleted").vault_events("policy.deleted")

    @staticmethod
    def vault_auth_method_enabled() -> Trigger:
        return Trigger("vault", "auth_method.enabled").vault_events("auth_method.enabled")

    @staticmethod
    def vault_auth_method_disabled() -> Trigger:
        return Trigger("vault", "auth_method.disabled").vault_events("auth_method.disabled")

    @staticmethod
    def vault_any() -> Trigger:
        return Trigger("vault", "any")

    # ======================================================================
    # Factory methods — Infisical (all poll-based, driven by the audit log
    # and project APIs. Secret values are never read.)
    # ======================================================================

    @staticmethod
    def infisical_secret_created() -> Trigger:
        return Trigger("infisical", "secret.created").infisical_events("secret.created")

    @staticmethod
    def infisical_secret_updated() -> Trigger:
        return Trigger("infisical", "secret.updated").infisical_events("secret.updated")

    @staticmethod
    def infisical_secret_deleted() -> Trigger:
        return Trigger("infisical", "secret.deleted").infisical_events("secret.deleted")

    @staticmethod
    def infisical_approval_requested() -> Trigger:
        """A secret change approval request was opened in a project."""
        return Trigger("infisical", "approval.requested").infisical_events("approval.requested")

    @staticmethod
    def infisical_secret_sync_failed() -> Trigger:
        """A secret sync to an external destination failed."""
        return Trigger("infisical", "sync.failed").infisical_events("sync.failed")

    @staticmethod
    def infisical_identity_created() -> Trigger:
        """A new machine identity appeared in the organization."""
        return Trigger("infisical", "identity.created").infisical_events("identity.created")

    @staticmethod
    def infisical_any() -> Trigger:
        return Trigger("infisical", "any")

    # ======================================================================
    # Factory methods — Jenkins
    # ======================================================================

    @staticmethod
    def jenkins_build_failed() -> Trigger:
        return Trigger("jenkins", "build.completed").jenkins_events("build.completed").jenkins_build_statuses("FAILURE")

    @staticmethod
    def jenkins_build_unstable() -> Trigger:
        return Trigger("jenkins", "build.completed").jenkins_events("build.completed").jenkins_build_statuses("UNSTABLE")

    @staticmethod
    def jenkins_build_succeeded() -> Trigger:
        return Trigger("jenkins", "build.completed").jenkins_events("build.completed").jenkins_build_statuses("SUCCESS")

    @staticmethod
    def jenkins_build_completed() -> Trigger:
        """Any build completion regardless of result."""
        return Trigger("jenkins", "build.completed").jenkins_events("build.completed").jenkins_build_statuses("*")

    @staticmethod
    def jenkins_build_started() -> Trigger:
        return Trigger("jenkins", "build.started").jenkins_events("build.started")

    @staticmethod
    def jenkins_any() -> Trigger:
        return Trigger("jenkins", "any")

    # ======================================================================
    # Factory methods — CircleCI
    # ======================================================================

    @staticmethod
    def circleci_workflow_failed() -> Trigger:
        return Trigger("circleci", "workflow-completed").circleci_events("workflow-completed").circleci_statuses("failed", "error")

    @staticmethod
    def circleci_workflow_succeeded() -> Trigger:
        return Trigger("circleci", "workflow-completed").circleci_events("workflow-completed").circleci_statuses("success")

    @staticmethod
    def circleci_workflow_completed() -> Trigger:
        """Any workflow completion regardless of status."""
        return Trigger("circleci", "workflow-completed").circleci_events("workflow-completed").circleci_statuses("*")

    @staticmethod
    def circleci_job_failed() -> Trigger:
        return Trigger("circleci", "job-completed").circleci_events("job-completed").circleci_statuses("failed")

    @staticmethod
    def circleci_any() -> Trigger:
        return Trigger("circleci", "any")

    # ======================================================================
    # Factory methods — SonarCloud
    # ======================================================================

    @staticmethod
    def sonarcloud_quality_gate_failed() -> Trigger:
        """Analysis completed with the quality gate in ERROR."""
        return Trigger("sonarcloud", "analysis.completed").sonarcloud_events("analysis.completed").sonarcloud_quality_gate_statuses("ERROR")

    @staticmethod
    def sonarcloud_quality_gate_passed() -> Trigger:
        """Analysis completed with the quality gate OK."""
        return Trigger("sonarcloud", "analysis.completed").sonarcloud_events("analysis.completed").sonarcloud_quality_gate_statuses("OK")

    @staticmethod
    def sonarcloud_analysis_completed() -> Trigger:
        """Any completed analysis regardless of quality gate result."""
        return Trigger("sonarcloud", "analysis.completed").sonarcloud_events("analysis.completed").sonarcloud_quality_gate_statuses("*")

    @staticmethod
    def sonarcloud_analysis_failed() -> Trigger:
        """The analysis task itself failed (broken scanner run)."""
        return Trigger("sonarcloud", "analysis.failed").sonarcloud_events("analysis.failed")

    @staticmethod
    def sonarcloud_any() -> Trigger:
        return Trigger("sonarcloud", "any")

    # ======================================================================
    # Factory methods — Okta
    # ======================================================================

    @staticmethod
    def okta_user_locked_out() -> Trigger:
        """User locked out after repeated failed sign-ins (brute-force indicator)."""
        return Trigger("okta", "user.account.lock").okta_events("user.account.lock")

    @staticmethod
    def okta_suspicious_activity() -> Trigger:
        """End-user reported suspicious activity or Okta ThreatInsight detected a threat."""
        return Trigger("okta", "user.account.report_suspicious_activity_by_enduser").okta_events(
            "user.account.report_suspicious_activity_by_enduser", "security.threat.detected"
        )

    @staticmethod
    def okta_admin_privilege_granted() -> Trigger:
        """A user was granted an admin role."""
        return Trigger("okta", "user.account.privilege.grant").okta_events("user.account.privilege.grant")

    @staticmethod
    def okta_mfa_factor_changed() -> Trigger:
        """A user's MFA factor was deactivated or all factors were reset."""
        return Trigger("okta", "user.mfa.factor.deactivate").okta_events(
            "user.mfa.factor.deactivate", "user.mfa.factor.reset_all"
        )

    @staticmethod
    def okta_user_created() -> Trigger:
        """A new user was created in Okta."""
        return Trigger("okta", "user.lifecycle.create").okta_events("user.lifecycle.create")

    @staticmethod
    def okta_user_deactivated() -> Trigger:
        """A user was deactivated or suspended."""
        return Trigger("okta", "user.lifecycle.deactivate").okta_events(
            "user.lifecycle.deactivate", "user.lifecycle.suspend"
        )

    @staticmethod
    def okta_group_membership_changed(*groups: str) -> Trigger:
        """A user was added to or removed from a group. Optionally scope to
        specific group names (e.g. "Okta Administrators")."""
        t = Trigger("okta", "group.user_membership.add").okta_events(
            "group.user_membership.add", "group.user_membership.remove"
        )
        if groups:
            t = t.okta_target_groups(*groups)
        return t

    @staticmethod
    def okta_app_assignment_changed() -> Trigger:
        """A user was assigned to or removed from an application."""
        return Trigger("okta", "application.user_membership.add").okta_events(
            "application.user_membership.add", "application.user_membership.remove"
        )

    @staticmethod
    def okta_any() -> Trigger:
        return Trigger("okta", "any")

    # ======================================================================
    # Factory methods — Request (Slack /kestrel-workflow)
    # ======================================================================

    @staticmethod
    def request_kubernetes() -> Trigger:
        return Trigger("request", "any").filter(request_categories=["k8s"])

    @staticmethod
    def request_cloud() -> Trigger:
        return Trigger("request", "any").filter(request_categories=["cloud"])

    @staticmethod
    def request_cloudflare() -> Trigger:
        return Trigger("request", "any").filter(request_categories=["cloudflare"])

    @staticmethod
    def request_pagerduty() -> Trigger:
        return Trigger("request", "any").filter(request_categories=["pagerduty"])

    @staticmethod
    def request_datadog() -> Trigger:
        return Trigger("request", "any").filter(request_categories=["datadog"])

    @staticmethod
    def request_argocd() -> Trigger:
        return Trigger("request", "any").filter(request_categories=["argocd"])

    @staticmethod
    def request_argo_rollouts() -> Trigger:
        return Trigger("request", "any").filter(request_categories=["argo-rollouts"])

    @staticmethod
    def request_fluxcd() -> Trigger:
        return Trigger("request", "any").filter(request_categories=["fluxcd"])

    @staticmethod
    def request_karpenter() -> Trigger:
        return Trigger("request", "any").filter(request_categories=["karpenter"])

    @staticmethod
    def request_kyverno() -> Trigger:
        return Trigger("request", "any").filter(request_categories=["kyverno"])

    @staticmethod
    def request_github() -> Trigger:
        return Trigger("request", "any").filter(request_categories=["github"])

    @staticmethod
    def request_gitlab() -> Trigger:
        return Trigger("request", "any").filter(request_categories=["gitlab"])

    @staticmethod
    def request_helm() -> Trigger:
        return Trigger("request", "any").filter(request_categories=["helm"])

    @staticmethod
    def request_vercel() -> Trigger:
        return Trigger("request", "any").filter(request_categories=["vercel"])

    @staticmethod
    def request_terraform() -> Trigger:
        return Trigger("request", "any").filter(request_categories=["terraform"])

    @staticmethod
    def request_pulumi() -> Trigger:
        return Trigger("request", "any").filter(request_categories=["pulumi"])

    @staticmethod
    def request_jenkins() -> Trigger:
        return Trigger("request", "any").filter(request_categories=["jenkins"])

    @staticmethod
    def request_circleci() -> Trigger:
        return Trigger("request", "any").filter(request_categories=["circleci"])

    @staticmethod
    def request_vault() -> Trigger:
        return Trigger("request", "any").filter(request_categories=["vault"])

    @staticmethod
    def request_infisical() -> Trigger:
        return Trigger("request", "any").filter(request_categories=["infisical"])

    @staticmethod
    def request_sonarcloud() -> Trigger:
        return Trigger("request", "any").filter(request_categories=["sonarcloud"])

    @staticmethod
    def request_okta() -> Trigger:
        return Trigger("request", "any").filter(request_categories=["okta"])

    @staticmethod
    def request_general() -> Trigger:
        return Trigger("request", "any").filter(request_categories=["general"])

    # ======================================================================
    # Factory methods — Schedule
    # ======================================================================

    @staticmethod
    def schedule_hourly() -> Trigger:
        """Fires at the top of every hour."""
        return Trigger("schedule", "schedule").schedule_interval("hourly")

    @staticmethod
    def schedule_daily(time_utc: str = "09:00") -> Trigger:
        """Fires once a day at the given HH:MM UTC time."""
        return Trigger("schedule", "schedule").schedule_interval("daily").schedule_time(time_utc)

    @staticmethod
    def schedule_weekly(day_of_week: int = 1, time_utc: str = "09:00") -> Trigger:
        """Fires once a week (0=Sunday ... 6=Saturday; default Monday) at HH:MM UTC."""
        return (
            Trigger("schedule", "schedule")
            .schedule_interval("weekly")
            .schedule_day_of_week(day_of_week)
            .schedule_time(time_utc)
        )

    @staticmethod
    def schedule_monthly(day_of_month: int = 1, time_utc: str = "09:00") -> Trigger:
        """Fires once a month on the given day (1-28) at HH:MM UTC."""
        return (
            Trigger("schedule", "schedule")
            .schedule_interval("monthly")
            .schedule_day_of_month(day_of_month)
            .schedule_time(time_utc)
        )

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
