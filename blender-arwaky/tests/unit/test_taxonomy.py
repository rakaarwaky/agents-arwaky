"""Unit tests for the taxonomy layer (Value Objects, Entities, Errors)."""
import pytest
from uuid import uuid4
from taxonomy.blender_spatial_vo import Vector3D, BoundingBox, create_float_triplet
from taxonomy.blender_job_vo import (
    JobStatus,
    JOB_STATE_PENDING,
    JOB_STATE_RUNNING,
    JOB_STATE_COMPLETED,
    JOB_STATE_FAILED,
    create_job_id,
    create_progress,
)
from taxonomy.blender_mcp_error import (
    BlenderMCPError,
    DomainError,
    SceneValidationError,
    AssetNotFoundError,
    ValidationError,
    ConnectionError,
    ProviderError,
    ExecutionError,
    BlenderConnectionError,
    InvalidCommandError,
)
from taxonomy.blender_object_entity import (
    BlenderObject,
    OBJECT_TYPE_MESH,
    OBJECT_TYPE_CAMERA,
    create_object_id,
)
from taxonomy.blender_scene_entity import SceneAggregate, SceneInfo
from taxonomy.core_types_vo import (
    ObjectName,
    ObjectType,
    ObjectId,
    JobId,
    ErrorMessage,
    Progress,
    ResultUrl,
    AssetId,
    ProviderName,
)


class TestVector3D:
    """Tests for Vector3D value object."""

    def test_vector_creation(self):
        v = Vector3D(1.0, 2.0, 3.0)
        assert v.x == 1.0
        assert v.y == 2.0
        assert v.z == 3.0

    def test_vector_creation_non_numeric(self):
        with pytest.raises(TypeError):
            Vector3D("1.0", 2.0, 3.0)  # type: ignore

    def test_vector_arithmetic(self):
        v1 = Vector3D(1.0, 2.0, 3.0)
        v2 = Vector3D(4.0, 5.0, 6.0)

        # Add
        assert v1 + v2 == Vector3D(5.0, 7.0, 9.0)

        # Subtract
        assert v1 - v2 == Vector3D(-3.0, -3.0, -3.0)

        # Multiply scalar
        assert v1 * 2.0 == Vector3D(2.0, 4.0, 6.0)

        # Divide scalar
        assert v1 / 2.0 == Vector3D(0.5, 1.0, 1.5)

    def test_vector_division_by_zero(self):
        v = Vector3D(1.0, 2.0, 3.0)
        with pytest.raises(ZeroDivisionError):
            v / 0.0

    def test_vector_magnitude(self):
        v = Vector3D(3.0, 4.0, 0.0)
        assert v.magnitude() == 5.0

    def test_vector_as_dict(self):
        v = Vector3D(1.0, 2.0, 3.0)
        assert v.as_dict() == {"x": 1.0, "y": 2.0, "z": 3.0}

    def test_vector_from_list(self):
        v = Vector3D.from_list([1.0, 2.0, 3.0])
        assert v == Vector3D(1.0, 2.0, 3.0)

        with pytest.raises(ValueError):
            Vector3D.from_list([1.0, 2.0])

    def test_create_float_triplet(self):
        v = create_float_triplet([1.0, 2.0, 3.0])
        assert v == Vector3D(1.0, 2.0, 3.0)

        with pytest.raises(ValueError):
            create_float_triplet([1.0, 2.0])


class TestBoundingBox:
    """Tests for BoundingBox value object."""

    def test_bounding_box_creation(self):
        b = BoundingBox(Vector3D(0, 0, 0), Vector3D(1, 1, 1))
        assert b.min == Vector3D(0, 0, 0)
        assert b.max == Vector3D(1, 1, 1)

    def test_bounding_box_invalid(self):
        with pytest.raises(ValueError):
            BoundingBox(Vector3D(1, 0, 0), Vector3D(0, 1, 1))

    def test_bounding_box_dimensions(self):
        b = BoundingBox(Vector3D(0, 1, 2), Vector3D(3, 5, 8))
        assert b.dimensions() == Vector3D(3, 4, 6)

    def test_bounding_box_expand(self):
        b = BoundingBox(Vector3D(0, 0, 0), Vector3D(1, 1, 1))
        b2 = b.expand(Vector3D(-1, 2, 0.5))
        assert b2.min == Vector3D(-1, 0, 0)
        assert b2.max == Vector3D(1, 2, 1)

    def test_bounding_box_merge(self):
        b1 = BoundingBox(Vector3D(0, 0, 0), Vector3D(1, 1, 1))
        b2 = BoundingBox(Vector3D(-1, -1, -1), Vector3D(0.5, 0.5, 0.5))
        merged = b1.merge(b2)
        assert merged.min == Vector3D(-1, -1, -1)
        assert merged.max == Vector3D(1, 1, 1)

    def test_bounding_box_contains(self):
        b = BoundingBox(Vector3D(0, 0, 0), Vector3D(2, 2, 2))
        assert b.contains(Vector3D(1, 1, 1)) is True
        assert b.contains(Vector3D(3, 1, 1)) is False

    def test_bounding_box_volume(self):
        b = BoundingBox(Vector3D(0, 0, 0), Vector3D(2, 3, 4))
        assert b.volume() == 24.0

    def test_bounding_box_dict(self):
        b = BoundingBox(Vector3D(0, 0, 0), Vector3D(1, 1, 1))
        data = b.to_dict()
        assert data == {
            "min": {"x": 0.0, "y": 0.0, "z": 0.0},
            "max": {"x": 1.0, "y": 1.0, "z": 1.0},
        }
        b2 = BoundingBox.from_dict(data)
        assert b == b2


class TestJobStatusAndFactories:
    """Tests for JobStatus and associated factories."""

    def test_job_status_lifecycle(self):
        jid = create_job_id("job-123")
        assert jid == "job-123"

        status = JobStatus(job_id=jid, status=JOB_STATE_PENDING)
        assert status.status == JOB_STATE_PENDING
        assert status.progress == 0.0

        status.mark_running()
        assert status.status == JOB_STATE_RUNNING
        assert status.progress == 0.0

        url = ResultUrl("http://example.com/asset.glb")
        status.mark_completed(url)
        assert status.status == JOB_STATE_COMPLETED
        assert status.progress == 100.0
        assert status.result_url == url

        status.mark_failed(ErrorMessage("Failed to render"))
        assert status.status == JOB_STATE_FAILED
        assert status.error == "Failed to render"

    def test_create_progress_validation(self):
        p = create_progress(50.0)
        assert p == 50.0

        with pytest.raises(ValueError):
            create_progress(-1.0)

        with pytest.raises(ValueError):
            create_progress(101.0)


class TestBlenderMCPError:
    """Tests for custom Exception classes."""

    def test_base_error_format(self):
        err = BlenderMCPError(ErrorMessage("Something failed"), {"reason": "timeout"})
        assert str(err) == "Something failed"
        assert err.details == {"reason": "timeout"}

        mcp_fmt = err.to_mcp_format()
        assert mcp_fmt["code"] == "BlenderMCPError"
        assert mcp_fmt["message"] == "Something failed"
        assert mcp_fmt["details"] == {"reason": "timeout"}

    def test_all_subclass_exceptions(self):
        # Verify base instantiations with defaults
        assert str(DomainError()) == "Domain error"
        assert str(SceneValidationError()) == "Scene validation failed"
        assert str(ValidationError()) == "Input validation failed"
        assert str(ConnectionError()) == "Connection failed"
        assert str(ProviderError()) == "Provider error"
        assert str(ExecutionError()) == "Execution failed"
        assert str(BlenderConnectionError()) == "Blender connection lost"
        assert str(InvalidCommandError()) == "Invalid command"

        # AssetNotFoundError specific test
        aid = AssetId("asset-999")
        pname = ProviderName("sketchfab")
        err = AssetNotFoundError(aid, pname)
        assert "asset-999" in str(err)
        assert "sketchfab" in str(err)
        assert err.asset_id == aid
        assert err.provider == pname


class TestBlenderObjectEntity:
    """Tests for BlenderObject entity."""

    def test_blender_object_creation(self):
        uid = uuid4()
        obj = BlenderObject(
            name=ObjectName("Cube"),
            type=OBJECT_TYPE_MESH,
            location=Vector3D(0, 0, 0),
            rotation=Vector3D(0, 0, 0),
            scale=Vector3D(1, 1, 1),
            id=create_object_id(uid),
        )
        assert obj.name == "Cube"
        assert obj.type == "MESH"
        assert obj.id == uid

    def test_blender_object_invalid_inputs(self):
        with pytest.raises(ValueError):
            BlenderObject(ObjectName(""), OBJECT_TYPE_MESH, Vector3D(0,0,0), Vector3D(0,0,0), Vector3D(1,1,1))

        with pytest.raises(ValueError):
            BlenderObject(ObjectName("Cube"), ObjectType(""), Vector3D(0,0,0), Vector3D(0,0,0), Vector3D(1,1,1))

        with pytest.raises(TypeError):
            BlenderObject(ObjectName("Cube"), OBJECT_TYPE_MESH, [0,0,0], Vector3D(0,0,0), Vector3D(1,1,1))  # type: ignore

        with pytest.raises(TypeError):
            BlenderObject(ObjectName("Cube"), OBJECT_TYPE_MESH, Vector3D(0,0,0), [0,0,0], Vector3D(1,1,1))  # type: ignore

        with pytest.raises(TypeError):
            BlenderObject(ObjectName("Cube"), OBJECT_TYPE_MESH, Vector3D(0,0,0), Vector3D(0,0,0), [1,1,1])  # type: ignore

        with pytest.raises(ValueError):
            BlenderObject(ObjectName("Cube"), ObjectType("INVALID_TYPE"), Vector3D(0,0,0), Vector3D(0,0,0), Vector3D(1,1,1))

    def test_transformations(self):
        obj = BlenderObject(
            name=ObjectName("Cube"),
            type=OBJECT_TYPE_MESH,
            location=Vector3D(0, 0, 0),
            rotation=Vector3D(0, 0, 0),
            scale=Vector3D(1, 1, 1),
        )

        obj.translate(Vector3D(1, 2, 3))
        assert obj.location == Vector3D(1, 2, 3)

        obj.rotate(Vector3D(0, 90, 0))
        assert obj.rotation == Vector3D(0, 90, 0)

        obj.resize(2.0, 3.0, 0.5)
        assert obj.scale == Vector3D(2.0, 3.0, 0.5)

    def test_hierarchy(self):
        obj = BlenderObject(ObjectName("Child"), OBJECT_TYPE_MESH, Vector3D(0,0,0), Vector3D(0,0,0), Vector3D(1,1,1))
        pid = uuid4()
        obj.parent_to(pid)
        assert obj.parent_id == pid

        with pytest.raises(ValueError):
            obj.parent_to(obj.id)

        obj.parent_to(None)
        assert obj.parent_id is None

        cid1 = uuid4()
        cid2 = uuid4()
        obj.add_child(cid1)
        obj.add_child(cid2)
        obj.add_child(cid1)  # duplicate check
        assert len(obj.children_ids) == 2
        assert cid1 in obj.children_ids

        obj.remove_child(cid1)
        assert len(obj.children_ids) == 1
        assert cid1 not in obj.children_ids


class TestSceneAggregate:
    """Tests for SceneAggregate root."""

    def test_add_and_get_objects(self):
        scene = SceneAggregate()
        obj = BlenderObject(ObjectName("Sphere"), OBJECT_TYPE_MESH, Vector3D(0,0,0), Vector3D(0,0,0), Vector3D(1,1,1))
        scene.add_object(obj)

        assert scene.get_object(obj.id) is obj
        assert scene.get_object_by_name(ObjectName("Sphere")) is obj
        assert scene.get_object_by_name(ObjectName("Nonexistent")) is None
        assert len(scene.list_objects()) == 1

    def test_add_duplicate_name_fails(self):
        scene = SceneAggregate()
        obj1 = BlenderObject(ObjectName("Sphere"), OBJECT_TYPE_MESH, Vector3D(0,0,0), Vector3D(0,0,0), Vector3D(1,1,1))
        obj2 = BlenderObject(ObjectName("Sphere"), OBJECT_TYPE_CAMERA, Vector3D(1,1,1), Vector3D(0,0,0), Vector3D(1,1,1))

        scene.add_object(obj1)
        with pytest.raises(SceneValidationError):
            scene.add_object(obj2)

    def test_remove_object_cascade(self):
        scene = SceneAggregate()
        parent = BlenderObject(ObjectName("Parent"), OBJECT_TYPE_MESH, Vector3D(0,0,0), Vector3D(0,0,0), Vector3D(1,1,1))
        child = BlenderObject(ObjectName("Child"), OBJECT_TYPE_MESH, Vector3D(0,0,0), Vector3D(0,0,0), Vector3D(1,1,1))

        scene.add_object(parent)
        scene.add_object(child)

        child.parent_to(parent.id)
        parent.add_child(child.id)

        # Cascade remove child when removing parent
        scene.remove_object(parent.id)
        assert len(scene.list_objects()) == 0

    def test_remove_object_updates_other_parents(self):
        scene = SceneAggregate()
        parent = BlenderObject(ObjectName("Parent"), OBJECT_TYPE_MESH, Vector3D(0,0,0), Vector3D(0,0,0), Vector3D(1,1,1))
        child = BlenderObject(ObjectName("Child"), OBJECT_TYPE_MESH, Vector3D(0,0,0), Vector3D(0,0,0), Vector3D(1,1,1))

        scene.add_object(parent)
        scene.add_object(child)
        child.parent_to(parent.id)

        # If we remove parent, child remains but parent_id becomes None
        # In SceneAggregate's remove_object, it recursively removes children (obj.children_ids),
        # but if we didn't add child to parent.children_ids, the cascade doesn't happen.
        # Instead, it cleans parent_id of orphans.
        scene.remove_object(parent.id)
        assert len(scene.list_objects()) == 1
        assert child.parent_id is None

    def test_update_object(self):
        scene = SceneAggregate()
        obj1 = BlenderObject(ObjectName("Obj1"), OBJECT_TYPE_MESH, Vector3D(0,0,0), Vector3D(0,0,0), Vector3D(1,1,1))
        obj2 = BlenderObject(ObjectName("Obj2"), OBJECT_TYPE_MESH, Vector3D(0,0,0), Vector3D(0,0,0), Vector3D(1,1,1))
        scene.add_object(obj1)
        scene.add_object(obj2)

        # Simple update
        scene.update_object(obj1.id, location=Vector3D(10, 10, 10))
        assert obj1.location == Vector3D(10, 10, 10)

        # Name update (allowed)
        scene.update_object(obj1.id, name="NewName")
        assert obj1.name == "NewName"
        assert scene.get_object_by_name(ObjectName("NewName")) is obj1

        # Name update (duplicate - forbidden)
        with pytest.raises(SceneValidationError):
            scene.update_object(obj1.id, name="Obj2")

    def test_get_bounds(self):
        scene = SceneAggregate()
        # Empty aggregate
        assert scene.get_bounds() == BoundingBox(Vector3D(0,0,0), Vector3D(0,0,0))

        # No meshes (only camera)
        cam = BlenderObject(ObjectName("Cam"), OBJECT_TYPE_CAMERA, Vector3D(1, 2, 3), Vector3D(0,0,0), Vector3D(1,1,1))
        scene.add_object(cam)
        assert scene.get_bounds() == BoundingBox(Vector3D(0,0,0), Vector3D(0,0,0))

        # With mesh
        mesh = BlenderObject(ObjectName("Mesh"), OBJECT_TYPE_MESH, Vector3D(0, 0, 0), Vector3D(0,0,0), Vector3D(2, 2, 2))
        scene.add_object(mesh)
        assert scene.get_bounds() == BoundingBox(Vector3D(-1, -1, -1), Vector3D(1, 1, 1))

        # Multiple meshes
        mesh2 = BlenderObject(ObjectName("Mesh2"), OBJECT_TYPE_MESH, Vector3D(3, 4, 5), Vector3D(0,0,0), Vector3D(2, 2, 2))
        scene.add_object(mesh2)
        assert scene.get_bounds() == BoundingBox(Vector3D(-1, -1, -1), Vector3D(4, 5, 6))

    def test_validate_parentage(self):
        scene = SceneAggregate()
        obj1 = BlenderObject(ObjectName("O1"), OBJECT_TYPE_MESH, Vector3D(0,0,0), Vector3D(0,0,0), Vector3D(1,1,1))
        obj2 = BlenderObject(ObjectName("O2"), OBJECT_TYPE_MESH, Vector3D(0,0,0), Vector3D(0,0,0), Vector3D(1,1,1))
        scene.add_object(obj1)
        scene.add_object(obj2)

        # Valid parentage
        obj1.parent_to(obj2.id)
        scene.validate_parentage()

        # Non-existent parent
        obj1.parent_to(uuid4())
        with pytest.raises(SceneValidationError):
            scene.validate_parentage()

        # Parent to self
        obj1.parent_id = obj1.id
        with pytest.raises(SceneValidationError):
            scene.validate_parentage()

        # Cyclic parentage
        obj1.parent_to(obj2.id)
        obj2.parent_to(obj1.id)
        with pytest.raises(SceneValidationError):
            scene.validate_parentage()

    def test_scene_info_snapshot(self):
        obj = BlenderObject(ObjectName("Obj"), OBJECT_TYPE_MESH, Vector3D(0,0,0), Vector3D(0,0,0), Vector3D(1,1,1))
        info = SceneInfo(objects=[obj], active_object_id=obj.id)
        assert info.active_object_id == obj.id
        assert len(info.objects) == 1
