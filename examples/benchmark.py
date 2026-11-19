"""Index vs full scan, and how per-region work falls as region servers are added."""
import time

import numpy as np

from geogrid import VectorStore, make_features

N = 30_000
features = list(make_features(N))
rng = np.random.default_rng(1)
windows = []
for size in [0.05, 0.5, 2.0]:
    for _ in range(20):
        x, y = rng.uniform(-120, -70), rng.uniform(26, 48)
        windows.append((size, (x, y, x + size, y + size)))

print(f"{N} features")
for regions in [1, 2, 4, 8]:
    store = VectorStore(n_regions=regions)
    t = time.perf_counter()
    for fid, g, a in features:
        store.put(fid, g, a)
    ingest = time.perf_counter() - t
    work = []
    for _, w in windows:
        s = {}
        store.range_query(w, s)
        work.append(s["max_region_work"])
    print(f"regions={regions}: ingest {N / ingest:,.0f} features/s, "
          f"mean busiest-region work per query {np.mean(work):,.0f} row reads")

store = VectorStore(n_regions=4)
for fid, g, a in features:
    store.put(fid, g, a)
print("\nwindow   index ms   scan ms   hits")
for size in [0.05, 0.5, 2.0]:
    ws = [w for s, w in windows if s == size]
    t = time.perf_counter(); h1 = [len(store.range_query(w)) for w in ws]; ti = time.perf_counter() - t
    t = time.perf_counter(); h2 = [len(store.full_scan(w)) for w in ws]; ts = time.perf_counter() - t
    assert h1 == h2
    print(f"{size:>5}°  {ti / len(ws) * 1000:9.2f}  {ts / len(ws) * 1000:8.2f}   {np.mean(h1):6.0f}")
