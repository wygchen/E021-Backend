# 🎯 RAG System - Quick Reference

## Essential Commands

```bash
# Setup (one-time)
cd RAG/
./setup.sh

# Or manual setup:
pip install -r requirements.txt
export GEMINI_API_KEY='your-key'
python build_vector_index.py

# Test
python rag_retriever.py
```

## Core Components

| File | Purpose | Run When |
|------|---------|----------|
| `build_vector_index.py` | Create embeddings | Once, or when DB changes |
| `rag_retriever.py` | Search engine + tests | To test or use in code |
| `populate_db.py` | Generate DB with LLM | Optional, for data creation |

## Retrieval API

### Destination Search

```python
# Top-Down (semantic search)
destinations = retriever.destination_retriever(
    query_string="quiet art slow-travel",
    top_k=3
)

# Bottom-Up (ID lookup)
destinations = retriever.destination_retriever(
    destination_ids=["CZX", "JPN-FUK"]
)
```

### Experience Search

```python
# Filtered by destination
experiences = retriever.experience_retriever(
    query_string="family fun adventure",
    destination_id="CZX",
    top_k=7
)

# Open search (all destinations)
experiences = retriever.experience_retriever(
    query_string="K-Pop concert",
    top_k=7
)
```

## Tech Stack Summary

- **Embeddings**: Google Gemini `text-embedding-004` (768-dim)
- **Similarity**: Cosine similarity (NumPy)
- **Storage**: Pickle files (`destination_index.pkl`, `experience_index.pkl`)
- **API**: `google-generativeai` Python client

## Performance

- **Index Build**: ~2-10 seconds (depends on dataset size)
- **Index Load**: ~10-50ms (one-time per session)
- **Query**: ~250-600ms (dominated by API call)
- **Search**: ~1-2ms (pure NumPy, blazing fast)

## File Locations

```
vector_indexes/
├── destination_index.pkl   # Prebuilt embeddings for destinations
└── experience_index.pkl    # Prebuilt embeddings for experiences
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| API key error | `export GEMINI_API_KEY='your-key'` |
| Import errors | `pip install -r requirements.txt` |
| Index not found | `python build_vector_index.py` |
| Slow queries | Normal - API latency ~200-500ms |

## Next Steps

1. ✅ Build indexes → `python build_vector_index.py`
2. 🧪 Test system → `python rag_retriever.py`
3. 📖 Read full docs → `RAG_TECH_STACK.md`
4. 🤖 Build agents → Use `create_retriever()` in your code

---

**Full Docs**: `RAG_TECH_STACK.md` | **Setup**: `./setup.sh` | **Help**: `README.md`
