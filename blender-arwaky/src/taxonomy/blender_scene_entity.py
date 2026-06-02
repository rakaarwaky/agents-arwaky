from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Final
from uuid import UUID

from .blender_mcp_error import SceneValidationError
from .blender_object_entity import BlenderObject
from .blender_spatial_vo import BoundingBox, Vector3D
from .core_types_vo import BlenderObjectList, ErrorMessage, ObjectId, ObjectName, RenderEngine

# ============================================================
# SCENE CONSTANTS
# ============================================================

RENDER_ENGINE_CYCLES: Final[RenderEngine] = RenderEngine("CYCLES")
RENDER_ENGINE_EEVEE: Final[RenderEngine] = RenderEngine("EEVEE")


# ============================================================
# READ MODEL: SceneInfo
# ============================================================


@dataclass
class SceneInfo:
    """Snapshot of the entire scene for external consumption."""

    objects: BlenderObjectList
    active_object_id: ObjectId | None = None
    render_engine: RenderEngine = RENDER_ENGINE_CYCLES
    resolution: Vector3D = field(default_factory=lambda: Vector3D(1920, 1080, 1))


# ============================================================
# AGGREGATE ROOT: SceneAggregate
# ============================================================


class SceneAggregate:
    """
    AGGREGATE ROOT: Manages a collection of BlenderObjects as a consistency boundary.
    Ensures no duplicate names, maintains parent-child consistency, and provides
    aggregate-level queries (bounds).
    """

    def __init__(self) -> None:
        self._objects: dict[UUID, BlenderObject] = {}
        self._name_index: dict[str, UUID] = {}

    def add_object(self, obj: BlenderObject) -> None:
        """Add an object to the scene, enforcing unique names."""
        if obj.name in self._name_index:
            raise SceneValidationError(ErrorMessage(f"Duplicate object name: {obj.name}"))

        self._objects[obj.id] = obj
        self._name_index[obj.name] = obj.id

    def remove_object(self, obj_id: UUID) -> None:
        """Remove an object and all its descendants (cascade)."""
        obj = self._find(obj_id)

        # Recursively remove children first
        for child_id in list(obj.children_ids):
            self.remove_object(child_id)

        # Remove from indexes
        del self._objects[obj_id]
        del self._name_index[obj.name]

        # Update any parent references
        for other in self._objects.values():
            if other.parent_id == obj_id:
                other.parent_id = None

    def update_object(self, obj_id: UUID, **changes: Any) -> BlenderObject:
        """
        Update an object's mutable fields.
        Name changes must preserve uniqueness.
        """
        obj = self._find(obj_id)

        if "name" in changes:
            new_name = changes["name"]
            if new_name != obj.name and new_name in self._name_index:
                raise SceneValidationError(ErrorMessage(f"Duplicate object name: {new_name}"))
            # Update name index
            del self._name_index[obj.name]
            self._name_index[new_name] = obj_id

        # Apply changes
        for key, value in changes.items():
            if hasattr(obj, key):
                setattr(obj, key, value)

        return obj

    def get_object(self, obj_id: UUID) -> BlenderObject:
        """Retrieve an object by ID."""
        return self._find(obj_id)

    def get_object_by_name(self, name: ObjectName) -> BlenderObject | None:
        """Retrieve an object by name, or None if not found."""
        obj_id = self._name_index.get(str(name))
        if obj_id is None:
            return None
        return self._objects[obj_id]

    def list_objects(self) -> list[BlenderObject]:
        """Return all objects in the scene."""
        return list(self._objects.values())

    def get_bounds(self) -> BoundingBox:
        """Calculate the aggregate bounding box of all mesh objects."""
        if not self._objects:
            return BoundingBox(Vector3D(0, 0, 0), Vector3D(0, 0, 0))

        mesh_objects = [obj for obj in self._objects.values() if obj.type == "MESH"]
        if not mesh_objects:
            return BoundingBox(Vector3D(0, 0, 0), Vector3D(0, 0, 0))

        first = mesh_objects[0]
        # Basic bounds estimation from location and scale (assuming cube primitives)
        min_pt = Vector3D(
            first.location.x - first.scale.x / 2,
            first.location.y - first.scale.y / 2,
            first.location.z - first.scale.z / 2,
        )
        max_pt = Vector3D(
            first.location.x + first.scale.x / 2,
            first.location.y + first.scale.y / 2,
            first.location.z + first.scale.z / 2,
        )

        for obj in mesh_objects[1:]:
            obj_min = Vector3D(
                obj.location.x - obj.scale.x / 2, obj.location.y - obj.scale.y / 2, obj.location.z - obj.scale.z / 2
            )
            obj_max = Vector3D(
                obj.location.x + obj.scale.x / 2, obj.location.y + obj.scale.y / 2, obj.location.z + obj.scale.z / 2
            )
            min_pt = Vector3D(min(min_pt.x, obj_min.x), min(min_pt.y, obj_min.y), min(min_pt.z, obj_min.z))
            max_pt = Vector3D(max(max_pt.x, obj_max.x), max(max_pt.y, obj_max.y), max(max_pt.z, obj_max.z))

        return BoundingBox(min_pt, max_pt)

    def validate_parentage(self) -> None:
        """Ensure all parent references point to existing objects and no cycles."""
        for obj in self._objects.values():
            if obj.parent_id is not None:
                if obj.parent_id not in self._objects:
                    raise SceneValidationError(
                        ErrorMessage(f"Object {obj.name} references non-existent parent {obj.parent_id}")
                    )
                if obj.parent_id == obj.id:
                    raise SceneValidationError(ErrorMessage(f"Object {obj.name} cannot parent to itself"))

        # Detect cycles
        visited: set[UUID] = set()
        for obj in self._objects.values():
            self._detect_cycle(obj, visited, set())

    def _detect_cycle(self, obj: BlenderObject, visited: set[UUID], stack: set[UUID]) -> None:
        if obj.id in stack:
            raise SceneValidationError(ErrorMessage(f"Parent cycle detected involving {obj.name}"))
        if obj.id in visited:
            return
        stack.add(obj.id)
        if obj.parent_id:
            parent = self._objects.get(obj.parent_id)
            if parent:
                self._detect_cycle(parent, visited, stack)
        stack.remove(obj.id)
        visited.add(obj.id)

    def _find(self, obj_id: UUID) -> BlenderObject:
        if obj_id not in self._objects:
            raise SceneValidationError(ErrorMessage(f"Object {obj_id} not found in scene"))
        return self._objects[obj_id]
