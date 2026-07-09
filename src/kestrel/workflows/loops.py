"""Poll-until loop builder for workflow definitions."""

from __future__ import annotations

from .actions import Action
from .conditions import Condition
from .types import _Node


class PollUntil:
    """Builds a self-looping "Poll Until" node.

    The node repeatedly executes ONE embedded catalog action at a fixed
    interval, evaluates a condition against that iteration's output, and exits
    on the **met** branch when the condition holds or on the **timeout**
    branch when the timeout elapses. The polling loop is internal to the node
    and durable across server restarts::

        poll = (
            PollUntil(
                Action.daytona_get_sandbox()
                .sandbox_id("{{step_outputs.action-1.sandbox_id}}"),
                Condition.not_equals("state", "started"),
            )
            .every(seconds=60)
            .timeout(minutes=60)
            .label("Poll until sandbox stops")
        )

        wf.then(poll).on_met(...).on_timeout(...)
    """

    def __init__(self, action: Action, condition: Condition) -> None:
        self._action = action
        self._condition = condition
        self._interval_seconds = 60
        self._timeout_minutes = 60
        self._label: str = ""

    def label(self, text: str) -> PollUntil:
        self._label = text
        return self

    def every(self, *, seconds: int = 0, minutes: int = 0) -> PollUntil:
        """Set the polling interval (minimum 30 seconds, default 60)."""
        total = seconds + minutes * 60
        if total > 0:
            self._interval_seconds = total
        return self

    def timeout(self, *, minutes: int = 0, hours: int = 0) -> PollUntil:
        """Set the loop timeout (default 60 minutes)."""
        total = minutes + hours * 60
        if total > 0:
            self._timeout_minutes = total
        return self

    # -- Internal ----------------------------------------------------------

    def _to_node(self, node_id: str) -> _Node:
        data = {
            "integration": self._action._integration,
            "action": self._action._action,
            "config": dict(self._action._config),
            "condition": self._condition._condition_payload(),
            "interval_seconds": self._interval_seconds,
            "timeout_minutes": self._timeout_minutes,
        }
        if self._label:
            data["label"] = self._label
        return _Node(id=node_id, type="loop", data=data)


class ForEach:
    """Builds a "For Each" fan-out node.

    The node resolves a list from an upstream step's output at runtime and
    executes ONE embedded catalog action per element, sequentially. Inside the
    embedded action's config, ``{{item}}`` is the current element,
    ``{{item.<field>}}`` reads a field of an object element, and
    ``{{item_index}}`` is the zero-based index::

        fan_out = (
            ForEach(
                "{{step_outputs.action-2.outputs.new_findings}}",
                Action.jira_create_ticket()
                .project("SEC")
                .title("[Audit] {{item.title}}")
                .body("{{item.description}}"),
            )
            .max_items(50)
            .continue_on_error()
            .label("Create ticket per finding")
        )

        wf.then(fan_out).then(...)  # successors run after ALL items

    The node emits one aggregated output with ``items_total``,
    ``items_processed``, ``succeeded``, ``failed``, per-item ``results``, and
    a flat ``summary`` string.
    """

    def __init__(self, items: str, action: Action) -> None:
        self._items_path = items
        self._action = action
        self._max_items = 0  # 0 => server default (25)
        self._continue_on_error = False
        self._label: str = ""

    def label(self, text: str) -> ForEach:
        self._label = text
        return self

    def max_items(self, n: int) -> ForEach:
        """Cap the number of items processed (server default 25, hard cap 100)."""
        if n > 0:
            self._max_items = n
        return self

    def continue_on_error(self, enabled: bool = True) -> ForEach:
        """Keep processing remaining items when one fails (default off)."""
        self._continue_on_error = enabled
        return self

    # -- Internal ----------------------------------------------------------

    def _to_node(self, node_id: str) -> _Node:
        data = {
            "integration": self._action._integration,
            "action": self._action._action,
            "config": dict(self._action._config),
            "items_path": self._items_path,
        }
        if self._max_items:
            data["max_items"] = self._max_items
        if self._continue_on_error:
            data["continue_on_error"] = True
        if self._label:
            data["label"] = self._label
        return _Node(id=node_id, type="for_each", data=data)
