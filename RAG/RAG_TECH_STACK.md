# 🧠 RAG Engine Technical Stack Documentation

## Overview

This document explains the technical architecture, design decisions, and implementation details of the **Dual-Brain RAG (Retrieval-Augmented Generation) System** for the Hybrid AI Planner.

---

## 📋 Table of Contents

1. [System Architecture](#system-architecture)
2. [Tech Stack Components](#tech-stack-components)
3. [Vector Embedding Strategy](#vector-embedding-strategy)
4. [Retrieval Mechanisms](#retrieval-mechanisms)
5. [Data Flow](#data-flow)
6. [File Structure](#file-structure)
7. [Setup & Usage](#setup--usage)
8. [Performance Considerations](#performance-considerations)

---

## 🏗️ System Architecture

### The "Dual-Brain" Design

Our RAG system consists of two independent vector indexes, each optimized for different types of semantic search:

```
┌─────────────────────────────────────────────────────────────┐
│                     RAG ENGINE                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────┐         ┌─────────────────────┐    │
│  │   RAG 1: CONTEXT   │         │  RAG 2: PRODUCTS    │    │
│  │  (Destinations)    │         │   (Experiences)     │    │
│  │                    │         │                     │    │
│  │ • 768-dim vectors  │         │ • 768-dim vectors   │    │
│  │ • Semantic Profile │         │ • Semantic Profile  │    │
│  │ • Top-Down Search  │         │ • Bottom-Up Search  │    │
│  └────────────────────┘         └─────────────────────┘    │
│           │                               │                 │
│           └───────────┬───────────────────┘                 │
│                       │                                     │
│              ┌────────▼────────┐                           │
│              │  Cosine Similarity│                          │
│              │  Search Engine   │                          │
│              └──────────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

### Why Two Separate Indexes?

1. **Different Search Patterns**: Destinations need broad "vibe-based" search, while Experiences need granular "activity-based" search
2. **Different Retrieval Counts**: Destinations return 2-3 results, Experiences return 5-7
3. **Filter Independence**: Experiences can be filtered by `parent_destination_id` without affecting destination search performance
4. **Modular Updates**: Update one index without rebuilding the other

---

## 🛠️ Tech Stack Components

### Core Libraries

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Embedding Model** | Google Gemini `text-embedding-004` | Latest | Generate 768-dimensional semantic vectors |
| **Vector Operations** | NumPy | ≥1.24.0 | Efficient array operations and cosine similarity |
| **Serialization** | Pickle (Python stdlib) | Built-in | Save/load vector indexes |
| **API Client** | `google-generativeai` | ≥0.3.0 | Interface with Gemini API |

### Why These Choices?

#### 1. **Google Gemini `text-embedding-004`**
- **768 dimensions**: Sweet spot between expressiveness and efficiency
- **Optimized for retrieval**: Specifically designed for semantic search tasks
- **Multi-lingual support**: Handles diverse content (important for travel data)
- **Cost-effective**: Free tier supports hackathon/demo needs
- **Task-specific embeddings**: Different embeddings for documents vs queries

#### 2. **NumPy for Vector Math**
- **Production-ready**: Industry standard for numerical computing
- **Highly optimized**: C-backed operations for fast similarity search
- **Memory efficient**: Handles large embedding matrices elegantly
- **No GPU required**: CPU-only solution keeps infrastructure simple

#### 3. **Pickle for Index Storage**
- **Simple**: No database setup required
- **Fast**: Binary format loads quickly
- **Complete**: Stores entire NumPy arrays without conversion
- **Portable**: Single file per index

---

## 🎯 Vector Embedding Strategy

### What Gets Embedded?

Each document type combines multiple fields for a richer semantic representation:

#### Destinations (RAG 1)
```python
combined_text = f"{one_line_pitch} {semantic_profile}"
```
- **`one_line_pitch`**: Concise hook (e.g., "Discover ancient temples and theme parks")
- **`semantic_profile`**: Rich 2-3 paragraph description of the destination's soul

**Why combine?** The pitch provides focused keywords, while the profile provides context.

#### Experiences (RAG 2)
```python
combined_text = f"{one_line_pitch} {semantic_profile}"
```
- **`one_line_pitch`**: Package hook (e.g., "Full-day ethical elephant sanctuary experience")
- **`semantic_profile`**: Detailed narrative of the experience

### Task-Type Differentiation

Gemini's embedding API supports task-specific optimization:

```python
# For indexing documents
embedding = embed_text(text, task_type="RETRIEVAL_DOCUMENT")

# For user queries
embedding = embed_text(query, task_type="RETRIEVAL_QUERY")
```

This creates **asymmetric embeddings** optimized for document-to-query matching.

### What We DON'T Embed

We intentionally **don't embed** structured fields like:
- `dominant_vibes`, `cost_index`, `physical_intensity`
- These are used for **post-retrieval filtering** and **agent reasoning**

**Why?** Structured tags are better for logical filtering after semantic retrieval narrows down candidates.

---

## 🔍 Retrieval Mechanisms

### Cosine Similarity Search

Our core search algorithm:

```python
def cosine_similarity(query_vec, doc_vecs):
    # Normalize vectors to unit length
    query_norm = query_vec / ||query_vec||
    docs_norm = doc_vecs / ||doc_vecs||
    
    # Dot product of normalized vectors = cosine similarity
    similarities = docs_norm @ query_norm
    
    return similarities  # Range: [-1, 1], higher = more similar
```

**Why cosine similarity?**
- **Scale-invariant**: Measures angle, not magnitude
- **Efficient**: Single matrix multiplication
- **Interpretable**: Scores in [-1, 1] range
- **Standard**: Used by most embedding models

### The Two Retrieval Tools

#### 1. `destination_retriever()`

**Signature:**
```python
def destination_retriever(
    query_string: str = None,      # For Top-Down semantic search
    destination_ids: List[str] = None,  # For Bottom-Up ID lookup
    top_k: int = 3                  # Number of results
) -> List[Dict[str, Any]]
```

**Two Modes:**

**Mode A: Top-Down (Vibe-First)**
```python
results = destination_retriever(
    query_string="quiet, art, slow-travel",
    top_k=3
)
# Returns: [Takamatsu, Changzhou, ...]
```

**Mode B: Bottom-Up (ID Lookup)**
```python
results = destination_retriever(
    destination_ids=["JPN-FUK", "JPN-OSA"]
)
# Returns: [Fukuoka_Dossier, Osaka_Dossier]
```

#### 2. `experience_retriever()`

**Signature:**
```python
def experience_retriever(
    query_string: str,              # Always required
    destination_id: str = None,     # Optional filter
    top_k: int = 7
) -> List[Dict[str, Any]]
```

**Two Modes:**

**Mode A: Filtered Search (within destination)**
```python
experiences = experience_retriever(
    query_string="quiet art slow-travel",
    destination_id="JPN-TKM",
    top_k=5
)
# Returns: Experiences ONLY from Takamatsu
```

**Mode B: Open Search (across all destinations)**
```python
experiences = experience_retriever(
    query_string="K-Pop concert",
    top_k=7
)
# Returns: Top 7 K-Pop experiences from ANY destination
```

---

## 🌊 Data Flow

### End-to-End Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: INDEX BUILDING (One-time setup)                    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
    ┌──────────────────────────────────────┐
    │ 1. Load destination_db.json          │
    │ 2. Extract semantic_profile fields   │
    │ 3. Call Gemini API (batched)        │
    │ 4. Generate 768-dim embeddings       │
    │ 5. Build NumPy matrix                │
    │ 6. Save as destination_index.pkl     │
    └──────────────────────────────────────┘
                          │
    ┌──────────────────────────────────────┐
    │ Repeat for experience_db.json        │
    │ → experience_index.pkl               │
    └──────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: RUNTIME RETRIEVAL (During agent execution)         │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
    ┌──────────────────────────────────────┐
    │ PlannerAgent gets user_profile       │
    │ → Constructs query string            │
    └──────────────────────────────────────┘
                          │
                          ▼
    ┌──────────────────────────────────────┐
    │ Call destination_retriever()         │
    │ 1. Embed query_string (Gemini API)  │
    │ 2. Load destination_index.pkl        │
    │ 3. Compute cosine similarity         │
    │ 4. Return top-3 destinations         │
    └──────────────────────────────────────┘
                          │
                          ▼
    ┌──────────────────────────────────────┐
    │ Call experience_retriever()          │
    │ 1. Embed query_string                │
    │ 2. Load experience_index.pkl         │
    │ 3. Filter by destination_id          │
    │ 4. Compute cosine similarity         │
    │ 5. Return top-7 experiences          │
    └──────────────────────────────────────┘
                          │
                          ▼
    ┌──────────────────────────────────────┐
    │ PlannerAgent reasons over results    │
    │ → Builds final itinerary             │
    └──────────────────────────────────────┘
```

---

## 📁 File Structure

```
RAG/
├── destination_db.json              # Raw destination data
├── experience_db.json               # Raw experience data
├── build_vector_index.py           # Index builder script
├── rag_retriever.py                # Retrieval engine
├── RAG_TECH_STACK.md              # This documentation
│
├── vector_indexes/                 # Generated indexes
│   ├── destination_index.pkl       # Destination vectors + metadata
│   └── experience_index.pkl        # Experience vectors + metadata
│
└── (future files)
    ├── supervisor_agent.py         # Main orchestrator
    ├── planner_agent.py           # Planning logic
    └── prompts/                    # LLM prompts
        ├── planner_prompt.txt
        └── psychologist_prompt.txt
```

---

## 🚀 Setup & Usage

### Prerequisites

```bash
# Python 3.10+
python --version

# Install dependencies
pip install numpy google-generativeai
```

### Environment Setup

```bash
# Set your Gemini API key
export GEMINI_API_KEY='your-api-key-here'

# Verify it's set
echo $GEMINI_API_KEY
```

### Step 1: Build Vector Indexes

```bash
cd RAG/
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
Processing batch 1/1...
✓ Destination index built successfully!
  - 3 destinations indexed
  - Embedding dimension: 768
  - Saved to: vector_indexes/destination_index.pkl

============================================================
Building Experience Vector Index
============================================================
Loaded 10 experiences
Generating embeddings...
Processing batch 1/1...
✓ Experience index built successfully!
  - 10 experiences indexed
  - Embedding dimension: 768
  - Saved to: vector_indexes/experience_index.pkl

============================================================
✓ All indexes built successfully!
============================================================
```

### Step 2: Test Retrieval

```bash
python rag_retriever.py
```

This runs built-in tests that demonstrate:
- Top-Down destination search
- Experience search within a destination
- Bottom-Up destination lookup by ID
- Open experience search across all destinations

### Step 3: Use in Your Agent Code

```python
from rag_retriever import create_retriever

# Initialize once
retriever = create_retriever(index_dir="RAG/vector_indexes")

# Use in PlannerAgent
def planner_agent(user_profile):
    # Top-Down search
    destinations = retriever.destination_retriever(
        query_string=user_profile.get('preferences'),
        top_k=3
    )
    
    # Get experiences for top destination
    top_dest = destinations[0]
    experiences = retriever.experience_retriever(
        query_string=user_profile.get('preferences'),
        destination_id=top_dest['destination_id'],
        top_k=7
    )
    
    # Build plan...
    return build_itinerary(top_dest, experiences)
```

---

## ⚡ Performance Considerations

### Index Building Performance

| Dataset Size | Embedding Time | Storage Size |
|--------------|----------------|--------------|
| 3 destinations | ~2-3 seconds | ~50 KB |
| 10 experiences | ~5-7 seconds | ~150 KB |
| 100 destinations | ~30-40 seconds | ~500 KB |
| 500 experiences | ~2-3 minutes | ~3 MB |

**Bottleneck:** Gemini API calls (rate-limited)
**Mitigation:** Batch processing, caching

### Retrieval Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Load index from disk | ~10-50ms | One-time per session |
| Embed query (Gemini API) | ~200-500ms | Network latency |
| Cosine similarity (100 docs) | ~1-2ms | Pure NumPy |
| Total retrieval time | ~250-600ms | Dominated by API call |

**Key Insight:** Once indexes are loaded, the bottleneck is always the query embedding API call, not the similarity search.

### Optimization Strategies

1. **Index Caching**: Load indexes once at startup, reuse across requests
2. **Query Caching**: Cache embeddings for common queries
3. **Batch Queries**: If possible, embed multiple queries in one API call
4. **Async API Calls**: Use async I/O for concurrent embedding requests

### Scaling Considerations

**Current Design (Hackathon/Demo):**
- ✅ Perfect for 10-100 destinations, 50-500 experiences
- ✅ No database setup required
- ✅ Runs on laptop CPU

**Production Scaling (Future):**
- Move to vector database (Pinecone, Weaviate, ChromaDB)
- Use approximate nearest neighbor (ANN) algorithms
- Add embedding cache layer (Redis)
- Consider self-hosted embedding models for cost

---

## 🔧 Troubleshooting

### Common Issues

**1. "GEMINI_API_KEY not found"**
```bash
# Solution: Set environment variable
export GEMINI_API_KEY='your-key'
```

**2. "Import 'numpy' could not be resolved"**
```bash
# Solution: Install dependencies
pip install numpy google-generativeai
```

**3. "FileNotFoundError: destination_index.pkl"**
```bash
# Solution: Build indexes first
python build_vector_index.py
```

**4. API Rate Limiting**
- **Symptom**: Slow embedding or errors
- **Solution**: Add delay between batches or use smaller batch sizes

---

## 📊 Data Schema Reference

### VectorIndex Object Structure

```python
{
    'embeddings': np.ndarray,  # Shape: (n_docs, 768)
    'documents': List[Dict],   # Original JSON objects
    'metadata': {
        'index_type': 'destination' | 'experience',
        'embedding_model': 'text-embedding-004',
        'embedding_dimension': 768,
        'num_documents': int,
        'fields_embedded': ['one_line_pitch', 'semantic_profile']
    }
}
```

---

## 🎓 Further Reading

### Embedding Best Practices
- [Google Embeddings API Guide](https://ai.google.dev/docs/embeddings_guide)
- [Cosine Similarity Explained](https://en.wikipedia.org/wiki/Cosine_similarity)

### RAG Architecture
- [Retrieval-Augmented Generation for Knowledge-Intensive NLP](https://arxiv.org/abs/2005.11401)
- [Building RAG Applications](https://python.langchain.com/docs/use_cases/question_answering/)

### Vector Databases
- [Pinecone Documentation](https://docs.pinecone.io/)
- [ChromaDB Getting Started](https://docs.trychroma.com/)

---

## 📝 License & Credits

**Built for:** Hybrid AI Planner Hackathon Project  
**Embedding Model:** Google Gemini `text-embedding-004`  
**Core Libraries:** NumPy, google-generativeai  

---

**Last Updated:** November 16, 2025
