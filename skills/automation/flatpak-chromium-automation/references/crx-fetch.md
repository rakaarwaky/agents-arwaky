# Fetching and unpacking a Chrome Web Store CRX (no browser needed)

## Download endpoint

```
curl -sS -L -o ext.crx \
  "https://clients2.google.com/service/update2/crx?response=redirect&os=linux&arch=x64&nacl_arch=x86-64&prod=chromiumcrx&prodversion=152.0.0.0&acceptformat=crx2,crx3&x=id%3D<EXTENSION_ID>%26uc"
```

Replace `<EXTENSION_ID>` with the 32-char store id (e.g. Bitwarden
`nngceckbapebfimnlniiiahkandclblb`). `prodversion` just needs to look modern;
the response is a real CRX (verify `file ext.crx` says "Google Chrome
extension", magic `Cr24`).

## CRX binary layout (gotcha that costs an hour)

Both versions start `Cr24` + 4-byte LE version, then diverge:

* **CRX3** (version=3): `magic(4) version(4) header_len(4)` then an opaque
  protobuf signed header. Zip payload starts at **offset 12 + header_len** —
  NOT after parsing pubkey/sig lengths (those fields do not exist in CRX3;
  reading them yields garbage offsets). `zipfile` accepts a wrong offset
  silently because the EOCD sits at the tail, then `namelist()` fails with
  "negative seek" — assert the literal `PK\x03\x04` at the candidate offset.
* **CRX2** (version=2): `magic(4) version(4) pub_len(4) sig_len(4)` + pub +
  sig, zip at `12 + pub_len + sig_len`.

Unpack:

```python
import io, struct, zipfile
from pathlib import Path
raw = Path('ext.crx').read_bytes()
assert raw[:4] == b'Cr24'
ver, = struct.unpack_from('<I', raw, 4)
if ver == 3:
    hlen, = struct.unpack_from('<I', raw, 8)
    off = 12 + hlen
else:
    pub, sig = struct.unpack_from('<II', raw, 8)
    off = 12 + pub + sig
assert raw[off:off + 4] == b'PK\x03\x04'
with zipfile.ZipFile(io.BytesIO(raw[off:])) as z:
    z.extractall('unpacked/')
```

Load the unpacked dir with `--load-extension=<abs path>`.

## Unpacked-extension ID is NOT the store ID

An unpacked dir gets a `chrome-extension://` id derived from a hash of its
absolute path, so it never matches (or reuses the permissions of) the store
extension. If the workflow needs the OFFICIAL id — for
`chrome-extension://<id>/...` URLs or matching an existing vault/login setup —
compute the id from the unpacked path (first 32 hex chars mapped `0-f` ->
`a-p`) and use that in URLs, or install the store-signed CRX through External
Extensions `external_crx` instead (untested under flatpak).
