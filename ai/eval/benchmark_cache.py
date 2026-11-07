"""Measure /ask latency without and with the Redis cache.

Clears cached answers, asks each eval question once (cache miss, full pipeline),
then asks again (cache hit). Needs the API running and Redis reachable.

Usage (from ai/):
    python eval/benchmark_cache.py [--url http://localhost:8000] [--limit 10]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from coursewise.cache import get_cache  # noqa: E402

QUESTIONS = Path(__file__).with_name("questions.jsonl")


def timed_ask(client: httpx.Client, url: str, question: str) -> tuple[float, dict]:
    start = time.perf_counter()
    resp = client.post(f"{url}/ask", json={"question": question}, timeout=120)
    resp.raise_for_status()
    return (time.perf_counter() - start) * 1000, resp.json()


def summary(label: str, ms: list[float]) -> str:
    p95 = sorted(ms)[max(0, int(len(ms) * 0.95) - 1)]
    median, mean = statistics.median(ms), statistics.mean(ms)
    return f"{label:<12} median {median:8.1f} ms   p95 {p95:8.1f} ms   mean {mean:8.1f} ms"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    rows = [json.loads(line) for line in QUESTIONS.read_text().splitlines() if line.strip()][: args.limit]
    print(f"Cleared {get_cache().clear()} cached answers")

    cold, warm = [], []
    with httpx.Client() as client:
        timed_ask(client, args.url, "warm up the embedding model")  # first call loads the model
        get_cache().clear()
        for r in rows:
            try:
                ms_cold, body_cold = timed_ask(client, args.url, r["question"])
            except httpx.HTTPStatusError as exc:
                print(f"#{r['id']:>2} skipped: {exc.response.status_code} {exc.response.text[:80]}")
                continue
            ms_warm, body_warm = timed_ask(client, args.url, r["question"])
            assert not body_cold["cached"] and body_warm["cached"], "cache did not behave as expected"
            cold.append(ms_cold)
            warm.append(ms_warm)
            print(f"#{r['id']:>2} {body_cold['route']:<11} miss {ms_cold:7.0f} ms   hit {ms_warm:5.1f} ms")

    print()
    print(summary("cache miss", cold))
    print(summary("cache hit", warm))
    print(f"speedup      {statistics.median(cold) / statistics.median(warm):.0f}x (median)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
