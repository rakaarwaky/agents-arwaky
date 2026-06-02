"""
Contract: Object Operations Contract (ABC based).
"""

from abc import ABC, abstractmethod

from taxonomy import (
    ApplyModifierRequestVO,
    ApplyModifierResponseVO,
    CreatePrimitiveRequestVO,
    CreatePrimitiveResponseVO,
    DeleteObjectRequestVO,
    DeleteObjectResponseVO,
    GetObjectInfoRequestVO,
    GetObjectInfoResponseVO,
    PlaceAssetRequestVO,
    PlaceAssetResponseVO,
    SetMaterialRequestVO,
    SetMaterialResponseVO,
    SetObjectTransformRequestVO,
    SetObjectTransformResponseVO,
)


class ObjectOperateProtocol(ABC):
    """Interface for object-level manipulation in Blender."""

    @abstractmethod
    async def place_asset(self, request: PlaceAssetRequestVO) -> PlaceAssetResponseVO:
        """Position and scale an imported asset."""
        pass

    @abstractmethod
    async def get_object_info(self, request: GetObjectInfoRequestVO) -> GetObjectInfoResponseVO:
        """Get properties of a specific object."""
        pass

    @abstractmethod
    async def set_object_transform(self, request: SetObjectTransformRequestVO) -> SetObjectTransformResponseVO:
        """Modify location, rotation, or scale."""
        pass

    @abstractmethod
    async def delete_object(self, request: DeleteObjectRequestVO) -> DeleteObjectResponseVO:
        """Remove object by name."""
        pass

    @abstractmethod
    async def create_primitive(self, request: CreatePrimitiveRequestVO) -> CreatePrimitiveResponseVO:
        """Spawn a basic mesh primitive."""
        pass

    @abstractmethod
    async def set_material(self, request: SetMaterialRequestVO) -> SetMaterialResponseVO:
        """Assign material to object."""
        pass

    @abstractmethod
    async def apply_modifier(self, request: ApplyModifierRequestVO) -> ApplyModifierResponseVO:
        """Apply mesh modifier permanently."""
        pass
