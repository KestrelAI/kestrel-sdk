"""Workflow builder — the main entry point for constructing workflows programmatically."""

from __future__ import annotations

from typing import Any, Optional, Union

from .actions import Action
from .approvals import Approval
from .conditions import Condition
from .triggers import Trigger
from .types import _Edge, _Node

Step = Union[Action, Condition, Approval]


class Workflow:
    """Fluent builder for Kestrel workflow definitions.

    Example::

        wf = (
            Workflow("Pod Crash RCA + Jira")
            .description("Run RCA and create Jira ticket on pod crash")
            .trigger(
                Trigger.k8s_pod_status()
                .filter(reasons=["CrashLoopBackOff"])
                .cluster("my-cluster")
            )
            .cooldown(hours=24)
            .then(Action.kestrel_trigger_rca().label("Run RCA"))
            .then(Action.jira_create_ticket()
                .project("KAN")
                .title("{{incident.title}}")
                .priority("High")
            )
        )

        client = KestrelClient.from_config()
        created = client.workflows.deploy(wf)
    """

    def __init__(self, name: str) -> None:
        self._name = name
        self._description = ""
        self._trigger: Optional[Trigger] = None
        self._cooldown_hours = 0
        self._cooldown_minutes = 0
        self._no_cooldown = False
        self._max_concurrent = 3
        self._alert_config: Optional[dict[str, Any]] = None

        self._nodes: list[_Node] = []
        self._edges: list[_Edge] = []
        self._action_counter = 0
        self._condition_counter = 0
        self._approval_counter = 0
        self._edge_counter = 0

        # Tracks where .then() / .on_true() / .on_false() etc. attach next
        self._cursor: Optional[str] = None
        self._cursor_label: Optional[str] = None

        # Last branching node (condition or approval) for .on_true()/.on_false() etc.
        self._last_branch_node: Optional[str] = None

    def description(self, desc: str) -> Workflow:
        self._description = desc
        return self

    def trigger(self, t: Trigger) -> Workflow:
        self._trigger = t
        node = t._to_node("trigger-1")
        self._nodes.append(node)
        self._cursor = node.id
        self._cursor_label = None
        return self

    def cooldown(self, *, hours: int = 0, minutes: int = 0) -> Workflow:
        if hours == 0 and minutes == 0:
            self._no_cooldown = True
        else:
            self._cooldown_hours = hours
            self._cooldown_minutes = minutes
            self._no_cooldown = False
        return self

    def max_concurrent(self, n: int) -> Workflow:
        self._max_concurrent = n
        return self

    def alert_on_failure(self, *, channel: str = "", dm_user_id: str = "") -> Workflow:
        self._alert_config = {"enabled": True, "channel": channel, "dm_user_id": dm_user_id}
        return self

    # -- Step attachment ---------------------------------------------------

    def then(self, step: Step) -> Workflow:
        """Attach a step after the current cursor position."""
        return self._attach(step, source=self._cursor, edge_label=self._cursor_label)

    def on_true(self, step: Step) -> Workflow:
        """Attach a step to the **true** branch of the last condition."""
        return self._attach(step, source=self._last_branch_node, edge_label="true")

    def on_false(self, step: Step) -> Workflow:
        """Attach a step to the **false** branch of the last condition."""
        return self._attach(step, source=self._last_branch_node, edge_label="false")

    def on_approved(self, step: Step) -> Workflow:
        """Attach a step to the **approved** branch of the last approval gate."""
        return self._attach(step, source=self._last_branch_node, edge_label="approved")

    def on_rejected(self, step: Step) -> Workflow:
        """Attach a step to the **rejected** branch of the last approval gate."""
        return self._attach(step, source=self._last_branch_node, edge_label="rejected")

    def also(self, step: Step) -> Workflow:
        """Attach a parallel step from the same parent as the last step (sibling)."""
        return self._attach(step, source=self._last_branch_node or self._cursor, edge_label=None)

    def after(self, node_id: str) -> Workflow:
        """Move the cursor to a specific node ID for explicit wiring."""
        self._cursor = node_id
        self._cursor_label = None
        return self

    # -- Build -------------------------------------------------------------

    def build(self) -> tuple[dict[str, Any], dict[str, Any]]:
        """Compile the builder into ``(definition, trigger_config)`` dicts."""
        if self._trigger is None:
            raise ValueError("Workflow must have a trigger (call .trigger() first)")

        definition = {
            "nodes": [n.to_dict() for n in self._nodes],
            "edges": [e.to_dict() for e in self._edges],
        }

        trigger_config = self._trigger._to_trigger_config(
            cooldown_hours=self._cooldown_hours,
            cooldown_minutes=self._cooldown_minutes,
            no_cooldown=self._no_cooldown,
            max_concurrent=self._max_concurrent,
        )

        return definition, trigger_config

    # -- Private -----------------------------------------------------------

    def _next_id(self, step: Step) -> str:
        if isinstance(step, Action):
            self._action_counter += 1
            return f"action-{self._action_counter}"
        elif isinstance(step, Condition):
            self._condition_counter += 1
            return f"condition-{self._condition_counter}"
        elif isinstance(step, Approval):
            self._approval_counter += 1
            return f"approval-{self._approval_counter}"
        raise TypeError(f"Unknown step type: {type(step)}")

    def _next_edge_id(self) -> str:
        self._edge_counter += 1
        return f"e{self._edge_counter}"

    def _attach(self, step: Step, *, source: Optional[str], edge_label: Optional[str]) -> Workflow:
        node_id = self._next_id(step)
        node = step._to_node(node_id)
        self._nodes.append(node)

        if source is not None:
            edge = _Edge(
                id=self._next_edge_id(),
                source=source,
                target=node_id,
                label=edge_label,
            )
            self._edges.append(edge)

        # Move cursor to the new node for subsequent .then() calls
        self._cursor = node_id
        self._cursor_label = None

        # Track branching nodes so .on_true()/.on_false() etc. can reference them
        if isinstance(step, (Condition, Approval)):
            self._last_branch_node = node_id

        return self
