"""Minimal vector geometry: Point, LineString, Polygon, WKB encoding and
rectangle-intersection tests (no external GIS library needed)."""
from __future__ import annotations

import struct
from dataclasses import dataclass

Coord = tuple[float, float]


@dataclass(frozen=True)
class Geometry:
    kind: str                 # "Point" | "LineString" | "Polygon"
    coords: tuple[Coord, ...]  # polygon: exterior ring, closed

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        xs = [c[0] for c in self.coords]
        ys = [c[1] for c in self.coords]
        return min(xs), min(ys), max(xs), max(ys)


def Point(x, y):
    return Geometry("Point", ((float(x), float(y)),))


def LineString(coords):
    return Geometry("LineString", tuple((float(x), float(y)) for x, y in coords))


def Polygon(coords):
    c = [(float(x), float(y)) for x, y in coords]
    if c[0] != c[-1]:
        c.append(c[0])
    return Geometry("Polygon", tuple(c))


# ---------------------------------------------------------------- WKB (OGC)
_TYPES = {"Point": 1, "LineString": 2, "Polygon": 3}
_NAMES = {v: k for k, v in _TYPES.items()}


def to_wkb(g: Geometry) -> bytes:
    out = struct.pack("<BI", 1, _TYPES[g.kind])
    if g.kind == "Point":
        return out + struct.pack("<dd", *g.coords[0])
    if g.kind == "LineString":
        out += struct.pack("<I", len(g.coords))
    else:
        out += struct.pack("<II", 1, len(g.coords))
    return out + b"".join(struct.pack("<dd", x, y) for x, y in g.coords)


def from_wkb(b: bytes) -> Geometry:
    _, t = struct.unpack_from("<BI", b, 0)
    kind, off = _NAMES[t], 5
    if kind == "Point":
        return Geometry(kind, (struct.unpack_from("<dd", b, off),))
    if kind == "Polygon":
        off += 4                      # number of rings (we write one)
    (n,) = struct.unpack_from("<I", b, off)
    off += 4
    pts = tuple(struct.unpack_from("<dd", b, off + 16 * i) for i in range(n))
    return Geometry(kind, pts)


# --------------------------------------------------------- intersection tests
def _in_rect(p, r):
    return r[0] <= p[0] <= r[2] and r[1] <= p[1] <= r[3]


def _ccw(a, b, c):
    return (c[1] - a[1]) * (b[0] - a[0]) - (b[1] - a[1]) * (c[0] - a[0])


def _seg_intersect(p1, p2, q1, q2):
    d1, d2 = _ccw(q1, q2, p1), _ccw(q1, q2, p2)
    d3, d4 = _ccw(p1, p2, q1), _ccw(p1, p2, q2)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return True
    return False


def _rect_edges(r):
    a, b, c, d = (r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])
    return [(a, b), (b, c), (c, d), (d, a)]


def _point_in_poly(p, poly):
    inside, n = False, len(poly)
    for i in range(n - 1):
        (x1, y1), (x2, y2) = poly[i], poly[i + 1]
        if (y1 > p[1]) != (y2 > p[1]):
            if p[0] < (x2 - x1) * (p[1] - y1) / (y2 - y1) + x1:
                inside = not inside
    return inside


def intersects_rect(g: Geometry, r) -> bool:
    """Exact test: does geometry g intersect rectangle r = (minx, miny, maxx, maxy)?"""
    b = g.bbox
    if b[2] < r[0] or b[0] > r[2] or b[3] < r[1] or b[1] > r[3]:
        return False
    if any(_in_rect(p, r) for p in g.coords):
        return True
    if g.kind == "Point":
        return False
    edges = _rect_edges(r)
    for i in range(len(g.coords) - 1):
        for e in edges:
            if _seg_intersect(g.coords[i], g.coords[i + 1], *e):
                return True
    if g.kind == "Polygon":
        return _point_in_poly((r[0], r[1]), g.coords)   # window fully inside polygon
    return False
