"""
Shared data structures for the RAG vector index system.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class VectorIndex:
    """Stores embeddings and metadata for a collection of documents."""
    embeddings: np.ndarray  # Shape: (n_documents, embedding_dim)
    documents: List[Dict[str, Any]]  # Original document data
    metadata: Dict[str, Any]  # Index metadata (model info, timestamp, etc.)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'embeddings': self.embeddings.tolist(),
            'documents': self.documents,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VectorIndex':
        """Load from dictionary."""
        return cls(
            embeddings=np.array(data['embeddings']),
            documents=data['documents'],
            metadata=data['metadata']
        )
