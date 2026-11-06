"""NON-FUNCTIONAL tests (OBS-NF-001, OBS-NF-004): 10,000 books + 20 concurrent sessions.

TC-Perf-01   90% of catalogue/search/detail requests finish within 3 seconds.
TC-Scale-01  the system works with 10,000 records and 20 concurrent sessions without failures.
"""
import statistics
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from scripts.seed import seed_books

pytestmark = pytest.mark.slow


@pytest.fixture()
def big_catalogue(db):
    seed_books(db, 10_000)


def _timed_get(client, url, params=None):
    start = time.perf_counter()
    response = client.get(url, params=params)
    return response.status_code, time.perf_counter() - start


def test_TC_Scale_01_catalogue_holds_10000_records(client, big_catalogue):
    r = client.get("/api/books", params={"limit": 100})
    assert r.status_code == 200
    assert r.json()["count"] == 10_000
    assert len(r.json()["results"]) == 100


def test_TC_Perf_01_and_Scale_01_20_concurrent_sessions_p90_under_3_seconds(client, big_catalogue):
    requests = [
        ("/api/books", {"limit": 50}),
        ("/api/books/search", {"q": "Silent", "sort": "price_asc"}),
        ("/api/books/search", {"category": "Science", "minPrice": 100, "maxPrice": 900}),
        ("/api/books/1", None),
    ] * 10  # 40 requests

    with ThreadPoolExecutor(max_workers=20) as pool:  # 20 concurrent sessions
        results = list(pool.map(lambda args: _timed_get(client, *args), requests))

    statuses = [s for s, _ in results]
    durations = sorted(d for _, d in results)
    assert all(s in (200, 204) for s in statuses), f"failed requests: {statuses}"
    p90 = durations[int(len(durations) * 0.9) - 1]
    print(f"\n p50={statistics.median(durations):.3f}s  p90={p90:.3f}s  max={durations[-1]:.3f}s")
    assert p90 <= 3.0
