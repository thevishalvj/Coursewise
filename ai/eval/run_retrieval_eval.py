"""Measure retrieval quality on eval/questions.jsonl.

For each question that has expected sources, checks whether those sources
appear in the top k results (recall@k), using the question's course filter.

Usage (from ai/):
    python eval/run_retrieval_eval.py [--k 5]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from coursewise.search import search  # noqa: E402

QUESTIONS = Path(__file__).with_name("questions.jsonl")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()

    rows = [json.loads(line) for line in QUESTIONS.read_text().splitlines() if line.strip()]
    scored = [r for r in rows if r["expected_sources"]]
    found_total = expected_total = 0
    for r in scored:
        hits = search(r["question"], course_codes=r["courses"] or None, k=args.k)
        got = {h.metadata["source"] for h in hits}
        found = [s for s in r["expected_sources"] if s in got]
        found_total += len(found)
        expected_total += len(r["expected_sources"])
        mark = "PASS" if len(found) == len(r["expected_sources"]) else "MISS"
        top = hits[0].metadata["source"] if hits else "-"
        print(f"{mark} #{r['id']:>2} top={top:<24} {r['question']}")
    recall = found_total / expected_total if expected_total else 0.0
    print(f"\nrecall@{args.k}: {recall:.2f} ({found_total}/{expected_total} expected sources found)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
