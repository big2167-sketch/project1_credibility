"""
Benchmark script for Deliverable 1.

This measures how long scoring takes for a small set of URLs.
We do:
- serial timing
- concurrent timing

Goal: show the function can handle reasonable loads without big delays.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.scorer import score_source

URLS = [
    "https://www.nih.gov",
    "https://www.cdc.gov",
    "https://www.nature.com",
    "https://en.wikipedia.org/wiki/Main_Page",
    "https://example.com",
    "https://www.bbc.com",
    "https://www.nytimes.com",
    "https://www.whitehouse.gov",
]

def run_serial(n_calls: int = 20):
    start = time.perf_counter()
    for i in range(n_calls):
        score_source(URLS[i % len(URLS)])
    end = time.perf_counter()
    total = end - start
    print(f"[SERIAL] calls={n_calls} total={total:.3f}s avg={total/n_calls:.3f}s")

def run_concurrent(n_calls: int = 20, workers: int = 8):
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(score_source, URLS[i % len(URLS)]) for i in range(n_calls)]
        for _ in as_completed(futures):
            pass
    end = time.perf_counter()
    total = end - start
    print(f"[CONCURRENT] calls={n_calls} workers={workers} total={total:.3f}s avg={total/n_calls:.3f}s")

if __name__ == "__main__":
    run_serial(20)
    run_concurrent(20, 8)