"""Approval gate builder for workflow definitions."""

from __future__ import annotations

from typing import Any

from .types import _Node


class Approval:
    """Builds an approval gate node that pauses the workflow until approved.

    Use the static factory methods to create the desired approval type::

        gate = Approval.slack("#approvals").message("Deploy to prod?")
    """

    def __init__(self, approval_type: str, *, refine: bool = False) -> None:
        self._approval_type = approval_type
        self._config: dict[str, Any] = {}
        self._label: str = ""
        self._refine = refine
        self._max_rounds: int | None = None

    def label(self, text: str) -> Approval:
        self._label = text
        return self

    def message(self, template: str) -> Approval:
        self._config["message_template"] = template
        return self

    def channel(self, ch: str) -> Approval:
        self._config["channel"] = ch
        return self

    def max_rounds(self, n: int) -> Approval:
        """For refine gates: cap how many times changes can be requested before
        the loop advances on the approved branch. Defaults to 5."""
        self._max_rounds = n
        return self

    def rules(self, *groups: list[dict[str, str]]) -> Approval:
        """Set approval rules.  Each group is a list of ``{"type": "user"|"group", "id": "..."}``
        entries.  OR across groups, AND within a group."""
        self._config["approval_rules"] = [{"entries": g} for g in groups]
        return self

    # -- Factory methods ---------------------------------------------------

    @staticmethod
    def manual() -> Approval:
        return Approval("manual")

    @staticmethod
    def slack(channel: str) -> Approval:
        a = Approval("slack")
        a._config["channel"] = channel
        return a

    @staticmethod
    def pr_approval() -> Approval:
        return Approval("pr_approval")

    @staticmethod
    def pr_merge() -> Approval:
        return Approval("pr_merge")

    @staticmethod
    def refine(channel_type: str = "manual") -> Approval:
        """Self-looping RCA refinement gate (Option C1).

        Presents the upstream RCA + fixes for approval. When the approver
        requests changes with free-text guidance, the upstream RCA agent
        re-runs with that feedback (accumulated across rounds) and re-requests
        approval on the SAME node — looping until approved/rejected or until
        ``max_rounds`` is reached. Requires an upstream ``kestrel.trigger_rca``
        or ``kestrel.trigger_cloud_rca`` step.

        ``channel_type`` selects where the approval is requested
        (``"manual"`` for the Kestrel UI, ``"slack"`` for Slack)::

            gate = Approval.refine().max_rounds(3)
        """
        return Approval(channel_type, refine=True)

    # -- Internal ----------------------------------------------------------

    def _to_node(self, node_id: str) -> _Node:
        data: dict[str, Any] = {
            "approval_type": self._approval_type,
            "config": self._config,
        }
        if self._label:
            data["label"] = self._label
        if self._refine:
            data["action"] = "approval-refine-rca"
            data["max_rounds"] = self._max_rounds if self._max_rounds is not None else 5
            return _Node(id=node_id, type="refine_approval", data=data)
        return _Node(id=node_id, type="approval", data=data)
