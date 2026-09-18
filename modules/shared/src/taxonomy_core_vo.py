"""Core value objects shared across the AES tool domains."""
from __future__ import annotations


class Timestamp:
    """Frozen float timestamp VO (e.g. install/update stamps)."""

    __slots__ = ("_value",)

    def __init__(self, value: float) -> None:
        if not isinstance(value, float):
            value = float(value)
        object.__setattr__(self, "_value", value)

    @property
    def value(self) -> float:
        return self._value

    def __str__(self) -> str:
        return str(self._value)

    def __repr__(self) -> str:
        return f"Timestamp({self._value!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Timestamp):
            return self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._value)


class ToolId:
    """Frozen string tool identifier VO (manifest `id`)."""

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        value = str(value)
        if not value:
            raise ValueError("ToolId must not be empty")
        object.__setattr__(self, "_value", value)

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"ToolId({self._value!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ToolId):
            return self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._value)
