"""Approval gate builder for workflow definitions."""

from __future__ import annotations

from typing import Any

from .types import _Node


class Approval:
    """Builds an approval gate node that pauses the workflow until approved.

    Use the static factory methods to create the desired approval type::

        gate = Approval.slack("#approvals").message("Deploy to prod?")
    """

    def __init__(self, approval_type: str) -> None:
        self._approval_type = approval_type
        self._config: dict[str, Any] = {}
        self._label: str = ""

    def label(self, text: str) -> Approval:
        self._label = text
        return self

    def message(self, template: str) -> Approval:
        self._config["message_template"] = template
        return self

    def channel(self, ch: str) -> Approval:
        self._config["channel"] = ch
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

    # -- Internal ----------------------------------------------------------

    def _to_node(self, node_id: str) -> _Node:
        data: dict[str, Any] = {
            "approval_type": self._approval_type,
            "config": self._config,
        }
        if self._label:
            data["label"] = self._label
        return _Node(id=node_id, type="approval", data=data)
