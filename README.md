# Coursewise

A personal RAG assistant for UT Austin CS courses. It answers questions from
course catalog entries and syllabi.

## Stack

- **AI service (`ai/`):** FastAPI, LangGraph, ChromaDB, sentence-transformers, Gemini
- **Web app (`web/`):** Next.js, Prisma, Supabase (Postgres and email login). Setup is in `web/README.md`.
- **Cache:** Redis stores answers to repeated questions for 7 days

## Data

| Folder | Contents |
|---|---|
| `data/markdown/catalog/` | One file per C S course from the UT catalog (196 courses) |
| `data/markdown/syllabi/` | Syllabi you add by hand (see the README there) |

Refresh the catalog files:

```bash
python ai/scripts/fetch_catalog.py
```

## AI service (`ai/`)

Setup, once:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r ai/requirements.txt
cp ai/.env.example ai/.env   # then add your Gemini key
cd ai && python -m coursewise.ingest
```

Run the API:

```bash
cd ai && uvicorn coursewise.api:app --reload --port 8000
```

Ask a question:

```bash
curl -s localhost:8000/ask -H 'content-type: application/json' -d '{"question": "What does CS 439 cover?"}'
```

`/ask` returns `answer`, `route` (`course_info`, `grading`, `compare`, or `off_topic`), `sources`, and `latency_ms`.

Tests and retrieval eval:

```bash
cd ai && pytest -q
cd ai && python eval/run_retrieval_eval.py
```

### How the agent works

LangGraph runs four steps: **classify** the question by route, **retrieve** chunks from
ChromaDB (filtered by any course codes in the question), **filter** weak matches (only when no
course is named), and **generate** an answer with Gemini using only the retrieved text. Off-topic
questions and questions with no matching sources are answered without calling Gemini.

### Redis cache

`/ask` caches each answer in Redis, keyed by the normalized question, any course filter, and the
Gemini model. Repeat questions skip retrieval and Gemini entirely, and responses include `"cached": true`.
Rebuilding the index clears the cache. If Redis is not running, the service still answers, just without caching.
Set `REDIS_URL=` (empty) in `ai/.env` to turn caching off.

Measured with `python eval/benchmark_cache.py` (local Redis, Gemini free tier):

| | Median | p95 |
|---|---|---|
| Cache miss, answered by Gemini (4 questions) | 25 s | 48 s |
| Cache hit | 3 ms | 4 ms |

The miss times are inflated: the free tier rate-limited the benchmark, so many requests waited on
retries, and 12 of 20 questions were skipped. Unhurried single questions took 3 to 10 seconds. Either
way, a cache hit is three to four orders of magnitude faster.
