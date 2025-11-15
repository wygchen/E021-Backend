#!/usr/bin/env python3
"""
Simple test script that directly tests the QuestionGeneratorAgent without ADK complexity.
"""

from app.question_generator import QuestionGeneratorAgent

def test_question_generator():
    """Test the question generator standalone."""
    
    print("\n" + "="*70)
    print("Testing QuestionGeneratorAgent Directly")
    print("="*70)
    
    agent = QuestionGeneratorAgent()
    
    # Simulate session state
    state = {}
    
    # Step 1: Initial call (should set first question)
    print("\n1. Initial call (no answer):")
    agent.step_state(state)
    print(f"   State keys: {list(state.keys())}")
    print(f"   Pending question: {state.get('pending_question')}")
    
    # Step 2: Submit first answer
    print("\n2. Submit answer 'A':")
    state['submitted_answer'] = {'answer': 'A', 'hesitation_seconds': 2}
    agent.step_state(state)
    print(f"   QA History: {state.get('qa_history')}")
    print(f"   Pending question: {state.get('pending_question')}")
    
    # Step 3: Submit second answer
    print("\n3. Submit answer 'B':")
    state['submitted_answer'] = {'answer': 'B', 'hesitation_seconds': 1}
    agent.step_state(state)
    print(f"   QA History: {state.get('qa_history')}")
    print(f"   Pending question: {state.get('pending_question')}")
    
    # Step 4: Submit third answer
    print("\n4. Submit answer 'A':")
    state['submitted_answer'] = {'answer': 'A', 'hesitation_seconds': 3}
    agent.step_state(state)
    print(f"   QA History: {state.get('qa_history')}")
    print(f"   Part: {state.get('part')}")
    print(f"   Profile: {state.get('user_travel_profile')}")
    
    print("\n" + "="*70)
    print("✅ QuestionGeneratorAgent works standalone!")
    print("="*70)


if __name__ == "__main__":
    test_question_generator()
