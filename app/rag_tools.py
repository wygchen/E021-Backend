#!/usr/bin/env python3
"""
RAG Tools for ADK Integration

This module provides ADK-compatible tool functions that wrap the RAG retriever
to enable the ExperiencePlanningAgent to search destinations and experiences.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add RAG directory to Python path
RAG_DIR = Path(__file__).parent.parent / "RAG"
sys.path.insert(0, str(RAG_DIR))

from rag_retriever import create_retriever


class RAGToolkit:
    """Provides RAG retrieval tools for the ADK agent system."""
    
    def __init__(self):
        """Initialize the RAG retriever with vector indexes."""
        # Get the RAG vector indexes directory
        index_dir = RAG_DIR / "vector_indexes"
        
        # Get API key from environment
        api_key = os.getenv('GEMINI_API_KEY')
        
        # Create and initialize retriever
        try:
            self.retriever = create_retriever(str(index_dir), api_key=api_key)
            print(f"✓ RAG Toolkit initialized successfully")
        except Exception as e:
            print(f"✗ Failed to initialize RAG Toolkit: {e}")
            raise
    
    def search_destinations(
        self,
        query: Optional[str] = None,
        destination_ids: Optional[List[str]] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search for destinations using semantic search or ID lookup.
        
        This is the destination_retriever tool for the PlannerAgent.
        
        Args:
            query: Natural language query describing desired destination characteristics
            destination_ids: List of specific destination IDs to retrieve
            top_k: Number of results to return (default: 3)
        
        Returns:
            List of destination dossiers with full metadata
        """
        return self.retriever.destination_retriever(
            query_string=query,
            destination_ids=destination_ids,
            top_k=top_k
        )
    
    def search_experiences(
        self,
        query: str,
        destination_id: Optional[str] = None,
        top_k: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Search for experiences using semantic search.
        
        This is the experience_retriever tool for the PlannerAgent.
        
        Args:
            query: Natural language query describing desired experience characteristics
            destination_id: Optional destination ID to filter experiences
            top_k: Number of results to return (default: 7)
        
        Returns:
            List of experience dossiers with full metadata
        """
        return self.retriever.experience_retriever(
            query_string=query,
            destination_id=destination_id,
            top_k=top_k
        )


# Global singleton instance
_rag_toolkit = None


def get_rag_toolkit() -> RAGToolkit:
    """Get or create the global RAG toolkit instance."""
    global _rag_toolkit
    if _rag_toolkit is None:
        _rag_toolkit = RAGToolkit()
    return _rag_toolkit


# Tool functions for ADK
def destination_retriever_tool(
    query: Optional[str] = None,
    destination_ids: Optional[List[str]] = None,
    top_k: int = 3
) -> str:
    """
    ADK tool function: Search for destinations.
    
    Use this when you need to find destinations based on user preferences
    or retrieve specific destinations by ID.
    
    Args:
        query: Natural language description of desired destination
        destination_ids: List of destination IDs to retrieve
        top_k: Number of results to return
    
    Returns:
        JSON string containing destination dossiers
    """
    import json
    toolkit = get_rag_toolkit()
    results = toolkit.search_destinations(query, destination_ids, top_k)
    return json.dumps(results, indent=2)


def experience_retriever_tool(
    query: str,
    destination_id: Optional[str] = None,
    top_k: int = 7
) -> str:
    """
    ADK tool function: Search for experiences.
    
    Use this when you need to find experiences that match user preferences.
    You can optionally filter by destination.
    
    Args:
        query: Natural language description of desired experiences
        destination_id: Optional destination ID to filter results
        top_k: Number of results to return
    
    Returns:
        JSON string containing experience dossiers
    """
    import json
    toolkit = get_rag_toolkit()
    results = toolkit.search_experiences(query, destination_id, top_k)
    return json.dumps(results, indent=2)
