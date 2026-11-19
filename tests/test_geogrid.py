import numpy as np

from geogrid import (Point, LineString, Polygon, to_wkb, from_wkb, intersects_rect,
                     HierarchicalGrid, VectorStore, make_features)


def test_wkb_roundtrip():
    for g in [Point(1, 2), LineString([(0, 0), (1, 1), (2, 0)]),
              Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]:
        assert from_wkb(to_wkb(g)) == g


def test_intersections():
    r = (0, 0, 1, 1)
    assert intersects_rect(Point(0.5, 0.5), r)
    assert not intersects_rect(Point(2, 2), r)
    assert intersects_rect(LineString([(-1, 0.5), (2, 0.5)]), r)       # crosses, no vertex inside
    assert intersects_rect(Polygon([(-5, -5), (5, -5), (5, 5), (-5, 5)]), r)  # window inside


def test_grid_ids():
    g = HierarchicalGrid()
    cells = g.cells_for_bbox((-1, -1, 1, 1), 2)
    assert all(c.startswith("2_") for c in cells) and len(cells) == 4


def test_index_matches_full_scan():
    s = VectorStore(n_regions=3)
    for fid, geom, a in make_features(3000, seed=5):
        s.put(fid, geom, a)
    rng = np.random.default_rng(0)
    for _ in range(25):
        x, y, d = rng.uniform(-120, -70), rng.uniform(26, 48), rng.uniform(0.01, 3)
        w = (x, y, x + d, y + d)
        assert sorted(s.range_query(w)) == sorted(s.full_scan(w))


def test_delete():
    s = VectorStore()
    s.put("a", Point(10, 10))
    s.delete("a")
    assert s.range_query((9, 9, 11, 11)) == [] and len(s) == 0
