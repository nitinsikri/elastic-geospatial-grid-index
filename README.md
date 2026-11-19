# Elastic Cloud Storage and Hierarchical Grid Indexing for Geospatial Vector Data

Reference implementation of the method described in:

**Nitin Sikri.** *Elastic Cloud Infrastructure for Massive-Scale Geospatial Vector Data Management.* Proceedings of the 5th International Conference on Big Data and Artificial Intelligence Applications (ICBDAIA'26), Springer, Lecture Notes in Networks and Systems, 2026. *(In press.)*

> **Reference implementation.** This repository was written in November 2026, after the paper was accepted, to illustrate the method described in the paper and to make it easy to reuse. It is **not** the original experimental code, it runs on **synthetic data**, and its numbers will **differ** from the results reported in the paper. Please cite the paper for the method and its reported results.

## What the paper proposes

A cloud-native design for storing points, linestrings and polygons on a distributed wide-column store (HBase). Geometries are stored as OGC WKB in a Data Table keyed by feature ID; a separate Index Table maps hierarchical grid cells (`level_x_y`) to feature IDs. Range queries look up overlapping cells, fetch candidates and refine them with an exact geometric test. Rows are spread across region servers by hashing.

## What this repository contains

- `geogrid/geometry.py` – Point / LineString / Polygon, WKB encode/decode, exact rectangle-intersection tests (no GIS dependency)
- `geogrid/grid.py` – hierarchical grid, cell IDs and level selection
- `geogrid/store.py` – in-memory stand-in for the HBase Data and Index tables, hash-partitioned across *n* region servers; insert, delete, range query, full-scan baseline
- `geogrid/synth.py` – clustered synthetic vector features
- `examples/benchmark.py`, `tests/`

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. python examples/benchmark.py
python -m pytest -q
```



## How it maps to the paper

| Paper | Code |
|---|---|
| WKB geometry serialisation (3.1) | `to_wkb`, `from_wkb` |
| Data Table / Index Table (3.3) | `VectorStore.data`, `VectorStore.index` |
| Hash partitioning across region servers (3.4) | `_region` |
| Grid construction and IDs (4.1) | `HierarchicalGrid.encode`, `cells_for_bbox` |
| Indexing algorithm (4.2) | `VectorStore.put` |
| Range query processing (4.3) | `VectorStore.range_query` |
| Index maintenance (4.4) | `VectorStore.delete` |

## Limitations

- Runs in memory in one process; to use HBase, replace the dicts in `store.py` with HBase tables (e.g. via `happybase`), keeping the same row keys.
- Spatial joins and geometry simplification (paper Sect. 6) are not implemented.
- Timings depend on hardware and are not comparable with the paper's cluster results.

## How to cite

If you use this code, please cite the paper:

```bibtex
@inproceedings{sikri2026geospatial,
  author    = {Sikri, Nitin},
  title     = {Elastic Cloud Infrastructure for Massive-Scale Geospatial Vector Data Management},
  booktitle = {Proceedings of the 5th International Conference on Big Data and Artificial Intelligence Applications (ICBDAIA'26)},
  publisher = {Springer, Lecture Notes in Networks and Systems},
  year      = {2026}
}
```

GitHub also shows a **"Cite this repository"** button generated from `CITATION.cff`.

## Licence

MIT – see [LICENSE](LICENSE).
