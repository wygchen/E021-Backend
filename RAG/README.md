# 🗂️ RAG System - Quick Start Guide

## Overview

This directory contains the **Dual-Brain RAG (Retrieval-Augmented Generation) System** for the Hybrid AI Planner. It includes vector embeddings, semantic search, and retrieval tools for intelligent travel planning.

---

## 📁 Directory Structure

```
RAG/
├── destination_db.json              # Destination database (manually curated or LLM-generated)
├── experience_db.json               # Experience database (manually curated or LLM-generated)
│
├── build_vector_index.py           # 🔨 Build vector embeddings
├── rag_retriever.py                # 🔍 Semantic search engine
├── populate_db.py                  # 🤖 LLM-assisted database generation
│
├── requirements.txt                # Python dependencies
├── RAG_TECH_STACK.md              # 📚 Complete technical documentation
├── idea.md                         # 💡 System design & architecture plan
│
├── vector_indexes/                 # 📦 Generated vector indexes (created by build_vector_index.py)
│   ├── destination_index.pkl
│   └── experience_index.pkl
│
└── prompts/                        # 📝 LLM prompts for database generation
    ├── llm_fill_destination.txt
    └── llm_fill_experience.txt
```

---

## 🚀 Quick Start

### Step 0: Install Dependencies

```bash
# From the RAG directory
pip install -r requirements.txt

# OR from project root
cd ..
pip install -e .  # Installs from pyproject.toml
```

### Step 1: Set Up API Key

```bash
# Set your Gemini API key
export GEMINI_API_KEY='your-api-key-here'

# Verify
echo $GEMINI_API_KEY
```

### Step 2: Build Vector Indexes

```bash
python build_vector_index.py
```

**Expected Output:**
```
🚀 RAG Vector Index Builder
Building semantic search indexes for Dual-Brain RAG System

Initializing Gemini Embedding API...
✓ API initialized successfully

============================================================
Building Destination Vector Index
============================================================
Loaded 3 destinations
Generating embeddings...
✓ Destination index built successfully!

============================================================
Building Experience Vector Index
============================================================
Loaded 10 experiences
Generating embeddings...
✓ Experience index built successfully!

============================================================
✓ All indexes built successfully!
============================================================
```

### Step 3: Test Retrieval

```bash
python rag_retriever.py
```

This runs comprehensive tests of the semantic search engine.

---

## 🧪 Usage Examples

### In Your Agent Code

```python
from rag_retriever import create_retriever

# Initialize (do this once at startup)
retriever = create_retriever(index_dir="RAG/vector_indexes")

# Top-Down: Vibe-first destination search
destinations = retriever.destination_retriever(
    query_string="family friendly with culture and theme parks",
    top_k=3
)

# Get experiences for a destination
experiences = retriever.experience_retriever(
    query_string="exciting activities for families",
    destination_id=destinations[0]['destination_id'],
    top_k=7
)

# Bottom-Up: ID lookup
specific_dests = retriever.destination_retriever(
    destination_ids=["CZX", "JPN-FUK"]
)
```

---

## 📊 Database Schema

### Destination Schema (RAG 1)

Key fields for embeddings:
- `semantic_profile` - Rich paragraph describing the destination's soul
- `semantic_antiprofile` - Negative match criteria
- `one_line_pitch` - Concise hook

Structured data for filtering:
- `dominant_vibes` - List of vibe tags
- `cost_index` - 1-5 scale
- `logistics_hub_score` - 1-5 scale
- `primary_experience_types` - Links to experiences

### Experience Schema (RAG 2)

Key fields for embeddings:
- `semantic_profile` - Detailed narrative of the experience
- `semantic_antiprofile` - Who should NOT book this
- `one_line_pitch` - Package hook

Structured data for filtering:
- `parent_destination_id` - Links to destination
- `vibe_tags` - Detailed vibe descriptors
- `cost_tier` - Budget/Mid-Range/Premium
- `itinerary_role` - Anchor/Secondary/Add-On
- `physical_intensity` - 1-5 scale

---

## 🛠️ Advanced Operations

### Regenerating Indexes

If you update `destination_db.json` or `experience_db.json`:

```bash
python build_vector_index.py
```

The script will overwrite existing indexes in `vector_indexes/`.

### Using LLM to Populate Databases

If you need to generate or augment your database:

```bash
python populate_db.py
```

This uses LLM prompts to create rich semantic profiles for destinations and experiences.

---

## 📚 Documentation

- **`RAG_TECH_STACK.md`** - Complete technical documentation
  - Architecture diagrams
  - Tech stack rationale
  - Performance benchmarks
  - Scaling considerations
  
- **`idea.md`** - System design and agent workflow
  - 3-Agent Supervisor architecture
  - Dual-Brain RAG design
  - Retrieval-as-a-Tool model
  - Full workflow examples

---

## 🔧 Troubleshooting

### "GEMINI_API_KEY not found"
```bash
export GEMINI_API_KEY='your-key'
```

### "Import 'numpy' could not be resolved"
```bash
pip install -r requirements.txt
```

### "FileNotFoundError: destination_index.pkl"
```bash
# Build indexes first
python build_vector_index.py
```

### Slow Embedding Generation
- **Cause:** API rate limiting or network latency
- **Solution:** The script batches requests automatically. For very large datasets, consider adding delays between batches.

---

## 🎯 Next Steps

1. ✅ Build vector indexes (done with `build_vector_index.py`)
2. 📝 Create agent prompts (`planner_prompt.txt`, `psychologist_prompt.txt`)
3. 🤖 Build SupervisorAgent orchestrator
4. 🧠 Implement PlannerAgent with tool calling
5. 💬 Implement FastPsychologistAgent for user profiling
6. 🔄 Add conflict-resolution loopback logic

---

## 📞 Support

For issues or questions:
1. Check `RAG_TECH_STACK.md` for detailed documentation
2. Review `idea.md` for architecture understanding
3. Run test mode: `python rag_retriever.py`

---

**Last Updated:** November 16, 2025
