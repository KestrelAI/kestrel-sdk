"""Condition builder for workflow definitions."""

from __future__ import annotations

from .types import _Node


class Condition:
    """Builds a condition node that branches the workflow based on a runtime value.

    Use the static factory methods to create a condition with the desired
    operator::

        cond = Condition.equals("rca_result.is_application_level_failure", "true")

    The value-comparing factories also accept multiple candidate values.
    ``equals``/``contains`` are met when ANY value matches;
    ``not_equals``/``not_contains`` are met only when NONE match::

        cond = Condition.equals("sandbox_state", "stopped", "error")
    """

    def __init__(
        self,
        field: str,
        operator: str,
        value: str = "",
        values: list[str] | None = None,
    ) -> None:
        self._field = field
        self._operator = operator
        self._value = value
        self._values = list(values) if values else []
        self._label: str = ""

    def label(self, text: str) -> Condition:
        self._label = text
        return self

    # -- Factory methods ---------------------------------------------------

    @staticmethod
    def _make(field: str, operator: str, value: str, more: tuple[str, ...]) -> Condition:
        if more:
            return Condition(field, operator, values=[value, *more])
        return Condition(field, operator, value)

    @staticmethod
    def equals(field: str, value: str, *more: str) -> Condition:
        """Met when the field equals the value (or ANY value when several are given)."""
        return Condition._make(field, "equals", value, more)

    @staticmethod
    def not_equals(field: str, value: str, *more: str) -> Condition:
        """Met when the field equals NONE of the given values."""
        return Condition._make(field, "not_equals", value, more)

    @staticmethod
    def contains(field: str, value: str, *more: str) -> Condition:
        """Met when the field contains the value (or ANY value when several are given)."""
        return Condition._make(field, "contains", value, more)

    @staticmethod
    def not_contains(field: str, value: str, *more: str) -> Condition:
        """Met when the field contains NONE of the given values."""
        return Condition._make(field, "not_contains", value, more)

    @staticmethod
    def exists(field: str) -> Condition:
        return Condition(field, "exists")

    @staticmethod
    def not_exists(field: str) -> Condition:
        return Condition(field, "not_exists")

    # -- Internal ----------------------------------------------------------

    def _condition_payload(self) -> dict:
        data = {
            "field": self._field,
            "operator": self._operator,
            "value": self._value,
        }
        if self._values:
            data["values"] = list(self._values)
        return data

    def _to_node(self, node_id: str) -> _Node:
        data = self._condition_payload()
        if self._label:
            data["label"] = self._label
        return _Node(id=node_id, type="condition", data=data)
