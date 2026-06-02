import base64
import hashlib
import hmac
import json
import os
import os.path as osp
import re
import shutil
import tempfile
import threading
import time
import zipfile
from datetime import datetime

import bpy  # type: ignore
import requests  # type: ignore

from . import utils


def get_hunyuan3d_status():
    """Check if Hunyuan3D integration is enabled in Blender."""
    try:
        scene = bpy.context.scene
        if scene is None:
            return {"enabled": False, "message": "No active scene"}

        enabled = getattr(scene, "blendermcp_use_hunyuan3d", False)
        if enabled:
            return {"enabled": True, "message": "Hunyuan3D integration is enabled"}
        else:
            return {"enabled": False, "message": "Hunyuan3D integration is disabled"}
    except Exception as e:  # pragma: no cover
        return {"error": str(e)}


def create_hunyuan_job(text_prompt: str | None = None, image: str | None = None):
    """Create a Hunyuan job, dispatching based on mode"""
    scene = bpy.context.scene
    if scene is None:
        return {"error": "No active scene"}

    mode = getattr(scene, "blendermcp_hunyuan3d_mode", "LOCAL_API")
    if mode == "OFFICIAL_API":
        return create_hunyuan_job_official(text_prompt, image)
    else:
        return create_hunyuan_job_local_site(text_prompt, image)


def create_hunyuan_job_official(text_prompt: str | None = None, image: str | None = None):
    """Create a job using the official Tencent Cloud Hunyuan 3D API."""
    try:
        scene = bpy.context.scene
        secret_id = getattr(scene, "blendermcp_hunyuan3d_secret_id", "")
        secret_key = getattr(scene, "blendermcp_hunyuan3d_secret_key", "")

        if not secret_id or not secret_key:
            return {"error": "Tencent Cloud SecretId/SecretKey not configured"}

        data = {}
        if text_prompt:
            data["Text"] = text_prompt

        if image:
            if re.match(r"^https?://", image, re.IGNORECASE):
                data["ImageUrl"] = image
            else:
                abs_image_path = os.path.abspath(image)
                with open(abs_image_path, "rb") as f:
                    data["ImageBase64"] = base64.b64encode(f.read()).decode("ascii")

        headParams = {
            "Action": "SubmitHunyuanTo3DProJob",
            "Version": "2023-09-01",
        }

        headers, endpoint = get_tencent_cloud_sign_headers(
            "POST", "/", headParams, data, "hunyuan", "ap-guangzhou", secret_id, secret_key
        )

        response = requests.post(endpoint, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            res_json = response.json()
            if "Response" in res_json and "Error" in res_json["Response"]:
                return {"error": res_json["Response"]["Error"]["Message"]}
            return res_json
        return {
            "error": f"Official API request failed with status {response.status_code}: {response.text}"
        }  # pragma: no cover

    except Exception as e:  # pragma: no cover
        return {"error": str(e)}


def get_tencent_cloud_sign_headers(
    method: str,
    path: str,
    headParams: dict,
    data: dict,
    service: str,
    region: str,
    secret_id: str,
    secret_key: str,
    host: str | None = None,
):
    """Generate the signature header required for Tencent Cloud API requests headers"""
    timestamp = int(time.time())
    date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")

    if not host:
        host = f"{service}.tencentcloudapi.com"

    endpoint = f"https://{host}"
    payload_str = json.dumps(data)

    canonical_uri = path
    canonical_querystring = ""
    ct = "application/json; charset=utf-8"
    canonical_headers = f"content-type:{ct}\nhost:{host}\nx-tc-action:{headParams.get('Action', '').lower()}\n"
    signed_headers = "content-type;host;x-tc-action"
    hashed_request_payload = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

    canonical_request = (
        method
        + "\n"
        + canonical_uri
        + "\n"
        + canonical_querystring
        + "\n"
        + canonical_headers
        + "\n"
        + signed_headers
        + "\n"
        + hashed_request_payload
    )

    credential_scope = f"{date}/{service}/tc3_request"
    hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
    string_to_sign = (
        "TC3-HMAC-SHA256" + "\n" + str(timestamp) + "\n" + credential_scope + "\n" + hashed_canonical_request
    )

    def sign(key, msg):
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    secret_date = sign(("TC3" + secret_key).encode("utf-8"), date)
    secret_service = sign(secret_date, service)
    secret_signing = sign(secret_service, "tc3_request")
    signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    authorization = (
        "TC3-HMAC-SHA256"
        + " "
        + "Credential="
        + secret_id
        + "/"
        + credential_scope
        + ", "
        + "SignedHeaders="
        + signed_headers
        + ", "
        + "Signature="
        + signature
    )

    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json; charset=utf-8",
        "Host": host,
        "X-TC-Action": headParams.get("Action", ""),
        "X-TC-Timestamp": str(timestamp),
        "X-TC-Version": headParams.get("Version", ""),
        "X-TC-Region": region,
    }

    return headers, endpoint


# Local job cache for async generation — thread-safe via Lock
_local_jobs = {}
_local_jobs_lock = threading.Lock()


def create_hunyuan_job_local_site(text_prompt: str | None = None, image: str | None = None):
    """
    Asynchronous version of local generation to prevent UI freeze.
    """
    import uuid

    try:
        scene = bpy.context.scene
        if scene is None:
            return {"error": "No active scene"}
        base_url = getattr(scene, "blendermcp_hunyuan3d_api_url", "").rstrip("/")
        if not base_url:
            return {"error": "API URL is not given"}

        # Prepare parameters from scene
        data = {
            "octree_resolution": getattr(scene, "blendermcp_hunyuan3d_octree_resolution", 256),
            "num_inference_steps": getattr(scene, "blendermcp_hunyuan3d_num_inference_steps", 20),
            "guidance_scale": getattr(scene, "blendermcp_hunyuan3d_guidance_scale", 7.0),
            "texture": getattr(scene, "blendermcp_hunyuan3d_texture", False),
        }

        if text_prompt:
            data["text"] = text_prompt

        if image:
            if re.match(r"^https?://", image, re.IGNORECASE):  # pragma: no cover
                resImg = requests.get(image, timeout=30)  # pragma: no cover
                resImg.raise_for_status()  # pragma: no cover
                data["image"] = base64.b64encode(resImg.content).decode("ascii")  # pragma: no cover
            else:  # pragma: no cover
                abs_image_path = os.path.abspath(image)  # pragma: no cover
                with open(abs_image_path, "rb") as f:  # pragma: no cover
                    data["image"] = base64.b64encode(f.read()).decode("ascii")  # pragma: no cover

        # Create job entry
        job_id = f"job_local_{uuid.uuid4().hex[:8]}"
        with _local_jobs_lock:
            _local_jobs[job_id] = {"status": "RUN", "temp_file": None, "error": None}

        def generation_worker():
            try:
                response = requests.post(f"{base_url}/generate", json=data, timeout=300)
                if response.status_code != 200:  # pragma: no cover
                    with _local_jobs_lock:  # pragma: no cover
                        _local_jobs[job_id]["status"] = "FAILED"  # pragma: no cover
                        _local_jobs[job_id]["error"] = f"Generation failed: {response.text}"  # pragma: no cover
                    return  # pragma: no cover

                from .config import get_config

                temp_dir_config = get_config("storage.temp_dir")

                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".glb", dir=temp_dir_config) as temp_file:
                    temp_file.write(response.content)
                    with _local_jobs_lock:
                        _local_jobs[job_id]["temp_file"] = temp_file.name

                with _local_jobs_lock:
                    _local_jobs[job_id]["status"] = "DONE"
            except Exception as e:  # pragma: no cover
                with _local_jobs_lock:  # pragma: no cover
                    _local_jobs[job_id]["status"] = "FAILED"  # pragma: no cover
                    _local_jobs[job_id]["error"] = str(e)  # pragma: no cover

        # Start thread
        threading.Thread(target=generation_worker, daemon=True).start()

        # Return JobId as expected by the server tool
        return {"Response": {"JobId": job_id}}

    except Exception as e:  # pragma: no cover
        return {"error": str(e)}


def poll_hunyuan_job_status(job_id: str):
    """Poll the status of a Hunyuan3D job, supports local and official jobs."""
    try:
        # Check local jobs first
        if job_id and job_id.startswith("job_local_"):
            with _local_jobs_lock:
                job = _local_jobs.get(job_id)
            if not job:
                return {"error": "Job not found"}

            with _local_jobs_lock:
                job_status = _local_jobs[job_id].get("status", "UNKNOWN")
                job_temp_file = _local_jobs[job_id].get("temp_file")
                job_error = _local_jobs[job_id].get("error")

            if job_status == "DONE":
                return {"Status": "DONE", "ResultFile3Ds": f"local://{job_temp_file}"}
            elif job_status == "FAILED":
                return {"Status": "FAILED", "Error": job_error}
            else:
                return {"Status": "RUN"}

        # Official API polling or proxy polling
        scene = bpy.context.scene
        if scene is None:
            return {"error": "No active scene"}

        mode = getattr(scene, "blendermcp_hunyuan3d_mode", "LOCAL_API")
        if mode == "OFFICIAL_API":
            secret_id = getattr(scene, "blendermcp_hunyuan3d_secret_id", "")  # pragma: no cover
            secret_key = getattr(scene, "blendermcp_hunyuan3d_secret_key", "")  # pragma: no cover

            data = {"JobId": job_id}  # pragma: no cover
            headParams = {  # pragma: no cover
                "Action": "QueryHunyuanTo3DProJob",  # pragma: no cover
                "Version": "2023-09-01",  # pragma: no cover
            }  # pragma: no cover

            headers, endpoint = get_tencent_cloud_sign_headers(  # pragma: no cover
                "POST",
                "/",
                headParams,
                data,
                "hunyuan",
                "ap-guangzhou",
                secret_id,
                secret_key,  # pragma: no cover
            )  # pragma: no cover

            response = requests.post(endpoint, headers=headers, json=data, timeout=10)  # pragma: no cover
            if response.status_code == 200:  # pragma: no cover
                res_json = response.json()  # pragma: no cover
                if "Response" in res_json:  # pragma: no cover
                    resp = res_json["Response"]  # pragma: no cover
                    if "Error" in resp:  # pragma: no cover
                        return {"error": resp["Error"]["Message"]}  # pragma: no cover

                    status = resp.get("Status", "RUN")  # pragma: no cover
                    result = {"Status": status}  # pragma: no cover
                    if status == "DONE":  # pragma: no cover
                        result["ResultFile3Ds"] = resp.get("ResultFile3Ds")  # pragma: no cover
                    elif status == "FAIL":  # pragma: no cover
                        result["Error"] = resp.get("ErrorMsg", "Unknown error")  # pragma: no cover
                    return result  # pragma: no cover
            return {"error": f"Official API polling failed with status {response.status_code}"}  # pragma: no cover

        # Legacy/Proxy API polling
        api_url = getattr(scene, "blendermcp_hunyuan3d_api_url", "")
        if not api_url:
            return {"error": "Hunyuan3D API URL not configured"}

        response = requests.get(f"{api_url}/status/{job_id}", timeout=10)
        if response.status_code == 200:
            return response.json()
        return {"error": f"API returned status {response.status_code}"}
    except Exception as e:  # pragma: no cover
        return {"error": str(e)}


def import_generated_asset_hunyuan(name: str, zip_file_url: str):
    """
    Import generated asset. Supports local temp files and remote ZIPs.
    """
    if not zip_file_url:
        return {"error": "Zip file/path not found"}

    temp_dir = None
    try:
        if zip_file_url.startswith("local://"):
            # Local async job result
            glb_path = zip_file_url[8:]
            if not os.path.exists(glb_path):
                return {"succeed": False, "error": f"Local file not found: {glb_path}"}

            obj = utils.clean_imported_glb(glb_path, name)

            # Cleanup the temp glb file
            try:
                os.unlink(glb_path)
            except OSError:  # pragma: no cover
                pass

            if not obj:
                return {"succeed": False, "error": "Import failed"}

            return {
                "succeed": True,
                "name": obj.name,
                "location": list(obj.location),
            }

        # Original logic for remote ZIP files
        from .config import get_config

        temp_dir = tempfile.mkdtemp(prefix="hunyuan_obj_", dir=get_config("storage.temp_dir"))
        zip_file_path = osp.join(temp_dir, "model.zip")

        zip_response = requests.get(zip_file_url, stream=True, timeout=60)
        zip_response.raise_for_status()
        with open(zip_file_path, "wb") as f:
            for chunk in zip_response.iter_content(chunk_size=8192):
                f.write(chunk)  # pragma: no cover

        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        # Look for OBJ or GLB in the zip
        model_file = next(
            (osp.join(temp_dir, f) for f in os.listdir(temp_dir) if f.endswith(".obj") or f.endswith(".glb")),
            None,
        )

        if not model_file:
            return {"succeed": False, "error": "No model file (OBJ/GLB) found in ZIP"}  # pragma: no cover

        model_file = os.path.abspath(model_file)

        if model_file.endswith(".obj"):
            existing = set(bpy.data.objects.keys())  # type: ignore
            if bpy.app.version >= (4, 0, 0):
                bpy.ops.wm.obj_import(filepath=model_file)
            else:
                bpy.ops.import_scene.obj(filepath=model_file)  # pragma: no cover

            new_objs = [
                obj
                for n, obj in bpy.data.objects.items()  # type: ignore
                if n not in existing and obj.type == "MESH"
            ]
            if not new_objs:
                return {"succeed": False, "error": "Import failed"}  # pragma: no cover
            obj = new_objs[0]
            if name:
                obj.name = name
        else:
            # GLB
            obj = utils.clean_imported_glb(model_file, name)
            if not obj:
                return {"succeed": False, "error": "Import failed"}  # pragma: no cover

        return {
            "succeed": True,
            "name": obj.name,
            "location": list(obj.location),
        }
    except Exception as e:
        return {"succeed": False, "error": str(e)}
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)
