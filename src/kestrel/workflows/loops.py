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
