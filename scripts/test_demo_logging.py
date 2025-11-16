#!/usr/bin/env python3
"""
Quick test to demonstrate the new terminal logging output.
Run this to see what the uvicorn terminal will display during demo.
"""

import requests
import time

BASE_URL = "http://localhost:8000"

def test_demo_flow():
    """Simulate a complete user flow with terminal logging."""
    
    print("\n" + "="*70)
    print("🎬 STARTING DEMO FLOW TEST")
    print("   Watch the uvicorn terminal for INFO messages!")
    print("="*70 + "\n")
    
    # 1. Create session
    print("1️⃣  Creating session...")
    response = requests.post(f"{BASE_URL}/session")
    session_id = response.json()["session_id"]
    print(f"   ✅ Session created: {session_id}")
    time.sleep(1)
    
    # 2. Get first question
    print("\n2️⃣  Getting first question...")
    response = requests.get(f"{BASE_URL}/session/{session_id}/question")
    question = response.json()["pending_question"]["question_text"]
    choices = response.json()["pending_question"]["choices"]
    print(f"   Question: {question}")
    print(f"   Choices: {', '.join(choices[:2])}...")
    time.sleep(1)
    
    # 3. Answer questions with varying hesitation
    test_answers = [
        {"answer": choices[0], "hesitation": 1.2, "desc": "Quick decision"},
        {"answer": choices[1], "hesitation": 3.8, "desc": "Moderate hesitation"},
        {"answer": choices[0], "hesitation": 6.5, "desc": "Long hesitation"},
        {"answer": choices[1], "hesitation": 2.1, "desc": "Quick decision"},
    ]
    
    for i, answer_data in enumerate(test_answers, 1):
        print(f"\n3️⃣  Submitting answer #{i} ({answer_data['desc']})...")
        
        # Get current question first
        response = requests.get(f"{BASE_URL}/session/{session_id}/question")
        question_data = response.json()["pending_question"]
        
        if not question_data:
            print("   ℹ️  No more questions - quiz complete!")
            break
            
        # Pick first choice for simplicity
        choice = question_data["choices"][0]
        
        # Submit answer
        response = requests.post(
            f"{BASE_URL}/session/{session_id}/answer",
            json={
                "answer": choice,
                "hesitation_seconds": answer_data["hesitation"]
            }
        )
        
        result = response.json()
        if result.get("pending_question"):
            print(f"   ✅ Answer submitted, next question ready")
        else:
            print(f"   ✅ Answer submitted, profile generated!")
            
        time.sleep(1.5)
    
    # 4. Generate travel plan
    print("\n4️⃣  Requesting travel plan...")
    response = requests.post(f"{BASE_URL}/session/{session_id}/plan")
    plan = response.json()
    
    if plan.get("status") == "SUCCESS":
        destinations = plan.get("data", [])
        print(f"   ✅ Planning complete: {len(destinations)} destinations")
        for i, dest in enumerate(destinations, 1):
            print(f"      {i}. {dest.get('name', 'Unknown')}")
    else:
        print(f"   ❌ Planning failed: {plan.get('message')}")
    
    print("\n" + "="*70)
    print("🎬 DEMO FLOW COMPLETE")
    print(f"   Check output/session_{session_id}.txt for full log")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        test_demo_flow()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Backend server not running!")
        print("   Start it with: .conda/bin/uvicorn app.question_api:app --reload --port 8000")
    except Exception as e:
        print(f"\n❌ Error: {e}")
