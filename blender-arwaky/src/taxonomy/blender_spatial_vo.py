from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# ============================================================
# SPATIAL VALUE OBJECTS
# ============================================================


@dataclass(frozen=True)
class Vector3D:
    """Immutable 3D vector with arithmetic and coordinate helpers."""

    x: float
    y: float
    z: float

    def __post_init__(self) -> None:
        if not all(isinstance(v, (int, float)) for v in (self.x, self.y, self.z)):
            raise TypeError("Vector3D coordinates must be numeric")

    def __add__(self, other: Vector3D) -> Vector3D:
        return Vector3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Vector3D) -> Vector3D:
        return Vector3D(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> Vector3D:
        return Vector3D(self.x * scalar, self.y * scalar, self.z * scalar)

    def __truediv__(self, scalar: float) -> Vector3D:
        if scalar == 0:
            raise ZeroDivisionError("Cannot divide Vector3D by zero")
        return Vector3D(self.x / scalar, self.y / scalar, self.z / scalar)

    def magnitude(self) -> float:
        """Euclidean length from origin."""
        return float((self.x**2 + self.y**2 + self.z**2) ** 0.5)

    def as_dict(self) -> dict[str, float]:
        return {"x": self.x, "y": self.y, "z": self.z}

    @staticmethod
    def from_list(vals: list[float]) -> Vector3D:
        if len(vals) != 3:
            raise ValueError(f"Expected 3 values for Vector3D, got {len(vals)}")
        return Vector3D(float(vals[0]), float(vals[1]), float(vals[2]))


@dataclass(frozen=True)
class BoundingBox:
    """Axis-aligned bounding box defined by min and max corners."""

    min: Vector3D
    max: Vector3D

    def __post_init__(self) -> None:
        for coord in ("x", "y", "z"):
            min_val = getattr(self.min, coord)
            max_val = getattr(self.max, coord)
            if min_val > max_val:
                raise ValueError(f"BoundingBox min.{coord} ({min_val}) cannot exceed max.{coord} ({max_val})")

    def dimensions(self) -> Vector3D:
        return Vector3D(
            self.max.x - self.min.x,
            self.max.y - self.min.y,
            self.max.z - self.min.z,
        )

    def expand(self, point: Vector3D) -> BoundingBox:
        new_min = Vector3D(
            min(self.min.x, point.x),
            min(self.min.y, point.y),
            min(self.min.z, point.z),
        )
        new_max = Vector3D(
            max(self.max.x, point.x),
            max(self.max.y, point.y),
            max(self.max.z, point.z),
        )
        return BoundingBox(new_min, new_max)

    def merge(self, other: BoundingBox) -> BoundingBox:
        new_min = Vector3D(
            min(self.min.x, other.min.x),
            min(self.min.y, other.min.y),
            min(self.min.z, other.min.z),
        )
        new_max = Vector3D(
            max(self.max.x, other.max.x),
            max(self.max.y, other.max.y),
            max(self.max.z, other.max.z),
        )
        return BoundingBox(new_min, new_max)

    def contains(self, point: Vector3D) -> bool:
        return (
            self.min.x <= point.x <= self.max.x
            and self.min.y <= point.y <= self.max.y
            and self.min.z <= point.z <= self.max.z
        )

    def volume(self) -> float:
        return (self.max.x - self.min.x) * (self.max.y - self.min.y) * (self.max.z - self.min.z)

    def to_dict(self) -> dict[str, Any]:
        return {"min": self.min.as_dict(), "max": self.max.as_dict()}

    @staticmethod
    def from_dict(data: dict[str, Any]) -> BoundingBox:
        return BoundingBox(
            Vector3D(data["min"]["x"], data["min"]["y"], data["min"]["z"]),
            Vector3D(data["max"]["x"], data["max"]["y"], data["max"]["z"]),
        )


def create_float_triplet(vals: list[float]) -> Vector3D:
    """Factory helper to create a Vector3D from a list of floats."""
    if len(vals) != 3:
        raise ValueError(f"Expected 3 values, got {len(vals)}")
    return Vector3D(float(vals[0]), float(vals[1]), float(vals[2]))
