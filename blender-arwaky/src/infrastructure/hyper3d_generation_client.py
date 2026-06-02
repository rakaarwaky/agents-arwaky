"""Hyper3D Rodin AI 3D generation tools"""

import base64
import json
import logging
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from contract import BlenderConnectionPort, Hyper3dToolPort
from taxonomy import (
    ActionName,
    BBoxIntegers,
    CoordinateList,
    JobId,
    JobState,
    ObjectName,
    Prompt,
    StatusString,
    StringList,
    TaskUuid,
)

logger = logging.getLogger("BlenderMCPServer")


class Hyper3dGenerationTool(Hyper3dToolPort):
    """Wrapper class for Hyper3D generation functions."""

    _job_id_ref: JobId = JobId("hyper3d-ref")
    _job_state_ref: JobState = JobState("pending")

    def __init__(self, connection: BlenderConnectionPort):
        """Initialize with an explicit connection port."""
        self._connection = connection

    @property
    def connection(self) -> BlenderConnectionPort:
        return self._connection

    def get_hyper3d_status(self) -> StatusString:
        """
        Check if Hyper3D Rodin integration is enabled in Blender.
        Returns a message indicating whether Hyper3D Rodin features are available.
        """
        try:
            blender = self.connection
            result = blender.send_command(ActionName("get_hyper3d_status"))
            enabled = result.get("enabled", False)
            message = str(result.get("message", ""))
            if enabled:
                return StatusString(message)
            return StatusString(message or "Hyper3D integration is not enabled")
        except Exception as e:
            logger.error(f"Error checking Hyper3D status: {str(e)}")
            return StatusString(f"Error checking Hyper3D status: {str(e)}")

    def process_bbox(self, original_bbox: CoordinateList | None) -> BBoxIntegers | None:
        if original_bbox is None:
            return None

        if not original_bbox:
            return None

        if any(i <= 0 for i in original_bbox):
            raise ValueError("Incorrect number range: bbox must be bigger than zero!")

        # Scale and convert to integers
        max_val = max(original_bbox)
        if max_val == 0:  # pragma: no cover
            return BBoxIntegers([0, 0, 0])

        return BBoxIntegers([int(float(i) / max_val * 100) for i in original_bbox])

    def generate_hyper3d_model_via_text(
        self, text_prompt: Prompt, bbox_condition: CoordinateList | None = None
    ) -> StatusString:
        """
        Generate 3D asset using Hyper3D by giving description of the desired asset, and import the asset into Blender.
        """
        try:
            blender = self.connection
            result = blender.send_command(
                ActionName("create_rodin_job"),
                {
                    "text_prompt": text_prompt,
                    "images": None,
                    "bbox_condition": self.process_bbox(bbox_condition),
                },
            )
            # Success detection: MAIN_SITE returns "submit_time", FAL_AI returns "request_id"
            succeed = bool(result.get("submit_time") or result.get("request_id"))
            if succeed:
                # Normalize to unified response format
                if result.get("request_id"):  # FAL_AI
                    return StatusString(json.dumps({"request_id": result["request_id"]}))
                else:  # MAIN_SITE
                    return StatusString(
                        json.dumps(
                            {
                                "task_uuid": result["uuid"],
                                "subscription_key": result["jobs"]["subscription_key"],
                            }
                        )
                    )
            else:
                return StatusString(json.dumps(result))
        except Exception as e:
            logger.error(f"Error generating Hyper3D task: {str(e)}")
            return StatusString(f"Error generating Hyper3D task: {str(e)}")

    @staticmethod
    def _load_images_from_paths(paths: list[str]) -> tuple[None, list[Any]]:
        """Load and base64-encode images from file paths."""
        images: list[Any] = []
        for path in paths:
            with open(path, "rb") as f:
                images.append((Path(path).suffix, base64.b64encode(f.read()).decode("ascii")))
        return None, images

    @staticmethod
    def _validate_and_prepare_images(
        input_image_paths: StringList | None,
        input_image_urls: StringList | None,
    ) -> tuple[str | None, list[Any] | None]:
        """Validate inputs and prepare images list for the API call."""
        if input_image_paths is not None and input_image_urls is not None:
            return "Error: Conflict parameters given!", None
        if input_image_paths is not None:
            if not all(os.path.exists(i) for i in input_image_paths):
                return "Error: not all image paths are valid!", None
            result = Hyper3dGenerationTool._load_images_from_paths(input_image_paths)
            return (str(result[0]) if result[0] else None, result[1] if result[1] else None)
        if input_image_urls is not None:
            if not all(urlparse(i) for i in input_image_urls):  # pragma: no cover
                return "Error: not all image URLs are valid!", None
            return None, list(input_image_urls)
        return "Error: No image given!", None

    @staticmethod
    def _parse_image_generation_result(result: dict) -> str:
        """Parse the create_rodin_job result for image generation."""
        succeed = result.get("submit_time", False)
        if succeed:
            return json.dumps(
                {
                    "task_uuid": result["uuid"],
                    "subscription_key": result["jobs"]["subscription_key"],
                }
            )
        else:
            return json.dumps(result)

    def generate_hyper3d_model_via_images(
        self,
        input_image_paths: StringList | None = None,
        input_image_urls: StringList | None = None,
        bbox_condition: CoordinateList | None = None,
    ) -> StatusString:
        """
        Generate 3D asset using Hyper3D by giving images of the wanted asset, and import the generated asset into Blender.
        """
        err, images = self._validate_and_prepare_images(input_image_paths, input_image_urls)
        if err is not None:
            return StatusString(err)
        try:
            blender = self.connection
            result = blender.send_command(
                ActionName("create_rodin_job"),
                {
                    "text_prompt": None,
                    "images": images,
                    "bbox_condition": self.process_bbox(bbox_condition),
                },
            )
            return StatusString(self._parse_image_generation_result(result))
        except Exception as e:
            logger.error(f"Error generating Hyper3D task: {str(e)}")
            return StatusString(f"Error generating Hyper3D task: {str(e)}")

    def poll_rodin_job_status(
        self,
        subscription_key: StatusString | None = None,
        request_id: StatusString | None = None,
    ) -> StatusString:
        """
        Check if the Hyper3D Rodin generation task is completed.
        """
        try:
            blender = self.connection
            kwargs = {}
            if subscription_key:
                kwargs = {
                    "subscription_key": subscription_key,
                }
            elif request_id:
                kwargs = {
                    "request_id": request_id,
                }
            result = blender.send_command(ActionName("poll_rodin_job_status"), kwargs)
            return StatusString(json.dumps(result))
        except Exception as e:
            logger.error(f"Error generating Hyper3D task: {str(e)}")
            return StatusString(f"Error generating Hyper3D task: {str(e)}")

    def import_generated_asset(
        self,
        name: ObjectName,
        task_uuid: TaskUuid | None = None,
        request_id: StatusString | None = None,
    ) -> StatusString:
        """
        Import the asset generated by Hyper3D Rodin after the generation task is completed.
        """
        try:
            blender = self.connection
            kwargs: dict[str, Any] = {"name": name}
            if task_uuid:
                kwargs["task_uuid"] = task_uuid
            elif request_id:
                kwargs["request_id"] = request_id
            result = blender.send_command(ActionName("import_generated_asset"), kwargs)
            return StatusString(json.dumps(result))
        except Exception as e:
            logger.error(f"Error generating Hyper3D task: {str(e)}")
            return StatusString(f"Error generating Hyper3D task: {str(e)}")
