from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final
from uuid import UUID, uuid4

from .blender_spatial_vo import Vector3D
from .core_types_vo import ObjectId, ObjectIdList, ObjectName, ObjectType, ScaleFactor

# ============================================================
# OBJECT TYPE CONSTANTS
# ============================================================

OBJECT_TYPE_MESH: Final[ObjectType] = ObjectType("MESH")
OBJECT_TYPE_CAMERA: Final[ObjectType] = ObjectType("CAMERA")
OBJECT_TYPE_LIGHT: Final[ObjectType] = ObjectType("LIGHT")
OBJECT_TYPE_EMPTY: Final[ObjectType] = ObjectType("EMPTY")
OBJECT_TYPE_ARMATURE: Final[ObjectType] = ObjectType("ARMATURE")
OBJECT_TYPE_CURVE: Final[ObjectType] = ObjectType("CURVE")
OBJECT_TYPE_SURFACE: Final[ObjectType] = ObjectType("SURFACE")
OBJECT_TYPE_META: Final[ObjectType] = ObjectType("META")
OBJECT_TYPE_FONT: Final[ObjectType] = ObjectType("FONT")
OBJECT_TYPE_LATTICE: Final[ObjectType] = ObjectType("LATTICE")
OBJECT_TYPE_GPENCIL: Final[ObjectType] = ObjectType("GPENCIL")
OBJECT_TYPE_VOLUME: Final[ObjectType] = ObjectType("VOLUME")
OBJECT_TYPE_POINTCLOUD: Final[ObjectType] = ObjectType("POINTCLOUD")

ALLOWED_OBJECT_TYPES: Final[list[ObjectType]] = [
    OBJECT_TYPE_MESH,
    OBJECT_TYPE_CAMERA,
    OBJECT_TYPE_LIGHT,
    OBJECT_TYPE_EMPTY,
    OBJECT_TYPE_ARMATURE,
    OBJECT_TYPE_CURVE,
    OBJECT_TYPE_SURFACE,
    OBJECT_TYPE_META,
    OBJECT_TYPE_FONT,
    OBJECT_TYPE_LATTICE,
    OBJECT_TYPE_GPENCIL,
    OBJECT_TYPE_VOLUME,
    OBJECT_TYPE_POINTCLOUD,
]


@dataclass
class BlenderObject:
    """Domain entity representing a Blender object."""

    # Required fields (no defaults)
    name: ObjectName
    type: ObjectType  # Branded type for allowed Blender object types
    location: Vector3D
    rotation: Vector3D
    scale: Vector3D
    # Optional relationship fields (with defaults)
    parent_id: ObjectId | None = None
    children_ids: ObjectIdList = field(default_factory=lambda: ObjectIdList([]))
    # Identity (auto-generated if not provided)
    id: ObjectId = field(default_factory=lambda: ObjectId(uuid4()))

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Object name cannot be empty")
        if not self.type:
            raise ValueError("Object type cannot be empty")
        # Ensure vectors are proper types
        if not isinstance(self.location, Vector3D):
            raise TypeError("location must be Vector3D")
        if not isinstance(self.rotation, Vector3D):
            raise TypeError("rotation must be Vector3D")
        if not isinstance(self.scale, Vector3D):
            raise TypeError("scale must be Vector3D")
        # Validate object type
        self.validate_type(ALLOWED_OBJECT_TYPES)

    def validate_type(self, allowed: list[ObjectType]) -> None:
        """Enforce that object type is in allowed set."""
        if self.type not in allowed:
            raise ValueError(f"Invalid object type '{self.type}'. Allowed: {allowed}")

    def translate(self, delta: Vector3D) -> None:
        """Move the object by a delta vector."""
        self.location = self.location + delta

    def rotate(self, delta: Vector3D) -> None:
        """Add rotation offset (Euler angles)."""
        self.rotation = self.rotation + delta

    def resize(self, sx: ScaleFactor, sy: ScaleFactor, sz: ScaleFactor) -> None:
        """Scale the object multiplicatively with individual factors."""
        self.scale = Vector3D(self.scale.x * sx, self.scale.y * sy, self.scale.z * sz)

    def parent_to(self, new_parent_id: UUID | None) -> None:
        """Change parentage - used by aggregate to maintain consistency."""
        if new_parent_id == self.id:
            raise ValueError("Object cannot parent to itself")
        self.parent_id = ObjectId(new_parent_id) if new_parent_id else None

    def add_child(self, child_id: UUID) -> None:
        """Add a child reference - aggregate maintains this."""
        wrapped = ObjectId(child_id)
        if wrapped not in self.children_ids:
            self.children_ids.append(wrapped)

    def remove_child(self, child_id: UUID) -> None:
        """Remove a child reference - aggregate maintains this."""
        wrapped = ObjectId(child_id)
        if wrapped in self.children_ids:
            self.children_ids.remove(wrapped)


def create_object_id(raw: UUID) -> ObjectId:
    """Factory helper to create an ObjectId from a UUID."""
    return ObjectId(raw)
