---
title: FigCraft save_file headless vs disk file
created: 2026-11-08
updated: 2026-11-08
type: concept
tags: [figcraft, save-file, mcp, headless, cli]
sources: []
confidence: high
contested: false
contradictions: []
---

## Masalah

`figcraft__save_file` melaporkan sukses (`{"bytes": 19023, "path": "/home/raka/x.figcraft"}`) tetapi file **tidak muncul di disk** dan `ls` tidak menemukannya. `figcraft-cli info` juga gagal membuka path tersebut.

## Penyebab

FigCraft MCP server berjalan **headless, in-process**. `save_file` menyimpan dokumen ke **simpanan internal (document store) FigCraft**, bukan sebagai file biasa di filesystem host. Dokumen masih bisa dibuka kembali melalui `open_file` (`dirty: false`), tetapi tidak ada file `.figcraft` nyata di disk yang bisa dilihat, disalin, atau dipindah.

## Solusi

Gunakan perintah `file.saveAs {data: true}` yang mengembalikan isi file dalam bentuk **base64 `data`**. Decode base64 tersebut dan tulis ke filesystem:

```python
import json, base64
data = json.load(open("<mcp-output>.json"))
raw = base64.b64decode(data["data"])
with open("/home/raka/timelapse_studio_landing_page.figcraft", "wb") as f:
    f.write(raw)
```

Hasilnya adalah file `.figcraft` valid (zip archive, `figcraft-cli info` bisa membuka: 151 nodes, 1 halaman, Desktop Frame 1440×1024).

## Catatan

- `save_file` juga **tidak membuat folder yang belum ada** — path harus sudah ada dan flat (tidak nested di subfolder).
- Setelah file ada di disk, bisa disalin ke folder lain mis. `/home/raka/figcraft/` dengan `cp` biasa.
- Terdapat pesan peringatan font: "missing font JetBrains Mono: 26 text layers" — teks digambar dengan fallback font.

## Terkait

- [[figcraft-cli]]
- [[mcp-server-headless-limits]]