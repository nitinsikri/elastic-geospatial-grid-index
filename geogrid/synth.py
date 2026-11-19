"""Synthetic vector datasets: clustered points, road-like linestrings, parcel polygons."""
from __future__ import annotations

import numpy as np

from .geometry import Point, LineString, Polygon


def make_features(n: int = 20_000, seed: int = 0, extent=(-125, 24, -66, 50)):
    """Yield (fid, geometry, attributes) roughly over the continental US."""
    rng = np.random.default_rng(seed)
    centres = rng.uniform([extent[0], extent[1]], [extent[2], extent[3]], size=(40, 2))
    for i in range(n):
        cx, cy = centres[rng.integers(len(centres))] + rng.normal(0, 1.5, 2)
        kind = rng.choice(["point", "line", "poly"], p=[0.6, 0.25, 0.15])
        if kind == "point":
            g = Point(cx, cy)
        elif kind == "line":
            steps = rng.normal(0, 0.05, size=(rng.integers(3, 12), 2)).cumsum(axis=0)
            g = LineString([(cx + dx, cy + dy) for dx, dy in steps])
        else:
            r = rng.uniform(0.005, 0.05)
            ang = np.sort(rng.uniform(0, 2 * np.pi, rng.integers(4, 9)))
            g = Polygon([(cx + r * np.cos(a), cy + r * np.sin(a)) for a in ang])
        yield f"f{i:07d}", g, {"type": str(kind), "value": int(rng.integers(0, 1000))}
