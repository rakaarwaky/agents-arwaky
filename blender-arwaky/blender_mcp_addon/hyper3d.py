import json
import os
import tempfile

import bpy  # type: ignore
import requests  # type: ignore

from . import utils


def get_hyper3d_status():
    """Check if Hyper3D Rodin integration is enabled in Blender."""
    try:
        scene = bpy.context.scene
        if scene is None:
            return {"enabled": False, "message": "No active scene"}

        enabled = getattr(scene, "blendermcp_use_hyper3d", False)
        if enabled:
            return {"enabled": True, "message": "Hyper3D Rodin integration is enabled"}
        else:
            return {"enabled": False, "message": "Hyper3D Rodin integration is disabled"}
    except Exception as e:  # pragma: no cover
        return {"error": str(e)}


def create_rodin_job(
    text_prompt: str | None = None,
    images: list[tuple[str, str]] | None = None,
    bbox_condition=None,
):
    """Create a Rodin job, dispatching based on mode"""
    scene = bpy.context.scene
    if scene is None:
        return {"error": "No active scene"}

    mode = getattr(scene, "blendermcp_hyper3d_mode", "MAIN_SITE")
    if mode == "FAL_AI":
        return create_rodin_job_fal_ai(text_prompt, images, bbox_condition)
    else:
        return create_rodin_job_main_site(text_prompt, images, bbox_condition)


def poll_rodin_job_status(
    subscription_key: str | None = None,
    request_id: str | None = None,
):
    """Poll Rodin job status, dispatching based on mode"""
    scene = bpy.context.scene
    if scene is None:
        return {"error": "No active scene"}

    mode = getattr(scene, "blendermcp_hyper3d_mode", "MAIN_SITE")
    if mode == "FAL_AI":
        if not request_id:
            return {"error": "request_id required for FAL_AI mode"}
        return poll_rodin_job_status_fal_ai(request_id)
    else:
        if not subscription_key:
            return {"error": "subscription_key required for MAIN_SITE mode"}
        return poll_rodin_job_status_main_site(subscription_key)


def create_rodin_job_fal_ai(
    text_prompt: str | None = None,
    images: list[tuple[str, str]] | None = None,
    bbox_condition=None,
):
    """Create a Rodin job using Fal.ai API"""
    try:
        scene = bpy.context.scene
        if scene is None:
            return {"error": "No active scene"}
        api_key = getattr(scene, "blendermcp_hyper3d_api_key", "")

        # Fal.ai Rodin API
        # If images are provided, we use the first one as base (Fal.ai often uses URL or base64)
        # For simplicity, we assume text_prompt is the main input if images are not handled yet
        # or we might need to upload images to a URL first.

        payload = {}
        if text_prompt:
            payload["prompt"] = text_prompt

        # Fal.ai specific options
        if bbox_condition:
            # Fal.ai might have different bbox format, but we'll pass it if needed
            pass  # pragma: no cover

        response = requests.post(
            "https://queue.fal.run/fal-ai/hyper3d/rodin",
            headers={"Authorization": f"Key {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def poll_rodin_job_status_fal_ai(request_id: str):
    """Poll Fal.ai job status"""
    try:
        scene = bpy.context.scene
        if scene is None:
            return {"error": "No active scene"}
        api_key = getattr(scene, "blendermcp_hyper3d_api_key", "")

        response = requests.get(
            f"https://queue.fal.run/fal-ai/hyper3d/requests/{request_id}/status",
            headers={"Authorization": f"Key {api_key}"},
            timeout=10,
        )
        return response.json()
    except Exception as e:  # pragma: no cover
        return {"error": str(e)}


def import_generated_asset(task_uuid: str | None = None, request_id: str | None = None, name: str = "Generated_Asset"):
    """Import generated asset, dispatching based on mode"""
    scene = bpy.context.scene
    if scene is None:
        return {"succeed": False, "error": "No active scene"}

    mode = getattr(scene, "blendermcp_hyper3d_mode", "MAIN_SITE")
    if mode == "FAL_AI":
        if not request_id:
            return {"succeed": False, "error": "request_id required for FAL_AI mode"}
        return import_generated_asset_fal_ai(request_id, name)
    else:
        if not task_uuid:
            return {"succeed": False, "error": "task_uuid required for MAIN_SITE mode"}
        return import_generated_asset_main_site(task_uuid, name)


def create_rodin_job_main_site(
    text_prompt: str | None = None,
    images: list[tuple[str, str]] | None = None,
    bbox_condition=None,
):
    try:
        scene = bpy.context.scene
        if scene is None:
            return {"error": "No active scene"}  # pragma: no cover
        api_key = getattr(scene, "blendermcp_hyper3d_api_key", "")
        if images is None:
            images = []  # pragma: no cover
        files = [
            *[("images", (f"{i:04d}{img_suffix}", img)) for i, (img_suffix, img) in enumerate(images)],
            ("tier", (None, "Sketch")),
            ("mesh_mode", (None, "Raw")),
        ]
        if text_prompt:
            files.append(("prompt", (None, text_prompt)))
        if bbox_condition:
            files.append(("bbox_condition", (None, json.dumps(bbox_condition))))

        response = requests.post(
            "https://hyperhuman.deemos.com/api/v2/rodin",
            headers={"Authorization": f"Bearer {api_key}"},
            files=files,
            timeout=30,
        )
        return response.json()
    except Exception as e:  # pragma: no cover
        return {"error": str(e)}


def poll_rodin_job_status_main_site(subscription_key: str):
    """Call the job status API to get the job status"""
    try:
        scene = bpy.context.scene
        if scene is None:
            return {"error": "No active scene"}
        api_key = getattr(scene, "blendermcp_hyper3d_api_key", "")
        response = requests.post(
            "https://hyperhuman.deemos.com/api/v2/status",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"subscription_key": subscription_key},
            timeout=10,
        )
        data = response.json()
        return {"status_list": [i["status"] for i in data.get("jobs", [])]}
    except Exception as e:  # pragma: no cover
        return {"error": str(e)}


def import_generated_asset_main_site(task_uuid: str, name: str):
    try:
        scene = bpy.context.scene
        if scene is None:
            return {"succeed": False, "error": "No active scene"}  # pragma: no cover
        api_key = getattr(scene, "blendermcp_hyper3d_api_key", "")
        response = requests.post(
            "https://hyperhuman.deemos.com/api/v2/download",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"task_uuid": task_uuid},
            timeout=30,
        )
        data = response.json()

        temp_file_name = None
        for i in data.get("list", []):
            if i["name"].endswith(".glb"):
                from .config import get_config

                with tempfile.NamedTemporaryFile(
                    delete=False, prefix=task_uuid, suffix=".glb", dir=get_config("storage.temp_dir")
                ) as tmp:
                    res = requests.get(i["url"], stream=True, timeout=60)
                    for chunk in res.iter_content(chunk_size=8192):
                        tmp.write(chunk)
                    temp_file_name = tmp.name
                break

        if not temp_file_name:
            return {"succeed": False, "error": "No GLB found"}  # pragma: no cover

        obj = utils.clean_imported_glb(temp_file_name, name)
        if not obj:
            return {"succeed": False, "error": "Import failed"}  # pragma: no cover

        return {
            "succeed": True,
            "name": obj.name,
            "location": [obj.location.x, obj.location.y, obj.location.z],
        }
    except Exception as e:  # pragma: no cover
        return {"succeed": False, "error": str(e)}
    finally:
        if temp_file_name and os.path.exists(temp_file_name):
            try:
                os.unlink(temp_file_name)
            except OSError:  # pragma: no cover
                pass


def import_generated_asset_fal_ai(request_id: str, name: str):
    """Fetch the generated asset from Fal.ai, import into blender"""
    try:
        scene = bpy.context.scene
        if scene is None:
            return {"succeed": False, "error": "No active scene"}  # pragma: no cover
        api_key = getattr(scene, "blendermcp_hyper3d_api_key", "")
        response = requests.get(
            f"https://queue.fal.run/fal-ai/hyper3d/requests/{request_id}",
            headers={"Authorization": f"Key {api_key}"},
            timeout=30,
        )
        data = response.json()

        url = data.get("model_mesh", {}).get("url")
        if not url:
            return {"succeed": False, "error": "Model URL not found in Fal.ai response"}  # pragma: no cover

        temp_file_name = None
        from .config import get_config

        with tempfile.NamedTemporaryFile(
            delete=False, prefix=request_id, suffix=".glb", dir=get_config("storage.temp_dir")
        ) as tmp:
            res = requests.get(url, stream=True, timeout=60)
            res.raise_for_status()
            for chunk in res.iter_content(chunk_size=8192):
                tmp.write(chunk)
            temp_file_name = tmp.name

        obj = utils.clean_imported_glb(temp_file_name, name)
        if not obj:
            return {"succeed": False, "error": "Import failed"}  # pragma: no cover

        return {
            "succeed": True,
            "name": obj.name,
            "location": [obj.location.x, obj.location.y, obj.location.z],
        }
    except Exception as e:  # pragma: no cover
        return {"succeed": False, "error": str(e)}
    finally:
        if temp_file_name and os.path.exists(temp_file_name):
            try:
                os.unlink(temp_file_name)
            except OSError:  # pragma: no cover
                pass
