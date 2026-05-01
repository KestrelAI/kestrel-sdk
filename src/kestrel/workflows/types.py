"""Internal types used by the workflow builder."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class _Node:
    """Internal representation of a workflow graph node."""

    id: str
    type: str  # trigger, action, condition, approval
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "type": self.type, "data": self.data}


@dataclass
class _Edge:
    """Internal representation of a workflow graph edge."""

    id: str
    source: str
    target: str
    label: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"id": self.id, "source": self.source, "target": self.target}
        if self.label:
            d["label"] = self.label
        return d
