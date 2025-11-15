"""
Simple test script to verify the question_api endpoints are working correctly.
Run this after starting the FastAPI server with: uvicorn app.question_api:app --reload
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_api():
    print("=" * 60)
    print("Testing Question Generator API")
    print("=" * 60)
    
    # Test 1: Create session
    print("\n1. Creating session...")
    response = requests.post(f"{BASE_URL}/session")
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"
    data = response.json()
    session_id = data['session_id']
    print(f"   ✓ Session created: {session_id}")
    
    # Test 2: Get first question
    print("\n2. Getting first question...")
    response = requests.get(f"{BASE_URL}/session/{session_id}/question")
    assert response.status_code == 200
    data = response.json()
    question = data.get('pending_question')
    assert question is not None, "Expected a pending question"
    print(f"   ✓ Question received:")
    print(f"     Part: {question['part']}")
    print(f"     Choice A: {question['choices'][0]}")
    print(f"     Choice B: {question['choices'][1]}")
    
    # Test 3: Submit answers and continue quiz
    print("\n3. Answering questions...")
    question_count = 0
    max_questions = 15  # Safety limit
    
    while question_count < max_questions:
        # Get current question
        response = requests.get(f"{BASE_URL}/session/{session_id}/question")
        data = response.json()
        question = data.get('pending_question')
        
        if question is None:
            # Quiz complete
            profile = data.get('user_travel_profile')
            print(f"\n   ✓ Quiz completed after {question_count} questions")
            if profile:
                print(f"   Profile: {profile[:100]}...")
            break
        
        # Simulate answering (alternate between A and B)
        answer = "A" if question_count % 2 == 0 else "B"
        hesitation = 2.5 + (question_count * 0.3)  # Vary hesitation time
        
        print(f"\n   Question {question_count + 1} ({question['part']}):")
        print(f"     A: {question['choices'][0][:60]}...")
        print(f"     B: {question['choices'][1][:60]}...")
        print(f"     Answering: {answer} (hesitation: {hesitation:.1f}s)")
        
        # Submit answer
        response = requests.post(
            f"{BASE_URL}/session/{session_id}/answer",
            json={"answer": answer, "hesitation_seconds": hesitation}
        )
        assert response.status_code == 200
        
        question_count += 1
    
    # Test 4: Get final state
    print("\n4. Getting final session state...")
    response = requests.get(f"{BASE_URL}/session/{session_id}/state")
    assert response.status_code == 200
    state = response.json()
    print(f"   ✓ Final state retrieved:")
    print(f"     Part: {state.get('part')}")
    print(f"     Questions answered: {len(state.get('qa_history', []))}")
    print(f"     Has profile: {'user_travel_profile' in state}")
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the API server.")
        print("   Make sure the server is running with:")
        print("   uvicorn app.question_api:app --reload")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
