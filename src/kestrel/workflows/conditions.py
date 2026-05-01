"""Condition builder for workflow definitions."""

from __future__ import annotations

from .types import _Node


class Condition:
    """Builds a condition node that branches the workflow based on a runtime value.

    Use the static factory methods to create a condition with the desired
    operator::

        cond = Condition.equals("rca_result.is_application_level_failure", "true")
    """

    def __init__(self, field: str, operator: str, value: str = "") -> None:
        self._field = field
        self._operator = operator
        self._value = value
        self._label: str = ""

    def label(self, text: str) -> Condition:
        self._label = text
        return self

    # -- Factory methods ---------------------------------------------------

    @staticmethod
    def equals(field: str, value: str) -> Condition:
        return Condition(field, "equals", value)

    @staticmethod
    def not_equals(field: str, value: str) -> Condition:
        return Condition(field, "not_equals", value)

    @staticmethod
    def contains(field: str, value: str) -> Condition:
        return Condition(field, "contains", value)

    @staticmethod
    def not_contains(field: str, value: str) -> Condition:
        return Condition(field, "not_contains", value)

    @staticmethod
    def exists(field: str) -> Condition:
        return Condition(field, "exists")

    @staticmethod
    def not_exists(field: str) -> Condition:
        return Condition(field, "not_exists")

    # -- Internal ----------------------------------------------------------

    def _to_node(self, node_id: str) -> _Node:
        data = {
            "field": self._field,
            "operator": self._operator,
            "value": self._value,
        }
        if self._label:
            data["label"] = self._label
        return _Node(id=node_id, type="condition", data=data)
