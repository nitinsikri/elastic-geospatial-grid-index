"""In-memory stand-in for the HBase Data Table and Index Table, partitioned
across region servers by hashing the row key."""
from __future__ import annotations

import hashlib
import time
from collections import defaultdict

from .geometry import Geometry, to_wkb, from_wkb, intersects_rect
from .grid import HierarchicalGrid


def _region(key: str, n: int) -> int:
    return int(hashlib.md5(key.encode()).hexdigest()[:8], 16) % n


class VectorStore:
    def __init__(self, n_regions: int = 4, grid: HierarchicalGrid | None = None):
        self.n = n_regions
        self.grid = grid or HierarchicalGrid()
        # one dict per region server, as HBase would shard rows
        self.data = [dict() for _ in range(n_regions)]                 # fid -> row
        self.index = [defaultdict(set) for _ in range(n_regions)]      # gid -> {fid}
        self.levels_used: set[int] = set()

    # ------------------------------------------------------------- ingestion
    def put(self, fid: str, geom: Geometry, attributes: dict | None = None, crs: str = "EPSG:4326"):
        row = {"geometry": to_wkb(geom),
               "attributes": {k: v for k, v in (attributes or {}).items() if v is not None},
               "metadata": {"crs": crs, "ts": time.time()}}
        self.data[_region(fid, self.n)][fid] = row
        level = self.grid.level_for_feature(geom.bbox)
        self.levels_used.add(level)
        for gid in self.grid.cells_for_bbox(geom.bbox, level):
            self.index[_region(gid, self.n)][gid].add(fid)

    def get(self, fid: str):
        row = self.data[_region(fid, self.n)].get(fid)
        return None if row is None else (from_wkb(row["geometry"]), row["attributes"])

    def delete(self, fid: str):
        got = self.get(fid)
        if not got:
            return
        g, _ = got
        for level in self.levels_used:
            for gid in self.grid.cells_for_bbox(g.bbox, level):
                self.index[_region(gid, self.n)][gid].discard(fid)
        del self.data[_region(fid, self.n)][fid]

    # ----------------------------------------------------------------- query
    def range_query(self, window, stats: dict | None = None) -> list[str]:
        """Features intersecting the rectangle ``window`` = (minx, miny, maxx, maxy).

        1. find grid cells overlapping the window at every level that holds features
        2. fetch candidate feature IDs from the Index Table (per region server)
        3. fetch geometries from the Data Table and refine with an exact test
        """
        cand: set[str] = set()
        region_work = [0] * self.n
        for level in self.levels_used:
            for gid in self.grid.cells_for_bbox(window, level):
                r = _region(gid, self.n)
                ids = self.index[r].get(gid)
                region_work[r] += 1
                if ids:
                    cand |= ids
        hits = []
        for fid in cand:
            r = _region(fid, self.n)
            region_work[r] += 1
            if intersects_rect(from_wkb(self.data[r][fid]["geometry"]), window):
                hits.append(fid)
        if stats is not None:
            stats.update(candidates=len(cand), hits=len(hits),
                         max_region_work=max(region_work), total_work=sum(region_work))
        return hits

    def full_scan(self, window) -> list[str]:
        """Baseline without an index: test every stored feature."""
        return [fid for part in self.data for fid, row in part.items()
                if intersects_rect(from_wkb(row["geometry"]), window)]

    def __len__(self):
        return sum(len(p) for p in self.data)
