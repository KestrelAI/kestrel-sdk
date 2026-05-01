"""Kestrel Workflow Builder — typed, fluent API for constructing workflows.

Quick start::

    from kestrel.workflows import Workflow, Trigger, Action, Condition, Approval

    wf = (
        Workflow("Pod Crash RCA")
        .trigger(Trigger.k8s_pod_status().reasons("CrashLoopBackOff"))
        .cooldown(hours=1)
        .then(Action.kestrel_trigger_rca())
        .then(Action.slack_send_message().channel("incidents").include_rca(True))
    )
"""

from .actions import Action
from .approvals import Approval
from .builder import Workflow
from .conditions import Condition
from .triggers import Trigger

__all__ = [
    "Action",
    "Approval",
    "Condition",
    "Trigger",
    "Workflow",
]
