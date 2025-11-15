#!/usr/bin/env python3
"""
Vector Index Builder for Dual-Brain RAG System

This script builds vector embeddings for both the Destination and Experience databases,
creating a semantic search index that can be saved and loaded for the RAG retrieval system.
"""

import json
import os
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

from vector_index import VectorIndex


class EmbeddingGenerator:
    """
    Generates embeddings using Google's Gemini Embedding API.
    
    This uses the text-embedding-004 model which provides 768-dimensional embeddings
    optimized for semantic search and retrieval tasks.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the embedding generator.
        
        Args:
            api_key: Google API key. If None, will try to get from GEMINI_API_KEY env var
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Set it as environment variable or pass to constructor."
            )
        
        # Import here to avoid dependency issues if not using Gemini
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.genai = genai
            self.model_name = "models/text-embedding-004"
        except ImportError:
            raise ImportError(
                "google-generativeai package not found. "
                "Install it with: pip install google-generativeai"
            )
    
    def embed_text(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            task_type: One of "RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY", "SEMANTIC_SIMILARITY"
        
        Returns:
            Numpy array of shape (768,)
        """
        result = self.genai.embed_content(
            model=self.model_name,
            content=text,
            task_type=task_type
        )
        return np.array(result['embedding'])
    
    def embed_batch(
        self, 
        texts: List[str], 
        task_type: str = "RETRIEVAL_DOCUMENT",
        batch_size: int = 100
    ) -> np.ndarray:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of texts to embed
            task_type: Embedding task type
            batch_size: Number of texts to process at once
        
        Returns:
            Numpy array of shape (len(texts), 768)
        """
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}...")
            
            for text in batch:
                embedding = self.embed_text(text, task_type)
                embeddings.append(embedding)
        
        return np.array(embeddings)


class VectorIndexBuilder:
    """Builds and manages vector indexes for the RAG system."""
    
    def __init__(self, embedding_generator: EmbeddingGenerator):
        """
        Initialize the index builder.
        
        Args:
            embedding_generator: Instance of EmbeddingGenerator
        """
        self.embedding_generator = embedding_generator
    
    def build_destination_index(
        self, 
        destination_db_path: str,
        output_dir: str = "vector_indexes"
    ) -> VectorIndex:
        """
        Build vector index for destinations.
        
        The semantic_profile field is used as the primary embedding source.
        The semantic_antiprofile is also embedded and stored separately.
        
        Args:
            destination_db_path: Path to destination_db.json
            output_dir: Directory to save the index
        
        Returns:
            VectorIndex object
        """
        print("\n" + "="*60)
        print("Building Destination Vector Index")
        print("="*60)
        
        # Load destination database
        with open(destination_db_path, 'r', encoding='utf-8') as f:
            destinations = json.load(f)
        
        print(f"Loaded {len(destinations)} destinations")
        
        # Extract semantic profiles for embedding
        semantic_profiles = []
        for dest in destinations:
            # Combine semantic_profile with one_line_pitch for richer context
            combined_text = f"{dest.get('one_line_pitch', '')} {dest.get('semantic_profile', '')}"
            semantic_profiles.append(combined_text)
        
        # Generate embeddings
        print("Generating embeddings...")
        embeddings = self.embedding_generator.embed_batch(
            semantic_profiles,
            task_type="RETRIEVAL_DOCUMENT"
        )
        
        # Create index
        index = VectorIndex(
            embeddings=embeddings,
            documents=destinations,
            metadata={
                'index_type': 'destination',
                'embedding_model': 'text-embedding-004',
                'embedding_dimension': embeddings.shape[1],
                'num_documents': len(destinations),
                'fields_embedded': ['one_line_pitch', 'semantic_profile']
            }
        )
        
        # Save index
        self._save_index(index, output_dir, 'destination_index.pkl')
        
        print(f"✓ Destination index built successfully!")
        print(f"  - {len(destinations)} destinations indexed")
        print(f"  - Embedding dimension: {embeddings.shape[1]}")
        
        return index
    
    def build_experience_index(
        self, 
        experience_db_path: str,
        output_dir: str = "vector_indexes"
    ) -> VectorIndex:
        """
        Build vector index for experiences.
        
        The semantic_profile field is used as the primary embedding source.
        
        Args:
            experience_db_path: Path to experience_db.json
            output_dir: Directory to save the index
        
        Returns:
            VectorIndex object
        """
        print("\n" + "="*60)
        print("Building Experience Vector Index")
        print("="*60)
        
        # Load experience database
        with open(experience_db_path, 'r', encoding='utf-8') as f:
            experiences = json.load(f)
        
        print(f"Loaded {len(experiences)} experiences")
        
        # Extract semantic profiles for embedding
        semantic_profiles = []
        for exp in experiences:
            # Combine one_line_pitch and semantic_profile for richer context
            combined_text = f"{exp.get('one_line_pitch', '')} {exp.get('semantic_profile', '')}"
            semantic_profiles.append(combined_text)
        
        # Generate embeddings
        print("Generating embeddings...")
        embeddings = self.embedding_generator.embed_batch(
            semantic_profiles,
            task_type="RETRIEVAL_DOCUMENT"
        )
        
        # Create index
        index = VectorIndex(
            embeddings=embeddings,
            documents=experiences,
            metadata={
                'index_type': 'experience',
                'embedding_model': 'text-embedding-004',
                'embedding_dimension': embeddings.shape[1],
                'num_documents': len(experiences),
                'fields_embedded': ['one_line_pitch', 'semantic_profile']
            }
        )
        
        # Save index
        self._save_index(index, output_dir, 'experience_index.pkl')
        
        print(f"✓ Experience index built successfully!")
        print(f"  - {len(experiences)} experiences indexed")
        print(f"  - Embedding dimension: {embeddings.shape[1]}")
        
        return index
    
    def _save_index(self, index: VectorIndex, output_dir: str, filename: str):
        """Save index to disk using pickle."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filepath = output_path / filename
        
        with open(filepath, 'wb') as f:
            pickle.dump(index, f)
        
        print(f"  - Saved to: {filepath}")
    
    @staticmethod
    def load_index(filepath: str) -> VectorIndex:
        """Load a saved index from disk."""
        with open(filepath, 'rb') as f:
            return pickle.load(f)


def main():
    """Main function to build both indexes."""
    print("\n🚀 RAG Vector Index Builder")
    print("Building semantic search indexes for Dual-Brain RAG System\n")
    
    # Get paths
    script_dir = Path(__file__).parent
    destination_db = script_dir / "destination_db.json"
    experience_db = script_dir / "experience_db.json"
    output_dir = script_dir / "vector_indexes"
    
    # Verify files exist
    if not destination_db.exists():
        raise FileNotFoundError(f"Destination database not found: {destination_db}")
    if not experience_db.exists():
        raise FileNotFoundError(f"Experience database not found: {experience_db}")
    
    # Initialize embedding generator
    print("Initializing Gemini Embedding API...")
    try:
        embedding_gen = EmbeddingGenerator()
        print("✓ API initialized successfully\n")
    except Exception as e:
        print(f"✗ Failed to initialize API: {e}")
        print("\nMake sure GEMINI_API_KEY is set in your environment:")
        print("  export GEMINI_API_KEY='your-api-key-here'")
        return
    
    # Build indexes
    builder = VectorIndexBuilder(embedding_gen)
    
    try:
        # Build destination index
        dest_index = builder.build_destination_index(
            str(destination_db),
            str(output_dir)
        )
        
        # Build experience index
        exp_index = builder.build_experience_index(
            str(experience_db),
            str(output_dir)
        )
        
        print("\n" + "="*60)
        print("✓ All indexes built successfully!")
        print("="*60)
        print(f"\nIndexes saved to: {output_dir}/")
        print("  - destination_index.pkl")
        print("  - experience_index.pkl")
        print("\nYou can now use these indexes with the rag_retriever.py module.")
        
    except Exception as e:
        print(f"\n✗ Error building indexes: {e}")
        raise


if __name__ == "__main__":
    main()
