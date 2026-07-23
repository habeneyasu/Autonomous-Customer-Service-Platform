# Docs assets

| File | Used in |
|------|---------|
| `zero-trust-control-plane.png` | Root `README.md` — Architecture at a Glance |
| `workbench-preview.png` | Root `README.md` — Golden flows (add screenshot from `:7861`) |

Other markdown under `docs/` is gitignored (local/architecture notes). Only this file is tracked from `docs/assets/`.

RAG policy sources (`knowledge/sources/`) and the Chroma index (`.knowledge/`) are also gitignored — rebuild locally:

```bash
PYTHONPATH=. python knowledge/index/run_indexer.py
```
