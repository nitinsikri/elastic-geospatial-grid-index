"""Hierarchical grid over the global extent.

Level 0 is the whole extent; level l has 2**l x 2**l cells. Grid IDs are
"<level>_<x-index>_<y-index>", e.g. "2_1_3", which supports prefix scans by level.
"""
from __future__ import annotations

import math

WORLD = (-180.0, -90.0, 180.0, 90.0)


class HierarchicalGrid:
    def __init__(self, extent=WORLD, min_level: int = 2, max_level: int = 10):
        self.extent, self.lmin, self.lmax = extent, min_level, max_level

    def cell_size(self, level: int) -> tuple[float, float]:
        n = 2 ** level
        return ((self.extent[2] - self.extent[0]) / n, (self.extent[3] - self.extent[1]) / n)

    @staticmethod
    def encode(level: int, ix: int, iy: int) -> str:
        return f"{level}_{ix}_{iy}"

    @staticmethod
    def decode(gid: str) -> tuple[int, int, int]:
        level, ix, iy = gid.split("_")
        return int(level), int(ix), int(iy)

    def cells_for_bbox(self, bbox, level: int) -> list[str]:
        w, h = self.cell_size(level)
        n = 2 ** level
        x0 = min(n - 1, max(0, int((bbox[0] - self.extent[0]) // w)))
        x1 = min(n - 1, max(0, int((bbox[2] - self.extent[0]) // w)))
        y0 = min(n - 1, max(0, int((bbox[1] - self.extent[1]) // h)))
        y1 = min(n - 1, max(0, int((bbox[3] - self.extent[1]) // h)))
        return [self.encode(level, ix, iy) for ix in range(x0, x1 + 1) for iy in range(y0, y1 + 1)]

    def cell_bbox(self, gid: str):
        level, ix, iy = self.decode(gid)
        w, h = self.cell_size(level)
        x, y = self.extent[0] + ix * w, self.extent[1] + iy * h
        return (x, y, x + w, y + h)

    def level_for_feature(self, bbox, max_cells: int = 4) -> int:
        """Finest level at which the feature touches at most ``max_cells`` cells."""
        for level in range(self.lmax, self.lmin - 1, -1):
            if len(self.cells_for_bbox(bbox, level)) <= max_cells:
                return level
        return self.lmin

    def level_for_query(self, window, target_cells: int = 64) -> int:
        """Finest level whose cell count for the window stays near ``target_cells``."""
        w = window[2] - window[0]
        h = window[3] - window[1]
        for level in range(self.lmax, self.lmin - 1, -1):
            cw, ch = self.cell_size(level)
            if math.ceil(w / cw + 1) * math.ceil(h / ch + 1) <= target_cells:
                return level
        return self.lmin
