#!/usr/bin/env python3
"""
RAG Retrieval Engine for Dual-Brain System

This module provides the destination_retriever and experience_retriever tools
that perform semantic search over the vector indexes.
"""

import os
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from vector_index import VectorIndex


class SemanticRetriever:
    """
    Semantic search engine using cosine similarity on pre-built vector indexes.
    """
    
    def __init__(self, embedding_generator):
        """
        Initialize the retriever.
        
        Args:
            embedding_generator: Instance of EmbeddingGenerator from build_vector_index.py
        """
        self.embedding_generator = embedding_generator
        self.destination_index = None
        self.experience_index = None
    
    def load_indexes(self, index_dir: str = "vector_indexes"):
        """
        Load pre-built vector indexes from disk.
        
        Args:
            index_dir: Directory containing the .pkl index files
        """
        index_path = Path(index_dir)
        
        # Load destination index
        dest_index_file = index_path / "destination_index.pkl"
        if not dest_index_file.exists():
            raise FileNotFoundError(f"Destination index not found: {dest_index_file}")
        
        with open(dest_index_file, 'rb') as f:
            self.destination_index = pickle.load(f)
        
        print(f"✓ Loaded destination index: {len(self.destination_index.documents)} destinations")
        
        # Load experience index
        exp_index_file = index_path / "experience_index.pkl"
        if not exp_index_file.exists():
            raise FileNotFoundError(f"Experience index not found: {exp_index_file}")
        
        with open(exp_index_file, 'rb') as f:
            self.experience_index = pickle.load(f)
        
        print(f"✓ Loaded experience index: {len(self.experience_index.documents)} experiences")
    
    def _cosine_similarity(self, query_embedding: np.ndarray, embeddings: np.ndarray) -> np.ndarray:
        """
        Compute cosine similarity between query and all document embeddings.
        
        Args:
            query_embedding: Shape (embedding_dim,)
            embeddings: Shape (n_documents, embedding_dim)
        
        Returns:
            Similarity scores of shape (n_documents,)
        """
        # Normalize embeddings
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        embeddings_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        # Compute cosine similarity
        similarities = np.dot(embeddings_norm, query_norm)
        
        return similarities
    
    def _search(
        self,
        query_embedding: np.ndarray,
        index,
        top_k: int = 5,
        filter_fn: Optional[callable] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Perform semantic search on an index.
        
        Args:
            query_embedding: Query vector
            index: VectorIndex object
            top_k: Number of top results to return
            filter_fn: Optional function to filter documents (returns True to keep)
        
        Returns:
            List of (document, similarity_score) tuples
        """
        # Apply filter if provided
        if filter_fn:
            valid_indices = [i for i, doc in enumerate(index.documents) if filter_fn(doc)]
            filtered_embeddings = index.embeddings[valid_indices]
            filtered_documents = [index.documents[i] for i in valid_indices]
        else:
            filtered_embeddings = index.embeddings
            filtered_documents = index.documents
        
        if len(filtered_documents) == 0:
            return []
        
        # Compute similarities
        similarities = self._cosine_similarity(query_embedding, filtered_embeddings)
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Return documents with scores
        results = [
            (filtered_documents[i], float(similarities[i]))
            for i in top_indices
        ]
        
        return results
    
    def destination_retriever(
        self,
        query_string: Optional[str] = None,
        destination_ids: Optional[List[str]] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve destinations using semantic search or ID lookup.
        
        This is the RAG 1 retrieval tool for the PlannerAgent.
        
        Args:
            query_string: Natural language query for semantic search (Top-Down search)
            destination_ids: List of destination IDs for direct lookup (Bottom-Up search)
            top_k: Number of results to return (only for semantic search)
        
        Returns:
            List of destination dossiers (full JSON objects)
        """
        if self.destination_index is None:
            raise RuntimeError("Destination index not loaded. Call load_indexes() first.")
        
        # Bottom-Up: Direct ID lookup
        if destination_ids:
            results = [
                doc for doc in self.destination_index.documents
                if doc['destination_id'] in destination_ids
            ]
            return results
        
        # Top-Down: Semantic search
        if query_string:
            # Generate query embedding
            query_embedding = self.embedding_generator.embed_text(
                query_string,
                task_type="RETRIEVAL_QUERY"
            )
            
            # Perform search
            results_with_scores = self._search(
                query_embedding,
                self.destination_index,
                top_k=top_k
            )
            
            # Return just the documents (without scores for cleaner agent input)
            results = [doc for doc, score in results_with_scores]
            
            # Debug: Print scores
            print(f"\n🔍 Destination Search Results for: '{query_string}'")
            for i, (doc, score) in enumerate(results_with_scores, 1):
                print(f"  {i}. {doc['destination_name']} (ID: {doc['destination_id']}) - Score: {score:.3f}")
            
            return results
        
        raise ValueError("Must provide either query_string or destination_ids")
    
    def experience_retriever(
        self,
        query_string: str,
        destination_id: Optional[str] = None,
        top_k: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Retrieve experiences using semantic search.
        
        This is the RAG 2 retrieval tool for the PlannerAgent.
        
        Args:
            query_string: Natural language query for semantic search
            destination_id: Optional filter to only search within a specific destination
            top_k: Number of results to return
        
        Returns:
            List of experience dossiers (full JSON objects)
        """
        if self.experience_index is None:
            raise RuntimeError("Experience index not loaded. Call load_indexes() first.")
        
        # Generate query embedding
        query_embedding = self.embedding_generator.embed_text(
            query_string,
            task_type="RETRIEVAL_QUERY"
        )
        
        # Create filter function if destination_id is provided
        filter_fn = None
        if destination_id:
            filter_fn = lambda doc: doc.get('parent_destination_id') == destination_id
        
        # Perform search
        results_with_scores = self._search(
            query_embedding,
            self.experience_index,
            top_k=top_k,
            filter_fn=filter_fn
        )
        
        # Return just the documents
        results = [doc for doc, score in results_with_scores]
        
        # Debug: Print scores
        destination_filter = f" (filtered to {destination_id})" if destination_id else ""
        print(f"\n🔍 Experience Search Results for: '{query_string}'{destination_filter}")
        for i, (doc, score) in enumerate(results_with_scores, 1):
            print(f"  {i}. {doc['experience_name']} (ID: {doc['experience_id']}) - Score: {score:.3f}")
        
        return results


# Convenience function for direct usage
def create_retriever(index_dir: str = "vector_indexes", api_key: Optional[str] = None):
    """
    Create and initialize a SemanticRetriever with loaded indexes.
    
    Args:
        index_dir: Path to directory containing vector indexes
        api_key: Gemini API key (optional, will use GEMINI_API_KEY env var if not provided)
    
    Returns:
        Initialized SemanticRetriever instance
    """
    # Import here to avoid circular dependency
    from build_vector_index import EmbeddingGenerator
    
    # Initialize embedding generator
    embedding_gen = EmbeddingGenerator(api_key=api_key)
    
    # Create retriever and load indexes
    retriever = SemanticRetriever(embedding_gen)
    retriever.load_indexes(index_dir)
    
    return retriever


# Example usage
if __name__ == "__main__":
    print("\n🔍 RAG Retrieval Engine - Test Mode\n")
    
    # Get the script directory
    script_dir = Path(__file__).parent
    index_dir = script_dir / "vector_indexes"
    
    # Create retriever
    print("Initializing retriever...")
    try:
        retriever = create_retriever(str(index_dir))
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        print("\nMake sure you've run build_vector_index.py first!")
        exit(1)
    
    print("\n" + "="*60)
    print("Testing Retrieval Tools")
    print("="*60)
    
    # Test 1: Top-Down destination search
    print("\n📍 Test 1: Top-Down Destination Search")
    print("-" * 60)
    query = "family friendly destination with theme parks and cultural sites"
    destinations = retriever.destination_retriever(query_string=query, top_k=2)
    print(f"\nFound {len(destinations)} destinations")
    
    # Test 2: Experience search within a destination
    if destinations:
        dest_id = destinations[0]['destination_id']
        print(f"\n🎯 Test 2: Experience Search within {destinations[0]['destination_name']}")
        print("-" * 60)
        exp_query = "family fun thrill rides and entertainment"
        experiences = retriever.experience_retriever(
            query_string=exp_query,
            destination_id=dest_id,
            top_k=3
        )
        print(f"\nFound {len(experiences)} experiences")
    
    # Test 3: Bottom-Up destination lookup
    print("\n🔄 Test 3: Bottom-Up Destination Lookup")
    print("-" * 60)
    if destinations:
        lookup_ids = [destinations[0]['destination_id']]
        print(f"Looking up IDs: {lookup_ids}")
        lookup_results = retriever.destination_retriever(destination_ids=lookup_ids)
        print(f"\nFound {len(lookup_results)} destinations by ID")
    
    # Test 4: Open experience search (no destination filter)
    print("\n🌍 Test 4: Open Experience Search")
    print("-" * 60)
    open_query = "adventure hiking outdoor nature experience"
    experiences = retriever.experience_retriever(query_string=open_query, top_k=5)
    print(f"\nFound {len(experiences)} experiences")
    
    print("\n" + "="*60)
    print("✓ All tests completed!")
    print("="*60)
