# ComfyUI — Run Examples

## Local run (defaults to http://127.0.0.1:8188)

```bash
python scripts/run_workflow.py \
  --workflow workflow_api.json \
  --args '{"prompt": "a beautiful sunset over mountains", "seed": -1, "steps": 30}' \
  --output-dir ./outputs
```

## Cloud run (export API key once; scripts route to /api automatically)

```bash
export COMFY_CLOUD_API_KEY="comfyui-..."
python scripts/run_workflow.py \
  --workflow workflow_api.json \
  --args '{"prompt": "..."}' \
  --host https://cloud.comfy.org \
  --output-dir ./outputs
```

## Real-time progress via WebSocket (requires `pip install websocket-client`)

```bash
python scripts/run_workflow.py --workflow flux_dev.json --args '{"prompt": "..."}' --ws
```

## img2img / inpaint: `--input-image` uploads + references automatically

```bash
python scripts/run_workflow.py \
  --workflow sdxl_img2img.json \
  --input-image image=./photo.png \
  --args '{"prompt": "make it watercolor", "denoise": 0.6}'
```

## Batch / sweep: N random seeds, parallel up to cloud tier limit

```bash
python scripts/run_batch.py \
  --workflow sdxl.json \
  --args '{"prompt": "abstract"}' \
  --count 8 --randomize-seed --parallel 3 \
  --output-dir ./outputs/batch
```

`-1` for `seed` (or `--randomize-seed`) generates a fresh random seed per run.
