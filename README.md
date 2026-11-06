# Coursewise

A personal RAG assistant for UT Austin CS courses. It answers questions from
course catalog entries and syllabi.

## Planned stack

- **AI service:** FastAPI, LangGraph, ChromaDB, sentence-transformers, Gemini, Redis
- **Web app:** Next.js, Prisma, Supabase (Postgres)

## Data

| Folder | Contents |
|---|---|
| `data/markdown/catalog/` | One file per C S course from the UT catalog (196 courses) |
| `data/markdown/syllabi/` | Syllabi you add by hand (see the README there) |

Refresh the catalog files:

```bash
python ai/scripts/fetch_catalog.py
```
