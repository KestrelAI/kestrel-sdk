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

    # -- Request filters ---------------------------------------------------

    def request_categories(self, *c: str) -> Trigger:
        self._filters["request_categories"] = list(c)
        return self

    def request_keywords(self, *k: str) -> Trigger:
        self._filters["request_keywords"] = list(k)
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
    # Factory methods — Request (Slack /kestrel-workflow)
    # ======================================================================

    @staticmethod
    def request_k8s_provision() -> Trigger:
        return Trigger("request", "k8s_provision")

    @staticmethod
    def request_k8s_config() -> Trigger:
        return Trigger("request", "k8s_config")

    @staticmethod
    def request_k8s_investigate() -> Trigger:
        return Trigger("request", "k8s_investigate")

    @staticmethod
    def request_cloud_provision() -> Trigger:
        return Trigger("request", "cloud_provision")

    @staticmethod
    def request_cloud_config() -> Trigger:
        return Trigger("request", "cloud_config")

    @staticmethod
    def request_cloud_investigate() -> Trigger:
        return Trigger("request", "cloud_investigate")

    @staticmethod
    def request_any() -> Trigger:
        return Trigger("request", "any")

    # ======================================================================
    # Factory methods — Custom Webhook
    # ======================================================================

    @staticmethod
    def custom_webhook(signal_type: str = "any") -> Trigger:
        return Trigger("custom_webhook", signal_type)

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
