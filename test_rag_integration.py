#!/usr/bin/env python3
"""
Simple test script to verify RAG integration with the agent system.

This script tests the RAG tools independently before running the full agent.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_rag_toolkit():
    """Test the RAG toolkit initialization and basic search."""
    print("\n" + "="*70)
    print("Testing RAG Toolkit Integration")
    print("="*70)
    
    try:
        from app.rag_tools import get_rag_toolkit
        print("\n✓ Successfully imported RAG toolkit")
        
        # Initialize toolkit
        print("\nInitializing RAG toolkit...")
        toolkit = get_rag_toolkit()
        print("✓ RAG toolkit initialized")
        
        # Test destination search
        print("\n" + "-"*70)
        print("Test 1: Destination Search (Top-Down)")
        print("-"*70)
        
        query = "relaxed cultural destination with temples and nature"
        print(f"Query: '{query}'")
        
        destinations = toolkit.search_destinations(query=query, top_k=2)
        print(f"\n✓ Found {len(destinations)} destinations:")
        for i, dest in enumerate(destinations, 1):
            print(f"  {i}. {dest.get('destination_name')} (ID: {dest.get('destination_id')})")
            print(f"     Cost Index: {dest.get('cost_index', 'N/A')}/5")
            print(f"     Type: {dest.get('hk_express_destination_type', 'N/A')}")
        
        # Test experience search
        if destinations:
            print("\n" + "-"*70)
            print("Test 2: Experience Search (within destination)")
            print("-"*70)
            
            dest_id = destinations[0]['destination_id']
            dest_name = destinations[0]['destination_name']
            print(f"Searching experiences in: {dest_name} ({dest_id})")
            
            exp_query = "cultural activities and nature experiences"
            experiences = toolkit.search_experiences(
                query=exp_query,
                destination_id=dest_id,
                top_k=4
            )
            
            print(f"\n✓ Found {len(experiences)} experiences:")
            for i, exp in enumerate(experiences, 1):
                print(f"  {i}. {exp.get('experience_name')}")
                print(f"     Role: {exp.get('itinerary_role', 'N/A')}")
                print(f"     Duration: {exp.get('duration_type', 'N/A')}")
                print(f"     Cost: {exp.get('cost_tier', 'N/A')}")
        
        # Test bottom-up search
        print("\n" + "-"*70)
        print("Test 3: Experience Search (Bottom-Up)")
        print("-"*70)
        
        anchor_query = "elephant sanctuary wildlife experience"
        print(f"Query: '{anchor_query}'")
        
        experiences = toolkit.search_experiences(query=anchor_query, top_k=3)
        print(f"\n✓ Found {len(experiences)} experiences:")
        for i, exp in enumerate(experiences, 1):
            print(f"  {i}. {exp.get('experience_name')}")
            print(f"     Parent Destination: {exp.get('parent_destination_id', 'N/A')}")
            print(f"     Role: {exp.get('itinerary_role', 'N/A')}")
        
        # Test destination lookup by ID
        if experiences:
            print("\n" + "-"*70)
            print("Test 4: Destination Lookup (by ID)")
            print("-"*70)
            
            dest_ids = list(set(exp.get('parent_destination_id') for exp in experiences if 'parent_destination_id' in exp))[:2]
            print(f"Looking up destination IDs: {dest_ids}")
            
            destinations = toolkit.search_destinations(destination_ids=dest_ids)
            print(f"\n✓ Found {len(destinations)} destinations:")
            for i, dest in enumerate(destinations, 1):
                print(f"  {i}. {dest.get('destination_name')} (ID: {dest.get('destination_id')})")
        
        print("\n" + "="*70)
        print("✅ All RAG toolkit tests passed!")
        print("="*70)
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "="*70)
        print("Make sure:")
        print("1. Vector indexes exist in RAG/vector_indexes/")
        print("2. GEMINI_API_KEY environment variable is set")
        print("3. All dependencies are installed")
        print("="*70)
        return False


def test_experience_planner():
    """Test the experience planning agent."""
    print("\n" + "="*70)
    print("Testing Experience Planning Agent")
    print("="*70)
    
    try:
        from app.experience_planner import ExperiencePlanningAgent
        print("\n✓ Successfully imported ExperiencePlanningAgent")
        
        # Create agent
        agent = ExperiencePlanningAgent()
        print("✓ Agent initialized")
        
        # Create a mock context
        print("\nCreating mock user profile...")
        
        mock_profile = "User prefers relaxed wellness activities, cultural temples and historical sites, and nature experiences. They want to avoid nightlife and prefer budget-friendly options."
        print(f"Profile: {mock_profile}")
        
        # Note: Full agent testing requires ADK context which is complex to mock
        # For now, we verify the agent can be instantiated
        print("\n✓ Agent ready (full testing requires ADK runner)")
        
        print("\n" + "="*70)
        print("✅ Experience Planning Agent tests passed!")
        print("="*70)
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("RAG Integration Test Suite")
    print("="*70)
    
    results = []
    
    # Test 1: RAG Toolkit
    results.append(("RAG Toolkit", test_rag_toolkit()))
    
    # Test 2: Experience Planner
    results.append(("Experience Planner", test_experience_planner()))
    
    # Summary
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! The RAG integration is working.")
        print("\nYou can now run the full agent with: python run_agent.py")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    print("="*70)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
