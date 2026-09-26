# EGL/ctypes mocking patterns for PSD Timelapse renderer tests

## Two distinct ctypes output patterns in `utility_gpu_rasterizer.py`

Both exist in the same module but require DIFFERENT mock access patterns. Getting them mixed up causes AttributeError failures.

### Pattern 1: `_enumerate_egl_devices` — `ctypes.byref` with `._obj.value`

`eglQueryDevicesEXT` receives `num` via `ctypes.byref(num)` — a pointer to c_int.
The mock callback writes to `num_written._obj.value`:

```python
def _mock_enum(display, max_devices, devices, num):
    num_written._obj.value = 1  # pointer: access via _obj.value
```

The test passes `new_callable=lambda: ctypes.Array(ctypes.c_int, 1)` so the
pointer has a real underlying integer to write to.

### Pattern 2: `_choose_egl_config` — direct `EGLint` with `.value`

`eglChooseConfig` receives `num_configs = EGLint()` — a plain c_int, NOT a pointer.
The mock callback writes to `num_out.value` directly:

```python
def _fake_choose(display, attribs, configs, max_cfgs, num_out):
    num_out.value = 1  # plain c_int: access via .value
```

## Pitfall: `_obj` is for pointers only

`ctypes.byref(c_int)` → pointer object → `._obj.value`
Plain `c_int()` → direct value → `.value`
Using `._obj.value` on a plain c_int raises AttributeError.
Using `.value` on a pointer raises AttributeError.

Check the production code: how is the parameter passed to the function?
- `ctypes.byref(x)` → mock must use `x._obj.value`
- `x` directly (no byref) → mock must use `x.value`

## Reference files
- `modules/renderer/src/utility_gpu_rasterizer.py` (real code)
- `modules/renderer/tests/test_utility_gpu_rasterizer.py` (test code)
